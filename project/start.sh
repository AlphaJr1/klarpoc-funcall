#!/usr/bin/env bash

# Start all services: Python Backend (FastAPI), Go Backend (Gin), Frontend (Next.js)

PROJECT_DIR=$(dirname "$(realpath "$0")")
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

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

free_port() {
    local port=$1
    local pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        echo "Port $port is in use by PID(s): $pid. Killing..."
        kill -9 $pid
    fi
}

BACKEND_PY_LOG="$LOG_DIR/backend_api.log"
BACKEND_GO_LOG="$LOG_DIR/backend_go.log"
FRONTEND_LOG="$LOG_DIR/frontend_ui.log"

echo "=============== STARTING SERVICES ==============="

# 1. Python Backend (FastAPI) - port 8000
free_port 8000
rotate_log "$BACKEND_PY_LOG"
echo "Starting Python Backend (FastAPI)..."
cd "$PROJECT_DIR"
if [ ! -d "../.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv ../.venv
fi
../.venv/bin/python3 -m ensurepip --upgrade > /dev/null 2>&1
../.venv/bin/python3 -m pip install -q fastapi uvicorn python-dotenv openai pydantic requests pyyaml
nohup ../.venv/bin/python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_PY_LOG" 2>&1 &
echo $! > "$LOG_DIR/backend_py.pid"
echo "Python Backend started [PID: $(cat $LOG_DIR/backend_py.pid)]. Log: $BACKEND_PY_LOG"

# 2. Go Backend (Gin) - port 8080
free_port 8080
rotate_log "$BACKEND_GO_LOG"
echo "Starting Go Backend (Gin)..."
cd "$PROJECT_DIR/go-api"
nohup go run cmd/api/main.go > "$BACKEND_GO_LOG" 2>&1 &
echo $! > "$LOG_DIR/backend_go.pid"
echo "Go Backend started [PID: $(cat $LOG_DIR/backend_go.pid)]. Log: $BACKEND_GO_LOG"

# 3. Frontend (Next.js)
free_port 3000
rotate_log "$FRONTEND_LOG"
echo "Starting Frontend (Next.js)..."
cd "$PROJECT_DIR/ui"
npm install --silent
nohup npm start > "$FRONTEND_LOG" 2>&1 &
echo $! > "$LOG_DIR/frontend.pid"
echo "Frontend started [PID: $(cat $LOG_DIR/frontend.pid)]. Log: $FRONTEND_LOG"


echo "================================================="
echo "Services Local:"
echo "  Python API  -> http://localhost:8000"
echo "  Go API      -> http://localhost:8080"
echo "  Frontend    -> http://localhost:3000"
echo "================================================="
