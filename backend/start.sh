#!/bin/bash
# Start script for Railway deployment
# Railway sets PORT environment variable

# Use PORT if set, otherwise default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
exec uvicorn main_webull:app --host 0.0.0.0 --port $PORT
