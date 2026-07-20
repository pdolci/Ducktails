#!/bin/sh
# Container entrypoint: prepare the database, then serve the app.
set -e

echo "[ducktails] Seeding database (idempotent)..."
flask --app run seed

echo "[ducktails] Starting gunicorn on 0.0.0.0:8000..."
# SQLite serialises writes, so a single worker avoids lock contention.
# --preload loads the app once in the master before forking.
exec gunicorn --bind 0.0.0.0:8000 --workers 1 --timeout 120 --preload run:app
