# About the project

This is a project made for the PROJ 309 (Capstone) Class at SAIT. The project was requested by our client HDB Systems

This system allows for administrators and guides to easiliy interact with the Oceanarium. Guides can easily view and manage their schedules as well as receiving relevant notifications.
Administrators can manage schedules, resources, bookings and access an interactive calendar, as well as a dashboard with metrics of the Oceanarium.

Overall the system automates the previously manual task of getting online ticket sales information, and using that information to schedule tours and assign guides

# Tech stack 📚

* Front-end: Vue3
* Back-end : FastAPI
* Database : PostgreSQL
* Authentication: Firebase

# Relevant Links 🔗

Vercel Deployment: cpsy301-small-prototype.vercel.app/

Jira Board: https://cloudhustler.atlassian.net/jira/software/projects/SCRUM/summary


# Running it Locally

## Backend Instructions

### Setup

Before starting, creating a .env file in your backend folder with the following content

```bash
#.env

# Database connection string
DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@IP/DATABASE #Replace Username, Password, Ip, and Database for the actual data
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
API runs on http://127.0.0.1:8000 (Access http://127.0.0.1:8000/group_members_example to view an example endpoint)


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
1. Start backend (uvicorn app.main:app --reload)

2. Start frontend (npm run dev)

3. Open http://localhost:5173 (you should see API + DB status)

