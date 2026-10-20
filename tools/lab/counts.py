#!/usr/bin/env python3
"""文档计数核对：检查模式（默认）或 --write 替换。

标记形式（成对，标记内只能是数字，标记外文字不动）：

    <!-- count:tests -->78<!-- /count -->

计数项与计算函数只在下方 COUNTERS 中显式映射；新增计数项须改此映射。

退出码：
    0  全部标记与计算值一致（或 --write 已完成）
    1  检查模式发现差异
    2  用法错误、未知标记名、标记不成对或内容非数字、文档不存在
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 允许携带计数标记的活文档。历史记录（CHANGELOG、episodes、docs/issues、reviews、
# examples、docs/features 下的设计稿）一律不列入，不被比对。
DOC_FILES = (
    "README.md",
    "index.md",
    "AGENTS.md",
    "docs/system-guide.md",
    "docs/design-decisions.md",
    "docs/product/README.md",
)

OPEN_TAG = "<!-- count:"
CLOSE_TAG = "<!-- /count -->"
MARKER = re.compile(r"<!-- count:(?P<name>[A-Za-z_]+) -->(?P<value>.*?)<!-- /count -->")
DIGITS = re.compile(r"[0-9]+")


def _is_testcase_class(node: ast.ClassDef, known: set[str]) -> bool:
    for base in node.bases:
        name = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", None)
        if name == "TestCase" or name in known:
            return True
    return False


def count_tests() -> int:
    """tests/test_*.py 中 TestCase 子类（含同模块内的间接子类）的 test_* 方法数。"""
    total = 0
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        known: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and _is_testcase_class(node, known):
                known.add(node.name)
                total += sum(
                    1
                    for f in node.body
                    if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name.startswith("test_")
                )
    return total


def count_schemas() -> int:
    """schemas/*.json 文件数。"""
    return len(list((ROOT / "schemas").glob("*.json")))


def count_agents() -> int:
    """agents/*.md 文件数（角色文件）。"""
    return len(list((ROOT / "agents").glob("*.md")))


def count_batches() -> int:
    """docs/features/ 下 feature-* 目录数（批次）。"""
    return sum(1 for p in (ROOT / "docs" / "features").glob("feature-*") if p.is_dir())


# 标记名 -> 计算函数。这是唯一的映射入口。
COUNTERS: dict[str, Callable[[], int]] = {
    "tests": count_tests,
    "schemas": count_schemas,
    "agents": count_agents,
    "batches": count_batches,
}


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="核对或替换文档中的计数标记")
    parser.add_argument("--write", action="store_true", help="仅替换标记之间的内容为计算值")
    args = parser.parse_args(argv)

    expected = {name: fn() for name, fn in COUNTERS.items()}
    print("计算值：" + "  ".join(f"{k}={v}" for k, v in expected.items()))

    diffs: list[str] = []
    edits: dict[Path, str] = {}
    marker_total = 0

    for rel in DOC_FILES:
        path = ROOT / rel
        if not path.is_file():
            return _fail(f"文档不存在：{rel}")
        text = path.read_bytes().decode("utf-8")
        matches = list(MARKER.finditer(text))
        opens = text.count(OPEN_TAG)
        closes = text.count(CLOSE_TAG)
        if opens != len(matches) or closes != len(matches):
            return _fail(
                f"{rel}：标记不成对或格式错误（开标记 {opens}，闭标记 {closes}，成对 {len(matches)}）"
            )
        for m in matches:
            name = m.group("name")
            if name not in COUNTERS:
                return _fail(f"{rel}：未知标记名 count:{name}")
            if not DIGITS.fullmatch(m.group("value")):
                return _fail(f"{rel}：count:{name} 的标记内容必须为纯数字，实为 {m.group('value')!r}")
            marker_total += 1
            line_no = text.count("\n", 0, m.start()) + 1
            found = m.group("value")
            want = str(expected[name])
            if found != want:
                diffs.append(f"DIFF {rel}:{line_no} count:{name} 文档={found} 计算={want}")

        if args.write:
            new_text = MARKER.sub(
                lambda m: f"<!-- count:{m.group('name')} -->{expected[m.group('name')]}<!-- /count -->",
                text,
            )
            if new_text != text:
                edits[path] = new_text

    if args.write:
        for path, new_text in edits.items():
            path.write_bytes(new_text.encode("utf-8"))
            print(f"已更新：{path.relative_to(ROOT)}")
        print(f"标记共 {marker_total} 处，已写入 {len(edits)} 个文件。")
        return 0

    for line in diffs:
        print(line)
    if diffs:
        print(f"差异 {len(diffs)} 条（标记共 {marker_total} 处）。")
        return 1
    print(f"OK：标记共 {marker_total} 处，全部与计算值一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
