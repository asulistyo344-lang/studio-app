#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ ! -f ".env" ]; then
  echo "No .env found — this is a redeploy script, not first-time setup. Run setup.sh first."
  exit 1
fi

if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
  echo "Uncommitted changes found in $REPO_ROOT — resolve or stash them before deploying, so 'git pull' doesn't collide with local edits."
  git -C "$REPO_ROOT" status --short
  exit 1
fi

echo "Pulling latest..."
git -C "$REPO_ROOT" pull

echo "Installing dependencies..."
venv/bin/python3.11 -m pip install -r requirements.txt

echo "Running Alembic migrations..."
venv/bin/alembic upgrade head

echo "Restarting PM2 processes..."
pm2 restart studio-backend studio-worker

echo "Deploy complete."
pm2 status
