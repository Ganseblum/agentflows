#!/usr/bin/env python3
"""Record one row of improvement-loop health signals into docs/trend.jsonl.

The 2026-10-12 裁撤批 (ISS-2026-052) removed the automatic measurement apparatus — evals/, the
runner, the adapter, the policy engine. The loop kept its four governance roles
(feedback-analyst / candidate-engineer / evaluator / release-governor) but lost the signal that
fed them: `validate.py recurrence` reports 0 escalated classes, so they had nothing to act on.
This is NOT that apparatus rebuilt — it adds no cases and no runner. It records the trend of
signals the checks *already produce*, so the loop's inputs stop being invisible between sessions:

  escalated_classes     recurrence-ledger classes at the strongest tier (validate.py recurrence)
  live_doc_findings     doc-chain findings across the live document surfaces (the compile gate)
  open_review_findings  findings listed under 发现摘要 in every review record (reviews/)
  unittest_count        size of the regression suite (validate.py tests)

Every value is derived from an existing artefact by a parser, never estimated; a signal whose
source is absent is recorded as null rather than dropped. This is a trend of counts, not a
quality verdict — the `measurement: none` honesty rule (docs/design-decisions.md §3) applies
here too, so a row is evidence of the loop's *inputs*, never of the method's effectiveness.

Usage:
    python3 tools/lab/trend.py            # print the row
    python3 tools/lab/trend.py --append   # print the row and append it to docs/trend.jsonl
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools" / "lab") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "lab"))

import validate  # noqa: E402  (same directory; the checks live there)

TREND_LOG = ROOT / "docs" / "trend.jsonl"


def escalated_classes() -> int:
    """Count recurrence-ledger classes at the escalated tier (the loop's strongest signal)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        validate.recurrence_report()
    count = 0
    for line in buffer.getvalue().splitlines():
        columns = line.split("\t")
        if len(columns) >= 6 and columns[5].strip() == "escalated":
            count += 1
    return count


def live_doc_findings() -> int:
    """Findings the compile gate reports across the live document surfaces."""
    return len(validate.validate_doc_chain_live())


def open_review_findings() -> int | None:
    """Findings listed under 发现摘要 across every review record; None when none exist."""
    reviews = ROOT / "reviews"
    if not reviews.is_dir():
        return None
    seen = False
    total = 0
    for path in sorted(reviews.rglob("review-*.md")):
        text = path.read_text(encoding="utf-8")
        if "## 发现摘要" not in text:
            continue
        seen = True
        section = text.split("## 发现摘要", 1)[1].split("\n## ", 1)[0]
        total += sum(1 for line in section.splitlines() if line.strip().startswith("- "))
    return total if seen else None


def unittest_count() -> int | None:
    """The regression-suite size, parsed from the unittest summary line."""
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    match = re.search(r"Ran (\d+) tests?", f"{completed.stderr}\n{completed.stdout}")
    return int(match.group(1)) if match else None


def collect() -> dict[str, object]:
    revision = (
        subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            capture_output=True,
        ).stdout.strip()
        or None
    )
    return {
        "recorded_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "revision": revision,
        "escalated_classes": escalated_classes(),
        "live_doc_findings": live_doc_findings(),
        "open_review_findings": open_review_findings(),
        "unittest_count": unittest_count(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--append",
        action="store_true",
        help="append the row to docs/trend.jsonl (default: print only)",
    )
    args = parser.parse_args(argv)
    row = collect()
    line = json.dumps(row, ensure_ascii=False)
    if args.append:
        with TREND_LOG.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        print(f"appended to {TREND_LOG.relative_to(ROOT)}")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
