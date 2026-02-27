#!/usr/bin/env bash
# Cloudflare Quick Tunnel — frontend only (port 3000)
# Usage: ./tunnel.sh

LOGS="$(dirname "$0")/project/logs"
mkdir -p "$LOGS"

echo "🚇 Starting Cloudflare tunnel for UI (port 3000)..."

cloudflared tunnel --config /dev/null --url http://localhost:3000 > "$LOGS/tunnel_ui.log" 2>&1 &
UI_PID=$!
echo "$UI_PID" > "$LOGS/tunnel.pid"

echo "⏳ Waiting for tunnel URL..."
for i in {1..10}; do
  UI_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOGS/tunnel_ui.log" 2>/dev/null | head -1)
  [ -n "$UI_URL" ] && break
  sleep 2
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🖥  Frontend UI : ${UI_URL:-'gagal – cek logs/tunnel_ui.log'}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Stop: kill \$(cat project/logs/tunnel.pid)"
