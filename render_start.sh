#!/bin/bash
echo "Starting Render single-container combined service..."

# Trap exit signals so they cascade down to the child processes
trap 'kill %1; kill %2' SIGINT SIGTERM SIGQUIT

# 1. Start the Background Worker (Celery/RQ equivalent worker.py) in the background
echo "Starting Worker..."
cd /app/services/worker
python worker.py &
WORKER_PID=$!

# 2. Start the FastAPI Application
echo "Starting API..."
cd /app/services/api
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &
API_PID=$!

# Wait for any process to exit
wait -n

echo "One of the processes exited. Shutting down container."
exit 1
