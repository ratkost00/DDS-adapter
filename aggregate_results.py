"""
Average repeated api_benchmark.py summary runs for the paper.

api_benchmark.py's --out CSV holds one summary row per subscriber run (see
its module docstring). Running compare_sweep.sh multiple times appends more
rows for the same (impl, interval, size) rate point rather than overwriting,
to smooth out run-to-run noise. This script groups rows by (impl, interval,
size) and averages every numeric column across however many repeated runs
that point has, producing one stable row per rate point.

Usage:
    python3 aggregate_results.py api_comparison_results.csv
    python3 aggregate_results.py api_comparison_results.csv --out averaged.csv
"""
import argparse
import csv
import sys
from collections import defaultdict

GROUP_COLUMNS = ["impl", "interval", "size"]
NUMERIC_COLUMNS = [
    "received", "dropped", "elapsed_s", "rate_msg_s",
    "min_ms", "avg_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Average repeated api_benchmark.py summary runs per rate point")
    parser.add_argument("csv_path", help="summary CSV produced by api_benchmark.py's --out")
    parser.add_argument("--out", type=str, default=None, help="path to write the averaged CSV to (default: stdout)")
    args = parser.parse_args()

    groups = defaultdict(list)
    with open(args.csv_path, newline="") as f:
        for row in csv.DictReader(f):
            groups[tuple(row[c] for c in GROUP_COLUMNS)].append(row)

    fieldnames = GROUP_COLUMNS + ["runs"] + NUMERIC_COLUMNS
    averaged_rows = []
    for key in sorted(groups, key=lambda k: (k[0], float(k[1]), k[2])):
        rows = groups[key]
        averaged = dict(zip(GROUP_COLUMNS, key))
        averaged["runs"] = len(rows)
        for col in NUMERIC_COLUMNS:
            values = [float(r[col]) for r in rows if r[col] != ""]
            averaged[col] = f"{sum(values) / len(values):.3f}" if values else ""
        averaged_rows.append(averaged)

    out_file = open(args.out, "w", newline="") if args.out else sys.stdout
    writer = csv.DictWriter(out_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(averaged_rows)
    if args.out:
        out_file.close()
        print(f"Wrote {len(averaged_rows)} averaged rows to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()