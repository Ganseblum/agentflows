"""Markdown execution-plan (`<plan_id>.md`) contract validation."""

from __future__ import annotations

import re
from pathlib import Path

from docchain.constants import TASK_STATUS_GLYPHS, TASK_STATUS_WORDS

from .common import (
    ROOT,
    ValidationError,
    header_columns,
    heading_present,
    is_separator_row,
    is_table_row,
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


def _header_status_columns(line: str) -> dict[str, int] | None:
    """Column mapping when `line` is a task-table header row, else None.

    Used per-table during the row walk: a plan may carry several tables in its task section,
    and reading the status column from the *first* table's header made rows in a later table
    read the wrong column — or an empty one, which the old code then skipped silently, letting
    an invalid status through whenever the column shift landed on a blank cell.
    """
    columns = header_columns(line)
    if columns is None or len(columns) < 5:
        return None
    first = next(iter(columns))
    if first.strip("`* ") != "ID" or "状态" not in columns:
        return None
    return columns


# 2026-10-29：这两个常量原样抄了 docchain/constants.py 的一份映射（两份拷贝靠注释维持同步，
# 见 2026-10-26 整体审核那条双拷贝记录）。现在导入同一份，改动只可能发生在一处。
PLAN_TASK_STATUSES = TASK_STATUS_WORDS
PLAN_TASK_STATUS_MARKS = TASK_STATUS_GLYPHS


BLOCKING_YES = ("是", "阻塞", "blocking", "yes")
BLOCKING_NO = ("否", "不阻塞", "非阻塞", "no")


def _blocking_cell(cells: list[str], columns: dict[str, int] | None) -> bool:
    """Whether a 未决项 row is blocking, read from the blocking column by name (T07)."""
    name = None
    if columns:
        for candidate in ("是否阻塞", "阻塞性", "是否阻塞实施", "阻塞"):
            if candidate in columns:
                name = candidate
                break
    if name is None or columns is None:
        # The official three-column form (前置 / 关联任务 / 说明) has no blocking column: its rows
        # are pending prerequisites, so they block approval until a closure marker appears.
        return len(cells) <= 3
    position = columns[name]
    if position >= len(cells):
        return True
    value = cells[position].strip().strip("`* ")
    if not value:
        return True  # an empty blocking cell is not a "no"
    if any(token in value for token in BLOCKING_NO):
        return False
    if any(token in value for token in BLOCKING_YES):
        return True
    # Fail closed: an unrecognised value (待定 / TBD / 未确认) is not evidence that the item
    # may proceed; treating it as "no" let an approved plan carry an open blocker (F2).
    return True


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
    # Status column of the table the current row belongs to. Reset when the row walk leaves a
    # table so a second table with a different column order cannot inherit the first one's map.
    table_status_columns: dict[str, int] | None = None
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
        # A separator row is still part of the table: it must not clear the column map that
        # the header row just set (otherwise every task row falls back to positional reads).
        if not is_table_row(line) and not is_separator_row(line):
            table_status_columns = None
            continue
        row = parse_plan_task_row(line)
        if row is None:
            continue
        # A header row is the table row immediately followed by a separator row: it opens a new
        # table, so the status-column map is re-read from *this* header, not kept from the
        # first table in the section.
        if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
            table_status_columns = _header_status_columns(line)
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
        # 依赖 read by column name (T05): the old `cells[4]` broke the moment a table carried
        # an extra column before 依赖. Fall back to index 4 only when the table has no header.
        deps_position = None
        if table_status_columns is not None and "依赖" in table_status_columns:
            deps_position = table_status_columns["依赖"]
        elif len(cells) > 4:
            deps_position = 4
        deps_cell = cells[deps_position] if deps_position is not None and len(cells) > deps_position else ""
        for dep in deps_cell.replace("`", "").replace("、", ",").replace("，", ",").replace("；", ",").split(","):
            dep = dep.strip().rstrip("；;、").strip()
            if dep in ("", "—", "-", "无"):
                continue
            deps.append(dep)
        task_deps[task_id] = deps
        # Read the status cell by column name when the row's table declares a header (C9 reads
        # it the same way). Reading by fixed index broke the shipped template, whose task table
        # carries a 优先级 column before 代码落点 — instructions and gate disagreed on which
        # column was "status" (2026-10-20 evaluation G10). Fall back to index 5 only when the
        # current table has no recognizable header. An empty cell is an error, not a skip:
        # `if status_cell:` let an invalid status pass whenever a column shift landed on a
        # blank cell — the check named "statuses come from the fixed enum" then checked nothing.
        if table_status_columns is not None and len(cells) > table_status_columns["状态"]:
            status_cell = cells[table_status_columns["状态"]].strip()
        elif len(cells) >= 6:
            status_cell = cells[5].strip()
        else:
            status_cell = ""
        if not status_cell:
            errors.append(
                ValidationError(
                    str(path),
                    f"line {lineno}: task {task_id} has an empty or missing status cell; "
                    f"the status column must be one of {PLAN_TASK_STATUSES}",
                )
            )
            continue
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
        # Scan the 未决项 table: a row whose blocking column says yes and whose status is not
        # closed marks an open blocking decision — approval is then invalid.
        #
        # T07: the blocking column is read *by name* and accepts both spellings the shipped
        # templates use ("阻塞 / 不阻塞" and "是 / 否"). The old code scanned every cell for the
        # substring 阻塞, so a row whose 问题 text merely mentioned 阻塞 counted as blocking, and
        # a template writing "是" counted as non-blocking. The official three-column form
        # (前置 / 关联任务 / 说明) carries no blocking column at all — its rows are pending
        # prerequisites, so they are blocking by definition until closed.
        in_unresolved = False
        columns: dict[str, int] | None = None
        for index, line in enumerate(lines):
            if line.startswith(("## ", "### ")):
                in_unresolved = "未决项" in line
                columns = None
                continue
            if not in_unresolved:
                continue
            if is_separator_row(line):
                continue
            row = parse_plan_task_row(line)
            if row is None or len(row["cells"]) < 3:
                columns = None
                continue
            # Only the real header row is skipped: the table row immediately followed by its
            # separator. Matching on text (a 未决 or 编号 substring) let an open decision pass.
            if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
                columns = header_columns(line)
                continue
            cells = row["cells"]
            is_blocking = _blocking_cell(cells, columns)
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
