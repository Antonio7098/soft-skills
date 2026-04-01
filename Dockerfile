FROM python:3.12-slim

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .
COPY backend/src/ ./src/
COPY backend/alembic.ini ./
COPY backend/alembic/ ./alembic/

ENV PYTHONPATH=src
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["sh", "-c", "PYTHONPATH=src alembic upgrade heads && PYTHONPATH=src uvicorn soft_skills_backend.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
