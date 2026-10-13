"""Subprocess checks: the regression suite and the doc-chain linter."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from .common import (EXPECTED_TEST_FILES, MIN_DOC_CHAIN_SELF_TEST_CASES, MIN_UNIT_TEST_COUNT, ROOT, ValidationError)


def validate_unit_tests(root: Path = ROOT) -> list[ValidationError]:
    """Assert the declared test layout, then run the repository's regression tests.

    `tests/` is protected by file rather than by directory so that generated `__pycache__` entries
    do not block a candidate that ran the checks. This declared-content assertion is the other half
    of that trade, and it must cover directories, not only `.py` files: `unittest discover` imports
    every matching module under the start directory, including packages in subdirectories, and
    import-time code runs before any assertion. A demonstrated bypass adds `tests/<subdir>/` whose
    module replaces a pinned test method at import time, so the broken assertion passes and the
    gate returns PASS. The scan therefore rejects every entry that is not declared here. These
    tests pin `validate.py` and `isolation.py`, so a failure is a gate regression.

    The run must also stay a regression suite: the unittest "Ran N tests" summary is checked
    against MIN_UNIT_TEST_COUNT, so an empty or degenerate suite fails even when it exits 0.
    `root` defaults to the repository; the negative contract tests point it at a fixture tree.
    """
    errors: list[ValidationError] = []
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return [ValidationError("tests", "the test directory is missing")]
    allowed = set(EXPECTED_TEST_FILES) | {"__pycache__"}
    for entry in sorted(tests_dir.iterdir()):
        # No dotfile exemption: discover() walks the start directory's entries directly,
        # so a dot-named package is another import-time hijack vector, and a stray
        # .DS_Store here is noise that must be removed rather than silently allowed.
        if entry.name in allowed and (entry.name != "__pycache__" or entry.is_dir()):
            continue
        errors.append(
            ValidationError(
                f"tests/{entry.name}",
                "unexpected entry in the test directory; declare it here and in protected-paths.txt",
            )
        )
    # The generated cache is exempt only as bytecode. A source file or package inside it is an
    # import-time hijack vector just like one at the top level.
    cache = tests_dir / "__pycache__"
    if cache.is_dir():
        for stray in sorted(cache.rglob("*")):
            if stray.is_dir() or stray.suffix != ".pyc":
                errors.append(
                    ValidationError(
                        f"tests/__pycache__/{stray.relative_to(cache).as_posix()}",
                        "only compiled .pyc files may live in the generated test cache",
                    )
                )
    for name in EXPECTED_TEST_FILES:
        if not (tests_dir / name).is_file():
            errors.append(ValidationError(f"tests/{name}", "declared test file is missing"))
    if errors:
        return errors
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    ran = re.search(r"Ran (\d+) tests?", f"{completed.stderr}\n{completed.stdout}")
    count = int(ran.group(1)) if ran else None
    if count == 0:
        # unittest exits 5 for an empty run on Python 3.12+, but 0 on older interpreters;
        # the count check makes the empty suite fail on both.
        return [ValidationError("tests", "unit tests ran 0 tests; the regression suite is empty")]
    skipped = re.search(r"\bskipped=(\d+)", f"{completed.stderr}\n{completed.stdout}")
    if skipped and int(skipped.group(1)) > 0:
        return [ValidationError("tests", "skipped tests are not permitted in the regression gate")]
    if completed.returncode != 0:
        detail = (completed.stderr.strip() or completed.stdout.strip()).splitlines()
        summary = detail[-1] if detail else "no output"
        return [ValidationError("tests", f"unit tests failed (exit {completed.returncode}): {summary}")]
    if count is None:
        return [
            ValidationError(
                "tests",
                "unit test output has no 'Ran N tests' summary; cannot confirm how many tests ran",
            )
        ]
    if count < MIN_UNIT_TEST_COUNT:
        return [
            ValidationError(
                "tests",
                f"unit tests ran {count} tests, below the required floor of {MIN_UNIT_TEST_COUNT}; "
                "shrinking the regression suite is a gate change that requires explicit review",
            )
        ]
    return []


def validate_doc_chain(root: Path = ROOT) -> list[ValidationError]:
    """Run the doc-chain linter's discrimination self-test as part of the compile gate.

    The linter gates every document chain a worker delivers, but until now it only ever ran
    when someone remembered to invoke it by hand, so a regression in one of its checks
    surfaced late or not at all. This check runs `doc_chain.py --self-test` the way
    validate_unit_tests runs the suite — as a subprocess whose summary line is parsed, not
    trusted: exit code, the N/M pass count (N must equal M and M must clear
    MIN_DOC_CHAIN_SELF_TEST_CASES), and the absence of silent truncation are all asserted,
    so an empty or half-disabled self-test fails the gate like an empty unit-test run.
    Per-feature linting stays a separate explicit invocation: this pins the checker, it does
    not guess which directories in the tree happen to be document chains.
    """
    linter = root / "tools" / "lab" / "doc_chain.py"
    if not linter.is_file():
        return [ValidationError("doc_chain", "tools/lab/doc_chain.py is missing")]
    completed = subprocess.run(
        [sys.executable, str(linter), "--self-test"],
        cwd=str(root),
        text=True,
        capture_output=True,
        timeout=300,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    ran = re.search(r"(\d+)/(\d+) self-test cases pass", output)
    if completed.returncode != 0:
        detail = (completed.stderr.strip() or completed.stdout.strip()).splitlines()
        summary = detail[-1] if detail else "no output"
        return [
            ValidationError(
                "doc_chain",
                f"doc-chain self-test failed (exit {completed.returncode}): {summary}",
            )
        ]
    if ran is None:
        return [
            ValidationError(
                "doc_chain",
                "self-test output has no 'N/M self-test cases pass' summary; "
                "cannot confirm how many cases ran",
            )
        ]
    passed, total = int(ran.group(1)), int(ran.group(2))
    if passed != total or total == 0:
        return [ValidationError("doc_chain", f"doc-chain self-test passed {passed}/{total} cases")]
    if total < MIN_DOC_CHAIN_SELF_TEST_CASES:
        return [
            ValidationError(
                "doc_chain",
                f"doc-chain self-test ran {total} cases, below the required floor of "
                f"{MIN_DOC_CHAIN_SELF_TEST_CASES}; shrinking the linter's self-test is a gate "
                "change that requires explicit review",
            )
        ]
    return []


# Live-document surfaces the compile gate lints with the doc-chain linter. validate_doc_chain
# pins the *checker* (its self-test); this pins the checker on the *documents* it exists for.
#   - docs/product/ is the product chain's own text (proposal/spec/design): the text-form checks
#     (C12/C13/C14) on every *.md, since it is not a feature batch.
#   - docs/features/<batch>/ is a feature batch: the full pass (structure C1–C11 plus text
#     C12–C14) on each batch directory, and the text pass on each batch README and on the loose
#     *.md directly under docs/features/.
# C13 exemptions are per file (C13_EXEMPT_FILES in doc_chain.py), so no surface is skipped whole.
# Deleting either surface is a visible gate change: validate_doc_chain_live fails when a declared
# surface is missing.
DOC_CHAIN_LIVE_ROOTS = ("docs/product", "docs/features")


DOC_CHAIN_FEATURE_SURFACE = "docs/features"


def validate_doc_chain_live(root: Path = ROOT) -> list[ValidationError]:
    """Run the doc-chain linter over the live document surfaces; any finding fails the gate.

    Companion to validate_doc_chain: that check pins the linter's self-test, this one points the
    linter at the documents. docs/product/ gets the text-form checks (--file) on every *.md.
    docs/features/ gets the full feature-directory pass on each batch directory (structure
    C1–C11 plus text C12–C14, run with --root so C9 paths resolve against this repository), and
    the text pass on each batch README and on the loose *.md directly under docs/features/.
    A missing declared surface fails the gate. `root` defaults to the repository; findings keep
    the repo-relative path.
    """
    linter = root / "tools" / "lab" / "doc_chain.py"
    if not linter.is_file():
        return [ValidationError("doc_chain_live", "tools/lab/doc_chain.py is missing")]
    errors: list[ValidationError] = []
    for surface in DOC_CHAIN_LIVE_ROOTS:
        base = root / surface
        if not base.is_dir():
            errors.append(
                ValidationError(surface, "declared live-document surface is missing")
            )
            continue
        targets: list[tuple[Path, bool]] = []  # (path, full feature-directory pass?)
        if surface == DOC_CHAIN_FEATURE_SURFACE:
            for path in sorted(base.iterdir()):
                if path.is_dir():
                    targets.append((path, True))
                    if (path / "README.md").is_file():
                        targets.append((path / "README.md", False))
                elif path.suffix == ".md":
                    targets.append((path, False))
        else:
            targets = [(path, False) for path in sorted(base.rglob("*.md"))]
        for path, full in targets:
            relative = path.relative_to(root).as_posix()
            args = ["--root", str(root), relative] if full else ["--file", relative]
            completed = subprocess.run(
                [sys.executable, str(linter), *args],
                cwd=str(root),
                text=True,
                capture_output=True,
                timeout=120,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            if completed.returncode == 0:
                continue
            findings = [
                line.strip()[2:].strip()
                for line in completed.stdout.splitlines()
                if line.strip().startswith("- ")
            ]
            if not findings:
                findings = [f"doc-chain linter exited {completed.returncode} with no findings"]
            for finding in findings:
                errors.append(ValidationError(relative, finding))
    return errors
