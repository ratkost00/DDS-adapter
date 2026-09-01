#!/bin/bash

###############################################################################
# Adapter vs. mpapi Rate Sweep Script
#
# Runs api_benchmark.py's subscriber and publisher back-to-back for each
# (impl, interval) pair, appending each run's summary latency stats (one row
# per run -- see api_benchmark.py's --out) into one CSV so both
# implementations' results land in the same comparable dataset. Run this
# script multiple times to accumulate repeated runs per (impl, interval),
# then use aggregate_results.py to average them into one stable number per
# rate point for the paper.
#
# mpapi.py (vendored, content-identical copy of ptbfla/ptbfla_pkg/mpapi.py)
# is never modified -- api_benchmark.py only imports and calls it, same as
# any PTB-FLA application would.
#
# Usage:
#   ./compare_sweep.sh                          # sweep the default interval list, both impls, once
#   ./compare_sweep.sh 0.001 0.005 0.01         # sweep custom intervals
#   IMPLS="mpapi" ./compare_sweep.sh            # mpapi only, if adapter doesn't need re-running
#   REPEATS=5 ./compare_sweep.sh                # repeat the whole sweep 5x, for aggregate_results.py
#   CONTINUE_ON_FAILURE=true ./compare_sweep.sh # log a failed run and move on instead of aborting
#
# Tune via environment variables:
#   IMPLS (default: "adapter mpapi"), REPEATS (default: 1),
#   CONTINUE_ON_FAILURE (default: false), COUNT, SIZE, TIMEOUT, DRAIN_WAIT, OUT, PORT
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

IMPLS="${IMPLS:-adapter mpapi}"
REPEATS="${REPEATS:-1}"
CONTINUE_ON_FAILURE="${CONTINUE_ON_FAILURE:-false}"
COUNT="${COUNT:-500}"
SIZE="${SIZE:-0}"
TIMEOUT="${TIMEOUT:-10}"
DRAIN_WAIT="${DRAIN_WAIT:-2}"
OUT="${OUT:-api_comparison_results.csv}"
PORT="${PORT:-7000}"

# 0 = as-fast-as-possible burst; the rest are paced sends (seconds between messages)
# -- same 14-point log sequence used for both the adapter and mpapi sweeps
DEFAULT_INTERVALS=(0 0.000001 0.000002 0.000005 0.00001 0.00002 0.00005 0.0001 0.0002 0.0005 0.001 0.002 0.005 0.01)
if [ "$#" -gt 0 ]; then
    INTERVALS=("$@")
else
    INTERVALS=("${DEFAULT_INTERVALS[@]}")
fi

cd "$SCRIPT_DIR"

if [ ! -f "$SCRIPT_DIR/mpapi.py" ]; then
    log_error "mpapi.py not found in $SCRIPT_DIR -- vendor a copy of ptbfla_pkg/mpapi.py there first."
    exit 1
fi

FAILURES=0

for run in $(seq 1 "$REPEATS"); do
    for impl in $IMPLS; do
        for interval in "${INTERVALS[@]}"; do
            log_info "[run $run/$REPEATS][$impl] Running interval=${interval}s (count=$COUNT, size=$SIZE)..."

            python3 api_benchmark.py subscriber --impl "$impl" --count "$COUNT" --interval "$interval" \
                --size "$SIZE" --timeout "$TIMEOUT" --out "$OUT" --port "$PORT" &
            sub_pid=$!

            sleep 1

            run_failed=false
            if ! python3 api_benchmark.py publisher --impl "$impl" --count "$COUNT" --interval "$interval" \
                --size "$SIZE" --drain-wait "$DRAIN_WAIT" --port "$PORT"; then
                log_error "[run $run/$REPEATS][$impl] Publisher failed for interval=${interval}s"
                kill "$sub_pid" 2>/dev/null || true
                run_failed=true
            fi

            if ! wait "$sub_pid"; then
                if [ "$run_failed" = false ]; then
                    log_error "[run $run/$REPEATS][$impl] Subscriber failed for interval=${interval}s"
                fi
                run_failed=true
            fi

            if [ "$run_failed" = true ]; then
                FAILURES=$((FAILURES + 1))
                if [ "$CONTINUE_ON_FAILURE" = "true" ]; then
                    log_error "[run $run/$REPEATS][$impl] interval=${interval}s failed -- continuing (CONTINUE_ON_FAILURE=true)"
                    continue
                fi
                exit 1
            fi
        done
    done
done

log_info "Comparison sweep complete ($REPEATS repeat(s), $FAILURES failed run(s)). Results appended to $OUT"