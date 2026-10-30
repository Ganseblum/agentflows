#!/usr/bin/env python3
"""Summarize sales CSV by region."""
import argparse
import csv
import sys
from collections import defaultdict


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def summarize(path):
    totals = defaultdict(float)
    for row in load_rows(path):
        totals[row["region"]] += float(row["amount"])
    return totals


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--top", type=int, metavar="N")
    args = parser.parse_args(argv)
    if args.top is not None and args.top < 1:
        parser.error("--top must be at least 1")
    try:
        totals = summarize(args.csv_path)
    except ValueError as exc:
        parser.error(f"invalid amount value: {exc}")
    if args.top is None:
        rows = sorted(totals.items())
    else:
        rows = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[: args.top]
    for region, total in rows:
        print(f"{region}\t{total:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
