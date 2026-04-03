#!/bin/bash
set -e

echo "Running database migrations..."
cd /app
PYTHONPATH=/app/src alembic -c alembic/alembic.ini upgrade head

echo "Starting API server..."
exec uvicorn drillsense.main:app --host 0.0.0.0 --port 8000
