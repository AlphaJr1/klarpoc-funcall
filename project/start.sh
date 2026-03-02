#!/usr/bin/env bash

# Script Description: Start up the frontend (Next.js) and backend (FastAPI) applications in the background.
# Logs are routed to specific log files, and rotated if they already exist.

PROJECT_DIR=$(dirname "$(realpath "$0")")
LOG_DIR="$PROJECT_DIR/logs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Helper function to rotate logs
rotate_log() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local filename=$(basename "$log_file")
        mkdir -p "$LOG_DIR/backup"
        mv "$log_file" "$LOG_DIR/backup/${filename}_bak_${timestamp}"
        echo "Rotated log: $log_file -> backup/${filename}_bak_${timestamp}"
    fi
}

echo "=============== STARTING SERVICES ==============="

# Define log files
BACKEND_LOG="$LOG_DIR/backend_api.log"
FRONTEND_LOG="$LOG_DIR/frontend_ui.log"

# Rotate existing logs
rotate_log "$BACKEND_LOG"
rotate_log "$FRONTEND_LOG"

# 1. Start Backend (FastAPI)
echo "Starting Backend API (FastAPI)..."
cd "$PROJECT_DIR"

# Ensure fastapi and uvicorn are installed
pip install -q fastapi uvicorn python-dotenv openai

# Start the API server in the background
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$LOG_DIR/backend.pid"
echo "Backend started with PID: $BACKEND_PID. Log: $BACKEND_LOG"


# 2. Start Frontend (Next.js)
echo "Starting Frontend UI (Next.js)..."
cd "$PROJECT_DIR/ui"

# Ensure dependencies are installed (optional but safe)
npm install --silent

# Start the frontend server in the background
nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
echo "Frontend started with PID: $FRONTEND_PID. Log: $FRONTEND_LOG"

echo "================================================="
echo "All services started successfully in the background."
echo "You can view logs with:"
echo "  tail -f $BACKEND_LOG"
echo "  tail -f $FRONTEND_LOG"
echo "================================================="
