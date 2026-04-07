# [FDR-005] AI Data Insights Panel

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | FDR-005                |
| **Version**      | 1.0                    |
| **Status**       | Approved               |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-04-07             |
| **Last Updated** | 2026-04-07             |

---

## 1. Purpose

Operations staff need quick, ad-hoc answers about scheduling health without leaving the dashboard or writing SQL. Questions like "How many upcoming schedules have no guide assigned?" or "Which tours have the most cancellations this month?" require cross-table joins that are impractical to answer through the existing KPI cards alone.

This feature adds a natural-language query panel to the Dashboard that translates a spoken or typed question into a safe SQL query (via OpenAI GPT-4o), executes it against the live database, and returns a structured answer - a text explanation, an AI-selected chart, and actionable recommendations (e.g. train guides, hire new staff, assign existing ones).

## 2. Scope

### In Scope

- Natural-language question input (typed or voice via Web Speech API)
- Two-phase OpenAI GPT-4o flow: NL -> SQL (Phase 1), rows -> answer + chart + recommendations (Phase 2)
- SELECT-only SQL guard: any generated query containing DDL or DML keywords is rejected before execution
- Azure Content Safety moderation on the question input: blocked questions return a distinct error code (`CONTENT_SAFETY_BLOCKED`)
- Six AI-selected chart types rendered as inline SVG: `number`, `bar`, `line`, `donut`, `list`, `comparison`
- Actionable recommendation cards with color-coded action types: `train`, `hire`, `assign`, `review`
- Four animated voice states in the UI: `idle`, `listening`, `processing`, `result`
- Content safety blocked popup modal in the frontend
- Admin-only feature (Dashboard is admin-scoped)

### Out of Scope

- Persistent query history or saved insights
- Guide-facing insights (guide dashboard not included)
- Write operations (INSERT, UPDATE, DELETE) via the AI query
- Fine-tuning or custom model training
- Export of results to CSV or PDF
- Multi-turn conversational context (each question is independent)

## 3. Actors

| Actor | Description |
|-------|-------------|
| **Admin** | Staff member who submits questions and views AI-generated answers on the Dashboard |
| **OpenAI GPT-4o** | External LLM that translates NL questions to SQL and interprets query results |
| **Azure Content Safety** | External moderation service that screens question text before LLM processing |
| **PostgreSQL** | Live read-only data source for query execution |

## 4. Functional Requirements

### FR-1: Natural-Language Question Input

- **Description**: The admin can type a question or use voice input on the Dashboard to ask about operational data.
- **Input**: Free-text string (1-500 characters) from a text field or Web Speech API transcription
- **Output**: Question string sent to `POST /insights/query`
- **Business Rules**:
  - Question must be non-empty
  - Voice recording starts and stops by tapping the mic button
  - Live speech transcript populates the input field in real time during recording
  - If the Web Speech API is not available in the browser, the mic button is hidden and text-only input is shown
- **Acceptance Criteria**:
  - Admin can submit a question by typing and pressing Enter or clicking Send
  - Admin can submit a question by tapping mic, speaking, tapping mic again to stop, which triggers submission automatically
  - Empty questions are not submitted
  - Voice and text paths both reach the same API endpoint

### FR-2: Content Safety Moderation

- **Description**: Every question is screened by Azure Content Safety before being processed by the LLM.
- **Input**: `question` string from `InsightRequest`
- **Output**: Pass (continues to LLM) or block (returns `CONTENT_SAFETY_BLOCKED` error)
- **Business Rules**:
  - Uses the existing `assert_text_is_safe(text, field_name)` from `content_moderation.py`
  - If `CONTENT_SAFETY_ENABLED=false`, moderation is skipped (pass-through)
  - If blocked, the route returns HTTP 400 with `{ "code": "CONTENT_SAFETY_BLOCKED", "message": "..." }`
  - The frontend renders a "Content Flagged" popup modal when this code is received
- **Acceptance Criteria**:
  - Questions with flagged content do not reach the LLM
  - Frontend shows a dismissible popup explaining the block
  - Popup dismissal resets the panel to `idle` state with the input cleared

### FR-3: NL-to-SQL Translation (Phase 1)

- **Description**: The service sends the admin's question and the full ERD schema to GPT-4o to produce a safe SQL query.
- **Input**: Question string + ERD schema context (table names, columns, relationships)
- **Output**: A single SQL `SELECT` statement
- **Business Rules**:
  - GPT-4o is instructed via system prompt to return only a `SELECT` statement and output JSON `{ "sql": "..." }`
  - The generated SQL must not contain `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, or `TRUNCATE` - otherwise it is rejected with HTTP 422
  - If OpenAI is unreachable, return HTTP 503
- **Acceptance Criteria**:
  - Only SELECT queries reach the database
  - DDL/DML in the generated SQL returns a 422 with a clear error message
  - Service returns 503 on OpenAI connectivity failure

### FR-4: Query Execution

- **Description**: The service executes the validated SELECT query against PostgreSQL and returns the row data.
- **Input**: Validated SQL string
- **Output**: List of rows (up to 100 rows to limit payload size)
- **Business Rules**:
  - Uses the existing `get_db()` connection dependency
  - Results are capped at 100 rows to prevent oversized payloads to Phase 2
  - DB errors are caught and returned as HTTP 500
- **Acceptance Criteria**:
  - Query results are forwarded to Phase 2
  - No more than 100 rows are sent to the LLM

### FR-5: AI Answer, Chart, and Recommendations (Phase 2)

- **Description**: The service sends the original question and the query rows to GPT-4o, which returns a structured answer including a text explanation, a chart, and up to 3 recommendations.
- **Input**: Question string + SQL rows (JSON)
- **Output**: `InsightResponse` JSON
- **Business Rules**:
  - GPT-4o is instructed to always return both `answer` (text) and `chart` (visual)
  - GPT-4o selects the chart type that best fits the data from: `number`, `bar`, `line`, `donut`, `list`, `comparison`
  - Recommendations must include a `title`, `description`, and `action_type` from: `train`, `hire`, `assign`, `review`
  - Maximum 3 recommendations per response
- **Acceptance Criteria**:
  - Every successful response contains a non-empty `answer` string
  - Every successful response contains a `chart` object with a valid `type`
  - `action_type` values are constrained to the four defined types

### FR-6: Frontend Result Rendering

- **Description**: The Dashboard panel renders the API response as a text answer, an inline SVG chart, and recommendation cards.
- **Input**: `InsightResponse` from the API
- **Output**: Rendered UI below the input field
- **Business Rules**:
  - Chart type determines which SVG renderer is used (6 types, see FR-5)
  - Recommendation cards are color-coded by `action_type`
  - The SQL used is shown as a collapsed "View SQL" detail for transparency
  - "Ask another question" button resets the panel to `idle`
- **Acceptance Criteria**:
  - All 6 chart types render correctly with the data provided
  - Recommendation badges display with correct colors
  - Panel resets cleanly to idle after asking another question

## 5. Data Model Impact

No new tables are created. All queries are read-only against the existing schema.

| Table | Access | Notes |
|-------|--------|-------|
| `schedule` | Read | Core table for scheduling insights |
| `guides` | Read | Guide availability and assignment queries |
| `guide_tour_types` | Read | Expertise checks |
| `guide_languages` | Read | Language coverage queries |
| `tours` | Read | Tour-level aggregations |
| `reservations` | Read | Booking and cancellation queries |
| `tickets` | Read | Visitor volume queries |
| `availability_patterns` / `slots` / `exceptions` | Read | Availability analysis |
| `surveys` | Read | Guide rating and feedback queries |
| `tour_assignment_logs` | Read | Assignment history queries |

## 6. API Contracts

### `POST /insights/query`

Translates a natural-language question into a SQL query, executes it, and returns a structured answer.

**Request:**
```json
{ "question": "How many upcoming schedules do I have without a guide?" }
```

**Response (200) - number type:**
```json
{
  "question": "How many upcoming schedules do I have without a guide?",
  "answer": "You have 12 upcoming schedules without an assigned guide, representing 34% of all future schedules.",
  "chart": {
    "type": "number",
    "title": "Unassigned Upcoming Schedules",
    "data": [{ "label": "Unassigned", "value": 12 }]
  },
  "recommendations": [
    {
      "title": "Train existing guides",
      "description": "3 active guides lack expertise for these tours. Add the required tour type to make them eligible.",
      "action_type": "train"
    },
    {
      "title": "Hire new guides",
      "description": "If training is not feasible in time, consider recruiting guides qualified for the affected tours.",
      "action_type": "hire"
    }
  ],
  "sql_used": "SELECT COUNT(*) FROM schedule WHERE guide_id IS NULL AND event_start_datetime > NOW()"
}
```

**Response (200) - bar type:**
```json
{
  "question": "Which tours have the most unassigned schedules?",
  "answer": "Coral Reef Tour has the most unassigned schedules (7), followed by Deep Dive (4) and Sunset Cruise (1).",
  "chart": {
    "type": "bar",
    "title": "Unassigned Schedules by Tour",
    "data": [
      { "label": "Coral Reef Tour", "value": 7 },
      { "label": "Deep Dive", "value": 4 },
      { "label": "Sunset Cruise", "value": 1 }
    ]
  },
  "recommendations": [
    {
      "title": "Assign qualified guides",
      "description": "Check which guides have Coral Reef expertise and are available for the unassigned slots.",
      "action_type": "assign"
    }
  ],
  "sql_used": "SELECT t.name, COUNT(*) FROM schedule s JOIN tours t ON t.id = s.tour_id WHERE s.guide_id IS NULL AND s.event_start_datetime > NOW() GROUP BY t.name ORDER BY 2 DESC"
}
```

### Error Responses

| HTTP Status | `code` (in `detail`) | Scenario |
|-------------|----------------------|----------|
| 400 | `CONTENT_SAFETY_BLOCKED` | Question flagged by Azure Content Safety |
| 422 | `EMPTY_QUESTION` | Question is empty or whitespace only |
| 422 | `UNSAFE_SQL` | GPT-4o generated non-SELECT SQL |
| 503 | `OPENAI_UNAVAILABLE` | OpenAI API unreachable |
| 500 | `DB_ERROR` | PostgreSQL query failed |

## 7. Error Handling

| Scenario | Expected Behavior | HTTP Status |
|----------|-------------------|-------------|
| Empty question submitted | Return 422 with `EMPTY_QUESTION` code | 422 |
| Content safety blocks question | Return 400 with `CONTENT_SAFETY_BLOCKED` code; frontend shows popup modal | 400 |
| GPT-4o generates non-SELECT SQL | Reject before execution; return 422 with `UNSAFE_SQL` code | 422 |
| OpenAI API is unreachable | Return 503 with `OPENAI_UNAVAILABLE` code | 503 |
| PostgreSQL query fails | Return 500 with `DB_ERROR` code | 500 |
| GPT-4o returns malformed JSON | Catch parse error; return 500 with `PARSE_ERROR` code | 500 |

## 8. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| OpenAI GPT-4o | External | Requires `OPENAI_API_KEY` env var; `openai` Python package |
| Azure Content Safety | External (optional) | Existing service in `content_moderation.py`; no-op if `CONTENT_SAFETY_ENABLED=false` |
| `content_moderation.assert_text_is_safe` | Internal | Reused from existing moderation service |
| PostgreSQL | Internal | Read-only via existing `get_db()` dependency |
| Web Speech API | Browser | Voice input; graceful degradation to text-only if unsupported |
| ERD schema context | Internal doc | `backend/docs/db/ERD.md` embedded in Phase 1 system prompt |

## 9. Open Questions

| # | Question | Answer | Status |
|---|----------|--------|--------|
| 1 | Should query history be persisted for the admin to revisit? | Out of scope for v1; deferred | Open |
| 2 | Should the SQL query shown in the UI be hidden behind a toggle? | Yes - "View SQL" collapsible detail element | Resolved |
| 3 | What row limit is safe for Phase 2 LLM context? | 100 rows; fits well within GPT-4o context window | Resolved |
| 4 | Should `OPENAI_API_KEY` be documented in `.env.example`? | Yes | Resolved |

## Changelog

| Version | Date       | Author         | Description |
|---------|------------|----------------|-------------|
| 1.0     | 2026-04-07 | Evandro Maciel | Initial FDR - AI Data Insights Panel |
