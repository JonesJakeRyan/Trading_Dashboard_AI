FROM node:18-slim AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy frontend build from builder stage
COPY --from=frontend-builder /frontend/dist/ ./frontend/dist/

WORKDIR /app/backend

# Start command
CMD ["bash", "start.sh"]
