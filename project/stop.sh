#!/usr/bin/env bash

# Script Description: Shutdown the frontend and backend applications gracefully

PROJECT_DIR=$(dirname "$(realpath "$0")")
LOG_DIR="$PROJECT_DIR/logs"

echo "=============== STOPPING SERVICES ==============="

# Stop Backend System
if [ -f "$LOG_DIR/backend.pid" ]; then
    PID=$(cat "$LOG_DIR/backend.pid")
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Backend (FastAPI) [PID: $PID]..."
        kill $PID
        rm "$LOG_DIR/backend.pid"
        echo "Backend stopped."
    else
        echo "Backend is not running. PID file found and removed."
        rm "$LOG_DIR/backend.pid"
    fi
else
    echo "No Backend PID found. Looking manually..."
    pkill -f "uvicorn api.main" && echo "Killed backend processes." || echo "No matching backend processes found."
fi

# Pastikan port 8000 benar-benar bebas
lsof -t -i:8000 | xargs kill -9 2>/dev/null && echo "Port 8000 cleared." || true

# Stop Frontend System
if [ -f "$LOG_DIR/frontend.pid" ]; then
    PID=$(cat "$LOG_DIR/frontend.pid")
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Frontend (Next.js) [PID: $PID]..."
        kill $PID
        rm "$LOG_DIR/frontend.pid"
        echo "Frontend stopped."
    else
        echo "Frontend is not running. PID file found and removed."
        rm "$LOG_DIR/frontend.pid"
    fi
else
    echo "No Frontend PID found. Looking manually..."
    pkill -f "next dev" && echo "Killed frontend/next processes." || echo "No matching frontend processes found."
fi

# Bersihkan lock file Next.js
rm -f "$PROJECT_DIR/ui/.next/dev/lock"

echo "================================================="
echo "All services stopped."
