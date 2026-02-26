# Oceanarium Tour Scheduling System

A full-stack tour scheduling system for an Oceanarium, built as a capstone project (PROJ 309) at SAIT for client HDB Systems.

The system automates the previously manual process of collecting online ticket sales and using that information to schedule tours and assign guides. Administrators can manage schedules, resources, bookings, and access an interactive calendar with a dashboard of key metrics. Guides can view and manage their schedules and receive relevant notifications.

## Tech Stack

| Layer          | Technology                                          |
| -------------- | --------------------------------------------------- |
| Frontend       | Vue 3, Vite, Tailwind CSS, Pinia, Vue Router        |
| Backend        | FastAPI, SQLAlchemy, Pydantic, Alembic, APScheduler |
| Database       | PostgreSQL 16                                       |
| Authentication | Firebase Auth                                       |
| CI/CD          | GitHub Actions                                      |
| Hosting        | Vercel (frontend), AWS EC2 + Docker (backend)       |

## Project Structure

```
├── backend/             # FastAPI backend application
│   ├── app/             # Source code (routers, models, schemas, services)
│   ├── alembic/         # Database migrations
│   ├── tests/           # Unit, integration, and API tests
│   ├── docs/            # ERD, architecture docs, Insomnia collection
│   └── scripts/         # Database reset utilities
│
├── frontend/            # Vue 3 frontend application
│   ├── src/             # Source code (views, components, stores, services)
│   └── public/          # Static assets
│
├── scripts/             # Git hooks installer
│   └── hooks/           # Pre-push hook (runs backend tests)
│
└── .github/workflows/   # CI/CD pipelines
    ├── backend-ci.yaml          # Tests + 95% coverage gate
    ├── backend-deploy.yaml      # Docker Hub → AWS EC2
    └── frontend-deploy.yaml     # Vercel production deploy
```

## Running Locally

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Python 3.11+
- Node.js 20.19+ or 22.12+

### Backend

See [backend/README.md](backend/README.md) for full setup instructions, Docker commands, testing, and database migrations.

```bash
cd backend

# Start PostgreSQL in Docker
docker compose up -d db

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations and start the server
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  python3 -m alembic upgrade head

DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  uvicorn app.main:app --reload --port 8000
```

API runs on http://localhost:8000 — Swagger docs at http://localhost:8000/docs

### Frontend

See [frontend/README.md](frontend/README.md) for full setup instructions and environment configuration.

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

### Verify Everything

1. Start the database and backend (see above)
2. Start the frontend (`npm run dev` in `frontend/`)
3. Open http://localhost:5173

## CI/CD

| Pipeline            | Trigger                                   | What it does                                                            |
| ------------------- | ----------------------------------------- | ----------------------------------------------------------------------- |
| Backend CI          | Push or PR touching `backend/`            | Runs pytest with 95% minimum coverage                                   |
| Backend Deployment  | Push to `main` or `develop` on `backend/` | Builds Docker image → pushes to Docker Hub → deploys to EC2 (main only) |
| Frontend Deployment | Push to `main` on `frontend/`             | Deploys to Vercel production                                            |

## Git Hooks

A pre-push hook runs the backend test suite (with 95% coverage gate) before every push that includes `backend/` changes. Install it once per clone:

```bash
bash scripts/install-hooks.sh
```

## Relevant Links

- **Frontend deployment:** https://cpsy301-small-prototype.vercel.app/
- **Jira board:** https://cloudhustler.atlassian.net/jira/software/projects/SCRUM/summary
- **API docs (local):** http://localhost:8000/docs
