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
