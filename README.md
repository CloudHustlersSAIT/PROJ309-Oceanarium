# About the project

This is a project made for the PROJ 309 (Capstone) Class at SAIT. The project was requested by our client HDB Systems.

This system allows for administrators and guides to easily interact with the Oceanarium. Guides can easily view and manage their schedules as well as receiving relevant notifications.
Administrators can manage schedules, resources, bookings and access an interactive calendar, as well as a dashboard with metrics of the Oceanarium.

Overall the system automates the previously manual task of getting online ticket sales information, and using that information to schedule tours and assign guides.

# Tech Stack

- Front-end: Vue 3
- Back-end: FastAPI
- Database: PostgreSQL
- Authentication: Firebase

# Relevant Links

Vercel Deployment: cpsy301-small-prototype.vercel.app/

Jira Board: https://cloudhustler.atlassian.net/jira/software/projects/SCRUM/summary

# Running it Locally

## Backend

See [backend/README.md](backend/README.md) for full setup instructions, Docker commands, testing, and database migrations.

Quick version:

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

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

## Verify Everything

1. Start backend (see above)
2. Start frontend (`npm run dev`)
3. Open http://localhost:5173
