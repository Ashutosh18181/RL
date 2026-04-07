# ─── Stage 1: Build Next.js frontend ─────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install --frozen-lockfile

# Copy source and build static export
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python backend ──────────────────────────────────────────────────
FROM python:3.12-slim AS final

WORKDIR /app

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend + env + baseline
COPY env/ ./env/
COPY backend/ ./backend/
COPY baseline/ ./baseline/

# Copy built frontend static files
COPY --from=frontend-builder /app/frontend/out ./frontend/out

# Expose port
EXPOSE 8000

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Start FastAPI (serves API + frontend static files)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
