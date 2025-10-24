FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy frontend build
COPY frontend/dist/ ./frontend/dist/

WORKDIR /app/backend

# Railway will provide the start command via service settings
