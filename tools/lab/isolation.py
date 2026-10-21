#!/usr/bin/env python3
"""Check or create the filesystem boundaries required for a candidate evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTECTED_PATHS_FILE = ROOT / "protected-paths.txt"


def resolved(path_value: str) -> Path:
    return Path(path_value).expanduser().resolve()


def load_protected_paths(path: Path) -> list[str]:
    """Read the protected-prefix list: one repository-relative path per line."""
    entries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        entries.append(entry.strip("/").replace("\\", "/"))
    if not entries:
        raise ValueError(f"no protected paths declared in {path}")
    return entries


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def layout_errors(
    repository: Path, candidate: Path, holdout: Path
) -> list[str]:
    errors: list[str] = []
    if repository == candidate:
        errors.append("candidate worktree must differ from the repository")
    if repository == holdout:
        errors.append("private holdout must differ from the repository")
    if candidate == holdout:
        errors.append("private holdout must differ from the candidate worktree")
    if is_within(candidate, repository) or is_within(repository, candidate):
        errors.append("candidate worktree must not be nested in or contain the repository")
    if is_within(holdout, repository) or is_within(repository, holdout):
        errors.append("private holdout must not be nested in or contain the repository")
    if is_within(holdout, candidate) or is_within(candidate, holdout):
        errors.append("private holdout must not be nested in or contain the candidate worktree")
    return errors


def validate_layout(args: argparse.Namespace) -> int:
    repository = resolved(args.repository)
    candidate = resolved(args.candidate)
    holdout = resolved(args.holdout)
    errors = layout_errors(repository, candidate, holdout)
    if not repository.is_dir():
        errors.append(f"repository is not a directory: {repository}")
    if not candidate.exists():
        errors.append(f"candidate path does not exist: {candidate}")
    if not holdout.exists():
        errors.append(f"holdout path does not exist: {holdout}")
    if errors:
        print("FAIL isolation layout", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    layout = {"repository": str(repository), "candidate": str(candidate), "holdout": str(holdout)}
    print(json.dumps(layout, indent=2))
    return 0


def create_worktree(args: argparse.Namespace) -> int:
    repository = resolved(args.repository)
    destination = resolved(args.destination)
    if not repository.is_dir():
        print(f"repository is not a directory: {repository}", file=sys.stderr)
        return 1
    if destination.exists():
        print(f"destination already exists: {destination}", file=sys.stderr)
        return 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = ["git", "-C", str(repository), "worktree", "add", "--detach", str(destination), args.revision]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        print(completed.stderr.rstrip() or "git worktree add failed", file=sys.stderr)
        return completed.returncode or 1
    print(f"CREATED {destination}")
    return 0


def changed_paths(candidate: Path, base: str) -> list[str]:
    if base.startswith("-"):
        raise RuntimeError(f"base revision must not start with '-': {base!r}")
    verify_base = ["git", "-C", str(candidate), "rev-parse", "--verify", f"{base}^{{commit}}"]
    verified = subprocess.run(verify_base, text=True, capture_output=True, check=False)
    if verified.returncode != 0:
        raise RuntimeError(f"base revision does not resolve to a commit: {base!r}")

    # Compare the complete candidate tree with the frozen parent. Disable rename detection so
    # both the old protected path and the new path are visible to the gate.
    commands = [
        ["git", "-C", str(candidate), "diff", "--no-renames", "--name-only", "-z", base],
        ["git", "-C", str(candidate), "ls-files", "--others", "--exclude-standard", "-z"],
        ["git", "-C", str(candidate), "ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
    ]
    paths: set[str] = set()
    for command in commands:
        completed = subprocess.run(command, capture_output=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.decode(errors="replace").rstrip() or "git diff failed")
        paths.update(item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
                    for item in completed.stdout.split(b"\0") if item)
    # Python bytecode caches are a side effect of *running the gate itself* (PYTHONDONTWRITEBYTECODE
    # is not always set by callers), not a candidate edit. tools/lab/gate/ is a protected prefix,
    # so without this filter an honest candidate that ran the checks is blocked by its own
    # __pycache__ (2026-10-20 evaluation G06). The tests/ prefix solved the same problem by
    # protecting files individually; a global cache filter is the honest equivalent.
    return sorted(path for path in paths if "__pycache__" not in Path(path).parts)


def check_diff(args: argparse.Namespace) -> int:
    candidate = resolved(args.candidate)
    checker_root_value = getattr(args, "checker_root", None)
    checker_root = resolved(checker_root_value) if checker_root_value else ROOT
    if checker_root == candidate or is_within(checker_root, candidate) or is_within(candidate, checker_root):
        print("FAIL candidate diff: checker root and candidate must be separate and non-nested", file=sys.stderr)
        return 1
    source = checker_root / "protected-paths.txt"
    try:
        forbidden = load_protected_paths(source)
        declared_by = str(source)
    except (OSError, ValueError) as exc:
        print(f"FAIL candidate diff: cannot load protected paths: {exc}", file=sys.stderr)
        return 1
    try:
        paths = changed_paths(candidate, args.base)
    except RuntimeError as exc:
        print(f"FAIL candidate diff: {exc}", file=sys.stderr)
        return 1
    blocked = [
        path
        for path in paths
        if any(path == prefix or path.startswith(prefix + "/") for prefix in forbidden)
    ]
    result = {
        "candidate": str(candidate),
        "changed_paths": paths,
        "protected_paths_declared_by": declared_by,
        "forbidden_paths": forbidden,
        "blocked": blocked,
    }
    print(json.dumps(result, indent=2))
    if blocked:
        print("candidate changed a forbidden path", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    layout_parser = subparsers.add_parser("validate-layout")
    layout_parser.add_argument("--repository", required=True)
    layout_parser.add_argument("--candidate", required=True)
    layout_parser.add_argument("--holdout", required=True)
    layout_parser.set_defaults(handler=validate_layout)

    create_parser = subparsers.add_parser("create-worktree")
    create_parser.add_argument("--repository", required=True)
    create_parser.add_argument("--destination", required=True)
    create_parser.add_argument("--revision", required=True)
    create_parser.set_defaults(handler=create_worktree)

    diff_parser = subparsers.add_parser("check-diff")
    diff_parser.add_argument("--candidate", required=True)
    diff_parser.add_argument("--checker-root", default=None, help="trusted checker checkout; must not overlap candidate")
    diff_parser.add_argument("--base", required=True, help="frozen parent revision to compare against")
    diff_parser.set_defaults(handler=check_diff)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
