"""Markdown execution-plan (`<plan_id>.md`) contract validation."""

from __future__ import annotations

import re
from pathlib import Path

from .common import (
    ROOT,
    ValidationError,
    heading_present,
    is_separator_row,
    load_record_markdown,
    parse_plan_task_row,
    validate_timestamp_order,
)
from .schema import SchemaValidator

PLAN_REQUIRED_HEADINGS = (
    "## 进展概览",
    "## 任务清单",
    "## 验证命令",
)


PLAN_TASK_ID_PATTERN = re.compile(r"^`?([A-Z][A-Z0-9._-]*)`?$")


PLAN_TASK_STATUSES = ("未开始", "进行中", "已完成", "阻塞", "本期不做")


PLAN_TASK_STATUS_MARKS = {"☐": "未开始", "◐": "进行中", "☑": "已完成", "⚠": "阻塞", "—": "本期不做"}


def validate_plan_markdown(path: Path) -> list[ValidationError]:
    """Validate a Markdown execution plan: frontmatter envelope plus body assertions.

    Body assertions (the hybrid contract's machine half): required sections exist; the task
    table's ID column is unique; every `依赖` reference resolves to a listed task and the
    dependency graph is acyclic; task statuses come from the fixed enum (checkbox mark or
    the literal status word); blocking `未决项` rows are closed before `status: approved`;
    the plan file is named after plan_id.
    """
    frontmatter, body, errors = load_record_markdown(path)
    if errors or frontmatter is None:
        return errors
    try:
        validator = SchemaValidator(ROOT / "schemas" / "plan.schema.json")
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors
    errors.extend(validate_timestamp_order(frontmatter, path))
    if path.stem != frontmatter.get("plan_id"):
        errors.append(ValidationError(str(path), "plan filename must equal its plan_id"))

    for heading in PLAN_REQUIRED_HEADINGS:
        if not heading_present(body, heading):
            errors.append(ValidationError(str(path), f"body section {heading!r} is required"))

    task_ids: list[str] = []
    task_deps: dict[str, list[str]] = {}
    task_rows: dict[str, int] = {}
    in_task_section = False
    lines = body.splitlines()
    for index, line in enumerate(lines):
        lineno = index + 1
        if line.startswith("## "):
            in_task_section = line.strip() == "## 任务清单"
            continue
        if not in_task_section:
            continue
        if line.strip().startswith(">"):
            continue
        row = parse_plan_task_row(line)
        if row is None:
            continue
        # A header row is the table row immediately followed by a separator row.
        if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
            continue
        cells = row["cells"]
        if len(cells) < 5:  # task tables carry ID/任务/优先级/代码落点/依赖/状态/证据 — narrower tables (e.g. the overview) are not task rows
            continue
        first = PLAN_TASK_ID_PATTERN.match(cells[0])
        if not first:
            continue
        task_id = first.group(1)
        if task_id in task_rows:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: duplicate task id {task_id!r} (first seen at line {task_rows[task_id]})",
                )
            )
            continue
        task_rows[task_id] = lineno
        task_ids.append(task_id)
        deps: list[str] = []
        for dep in cells[4].replace("`", "").replace("、", ",").replace("，", ",").replace("；", ",").split(","):
            dep = dep.strip().rstrip("；;、").strip()
            if dep in ("", "—", "-", "无"):
                continue
            deps.append(dep)
        task_deps[task_id] = deps
        if len(cells) >= 6:
            status_cell = cells[5].strip()
            mark = status_cell[:1]
            status_word = PLAN_TASK_STATUS_MARKS.get(mark, status_cell)
            if status_word not in PLAN_TASK_STATUSES:
                errors.append(
                    ValidationError(
                        str(path),
                        f"line {lineno}: task {task_id} status {status_cell!r} must be one of {PLAN_TASK_STATUSES}",
                    )
                )

    known = set(task_ids)
    graph: dict[str, list[str]] = task_deps
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(ValidationError(str(path), f"task dependency cycle includes {node!r}"))
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for task_id in task_ids:
        for dep in task_deps.get(task_id, []):
            if dep not in known:
                errors.append(
                    ValidationError(str(path), f"task {task_id!r} references unknown dependency {dep!r}")
                )
        visit(task_id)

    if frontmatter.get("status") == "approved":
        # Scan the 未决项 table: a row whose 是否阻塞 column says 阻塞 and whose 状态 column
        # is not closed marks an open blocking decision — approval is then invalid.
        in_unresolved = False
        for index, line in enumerate(lines):
            if line.startswith(("## ", "### ")):
                in_unresolved = "未决项" in line
                continue
            if not in_unresolved:
                continue
            if is_separator_row(line):
                continue
            row = parse_plan_task_row(line)
            if row is None or len(row["cells"]) < 4:
                continue
            # Only the real header row is skipped: the table row immediately followed by its
            # separator. Matching on text (a 未决 or 编号 substring) let an open decision pass.
            if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
                continue
            cells = row["cells"]
            is_blocking = any(
                "阻塞" in cell and "不阻塞" not in cell for cell in cells[:-1]
            )
            # Open unless a closure marker appears in the row; "尚未关闭"/"未关闭"/"待定" are all open.
            closed = any(marker in cell for cell in cells for marker in ("已关闭", "已解决", "已定"))
            if is_blocking and not closed:
                errors.append(
                    ValidationError(
                        str(path),
                        f"status is approved but blocking unresolved decision {cells[0]!r} is still open; "
                        "close it or downgrade the status",
                    )
                )
    return errors
