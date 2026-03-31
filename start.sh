#!/bin/sh
set -e

export PORT=${PORT:-8080}

echo "Starting SoftSkills on port $PORT"

sed -i "s/listen 8080/listen $PORT/" /etc/nginx/nginx.conf

echo "Running database migrations..."
PYTHONPATH=src alembic upgrade heads

echo "Starting backend on port 8000"
PYTHONPATH=src uvicorn soft_skills_backend.app:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 &

sleep 2

echo "Starting nginx on port $PORT"
exec nginx -g 'daemon off;'
