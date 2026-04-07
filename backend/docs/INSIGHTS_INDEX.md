# AI Data Insights - Documentation Index

Complete documentation for the AI Data Insights feature in Oceanarium.

---

## 📚 Documentation Suite

### 1. User Guide (Non-Technical)
**File:** [`INSIGHTS_USER_GUIDE.md`](./INSIGHTS_USER_GUIDE.md)  
**Audience:** Operations staff, administrators, non-technical users  
**Content:**
- What the feature does (in plain language)
- Step-by-step usage instructions
- Voice input guide
- Chart types explained with examples
- Troubleshooting common issues
- Privacy and data handling
- Example questions to ask

**Best for:** Learning how to use the feature, training new staff, understanding what questions to ask.

---

### 2. Technical Reference (Lean)
**File:** [`INSIGHTS_TECHNICAL_REFERENCE.md`](./INSIGHTS_TECHNICAL_REFERENCE.md)  
**Audience:** Developers, technical staff  
**Content:**
- Architecture overview
- API specification (request/response)
- Implementation details (Phase 1 & 2)
- Chart types (technical breakdown)
- Security layers
- Configuration (env vars)
- Performance metrics
- Testing strategy
- Troubleshooting for developers
- API integration examples (cURL, Python, JavaScript)

**Best for:** Quick technical reference, API integration, debugging, understanding the tech stack.

---

### 3. Architecture Deep Dive (Complete)
**File:** [`INSIGHTS_ARCHITECTURE.md`](./INSIGHTS_ARCHITECTURE.md)  
**Audience:** Architects, senior developers, DevOps  
**Content:**
- Complete system architecture diagram
- 4 detailed sequence diagrams
- Backend flow with code walkthrough
- Frontend flow with code walkthrough
- File structure and responsibilities
- Service layer analysis
- Error handling flows
- Data enrichment pipeline
- Integration points
- Performance characteristics
- Monitoring and observability
- Deployment considerations

**Best for:** Understanding the complete system, architectural decisions, code structure, integration points.

---

### 4. Visual Diagrams
**Folder:** [`diagrams/`](./diagrams/)  
**Files:**
1. `insights-system-architecture.png` — Complete system overview
2. `insights-complete-query-flow.png` — Full request lifecycle
3. `insights-content-safety-block-flow.png` — Content moderation flow
4. `insights-sql-safety-violation-flow.png` — SQL guard in action
5. `insights-voice-input-flow.png` — Voice recognition flow
6. `insights-state-machine.png` — Frontend state transitions
7. `insights-enrichment-flow.png` — Data enrichment pipeline
8. `insights-error-propagation.png` — Error handling flow

**Best for:** Visual learners, presentations, architectural reviews, onboarding.

---

### 5. Requirements Document (FDR)
**File:** [`FDR/FDR-005-ai-data-insights.md`](./FDR/FDR-005-ai-data-insights.md)  
**Audience:** Product managers, stakeholders, developers  
**Content:**
- Purpose and scope
- Functional requirements (FR-1 through FR-6)
- Data model impact
- API contracts
- Error handling specification
- Dependencies
- Open questions

**Best for:** Understanding requirements, acceptance criteria, business logic, feature scope.

---

## 🎯 Quick Navigation

### I want to...

| Goal | Document to Read |
|------|------------------|
| Learn how to use the feature | [User Guide](./INSIGHTS_USER_GUIDE.md) |
| Integrate the API | [Technical Reference](./INSIGHTS_TECHNICAL_REFERENCE.md) - API section |
| Understand the architecture | [Architecture Deep Dive](./INSIGHTS_ARCHITECTURE.md) |
| See visual diagrams | [Diagrams Folder](./diagrams/) |
| Debug an issue | [Technical Reference](./INSIGHTS_TECHNICAL_REFERENCE.md) - Troubleshooting |
| Understand requirements | [FDR-005](./FDR/FDR-005-ai-data-insights.md) |
| Train new users | [User Guide](./INSIGHTS_USER_GUIDE.md) |
| Present to stakeholders | [Diagrams](./diagrams/) + [User Guide](./INSIGHTS_USER_GUIDE.md) |
| Review code structure | [Architecture Deep Dive](./INSIGHTS_ARCHITECTURE.md) - File Structure |
| Understand error handling | [Architecture Deep Dive](./INSIGHTS_ARCHITECTURE.md) - Error Handling Flow |

---

## 📊 Documentation Coverage

| Aspect | Coverage | Documents |
|--------|----------|-----------|
| **User-facing** | ✅ Complete | User Guide |
| **API Reference** | ✅ Complete | Technical Reference |
| **Architecture** | ✅ Complete | Architecture Deep Dive |
| **Visual Diagrams** | ✅ Complete | 8 diagrams |
| **Code Walkthrough** | ✅ Complete | Architecture Deep Dive |
| **Requirements** | ✅ Complete | FDR-005 |
| **Security** | ✅ Complete | Technical Reference + Architecture |
| **Testing** | ✅ Complete | Technical Reference + Architecture |
| **Deployment** | ✅ Complete | Technical Reference |
| **Monitoring** | ✅ Complete | Architecture Deep Dive |

---

## 🔗 Related Files

### Backend Code
- **Route:** `backend/app/routes/insights.py`
- **Service:** `backend/app/services/insights.py`
- **Content Moderation:** `backend/app/services/content_moderation.py`
- **Guide Assignment:** `backend/app/services/guide_assignment.py`

### Frontend Code
- **Component:** `frontend/src/components/DashboardInsightPanel.vue`
- **View:** `frontend/src/views/DashboardView.vue`
- **API Client:** `frontend/src/services/api.js`

### Configuration
- **Environment:** `backend/.env` (requires `OPENAI_API_KEY`)
- **Example:** `backend/.env.example`

---

## 📝 Document Versions

| Document | Version | Last Updated | Author |
|----------|---------|--------------|--------|
| User Guide | 1.0 | 2026-04-07 | Evandro Maciel |
| Technical Reference | 1.0 | 2026-04-07 | Evandro Maciel |
| Architecture Deep Dive | 1.0 | 2026-04-07 | Evandro Maciel |
| Visual Diagrams | 1.0 | 2026-04-07 | AI Generated |
| FDR-005 | 1.0 | 2026-04-07 | Evandro Maciel |

---

## 🚀 Feature Status

**Current Version:** 1.0  
**Status:** ✅ Production Ready  
**Released:** April 7, 2026

### Key Features (v1.0)
- ✅ Natural language query interface
- ✅ Voice input support (Web Speech API)
- ✅ Two-phase LLM pipeline (GPT-4o)
- ✅ 6 adaptive chart types
- ✅ 4 recommendation categories
- ✅ Content safety moderation
- ✅ SQL safety guards
- ✅ Data enrichment for unassigned schedules
- ✅ Admin-only access
- ✅ Dark mode support

### Future Enhancements (Planned)
- ⏳ Query history and saved insights
- ⏳ Multi-turn conversational context
- ⏳ Export to CSV/PDF
- ⏳ Scheduled insight reports
- ⏳ Guide-facing dashboard
- ⏳ Custom alert triggers

---

## 📧 Support & Feedback

For questions, issues, or suggestions:
1. **Technical Issues:** Contact IT/DevOps team
2. **Usage Questions:** Refer to User Guide or ask your administrator
3. **Feature Requests:** Submit through organization's feature request process
4. **Bug Reports:** Include question asked, error message, screenshot, and SQL (if available)

---

## 🏗️ Architecture at a Glance

```
User → Frontend (Vue) → Backend (FastAPI) → OpenAI GPT-4o
                             ↓
                      PostgreSQL (read-only)
                             ↓
                      Azure Content Safety (optional)
```

**Key Technologies:**
- **Frontend:** Vue 3 (Composition API), Web Speech API, Inline SVG charts
- **Backend:** FastAPI (Python), SQLAlchemy, Pydantic
- **LLM:** OpenAI GPT-4o (`gpt-4o` model)
- **Database:** PostgreSQL (read-only, 100 row limit)
- **Content Moderation:** Azure Content Safety (optional)

---

## 📖 Reading Order Recommendations

### For New Users
1. [User Guide](./INSIGHTS_USER_GUIDE.md) — Start here
2. [Diagrams](./diagrams/) — Visual overview
3. Practice asking questions on the Dashboard

### For Developers (New to Project)
1. [Technical Reference](./INSIGHTS_TECHNICAL_REFERENCE.md) — Quick overview
2. [Architecture Deep Dive](./INSIGHTS_ARCHITECTURE.md) — Complete understanding
3. [Diagrams](./diagrams/) — Visual reference
4. Code files — Backend and Frontend implementation

### For Architects/Reviewers
1. [Diagrams](./diagrams/) — Visual overview
2. [Architecture Deep Dive](./INSIGHTS_ARCHITECTURE.md) — Complete system
3. [FDR-005](./FDR/FDR-005-ai-data-insights.md) — Requirements
4. [Technical Reference](./INSIGHTS_TECHNICAL_REFERENCE.md) — API and integration

---

**Documentation maintained by:** Evandro Maciel  
**Last updated:** April 7, 2026  
**Feature version:** 1.0
