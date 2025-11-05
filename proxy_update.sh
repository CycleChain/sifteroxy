#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/sifteroxy"   # Directory where sifteroxy.py is located
PYTHON="/usr/bin/python3"      # Use venv/bin/python if using virtual environment
OUT_TXT="$APP_DIR/proxies_alive.txt"
METRICS_DIR="$APP_DIR/metrics"
LOG_DIR="$APP_DIR/logs"
LOCK_FILE="$APP_DIR/.proxy_update.lock"

mkdir -p "$METRICS_DIR" "$LOG_DIR"

# Prevent concurrent runs (second run exits silently)
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

TS="$(date +'%Y%m%d-%H%M%S')"
METRICS_JSON="$METRICS_DIR/metrics-$TS.json"
LOG_FILE="$LOG_DIR/run-$TS.log"

cd "$APP_DIR"
"$PYTHON" sifteroxy.py \
  --timeout 5 \
  --concurrency 128 \
  --test-url "https://httpbin.org/ip" \
  --out "$OUT_TXT" \
  --metrics "$METRICS_JSON" \
  --log-level INFO \
  > "$LOG_FILE" 2>&1

# Create symlink to latest metrics
ln -sfn "$METRICS_JSON" "$METRICS_DIR/latest.json"

# Clean up old logs and metrics (older than 7 days)
find "$LOG_DIR" -type f -mtime +7 -delete || true
find "$METRICS_DIR" -type f -name 'metrics-*.json' -mtime +7 -delete || true