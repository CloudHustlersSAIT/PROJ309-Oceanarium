# AI Data Insights - Technical Reference

**Version:** 1.0  
**Last Updated:** 2026-04-07  
**Status:** Production

---

## Overview

Natural-language query interface for operational data analysis. Two-phase LLM pipeline (NL→SQL→Insights) using OpenAI GPT-4o with read-only database access.

**Core Flow:**
```
User Question → Content Safety Check → GPT-4o (Phase 1) → SQL Generation → 
PostgreSQL Query → Eligibility Enrichment → GPT-4o (Phase 2) → 
Answer + Chart + Recommendations
```

---

## Architecture

### Tech Stack
- **LLM:** OpenAI GPT-4o (`gpt-4o` model)
- **Content Moderation:** Azure Content Safety (optional, toggle via `CONTENT_SAFETY_ENABLED`)
- **Database:** PostgreSQL (read-only, SELECT only)
- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Vue 3 + Composition API
- **Voice Input:** Web Speech API (browser-native, progressive enhancement)

### File Structure
```
backend/
├── app/
│   ├── routes/insights.py          # FastAPI endpoint
│   ├── services/insights.py        # Two-phase LLM logic
│   └── services/content_moderation.py  # Azure Content Safety integration
frontend/
└── src/
    └── components/DashboardInsightPanel.vue  # UI component
```

---

## API Specification

### Endpoint: `POST /insights/query`

**Authentication:** Required (JWT via `require_authenticated_user`)  
**Rate Limiting:** None (v1.0)  
**Timeout:** Default FastAPI timeout (~30s)

#### Request
```json
{
  "question": "string (1-500 chars, required)"
}
```

#### Response (200 OK)
```json
{
  "question": "string",
  "answer": "string",
  "chart": {
    "type": "number|bar|line|donut|list|comparison",
    "title": "string",
    "data": [
      { "label": "string", "value": number }
    ]
  },
  "recommendations": [
    {
      "title": "string",
      "description": "string",
      "action_type": "train|hire|assign|review"
    }
  ],
  "sql_used": "string"
}
```

#### Error Responses
| HTTP | Code | Trigger | Retry? |
|------|------|---------|--------|
| 400 | `CONTENT_SAFETY_BLOCKED` | Azure Content Safety flagged input | No (rephrase) |
| 422 | `EMPTY_QUESTION` | Empty/whitespace-only question | No |
| 422 | `UNSAFE_SQL` | Generated SQL contains DDL/DML | No (report bug) |
| 503 | `OPENAI_UNAVAILABLE` | OpenAI API unreachable | Yes (backoff) |
| 500 | `DB_ERROR` | PostgreSQL query failed | Maybe |
| 500 | `PARSE_ERROR` | GPT-4o returned malformed JSON | Yes (retry) |

---

## Implementation Details

### Phase 1: NL → SQL Translation

**Model Config:**
```python
model="gpt-4o"
response_format={"type": "json_object"}
temperature=0
max_tokens=512
```

**System Prompt:** Includes full ERD schema (tables, columns, relationships). Instructs model to:
- Return only `SELECT` statements
- Use only columns present in schema
- Limit results to 100 rows
- Never invent columns

**Output Schema:**
```json
{ "sql": "SELECT ..." }
```

**SQL Safety Guard:**
```python
# Regex check for blocked keywords
_BLOCKED_KEYWORDS = r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|MERGE|GRANT|REVOKE|EXEC|EXECUTE|CALL)\b"

# Query must start with SELECT or WITH (CTE)
if not stripped.upper().startswith(("SELECT", "WITH")):
    raise ValidationError(...)
```

### Phase 2: SQL Results → Insights

**Model Config:**
```python
model="gpt-4o"
response_format={"type": "json_object"}
temperature=0.3  # Slightly creative for recommendations
max_tokens=1536
```

**Input Context:**
- Original question
- SQL query used
- Query results (up to 100 rows, JSON-serialized)
- **Enrichment data** (for unassigned schedule queries only)

**Enrichment Logic:**
When question contains keywords like "unassigned", "without guide", "no guide":
1. Extract schedule IDs from query results
2. For each schedule (max 10), call `guide_assignment.find_eligible_guides()`
3. Collect eligibility reasons: `NO_EXPERTISE_MATCH`, `NO_LANGUAGE_MATCH`, `NO_AVAILABILITY_MATCH`
4. Inject enrichment into Phase 2 prompt with specific instructions

**Output Schema:**
```json
{
  "answer": "string (1-3 sentences)",
  "chart": {
    "type": "number|bar|line|donut|list|comparison",
    "title": "string",
    "data": [{"label": "string", "value": number}]
  },
  "recommendations": [
    {
      "title": "string",
      "description": "string",
      "action_type": "train|hire|assign|review"
    }
  ]
}
```

---

## Chart Types

Frontend renders 6 chart types as inline SVG:

| Type | Use Case | Data Structure | Frontend Renderer |
|------|----------|----------------|-------------------|
| `number` | Single KPI | `[{label, value}]` (1 item) | Large centered number |
| `bar` | Multi-item comparison | `[{label, value}, ...]` | Horizontal bars (max % scaled) |
| `line` | Time series | `[{label, value}, ...]` (ordered) | SVG path with grid lines |
| `donut` | Proportional breakdown | `[{label, value}, ...]` | SVG arcs (percentage-based) |
| `list` | Ranking or details | `[{label, value}, ...]` | Numbered list |
| `comparison` | Two-value contrast | `[{label, value}, {label, value}]` | Side-by-side + delta % |

**Chart Selection Logic:** Performed by GPT-4o in Phase 2 based on data shape and question intent.

---

## Security & Safety

### 1. Content Safety Moderation
```python
# backend/app/services/content_moderation.py
assert_text_is_safe(question, "question")
```
- Pre-LLM screening via Azure Content Safety
- Configurable: `CONTENT_SAFETY_ENABLED=true|false`
- Blocks NSFW, hate speech, violence, self-harm per Azure policies
- Returns HTTP 400 with `CONTENT_SAFETY_BLOCKED` code

### 2. SQL Injection Prevention
- No user input directly interpolated into SQL
- All SQL generated by LLM, validated with regex before execution
- Parameterized execution via SQLAlchemy `text()` (no user params in v1.0)

### 3. Read-Only Database Access
- Uses existing `get_db()` dependency (standard connection pool)
- No special DB user in v1.0 (relies on SQL safety guard)
- Row limit: 100 rows per query

### 4. Authentication & Authorization
- Endpoint protected by `require_authenticated_user` dependency
- Admin-only (Dashboard is admin-scoped)
- No role-based fine-tuning in v1.0

### 5. Data Exposure
**Sent to OpenAI:**
- Question text (max 500 chars)
- Database schema metadata (table/column names)
- Query results (max 100 rows, JSON)

**NOT sent to OpenAI:**
- Full database dump
- User credentials/passwords
- Payment information
- Data from non-queried tables

---

## Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
CONTENT_SAFETY_ENABLED=true  # Default: false
CONTENT_SAFETY_ENDPOINT=https://...
CONTENT_SAFETY_KEY=...
```

### Model Parameters
Hardcoded in `backend/app/services/insights.py`:
```python
_MAX_ROWS = 100  # Result row limit
_PHASE1_SYSTEM = "..."  # Includes ERD schema
_PHASE2_SYSTEM = "..."  # Includes chart type guidance
```

---

## Frontend Implementation

### Component: `DashboardInsightPanel.vue`

**State Machine:**
```
idle → listening → processing → result
  ↑                               ↓
  └──────── (ask another) ────────┘
```

**Voice Input:**
- Uses Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`)
- Continuous recognition with interim results
- Auto-submits on recognition end
- Graceful degradation: hides mic button if unsupported

**Error Handling:**
- `CONTENT_SAFETY_BLOCKED` → Modal popup
- All other errors → Inline error message
- API errors displayed with message from `detail.message`

**Chart Rendering:**
- All charts rendered as inline SVG (no external libs)
- Responsive: adapts to container width
- Dark mode support via Tailwind classes
- Computed properties for each chart type

---

## Database Schema Access

### Tables Used (Read-Only)
```sql
-- Core operational data
schedule, guides, tours, reservations, tickets

-- Guide capabilities
guide_tour_types, guide_languages, languages

-- Availability
availability_patterns, availability_slots, availability_exceptions

-- Feedback & history
surveys, tour_assignment_logs

-- System tables (rarely queried)
users, notifications, poll_execution, sync_logs
```

### ERD Context Injection
Full schema embedded in Phase 1 system prompt (`_ERD_SCHEMA` constant):
- Table names
- Column names + types
- Foreign key relationships
- Domain notes (e.g., "schedule.status values", "expertise stored in guide_tour_types")

---

## Performance Considerations

### Latency Breakdown (Typical)
```
Content Safety:     ~200ms
Phase 1 (GPT-4o):   ~2-4s
PostgreSQL Query:   ~50-500ms (depends on query complexity)
Enrichment:         ~100-300ms (if triggered)
Phase 2 (GPT-4o):   ~3-5s
───────────────────────────
Total:              ~5-10s
```

### Optimization Opportunities
- [ ] Cache common queries (e.g., "How many guides?")
- [ ] Stream Phase 2 response (LLM streaming API)
- [ ] Parallel Phase 1 + enrichment (speculative execution)
- [ ] Dedicated read-replica for insights queries
- [ ] Rate limiting per user

---

## Testing Strategy

### Unit Tests
- `services/insights.py`: Mock OpenAI responses, test SQL guard
- `routes/insights.py`: Mock service layer, test error handling

### Integration Tests
- End-to-end with test database + OpenAI API (use `gpt-4o-mini` for cost)
- Content safety bypass: `CONTENT_SAFETY_ENABLED=false`

### Manual Test Cases
1. Simple count query: "How many guides?"
2. Multi-table join: "Which tours have unassigned schedules?"
3. Time-based filter: "Bookings this month"
4. Enrichment trigger: "Unassigned schedules without guide"
5. Chart type coverage: Test all 6 chart types render correctly
6. Error scenarios: Empty question, content safety block, OpenAI down

---

## Monitoring & Logging

### Key Metrics
- **Request rate:** Insights queries per minute
- **Latency:** P50, P95, P99 response times
- **Error rate:** 4xx/5xx by error code
- **LLM cost:** OpenAI API spend per day
- **Cache hit rate:** (if caching implemented)

### Log Events
```python
logger.info("Insights Phase 1: generating SQL for question: %r", question[:120])
logger.info("Insights Phase 1 SQL: %s", sql[:300])
logger.info("Insights query returned %d rows", len(rows))
logger.info("Insights Phase 2: interpreting %d rows (enriched: %s)", len(rows), bool(enrichment))
```

### Error Tracking
- Sentry/similar for LLM parsing errors
- Alert on sustained OpenAI 503s
- Monitor for SQL safety violations (should be rare)

---

## Limitations & Future Work

### Current Limitations (v1.0)
- No query history or saved insights
- No multi-turn conversational context
- No scheduled/automated insights
- No export (CSV, PDF)
- No fine-tuned model (uses base GPT-4o)
- No streaming response (full response wait)
- No caching layer
- No rate limiting per user

### Roadmap Considerations
- [ ] Persistent query history table
- [ ] Conversational memory (Redis-backed context)
- [ ] Scheduled insight reports (daily/weekly email)
- [ ] Export API (CSV, PDF generation)
- [ ] Fine-tuned model on domain-specific queries
- [ ] Streaming LLM response (chunked answer)
- [ ] Redis cache for common queries (TTL: 5 min)
- [ ] User-level rate limiting (10 queries/min)
- [ ] Guide-facing insights (filtered dataset)

---

## Troubleshooting

### Debug Workflow
1. Check `OPENAI_API_KEY` is set and valid
2. Review logs for Phase 1/2 LLM responses
3. Inspect `sql_used` in API response
4. Test SQL manually in PostgreSQL client
5. Verify enrichment triggered (logs: "Enriching N schedules")
6. Check Content Safety config if questions blocked

### Common Issues

**Issue:** GPT-4o generates SQL with non-existent columns  
**Cause:** Schema in `_ERD_SCHEMA` outdated  
**Fix:** Update ERD context in `backend/app/services/insights.py`

**Issue:** Chart renders incorrectly  
**Cause:** GPT-4o returned wrong data shape for chart type  
**Fix:** Improve Phase 2 system prompt with examples

**Issue:** High latency (>15s)  
**Cause:** Complex query or large result set  
**Fix:** Add query timeout, optimize SQL, or cache results

**Issue:** Content safety false positives  
**Cause:** Azure Content Safety overly strict  
**Fix:** Disable for testing (`CONTENT_SAFETY_ENABLED=false`) or adjust Azure policy

---

## API Integration Example

### cURL
```bash
curl -X POST https://api.oceanarium.com/insights/query \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many unassigned schedules?"}'
```

### Python (requests)
```python
import requests

response = requests.post(
    "https://api.oceanarium.com/insights/query",
    headers={"Authorization": f"Bearer {jwt_token}"},
    json={"question": "How many unassigned schedules?"}
)

if response.status_code == 200:
    data = response.json()
    print(f"Answer: {data['answer']}")
    print(f"Chart type: {data['chart']['type']}")
    print(f"SQL used: {data['sql_used']}")
elif response.status_code == 400:
    print(f"Content blocked: {response.json()['detail']['message']}")
```

### JavaScript (Axios)
```javascript
const response = await axios.post('/insights/query', {
  question: 'How many unassigned schedules?'
}, {
  headers: { Authorization: `Bearer ${jwtToken}` }
});

console.log(response.data.answer);
console.log(response.data.chart);
```

---

## References

- **FDR:** `backend/docs/FDR/FDR-005-ai-data-insights.md` (full requirements doc)
- **ERD:** `backend/docs/db/ERD.md` (database schema)
- **OpenAI Docs:** https://platform.openai.com/docs/guides/structured-outputs
- **Azure Content Safety:** https://learn.microsoft.com/azure/ai-services/content-safety/

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-07 | Initial release: two-phase LLM pipeline, 6 chart types, 4 action types, enrichment for unassigned schedules |

---

## Quick Reference

**Key Files:**
- Service: `backend/app/services/insights.py`
- Route: `backend/app/routes/insights.py`
- Frontend: `frontend/src/components/DashboardInsightPanel.vue`

**Key Functions:**
- `run_insight_query(conn, question)` - Main two-phase flow
- `_guard_sql(sql)` - SQL safety validator
- `_enrich_unassigned_schedules(conn, rows, question)` - Eligibility enrichment

**Environment:**
- `OPENAI_API_KEY` (required)
- `CONTENT_SAFETY_ENABLED` (optional, default: false)

**Test Command:**
```bash
# Backend unit tests
pytest backend/tests/test_insights.py -v

# Manual test via API
curl -X POST http://localhost:8000/insights/query \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"question": "How many guides?"}'
```
