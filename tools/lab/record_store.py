#!/usr/bin/env python3
"""Agentflow 记录的小型本地读侧索引。

本存储是一次性的：磁盘上的记录始终是权威。SQLite FTS5 仅用于词法索引与查询；
不使用向量、嵌入，也不对记录文件做任何写入。

自 2026-10 结构改造起，现行记录根为 `docs/issues/`、`docs/releases/`、`docs/features/`、`episodes/`、
`reviews/`（取代了原先单一的 `records/` 树）。`index` 会遍历每个默认根；
`--records` 选项以一个或多个显式根覆盖它们，并保留「先索引、后查询」的 CLI 语义。
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
    ROOT / name
    for name in ("docs/issues", "docs/releases", "docs/features", "episodes", "reviews")
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
    """为每个根之下的所有记录文件建立索引；单个 Path 视为一个根。"""
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
    parser = argparse.ArgumentParser(description="用 SQLite FTS5 为 Agentflow 记录建索引/查询")
    parser.add_argument(
        "--records",
        type=Path,
        nargs="+",
        default=list(DEFAULT_ROOTS),
        help="要建索引的记录根（可多个）；默认为五个现行记录根",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("index", help="为记录建索引；源文件始终是权威")
    query_parser = subparsers.add_parser("query", help="对索引做词法查询")
    query_parser.add_argument("expression")
    query_parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.command == "index":
        print(f"已将 {index(args.records, args.db)} 条记录索引到 {args.db}")
        return 0
    for path, snippet in query(args.db, args.expression, args.limit):
        print(f"{path}\t{snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
