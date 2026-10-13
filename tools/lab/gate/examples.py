"""The examples/ fixture set and its declared negative examples."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import (ROOT, ValidationError, load_record_markdown)
from .plan import (validate_plan_markdown)
from .records import (validate_bug_markdown)
from .testing import (parse_test_case_registry, validate_test_plan_markdown, validate_test_run_markdown)


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
    "PLAN-INVALID-002.md": ("plan", validate_invalid_plan_example),
    "test-run-bad-status.md": ("test-run", validate_invalid_test_run_example),
}


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
    return errors
