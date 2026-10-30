"""Test-plan and test-run record contracts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import (
    TEST_PLAN_SCHEMA,
    TEST_RUN_SCHEMA,
    ValidationError,
    dated_id_errors,
    header_columns,
    heading_present,
    is_separator_row,
    load_record_markdown,
    parse_plan_task_row,
    validate_timestamp_order,
)
from .records import validate_body_references
from .schema import SchemaValidator


def _cell(cells: list[str], columns: dict[str, int] | None, name: str, fallback: int) -> str:
    """Read a cell by column name; fall back to a position only when the table has no header.

    T05: positional reads (`cells[1]`) silently moved meaning whenever a table gained a column.
    """
    position = columns.get(name) if columns else None
    if position is None:
        position = fallback
    return cells[position].strip() if len(cells) > position else ""

TEST_CASE_ID_PATTERN = re.compile(r"^TC-[A-Z0-9][A-Z0-9-]*$")


TEST_CASE_LEVELS = ("smoke", "e2e", "api", "boundary")


TEST_CASE_PRIORITIES = ("P0", "P1", "P2", "P3")


TEST_RESULT_STATUSES = ("pass", "fail", "blocked", "not-run")


TEST_PLAN_REQUIRED_HEADINGS = ("## 用例", "## 边界覆盖", "## 流程疑点")


TEST_RUN_REQUIRED_HEADINGS = ("## 结果", "## 证据", "## 结论")


# Cells that count as "no evidence" in a run's 结果 table; fail/blocked rows may not use them.
NO_EVIDENCE_CELLS = ("", "—", "-", "无")


def _int_version(value: Any) -> int | None:
    """A record version as an int; YAML hands back `2`, `"2"`, or a non-numeric string."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip().strip("\"'")
        if text.isdigit():
            return int(text)
    return None


def parse_test_case_registry(
    body: str, path: Path
) -> tuple[list[dict[str, str]], list[ValidationError]]:
    """Parse the 用例 registry table: rows whose first cell is a TC id carry ID/级别/优先级/标题."""
    cases: list[dict[str, str]] = []
    errors: list[ValidationError] = []
    lines = body.splitlines()
    seen: dict[str, int] = {}
    columns: dict[str, int] | None = None
    for index, line in enumerate(lines):
        lineno = index + 1
        row = parse_plan_task_row(line)
        if row is None:
            # A separator row belongs to the table; only a real break clears the column map.
            if not is_separator_row(line):
                columns = None
            continue
        if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
            columns = header_columns(line)
            continue  # header row
        cells = row["cells"]
        if len(cells) < 4 or not TEST_CASE_ID_PATTERN.match(cells[0]):
            continue
        case_id = cells[0]
        level = _cell(cells, columns, "级别", 1)
        priority = _cell(cells, columns, "优先级", 2)
        if case_id in seen:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: duplicate case id {case_id!r} (first seen at line {seen[case_id]})",
                )
            )
            continue
        seen[case_id] = lineno
        if level not in TEST_CASE_LEVELS:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: case {case_id} level {level!r} must be one of {TEST_CASE_LEVELS}",
                )
            )
        if priority not in TEST_CASE_PRIORITIES:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: case {case_id} priority {priority!r} must be one of {TEST_CASE_PRIORITIES}",
                )
            )
        source = _cell(cells, columns, "来源", -1)
        if columns is not None and "来源" in columns and (not source or source in ("无", "—", "-")):
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: case {case_id} 来源 must name its acceptance origin "
                    "(proposal G/AC id or ISS id), or write '无 — <reason>'",
                )
            )
        cases.append(
            {
                "case_id": case_id,
                "level": level,
                "priority": priority,
                "title": _cell(cells, columns, "标题", 3),
            }
        )
    return cases, errors


def validate_test_plan_markdown(
    path: Path, relative: Path, seen_plan_ids: dict[str, Path]
) -> tuple[list[ValidationError], dict[str, Any] | None]:
    """Validate one test plan and return (errors, plan entry) for run-record cross-checks.

    Home (2026-10 structural overhaul): features/<batch>/testing/<project>-<feature-slug>/
    plan-<YYYY-MM-DD>-<NNN>.md — feature-anchored directory, filename matches test_plan_id,
    revised in place (test_version bump). The artifacts walk patrols features/<batch>/testing/
    and runs this function on each plan there; the examples/ fixtures exercise it directly too.
    Body contract: the 用例 registry table (unique TC ids, level/priority enums, case_count
    equality, one detail heading per case) plus the 边界覆盖 and 流程疑点 sections.
    """
    frontmatter, body, errors = load_record_markdown(path)
    if errors or frontmatter is None:
        return errors, None
    try:
        validator = SchemaValidator(TEST_PLAN_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")], None
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors, None
    errors.extend(validate_timestamp_order(frontmatter, path))
    errors.extend(validate_body_references(body, path))
    test_plan_id = frontmatter.get("test_plan_id")
    match = None
    if isinstance(test_plan_id, str):
        if test_plan_id in seen_plan_ids:
            errors.append(
                ValidationError(
                    str(path),
                    f"duplicate test_plan_id {test_plan_id!r} already declared in {seen_plan_ids[test_plan_id]}",
                )
            )
        else:
            seen_plan_ids[test_plan_id] = path
        match = re.fullmatch(r"TP-(\d{4})-(\d{2})-(\d{2})-(\d{3})", test_plan_id)
        if match:
            errors.extend(dated_id_errors(path, frontmatter, match, "plan", "test_plan_id"))
        else:
            errors.append(
                ValidationError(str(path), "plan record filename must match its test_plan_id date and seq")
            )
    # Layout: test plans live in the feature batch directory
    # (features/<batch>/testing/<project>-<feature-slug>/plan-<date>-<seq>.md); the directory shape
    # is checked by the artifacts walk, while this function validates the frontmatter/body contract.
    for heading in TEST_PLAN_REQUIRED_HEADINGS:
        if not heading_present(body, heading):
            errors.append(ValidationError(str(path), f"body section {heading!r} is required"))
    cases, registry_errors = parse_test_case_registry(body, path)
    errors.extend(registry_errors)
    declared_count = frontmatter.get("case_count")
    if isinstance(declared_count, str) and declared_count.isdigit() and int(declared_count) != len(cases):
        errors.append(
            ValidationError(
                str(path),
                f"case_count {declared_count} does not match the {len(cases)} cases in the 用例 registry",
            )
        )
    detail_headings: set[str] = set()
    in_case_section = False
    for line in body.splitlines():
        if line.startswith("## "):
            in_case_section = line.strip() == "## 用例"
            continue
        if in_case_section and line.startswith("### "):
            tokens = line.lstrip("#").split()
            if tokens:
                detail_headings.add(tokens[0])
    for case in cases:
        if case["case_id"] not in detail_headings:
            errors.append(
                ValidationError(
                    str(path),
                    f"case {case['case_id']} has no detail heading (### <case id> ...) under ## 用例",
                )
            )
    if errors:
        return errors, None
    entry = {
        "path": path,
        "frontmatter": frontmatter,
        "cases": [case["case_id"] for case in cases],
    }
    return errors, entry


def validate_test_run_markdown(
    path: Path,
    relative: Path,
    seen_run_ids: dict[str, Path],
    test_plans: dict[str, dict[str, Any]],
) -> tuple[list[ValidationError], list[str], list[str]]:
    """Validate one test run record; return (errors, findings, flow_findings) so the caller can
    cross-check the bug-id pools after the whole tree has been walked.

    Body contract: the 结果 table (unique case ids from the referenced plan's registry, fixed
    result enum, evidence required on fail/blocked rows), summary counts equal to the table,
    decision pass requires zero fail/blocked, and — when the run pins the plan's current
    test_version — every case in the registry is accounted for.
    """
    frontmatter, body, errors = load_record_markdown(path)
    if errors or frontmatter is None:
        return errors, [], []
    try:
        validator = SchemaValidator(TEST_RUN_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")], [], []
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors, [], []
    errors.extend(validate_timestamp_order(frontmatter, path))
    errors.extend(validate_body_references(body, path))
    test_run_id = frontmatter.get("test_run_id")
    if isinstance(test_run_id, str):
        if test_run_id in seen_run_ids:
            errors.append(
                ValidationError(
                    str(path),
                    f"duplicate test_run_id {test_run_id!r} already declared in {seen_run_ids[test_run_id]}",
                )
            )
        else:
            seen_run_ids[test_run_id] = path
        match = re.fullmatch(r"TR-(\d{4})-(\d{2})-(\d{2})-(\d{3})", test_run_id)
        if match:
            errors.extend(dated_id_errors(path, frontmatter, match, "run", "test_run_id"))
        else:
            errors.append(
                ValidationError(str(path), "run record filename must match its test_run_id date and seq")
            )
    # Layout: test runs live in the feature batch directory
    # (features/<batch>/testing/<project>-<feature-slug>/run-<date>-<seq>.md); the directory shape
    # is checked by the artifacts walk, while this function validates the frontmatter/body contract.
    for heading in TEST_RUN_REQUIRED_HEADINGS:
        if not heading_present(body, heading):
            errors.append(ValidationError(str(path), f"body section {heading!r} is required"))

    plan_id = frontmatter.get("test_plan_id")
    plan = test_plans.get(plan_id) if isinstance(plan_id, str) else None
    if isinstance(plan_id, str) and plan is None:
        errors.append(
            ValidationError(str(path), f"test_plan_id {plan_id!r} does not resolve to a test plan record")
        )
    elif plan is not None:
        if plan["path"].parent != path.parent:
            errors.append(
                ValidationError(
                    str(path),
                    f"referenced plan {plan_id!r} lives in {plan['path'].parent}, not next to this run",
                )
            )
        if frontmatter.get("project") != plan["frontmatter"].get("project"):
            errors.append(
                ValidationError(str(path), "run project must match the referenced plan's project")
            )

    results: dict[str, tuple[int, str]] = {}
    counts = {"pass": 0, "fail": 0, "blocked": 0, "not-run": 0}
    in_results = False
    columns: dict[str, int] | None = None
    lines = body.splitlines()
    for index, line in enumerate(lines):
        lineno = index + 1
        if line.startswith("## "):
            in_results = line.strip() == "## 结果"
            columns = None
            continue
        if not in_results:
            continue
        row = parse_plan_task_row(line)
        if row is None:
            if not is_separator_row(line):
                columns = None
            continue
        if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
            columns = header_columns(line)
            continue  # header row
        cells = row["cells"]
        if len(cells) < 4 or not TEST_CASE_ID_PATTERN.match(cells[0]):
            continue
        case_id = cells[0]
        status_cell = _cell(cells, columns, "状态", 1)
        evidence = _cell(cells, columns, "证据", 2)
        if case_id in results:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: duplicate result row for case {case_id!r} "
                    f"(first seen at line {results[case_id][0]})",
                )
            )
            continue
        if status_cell not in TEST_RESULT_STATUSES:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: case {case_id} result {status_cell!r} must be one of {TEST_RESULT_STATUSES}",
                )
            )
            continue
        results[case_id] = (lineno, status_cell)
        counts[status_cell] += 1
        if status_cell in ("fail", "blocked") and evidence in NO_EVIDENCE_CELLS:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: {status_cell} row for {case_id} must carry evidence "
                    "(a path next to this record, or the recorded observation)",
                )
            )
        actual = _cell(cells, columns, "实际结果", -1)
        if (
            columns is not None
            and "实际结果" in columns
            and status_cell in ("pass", "fail", "blocked")
            and (not actual or actual in NO_EVIDENCE_CELLS)
        ):
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: case {case_id} 实际结果 must record the observed behaviour",
                )
            )
    for key, observed in (
        ("pass", counts["pass"]),
        ("fail", counts["fail"]),
        ("blocked", counts["blocked"]),
        ("not_run", counts["not-run"]),
    ):
        declared = frontmatter.get(f"summary_{key}")
        if isinstance(declared, str) and declared.isdigit() and int(declared) != observed:
            errors.append(
                ValidationError(
                    str(path),
                    f"summary_{key} {declared} does not match the 结果 table ({observed})",
                )
            )
    if frontmatter.get("decision") == "pass" and (counts["fail"] or counts["blocked"]):
        errors.append(
            ValidationError(str(path), "decision 'pass' requires zero fail and zero blocked rows")
        )
    # T06: a run whose 结果 table is empty used to be exempt — the case-accounting check only ran
    # when the run pinned the plan's *current* version, so a zero-case run declaring `pass` was
    # accepted. Both conditions are now unconditional: a run must observe at least one case.
    if not results or sum(counts.values()) <= 0:
        errors.append(
            ValidationError(
                str(path),
                "the 结果 table must carry at least one case row and a non-zero summary total",
            )
        )
    if plan is not None:
        for case_id in results:
            if case_id not in plan["cases"]:
                errors.append(
                    ValidationError(
                        str(path),
                        f"result row {case_id!r} is not in plan {plan_id!r}'s case registry",
                    )
                )
        version = frontmatter.get("test_plan_version")
        current = (plan["frontmatter"] or {}).get("test_version")
        pinned = _int_version(version)
        current_version = _int_version(current)
        if pinned is None:
            errors.append(
                ValidationError(
                    str(path),
                    f"test_plan_version {version!r} must be an integer so it can be matched "
                    f"against plan {plan_id!r}'s test_version",
                )
            )
        elif current_version is not None and pinned > current_version:
            errors.append(
                ValidationError(
                    str(path),
                    f"test_plan_version {pinned} pins a version that plan {plan_id!r} never had "
                    f"(current test_version {current_version})",
                )
            )
        elif current_version is not None and pinned == current_version:
            missing = [case_id for case_id in plan["cases"] if case_id not in results]
            if missing:
                errors.append(
                    ValidationError(
                        str(path),
                        f"run pins the current plan version but does not account for cases {missing}",
                    )
                )
    findings = [entry for entry in frontmatter.get("findings") or [] if isinstance(entry, str)]
    flow_findings = [entry for entry in frontmatter.get("flow_findings") or [] if isinstance(entry, str)]
    return errors, findings, flow_findings
