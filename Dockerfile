# Ducktails — production image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run \
    # SQLite database lives on a mounted volume so data survives restarts.
    DATABASE_URL=sqlite:////data/ducktails.db

WORKDIR /app

# Install Python deps first for better layer caching. gunicorn is the
# production WSGI server (added here, not in requirements.txt, so local
# Windows dev is unaffected).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# App source
COPY . .

# Non-root user + writable data dir. A named volume mounted at /data inherits
# this ownership on first creation, so the app can write the SQLite file.
RUN useradd --create-home appuser \
    && mkdir -p /data \
    && chmod +x docker/entrypoint.sh \
    && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

# Seed (idempotent) then launch gunicorn.
ENTRYPOINT ["sh", "docker/entrypoint.sh"]
