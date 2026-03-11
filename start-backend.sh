#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"

echo "▸ Starting PostgreSQL container..."
docker compose -f "$REPO_ROOT/docker-compose.yml" up db -d

echo "▸ Waiting for PostgreSQL to be healthy..."
until docker compose -f "$REPO_ROOT/docker-compose.yml" exec db pg_isready -U oceanarium -q 2>/dev/null; do
  sleep 1
done
echo "  ✓ PostgreSQL is ready"

if [ ! -d "$BACKEND_DIR/venv" ]; then
  echo "▸ Creating virtual environment..."
  python3.11 -m venv "$BACKEND_DIR/venv"
  echo "▸ Installing dependencies..."
  "$BACKEND_DIR/venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

echo "▸ Running migrations..."
"$BACKEND_DIR/venv/bin/alembic" -c "$BACKEND_DIR/alembic.ini" upgrade head

echo "▸ Starting backend on http://127.0.0.1:8000"
echo "  Swagger docs: http://127.0.0.1:8000/docs"
"$BACKEND_DIR/venv/bin/uvicorn" app.main:app --reload --app-dir "$BACKEND_DIR"
