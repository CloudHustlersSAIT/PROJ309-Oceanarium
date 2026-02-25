# Foundation Architecture Document

| Field            | Detail                                               |
| ---------------- | ---------------------------------------------------- |
| **Project**      | Oceanarium Tour Scheduling System                    |
| **Author**       | Evandro Maciel                                       |
| **Version**      | 1.0                                                  |
| **Last Updated** | February 24, 2026                                    |
| **Status**       | Living document — updated as the architecture evolves |

---

## 1. Purpose & Scope

This document describes the foundational architecture of the Oceanarium Tour Scheduling System. It serves as the single source of truth for all architectural decisions, component interactions, technology choices, and operational concerns across the full stack.

**Audience**: Developers, DevOps, QA, project stakeholders, and future maintainers.

**Companion documents**:

- [Backend Architecture Overview](backend-overview.md) — detailed backend layers, data flow, and API reference
- [FDR-001: Guide Assignment](../fdr/FDR-001-Guide-Assignment.md) — functional requirements for the core feature

---

## 2. System Overview

The Oceanarium Tour Scheduling System automates what was previously a manual process: retrieving online ticket sales information and using it to schedule tours and assign guides at an oceanarium facility.

### Key Capabilities

| Capability              | Description                                                        |
| ----------------------- | ------------------------------------------------------------------ |
| **Tour Synchronization** | Periodically pulls booking data from the external Clorian ticketing system |
| **Guide Assignment**     | Automatically matches and assigns guides to tours based on availability, language, and expertise |
| **Schedule Management**  | Guides and admins can view and manage tour schedules               |
| **Booking Management**   | Create, reschedule, and cancel bookings                            |
| **Dashboard & Metrics**  | Interactive dashboard with operational statistics                   |
| **Notification System**  | Alerts for schedule changes, new assignments, and issues           |
| **Issue Reporting**      | Staff can report operational issues                                |

---

## 3. Architecture Principles

| Principle                     | Rationale                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------ |
| **Separation of Concerns**    | Each layer has a single responsibility; business logic is isolated from HTTP and data access |
| **Dependency Inversion**      | External systems are accessed through abstract interfaces (adapter pattern)          |
| **Convention over Configuration** | Consistent project structure and naming reduce onboarding friction                |
| **Environment-Based Config**  | No secrets in code; all configuration via environment variables                      |
| **Progressive Enhancement**   | Firebase auth is optional in development; mock adapters allow work without external APIs |
| **Monorepo, Loose Coupling**  | Frontend and backend live in one repository but are independently deployable         |

---

## 4. System Context

```
                          ┌──────────────┐
                          │   Admins &   │
                          │    Guides    │
                          └──────┬───────┘
                                 │ HTTPS
                          ┌──────▼───────┐
                          │   Frontend   │
                          │  (Vue 3 SPA) │
                          │   Vercel     │
                          └──────┬───────┘
                                 │ REST / JSON
                          ┌──────▼───────┐
                          │   Backend    │
                          │  (FastAPI)   │
                          │   AWS EC2    │
                          └──┬───────┬───┘
                             │       │
                    ┌────────▼──┐ ┌──▼──────────┐
                    │PostgreSQL │ │   Clorian    │
                    │   (RDS /  │ │  Ticketing   │
                    │  EC2 local│ │   System     │
                    │  )        │ │  (External)  │
                    └───────────┘ └──────────────┘
                                         ▲
                          ┌──────────────┘
                          │ Firebase Auth
                          │ (Google Cloud)
                          └──────────────
```

### Actors

| Actor          | Role                                                                 |
| -------------- | -------------------------------------------------------------------- |
| **Admin**      | Manages guides, tours, bookings; views dashboard; triggers manual sync |
| **Guide**      | Views personal schedule, availability, and notifications             |
| **Clorian**    | External ticketing system — source of truth for bookings             |
| **Firebase**   | Identity provider for frontend authentication                        |

---

## 5. Technology Stack

### Frontend

| Concern          | Technology                    | Version   |
| ---------------- | ----------------------------- | --------- |
| Framework        | Vue 3 (Composition API)       | 3.5.x     |
| Build Tool       | Vite                          | 7.x       |
| Styling          | Tailwind CSS                  | 4.x       |
| State Management | Pinia                         | 3.x       |
| Routing          | Vue Router                    | 4.x       |
| Authentication   | Firebase Authentication       | 12.x      |
| HTTP Client      | Native Fetch API              | —         |
| Code Formatting  | Prettier                      | 3.6.x     |
| Node Runtime     | Node.js                       | ^20.19.0  |

### Backend

| Concern          | Technology                    | Version   |
| ---------------- | ----------------------------- | --------- |
| Framework        | FastAPI                       | latest    |
| Language         | Python                        | 3.11      |
| ORM              | SQLAlchemy                    | 2.x       |
| Database Driver  | psycopg2-binary               | latest    |
| Migrations       | Alembic                       | latest    |
| Scheduler        | APScheduler (BackgroundScheduler) | latest |
| HTTP Client      | httpx (for future Clorian)    | latest    |
| ASGI Server      | Uvicorn                       | latest    |
| Config           | python-dotenv                 | latest    |

### Infrastructure & DevOps

| Concern              | Technology                        |
| -------------------- | --------------------------------- |
| Frontend Hosting     | Vercel                            |
| Backend Hosting      | AWS EC2 (Docker container)        |
| Database Hosting     | PostgreSQL on EC2 (host network)  |
| Container Runtime    | Docker                            |
| CI/CD                | GitHub Actions                    |
| Container Registry   | Docker Hub                        |
| DNS / CDN            | Vercel Edge Network (frontend)    |

### Testing

| Layer       | Tool                | Scope                             |
| ----------- | ------------------- | --------------------------------- |
| Backend Unit       | pytest       | Services, business logic          |
| Backend Integration| pytest       | Service ↔ DB interaction          |
| Backend API        | FastAPI TestClient | Full HTTP endpoint tests    |
| Backend Coverage   | pytest-cov   | Coverage reporting                |
| API Manual         | Insomnia     | Collection for manual validation  |
| Frontend           | —            | Not yet configured                |

---

## 6. Component Architecture

### 6.1 Frontend

```
frontend/src/
├── main.js                    # App bootstrap: Vue + Pinia + Router
├── App.vue                    # Root component (router-view)
├── router/index.js            # Route definitions + auth guards
├── contexts/authContext.js     # Firebase auth composable (reactive user state)
├── utils/firebase.js           # Firebase initialization + graceful fallback
├── services/api.js             # Centralized REST client (fetch wrapper)
├── stores/                     # Pinia stores (state management)
├── views/                      # Page-level components (one per route)
│   ├── DashboardView.vue
│   ├── BookingsView.vue
│   ├── CalendarView.vue
│   ├── AssetsView.vue
│   ├── NotificationsView.vue
│   ├── SettingsView.vue
│   ├── LoginView.vue
│   ├── ForgotPasswordView.vue
│   └── HomeView.vue
├── components/                 # Reusable UI components
│   ├── Sidebar.vue
│   └── SidebarButton.vue
└── assets/                     # Static assets (CSS, images, videos, icons)
```

**Key design decisions**:

- **Composable auth**: `useAuth()` provides reactive `user` ref, login/logout/register functions. Firebase is optional — when env vars are missing, auth is bypassed for local development.
- **Centralized API layer**: All backend calls go through `services/api.js`, which reads `VITE_API_BASE_URL` and provides typed helper functions per domain.
- **Route guards**: `router.beforeEach` checks auth state; public routes (`/login`, `/forgot-password`) are accessible without login.

### 6.2 Backend

The backend follows a **layered architecture** described in detail in the [Backend Architecture Overview](backend-overview.md). The layers are:

```
Routers → Services → Models / Adapters → Database / External APIs
```

| Layer      | Responsibility                                              |
| ---------- | ----------------------------------------------------------- |
| Routers    | HTTP handling, input validation, response formatting        |
| Services   | Business logic, orchestration (framework-agnostic)          |
| Schemas    | Pydantic models for API contract (decoupled from ORM)       |
| Models     | SQLAlchemy ORM classes mapping to database tables           |
| Adapters   | Abstract interfaces for external system integrations        |
| Jobs       | Scheduled background tasks (APScheduler)                    |

### 6.3 Database

PostgreSQL with 10 tables organized around three domains:

| Domain         | Tables                                                                    |
| -------------- | ------------------------------------------------------------------------- |
| **Guide**      | `guides`, `languages`, `expertises`, `guide_languages`, `guide_expertises` |
| **Availability** | `availability_patterns`, `availability_slots`, `availability_exceptions` |
| **Tour & Audit** | `tours`, `tour_assignment_logs`, `sync_logs`                            |

See the [Backend Architecture Overview](backend-overview.md#5-database) for the full ERD and table descriptions.

---

## 7. Deployment Architecture

### 7.1 Environment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                        Production                           │
│                                                             │
│  ┌───────────────────┐         ┌──────────────────────┐     │
│  │     Vercel         │  HTTPS  │     AWS EC2          │     │
│  │  ┌─────────────┐  │────────▶│  ┌────────────────┐  │     │
│  │  │ Vue 3 SPA   │  │  REST   │  │  Docker         │  │     │
│  │  │ (static)    │  │         │  │  ┌────────────┐ │  │     │
│  │  └─────────────┘  │         │  │  │ FastAPI    │ │  │     │
│  └───────────────────┘         │  │  │ (Uvicorn)  │ │  │     │
│                                │  │  └──────┬─────┘ │  │     │
│  ┌───────────────────┐         │  └─────────┼───────┘  │     │
│  │  Firebase Auth    │         │            │          │     │
│  │  (Google Cloud)   │         │     ┌──────▼───────┐  │     │
│  └───────────────────┘         │     │  PostgreSQL  │  │     │
│                                │     │  (localhost) │  │     │
│                                │     └──────────────┘  │     │
│                                └──────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Local Development

| Service    | Command                               | URL                    |
| ---------- | ------------------------------------- | ---------------------- |
| Frontend   | `cd frontend && npm run dev`          | http://localhost:5173   |
| Backend    | `cd backend && uvicorn app.main:app --reload` | http://localhost:8000 |
| Database   | PostgreSQL (local or Docker)          | localhost:5432         |

Firebase is **optional** locally. When `VITE_FIREBASE_*` env vars are absent, the app bypasses authentication and redirects to `/home`.

### 7.3 CI/CD Pipelines

#### Backend Pipeline (`.github/workflows/backend-deploy.yaml`)

```
Push to main/develop (backend/**)
  │
  ├─ build-and-push (always)
  │    ├─ Checkout code
  │    ├─ Login to Docker Hub
  │    └─ Build & push image → dockerhub/capstone-backend:latest
  │
  └─ deploy (main branch only)
       ├─ Get runner IP
       ├─ Open SSH in AWS Security Group (temporary)
       ├─ SSH into EC2:
       │    ├─ docker pull latest image
       │    ├─ docker stop/rm old container
       │    └─ docker run new container (--network=host, inject DATABASE_URL)
       └─ Close SSH in Security Group (always, even on failure)
```

#### Frontend Pipeline (`.github/workflows/frontend-deploy.yaml`)

```
Push to main (frontend/**)
  │
  └─ deploy
       ├─ Checkout code
       ├─ Setup Node.js 20.19.0
       ├─ Install Vercel CLI v37.4.1
       ├─ Pull Vercel environment
       └─ Deploy to Vercel production
```

---

## 8. Security Architecture

### 8.1 Authentication

| Layer    | Mechanism                                                          |
| -------- | ------------------------------------------------------------------ |
| Frontend | Firebase Authentication (email/password)                           |
| Route    | Vue Router guards check `user` ref from `useAuth()` composable    |
| Backend  | CORS whitelist (localhost + Vercel); no token validation middleware yet |

**Planned improvement**: Validate Firebase ID tokens on the backend via middleware to secure API endpoints.

### 8.2 Secrets Management

| Secret               | Storage                          | Accessed By       |
| -------------------- | -------------------------------- | ----------------- |
| `DATABASE_URL`       | GitHub Secrets → EC2 env var     | Backend container |
| Firebase config      | Vercel env vars → `VITE_*` vars  | Frontend build    |
| Docker Hub creds     | GitHub Secrets                   | CI/CD pipeline    |
| AWS credentials      | GitHub Secrets                   | CI/CD pipeline    |
| EC2 SSH key          | GitHub Secrets                   | CI/CD pipeline    |

### 8.3 Network Security

- **EC2 Security Group**: SSH port (22) opened only during deployment (runner IP whitelisted, then revoked).
- **CORS**: Backend accepts requests only from `localhost:5173`, `127.0.0.1:5173`, and `*.vercel.app`.
- **Docker**: Container runs with `--network=host` for local PostgreSQL access; `--restart always` for resilience.

---

## 9. Integration Architecture

### 9.1 Clorian Ticketing System

The Clorian integration uses the **adapter pattern** to decouple the sync logic from the external API:

```
                  ┌──────────────────────┐
                  │  ClorianClientBase   │  (abstract interface)
                  │  - fetch_bookings()  │
                  └──────────┬───────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
   ┌──────────▼───┐  ┌──────▼──────┐  ┌───▼────────────┐
   │ClorianMock   │  │ClorianHttp  │  │ Future adapters │
   │Client (dev)  │  │Client (prod)│  │                 │
   └──────────────┘  └─────────────┘  └─────────────────┘
```

- **Current**: `ClorianMockClient` generates realistic test data for development.
- **Future**: `ClorianHttpClient` will call the real API using `httpx`.
- **Sync schedule**: APScheduler runs every 15 minutes with an overlap guard (thread lock).

### 9.2 Firebase Authentication

- Frontend-only integration through the Firebase JS SDK.
- `src/utils/firebase.js` initializes the Firebase app and exports the `auth` instance.
- `src/contexts/authContext.js` wraps Firebase's `onAuthStateChanged` into a Vue composable.
- Graceful degradation: if Firebase env vars are missing, `firebaseDisabled = true` and auth is bypassed.

---

## 10. Cross-Cutting Concerns

### 10.1 Error Handling

| Layer    | Strategy                                                                |
| -------- | ----------------------------------------------------------------------- |
| Frontend | API service catches fetch errors; Vue Router guards handle auth failures |
| Backend  | FastAPI exception handlers; services raise descriptive `HTTPException`s  |
| Sync Job | Failures logged to `sync_logs` table with error details; job continues  |

### 10.2 Logging & Audit

| What                    | Where                            | Purpose                     |
| ----------------------- | -------------------------------- | --------------------------- |
| Assignment changes      | `tour_assignment_logs` table     | Full audit trail (NFR-02)   |
| Sync cycle results      | `sync_logs` table                | Debugging sync issues       |
| Application logs        | stdout (Docker → CloudWatch)     | Operational monitoring      |

### 10.3 Configuration

All runtime configuration is managed through environment variables:

**Backend** (`.env`):
```
DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:5432/DB
```

**Frontend** (`.env` or Vercel dashboard):
```
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

---

## 11. Quality Attributes

| Attribute        | Target                                                                  | How Achieved                                      |
| ---------------- | ----------------------------------------------------------------------- | ------------------------------------------------- |
| **Maintainability** | New features require changes in ≤ 2 layers                           | Layered architecture, single-responsibility modules |
| **Testability**  | 52 backend tests, all acceptance criteria covered                       | Framework-agnostic services, DI via `get_db`, mock adapters |
| **Deployability** | Zero-downtime deploy in < 5 min                                       | Docker + GitHub Actions CI/CD, independent frontend/backend deploys |
| **Reliability**  | Sync failures don't crash the system                                    | Overlap guard, error logging to `sync_logs`, `--restart always` |
| **Scalability**  | Single-instance sufficient for current load (~50 tours/day)             | Stateless API, can scale horizontally if needed    |
| **Security**     | No secrets in source code                                               | GitHub Secrets, env vars, `.gitignore` enforcement |
| **Auditability** | Every assignment change is traceable                                    | `tour_assignment_logs` with actor, timestamp, reason |

---

## 12. Known Constraints & Technical Debt

| Item                                    | Impact                              | Mitigation Plan                          |
| --------------------------------------- | ----------------------------------- | ---------------------------------------- |
| No backend API authentication           | Endpoints are publicly accessible   | Add Firebase token validation middleware |
| No frontend test suite                  | UI regressions go undetected        | Add Vitest + Vue Test Utils              |
| Clorian uses mock adapter only          | Cannot validate real sync behavior  | Implement `ClorianHttpClient` when API is available |
| APScheduler is in-process               | Scheduler dies if the process dies  | Acceptable for single instance; consider Celery for multi-node |
| PostgreSQL on same EC2 instance         | Single point of failure             | Migrate to AWS RDS for production resilience |
| No rate limiting or throttling          | Vulnerable to abuse                 | Add middleware (e.g., `slowapi`)         |
| Console logs dropped in production build | Harder to debug frontend issues    | Add structured logging (e.g., Sentry)   |
| CORS allows `*.vercel.app` wildcard     | Any Vercel app could call the API   | Restrict to the specific deployment URL  |

---

## 13. Repository Structure

```
PROJ309-Oceanarium/
│
├── .github/workflows/             # CI/CD pipeline definitions
│   ├── backend-deploy.yaml        #   Docker build → EC2 deploy
│   └── frontend-deploy.yaml       #   Vercel production deploy
│
├── backend/                       # Python / FastAPI application
│   ├── app/                       #   Application code (see backend-overview.md)
│   │   ├── adapters/              #     External system integrations
│   │   ├── jobs/                  #     Scheduled background tasks
│   │   ├── models/                #     SQLAlchemy ORM models
│   │   ├── routers/               #     FastAPI route handlers
│   │   ├── schemas/               #     Pydantic request/response models
│   │   ├── services/              #     Business logic layer
│   │   ├── db.py                  #     Database engine & session factory
│   │   └── main.py                #     App factory, CORS, lifespan
│   ├── alembic/                   #   Database migrations
│   ├── tests/                     #   Test suite (unit, integration, API)
│   ├── docs/                      #   Documentation
│   │   ├── architecture/          #     Architecture documents (this file)
│   │   ├── fdr/                   #     Functional Design Requirements
│   │   └── insomnia.json          #     API test collection
│   ├── Dockerfile                 #   Container image definition
│   └── requirements.txt           #   Python dependencies
│
├── frontend/                      # Vue 3 / Vite application
│   ├── src/
│   │   ├── views/                 #     Page components (one per route)
│   │   ├── components/            #     Reusable UI components
│   │   ├── contexts/              #     Vue composables (auth)
│   │   ├── services/              #     API client layer
│   │   ├── stores/                #     Pinia state management
│   │   ├── utils/                 #     Firebase setup, helpers
│   │   ├── assets/                #     CSS, images, videos, icons
│   │   ├── router/                #     Route definitions + guards
│   │   ├── App.vue                #     Root component
│   │   └── main.js                #     App bootstrap
│   ├── public/                    #   Static assets (favicon)
│   ├── index.html                 #   SPA entry point
│   ├── vite.config.js             #   Vite build configuration
│   └── package.json               #   Node dependencies & scripts
│
├── .gitignore                     # Git ignore rules
└── README.md                      # Project overview & setup instructions
```

---

## 14. Glossary

| Term                | Definition                                                              |
| ------------------- | ----------------------------------------------------------------------- |
| **Clorian**         | Third-party ticketing system that sells oceanarium tours online         |
| **Guide**           | Staff member who leads tours at the oceanarium                          |
| **Tour**            | A scheduled visit synced from Clorian, assigned to one guide            |
| **Sync**            | The process of pulling new/changed bookings from Clorian into the local database |
| **Assignment**      | Linking a guide to a tour (automatic or manual)                         |
| **SPA**             | Single-Page Application — the Vue frontend runs entirely in the browser |
| **Adapter**         | Design pattern providing an interface to an external system             |
| **Composable**      | Vue 3 pattern for encapsulating and reusing reactive logic              |
| **Lifespan**        | FastAPI mechanism for running startup/shutdown code                     |

---

## Revision History

| Version | Date           | Author          | Changes            |
| ------- | -------------- | --------------- | ------------------ |
| 1.0     | Feb 24, 2026   | Evandro Maciel  | Initial version    |
