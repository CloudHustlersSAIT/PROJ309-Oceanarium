# AI Data Insights - Visual Diagrams

This folder contains visual diagrams for the AI Data Insights feature architecture and flows.

## Diagrams Overview

### 1. System Architecture
**File:** `insights-system-architecture.png`

Complete system architecture showing:
- Frontend components (DashboardView, DashboardInsightPanel)
- Backend layers (routes, services)
- Phase 1 and Phase 2 LLM flows
- External services (OpenAI GPT-4o, PostgreSQL, Azure Content Safety)
- Data flow between all components

### 2. Complete Query Flow (Success Case)
**File:** `insights-complete-query-flow.png`

Detailed sequence diagram showing the full request lifecycle:
1. User input (type/speak)
2. Frontend submission
3. Backend authentication and content safety check
4. Phase 1: NL → SQL translation
5. SQL validation and execution
6. Data enrichment (for unassigned schedules)
7. Phase 2: SQL results → insights generation
8. Response rendering (chart + answer + recommendations)

### 3. Content Safety Block Flow
**File:** `insights-content-safety-block-flow.png`

Sequence diagram showing what happens when content is flagged:
- User asks inappropriate question
- Azure Content Safety blocks it
- HTTP 400 returned with `CONTENT_SAFETY_BLOCKED` code
- Frontend displays modal popup

### 4. SQL Safety Violation Flow
**File:** `insights-sql-safety-violation-flow.png`

Sequence diagram showing SQL guard in action:
- OpenAI generates unsafe SQL (e.g., DELETE)
- `_guard_sql()` detects dangerous keywords
- HTTP 422 returned with `UNSAFE_SQL` code
- Frontend displays error message

### 5. Voice Input Flow
**File:** `insights-voice-input-flow.png`

Frontend-only sequence showing Web Speech API integration:
- User taps microphone button
- Browser starts speech recognition
- Real-time transcription updates input field
- User stops recording
- Question auto-submitted to backend

### 6. State Machine
**File:** `insights-state-machine.png`

Frontend state transitions:
- **IDLE** → user ready to ask
- **LISTENING** → recording voice (pulsing red ring)
- **PROCESSING** → API call in progress (spinner)
- **RESULT** → displaying answer/chart/recommendations
- Transitions for all success/error paths

### 7. Data Enrichment Flow
**File:** `insights-enrichment-flow.png`

Data transformation pipeline for unassigned schedule queries:
1. Extract schedule IDs from Phase 1 results
2. Check eligibility for each schedule (`find_eligible_guides`)
3. Aggregate blocking reasons (expertise, language, availability)
4. Inject enriched context into Phase 2 prompt
5. Generate specific, actionable recommendations

### 8. Error Propagation
**File:** `insights-error-propagation.png`

Backend error handling flow:
- Service layer exceptions (ValidationError, OpenAIError, RuntimeError)
- Route handler catches and maps to HTTP status codes
- Error codes: `UNSAFE_SQL` (422), `OPENAI_UNAVAILABLE` (503), `DB_ERROR` (500), `CONTENT_SAFETY_BLOCKED` (400)

---

## Using These Diagrams

### In Documentation
Reference diagrams in markdown files using relative paths:

```markdown
![System Architecture](./diagrams/insights-system-architecture.png)
```

### In Presentations
All diagrams are high-resolution PNGs suitable for:
- Technical presentations
- Architecture review meetings
- Onboarding documentation
- System design documents

### For Development
Use these diagrams to:
- Understand the complete request flow
- Debug issues at specific integration points
- Plan new features or modifications
- Communicate architecture to team members

---

## Diagram Generation

These diagrams were generated using AI image generation on **April 7, 2026**.

To regenerate or update diagrams:
1. Modify the text descriptions in the generation prompts
2. Use the same AI generation tool
3. Ensure consistent style and color coding
4. Update this README with any new diagrams

---

## Color Coding

Consistent colors across diagrams:
- **Blue** — Frontend components and flows
- **Green** — Backend services and successful paths
- **Orange** — External services (OpenAI, Azure, PostgreSQL)
- **Red** — Error states and blocked flows
- **Purple** — Voice/audio features
- **Yellow** — Warning states (content safety)

---

## Related Documentation

- **User Guide:** `../INSIGHTS_USER_GUIDE.md`
- **Technical Reference:** `../INSIGHTS_TECHNICAL_REFERENCE.md`
- **Architecture Document:** `../INSIGHTS_ARCHITECTURE.md`
- **FDR:** `../FDR/FDR-005-ai-data-insights.md`

---

**Last Updated:** April 7, 2026
