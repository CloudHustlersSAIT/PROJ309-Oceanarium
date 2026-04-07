# AI Data Insights - Technical Architecture & Flow Documentation

**Version:** 1.0  
**Last Updated:** 2026-04-07  
**Audience:** Developers, Architects, DevOps

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Sequence Diagrams](#sequence-diagrams)
3. [Backend Flow](#backend-flow)
4. [Frontend Flow](#frontend-flow)
5. [File Structure & Responsibilities](#file-structure--responsibilities)
6. [Service Layer Deep Dive](#service-layer-deep-dive)
7. [API Request/Response Flow](#api-requestresponse-flow)
8. [Error Handling Flow](#error-handling-flow)
9. [Data Enrichment Flow](#data-enrichment-flow)
10. [Integration Points](#integration-points)

---

## System Architecture

> **Visual Diagram:** See [`diagrams/insights-system-architecture.png`](./diagrams/insights-system-architecture.png)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT BROWSER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  DashboardView.vue                                                │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  DashboardInsightPanel.vue (Composition API)              │  │  │
│  │  │                                                             │  │  │
│  │  │  • Voice State Machine (idle/listening/processing/result) │  │  │
│  │  │  • Web Speech API Integration                             │  │  │
│  │  │  • Chart Rendering (6 SVG types)                          │  │  │
│  │  │  • Error Modal Management                                  │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    │ HTTP POST                           │
│                                    ▼                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │   /insights/query               │
                    │   (FastAPI Route)               │
                    └────────────────┬────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  app/routes/insights.py                                           │  │
│  │  • Authentication Guard (require_authenticated_user)             │  │
│  │  • Request Validation (InsightRequest)                           │  │
│  │  • Content Safety Pre-check (assert_text_is_safe)                │  │
│  │  • Service Layer Orchestration                                   │  │
│  │  • Error Response Mapping (400/422/500/503)                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    │ calls                               │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  app/services/insights.py                                         │  │
│  │                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │  PHASE 1: NL → SQL                                          │ │  │
│  │  │  • Embed ERD schema in system prompt                        │ │  │
│  │  │  • Call OpenAI GPT-4o (JSON mode)                           │ │  │
│  │  │  • Parse SQL from response                                  │ │  │
│  │  │  • SQL Safety Guard (_guard_sql)                            │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                     │  │
│  │                              │ execute SQL                         │  │
│  │                              ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │  PostgreSQL Query Execution                                 │ │  │
│  │  │  • Use SQLAlchemy text() for safe execution                 │ │  │
│  │  │  • Fetch up to 100 rows                                     │ │  │
│  │  │  • Convert to list of dicts                                 │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                     │  │
│  │                              │ rows                                │  │
│  │                              ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │  Enrichment (if unassigned schedule query)                  │ │  │
│  │  │  • Detect keywords in question                              │ │  │
│  │  │  • Extract schedule IDs from rows                           │ │  │
│  │  │  • Call guide_assignment.find_eligible_guides()             │ │  │
│  │  │  • Aggregate blocking reasons                               │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                     │  │
│  │                              │ enriched context                    │  │
│  │                              ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │  PHASE 2: Rows → Insights                                   │ │  │
│  │  │  • Build prompt: question + SQL + rows + enrichment         │ │  │
│  │  │  • Call OpenAI GPT-4o (JSON mode)                           │ │  │
│  │  │  • Parse: answer, chart, recommendations                    │ │  │
│  │  │  • Return structured InsightResponse                        │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
                    ▼                                  ▼
        ┌────────────────────┐          ┌─────────────────────────┐
        │  OpenAI GPT-4o     │          │  PostgreSQL Database    │
        │  • Phase 1: NL→SQL │          │  • Read-only access     │
        │  • Phase 2: Insights│          │  • 100 row limit        │
        └────────────────────┘          └─────────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │ Azure Content      │
        │ Safety (optional)  │
        └────────────────────┘
```

---

## Sequence Diagrams

> **Visual Diagrams:** All sequence diagrams are available as high-resolution images in the [`diagrams/`](./diagrams/) folder.

### 1. Complete Query Flow (Success Case)

> **Visual Diagram:** See [`diagrams/insights-complete-query-flow.png`](./diagrams/insights-complete-query-flow.png)

```
User            Frontend              Backend Route         Insights Service      Content Safety    OpenAI GPT-4o    PostgreSQL    Guide Assignment
 │                  │                       │                      │                    │                 │               │                 │
 │─── Type/Speak ──▶│                       │                      │                    │                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │─── POST /insights/query ────────────────────▶│                    │                 │               │                 │
 │                  │   {question: "..."}   │                      │                    │                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │─── validate auth ───▶│                    │                 │               │                 │
 │                  │                       │◀──── JWT OK ─────────│                    │                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │─── assert_text_is_safe(question) ────────▶│                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │◀──── PASS ─────────│                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │─── run_insight_query(conn, question) ────▶│                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │──────────────────────────────────────▶│               │                 │
 │                  │                       │                      │  PHASE 1: {question, ERD schema}     │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │◀─────────────────────────────────────│               │                 │
 │                  │                       │                      │     {"sql": "SELECT ..."}             │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │─── _guard_sql(sql) ──────────────────▶│               │                 │
 │                  │                       │                      │◀──── validation OK ───────────────────│               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │────────────────────────────────────────────────────────▶│                 │
 │                  │                       │                      │     execute(text(sql))                                 │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │◀───────────────────────────────────────────────────────│                 │
 │                  │                       │                      │     rows (list of dicts)                               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │─── _enrich_unassigned_schedules() ─────────────────────────────────────▶│
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │◀──────────────────────────────────────────────────────────────────────│
 │                  │                       │                      │     {schedules: [...], enrichment_summary}            │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │──────────────────────────────────────▶│               │                 │
 │                  │                       │                      │  PHASE 2: {question, sql, rows, enrichment}           │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │                      │◀─────────────────────────────────────│               │                 │
 │                  │                       │                      │  {answer, chart, recommendations}     │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │                       │◀── return InsightResponse ───────────────│                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │                  │◀─── HTTP 200 ─────────│                      │                    │                 │               │                 │
 │                  │   {question, answer, chart, recommendations, sql_used}            │                 │               │                 │
 │                  │                       │                      │                    │                 │               │                 │
 │◀─ Display ───────│                       │                      │                    │                 │               │                 │
 │   Chart +        │                       │                      │                    │                 │               │                 │
 │   Answer +       │                       │                      │                    │                 │               │                 │
 │   Recommendations│                       │                      │                    │                 │               │                 │
```

### 2. Content Safety Block Flow

> **Visual Diagram:** See [`diagrams/insights-content-safety-block-flow.png`](./diagrams/insights-content-safety-block-flow.png)

```
User            Frontend              Backend Route         Content Safety
 │                  │                       │                      │
 │─── Ask Question ▶│                       │                      │
 │                  │                       │                      │
 │                  │─── POST /insights/query ──────────────────▶│
 │                  │   {question: "..."}   │                      │
 │                  │                       │                      │
 │                  │                       │─── assert_text_is_safe(question) ────▶│
 │                  │                       │                      │                 │
 │                  │                       │◀──── BLOCKED ────────────────────────│
 │                  │                       │      (ValidationError)                │
 │                  │                       │                      │
 │                  │◀─── HTTP 400 ─────────│                      │
 │                  │   {code: "CONTENT_SAFETY_BLOCKED", message}  │
 │                  │                       │                      │
 │◀─ Show Modal ────│                       │                      │
 │   "Content       │                       │                      │
 │   Flagged"       │                       │                      │
```

### 3. SQL Safety Violation Flow

> **Visual Diagram:** See [`diagrams/insights-sql-safety-violation-flow.png`](./diagrams/insights-sql-safety-violation-flow.png)

```
User            Frontend              Backend Route         Insights Service      OpenAI GPT-4o
 │                  │                       │                      │                    │
 │─── Ask Question ▶│                       │                      │                    │
 │                  │                       │                      │                    │
 │                  │─── POST /insights/query ──────────────────▶│                    │
 │                  │                       │                      │                    │
 │                  │                       │─── run_insight_query() ────────────────▶│
 │                  │                       │                      │                    │
 │                  │                       │                      │───── PHASE 1 ─────▶│
 │                  │                       │                      │                    │
 │                  │                       │                      │◀─── {"sql": "DELETE ..."}
 │                  │                       │                      │                    │
 │                  │                       │                      │─── _guard_sql() ───│
 │                  │                       │                      │    (detects DELETE)│
 │                  │                       │                      │                    │
 │                  │                       │◀─── ValidationError ─│                    │
 │                  │                       │     "Unsafe SQL"     │                    │
 │                  │                       │                      │                    │
 │                  │◀─── HTTP 422 ─────────│                      │                    │
 │                  │   {code: "UNSAFE_SQL"}│                      │                    │
 │                  │                       │                      │                    │
 │◀─ Display Error ─│                       │                      │                    │
 │   (inline msg)   │                       │                      │                    │
```

### 4. Voice Input Flow (Frontend Only)

> **Visual Diagram:** See [`diagrams/insights-voice-input-flow.png`](./diagrams/insights-voice-input-flow.png)

```
User            DashboardInsightPanel     Web Speech API
 │                      │                        │
 │─── Tap Mic ─────────▶│                        │
 │                      │                        │
 │                      │─── recognition.start() ─────────────────▶│
 │                      │                        │
 │                      │    voiceState = 'listening'
 │                      │    show pulsing ring  │
 │                      │                        │
 │──── Speak ──────────────────────────────────────────────────────▶│
 │    "How many guides?"│                        │
 │                      │                        │
 │                      │◀──── onresult ─────────│
 │                      │      event.results[0].transcript
 │                      │                        │
 │                      │    question.value = transcript
 │                      │    (updates input field)
 │                      │                        │
 │─── Tap Mic Again ───▶│                        │
 │    (stop)            │                        │
 │                      │                        │
 │                      │─── recognition.stop() ──────────────────▶│
 │                      │                        │
 │                      │◀──── onend ────────────│
 │                      │                        │
 │                      │─── submitQuestion() ───│
 │                      │    voiceState = 'processing'
 │                      │                        │
 │                      │─── POST /insights/query (continues to backend flow)
```

---

## Backend Flow

### Entry Point: `app/routes/insights.py`

```python
# FILE: backend/app/routes/insights.py

@router.post("/query", response_model=InsightResponse)
def query_insights(
    payload: InsightRequest,              # Step 1: Pydantic validation
    conn=Depends(get_db),                 # Step 2: DB connection injection
    _user: dict = Depends(require_authenticated_user),  # Step 3: Auth guard
):
    # Step 4: Trim and validate question
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail={...})
    
    # Step 5: Content safety check (pre-LLM)
    try:
        assert_text_is_safe(question, "question")
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail={"code": "CONTENT_SAFETY_BLOCKED", ...})
    
    # Step 6: Two-phase LLM + DB flow
    try:
        result = run_insight_query(conn, question)  # Main service call
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail={"code": "UNSAFE_SQL", ...})
    except OpenAIError as exc:
        raise HTTPException(status_code=503, detail={"code": "OPENAI_UNAVAILABLE", ...})
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail={"code": "DB_ERROR", ...})
    
    # Step 7: Return structured response
    return result
```

**Responsibilities:**
- Request validation (Pydantic)
- Authentication enforcement
- Content safety pre-check
- Service layer orchestration
- Error translation (exception → HTTP status + error code)

---

### Service Layer: `app/services/insights.py`

#### Function: `run_insight_query(conn, question) -> dict`

```python
# FILE: backend/app/services/insights.py

def run_insight_query(conn: Any, question: str) -> dict:
    """
    Two-phase LLM flow:
      Phase 1 — question + ERD → GPT-4o → safe SELECT SQL
      Phase 2 — SQL rows + question → GPT-4o → answer + chart + recommendations
    """
    # ══════════════════════════════════════════════════════════════════
    # STEP 1: Initialize OpenAI client
    # ══════════════════════════════════════════════════════════════════
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    client = OpenAI(api_key=api_key)
    
    # ══════════════════════════════════════════════════════════════════
    # PHASE 1: Natural Language → SQL
    # ══════════════════════════════════════════════════════════════════
    logger.info("Insights Phase 1: generating SQL for question: %r", question[:120])
    
    phase1_response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},  # Force JSON output
        messages=[
            {"role": "system", "content": _PHASE1_SYSTEM},  # Includes ERD schema
            {"role": "user", "content": question},
        ],
        temperature=0,      # Deterministic
        max_tokens=512,     # SQL queries are typically short
    )
    
    # Parse JSON response
    phase1_content = phase1_response.choices[0].message.content or "{}"
    phase1_json = json.loads(phase1_content)
    sql = phase1_json.get("sql", "").strip()
    
    if not sql:
        raise ValidationError("Phase 1 did not return a SQL query")
    
    # ══════════════════════════════════════════════════════════════════
    # SQL SAFETY GUARD: Block non-SELECT statements
    # ══════════════════════════════════════════════════════════════════
    _guard_sql(sql)  # Raises ValidationError if unsafe
    logger.info("Insights Phase 1 SQL: %s", sql[:300])
    
    # ══════════════════════════════════════════════════════════════════
    # STEP 2: Execute SQL against PostgreSQL
    # ══════════════════════════════════════════════════════════════════
    try:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchmany(_MAX_ROWS)]
    except Exception as exc:
        raise RuntimeError(f"Database query failed: {exc}") from exc
    
    logger.info("Insights query returned %d rows", len(rows))
    
    # ══════════════════════════════════════════════════════════════════
    # STEP 3: Enrich context for unassigned schedules (conditional)
    # ══════════════════════════════════════════════════════════════════
    enrichment = _enrich_unassigned_schedules(conn, rows, question)
    
    # ══════════════════════════════════════════════════════════════════
    # PHASE 2: SQL Rows → Insights (answer + chart + recommendations)
    # ══════════════════════════════════════════════════════════════════
    rows_payload = json.dumps(rows, default=str)
    
    user_message_parts = [
        f"Question: {question}",
        f"Query used: {sql}",
        f"Query results ({len(rows)} rows):\n{rows_payload}",
    ]
    
    # Inject enrichment context if available
    if enrichment:
        enrichment_payload = json.dumps(enrichment, default=str, indent=2)
        user_message_parts.append(f"\n**ENRICHED CONTEXT**:\n{enrichment_payload}\n...")
    
    user_message = "\n\n".join(user_message_parts)
    
    logger.info("Insights Phase 2: interpreting %d rows (enriched: %s)", len(rows), bool(enrichment))
    
    phase2_response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _PHASE2_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,    # Slightly creative for recommendations
        max_tokens=1536,    # Longer output for answer + recommendations
    )
    
    # Parse JSON response
    phase2_content = phase2_response.choices[0].message.content or "{}"
    phase2_json = json.loads(phase2_content)
    
    # ══════════════════════════════════════════════════════════════════
    # STEP 4: Return structured response
    # ══════════════════════════════════════════════════════════════════
    return {
        "question": question,
        "answer": phase2_json.get("answer", ""),
        "chart": phase2_json.get("chart"),
        "recommendations": phase2_json.get("recommendations", []),
        "sql_used": sql,
    }
```

---

#### Function: `_guard_sql(sql: str) -> None`

```python
# FILE: backend/app/services/insights.py

_BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|MERGE|GRANT|REVOKE|EXEC|EXECUTE|CALL)\b",
    re.IGNORECASE,
)

def _guard_sql(sql: str) -> None:
    """Raise ValidationError if the SQL contains any non-SELECT statements."""
    stripped = sql.strip()
    
    # Must start with SELECT or WITH (for CTEs)
    if not stripped.upper().startswith("SELECT") and not stripped.upper().startswith("WITH"):
        raise ValidationError(f"Generated query is not a SELECT statement: {stripped[:80]}")
    
    # Block dangerous keywords
    if _BLOCKED_KEYWORDS.search(stripped):
        raise ValidationError("Generated query contains disallowed keywords")
```

**Flow:**
1. Strip whitespace
2. Check if query starts with `SELECT` or `WITH` (Common Table Expression)
3. Regex search for blocked keywords (INSERT, UPDATE, DELETE, etc.)
4. Raise `ValidationError` if unsafe (caught by route handler → HTTP 422)

---

#### Function: `_enrich_unassigned_schedules(conn, rows, question) -> dict`

```python
# FILE: backend/app/services/insights.py

def _enrich_unassigned_schedules(conn: Any, rows: list[dict], question: str) -> dict:
    """
    If the question is about unassigned schedules and the results contain schedule IDs,
    check eligibility for each and return enriched context.
    """
    # Step 1: Detect if question is about unassigned schedules
    keywords = ["unassigned", "without guide", "no guide", "without assignment", "missing guide"]
    if not any(kw in question.lower() for kw in keywords):
        return {}  # No enrichment needed
    
    # Step 2: Extract schedule IDs from query results
    schedule_ids = []
    for row in rows:
        if "id" in row and isinstance(row["id"], int):
            schedule_ids.append(row["id"])
        elif "schedule_id" in row and isinstance(row["schedule_id"], int):
            schedule_ids.append(row["schedule_id"])
    
    if not schedule_ids:
        return {}  # No schedules to enrich
    
    logger.info("Enriching %d unassigned schedules with eligibility data", len(schedule_ids))
    
    # Step 3: Check eligibility for each schedule (limit to 10 for performance)
    enriched_schedules = []
    total_eligible = 0
    total_no_expertise = 0
    total_no_language = 0
    total_no_availability = 0
    
    for sched_id in schedule_ids[:10]:
        try:
            # Call guide assignment service
            eligible, reasons = guide_assignment.find_eligible_guides(conn, sched_id)
            
            enriched_schedules.append({
                "schedule_id": sched_id,
                "eligible_count": len(eligible),
                "eligible_guides": [
                    {
                        "id": g["id"],
                        "name": f"{g['first_name']} {g['last_name']}",
                        "rating": float(g.get("guide_rating") or 0),
                    }
                    for g in eligible[:3]  # Top 3 guides
                ],
                "reasons": reasons,
            })
            
            # Aggregate blocking reasons
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
    
    # Step 4: Build summary text
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
```

**Flow:**
1. Detect keywords in question ("unassigned", "without guide", etc.)
2. Extract schedule IDs from query results
3. For each schedule (max 10), call `guide_assignment.find_eligible_guides()`
4. Aggregate blocking reasons (expertise, language, availability)
5. Return enriched context with eligible guides + summary

---

### Content Safety: `app/services/content_moderation.py`

```python
# FILE: backend/app/services/content_moderation.py (existing service, reused)

def assert_text_is_safe(text: str, field_name: str) -> None:
    """
    Check text against Azure Content Safety API.
    Raises ValidationError if flagged.
    """
    if not os.getenv("CONTENT_SAFETY_ENABLED", "false").lower() == "true":
        return  # Skip if disabled
    
    # Call Azure Content Safety API
    # (Implementation details in existing service)
    # If flagged, raise ValidationError with message
    pass
```

**Integration Point:**
- Called by `app/routes/insights.py` before LLM processing
- If flagged, raises `ValidationError`
- Route handler catches and returns HTTP 400 with `CONTENT_SAFETY_BLOCKED` code

---

## Frontend Flow

### Component: `DashboardInsightPanel.vue`

#### State Management

```javascript
// FILE: frontend/src/components/DashboardInsightPanel.vue

const voiceState = ref('idle')  // State machine: idle | listening | processing | result
const question = ref('')        // User input (text or transcribed voice)
const result = ref(null)        // API response: {question, answer, chart, recommendations, sql_used}
const apiError = ref('')        // Error message for display
const showContentSafetyModal = ref(false)  // Content safety blocked popup
const showSql = ref(false)      // SQL collapsible toggle
```

#### State Machine Transitions

> **Visual Diagram:** See [`diagrams/insights-state-machine.png`](./diagrams/insights-state-machine.png)

```
┌──────┐
│ idle │ ◀──────────────────────────────────┐
└──┬───┘                                     │
   │                                         │
   │ User taps mic OR types + presses Enter  │
   │                                         │
   ▼                                         │
┌───────────┐                                │
│ listening │ (voice input only)             │
└─────┬─────┘                                │
      │                                      │
      │ User stops mic                       │
      │                                      │
      ▼                                      │
┌────────────┐                               │
│ processing │ ◀─────┐                       │
└──────┬─────┘       │                       │
       │             │                       │
       │ API success │ API error             │
       │             │ (not content safety)  │
       ▼             │                       │
   ┌────────┐        │                       │
   │ result │ ───────┘                       │
   └────┬───┘                                │
        │                                    │
        │ User clicks "Ask another question" │
        │                                    │
        └────────────────────────────────────┘

Note: Content safety errors show modal and reset to 'idle'
```

#### Voice Input Integration

```javascript
// FILE: frontend/src/components/DashboardInsightPanel.vue

// Check browser support
const speechSupported =
  typeof window !== 'undefined' &&
  ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)

// Initialize Web Speech API
let recognition = null
if (speechSupported) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.continuous = true      // Keep listening until stopped
  recognition.interimResults = true  // Show interim transcription
  recognition.lang = 'en-US'
  
  // Event: Transcription result
  recognition.onresult = (event) => {
    let transcript = ''
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript
    }
    question.value = transcript  // Update input field in real-time
  }
  
  // Event: Recognition ended
  recognition.onend = () => {
    if (voiceState.value === 'listening') {
      submitQuestion()  // Auto-submit on end
    }
  }
  
  // Event: Error occurred
  recognition.onerror = (event) => {
    if (event.error !== 'no-speech') {
      voiceState.value = 'idle'
    }
  }
}

// Cleanup on component unmount
onUnmounted(() => {
  recognition?.stop()
})
```

**Flow:**
1. User taps mic button
2. `toggleMic()` calls `recognition.start()`
3. `voiceState` → `'listening'` (shows pulsing red ring)
4. User speaks → `onresult` fires → updates `question.value`
5. User taps mic again → `recognition.stop()`
6. `onend` fires → calls `submitQuestion()`

---

#### Function: `submitQuestion()`

```javascript
// FILE: frontend/src/components/DashboardInsightPanel.vue

async function submitQuestion() {
  const q = question.value.trim()
  
  // Validate non-empty
  if (!q) {
    voiceState.value = 'idle'
    return
  }
  
  // Reset state
  voiceState.value = 'processing'
  result.value = null
  apiError.value = ''
  showSql.value = false
  
  try {
    // Call backend API
    const data = await postInsightQuery(q)
    
    // Success: display results
    result.value = data
    voiceState.value = 'result'
    
  } catch (err) {
    // Check for content safety block
    const code = err?.response?.data?.detail?.code ?? err?.detail?.code
    
    if (code === 'CONTENT_SAFETY_BLOCKED' || 
        (err?.status === 400 && JSON.stringify(err).includes('CONTENT_SAFETY_BLOCKED'))) {
      // Show modal popup
      showContentSafetyModal.value = true
    } else {
      // Show inline error message
      apiError.value =
        err?.response?.data?.detail?.message ??
        err?.message ??
        'Something went wrong. Please try again.'
    }
    
    voiceState.value = 'idle'
  }
}
```

**Flow:**
1. Validate question is non-empty
2. Set state to `'processing'` (shows spinner)
3. Call `postInsightQuery(question)` from `services/api.js`
4. On success: store result, transition to `'result'` state
5. On error:
   - If `CONTENT_SAFETY_BLOCKED`: show modal
   - Otherwise: show inline error message
   - Reset to `'idle'`

---

#### API Service: `frontend/src/services/api.js`

```javascript
// FILE: frontend/src/services/api.js

export async function postInsightQuery(question) {
  const response = await apiClient.post('/insights/query', {
    question: question
  })
  return response.data  // Returns InsightResponse object
}
```

**Integration:**
- Uses existing `apiClient` (Axios instance with auth interceptors)
- JWT token automatically attached via interceptor
- Returns: `{question, answer, chart, recommendations, sql_used}`

---

#### Chart Rendering

Frontend renders 6 chart types as **inline SVG** (no external chart libraries):

##### 1. Number Chart
```vue
<div v-if="result.chart.type === 'number'" class="...">
  <span class="text-7xl font-bold">
    {{ result.chart.data[0].value.toLocaleString() }}
  </span>
  <span class="text-lg">{{ result.chart.data[0].label }}</span>
</div>
```

##### 2. Bar Chart
```vue
<div v-else-if="result.chart.type === 'bar'" class="...">
  <div v-for="item in barChartData.items" :key="item.label">
    <span>{{ item.label }}</span>
    <div class="bar-container">
      <div class="bar" :style="{ width: item.pct }"></div>
    </div>
    <span>{{ item.value }}</span>
  </div>
</div>
```

**Computed Property:**
```javascript
const barChartData = computed(() => {
  const chart = result.value?.chart
  if (!chart || chart.type !== 'bar') return null
  
  const maxValue = Math.max(...chart.data.map(d => d.value), 1)
  return {
    items: chart.data.map(d => ({
      ...d,
      pct: `${Math.round((d.value / maxValue) * 100)}%`  // Scale to max
    })),
    maxValue
  }
})
```

##### 3. Line Chart
```vue
<svg :viewBox="`0 0 ${lineChartData.W} ${lineChartData.H}`">
  <!-- Grid lines -->
  <line v-for="g in lineChartData.gridLines" :key="g.y"
        :x1="padL" :y1="g.y" :x2="W" :y2="g.y" />
  
  <!-- Line path -->
  <path :d="lineChartData.pathD" stroke="#0284c7" />
  
  <!-- Data points -->
  <circle v-for="pt in lineChartData.points" :key="pt.x"
          :cx="pt.x" :cy="pt.y" r="4" />
</svg>
```

**Computed Property:**
```javascript
const lineChartData = computed(() => {
  const chart = result.value?.chart
  if (!chart || chart.type !== 'line') return null
  
  const W = 560, H = 160
  const padL = 40, padR = 16, padT = 12, padB = 28
  const chartW = W - padL - padR
  const chartH = H - padT - padB
  const maxVal = Math.max(...chart.data.map(d => d.value), 1)
  
  // Map data points to SVG coordinates
  const xOf = (i) => padL + (i / (chart.data.length - 1 || 1)) * chartW
  const yOf = (v) => padT + chartH - (v / maxVal) * chartH
  
  const points = chart.data.map((d, i) => ({
    x: xOf(i),
    y: yOf(d.value),
    v: d.value,
    label: d.label
  }))
  
  // Build SVG path
  const pathD = points.map((p, i) => 
    `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
  ).join(' ')
  
  return { W, H, padL, padB, points, pathD, gridLines }
})
```

##### 4. Donut Chart
```vue
<svg viewBox="0 0 160 160">
  <!-- Donut segments -->
  <path v-for="seg in donutData.segments" :key="seg.label"
        :d="seg.d" :fill="seg.color" />
  
  <!-- Center text (total) -->
  <text :x="cx" :y="cy">{{ donutData.total }}</text>
</svg>
```

**Computed Property:**
```javascript
const donutData = computed(() => {
  const chart = result.value?.chart
  if (!chart || chart.type !== 'donut') return null
  
  const total = chart.data.reduce((s, d) => s + d.value, 0) || 1
  const cx = 80, cy = 80, r = 60, innerR = 36
  const colors = ['#0284c7', '#7c3aed', '#059669', '#d97706', '#dc2626']
  
  let cumAngle = -Math.PI / 2  // Start at top
  const segments = chart.data.map((d, i) => {
    const angle = (d.value / total) * 2 * Math.PI
    const startAngle = cumAngle
    const endAngle = cumAngle + angle
    cumAngle = endAngle
    
    // Build SVG arc path (outer + inner arcs)
    const x1 = cx + r * Math.cos(startAngle)
    const y1 = cy + r * Math.sin(startAngle)
    const x2 = cx + r * Math.cos(endAngle)
    const y2 = cy + r * Math.sin(endAngle)
    const ix1 = cx + innerR * Math.cos(endAngle)
    const iy1 = cy + innerR * Math.sin(endAngle)
    const ix2 = cx + innerR * Math.cos(startAngle)
    const iy2 = cy + innerR * Math.sin(startAngle)
    const largeArc = angle > Math.PI ? 1 : 0
    
    return {
      d: `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} ` +
         `L ${ix1} ${iy1} A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix2} ${iy2} Z`,
      color: colors[i % colors.length],
      label: d.label,
      value: d.value,
      pct: Math.round((d.value / total) * 100)
    }
  })
  
  return { segments, cx, cy, total }
})
```

##### 5. List Chart
```vue
<ol v-else-if="result.chart.type === 'list'">
  <li v-for="(item, idx) in result.chart.data" :key="item.label">
    <span class="number-badge">{{ idx + 1 }}</span>
    <span>{{ item.label }}</span>
    <span class="value">{{ item.value }}</span>
  </li>
</ol>
```

##### 6. Comparison Chart
```vue
<div v-else-if="result.chart.type === 'comparison'" class="grid grid-cols-2">
  <div v-for="item in result.chart.data.slice(0, 2)" :key="item.label">
    <span class="text-4xl">{{ item.value }}</span>
    <span>{{ item.label }}</span>
  </div>
  
  <!-- Delta calculation -->
  <div class="col-span-2">
    <span>{{ deltaPercent }}% {{ deltaDirection }}</span>
  </div>
</div>
```

---

#### Recommendation Rendering

```vue
<div v-if="result.recommendations?.length">
  <p class="typo-card-label">Recommended Actions</p>
  
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
    <article v-for="rec in result.recommendations" :key="rec.title">
      <div class="flex items-start justify-between">
        <p class="font-semibold">{{ rec.title }}</p>
        <span class="badge" :class="badgeClasses(rec.action_type)">
          {{ badgeLabel(rec.action_type) }}
        </span>
      </div>
      <p class="mt-2">{{ rec.description }}</p>
    </article>
  </div>
</div>
```

**Badge Helper:**
```javascript
const ACTION_BADGE = {
  train: {
    bg: 'bg-blue-100 dark:bg-blue-900/40',
    text: 'text-blue-700 dark:text-blue-300',
    label: 'Train'
  },
  hire: {
    bg: 'bg-violet-100 dark:bg-violet-900/40',
    text: 'text-violet-700 dark:text-violet-300',
    label: 'Hire'
  },
  assign: {
    bg: 'bg-emerald-100 dark:bg-emerald-900/40',
    text: 'text-emerald-700 dark:text-emerald-300',
    label: 'Assign'
  },
  review: {
    bg: 'bg-amber-100 dark:bg-amber-900/40',
    text: 'text-amber-700 dark:text-amber-300',
    label: 'Review'
  }
}

function badgeClasses(actionType) {
  const b = ACTION_BADGE[actionType] ?? ACTION_BADGE.review
  return `${b.bg} ${b.text}`
}
```

---

## File Structure & Responsibilities

### Backend Files

```
backend/
├── app/
│   ├── routes/
│   │   └── insights.py                        # FastAPI endpoint
│   │       • POST /insights/query
│   │       • Request: InsightRequest (Pydantic)
│   │       • Response: InsightResponse (Pydantic)
│   │       • Auth: require_authenticated_user
│   │       • Content safety pre-check
│   │       • Error handling & HTTP status mapping
│   │
│   ├── services/
│   │   ├── insights.py                        # Two-phase LLM logic
│   │   │   • run_insight_query(conn, question)
│   │   │   • _guard_sql(sql)
│   │   │   • _enrich_unassigned_schedules(conn, rows, question)
│   │   │   • _PHASE1_SYSTEM (prompt with ERD schema)
│   │   │   • _PHASE2_SYSTEM (prompt with chart guidance)
│   │   │
│   │   ├── content_moderation.py             # Azure Content Safety
│   │   │   • assert_text_is_safe(text, field_name)
│   │   │
│   │   ├── guide_assignment.py               # Eligibility check (existing)
│   │   │   • find_eligible_guides(conn, schedule_id)
│   │   │   • Returns: (eligible_guides, blocking_reasons)
│   │   │
│   │   └── exceptions.py                      # Custom exceptions
│   │       • ValidationError
│   │
│   ├── db.py                                  # Database connection
│   │   • get_db() dependency (SQLAlchemy)
│   │
│   └── dependencies/
│       └── auth.py                            # Authentication
│           • require_authenticated_user()
│
└── docs/
    ├── FDR/
    │   └── FDR-005-ai-data-insights.md       # Requirements doc
    │
    ├── db/
    │   └── ERD.md                            # Database schema (used in Phase 1 prompt)
    │
    ├── INSIGHTS_USER_GUIDE.md                # User-facing documentation
    └── INSIGHTS_TECHNICAL_REFERENCE.md       # Developer documentation
```

### Frontend Files

```
frontend/
└── src/
    ├── components/
    │   └── DashboardInsightPanel.vue          # Main UI component
    │       • State machine (idle/listening/processing/result)
    │       • Web Speech API integration
    │       • 6 chart type renderers (inline SVG)
    │       • Recommendation cards
    │       • Content safety modal
    │       • SQL collapsible view
    │
    ├── services/
    │   └── api.js                             # API client
    │       • postInsightQuery(question)
    │       • Uses axios with JWT interceptor
    │
    └── views/
        └── DashboardView.vue                  # Parent view (admin dashboard)
            • Imports and renders DashboardInsightPanel
```

---

## Service Layer Deep Dive

### Service: `insights.py`

**Public Function:**
- `run_insight_query(conn, question) -> dict`

**Private Functions:**
- `_guard_sql(sql) -> None` — SQL safety validation
- `_enrich_unassigned_schedules(conn, rows, question) -> dict` — Eligibility enrichment

**Constants:**
- `_ERD_SCHEMA` — Database schema embedded in Phase 1 prompt
- `_PHASE1_SYSTEM` — System prompt for NL→SQL translation
- `_PHASE2_SYSTEM` — System prompt for insights generation
- `_BLOCKED_KEYWORDS` — Regex for unsafe SQL keywords
- `_MAX_ROWS` — Result row limit (100)

**Dependencies:**
- `OpenAI` — Python client for GPT-4o API
- `SQLAlchemy` — Database query execution
- `guide_assignment` — Eligibility check service
- `exceptions.ValidationError` — Custom exception

**LLM Configuration:**

| Phase | Model | Temperature | Max Tokens | Response Format |
|-------|-------|-------------|------------|-----------------|
| 1 (NL→SQL) | gpt-4o | 0 (deterministic) | 512 | JSON object |
| 2 (Insights) | gpt-4o | 0.3 (slightly creative) | 1536 | JSON object |

---

### Service: `content_moderation.py`

**Public Function:**
- `assert_text_is_safe(text, field_name) -> None`

**Behavior:**
- If `CONTENT_SAFETY_ENABLED=true`: Call Azure Content Safety API
- If `CONTENT_SAFETY_ENABLED=false`: No-op (pass-through)
- If flagged: Raise `ValidationError` with message

**Environment Variables:**
- `CONTENT_SAFETY_ENABLED` — Toggle (true/false)
- `CONTENT_SAFETY_ENDPOINT` — Azure endpoint URL
- `CONTENT_SAFETY_KEY` — Azure API key

---

### Service: `guide_assignment.py` (Existing, Reused)

**Public Function:**
- `find_eligible_guides(conn, schedule_id) -> tuple[list, list]`

**Returns:**
```python
(
    eligible_guides: [
        {"id": 1, "first_name": "John", "last_name": "Doe", "guide_rating": 4.8},
        ...
    ],
    blocking_reasons: [
        "NO_EXPERTISE_MATCH",
        "NO_LANGUAGE_MATCH",
        "NO_AVAILABILITY_MATCH"
    ]
)
```

**Logic:**
1. Fetch schedule details (tour, language, time)
2. Query all active guides
3. Filter by tour expertise (`guide_tour_types`)
4. Filter by language (`guide_languages`)
5. Check availability patterns and exceptions
6. Return eligible guides + reasons for ineligible ones

---

## API Request/Response Flow

### Request Structure

```http
POST /insights/query HTTP/1.1
Host: api.oceanarium.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "question": "How many unassigned schedules do I have?"
}
```

**Pydantic Model:**
```python
class InsightRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
```

---

### Response Structure (Success)

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "question": "How many unassigned schedules do I have?",
  "answer": "You have 12 unassigned schedules, representing 34% of all upcoming schedules. 7 have eligible guides available, while 5 are blocked by missing expertise.",
  "chart": {
    "type": "number",
    "title": "Unassigned Upcoming Schedules",
    "data": [
      {
        "label": "Unassigned",
        "value": 12
      }
    ]
  },
  "recommendations": [
    {
      "title": "Assign qualified guides",
      "description": "Sarah Johnson and Mike Chen are available for 7 schedules. Review and assign them to reduce unassigned count.",
      "action_type": "assign"
    },
    {
      "title": "Train existing guides",
      "description": "3 guides need Coral Reef Tour expertise to cover 5 remaining schedules. Schedule training sessions.",
      "action_type": "train"
    }
  ],
  "sql_used": "SELECT COUNT(*) AS unassigned FROM schedule WHERE guide_id IS NULL AND event_start_datetime > NOW() AND status NOT IN ('CANCELLED', 'COMPLETED')"
}
```

**Pydantic Models:**
```python
class ChartDataPoint(BaseModel):
    label: str
    value: float

class ChartData(BaseModel):
    type: str  # number|bar|line|donut|list|comparison
    title: str
    data: list[ChartDataPoint]

class Recommendation(BaseModel):
    title: str
    description: str
    action_type: str  # train|hire|assign|review

class InsightResponse(BaseModel):
    question: str
    answer: str
    chart: ChartData | None = None
    recommendations: list[Recommendation] = []
    sql_used: str = ""
```

---

### Error Responses

#### 1. Content Safety Blocked
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": {
    "code": "CONTENT_SAFETY_BLOCKED",
    "message": "Your question contains inappropriate content and cannot be processed."
  }
}
```

#### 2. Empty Question
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": {
    "code": "EMPTY_QUESTION",
    "message": "Question cannot be empty"
  }
}
```

#### 3. Unsafe SQL
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": {
    "code": "UNSAFE_SQL",
    "message": "Generated query contains disallowed keywords"
  }
}
```

#### 4. OpenAI Unavailable
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": {
    "code": "OPENAI_UNAVAILABLE",
    "message": "AI service is temporarily unavailable. Please try again later."
  }
}
```

#### 5. Database Error
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "detail": {
    "code": "DB_ERROR",
    "message": "Database query failed: syntax error near 'FORM'"
  }
}
```

---

## Error Handling Flow

> **Visual Diagram:** See [`diagrams/insights-error-propagation.png`](./diagrams/insights-error-propagation.png)

### Backend Error Propagation

```
Service Layer                 Route Handler                   HTTP Response
─────────────────────────────────────────────────────────────────────────────

ValidationError
  "Unsafe SQL"        ───────▶  catch ValidationError  ───────▶  HTTP 422
                                detail: {                        UNSAFE_SQL
                                  code: "UNSAFE_SQL"
                                }

OpenAIError           ───────▶  catch OpenAIError      ───────▶  HTTP 503
                                detail: {                        OPENAI_UNAVAILABLE
                                  code: "OPENAI_UNAVAILABLE"
                                }

RuntimeError          ───────▶  catch RuntimeError     ───────▶  HTTP 500
  "DB query failed"             detail: {                        DB_ERROR
                                  code: "DB_ERROR"
                                }

ValidationError       ───────▶  catch ValidationError  ───────▶  HTTP 400
  (from content safety)         (in pre-check block)             CONTENT_SAFETY_BLOCKED
                                detail: {
                                  code: "CONTENT_SAFETY_BLOCKED"
                                }
```

### Frontend Error Handling

```javascript
try {
  const data = await postInsightQuery(question)
  result.value = data
  voiceState.value = 'result'
  
} catch (err) {
  const code = err?.response?.data?.detail?.code
  
  if (code === 'CONTENT_SAFETY_BLOCKED') {
    // Special handling: modal popup
    showContentSafetyModal.value = true
    
  } else {
    // Generic error: inline message
    apiError.value = err?.response?.data?.detail?.message ?? 
                     err?.message ?? 
                     'Something went wrong.'
  }
  
  voiceState.value = 'idle'
}
```

---

## Data Enrichment Flow

> **Visual Diagram:** See [`diagrams/insights-enrichment-flow.png`](./diagrams/insights-enrichment-flow.png)

### Trigger Conditions

Enrichment activates when:
1. Question contains keywords: `["unassigned", "without guide", "no guide", "without assignment", "missing guide"]`
2. Query results contain schedule IDs (columns: `id` or `schedule_id`)

### Enrichment Process

```
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 1 SQL Results                                                │
│  [                                                                   │
│    {id: 101, tour_name: "Coral Reef", language: "en", ...},        │
│    {id: 102, tour_name: "Deep Dive", language: "es", ...},         │
│    ...                                                              │
│  ]                                                                  │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ Extract schedule IDs
                       ▼
              ┌────────────────┐
              │ [101, 102, ...] │
              └────────┬───────┘
                       │
                       │ For each schedule (max 10)
                       ▼
    ┌──────────────────────────────────────────────────────┐
    │  guide_assignment.find_eligible_guides(conn, 101)    │
    │                                                       │
    │  Returns:                                            │
    │  • eligible_guides: [                                │
    │      {id: 5, name: "Sarah Johnson", rating: 4.8},   │
    │      {id: 7, name: "Mike Chen", rating: 4.5}        │
    │    ]                                                 │
    │  • reasons: ["NO_EXPERTISE_MATCH"]                  │
    └──────────────────────┬───────────────────────────────┘
                           │
                           │ Aggregate
                           ▼
           ┌───────────────────────────────────┐
           │  Enrichment Context               │
           │  {                                │
           │    schedules: [                   │
           │      {                            │
           │        schedule_id: 101,          │
           │        eligible_count: 2,         │
           │        eligible_guides: [         │
           │          {id: 5, name: "Sarah..."}│
           │        ],                         │
           │        reasons: ["NO_EXPERTISE"]  │
           │      },                           │
           │      ...                          │
           │    ],                             │
           │    enrichment_summary:            │
           │      "7 schedules have eligible   │
           │       guides; 5 blocked by        │
           │       missing expertise"          │
           │  }                                │
           └──────────┬────────────────────────┘
                      │
                      │ Inject into Phase 2 prompt
                      ▼
        ┌────────────────────────────────────────┐
        │  Phase 2 User Message                  │
        │                                        │
        │  Question: ...                         │
        │  Query used: ...                       │
        │  Query results: ...                    │
        │                                        │
        │  **ENRICHED CONTEXT**:                 │
        │  {schedules: [...], summary: "..."}    │
        │                                        │
        │  Use this enrichment to:               │
        │  • Recommend 'assign' with guide names │
        │  • Recommend 'train' for expertise gaps│
        │  • Recommend 'hire' for language gaps  │
        └────────────────────────────────────────┘
```

### Enrichment Impact on Recommendations

**Without Enrichment:**
```json
{
  "recommendations": [
    {
      "title": "Review unassigned schedules",
      "description": "Check guide availability and qualifications for these schedules.",
      "action_type": "review"
    }
  ]
}
```

**With Enrichment:**
```json
{
  "recommendations": [
    {
      "title": "Assign qualified guides",
      "description": "Sarah Johnson (4.8★) and Mike Chen (4.5★) are available for schedules #101, #103, #107. Assign them immediately.",
      "action_type": "assign"
    },
    {
      "title": "Train existing guides",
      "description": "Tom Williams and Lisa Brown need Coral Reef Tour expertise to cover schedules #102, #105. Schedule training this week.",
      "action_type": "train"
    }
  ]
}
```

---

## Integration Points

### 1. OpenAI GPT-4o API

**Endpoint:** `https://api.openai.com/v1/chat/completions`

**Authentication:** Bearer token via `OPENAI_API_KEY` env var

**Usage:**
- Phase 1: ~500-800 tokens per request (prompt + response)
- Phase 2: ~1500-3000 tokens per request (prompt + response)
- Model: `gpt-4o`
- Pricing: ~$5/million input tokens, ~$15/million output tokens (as of 2026)

**Error Handling:**
- Network errors → HTTP 503 (`OPENAI_UNAVAILABLE`)
- Malformed JSON response → HTTP 500 (`PARSE_ERROR`)
- Rate limits → Exponential backoff (not implemented in v1.0)

---

### 2. Azure Content Safety API

**Endpoint:** Configured via `CONTENT_SAFETY_ENDPOINT` env var

**Authentication:** API key via `CONTENT_SAFETY_KEY` env var

**Usage:**
- Called once per question (pre-LLM)
- Checks for: hate speech, self-harm, violence, NSFW content
- Configurable severity thresholds

**Error Handling:**
- Flagged content → HTTP 400 (`CONTENT_SAFETY_BLOCKED`)
- API unavailable → Allow request through (fail-open behavior)

---

### 3. PostgreSQL Database

**Connection:** Via SQLAlchemy `get_db()` dependency

**Access Pattern:**
- Read-only (SELECT queries only)
- No transaction management needed (single query per request)
- Row limit: 100 rows (performance + LLM context window)

**Tables Accessed:**
- `schedule` (primary)
- `guides`, `tours`, `reservations`, `tickets`
- `guide_tour_types`, `guide_languages`, `languages`
- `availability_patterns`, `availability_slots`, `availability_exceptions`
- `surveys`, `tour_assignment_logs`

**Error Handling:**
- Query syntax errors → HTTP 500 (`DB_ERROR`)
- Connection timeouts → HTTP 500 (`DB_ERROR`)

---

### 4. Guide Assignment Service

**Function:** `guide_assignment.find_eligible_guides(conn, schedule_id)`

**Purpose:** Check which guides can be assigned to a schedule

**Returns:**
```python
(
    eligible_guides: list[dict],  # {id, first_name, last_name, guide_rating}
    blocking_reasons: list[str]   # ["NO_EXPERTISE_MATCH", "NO_LANGUAGE_MATCH", ...]
)
```

**Performance:**
- ~50-100ms per schedule check (depends on guide count)
- Limited to 10 schedules per enrichment to keep latency under 1s

---

## Performance Characteristics

### Latency Breakdown (Typical Request)

```
Component                          Time (ms)    Percentage
─────────────────────────────────────────────────────────
FastAPI request validation         10-20        0.2%
JWT authentication check           20-40        0.5%
Content Safety API call            150-300      3%
Phase 1 (GPT-4o NL→SQL)           2000-4000    40%
PostgreSQL query execution         50-500       5%
Enrichment (if triggered)          100-300      3%
Phase 2 (GPT-4o insights)         3000-5000    50%
Response serialization             10-20        0.2%
─────────────────────────────────────────────────────────
TOTAL                              5500-10000   100%
```

### Bottlenecks

1. **Phase 2 LLM call** (50% of latency)
   - Mitigation: Stream response (not implemented in v1.0)
   
2. **Phase 1 LLM call** (40% of latency)
   - Mitigation: Cache common queries (not implemented in v1.0)
   
3. **Complex SQL queries** (5% of latency)
   - Mitigation: Read replica, query optimization

---

## Security Considerations

### 1. Authentication & Authorization
- Endpoint requires valid JWT token
- Admin-only access (Dashboard is admin-scoped)
- No per-question authorization (all admins have same access)

### 2. Input Validation
- Question length: 1-500 characters
- Content safety moderation (Azure)
- SQL injection prevention (LLM-generated, validated)

### 3. SQL Safety
- Regex guard for DDL/DML keywords
- Must start with SELECT or WITH
- No user input directly interpolated

### 4. Data Exposure
- Only queried data sent to OpenAI
- No full database dump
- No credentials or passwords in context

### 5. Rate Limiting
- Not implemented in v1.0
- Recommended: 10 queries/minute per user

---

## Testing Checklist

### Unit Tests
- [ ] `_guard_sql()` — Test blocked keywords, SELECT validation
- [ ] `_enrich_unassigned_schedules()` — Test keyword detection, ID extraction
- [ ] Request validation — Test empty question, length limits
- [ ] Error mapping — Test all exception types

### Integration Tests
- [ ] End-to-end flow with test database
- [ ] Mock OpenAI responses for deterministic testing
- [ ] Content safety bypass in test environment
- [ ] All 6 chart types render correctly

### Manual Test Cases
- [ ] Simple count: "How many guides?"
- [ ] Multi-table join: "Which tours have unassigned schedules?"
- [ ] Time filter: "Bookings this month"
- [ ] Enrichment trigger: "Unassigned schedules without guide"
- [ ] Voice input (Chrome/Edge)
- [ ] Content safety block
- [ ] OpenAI unavailable (disconnect network)
- [ ] Invalid SQL from LLM (inject bad prompt)

---

## Monitoring & Observability

### Key Metrics to Track

```python
# Request metrics
insights_requests_total{status="success|error"}
insights_request_duration_seconds{phase="1|2"}

# Error metrics
insights_errors_total{error_code="CONTENT_SAFETY_BLOCKED|UNSAFE_SQL|..."}

# LLM metrics
openai_api_calls_total{phase="1|2"}
openai_api_latency_seconds{phase="1|2"}
openai_api_cost_usd

# Enrichment metrics
insights_enrichment_triggered_total
insights_enrichment_schedules_checked

# Chart type distribution
insights_chart_type_total{type="number|bar|line|donut|list|comparison"}
```

### Logging Strategy

```python
logger.info("Insights Phase 1: generating SQL for question: %r", question[:120])
logger.info("Insights Phase 1 SQL: %s", sql[:300])
logger.info("Insights query returned %d rows", len(rows))
logger.info("Enriching %d unassigned schedules with eligibility data", len(schedule_ids))
logger.info("Insights Phase 2: interpreting %d rows (enriched: %s)", len(rows), bool(enrichment))
logger.error("OpenAI error during insights query: %s", exc)
logger.warning("Could not check eligibility for schedule %d: %s", sched_id, exc)
```

---

## Deployment Considerations

### Environment Variables Required

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (content safety)
CONTENT_SAFETY_ENABLED=true
CONTENT_SAFETY_ENDPOINT=https://...contentmoderator.azure.com/
CONTENT_SAFETY_KEY=...

# Database (existing)
DATABASE_URL=postgresql://...
```

### Infrastructure Requirements

- **Compute:** No special requirements (standard FastAPI deployment)
- **Network:** Outbound HTTPS to api.openai.com and Azure (if enabled)
- **Database:** Read-only access sufficient (consider read replica)
- **Secrets Management:** Store API keys in secret manager (AWS Secrets Manager, Azure Key Vault, etc.)

### Cost Estimation

**LLM Costs (GPT-4o):**
- Avg tokens per request: ~3000 total (input + output)
- Cost per request: ~$0.03
- 1000 requests/day: ~$30/day = $900/month

**Azure Content Safety:**
- Cost per request: ~$0.001
- 1000 requests/day: ~$1/day = $30/month

**Total:** ~$930/month for 1000 daily queries

---

## Quick Reference

### Key Endpoints
- `POST /insights/query` — Main endpoint

### Key Files (Backend)
- `app/routes/insights.py` — Route handler
- `app/services/insights.py` — Two-phase LLM logic
- `app/services/content_moderation.py` — Content safety
- `app/services/guide_assignment.py` — Eligibility check

### Key Files (Frontend)
- `frontend/src/components/DashboardInsightPanel.vue` — UI component
- `frontend/src/services/api.js` — API client

### Key Functions
- `run_insight_query(conn, question)` — Main service function
- `_guard_sql(sql)` — SQL safety validator
- `_enrich_unassigned_schedules(conn, rows, question)` — Enrichment
- `submitQuestion()` — Frontend submission handler

### Error Codes
- `CONTENT_SAFETY_BLOCKED` (400)
- `EMPTY_QUESTION` (422)
- `UNSAFE_SQL` (422)
- `OPENAI_UNAVAILABLE` (503)
- `DB_ERROR` (500)

### Chart Types
- `number`, `bar`, `line`, `donut`, `list`, `comparison`

### Action Types
- `train`, `hire`, `assign`, `review`

---

**End of Technical Architecture Documentation**
