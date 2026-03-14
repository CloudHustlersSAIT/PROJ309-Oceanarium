#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"

DB_USER="oceanarium"
DB_NAME="oceanarium"

echo "▸ Ensuring PostgreSQL container is running..."
docker compose -f "$COMPOSE_FILE" up db -d

echo "▸ Waiting for PostgreSQL to be healthy..."
until docker compose -f "$COMPOSE_FILE" exec db pg_isready -U "$DB_USER" -q 2>/dev/null; do
  sleep 1
done
echo "  ✓ PostgreSQL is ready"

echo "▸ Dropping and recreating database '$DB_NAME'..."
docker compose -f "$COMPOSE_FILE" exec db \
  psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME WITH (FORCE);"
docker compose -f "$COMPOSE_FILE" exec db \
  psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
echo "  ✓ Database recreated"

ALEMBIC="$BACKEND_DIR/venv/bin/alembic"
if [ ! -f "$ALEMBIC" ]; then
  echo "✗ venv not found — run ./start-backend.sh first to create it" >&2
  exit 1
fi

echo "▸ Running migrations to head..."
"$ALEMBIC" -c "$BACKEND_DIR/alembic.ini" upgrade head
echo "  ✓ Migrations applied"

echo "▸ Creating default users..."
docker compose -f "$COMPOSE_FILE" exec db \
  psql -U "$DB_USER" -d "$DB_NAME" -c "
    INSERT INTO users (username, email, password_hash, full_name, role, is_active)
    VALUES
      ('admin', 'evandro.maciel.silva@gmail.com', '123456', 'Admin User', 'admin', true);
  "
echo "  ✓ Users created"

echo ""
echo "Done! Database is clean, migrated, and ready to use."
echo "  Admin: evandro.maciel.silva@gmail.com (admin)"
