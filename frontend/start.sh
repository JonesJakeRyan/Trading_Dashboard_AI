#!/bin/sh
# Start script for Railway deployment - Frontend
# Railway sets PORT environment variable

# Use PORT if set, otherwise default to 5173
PORT=${PORT:-5173}

echo "Starting Vite dev server on port $PORT"
exec npm run dev -- --host 0.0.0.0 --port $PORT
