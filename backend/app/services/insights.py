from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from openai import OpenAI
from sqlalchemy import text

from . import guide_assignment
from .exceptions import ValidationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ERD schema context embedded for Phase 1 system prompt
# ---------------------------------------------------------------------------
_ERD_SCHEMA = """
Tables and columns (PostgreSQL schema):

customers(id PK, clorian_client_id UK, first_name, last_name, email)

reservations(id PK, clorian_reservation_id UK, clorian_purchase_id, customer_id FK->customers,
  tour_id FK->tours, schedule_id FK->schedule (nullable), language_code, event_start_datetime TIMESTAMPTZ,
  status, current_ticket_num, clorian_created_at, clorian_modified_at, created_at)

reservation_versions(id PK, reservation_id FK->reservations, hash, status, current_ticket_num,
  language_code, event_start_datetime, received_at, valid_from, poll_execution_id FK->poll_execution)

tickets(id PK, clorian_ticket_id UK, reservation_id FK->reservations, buyer_type_id,
  buyer_type_name, start_datetime, end_datetime, ticket_status, price, venue_id, venue_name,
  clorian_created_at, clorian_modified_at, created_at)

tours(id PK, clorian_product_id UK, name, description TEXT, duration INT)

schedule(id PK, guide_id FK->guides (nullable), tour_id FK->tours, language_code,
  event_start_datetime TIMESTAMPTZ, event_end_datetime TIMESTAMPTZ,
  status VARCHAR -- values: UNASSIGNED, ASSIGNED, COMPLETED, CANCELLED, created_at)

guides(id PK, first_name, last_name, email, phone, guide_rating DECIMAL, is_active BOOLEAN)

languages(id PK, code UK, name)

guide_languages(guide_id FK->guides, language_id FK->languages)
  -- junction: which languages a guide speaks

guide_tour_types(guide_id FK->guides, tour_id FK->tours)
  -- junction: which tours a guide is qualified to lead (expertise)

availability_patterns(id PK, guide_id FK->guides, timezone)
availability_slots(id PK, pattern_id FK->availability_patterns, day_of_week, start_time, end_time)
availability_exceptions(id PK, pattern_id FK->availability_patterns, date, type, reason)

surveys(id PK, customer_id FK->customers, guide_id FK->guides, reservation_id FK->reservations,
  comment TEXT, rating INT)

notifications(id PK, event_type, schedule_id FK->schedule, guide_id FK->guides (nullable),
  user_id FK->users (nullable), channel, status, priority, action_required BOOLEAN,
  message TEXT, detail_json JSONB, actions_json JSONB, sent_at, read_at, retry_count, created_at)

poll_execution(id PK, window_start, window_end, executed_at, finished_at, status, seed,
  generated_total, generated_created, generated_updated, generated_unchanged, error_message TEXT)

poll_staging(id PK, poll_execution_id FK->poll_execution, entity_type, external_id, scenario,
  payload_json JSONB, created_at, processed_at, processed_status, processed_error TEXT)

sync_logs(id PK, poll_execution_id FK->poll_execution, started_at, finished_at, new_count,
  changed_count, cancelled_count, status, errors TEXT)

tour_assignment_logs(id PK, schedule_id FK->schedule, guide_id FK->guides, assigned_at,
  assigned_by, assignment_type, action)

users(id PK, username UK, email UK, password_hash, full_name, role, is_active BOOLEAN, created_at)

Key domain notes:
- A "schedule" groups N reservations for the same tour + language + timeslot. guide_id is NULL when unassigned.
- "Expertise" is stored in guide_tour_types (guide qualifies for a tour type).
- schedule.status = 'UNASSIGNED' means no guide is assigned yet.
- Upcoming schedules: event_start_datetime > NOW() AND status NOT IN ('CANCELLED', 'COMPLETED').
"""

_PHASE1_SYSTEM = f"""You are a PostgreSQL expert. Given a natural-language question about Oceanarium operations,
produce a single safe SELECT query that answers it.

Database schema:
{_ERD_SCHEMA}

Rules:
- Return ONLY a JSON object with a single key "sql" containing the SQL string.
- The query MUST be a SELECT statement only. Never use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE.
- **CRITICAL**: Only use columns explicitly listed in the schema above. Never invent or assume columns exist.
- If a question cannot be answered with available columns, return a query selecting a helpful error message.
- Limit result rows to 100 using LIMIT 100 unless the question asks for a single count.
- Use table aliases for readability.
- Use NOW() for the current timestamp.
- Do not wrap the SQL in markdown code fences.

Example output:
{{"sql": "SELECT COUNT(*) AS unassigned FROM schedule WHERE guide_id IS NULL AND event_start_datetime > NOW()"}}
"""

_PHASE2_SYSTEM = """You are an operations analyst for Oceanarium, a tour guide management platform.
You have been given the results of a database query and the original question from the admin.
You may also receive ENRICHED CONTEXT with eligibility data for unassigned schedules.

Your job is to:
1. Write a clear, concise text answer to the question (1-3 sentences).
2. Choose the best chart type to visualize the data.
3. Provide up to 3 actionable, data-driven recommendations.

Chart type selection guide:
- "number": single count or KPI (data has one row/value)
- "bar": comparing multiple items by a numeric value
- "line": trend over time (data has date/month labels)
- "donut": proportional breakdown / percentages
- "list": ranking with values OR showing individual schedule/guide details
- "comparison": exactly two values to contrast (e.g. this week vs last week)

**IMPORTANT for unassigned schedules:**
- If ENRICHED CONTEXT is provided, use it to make recommendations specific and actionable.
- For "list" chart type, you can show schedule details (tour name, time, language) as the list items
  instead of just counts. The "value" can be the number of eligible guides for that schedule.
- Recommendations should reference actual guide names and specific blocking reasons from the enrichment.

Recommendation action_type values (use only these):
- "train": guide needs additional tour type expertise (name which guides and which tours)
- "hire": new guides should be recruited (specify missing language or expertise)
- "assign": existing eligible guides should be assigned (name the top guide candidates)
- "review": admin should review a situation manually (explain what to check)

Return ONLY a JSON object with this exact shape:
{
  "answer": "string — 1-3 sentence answer",
  "chart": {
    "type": "number|bar|line|donut|list|comparison",
    "title": "short chart title",
    "data": [{"label": "string", "value": number}]
  },
  "recommendations": [
    {
      "title": "string",
      "description": "string (be specific, use guide names/tour names from enrichment)",
      "action_type": "train|hire|assign|review"
    }
  ]
}

Keep recommendations practical and specific to the data returned. Maximum 3 recommendations.
"""

# ---------------------------------------------------------------------------
# SQL safety guard
# ---------------------------------------------------------------------------
_BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|MERGE|GRANT|REVOKE|EXEC|EXECUTE|CALL)\b",
    re.IGNORECASE,
)

_MAX_ROWS = 100


def _guard_sql(sql: str) -> None:
    """Raise ValidationError if the SQL contains any non-SELECT statements."""
    stripped = sql.strip()
    if not stripped.upper().startswith("SELECT") and not stripped.upper().startswith("WITH"):
        raise ValidationError(f"Generated query is not a SELECT statement: {stripped[:80]}")
    if _BLOCKED_KEYWORDS.search(stripped):
        raise ValidationError("Generated query contains disallowed keywords")


# ---------------------------------------------------------------------------
# Context enrichment for unassigned schedules
# ---------------------------------------------------------------------------
def _enrich_unassigned_schedules(conn: Any, rows: list[dict], question: str) -> dict:
    """
    If the question is about unassigned schedules and the results contain schedule IDs,
    check eligibility for each and return enriched context.

    Returns a dict with:
      - "schedules": original rows + "eligible_guides" per schedule
      - "enrichment_summary": text summary of findings
    """
    keywords = ["unassigned", "without guide", "no guide", "without assignment", "missing guide"]
    if not any(kw in question.lower() for kw in keywords):
        return {}

    schedule_ids = []
    for row in rows:
        if "id" in row and isinstance(row["id"], int):
            schedule_ids.append(row["id"])
        elif "schedule_id" in row and isinstance(row["schedule_id"], int):
            schedule_ids.append(row["schedule_id"])

    if not schedule_ids:
        return {}

    logger.info("Enriching %d unassigned schedules with eligibility data", len(schedule_ids))

    enriched_schedules = []
    total_eligible = 0
    total_no_expertise = 0
    total_no_language = 0
    total_no_availability = 0

    for sched_id in schedule_ids[:10]:
        try:
            eligible, reasons = guide_assignment.find_eligible_guides(conn, sched_id)
            enriched_schedules.append(
                {
                    "schedule_id": sched_id,
                    "eligible_count": len(eligible),
                    "eligible_guides": [
                        {
                            "id": g["id"],
                            "name": f"{g['first_name']} {g['last_name']}",
                            "rating": float(g.get("guide_rating") or 0),
                        }
                        for g in eligible[:3]
                    ],
                    "reasons": reasons,
                }
            )
            if eligible:
                total_eligible += 1
            else:
                if "NO_EXPERTISE_MATCH" in reasons:
                    total_no_expertise += 1
                if "NO_LANGUAGE_MATCH" in reasons:
                    total_no_language += 1
                if "NO_AVAILABILITY_MATCH" in reasons:
                    total_no_availability += 1
        except Exception as exc:
            logger.warning("Could not check eligibility for schedule %d: %s", sched_id, exc)
            continue

    summary_parts = []
    if total_eligible > 0:
        summary_parts.append(f"{total_eligible} schedules have eligible guides available")
    if total_no_expertise > 0:
        summary_parts.append(f"{total_no_expertise} blocked by missing expertise")
    if total_no_language > 0:
        summary_parts.append(f"{total_no_language} blocked by language mismatch")
    if total_no_availability > 0:
        summary_parts.append(f"{total_no_availability} blocked by guide availability conflicts")

    return {
        "schedules": enriched_schedules,
        "enrichment_summary": "; ".join(summary_parts) if summary_parts else "No blocking issues detected",
    }


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------
def run_insight_query(conn: Any, question: str) -> dict:
    """
    Two-phase LLM flow:
      Phase 1 — question + ERD → GPT-4o → safe SELECT SQL
      Phase 2 — SQL rows + question → GPT-4o → answer + chart + recommendations

    Raises:
      ValidationError: if generated SQL is unsafe
      OpenAIError: re-raised as-is so the route can return 503
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)

    # ------------------------------------------------------------------
    # Phase 1: NL → SQL
    # ------------------------------------------------------------------
    logger.info("Insights Phase 1: generating SQL for question: %r", question[:120])
    phase1_response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _PHASE1_SYSTEM},
            {"role": "user", "content": question},
        ],
        temperature=0,
        max_tokens=512,
    )

    phase1_content = phase1_response.choices[0].message.content or "{}"
    try:
        phase1_json = json.loads(phase1_content)
        sql = phase1_json.get("sql", "").strip()
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Phase 1 returned invalid JSON: {phase1_content[:200]}") from exc

    if not sql:
        raise ValidationError("Phase 1 did not return a SQL query")

    _guard_sql(sql)
    logger.info("Insights Phase 1 SQL: %s", sql[:300])

    # ------------------------------------------------------------------
    # Execute SELECT against PostgreSQL
    # ------------------------------------------------------------------
    try:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchmany(_MAX_ROWS)]
    except Exception as exc:
        raise RuntimeError(f"Database query failed: {exc}") from exc

    logger.info("Insights query returned %d rows", len(rows))

    # ------------------------------------------------------------------
    # Enrich context for unassigned schedules
    # ------------------------------------------------------------------
    enrichment = _enrich_unassigned_schedules(conn, rows, question)

    # ------------------------------------------------------------------
    # Phase 2: rows + enrichment + question → answer + chart + recommendations
    # ------------------------------------------------------------------
    rows_payload = json.dumps(rows, default=str)
    user_message_parts = [
        f"Question: {question}",
        f"Query used: {sql}",
        f"Query results ({len(rows)} rows):\n{rows_payload}",
    ]

    if enrichment:
        enrichment_payload = json.dumps(enrichment, default=str, indent=2)
        user_message_parts.append(
            f"\n**ENRICHED CONTEXT** (eligibility check for unassigned schedules):\n{enrichment_payload}\n\n"
            "Use this enrichment to provide specific, actionable recommendations:\n"
            "- If eligible_count > 0 for a schedule, recommend 'assign' and name the top guides.\n"
            "- If NO_EXPERTISE_MATCH, recommend 'train' (list which guides need tour type added).\n"
            "- If NO_LANGUAGE_MATCH, recommend 'hire' (specify missing language).\n"
            "- If NO_AVAILABILITY_MATCH, recommend 'review' (check guide availability patterns).\n"
            "- Show the actual schedule details (tour, time, language) in the answer or chart data."
        )

    user_message = "\n\n".join(user_message_parts)

    logger.info("Insights Phase 2: interpreting %d rows (enriched: %s)", len(rows), bool(enrichment))
    phase2_response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _PHASE2_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1536,
    )

    phase2_content = phase2_response.choices[0].message.content or "{}"
    try:
        phase2_json = json.loads(phase2_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Phase 2 returned invalid JSON: {phase2_content[:200]}") from exc

    return {
        "question": question,
        "answer": phase2_json.get("answer", ""),
        "chart": phase2_json.get("chart"),
        "recommendations": phase2_json.get("recommendations", []),
        "sql_used": sql,
    }
