# About the project

This is a project made for the PROJ 309 (Capstone) Class at SAIT. The project was requested by our client HDB Systems

This system allows for administrators and guides to easiliy interact with the Oceanarium. Guides can easily view and manage their schedules as well as receiving relevant notifications.
Administrators can manage schedules, resources, bookings and access an interactive calendar, as well as a dashboard with metrics of the Oceanarium.

Overall the system automates the previously manual task of getting online ticket sales information, and using that information to schedule tours and assign guides

# Tech stack

* Front-end: Vue3
* Back-end : FastAPI (layered architecture — see `backend/README.md`)
* Database : PostgreSQL
* Authentication: Firebase
* Email: Resend.com

# Relevant Links

Vercel Deployment: cpsy301-small-prototype.vercel.app/

Jira Board: https://cloudhustler.atlassian.net/jira/software/projects/SCRUM/summary


# Running it Locally

## Backend Instructions

### Setup

Before starting, create a .env file in your backend folder with the following content

```bash
#.env

# Database connection string
DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@IP/DATABASE #Replace Username, Password, Ip, and Database for the actual data

# Email Configuration (for notifications)
EMAIL_ENABLED=true
RESEND_API_KEY=re_your_api_key_here  # Get from https://resend.com/api-keys
EMAIL_FROM=onboarding@resend.dev      # Use this for testing; verify your domain for production
EMAIL_FROM_NAME=Oceanarium Scheduling System
FRONTEND_URL=http://localhost:5173
```

Then install the required libraries

```bash
cd backend
python -m venv venv
Windows: venv\Scripts\activate #To activate the virtual environment

pip install -r requirements.txt
# edit .env to put your real DATABASE_URL
```

### Run in the terminal

```
uvicorn app.main:app --reload
```
API runs on http://127.0.0.1:8000 — interactive docs at http://127.0.0.1:8000/docs

For the full backend architecture guide, API reference, and how to add new endpoints, see [`backend/README.md`](backend/README.md).


## Frontend Instructions

### Setup
```bash
npm install
npm install axios
npm install tailwindcss @tailwindcss/vite
npm run dev
```
Frontend runs on http://localhost:5173

## To Test everything
1. **Set up Resend.com** (for email notifications):
   - Sign up at https://resend.com
   - Get your API key from https://resend.com/api-keys
   - Add it to your `backend/.env` file as `RESEND_API_KEY`
   - For testing, use `EMAIL_FROM=onboarding@resend.dev`
   - For production, verify your domain at https://resend.com/domains

2. Start backend (`uvicorn app.main:app --reload`)

3. Start frontend (`npm run dev`)

4. Open http://localhost:5173 (you should see API + DB status)
