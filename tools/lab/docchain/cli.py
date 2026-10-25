"""Command-line entry point for the doc-chain linter.

Usage:
    python3 tools/lab/doc_chain.py [--root <repo-dir>] <feature-dir>
    python3 tools/lab/doc_chain.py --file <single-markdown-path>
    python3 tools/lab/doc_chain.py --repo <repo-dir>
    python3 tools/lab/doc_chain.py --self-test

Exit code 0 = all checks pass; 1 = findings; 2 = usage error. --file runs only the text-form
checks (C12/C13/C14) against one standalone markdown file — a session deliverable handed to
the user (analysis report, status report) has no feature-directory shape, so every structure
check (C1–C11) is skipped by design; --file and a positional feature dir are mutually exclusive.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .checks import lint, read, repo_policy_findings, text_form_findings
from .constants import REPO_ROOT
from .selftest import self_test


def lint_file(path: Path) -> int:
    """--file mode: text-form checks only (C12/C13/C14) against one standalone markdown file."""
    if not path.is_file():
        print("FAIL doc-chain --file (1 findings)")
        print(f"  - 文件不存在: {path}")
        return 1
    errors = text_form_findings(str(path), read(path), [path.parent])
    if errors:
        print(f"FAIL doc-chain --file {path} ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS doc-chain --file {path}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 1 and argv[0] == "--self-test":
        return self_test()
    root = REPO_ROOT
    if argv[:1] == ["--root"]:
        if len(argv) < 2 or argv[2:3] == ["--file"]:
            print(__doc__)
            return 2
        root, argv = Path(argv[1]), argv[2:]
    if argv and argv[0] == "--file":
        if len(argv) != 2:
            print(__doc__)
            return 2
        return lint_file(Path(argv[1]))
    if argv and argv[0] == "--repo":
        if len(argv) != 2:
            print(__doc__)
            return 2
        root = Path(argv[1])
        if not root.is_dir():
            print(f"FAIL decision-gate: 目录不存在: {root}")
            return 1
        errors = repo_policy_findings(root)
        if errors:
            print(f"FAIL decision-gate ({len(errors)} findings)")
            for e in errors:
                print(f"  - {e}")
            return 1
        print("PASS decision-gate")
        return 0
    if len(argv) != 1:
        print(__doc__)
        return 2
    errors = lint(Path(argv[0]), root)
    if errors:
        print(f"FAIL doc-chain ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS doc-chain {argv[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
