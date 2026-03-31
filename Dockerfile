# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build backend
FROM python:3.12-slim AS backend-build
WORKDIR /app/backend
RUN pip install --no-cache-dir hatchling
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .
COPY backend/src/ ./src/

# Stage 3: Runtime
FROM python:3.12-slim

# Install nginx and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY --from=backend-build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-build /usr/local/bin /usr/local/bin
COPY backend/src/ /app/backend/src/
COPY backend/alembic.ini /app/backend/
COPY backend/alembic/ /app/backend/alembic/

# Copy frontend build
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

WORKDIR /app/backend

# Set Python path
ENV PYTHONPATH=src

# Cloud Run sets PORT env var, default to 8080
ENV PORT=8080
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health/liveness || exit 1

# Run as root (required for nginx)
# For production, consider using a non-root user with proper nginx setup
CMD ["/app/start.sh"]
