#!/usr/bin/env bash

# Restart all or specific services
# Usage:
#   ./restart.sh           -> restart semua
#   ./restart.sh python    -> restart Python backend saja
#   ./restart.sh go        -> restart Go backend saja
#   ./restart.sh frontend  -> restart Frontend saja

PROJECT_DIR=$(dirname "$(realpath "$0")")
LOG_DIR="$PROJECT_DIR/logs"

TARGET="${1:-all}"

rotate_log() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local filename=$(basename "$log_file")
        mkdir -p "$LOG_DIR/backup"
        mv "$log_file" "$LOG_DIR/backup/${filename}_bak_${timestamp}"
    fi
}

stop_service() {
    local name=$1
    local pid_file=$2
    local port=$3
    local fallback_pattern=$4
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        kill -0 $PID 2>/dev/null && kill $PID
        rm -f "$pid_file"
    else
        pkill -f "$fallback_pattern" || true
    fi
    [ -n "$port" ] && lsof -t -i:$port | xargs kill -9 2>/dev/null || true
    sleep 1
}

echo "=============== RESTARTING: $TARGET ==============="

case "$TARGET" in
    python)
        stop_service "Python Backend" "$LOG_DIR/backend_py.pid" 8000 "uvicorn api.main"
        rotate_log "$LOG_DIR/backend_api.log"
        echo "Starting Python Backend..."
        cd "$PROJECT_DIR"
        nohup ../.venv/bin/python3.14 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend_api.log" 2>&1 &
        echo $! > "$LOG_DIR/backend_py.pid"
        echo "Python Backend restarted [PID: $(cat $LOG_DIR/backend_py.pid)]."
        ;;
    go)
        stop_service "Go Backend" "$LOG_DIR/backend_go.pid" 8080 "go-api/cmd/api/main.go"
        rotate_log "$LOG_DIR/backend_go.log"
        echo "Starting Go Backend..."
        cd "$PROJECT_DIR/go-api"
        nohup go run cmd/api/main.go > "$LOG_DIR/backend_go.log" 2>&1 &
        echo $! > "$LOG_DIR/backend_go.pid"
        echo "Go Backend restarted [PID: $(cat $LOG_DIR/backend_go.pid)]."
        ;;
    frontend)
        stop_service "Frontend" "$LOG_DIR/frontend.pid" "" "next dev"
        rm -f "$PROJECT_DIR/ui/.next/dev/lock"
        rotate_log "$LOG_DIR/frontend_ui.log"
        echo "Starting Frontend..."
        cd "$PROJECT_DIR/ui"
        nohup npm run dev > "$LOG_DIR/frontend_ui.log" 2>&1 &
        echo $! > "$LOG_DIR/frontend.pid"
        echo "Frontend restarted [PID: $(cat $LOG_DIR/frontend.pid)]."
        ;;
    all|*)
        bash "$PROJECT_DIR/stop.sh"
        sleep 2
        bash "$PROJECT_DIR/start.sh"
        ;;
esac

echo "=============== RESTART COMPLETE =================="
