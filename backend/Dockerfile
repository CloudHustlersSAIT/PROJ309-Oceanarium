FROM python:3.11-slim

# Set working directory
WORKDIR /app

# 1. FIX CVE-2026-24049: Upgrade core build tools immediately
# This patches 'wheel' to version 0.46.2 or higher as required by Scout
RUN pip install --no-cache-dir --upgrade pip wheel setuptools


# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run the app (considering our files are in the app folder)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]