#!/usr/bin/env bash
# Claude Code Hook → Agent Monitor
# Reads JSON from stdin (provided by Claude Code hooks) and POSTs it to the monitor server.

MONITOR_URL="${AGENT_MONITOR_URL:-http://localhost:7778/event}"
LOGFILE="/tmp/hook-debug.log"

# Read the hook payload from stdin
payload=$(cat)

echo "$(date): Hook fired. Payload length: ${#payload}" >> "$LOGFILE"
echo "$(date): Payload: $payload" >> "$LOGFILE"

# POST to the monitor server (fire-and-forget, don't block Claude Code)
result=$(curl -s -X POST "$MONITOR_URL" \
  -H "Content-Type: application/json" \
  -d "$payload" 2>&1)

echo "$(date): Curl result: $result" >> "$LOGFILE"

# Always exit 0 so we never block Claude Code
exit 0
