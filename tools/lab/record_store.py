#!/usr/bin/env python3
"""Small local read-side index for Agentflow records.

The store is disposable: records remain authoritative on disk.  SQLite FTS5 is used only
for lexical indexing and querying; no vectors, embeddings, or writes to record files occur.

Since the 2026-10 structural overhaul the live record roots are `issues/`, `episodes/`,
`plans/`, `improvements/`, `releases/`, and `reviews/` (the former single `records/` tree).
`index` walks every default root; the `--records` option overrides them with one or more
explicit roots and keeps the "index then query" CLI semantics.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / ".agentflow-records.sqlite3"
DEFAULT_ROOTS = tuple(
    ROOT / name for name in ("issues", "episodes", "plans", "improvements", "releases", "reviews")
)


def _text(path: Path) -> tuple[str, str, str]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        try:
            value = json.loads(raw)
            title = str(value.get("objective", value.get("episode_id", path.stem))) if isinstance(value, dict) else path.stem
            body = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except json.JSONDecodeError:
            title, body = path.stem, raw
    else:
        title = next((line[2:].strip() for line in raw.splitlines() if line.startswith("# ")), path.stem)
        body = raw
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:
        relative = path.as_posix()
    return title, body, relative


def connect(db: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db)
    connection.execute("CREATE TABLE IF NOT EXISTS records (path TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL)")
    connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(path UNINDEXED, title, body)")
    return connection


def index(roots: Path | Iterable[Path], db: Path) -> int:
    """Index every record file under each root; a single Path is accepted as one root."""
    if isinstance(roots, Path):
        roots = (roots,)
    connection = connect(db)
    count = 0
    for root in sorted(Path(root) for root in roots):
        root = root.resolve()
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".json"} or path.name == "README.md":
                continue
            title, body, relative = _text(path)
            connection.execute("INSERT OR REPLACE INTO records(path, title, body) VALUES (?, ?, ?)", (relative, title, body))
            connection.execute("DELETE FROM records_fts WHERE path = ?", (relative,))
            connection.execute("INSERT INTO records_fts(path, title, body) VALUES (?, ?, ?)", (relative, title, body))
            count += 1
    connection.commit()
    connection.close()
    return count


def query(db: Path, expression: str, limit: int = 20) -> list[tuple[str, str]]:
    connection = connect(db)
    rows = connection.execute(
        "SELECT path, snippet(records_fts, 2, '[', ']', ' … ', 18) "
        "FROM records_fts WHERE records_fts MATCH ? ORDER BY rank LIMIT ?",
        (expression, limit),
    ).fetchall()
    connection.close()
    return [(str(path), str(snippet)) for path, snippet in rows]


def main() -> int:
    parser = argparse.ArgumentParser(description="Index/query Agentflow records with SQLite FTS5")
    parser.add_argument(
        "--records",
        type=Path,
        nargs="+",
        default=list(DEFAULT_ROOTS),
        help="record root(s) to index; defaults to the six live record roots",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("index", help="index records; source files remain authoritative")
    query_parser = subparsers.add_parser("query", help="lexically query the index")
    query_parser.add_argument("expression")
    query_parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.command == "index":
        print(f"indexed {index(args.records, args.db)} records into {args.db}")
        return 0
    for path, snippet in query(args.db, args.expression, args.limit):
        print(f"{path}\t{snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
