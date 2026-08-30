#!/bin/bash
set -e

# Run database migrations if configured
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Running database migrations via Alembic..."
    alembic upgrade head || echo "Migration notice: DB migration step failed or database already up-to-date."
fi

# Fetch PORT from environment (Cloud Run injects PORT dynamically, defaulting to 8000 for local docker)
APP_PORT="${PORT:-8000}"
echo "Starting Uvicorn server on port ${APP_PORT}..."

exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
