#!/bin/bash

###############################################################################
# Benchmark Rate Sweep Script
#
# Runs benchmark.py's subscriber and publisher back-to-back for each interval
# below, accumulating every run's per-message latencies into one CSV (see
# benchmark.py's --out) for later analysis.
#
# Usage:
#   ./sweep.sh                          # sweep the default interval list
#   ./sweep.sh 0.001 0.005 0.01 0.05    # sweep custom intervals (seconds)
#
# Tune via environment variables:
#   COUNT, SIZE, TIMEOUT, DRAIN_WAIT, OUT
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COUNT="${COUNT:-500}"
SIZE="${SIZE:-0}"
TIMEOUT="${TIMEOUT:-10}"
DRAIN_WAIT="${DRAIN_WAIT:-2}"
OUT="${OUT:-benchmark_results.csv}"

# 0 = as-fast-as-possible burst; the rest are paced sends (seconds between messages)
DEFAULT_INTERVALS=(0 0.001 0.002 0.005 0.01 0.02 0.05 0.1)
if [ "$#" -gt 0 ]; then
    INTERVALS=("$@")
else
    INTERVALS=("${DEFAULT_INTERVALS[@]}")
fi

cd "$SCRIPT_DIR"

for interval in "${INTERVALS[@]}"; do
    log_info "Running interval=${interval}s (count=$COUNT, size=$SIZE)..."

    python3 benchmark.py subscriber --count "$COUNT" --interval "$interval" --size "$SIZE" --timeout "$TIMEOUT" --out "$OUT" &
    sub_pid=$!

    sleep 1

    if ! python3 benchmark.py publisher --count "$COUNT" --interval "$interval" --size "$SIZE" --drain-wait "$DRAIN_WAIT"; then
        log_error "Publisher failed for interval=${interval}s"
        kill "$sub_pid" 2>/dev/null || true
        exit 1
    fi

    wait "$sub_pid"
done

log_info "Sweep complete. Results appended to $OUT"