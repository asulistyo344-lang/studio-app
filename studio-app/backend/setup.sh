#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "python3.11 not found. Installing..."
  apt-get update
  apt-get install -y python3.11 python3.11-venv
fi

if [ ! -d "venv" ]; then
  python3.11 -m venv venv
fi

venv/bin/python3.11 -m pip install --upgrade pip
venv/bin/python3.11 -m pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit it with real values before running."
fi

mkdir -p logs storage

# --- PostgreSQL: install/start if not already available, then ensure the app's db exists ---
if ! command -v psql >/dev/null 2>&1; then
  echo "PostgreSQL not found. Installing..."
  apt-get update
  apt-get install -y postgresql
fi

if ! pg_isready -q 2>/dev/null; then
  echo "Starting PostgreSQL..."
  service postgresql start
fi

DB_URL="$(grep -E '^DATABASE_URL=' .env | cut -d= -f2-)"
DB_USER="$(echo "$DB_URL" | sed -E 's#.*://([^:]+):.*#\1#')"
DB_PASS="$(echo "$DB_URL" | sed -E 's#.*://[^:]+:([^@]+)@.*#\1#')"
DB_NAME="$(echo "$DB_URL" | sed -E 's#.*/([^/?]+)(\?.*)?$#\1#')"

if [ -z "$DB_PASS" ] || [ "$DB_PASS" = "your_studio_db_password_here" ]; then
  echo "WARNING: DATABASE_URL in .env still has placeholder values — edit .env with real credentials, then re-run setup.sh to create the db and run migrations."
else
  echo "Ensuring database role/db exist for '$DB_NAME'..."
  sudo -u postgres psql -v ON_ERROR_STOP=1 >/dev/null <<-EOSQL
		DO \$\$
		BEGIN
		   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
		      CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASS';
		   END IF;
		END
		\$\$;
	EOSQL
  sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER"

  echo "Running Alembic migrations..."
  venv/bin/alembic upgrade head
fi

# --- Redis: install/start if not already available ---
if ! command -v redis-server >/dev/null 2>&1; then
  echo "Redis not found. Installing..."
  apt-get update
  apt-get install -y redis-server
fi

if ! redis-cli ping >/dev/null 2>&1; then
  echo "Starting Redis..."
  service redis-server start
fi

echo "Setup complete."
echo "Run backend with: venv/bin/python3.11 -m app.main"
echo "Run worker with:  venv/bin/arq app.workers.generation_worker.WorkerSettings"
