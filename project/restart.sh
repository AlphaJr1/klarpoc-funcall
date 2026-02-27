#!/usr/bin/env bash

# Script Description: Restart the frontend and backend applications gracefully

PROJECT_DIR=$(dirname "$(realpath "$0")")

echo "=============== RESTARTING SERVICES ==============="

# Call the shutdown script
bash "$PROJECT_DIR/stop.sh"

# Optional small delay to ensure ports are freed
sleep 2

# Call the startup script
bash "$PROJECT_DIR/start.sh"

echo "=============== RESTART COMPLETE =================="
