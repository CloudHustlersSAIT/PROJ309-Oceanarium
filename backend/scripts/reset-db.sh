#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Stopping containers and removing volumes..."
docker compose down -v 2>/dev/null || true

echo "==> Starting fresh PostgreSQL..."
docker compose up -d db

echo "==> Waiting for PostgreSQL to be ready..."
until docker compose exec db pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done
echo "    PostgreSQL is healthy."

echo "==> Creating test database..."
docker compose exec db psql -U postgres -c "CREATE DATABASE oceanarium_test" 2>/dev/null || true

echo "==> Running Alembic migrations..."
python3 -m alembic upgrade head

echo ""
echo "Database is ready!"

if [ "${1:-}" = "--seed" ]; then
  echo "==> Seeding data via /sync/trigger (backend must be running on :8000)..."
  curl -sf -X POST http://localhost:8000/sync/trigger \
    && echo "    Seed complete!" \
    || echo "    Seed failed — is the backend running on port 8000?"
fi
