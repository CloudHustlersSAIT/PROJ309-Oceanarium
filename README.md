# Backend Instructions

## Setup

```bash
cd backend
python -m venv venv
Windows: venv\Scripts\activate #To activate the virtual environment

pip install -r requirements.txt
# edit .env to put your real DATABASE_URL
```

## Run in the terminal

```
uvicorn app.main:app --reload
```
API runs on http://127.0.0.1:8000


# Frontend Instructions

## Setup
```bash
npm install
npm install axios
npm run dev
```
Frontend runs on http://localhost:5173

# To Test everything
1. Start backend (uvicorn app.main:app --reload)

2. Start frontend (npm run dev)

3. Open http://localhost:5173 (you should see API + DB status)

