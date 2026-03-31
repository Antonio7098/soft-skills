#!/bin/sh
set -e

# Cloud Run sets PORT, default to 8080
export PORT=${PORT:-8080}

echo "Starting SoftSkills on port $PORT"

# Update nginx config to use the correct port
if [ -f /etc/nginx/nginx.conf ]; then
    sed -i "s/listen 8080/listen $PORT/" /etc/nginx/nginx.conf
else
    echo "Error: nginx.conf not found" >&2
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
PYTHONPATH=src alembic upgrade heads

# Start backend in background
echo "Starting backend on port 8000"
PYTHONPATH=src uvicorn soft_skills_backend.app:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 &

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 2

# Start nginx in foreground
echo "Starting nginx on port $PORT"
exec nginx -g 'daemon off;'
