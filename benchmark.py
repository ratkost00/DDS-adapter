"""
Latency/throughput benchmark for the DDS adapter.

Talks to the adapter's Writer/Reader classes directly (not through the
msg_passing_api broadcast/peer-discovery layer), to measure the DDS pub/sub
path itself. The timestamp and sequence number are smuggled through the
existing Adapter.message string field as "seq:send_time:padding" -- no
changes to the IDL or the generated library are needed.

Run subscriber and publisher in two separate terminals (same machine, so
they share one wall clock):

    python3 benchmark.py subscriber --count 1000
    python3 benchmark.py publisher --count 1000
"""
import argparse
import csv
import time
from multiprocessing import Queue
from queue import Empty

from src.adapter.AdapterPublisher import Writer
from src.adapter.AdapterSubscriber import Reader

TOPIC_NAME = "BenchTopic"
TOPIC = "bench"


def run_publisher(count: int, payload_size: int, interval: float, drain_wait: float) -> None:
    writer = Writer(topicName=TOPIC_NAME, topic=TOPIC)
    writer.wait_discovery()

    padding = "x" * payload_size
    start = time.time()
    for seq in range(count):
        writer.write(message=f"{seq}:{time.time()}:{padding}")
        if interval > 0:
            time.sleep(interval)
    elapsed = time.time() - start

    print(f"Sent {count} messages in {elapsed:.3f}s ({count / elapsed:.1f} msg/s)")

    # RELIABLE delivery of a burst isn't necessarily complete just because write()
    # returned -- give the RTPS heartbeat/ACKNACK retransmission cycle time to
    # finish before tearing the writer down, or un-acked samples get dropped.
    time.sleep(drain_wait)
    writer.delete()


def run_subscriber(count: int, timeout: float, out_path: str) -> None:
    queue: Queue = Queue()
    reader = Reader(topicName=TOPIC_NAME, topic=TOPIC, queue=queue)

    received = []
    start = time.time()
    for _ in range(count):
        try:
            message = queue.get(timeout=timeout)
        except Empty:
            print(f"Timed out waiting for a message ({len(received)}/{count} received).")
            break
        recv_time = time.time()
        seq_str, send_time_str, _ = message.split(":", 2)
        received.append((int(seq_str), float(send_time_str), recv_time))
    elapsed = time.time() - start
    reader.delete()

    if not received:
        print("No messages received.")
        return

    latencies_ms = sorted((r - s) * 1000 for _, s, r in received)
    n = len(latencies_ms)

    def pct(p: float) -> float:
        return latencies_ms[min(n - 1, int(n * p))]

    print(f"Received {n} messages in {elapsed:.3f}s ({n / elapsed:.1f} msg/s)")
    print(f"Dropped: {count - n} of {count}")
    print(
        f"Latency ms - min: {latencies_ms[0]:.3f}, avg: {sum(latencies_ms) / n:.3f}, "
        f"p50: {pct(0.50):.3f}, p95: {pct(0.95):.3f}, p99: {pct(0.99):.3f}, "
        f"max: {latencies_ms[-1]:.3f}"
    )

    if out_path:
        with open(out_path, "w", newline="") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["seq", "send_time", "recv_time", "latency_ms"])
            for seq, s, r in received:
                csv_writer.writerow([seq, s, r, (r - s) * 1000])
        print(f"Wrote per-message results to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="DDS adapter latency/throughput benchmark")
    parser.add_argument("role", choices=["publisher", "subscriber"])
    parser.add_argument("--count", type=int, default=1000, help="number of messages")
    parser.add_argument("--size", type=int, default=0, help="publisher: extra padding bytes per message")
    parser.add_argument("--interval", type=float, default=0.0, help="publisher: seconds between sends (0 = as fast as possible)")
    parser.add_argument("--drain-wait", type=float, default=2.0, help="publisher: seconds to wait after sending before tearing down the writer, so reliable retransmission can finish")
    parser.add_argument("--timeout", type=float, default=10.0, help="subscriber: seconds to wait per message before giving up")
    parser.add_argument("--out", type=str, default="bench_results.csv", help="subscriber: CSV output path (empty to skip)")
    args = parser.parse_args()

    if args.role == "publisher":
        run_publisher(args.count, args.size, args.interval, args.drain_wait)
    else:
        run_subscriber(args.count, args.timeout, args.out)


if __name__ == "__main__":
    main()