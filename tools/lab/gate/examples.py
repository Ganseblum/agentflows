"""The examples/ fixture set and its declared negative examples."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .common import ROOT, ValidationError, load_json, load_record_markdown
from .plan import validate_plan_markdown
from .records import validate_bug_markdown
from .schema import SchemaValidator
from .testing import (
    parse_test_case_registry,
    validate_test_plan_markdown,
    validate_test_run_markdown,
)

IMPROVE_EXAMPLE_DIR = ROOT / "examples" / "improve"
IMPROVE_VALID_CANDIDATE = "candidate-valid.json"
IMPROVE_VALID_RELEASE = "release-record-valid.json"
IMPROVE_NEGATIVE_RELEASE = "release-record-none-better.json"
# G10: under measurement.status "none", evaluation_result "better" is structurally impossible
# (no instrumented baseline exists since the 2026-10-12 apparatus removal). The negative example
# must be rejected for that reason, not for an unrelated defect.
# The negative example exists to pin the "measurement:none ⇒ evaluation_result must not be
# `better`" guardrail. The SchemaValidator emits that `not`-rule as a `must not match the
# forbidden schema` error on `$.evaluation_result`; tying the pin to both the path and the
# message keeps it specific to this judgement (the only `not` keyword in the contract) rather
# than to a passing-fancy substring that the rule's wording could change without the gate
# catching it — G13 taught that a pin surviving the rule it names is the dangerous case.
IMPROVE_NEGATIVE_EXPECTS_PATH = "$.evaluation_result"
IMPROVE_NEGATIVE_EXPECTS_MSG = "must not match the forbidden schema"


def validate_invalid_plan_example(path: Path) -> list[ValidationError]:
    """Reject one negative plan example; `validate_plan_markdown` needs the relative path."""
    return validate_plan_markdown(path)


def example_test_plans() -> dict[str, dict[str, Any]]:
    """Test plan entries parsed from examples/testing for standalone run-example validation."""
    plans: dict[str, dict[str, Any]] = {}
    for plan_path in sorted((ROOT / "examples" / "testing").glob("plan-*.md")):
        frontmatter, body, load_errors = load_record_markdown(plan_path)
        if load_errors or frontmatter is None or not isinstance(frontmatter.get("test_plan_id"), str):
            continue
        cases, _ = parse_test_case_registry(body, plan_path)
        plans[frontmatter["test_plan_id"]] = {
            "path": plan_path,
            "frontmatter": frontmatter,
            "cases": [case["case_id"] for case in cases],
        }
    return plans


def validate_invalid_test_run_example(path: Path) -> list[ValidationError]:
    """Reject one negative test-run example; needs the example plan registry for resolution."""
    errors, _, _ = validate_test_run_markdown(path, path.relative_to(ROOT), {}, example_test_plans())
    return errors


# Declared contents of `examples/invalid`. The directory used to be classified by filename
# prefix (case-sensitive for bug records, insensitive for plans), so a misspelled negative
# example was silently skipped and never exercised its gate. Now every non-hidden entry in the
# directory must be declared here together with the validator that must reject it, and every
# declared entry must exist and be rejected. Only bug-record and plan negatives exist today;
# do not add other negative families here without extending the validators that cover them.
INVALID_EXAMPLES: dict[str, tuple[str, Any]] = {
    "bug-record-verified-without-review.md": ("bug-record", validate_bug_markdown),
    "bug-record-verified-heading-missing.md": ("bug-record", validate_bug_markdown),
    "bug-record-disposition-unknown.md": ("bug-record", validate_bug_markdown),
    "PLAN-INVALID-002.md": ("plan", validate_invalid_plan_example),
    "PLAN-INVALID-003.md": ("plan", validate_invalid_plan_example),
    "PLAN-INVALID-004.md": ("plan", validate_invalid_plan_example),
    "PLAN-INVALID-005.md": ("plan", validate_invalid_plan_example),
    "PLAN-INVALID-006.md": ("plan", validate_invalid_plan_example),
    "PLAN-INVALID-007.md": ("plan", validate_invalid_plan_example),
    "test-run-bad-status.md": ("test-run", validate_invalid_test_run_example),
}

# What each negative example exists to pin. Asserting only "this file is rejected" is not
# enough: a negative example that trips several rules stays rejected after the rule it names
# is fixed, so the pin silently disappears while the gate stays green (2026-10-26 audit G13 —
# test-run-bad-status.md survived its status word being repaired, because the filename, the
# plan adjacency and the case coverage still rejected it). The expected substring ties the
# rejection to the specific judgement the example was written for.
INVALID_EXAMPLE_EXPECTS: dict[str, str] = {
    "test-run-bad-status.md": "must be one of",
    "bug-record-verified-without-review.md": "reviewer",
    "bug-record-verified-heading-missing.md": "## 审查",
}


def validate_improve_examples() -> list[ValidationError]:
    """G10 — the improvement contracts (candidate / release-record) had zero compiled instances.

    Both schemas carry their allOf guardrails mechanically (the "none ⇒ not better" rule, the
    "promote under none needs human review + approved evidence" rule, the prohibited-slices
    check), but nothing in the repo ever exercised them. This check pins two positive instances
    (a candidate and its release record must validate) and one negative instance (a release
    record claiming "better" under measurement "none" must be rejected for that reason). The
    contracts stop being dead the moment they have consumers that the gate actually compiles.
    """
    errors: list[ValidationError] = []
    if not IMPROVE_EXAMPLE_DIR.is_dir():
        return [ValidationError("examples/improve", "improvement contract examples directory is missing")]
    candidate_schema = SchemaValidator(ROOT / "skills" / "improve" / "references" / "candidate.schema.json")
    release_schema = SchemaValidator(ROOT / "skills" / "improve" / "references" / "release-record.schema.json")

    for name in (IMPROVE_VALID_CANDIDATE, IMPROVE_VALID_RELEASE):
        path = IMPROVE_EXAMPLE_DIR / name
        if not path.is_file():
            errors.append(ValidationError(str(path), "declared positive improvement example is missing"))
            continue
        instance, load_errors = load_json(path)
        if load_errors or not isinstance(instance, dict):
            errors.append(ValidationError(str(path), f"invalid JSON: {load_errors[0] if load_errors else 'not an object'}"))
            continue
        schema = candidate_schema if name == IMPROVE_VALID_CANDIDATE else release_schema
        if schema.validate(instance):
            errors.append(ValidationError(str(path), "expected valid improvement example, but it failed validation"))

    negative_path = IMPROVE_EXAMPLE_DIR / IMPROVE_NEGATIVE_RELEASE
    if not negative_path.is_file():
        errors.append(ValidationError(str(negative_path), "declared negative improvement example is missing"))
    else:
        instance, load_errors = load_json(negative_path)
        if load_errors or not isinstance(instance, dict):
            errors.append(ValidationError(str(negative_path), f"invalid JSON: {load_errors[0] if load_errors else 'not an object'}"))
        else:
            doc_errors = release_schema.validate(instance)
            if not doc_errors:
                errors.append(
                    ValidationError(str(negative_path), "expected negative improvement example to be rejected")
                )
            elif not any(
                e.path == IMPROVE_NEGATIVE_EXPECTS_PATH and IMPROVE_NEGATIVE_EXPECTS_MSG in e.message
                for e in doc_errors
            ):
                errors.append(
                    ValidationError(
                        str(negative_path),
                        f"negative example was rejected, but not by the rule it pins: expected an "
                        f"error at {IMPROVE_NEGATIVE_EXPECTS_PATH!r} reading {IMPROVE_NEGATIVE_EXPECTS_MSG!r} "
                        "(the measurement:none ⇒ not-better guardrail). The rejection must come from that "
                        "guardrail, not an unrelated defect.",
                    )
                )
    return errors


def validate_examples() -> list[ValidationError]:
    errors: list[ValidationError] = []
    bug_paths = sorted((ROOT / "examples" / "issues").glob("*.md"))
    plan_paths = sorted((ROOT / "examples" / "plans").glob("*.md"))
    test_paths = sorted((ROOT / "examples" / "testing").glob("*.md"))
    test_plan_paths = [path for path in test_paths if re.fullmatch(r"plan-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name)]
    test_run_paths = [path for path in test_paths if re.fullmatch(r"run-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name)]
    valid_paths = plan_paths
    invalid_dir = ROOT / "examples" / "invalid"
    present = sorted(invalid_dir.iterdir()) if invalid_dir.is_dir() else []
    declared: set[str] = set()
    for path in present:
        if path.name.startswith("."):
            # Hidden entries (.DS_Store and friends) are host/OS artifacts, not examples.
            continue
        if path.name not in INVALID_EXAMPLES:
            errors.append(
                ValidationError(
                    str(path),
                    "undeclared negative example; declare it in INVALID_EXAMPLES together with "
                    "the validator that must reject it",
                )
            )
        elif path.is_file():
            declared.add(path.name)
    if not bug_paths or not valid_paths or not declared:
        errors.append(ValidationError("examples", "valid and invalid example sets are all required"))
    if not test_plan_paths or not test_run_paths:
        errors.append(
            ValidationError(
                "examples",
                "a valid test plan example and a valid test run example are both required",
            )
        )
    plan_negatives = {
        name for name, (kind, _) in INVALID_EXAMPLES.items() if kind == "plan" and name in declared
    }
    if not plan_paths or not plan_negatives:
        # A naming mismatch here once silently excluded the invalid plan example from this check.
        errors.append(
            ValidationError("examples", "a valid plan example and an invalid plan example are both required")
        )
    for name, (kind, check) in sorted(INVALID_EXAMPLES.items()):
        path = invalid_dir / name
        if not path.is_file():
            errors.append(
                ValidationError(str(path), f"declared {kind} negative example is missing from examples/invalid")
            )
            continue
        document_errors = check(path)
        if not document_errors:
            errors.append(ValidationError(str(path), "expected invalid example to be rejected"))
            continue
        expect = INVALID_EXAMPLE_EXPECTS.get(name)
        if expect is not None and not any(expect in e.message for e in document_errors):
            errors.append(
                ValidationError(
                    str(path),
                    f"negative example was rejected, but not by the rule it pins: expected an "
                    f"error containing {expect!r}. The rejection must come from the judgement "
                    "this example exists for, not from an unrelated defect.",
                )
            )
    for path in bug_paths:
        document_errors = validate_bug_markdown(path)
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    for path in plan_paths:
        document_errors = validate_plan_markdown(path)
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    for path in test_plan_paths:
        document_errors, _ = validate_test_plan_markdown(path, path.relative_to(ROOT), {})
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    for path in test_run_paths:
        document_errors, _, _ = validate_test_run_markdown(
            path, path.relative_to(ROOT), {}, example_test_plans()
        )
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    errors.extend(validate_doc_chain_examples())
    errors.extend(validate_improve_examples())
    return errors


# Example document chains the compile gate lints end-to-end: (directory, expected exit code,
# findings the linter must report). The dense chain is the positive fixture — the shape every
# delivered chain must reach; the thin one is the 2026-09-20 failure shape (every stage exists,
# nothing has density), which must fail with the findings the density floor names.
DOC_CHAIN_EXAMPLES = (
    ("good/feature-demo", 0, ()),
    ("bad/feature-demo-thin", 1, ("C4 design/be", "C7 design/fe", "C9 plan 落点")),
)


def validate_doc_chain_examples() -> list[ValidationError]:
    """Run the doc-chain structure checks (C1–C11) against the shipped example chains.

    `validate_doc_chain` pins the linter's self-test and `validate_doc_chain_live` points its
    text checks at the live document surfaces — but until 2026-10-13 nothing ever ran C1–C11,
    the structure and density checks the linter was built for, against any real chain. The tree's
    only feature directory has no proposal/spec/design track, so it could never pass them and was
    never asked to; the checks therefore had no live exercise at all and could rot while every
    gate stayed green. These fixtures carry that load on every compile run.
    """
    errors: list[ValidationError] = []
    linter = ROOT / "tools" / "lab" / "doc_chain.py"
    if not linter.is_file():
        return [ValidationError("examples", "tools/lab/doc_chain.py is missing")]
    for name, expected_rc, want in DOC_CHAIN_EXAMPLES:
        target = ROOT / "examples" / "doc-chain" / name
        relative = target.relative_to(ROOT)
        if not target.is_dir():
            errors.append(ValidationError(str(relative), "declared doc-chain example is missing"))
            continue
        completed = subprocess.run(
            [sys.executable, str(linter), str(relative)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        output = f"{completed.stdout}\n{completed.stderr}"
        if completed.returncode != expected_rc:
            errors.append(
                ValidationError(
                    str(relative),
                    f"doc-chain linter exited {completed.returncode}, expected {expected_rc}",
                )
            )
            continue
        for finding in want:
            if finding not in output:
                errors.append(
                    ValidationError(
                        str(relative), f"expected doc-chain finding {finding!r} was not reported"
                    )
                )
    return errors
