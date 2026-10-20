#!/usr/bin/env python3
"""把可安装的插件面复制到 packaging/runtime。

真源保持在仓库根（agents/、skills/、各 manifest）。本脚本把该面复制到一个生成目录，使
local-directory marketplace 可以在不包含记录根（issues/、episodes/、plans/、improvements/、
releases/、reviews/）、tests/、tools/、docs/、evals/、examples/ 的情况下对其进行快照。

复制只涉及常规文件。符号链接一律拒绝，确保生成树不能指向声明的面之外
（与 tools/lab/artifact_digest.py 同规则）。
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_DEST = SCRIPT_DIR / "runtime"

RUNTIME_DIRECTORIES = (
    "agents",
    "skills",
    "schemas",
    ".zcode-plugin",
    ".claude-plugin",
    ".codex-plugin",
)
RUNTIME_FILES = (
    "plugin.json",
    "marketplace.json",
    "protected-paths.txt",
)
FORBIDDEN_TOP_LEVEL = frozenset(
    {
        "issues",
        "episodes",
        "plans",
        "improvements",
        "releases",
        "reviews",
        "tests",
        "tools",
        "docs",
        "evals",
        "examples",
        ".git",
        "packaging",
    }
)


def fail(message: str) -> int:
    print(f"packaging: {message}", file=sys.stderr)
    return 1


def assert_safe_destination(destination: Path) -> None:
    resolved = destination.resolve()
    # 拒绝仓库根本身及其任意祖先目录（如 `..`、`../..`、`/`）。
    # 否则 build() 的 shutil.rmtree(destination) 会销毁仓库根与其父目录的全部内容。
    if ROOT.is_relative_to(resolved):
        raise ValueError("拒绝覆盖仓库根或其任意祖先目录")
    if resolved == SCRIPT_DIR:
        raise ValueError("拒绝覆盖 packaging/")
    for name in RUNTIME_DIRECTORIES:
        source = (ROOT / name).resolve()
        if resolved == source or source in resolved.parents:
            raise ValueError(f"拒绝覆盖源树 {name}")
    for name in RUNTIME_FILES:
        source = (ROOT / name).resolve()
        if resolved == source:
            raise ValueError(f"拒绝覆盖源文件 {name}")


def copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"不允许符号链接：{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"不允许符号链接：{source}")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part == "__pycache__" for part in relative.parts):
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink():
            raise ValueError(f"不允许符号链接：{path}")
        if not path.is_file():
            continue
        copy_file(path, destination / relative)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(destination: Path) -> list[str]:
    if destination.resolve() == ROOT:
        raise ValueError("拒绝以 runtime 树覆盖仓库根")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    copied: list[str] = []
    for name in RUNTIME_DIRECTORIES:
        source = ROOT / name
        if not source.is_dir():
            raise ValueError(f"缺少必需目录：{name}")
        copy_tree(source, destination / name)
        copied.append(name)
    for name in RUNTIME_FILES:
        source = ROOT / name
        if not source.is_file():
            raise ValueError(f"缺少必需文件：{name}")
        copy_file(source, destination / name)
        copied.append(name)
        if digest(source) != digest(destination / name):
            raise ValueError(f"复制摘要不匹配：{name}")
    return copied


def verify(destination: Path) -> None:
    names = {entry.name for entry in destination.iterdir()}
    forbidden = sorted(names & FORBIDDEN_TOP_LEVEL)
    if forbidden:
        raise ValueError("runtime 树包含 lab/evidence 路径： " + ", ".join(forbidden))
    required = set(RUNTIME_DIRECTORIES) | set(RUNTIME_FILES)
    missing = sorted(required - names)
    if missing:
        raise ValueError("runtime 树缺少： " + ", ".join(missing))
    unexpected = sorted(names - required)
    if unexpected:
        raise ValueError("runtime 树存在未声明的顶层名称： " + ", ".join(unexpected))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        default=str(DEFAULT_DEST),
        help="输出目录（会被销毁并重建）；默认 packaging/runtime",
    )
    args = parser.parse_args(argv)
    destination = Path(args.destination).expanduser().resolve()
    try:
        assert_safe_destination(destination)
        copied = build(destination)
        verify(destination)
    except (OSError, ValueError) as exc:
        return fail(str(exc))
    print(f"已写入 {destination}")
    print("已复制 " + ", ".join(copied))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
