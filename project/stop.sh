#!/usr/bin/env bash

# Stop all or specific services
# Usage:
#   ./stop.sh           -> stop semua
#   ./stop.sh python    -> stop Python backend saja
#   ./stop.sh go        -> stop Go backend saja
#   ./stop.sh frontend  -> stop Frontend saja

PROJECT_DIR=$(dirname "$(realpath "$0")")
LOG_DIR="$PROJECT_DIR/logs"

TARGET="${1:-all}"

stop_service() {
    local name=$1
    local pid_file=$2
    local port=$3
    local fallback_pattern=$4

    echo "Stopping $name..."
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if kill -0 $PID 2>/dev/null; then
            kill $PID && echo "$name stopped [PID: $PID]."
        else
            echo "$name not running."
        fi
        rm -f "$pid_file"
    else
        pkill -f "$fallback_pattern" && echo "$name killed." || echo "No $name process found."
    fi

    if [ -n "$port" ]; then
        lsof -t -i:$port | xargs kill -9 2>/dev/null && echo "Port $port cleared." || true
    fi
}

echo "=============== STOPPING: $TARGET ==============="

case "$TARGET" in
    python)
        stop_service "Python Backend" "$LOG_DIR/backend_py.pid" 8000 "uvicorn api.main"
        ;;
    go)
        stop_service "Go Backend" "$LOG_DIR/backend_go.pid" 8080 "go-api/cmd/api/main.go"
        ;;
    frontend)
        stop_service "Frontend" "$LOG_DIR/frontend.pid" "" "next dev"
        rm -f "$PROJECT_DIR/ui/.next/dev/lock"
        ;;
    all|*)
        stop_service "Python Backend" "$LOG_DIR/backend_py.pid" 8000 "uvicorn api.main"
        stop_service "Go Backend" "$LOG_DIR/backend_go.pid" 8080 "go-api/cmd/api/main.go"
        stop_service "Frontend" "$LOG_DIR/frontend.pid" "" "next dev"
        rm -f "$PROJECT_DIR/ui/.next/dev/lock"
        ;;
esac

echo "================================================="
echo "Done."
