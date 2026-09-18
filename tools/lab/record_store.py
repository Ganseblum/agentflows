#!/usr/bin/env python3
"""Small local read-side index for Agentflow records.

The store is disposable: records remain authoritative on disk.  SQLite FTS5 is used only
for lexical indexing and querying; no vectors, embeddings, or writes to record files occur.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / ".agentflow-records.sqlite3"


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


def index(records_root: Path, db: Path) -> int:
    records_root = records_root.resolve()
    connection = connect(db)
    count = 0
    for path in sorted(records_root.rglob("*")):
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
    parser.add_argument("--records", type=Path, default=ROOT / "records")
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
