"""Command-line entry point for the doc-chain linter.

Usage:
    python3 tools/lab/doc_chain.py [--root <repo-dir>] <feature-dir>
    python3 tools/lab/doc_chain.py --file <single-markdown-path>
    python3 tools/lab/doc_chain.py --repo <repo-dir>
    python3 tools/lab/doc_chain.py --self-test
    python3 tools/lab/doc_chain.py --version

Exit code 0 = all checks pass; 1 = findings; 2 = usage error. --file runs only the text-form
checks (C12/C13/C14) against one standalone markdown file — a session deliverable handed to
the user (analysis report, status report) has no feature-directory shape, so every structure
check (C1–C11) is skipped by design; --file and a positional feature dir are mutually exclusive.
--version prints the version declared by the manifests of the tree this checker was loaded from,
which is how an installed user confirms which snapshot an upgrade actually installed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .checks import (
    closure_claim_findings,
    lint,
    read,
    repo_policy_findings,
    text_form_findings,
)
from .constants import CLOSURE_MARKER, REPO_ROOT
from .selftest import self_test


def plugin_version() -> str:
    """The version of the tree this checker was loaded from, as its manifests declare it.

    Answers the only question an installed user actually has after an upgrade: which snapshot am
    I running? Reads `<repo>/plugin.json` (the plugin root is three levels up from this package),
    so the printed value is the shipped manifest rather than a hardcoded constant that could
    drift from it.
    """
    manifest = REPO_ROOT / "plugin.json"
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"unknown ({manifest} unreadable: {exc})"
    version = document.get("version")
    return str(version) if version else f"unknown ({manifest} has no version)"


def lint_file(path: Path) -> int:
    """--file mode: text-form checks (C12/C13/C14) and the opt-in closure claim (C25).

    C25 stays opt-in here too: the single file is judged `marked` by whether it itself carries
    the 「agentflow 链路收口」 marker, mirroring the feature-chain pass where the README's
    marker switches the check on. Hard-coding marked=True held every --file deliverable to the
    stricter marked criterion — including files that never promised a closure read.
    """
    if not path.is_file():
        print("FAIL doc-chain --file (1 findings)")
        print(f"  - 文件不存在: {path}")
        return 1
    text = read(path)
    errors = text_form_findings(str(path), text, [path.parent])
    errors.extend(closure_claim_findings(str(path), text, [path.parent], marked=CLOSURE_MARKER in text))
    if errors:
        print(f"FAIL doc-chain --file {path} ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS doc-chain --file {path}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] in (["--help"], ["-h"]):
        print(__doc__)
        return 0
    if argv[:1] in (["--version"], ["-V"]):
        print(f"agentflow {plugin_version()}")
        return 0
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
