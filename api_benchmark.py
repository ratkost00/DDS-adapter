"""
Latency/throughput comparison between the DDS adapter's msg_passing_api and
PTB-FLA's original mpapi, measured at the same level: the five-function
sendMsg/rcvMsg/server_fun API both modules expose identically (that
equivalence is the adapter's whole drop-in-substitutability premise). This
does NOT modify ptbfla_pkg in any way -- it only imports and calls it,
exactly like a PTB-FLA application would.

mpapi.py in this directory is a verbatim copy of ptbfla/ptbfla_pkg/mpapi.py
(content-identical -- only line endings differ, LF here vs. CRLF there),
vendored onto this benchmarking branch so the comparison doesn't depend on
where the ptbfla repo happens to be checked out. It is never edited.

Both sides receive the identical wire format ("seq:send_time:padding") on
their multiprocessing.Queue: the adapter's ReaderListener queues the IDL
message string directly, and mpapi's server_fun round-trips the same string
through json.dumps/json.loads unchanged -- so one shared subscriber/parsing
path is used for both.

Usage (two terminals, same --port on both, same --impl on both):

    python3 api_benchmark.py subscriber --impl adapter --count 500 --port 7000
    python3 api_benchmark.py publisher  --impl adapter --count 500 --port 7000

    python3 api_benchmark.py subscriber --impl mpapi --count 500 --port 7000
    python3 api_benchmark.py publisher  --impl mpapi --count 500 --port 7000

Results append to --out (default api_comparison_results.csv) as one summary
row per subscriber run (min/avg/p50/p95/p99/max latency, received/dropped
counts, throughput), tagged with --impl and --interval, so both sides
accumulate into one comparable dataset. Re-running the same sweep (e.g. via
compare_sweep.sh) appends more rows for the same (impl, interval) rather than
overwriting -- use aggregate_results.py afterwards to average repeated runs
of the same rate point into a single stable number per point.
"""
import argparse
import csv
import os
import time
from datetime import datetime
from multiprocessing import Process, Queue
from queue import Empty

# ---------------------------------------------------------------------------
# Publisher side -- impl-specific setup, identical send-loop shape otherwise
# ---------------------------------------------------------------------------

def run_publisher_adapter(count: int, payload_size: int, interval: float, drain_wait: float, port: int) -> None:
    from src.message_api.msg_passing_api import MessageWriter, sendMsg

    writer_singleton = MessageWriter()
    writer_singleton.add_writer(port)
    writer_singleton.peers[port].wait_discovery()

    padding = "x" * payload_size
    start = time.time()
    for seq in range(count):
        sendMsg(port, f"{seq}:{time.time()}:{padding}")
        if interval > 0:
            time.sleep(interval)
    elapsed = time.time() - start
    print(f"[adapter] Sent {count} messages in {elapsed:.3f}s ({count / elapsed:.1f} msg/s)")

    # Same reasoning as benchmark.py: give RELIABLE's retransmission a chance
    # to finish before the writer's participant is torn down.
    time.sleep(drain_wait)
    writer_singleton.peers[port].delete()


def run_publisher_mpapi(count: int, payload_size: int, interval: float, port: int) -> None:
    from mpapi import sendMsg

    remote_address = ("localhost", port)
    padding = "x" * payload_size
    start = time.time()
    for seq in range(count):
        sendMsg(remote_address, f"{seq}:{time.time()}:{padding}")
        if interval > 0:
            time.sleep(interval)
    elapsed = time.time() - start
    print(f"[mpapi] Sent {count} messages in {elapsed:.3f}s ({count / elapsed:.1f} msg/s)")
    # No drain-wait equivalent: each sendMsg is its own synchronous TCP
    # connect/send/close, so there's no outstanding un-acked history to flush.


# ---------------------------------------------------------------------------
# Subscriber side -- impl-specific server_fun, shared receive/stats logic
# ---------------------------------------------------------------------------

SUMMARY_HEADER = [
    "run_timestamp", "impl", "interval", "size", "count",
    "received", "dropped", "elapsed_s", "rate_msg_s",
    "min_ms", "avg_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms",
]


def _append_summary_row(out_path: str, run_timestamp: str, impl: str, interval: float, size: int,
                         count: int, received: int, dropped: int, elapsed, stats) -> None:
    write_header = not (os.path.isfile(out_path) and os.path.getsize(out_path) > 0)
    rate = f"{received / elapsed:.3f}" if elapsed and elapsed > 0 else ""
    row = [
        run_timestamp, impl, interval, size, count, received, dropped,
        f"{elapsed:.6f}" if elapsed is not None else "", rate,
    ]
    row += [f"{stats[k]:.3f}" for k in ("min_ms", "avg_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms")] \
        if stats is not None else [""] * 6
    with open(out_path, "a", newline="") as f:
        csv_writer = csv.writer(f)
        if write_header:
            csv_writer.writerow(SUMMARY_HEADER)
        csv_writer.writerow(row)
    print(f"[{impl}] Appended summary row for this run to {out_path}")


def run_subscriber(impl: str, count: int, timeout: float, out_path: str, interval: float,
                    size: int, port: int) -> None:
    run_timestamp = datetime.now().isoformat(timespec="seconds")
    queue: Queue = Queue()

    # mpapi's server_fun blocks forever inside Listener.accept(), so it has
    # no choice but to run in its own process. The adapter's server_fun does
    # NOT need that -- MessageListener(...) returns immediately and Fast DDS
    # receives on its own internal thread regardless of what server_fun does
    # afterwards -- so constructing it in-process here matches benchmark.py's
    # methodology (no extra inter-process queue hand-off inflating latency
    # for a reason that has nothing to do with msg_passing_api itself).
    server_process = None
    if impl == "adapter":
        from src.message_api.msg_passing_api import MessageListener
        MessageListener(msg_queue=queue, local_port=port)
    else:
        from mpapi import server_fun
        server_process = Process(target=server_fun, args=(port, queue))
        server_process.start()

    received = []
    for _ in range(count):
        try:
            message = queue.get(timeout=timeout)
        except Empty:
            print(f"[{impl}] Timed out waiting for a message ({len(received)}/{count} received).")
            break
        recv_time = time.time()
        seq_str, send_time_str, _ = message.split(":", 2)
        received.append((int(seq_str), float(send_time_str), recv_time))

    if server_process is not None:
        server_process.terminate()
        server_process.join(timeout=5)

    dropped = count - len(received)

    if not received:
        print(f"[{impl}] No messages received.")
        if out_path:
            _append_summary_row(out_path, run_timestamp, impl, interval, size, count,
                                 received=0, dropped=dropped, elapsed=None, stats=None)
        return

    elapsed = received[-1][2] - received[0][2]
    latencies_ms = sorted((r - s) * 1000 for _, s, r in received)
    n = len(latencies_ms)

    def pct(p: float) -> float:
        return latencies_ms[min(n - 1, int(n * p))]

    stats = {
        "min_ms": latencies_ms[0],
        "avg_ms": sum(latencies_ms) / n,
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "p99_ms": pct(0.99),
        "max_ms": latencies_ms[-1],
    }

    rate = f"{n / elapsed:.1f} msg/s" if elapsed > 0 else "n/a (span too short to measure)"
    print(f"[{impl}] Received {n} messages in {elapsed:.3f}s ({rate})")
    print(f"[{impl}] Dropped: {dropped} of {count}")
    print(
        f"[{impl}] Latency ms - min: {stats['min_ms']:.3f}, avg: {stats['avg_ms']:.3f}, "
        f"p50: {stats['p50_ms']:.3f}, p95: {stats['p95_ms']:.3f}, p99: {stats['p99_ms']:.3f}, "
        f"max: {stats['max_ms']:.3f}"
    )

    if out_path:
        _append_summary_row(out_path, run_timestamp, impl, interval, size, count,
                             received=n, dropped=dropped, elapsed=elapsed, stats=stats)


def main() -> None:
    parser = argparse.ArgumentParser(description="Adapter vs. mpapi latency/throughput comparison")
    parser.add_argument("role", choices=["publisher", "subscriber"])
    parser.add_argument("--impl", choices=["adapter", "mpapi"], required=True)
    parser.add_argument("--count", type=int, default=500, help="number of messages")
    parser.add_argument("--size", type=int, default=0, help="extra padding bytes per message (publisher: applied; subscriber: recorded in --out)")
    parser.add_argument("--interval", type=float, default=0.0, help="seconds between sends (publisher: applied, 0 = as fast as possible; subscriber: recorded in --out)")
    parser.add_argument("--drain-wait", type=float, default=2.0, help="adapter publisher only: seconds to wait before writer teardown")
    parser.add_argument("--timeout", type=float, default=10.0, help="subscriber: seconds to wait per message before giving up")
    parser.add_argument("--out", type=str, default="api_comparison_results.csv", help="subscriber: CSV path to append this run's results to (empty to skip)")
    parser.add_argument("--port", type=int, default=7000, help="shared port/topic key: subscriber's local_port, publisher's remote address")
    args = parser.parse_args()

    if args.role == "publisher":
        if args.impl == "adapter":
            run_publisher_adapter(args.count, args.size, args.interval, args.drain_wait, args.port)
        else:
            run_publisher_mpapi(args.count, args.size, args.interval, args.port)
    else:
        run_subscriber(args.impl, args.count, args.timeout, args.out, args.interval,
                        args.size, args.port)


if __name__ == "__main__":
    main()