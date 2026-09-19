#!/usr/bin/env python3
"""Copy the installable plugin surface into packaging/runtime.

The source of truth stays at the repository root (agents/, skills/, manifests). This
script copies that surface into a generated directory so a local-directory marketplace
can snapshot it without records/, tests/, tools/, docs/, evals/, or mock/.

The copy is regular files only. Symlinks are refused so a generated tree cannot point
outside the declared surface (same rule as tools/lab/artifact_digest.py).
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
        "records",
        "tests",
        "tools",
        "docs",
        "evals",
        "mock",
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
    if resolved == ROOT:
        raise ValueError("refusing to write the runtime tree over the repository root")
    if resolved == SCRIPT_DIR:
        raise ValueError("refusing to write over packaging/")
    for name in RUNTIME_DIRECTORIES:
        source = (ROOT / name).resolve()
        if resolved == source or source in resolved.parents:
            raise ValueError(f"refusing to write over source tree {name}")
    for name in RUNTIME_FILES:
        source = (ROOT / name).resolve()
        if resolved == source:
            raise ValueError(f"refusing to write over source file {name}")


def copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"symlink is not allowed: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"symlink is not allowed: {source}")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part == "__pycache__" for part in relative.parts):
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed: {path}")
        if not path.is_file():
            continue
        copy_file(path, destination / relative)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(destination: Path) -> list[str]:
    if destination.resolve() == ROOT:
        raise ValueError("refusing to write the runtime tree over the repository root")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    copied: list[str] = []
    for name in RUNTIME_DIRECTORIES:
        source = ROOT / name
        if not source.is_dir():
            raise ValueError(f"required directory missing: {name}")
        copy_tree(source, destination / name)
        copied.append(name)
    for name in RUNTIME_FILES:
        source = ROOT / name
        if not source.is_file():
            raise ValueError(f"required file missing: {name}")
        copy_file(source, destination / name)
        copied.append(name)
        if digest(source) != digest(destination / name):
            raise ValueError(f"copy digest mismatch: {name}")
    return copied


def verify(destination: Path) -> None:
    names = {entry.name for entry in destination.iterdir()}
    forbidden = sorted(names & FORBIDDEN_TOP_LEVEL)
    if forbidden:
        raise ValueError("runtime tree contains lab/evidence paths: " + ", ".join(forbidden))
    required = set(RUNTIME_DIRECTORIES) | set(RUNTIME_FILES)
    missing = sorted(required - names)
    if missing:
        raise ValueError("runtime tree missing: " + ", ".join(missing))
    unexpected = sorted(names - required)
    if unexpected:
        raise ValueError("runtime tree has undeclared top-level names: " + ", ".join(unexpected))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        default=str(DEFAULT_DEST),
        help="output directory (destroyed and recreated); default packaging/runtime",
    )
    args = parser.parse_args(argv)
    destination = Path(args.destination).expanduser().resolve()
    try:
        assert_safe_destination(destination)
        copied = build(destination)
        verify(destination)
    except (OSError, ValueError) as exc:
        return fail(str(exc))
    print(f"WROTE {destination}")
    print("copied " + ", ".join(copied))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
