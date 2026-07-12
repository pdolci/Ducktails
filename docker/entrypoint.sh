#!/bin/sh
# Container entrypoint: prepare the database, then serve the app.
set -e

echo "[ducktails] Seeding database (idempotent)..."
flask --app run seed

echo "[ducktails] Starting gunicorn on 0.0.0.0:8000..."
# SQLite + a couple of sync workers is plenty for this low-traffic app.
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 60 run:app
