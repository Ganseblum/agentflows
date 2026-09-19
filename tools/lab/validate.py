#!/usr/bin/env python3
"""Validate Agentflow contracts, examples, and public evaluation fixtures.

This intentionally uses only the Python standard library. It implements the small
Draft 2020-12 vocabulary used by the repository's contracts and adds explicit
cross-document checks that JSON Schema cannot express conveniently.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import artifact_digest  # noqa: E402  (sibling module, standard library only)


ROOT = Path(__file__).resolve().parents[2]
BUG_RECORD_SCHEMA = ROOT / "schemas" / "bug-record.schema.json"
RECURRENCE_SCHEMA = ROOT / "schemas" / "recurrence.schema.json"
REVIEW_SCHEMA = ROOT / "schemas" / "review.schema.json"
TEST_PLAN_SCHEMA = ROOT / "schemas" / "test-plan.schema.json"
TEST_RUN_SCHEMA = ROOT / "schemas" / "test-run.schema.json"
EPISODE_SCHEMA = ROOT / "skills" / "improve" / "references" / "episode.schema.json"
PROTECTED_PATHS_FILE = ROOT / "protected-paths.txt"
SCHEMA_PATHS = [
    ROOT / "schemas",
    ROOT / "skills" / "improve" / "references",
]
IMPROVEMENT_SCHEMA_NAMES = {
    "business-case.schema.json",
    "candidate.schema.json",
    "episode.schema.json",
    "eval-case.schema.json",
    "release-record.schema.json",
}

# The minimum gate surface protected-paths.txt must still cover. Editing this set is a release
# policy change and requires explicit human review; it is not something a candidate may arrange
# around. Keep it in sync with the inclusion rule documented in protected-paths.txt.
REQUIRED_PROTECTED_PATHS = {
    "agents/evaluator.md",
    "agents/release-governor.md",
    "evals",
    "schemas/bug-record.schema.json",
    "schemas/recurrence.schema.json",
    "schemas/review.schema.json",
    "schemas/plan.schema.json",
    "schemas/evaluation-result.schema.json",
    "schemas/test-plan.schema.json",
    "schemas/test-run.schema.json",
    "skills/improve/references/evidence-and-release.md",
    "skills/improve/references/episode.schema.json",
    "skills/improve/references/eval-case.schema.json",
    "skills/improve/references/candidate.schema.json",
    "skills/improve/references/release-record.schema.json",
    "tests/test_lab_contracts.py",
    "tests/test_record_store.py",
    "tools/lab/artifact_digest.py",
    "tools/lab/eval_runner.py",
    "tools/lab/host_adapter.py",
    "tools/lab/isolation.py",
    "tools/lab/policy.py",
    "tools/lab/seed_grader.py",
    "tools/lab/validate.py",
    "protected-paths.txt",
    ".github/workflows/validate.yml",
}

# The business evaluation slice (evals/business): real document review against a read-only
# enterprise snapshot. The snapshot repository is deliberately absent from this checkout, so
# target_id, target_pin, and target_docs are checked structurally only — requiring them to
# resolve would drag an enterprise path into the public validation surface. input_ref and
# seeds_ref do point into this repository and must resolve.
BUSINESS_EVALS_DIR = ROOT / "evals" / "business"
BUSINESS_CASE_SCHEMA = ROOT / "skills" / "improve" / "references" / "business-case.schema.json"
BUSINESS_CASE_COUNT_RANGE = (3, 10)
BUSINESS_SEED_STRATEGY_TYPES = ("path_and_anchor",)

# Declared contents of `tests/`. The directory is not a protected prefix — generated
# `__pycache__` entries there would otherwise block every candidate that ran the checks — so the
# pinned test files are protected individually and this list asserts nothing else appears. A new
# test file is a human-authored change to this list plus the protection entry above.
EXPECTED_TEST_FILES = ("test_lab_contracts.py", "test_record_store.py")

# Floor for the regression suite size, parsed from the unittest "Ran N tests" summary. The
# suite currently runs 108 tests; the floor is set far below that steady state but far above a
# trivial suite, so deleting or gutting the tests cannot yield a green gate — shrinking the
# suite becomes a deliberate gate change that must be reviewed, not an accident that passes.
MIN_UNIT_TEST_COUNT = 20

# Every manifest that carries the plugin name and version. They are bumped by hand, so a missed
# bump would otherwise surface only after a host reinstall. The pointer locates the value.
MANIFEST_POINTERS = (
    ("plugin.json", ()),
    ("marketplace.json", ("plugins", 0)),
    (".zcode-plugin/plugin.json", ()),
    (".claude-plugin/plugin.json", ()),
    (".codex-plugin/plugin.json", ()),
)

# Components whose content decides installed plugin behavior. Anything outside this list
# (docs, records, evals) may legitimately differ between a source checkout and a snapshot.
INSTALLED_COMPONENTS = ("agents", "skills")
INSTALLED_FILES = (
    "plugin.json",
    "marketplace.json",
    ".zcode-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
)


class ValidationError:
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def load_json(path: Path) -> tuple[Any | None, list[ValidationError]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, [ValidationError(str(path), f"invalid JSON: {exc}")]


def read_document_text(path: Path) -> tuple[str | None, list[ValidationError]]:
    """Read a Markdown/text document for a doc-surface check; read failures are structured.

    Mirrors `load_json` for text: UnicodeDecodeError is a ValueError, not an OSError, so a
    file saved in a non-UTF-8 encoding (or a missing document) must surface as a
    ValidationError instead of an uncaught traceback escaping the check.
    """
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeDecodeError) as exc:
        return None, [ValidationError(str(path), f"cannot read document: {exc}")]


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    """Parse a '---' delimited frontmatter block of flat scalars and simple lists.

    Accepts exactly: blank lines, `key: value` scalars, `key:` starting a list of
    `  - item` lines, and `key: [a, b]` inline lists. Anything else is an error —
    nested mappings are deliberately unsupported so the contract stays flat.
    """
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "", ["frontmatter block is missing"]
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, "", ["frontmatter block is not closed"]

    data: dict[str, Any] = {}
    list_key: str | None = None
    for lineno, raw in enumerate(lines[1:end], start=2):
        line = raw.rstrip()
        if not line.strip():
            continue
        if "\t" in line:
            errors.append(f"frontmatter line {lineno}: tabs are not allowed")
            continue
        if line.startswith("  - "):
            if list_key is None:
                errors.append(f"frontmatter line {lineno}: list item without a key")
                continue
            data[list_key].append(line[4:].strip())
            continue
        if line.startswith("- "):
            errors.append(f"frontmatter line {lineno}: list items must be indented under a key")
            continue
        if line.startswith("  "):
            errors.append(f"frontmatter line {lineno}: nested mappings are not supported")
            continue
        if ":" not in line:
            errors.append(f"frontmatter line {lineno}: expected 'key: value'")
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            errors.append(f"frontmatter line {lineno}: empty key")
            continue
        if key in data:
            errors.append(f"frontmatter line {lineno}: duplicate key {key!r}")
            continue
        if value == "":
            data[key] = []
            list_key = key
            continue
        list_key = None
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [item.strip() for item in inner.split(",") if item.strip()]
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            data[key] = value
    body = "\n".join(lines[end + 1 :])
    return data, body, errors


def load_bug_markdown(path: Path) -> tuple[dict[str, Any] | None, str, list[ValidationError]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError is a ValueError, not an OSError: a non-UTF-8 record must
        # surface as a structured ValidationError (mirrors read_document_text), not an
        # uncaught traceback escaping the check.
        return None, "", [ValidationError(str(path), f"unreadable file: {exc}")]
    frontmatter, body, parse_errors = parse_frontmatter(text)
    if parse_errors:
        return None, "", [ValidationError(str(path), message) for message in parse_errors]
    if not isinstance(frontmatter, dict) or not frontmatter:
        return None, "", [ValidationError(str(path), "frontmatter is empty")]
    return frontmatter, body, []


def heading_present(body: str, heading: str) -> bool:
    return any(line.strip() == heading for line in body.splitlines())


def json_equal_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def json_values_equal(left: Any, right: Any) -> bool:
    """Compare JSON values using JSON Schema equality (booleans are not numbers)."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


RFC3339_DATE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)


def parse_rfc3339_date_time(value: str) -> dt.datetime:
    """Parse the RFC 3339 subset supported by the standard library.

    Repository artifacts accept either case for the RFC 3339 ``T``/``Z`` separators.
    Leap-second values (``:60``) remain intentionally unsupported because Python's
    ``datetime`` cannot represent them.
    """
    if RFC3339_DATE_TIME.fullmatch(value) is None:
        raise ValueError("must be an RFC 3339 date-time")
    parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00" if value[-1] in "Zz" else value)
    if parsed.tzinfo is None:
        raise ValueError("must include a timezone offset")
    return parsed


def is_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


class SchemaValidator:
    def __init__(self, schema_path: Path):
        self.schema_path = schema_path.resolve()
        self.schema, errors = load_json(self.schema_path)
        if errors:
            raise ValueError(str(errors[0]))
        self._loaded: dict[Path, Any] = {self.schema_path: self.schema}

    def validate(self, instance: Any) -> list[ValidationError]:
        return self._validate(instance, self.schema, "$", self.schema_path)

    def _load_schema(self, path: Path) -> Any:
        path = path.resolve()
        if path not in self._loaded:
            schema, errors = load_json(path)
            if errors:
                raise ValueError(str(errors[0]))
            self._loaded[path] = schema
        return self._loaded[path]

    def _resolve_pointer(self, value: Any, fragment: str) -> Any:
        if fragment in ("", "#"):
            return value
        pointer = fragment[1:] if fragment.startswith("#") else fragment
        if pointer.startswith("/"):
            current = value
            for part in pointer[1:].split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                if isinstance(current, list):
                    current = current[int(part)]
                else:
                    current = current[part]
            return current
        raise ValueError(f"unsupported JSON reference fragment: {fragment}")

    def _resolve_ref(self, ref: str, current_schema_path: Path) -> tuple[Any, Path]:
        if ref.startswith("#"):
            return self._resolve_pointer(self._load_schema(current_schema_path), ref), current_schema_path
        raw_path, separator, fragment = ref.partition("#")
        target_path = (current_schema_path.parent / raw_path).resolve()
        target = self._load_schema(target_path)
        return self._resolve_pointer(target, f"#{fragment}" if separator else ""), target_path

    def _matches(self, instance: Any, schema: Any, schema_path: Path) -> bool:
        return not self._validate(instance, schema, "$", schema_path)

    def _validate(
        self,
        instance: Any,
        schema: Any,
        path: str,
        schema_path: Path,
    ) -> list[ValidationError]:
        if not isinstance(schema, dict):
            return []

        errors: list[ValidationError] = []

        if "$ref" in schema:
            try:
                target, target_path = self._resolve_ref(schema["$ref"], schema_path)
                errors.extend(self._validate(instance, target, path, target_path))
            except (KeyError, IndexError, ValueError, OSError) as exc:
                errors.append(ValidationError(path, f"cannot resolve $ref {schema['$ref']!r}: {exc}"))
            return errors

        if "const" in schema and not json_values_equal(instance, schema["const"]):
            errors.append(ValidationError(path, f"must equal {schema['const']!r}"))

        if "enum" in schema and not any(json_values_equal(instance, item) for item in schema["enum"]):
            errors.append(ValidationError(path, f"must be one of {schema['enum']!r}"))

        expected_type = schema.get("type")
        if expected_type is not None:
            types = expected_type if isinstance(expected_type, list) else [expected_type]
            if not any(is_type(instance, type_name) for type_name in types):
                return errors + [ValidationError(path, f"must be of type {expected_type!r}")]

        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < schema["minLength"]:
                errors.append(ValidationError(path, f"must have at least {schema['minLength']} characters"))
            if "maxLength" in schema and len(instance) > schema["maxLength"]:
                errors.append(ValidationError(path, f"must have at most {schema['maxLength']} characters"))
            if "pattern" in schema:
                try:
                    matches = re.search(schema["pattern"], instance)
                except re.error as exc:
                    errors.append(ValidationError(path, f"invalid schema pattern: {exc}"))
                else:
                    if matches is None:
                        errors.append(ValidationError(path, f"does not match {schema['pattern']!r}"))
            if schema.get("format") == "date-time":
                try:
                    parse_rfc3339_date_time(instance)
                except ValueError:
                    errors.append(ValidationError(path, "must be an RFC 3339 date-time"))

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(ValidationError(path, f"must be >= {schema['minimum']}"))
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(ValidationError(path, f"must be <= {schema['maximum']}"))

        if isinstance(instance, list):
            if "minItems" in schema and len(instance) < schema["minItems"]:
                errors.append(ValidationError(path, f"must contain at least {schema['minItems']} items"))
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                errors.append(ValidationError(path, f"must contain at most {schema['maxItems']} items"))
            if schema.get("uniqueItems"):
                keys = [json_equal_key(item) for item in instance]
                if len(keys) != len(set(keys)):
                    errors.append(ValidationError(path, "items must be unique"))
            if "items" in schema:
                for index, item in enumerate(instance):
                    errors.extend(self._validate(item, schema["items"], f"{path}[{index}]", schema_path))
            if "contains" in schema:
                matches = sum(1 for item in instance if self._matches(item, schema["contains"], schema_path))
                minimum = schema.get("minContains", 1)
                if matches < minimum:
                    errors.append(ValidationError(path, f"must contain at least {minimum} matching item(s)"))

        if isinstance(instance, dict):
            for required in schema.get("required", []):
                if required not in instance:
                    errors.append(ValidationError(path, f"missing required property {required!r}"))

            properties = schema.get("properties", {})
            for name, value in instance.items():
                if name in properties:
                    errors.extend(self._validate(value, properties[name], f"{path}.{name}", schema_path))
                elif schema.get("additionalProperties") is False:
                    errors.append(ValidationError(path, f"unexpected property {name!r}"))
                elif isinstance(schema.get("additionalProperties"), dict):
                    errors.extend(
                        self._validate(value, schema["additionalProperties"], f"{path}.{name}", schema_path)
                    )

        for subschema in schema.get("allOf", []):
            errors.extend(self._validate(instance, subschema, path, schema_path))

        if "if" in schema and self._matches(instance, schema["if"], schema_path):
            if "then" in schema:
                errors.extend(self._validate(instance, schema["then"], path, schema_path))
        elif "else" in schema:
            errors.extend(self._validate(instance, schema["else"], path, schema_path))

        if "not" in schema and self._matches(instance, schema["not"], schema_path):
            errors.append(ValidationError(path, "must not match the forbidden schema"))

        if "anyOf" in schema and not any(self._matches(instance, item, schema_path) for item in schema["anyOf"]):
            errors.append(ValidationError(path, "must match at least one anyOf schema"))

        if "oneOf" in schema and sum(self._matches(instance, item, schema_path) for item in schema["oneOf"]) != 1:
            errors.append(ValidationError(path, "must match exactly one oneOf schema"))

        return errors


def iter_schema_paths() -> Iterable[Path]:
    for directory in SCHEMA_PATHS:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.schema.json")):
            if directory.name == "references" and path.name not in IMPROVEMENT_SCHEMA_NAMES:
                continue
            yield path


def schema_for(relative_path: Path) -> Path | None:
    parts = relative_path.parts
    if len(parts) >= 2 and parts[0] == "evals" and parts[1] == "public":
        return ROOT / "skills" / "improve" / "references" / "eval-case.schema.json"
    if len(parts) >= 2 and parts[0] == "evals" and parts[1] == "business":
        return BUSINESS_CASE_SCHEMA
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "evaluation-results":
        return ROOT / "schemas" / "evaluation-result.schema.json"
    return None


def path_inside_root(relative_ref: str) -> Path | None:
    candidate = (ROOT / relative_ref).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def validate_timestamp_order(document: dict[str, Any], path: Path) -> list[ValidationError]:
    recorded = document.get("recorded_at")
    updated = document.get("updated_at")
    if not isinstance(recorded, str):
        return []
    timestamps: list[tuple[str, str]] = [("recorded_at", recorded)]
    if isinstance(updated, str):
        timestamps.append(("updated_at", updated))
    parsed: dict[str, dt.datetime] = {}
    for name, raw in timestamps:
        try:
            parsed[name] = parse_rfc3339_date_time(raw)
        except ValueError:
            return [ValidationError(str(path), f"{name} must be an RFC 3339 date-time value")]
    now = dt.datetime.now(dt.timezone.utc)
    for name, value in parsed.items():
        if value > now + dt.timedelta(minutes=5):
            errors = [ValidationError(str(path), f"{name} is in the future; stamps must reflect real time")]
            return errors
    if "updated_at" in parsed and parsed["updated_at"] < parsed["recorded_at"]:
        return [ValidationError(str(path), "updated_at must not precede recorded_at")]
    return []


BUG_REQUIRED_HEADINGS = ("## 现象", "## 根因")
BUG_ARCHIVE_DIR = "archive"
RECURRENCE_DIR = "recurrence"
BUG_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

PLAN_REQUIRED_HEADINGS = (
    "## 进展概览",
    "## 任务清单",
    "## 验证命令",
)
PLAN_TASK_ID_PATTERN = re.compile(r"^`?([A-Z][A-Z0-9._-]*)`?$")
PLAN_TASK_STATUSES = ("未开始", "进行中", "已完成", "阻塞", "本期不做")
PLAN_TASK_STATUS_MARKS = {"☐": "未开始", "◐": "进行中", "☑": "已完成", "⚠": "阻塞", "—": "本期不做"}


def is_separator_row(line: str) -> bool:
    """True for a Markdown table separator row (---|:---:|...)."""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return bool(cells) and all(set(cell) <= {"-", ":", " "} and cell for cell in cells)


def parse_plan_task_row(line: str) -> dict[str, str] | None:
    """Parse one Markdown table row of the plan task table into its cells."""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if len(cells) < 3:
        return None
    if all(set(cell) <= {"-", ":", " "} for cell in cells):
        return None  # separator row
    return {"cells": cells}


def validate_plan_markdown(path: Path, relative: Path) -> list[ValidationError]:
    """Validate a Markdown execution plan: frontmatter envelope plus body assertions.

    Body assertions (the hybrid contract's machine half): required sections exist; the task
    table's ID column is unique; every `依赖` reference resolves to a listed task and the
    dependency graph is acyclic; task statuses come from the fixed enum (checkbox mark or
    the literal status word); blocking `未决项` rows are closed before `status: approved`;
    the plan file is named after plan_id.
    """
    frontmatter, body, errors = load_bug_markdown(path)
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
        for line in body.splitlines():
            if line.startswith("## ") or line.startswith("### "):
                in_unresolved = "未决项" in line
                continue
            if not in_unresolved:
                continue
            if is_separator_row(line):
                continue
            row = parse_plan_task_row(line)
            if row is None or len(row["cells"]) < 4:
                continue
            cells = row["cells"]
            joined = "".join(cells)
            if "未决" in joined or "编号" in cells[0]:
                continue  # header or intro row
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


def version_tuple(value: str) -> tuple[int, int, int]:
    """Numeric ordering key for the semver-like versions the schemas enforce."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def validate_recurrence_markdown(path: Path) -> list[ValidationError]:
    """Validate one recurrence ledger: schema, timestamp order, filename/class_id agreement."""
    frontmatter, body, errors = load_bug_markdown(path)
    if errors or frontmatter is None:
        return errors
    try:
        validator = SchemaValidator(RECURRENCE_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors
    errors.extend(validate_timestamp_order(frontmatter, path))
    errors.extend(validate_body_references(body, path))
    if path.stem != frontmatter.get("class_id"):
        errors.append(
            ValidationError(str(path), "ledger filename must equal class_id")
        )
    return errors


BODY_PATH_PATTERN = re.compile(
    r"(?:\.\./|\./)?[\w.][\w.\-]*(?:/[\w.\-]+)+\.[A-Za-z]{2,8}"
)
QUALIFIED_REF_PATTERN = re.compile(r"[A-Za-z0-9_.\-]+@[A-Za-z0-9_.\-]+:\S+")
URL_PATTERN = re.compile(r"https?://\S+")


def prose_without_quotations(body: str) -> str:
    """Plain prose only: fenced blocks and inline code spans are quotations, not claims."""
    segments: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            segments.append(line)
    prose = "\n".join(segments)
    return re.sub(r"`[^`]*`", " ", prose)


def validate_body_references(body: str, path: Path) -> list[ValidationError]:
    """Every doc/code path the record itself claims must resolve; quotations are exempt.

    A path in plain prose is the record's own reference: it must exist in this repository
    (or next to the record) or be a repo-qualified reference. Fenced blocks and inline code
    are quotations — evidence quoted verbatim, including historical paths — and are not
    scanned. Personal absolute paths are banned outright: they are neither portable nor
    evidence. URLs cannot be validated and are supplementary at most, never the evidence.
    """
    errors: list[ValidationError] = []
    prose = prose_without_quotations(body)
    if re.search(r"/Users/|/home/|(?<![A-Za-z0-9_.])~/", prose):
        errors.append(
            ValidationError(
                str(path),
                "personal absolute path in prose — records are portable evidence; "
                "use a repo-relative or repo-qualified reference",
            )
        )
    cleaned = URL_PATTERN.sub(" ", prose)
    cleaned = QUALIFIED_REF_PATTERN.sub(" ", cleaned)
    for token in BODY_PATH_PATTERN.findall(cleaned):
        # Containment, not just existence: the pattern admits "../" prefixes, and the old
        # bare is_file() check resolved `(ROOT / "../secret.md")` OUTSIDE the repository —
        # an escape that passed as if it were portable evidence. Both anchors are
        # repository-inside directories, so a reference is accepted only when the resolved
        # path stays inside the repository (relative climbs between record directories
        # stay legal) and the file exists.
        repo_candidate = (ROOT / token).resolve()
        local_candidate = (path.parent / token).resolve()
        repo_root = ROOT.resolve()
        if repo_candidate.is_file() and repo_candidate.is_relative_to(repo_root):
            continue
        if local_candidate.is_file() and local_candidate.is_relative_to(repo_root):
            continue
        errors.append(
            ValidationError(
                str(path),
                f"body references {token!r} which exists neither in this repository nor next "
                "to the record — carry the evidence (quote it, archive it, or use a "
                "repo-qualified reference)",
            )
        )
    return errors


def validate_episode_document(path: Path) -> list[ValidationError]:
    """Validate one episode record: improve-loop episode schema, timestamp, filename=id."""
    document, load_errors = load_json(path)
    if load_errors or not isinstance(document, dict):
        return load_errors or [ValidationError(str(path), "episode record is not a JSON object")]
    try:
        validator = SchemaValidator(EPISODE_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors = validator.validate(document)
    if errors:
        return errors
    expected_id = document.get("episode_id")
    if isinstance(expected_id, str) and path.stem != expected_id:
        errors.append(
            ValidationError(str(path), f"filename stem must equal episode_id {expected_id!r}")
        )
    return errors


def validate_external_excerpts(
    frontmatter: dict[str, Any], body: str, path: Path
) -> list[ValidationError]:
    """External references must carry their evidence: an embedded fragment, cited at its address.

    A repo-qualified reference is an address, not evidence — the record must embed the decisive
    fragment (a fenced code block for code, a blockquote for document passages) and cite the
    qualified address in the body next to it, so the record stays readable and checkable when
    the other repository is absent.
    """
    errors: list[ValidationError] = []
    external = [
        entry
        for entry in frontmatter.get("files") or []
        if isinstance(entry, str) and "@" in entry.partition(":")[0] and ":" in entry
    ]
    if not external:
        return errors
    has_fragment = "```" in body or any(
        line.lstrip().startswith(">") for line in body.splitlines()
    )
    if not has_fragment:
        errors.append(
            ValidationError(
                str(path),
                "external references require an embedded fragment in the body "
                "(fenced code block for code, blockquote for document passages)",
            )
        )
    for entry in external:
        if entry not in body:
            errors.append(
                ValidationError(
                    str(path),
                    f"external reference {entry!r} must be cited in the body next to its excerpt",
                )
            )
    return errors


def validate_review_markdown(
    path: Path, relative: Path, seen_review_ids: dict[str, Path]
) -> list[ValidationError]:
    """Validate one review record: schema, timestamp order, layout, archived-doc existence.

    Layout: records/reviews/<project>-<feature-slug>/review-<YYYY-MM-DD>-<NNN>.md — the
    directory is anchored on the reviewed feature (the same feature may be reviewed many
    times), and the filename must equal the review_id so rounds sort chronologically.
    """
    frontmatter, body, errors = load_bug_markdown(path)
    if errors or frontmatter is None:
        return errors
    try:
        validator = SchemaValidator(REVIEW_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors
    errors.extend(validate_timestamp_order(frontmatter, path))
    errors.extend(validate_body_references(body, path))
    review_id = frontmatter.get("review_id")
    if isinstance(review_id, str):
        if review_id in seen_review_ids:
            errors.append(
                ValidationError(
                    str(path),
                    f"duplicate review_id {review_id!r} already declared in {seen_review_ids[review_id]}",
                )
            )
        else:
            seen_review_ids[review_id] = path
    parts = relative.parts  # ("records", "reviews", "<project>-<feature-slug>", "review-<date>-<NNN>.md")
    if len(parts) != 4:
        errors.append(
            ValidationError(str(path), "review records live in records/reviews/<project>-<feature-slug>/")
        )
    else:
        if "-" not in parts[2] or parts[2].startswith("-") or parts[2].endswith("-"):
            errors.append(
                ValidationError(str(path), "review directory must be named <project>-<feature-slug>")
            )
        if isinstance(review_id, str):
            m = re.fullmatch(r"REV-(\d{4})(\d{2})(\d{2})-(\d{3})", review_id)
            if m:
                expected_stem = f"review-{m.group(1)}-{m.group(2)}-{m.group(3)}-{m.group(4)}"
                if path.stem != expected_stem:
                    errors.append(
                        ValidationError(
                            str(path),
                            f"filename must be {expected_stem}.md to match review_id {review_id!r}",
                        )
                    )
                recorded = frontmatter.get("recorded_at")
                if isinstance(recorded, str):
                    try:
                        recorded_date = dt.datetime.fromisoformat(
                            recorded.replace("Z", "+00:00")
                        ).date()
                    except ValueError:
                        recorded_date = None
                    if recorded_date is not None and recorded_date.strftime("%Y%m%d") != "".join(m.group(1, 2, 3)):
                        errors.append(
                            ValidationError(
                                str(path),
                                f"review_id date must match recorded_at date {recorded_date.isoformat()}",
                            )
                        )
            elif path.stem != review_id:
                errors.append(
                    ValidationError(str(path), "review record filename must match its review_id date and seq")
                )
    for doc in frontmatter.get("reviewed_docs") or []:
        if isinstance(doc, str) and not (path.parent / doc).is_file():
            errors.append(
                ValidationError(str(path), f"archived document {doc!r} not found next to the review record")
            )
    return errors


TEST_CASE_ID_PATTERN = re.compile(r"^TC-[A-Z0-9][A-Z0-9-]*$")
TEST_CASE_LEVELS = ("smoke", "e2e", "api", "boundary")
TEST_CASE_PRIORITIES = ("P0", "P1", "P2", "P3")
TEST_RESULT_STATUSES = ("pass", "fail", "blocked", "not-run")
TEST_PLAN_REQUIRED_HEADINGS = ("## 用例", "## 边界覆盖", "## 流程疑点")
TEST_RUN_REQUIRED_HEADINGS = ("## 结果", "## 证据", "## 结论")
# Cells that count as "no evidence" in a run's 结果 table; fail/blocked rows may not use them.
NO_EVIDENCE_CELLS = ("", "—", "-", "无")


def parse_test_case_registry(
    body: str, path: Path
) -> tuple[list[dict[str, str]], list[ValidationError]]:
    """Parse the 用例 registry table: rows whose first cell is a TC id carry ID/级别/优先级/标题."""
    cases: list[dict[str, str]] = []
    errors: list[ValidationError] = []
    lines = body.splitlines()
    seen: dict[str, int] = {}
    for index, line in enumerate(lines):
        lineno = index + 1
        row = parse_plan_task_row(line)
        if row is None:
            continue
        if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
            continue  # header row
        cells = row["cells"]
        if len(cells) < 4 or not TEST_CASE_ID_PATTERN.match(cells[0]):
            continue
        case_id, level, priority = cells[0], cells[1], cells[2]
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
        cases.append({"case_id": case_id, "level": level, "priority": priority, "title": cells[3]})
    return cases, errors


def validate_test_plan_markdown(
    path: Path, relative: Path, seen_plan_ids: dict[str, Path]
) -> tuple[list[ValidationError], dict[str, Any] | None]:
    """Validate one test plan and return (errors, plan entry) for run-record cross-checks.

    Layout: records/tests/<project>-<feature-slug>/plan-<YYYY-MM-DD>-<NNN>.md — feature-anchored
    directory, filename matches test_plan_id, revised in place (test_version bump). Body
    contract: the 用例 registry table (unique TC ids, level/priority enums, case_count equality,
    one detail heading per case) plus the 边界覆盖 and 流程疑点 sections.
    """
    frontmatter, body, errors = load_bug_markdown(path)
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
        match = re.fullmatch(r"TP-(\d{4})(\d{2})(\d{2})-(\d{3})", test_plan_id)
        if match:
            expected_stem = f"plan-{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
            if path.stem != expected_stem:
                errors.append(
                    ValidationError(
                        str(path),
                        f"filename must be {expected_stem}.md to match test_plan_id {test_plan_id!r}",
                    )
                )
            recorded = frontmatter.get("recorded_at")
            if isinstance(recorded, str):
                try:
                    recorded_date = dt.datetime.fromisoformat(recorded.replace("Z", "+00:00")).date()
                except ValueError:
                    recorded_date = None
                if recorded_date is not None and recorded_date.strftime("%Y%m%d") != "".join(
                    match.group(1, 2, 3)
                ):
                    errors.append(
                        ValidationError(
                            str(path),
                            f"test_plan_id date must match recorded_at date {recorded_date.isoformat()}",
                        )
                    )
        else:
            errors.append(
                ValidationError(str(path), "plan record filename must match its test_plan_id date and seq")
            )
    parts = relative.parts
    if parts[0] == "records":
        # Example instances live under examples/ and are not layout-checked.
        if len(parts) != 4:
            errors.append(
                ValidationError(str(path), "test plans live in records/tests/<project>-<feature-slug>/")
            )
        elif "-" not in parts[2] or parts[2].startswith("-") or parts[2].endswith("-"):
            errors.append(
                ValidationError(str(path), "test directory must be named <project>-<feature-slug>")
            )
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
    cross-check the bug-id pools after the whole records tree has been walked.

    Body contract: the 结果 table (unique case ids from the referenced plan's registry, fixed
    result enum, evidence required on fail/blocked rows), summary counts equal to the table,
    decision pass requires zero fail/blocked, and — when the run pins the plan's current
    test_version — every case in the registry is accounted for.
    """
    frontmatter, body, errors = load_bug_markdown(path)
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
        match = re.fullmatch(r"TR-(\d{4})(\d{2})(\d{2})-(\d{3})", test_run_id)
        if match:
            expected_stem = f"run-{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
            if path.stem != expected_stem:
                errors.append(
                    ValidationError(
                        str(path),
                        f"filename must be {expected_stem}.md to match test_run_id {test_run_id!r}",
                    )
                )
            recorded = frontmatter.get("recorded_at")
            if isinstance(recorded, str):
                try:
                    recorded_date = dt.datetime.fromisoformat(recorded.replace("Z", "+00:00")).date()
                except ValueError:
                    recorded_date = None
                if recorded_date is not None and recorded_date.strftime("%Y%m%d") != "".join(
                    match.group(1, 2, 3)
                ):
                    errors.append(
                        ValidationError(
                            str(path),
                            f"test_run_id date must match recorded_at date {recorded_date.isoformat()}",
                        )
                    )
        else:
            errors.append(
                ValidationError(str(path), "run record filename must match its test_run_id date and seq")
            )
    parts = relative.parts
    if parts[0] == "records" and len(parts) != 4:
        errors.append(
            ValidationError(str(path), "test runs live in records/tests/<project>-<feature-slug>/")
        )
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
    lines = body.splitlines()
    for index, line in enumerate(lines):
        lineno = index + 1
        if line.startswith("## "):
            in_results = line.strip() == "## 结果"
            continue
        if not in_results:
            continue
        row = parse_plan_task_row(line)
        if row is None:
            continue
        if index + 1 < len(lines) and is_separator_row(lines[index + 1]):
            continue  # header row
        cells = row["cells"]
        if len(cells) < 4 or not TEST_CASE_ID_PATTERN.match(cells[0]):
            continue
        case_id, status_cell, evidence = cells[0], cells[1].strip(), cells[2].strip()
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
        if (
            version is not None
            and version == (plan["frontmatter"] or {}).get("test_version")
        ):
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


def validate_bug_markdown(path: Path) -> list[ValidationError]:
    """Validate one Markdown bug record: frontmatter schema, body sections, state rules."""
    frontmatter, body, errors = load_bug_markdown(path)
    if errors or frontmatter is None:
        return errors
    try:
        validator = SchemaValidator(BUG_RECORD_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors
    errors.extend(validate_timestamp_order(frontmatter, path))

    for heading in BUG_REQUIRED_HEADINGS:
        if not heading_present(body, heading):
            errors.append(ValidationError(str(path), f"body section {heading!r} is required"))
    if frontmatter.get("status") != "open" and not heading_present(body, "## 修复"):
        errors.append(ValidationError(str(path), "body section '## 修复' is required unless the bug is open"))
    if frontmatter.get("status") == "verified" and not heading_present(body, "## 审查"):
        errors.append(ValidationError(str(path), "body section '## 审查' is required for a verified record"))
    return errors


def validate_bug_layout(frontmatter: dict[str, Any], path: Path, relative: Path, seen_ids: dict[str, Path]) -> list[ValidationError]:
    """Validate date directory, filename slug, and bug_id uniqueness for one record."""
    errors: list[ValidationError] = []
    bug_id = frontmatter.get("bug_id")
    if isinstance(bug_id, str):
        if bug_id in seen_ids:
            errors.append(
                ValidationError(str(path), f"duplicate bug_id {bug_id!r} already recorded in {seen_ids[bug_id]}")
            )
        else:
            seen_ids[bug_id] = path
    if not BUG_SLUG_PATTERN.match(path.stem):
        errors.append(ValidationError(str(path), "filename must be a kebab-case slug (lowercase letters, digits, hyphens)"))

    parts = relative.parts  # e.g. ("records", "bugs", "2026-09-14", "slug.md") or (..., "archive", "2026-09-14", ...)
    date_parts = [p for p in parts[2:] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p)]
    if not date_parts:
        errors.append(ValidationError(str(path), "record must live in a YYYY-MM-DD directory under records/bugs/"))
        return errors
    recorded = frontmatter.get("recorded_at")
    if isinstance(recorded, str):
        try:
            recorded_date = dt.datetime.fromisoformat(recorded.replace("Z", "+00:00")).date()
        except ValueError:
            recorded_date = None
        if recorded_date is not None and date_parts[-1] != recorded_date.isoformat():
            errors.append(
                ValidationError(
                    str(path),
                    f"date directory {date_parts[-1]!r} does not match recorded_at date {recorded_date.isoformat()}",
                )
            )
    return errors



def validate_eval_invariants(document: dict[str, Any], path: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if document.get("holdout") is not False:
        errors.append(ValidationError(str(path), "public evaluation cases must have holdout=false"))
    input_ref = document.get("input_ref")
    if isinstance(input_ref, str):
        resolved = path_inside_root(input_ref)
        if resolved is None or not resolved.is_file():
            errors.append(ValidationError(str(path), f"input_ref does not resolve to a file: {input_ref!r}"))
    return errors


def validate_evaluation_result_invariants(document: dict[str, Any], path: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    case_results = document.get("case_results", [])
    case_ids = [item.get("case_id") for item in case_results]
    if len(case_ids) != len(set(case_ids)):
        errors.append(ValidationError(str(path), "evaluation case_id values must be unique"))
    if document.get("suite_case_count") != len(case_results):
        errors.append(ValidationError(str(path), "suite_case_count must equal the number of case_results"))
    observed = document.get("observed_context", {})
    for field in ("host", "model", "permissions_profile", "fixture_revision"):
        if observed.get(field) != document.get(field):
            errors.append(ValidationError(str(path), f"observed_context.{field} must match the declared result context"))
    repeat_count = document.get("repeat_count")
    for index, item in enumerate(case_results):
        actual = len(item.get("repetitions", []))
        if actual != repeat_count:
            errors.append(
                ValidationError(
                    f"{path}:$.case_results[{index}].repetitions",
                    f"expected exactly {repeat_count} repetitions, found {actual}",
                )
            )
    return errors


def validate_document(path: Path) -> list[ValidationError]:
    document, errors = load_json(path)
    if errors:
        return errors
    schema_path = schema_for(path.relative_to(ROOT))
    if schema_path is None:
        return [ValidationError(str(path), "no schema mapping is defined")]
    try:
        validator = SchemaValidator(schema_path)
        errors.extend(validator.validate(document))
    except (OSError, ValueError) as exc:
        errors.append(ValidationError(str(path), f"validator setup failed: {exc}"))
        return errors
    if not errors and isinstance(document, dict):
        relative = path.relative_to(ROOT)
        record_parts = relative.parts[0:2]
        if relative.parts[0:2] == ("evals", "public"):
            errors.extend(validate_eval_invariants(document, path))
        elif relative.parts[0:2] == ("examples", "evaluation-results"):
            errors.extend(validate_evaluation_result_invariants(document, path))
    return errors


def validate_schemas() -> list[ValidationError]:
    errors: list[ValidationError] = []
    found = list(iter_schema_paths())
    if not found:
        return [ValidationError("schemas", "no schema files found")]
    for path in found:
        document, load_errors = load_json(path)
        errors.extend(load_errors)
        if load_errors or not isinstance(document, dict):
            continue
        if document.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(ValidationError(str(path), "must declare the Draft 2020-12 schema URI"))
        if not isinstance(document.get("$id"), str) or not document["$id"]:
            errors.append(ValidationError(str(path), "must declare a non-empty $id"))
        errors.extend(check_schema_refs(document, path))
    return errors


def check_schema_refs(value: Any, schema_path: Path, location: str = "$") -> list[ValidationError]:
    errors: list[ValidationError] = []
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and not ref.startswith("#"):
            raw_path = ref.split("#", 1)[0]
            target = (schema_path.parent / raw_path).resolve()
            if not target.is_file():
                errors.append(ValidationError(str(schema_path), f"{location}: unresolved schema reference {ref!r}"))
        for key, child in value.items():
            errors.extend(check_schema_refs(child, schema_path, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(check_schema_refs(child, schema_path, f"{location}[{index}]"))
    return errors


def validate_invalid_plan_example(path: Path) -> list[ValidationError]:
    """Reject one negative plan example; `validate_plan_markdown` needs the relative path."""
    return validate_plan_markdown(path, path.relative_to(ROOT))


def example_test_plans() -> dict[str, dict[str, Any]]:
    """Test plan entries parsed from examples/test-records for standalone run-example validation."""
    plans: dict[str, dict[str, Any]] = {}
    for plan_path in sorted((ROOT / "examples" / "test-records").glob("plan-*.md")):
        frontmatter, body, load_errors = load_bug_markdown(plan_path)
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
    bug_paths = sorted((ROOT / "examples" / "bug-records").glob("*.md"))
    plan_paths = sorted((ROOT / "examples" / "plans").glob("*.md"))
    result_paths = sorted((ROOT / "examples" / "evaluation-results").glob("*.json"))
    test_paths = sorted((ROOT / "examples" / "test-records").glob("*.md"))
    test_plan_paths = [path for path in test_paths if re.fullmatch(r"plan-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name)]
    test_run_paths = [path for path in test_paths if re.fullmatch(r"run-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name)]
    valid_paths = plan_paths + result_paths
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
        document_errors = validate_plan_markdown(path, path.relative_to(ROOT))
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
    for path in result_paths:
        document_errors = validate_document(path)
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    return errors


def validate_evals() -> list[ValidationError]:
    errors: list[ValidationError] = []
    paths = sorted((ROOT / "evals" / "public").glob("AF-*.json"))
    if not paths:
        return [ValidationError("evals/public", "no public evaluation cases found")]
    case_ids: set[str] = set()
    for path in paths:
        document_errors = validate_document(path)
        if document_errors:
            errors.extend(document_errors)
            continue
        document, load_errors = load_json(path)
        errors.extend(load_errors)
        if isinstance(document, dict):
            case_id = document.get("case_id")
            if case_id in case_ids:
                errors.append(ValidationError(str(path), f"duplicate case_id {case_id!r}"))
            case_ids.add(case_id)
            if path.stem != case_id:
                errors.append(ValidationError(str(path), "filename stem must match case_id"))
    if len(paths) < 10 or len(paths) > 20:
        errors.append(ValidationError("evals/public", f"expected 10-20 public cases, found {len(paths)}"))
    return errors


def relative_to_root(path: Path) -> Path | None:
    """The repository-relative form of `path`, or None when it lies outside the repository."""
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return None


def validate_document_with_schema(path: Path, schema_path: Path) -> list[ValidationError]:
    """Validate one JSON document against an explicit schema file.

    `validate_document` derives the schema from a repository-relative path; this variant
    serves documents outside the repository, such as the temporary fixture directories the
    negative tests use.
    """
    document, errors = load_json(path)
    if errors:
        return errors
    try:
        validator = SchemaValidator(schema_path)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    return validator.validate(document)


def validate_business_seeds(case: dict[str, Any], case_path: Path) -> list[ValidationError]:
    """Check one business case's seed list: location, parseability, declared structure.

    Structure only — the seed doc_refs name paths inside the enterprise snapshot and are not
    resolved here. What is enforced: the seed file is a repository-local file, its case_id
    matches the case, every seed's doc_ref is one of the case's target_docs, every
    strategy.type is one the seed grader implements (an unknown type is fail-closed there, so
    it must not pass validation here), and seed_id values are unique. An empty seed list is an
    answer key with no answers and is rejected.
    """
    errors: list[ValidationError] = []
    case_id = case.get("case_id")
    seeds_ref = case.get("seeds_ref")
    if not isinstance(seeds_ref, str):
        return errors  # the schema check already reported the missing or invalid field
    source = path_inside_root(seeds_ref)
    if source is None or not source.is_file():
        return [ValidationError(str(case_path), f"seeds_ref does not resolve to a file: {seeds_ref!r}")]
    seed_document, load_errors = load_json(source)
    if load_errors:
        return [
            ValidationError(str(case_path), f"seeds_ref {seeds_ref!r}: {error.message}")
            for error in load_errors
        ]
    if not isinstance(seed_document, dict):
        return [ValidationError(str(case_path), f"seeds_ref {seeds_ref!r} must be a JSON object")]
    if seed_document.get("case_id") != case_id:
        errors.append(
            ValidationError(
                str(case_path),
                f"seeds_ref {seeds_ref!r} declares case_id {seed_document.get('case_id')!r}, not {case_id!r}",
            )
        )
    seeds = seed_document.get("seeds")
    if not isinstance(seeds, list) or not seeds:
        errors.append(
            ValidationError(str(case_path), f"seeds_ref {seeds_ref!r} must declare a non-empty seeds array")
        )
        return errors
    target_docs = case.get("target_docs") or []
    seen_seed_ids: set[str] = set()
    for index, seed in enumerate(seeds):
        if not isinstance(seed, dict):
            errors.append(
                ValidationError(str(case_path), f"seeds_ref {seeds_ref!r}: seeds[{index}] must be an object")
            )
            continue
        seed_id = seed.get("seed_id")
        if not isinstance(seed_id, str) or not seed_id:
            errors.append(
                ValidationError(
                    str(case_path), f"seeds_ref {seeds_ref!r}: seeds[{index}] must declare a non-empty seed_id"
                )
            )
        elif seed_id in seen_seed_ids:
            errors.append(
                ValidationError(str(case_path), f"seeds_ref {seeds_ref!r}: duplicate seed_id {seed_id!r}")
            )
        else:
            seen_seed_ids.add(seed_id)
        doc_ref = seed.get("doc_ref")
        if not isinstance(doc_ref, str) or not doc_ref:
            errors.append(
                ValidationError(
                    str(case_path), f"seeds_ref {seeds_ref!r}: seed {seed_id!r} must declare a non-empty doc_ref"
                )
            )
        elif doc_ref not in target_docs:
            errors.append(
                ValidationError(
                    str(case_path),
                    f"seeds_ref {seeds_ref!r}: seed {seed_id!r} doc_ref {doc_ref!r} is not one of "
                    "the case target_docs",
                )
            )
        strategy = seed.get("strategy")
        strategy_type = strategy.get("type") if isinstance(strategy, dict) else None
        if strategy_type not in BUSINESS_SEED_STRATEGY_TYPES:
            errors.append(
                ValidationError(
                    str(case_path),
                    f"seeds_ref {seeds_ref!r}: seed {seed_id!r} declares unknown strategy.type "
                    f"{strategy_type!r}; known types: {', '.join(BUSINESS_SEED_STRATEGY_TYPES)}",
                )
            )
    return errors


def validate_business_evals(directory: Path | None = None) -> list[ValidationError]:
    """Validate the business evaluation slice: case count, case contract, and seed lists.

    The optional `directory` (default evals/business) exists so negative tests and the pinned
    contract tests can validate a fixture copy; a directory outside the repository is still
    validated against the business schema.

    Acceptance mirrors `evals/public`: the filename stem equals the case_id and case_ids are
    unique across the suite. `target_id`/`target_pin`/`target_docs` stay structural — the
    enterprise snapshot is not part of this repository, and the public checks must pass
    without it. `input_ref` and `seeds_ref` resolve inside this repository and are enforced.
    """
    errors: list[ValidationError] = []
    directory = BUSINESS_EVALS_DIR if directory is None else directory
    relative = relative_to_root(directory)
    label = relative.as_posix() if relative is not None else str(directory)
    paths = sorted(directory.glob("BT-*.json"))
    if not paths:
        return [ValidationError(label, "no business evaluation cases found")]
    minimum, maximum = BUSINESS_CASE_COUNT_RANGE
    if len(paths) < minimum or len(paths) > maximum:
        errors.append(ValidationError(label, f"expected {minimum}-{maximum} business cases, found {len(paths)}"))
    case_ids: set[str] = set()
    for path in paths:
        if relative_to_root(path) is not None:
            case_errors = validate_document(path)
        else:
            case_errors = validate_document_with_schema(path, BUSINESS_CASE_SCHEMA)
        if case_errors:
            errors.extend(case_errors)
            continue
        document, load_errors = load_json(path)
        errors.extend(load_errors)
        if not isinstance(document, dict):
            continue
        case_id = document.get("case_id")
        if case_id in case_ids:
            errors.append(ValidationError(str(path), f"duplicate case_id {case_id!r}"))
        case_ids.add(case_id)
        if path.stem != case_id:
            errors.append(ValidationError(str(path), "filename stem must match case_id"))
        input_ref = document.get("input_ref")
        if isinstance(input_ref, str):
            resolved = path_inside_root(input_ref)
            if resolved is None or not resolved.is_file():
                errors.append(ValidationError(str(path), f"input_ref does not resolve to a file: {input_ref!r}"))
        errors.extend(validate_business_seeds(document, path))
    return errors


def validate_evals_suite() -> list[ValidationError]:
    """Public cases plus the business slice, reported under the single `evals` row."""
    return validate_evals() + validate_business_evals()


# The improvement loop's JSON handoff plane (records/improvement/): each subtree has its own
# schema and its own identity rule, compiled by validate_workspace_artifacts. The schema split
# is deliberate — schemas/ holds the deterministic tool-output contracts (evaluation result,
# comparison), skills/improve/references/ holds the improve-loop rulebook contracts (candidate,
# release record) — see records/improvement/README.md.
EVALUATION_RESULT_SCHEMA = ROOT / "schemas" / "evaluation-result.schema.json"
COMPARISON_SCHEMA = ROOT / "schemas" / "comparison.schema.json"
CANDIDATE_SCHEMA = ROOT / "skills" / "improve" / "references" / "candidate.schema.json"
RELEASE_RECORD_SCHEMA = ROOT / "skills" / "improve" / "references" / "release-record.schema.json"
IMPROVEMENT_SCHEMA_BY_SUBTREE = {
    "candidates": CANDIDATE_SCHEMA,
    "evaluations": EVALUATION_RESULT_SCHEMA,
    "comparisons": COMPARISON_SCHEMA,
    "releases": RELEASE_RECORD_SCHEMA,
}
# The seven execution-context fields the runner compares on (eval_runner.py compare) and that
# every improvement cross-check treats as one unit.
COMPARISON_CONTEXT_FIELDS = (
    "suite_revision",
    "host",
    "model",
    "permissions_profile",
    "fixture_revision",
    "repeat_count",
    "suite_case_count",
)

# Every path under records/ is a stray file or an unknown subdirectory and must fail the
# artifacts check explicitly instead of falling through the parts[0:2] dispatch silently.
KNOWN_RECORD_CLASSES = ("bugs", "episodes", "reviews", "plans", "improvement", "tests")


def validate_improvement_document(
    path: Path, subtree: str
) -> tuple[dict[str, Any] | None, list[ValidationError]]:
    """Validate one JSON artifact under records/improvement/<subtree>/ against its own schema.

    Improvement artifacts are exchanged between loop roles, so identity is the filename: a
    candidate record's stem must equal its ``candidate_version`` and an evaluation result's
    stem must equal its ``result_id`` (a release record's embedded candidate and a comparison
    have no file identity of their own). Evaluation results additionally reuse the evaluation
    invariants. Returns the parsed document so the caller can collect it for the
    cross-document pass; ``None`` means the document could not be read or parsed at all.
    """
    document, load_errors = load_json(path)
    if load_errors or not isinstance(document, dict):
        return None, load_errors or [
            ValidationError(str(path), f"{subtree} artifact is not a JSON object")
        ]
    try:
        validator = SchemaValidator(IMPROVEMENT_SCHEMA_BY_SUBTREE[subtree])
    except (OSError, ValueError) as exc:
        return None, [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors = validator.validate(document)
    if errors:
        return document, errors
    if subtree == "candidates":
        expected = document.get("candidate_version")
        if path.stem != expected:
            errors.append(
                ValidationError(str(path), f"filename stem must equal candidate_version {expected!r}")
            )
    elif subtree == "evaluations":
        expected = document.get("result_id")
        if path.stem != expected:
            errors.append(
                ValidationError(str(path), f"filename stem must equal result_id {expected!r}")
            )
        errors.extend(validate_evaluation_result_invariants(document, path))
    return document, errors


def validate_improvement_cross_references(
    candidates: dict[str, tuple[Path, dict[str, Any]]],
    results: dict[str, tuple[Path, dict[str, Any]]],
    comparisons: list[tuple[Path, dict[str, Any]]],
    releases: list[tuple[Path, dict[str, Any]]],
    seen_episode_ids: dict[str, Path],
    seen_bug_ids: dict[str, Path],
) -> list[ValidationError]:
    """Second pass over the collected improvement artifacts: every claim one record makes
    about another must resolve.

    Checked here, not per file, because the rglob pass is single-shot and sorted — a
    comparison may reference a result collected later in the same pass. ``rollback_to`` is
    deliberately unchecked: it names a release pointer, not a record in this tree.
    """
    errors: list[ValidationError] = []
    comparison_pairs: set[tuple[str, str]] = set()
    for path, comparison in comparisons:
        pair = (comparison["baseline_result_id"], comparison["candidate_result_id"])
        comparison_pairs.add(pair)
        for role, result_id in (("baseline", pair[0]), ("candidate", pair[1])):
            entry = results.get(result_id)
            if entry is None:
                errors.append(
                    ValidationError(
                        str(path),
                        f"{role}_result_id {result_id!r} does not resolve to an evaluation "
                        "result under records/improvement/evaluations/",
                    )
                )
                continue
            result_document = entry[1]
            expected_kind = role  # baseline result carries source_kind "baseline", etc.
            actual_kind = result_document.get("source_kind")
            if actual_kind != expected_kind:
                errors.append(
                    ValidationError(
                        str(path),
                        f"{role}_result_id {result_id!r} points at a result whose source_kind "
                        f"is {actual_kind!r}, not {expected_kind!r}",
                    )
                )
            for field in COMPARISON_CONTEXT_FIELDS:
                if result_document.get(field) != comparison["context"].get(field):
                    errors.append(
                        ValidationError(
                            str(path),
                            f"context.{field} does not match the {role} result {result_id!r} "
                            f"({comparison['context'].get(field)!r} vs {result_document.get(field)!r})",
                        )
                    )
    for path, release in releases:
        embedded = release.get("candidate")
        version = embedded.get("candidate_version") if isinstance(embedded, dict) else None
        candidate_entry = candidates.get(version) if isinstance(version, str) else None
        if candidate_entry is None:
            errors.append(
                ValidationError(
                    str(path),
                    f"embedded candidate_version {version!r} does not resolve to a candidate "
                    "record under records/improvement/candidates/",
                )
            )
        else:
            candidate_path = candidate_entry[0]
            file_document, load_errors = load_json(candidate_path)
            if load_errors or not isinstance(file_document, dict):
                errors.append(
                    ValidationError(
                        str(path),
                        f"candidate record {candidate_path.name} could not be re-read for the "
                        "equality check",
                    )
                )
            elif json_equal_key(file_document) != json_equal_key(embedded):
                errors.append(
                    ValidationError(
                        str(path),
                        f"embedded candidate object is not JSON-equal to candidate record "
                        f"{candidate_path.name}",
                    )
                )
        referenced: dict[str, str] = {}
        for role in ("baseline_results", "candidate_results"):
            entry = release.get(role)
            result_id = entry.get("result_id") if isinstance(entry, dict) else None
            referenced[role] = result_id if isinstance(result_id, str) else ""
            if isinstance(result_id, str) and result_id not in results:
                errors.append(
                    ValidationError(
                        str(path),
                        f"{role}.result_id {result_id!r} does not resolve to an evaluation "
                        "result under records/improvement/evaluations/",
                    )
                )
        pair = (referenced["baseline_results"], referenced["candidate_results"])
        if pair not in comparison_pairs:
            errors.append(
                ValidationError(
                    str(path),
                    "no comparison under records/improvement/comparisons/ matches this "
                    f"release's result pair ({pair[0]!r}, {pair[1]!r})",
                )
            )
    for version, (candidate_path, document) in candidates.items():
        for evidence_id in document.get("evidence_ids") or []:
            if not isinstance(evidence_id, str):
                continue
            if evidence_id.startswith("EP-"):
                pool, location = seen_episode_ids, "records/episodes/"
            elif evidence_id.startswith("BUG-"):
                pool, location = seen_bug_ids, "records/bugs/"
            else:
                continue  # other evidence shapes are outside this tree's resolver
            if evidence_id not in pool:
                errors.append(
                    ValidationError(
                        str(candidate_path),
                        f"evidence_ids entry {evidence_id!r} does not resolve to an existing "
                        f"record under {location}",
                    )
                )
    return errors


def validate_workspace_artifacts() -> list[ValidationError]:
    """Validate record instances under records/ (Markdown bug records, JSON plans)."""
    errors: list[ValidationError] = []
    records_root = ROOT / "records"
    if not records_root.is_dir():
        return [ValidationError(str(records_root), "records directory is missing; artifacts are required")]
    seen_bug_ids: dict[str, Path] = {}
    seen_review_ids: dict[str, Path] = {}
    seen_episode_ids: dict[str, Path] = {}
    record_versions: dict[str, str] = {}
    ledgers: dict[str, dict[str, Any]] = {}
    class_records: list[tuple[str, Any, str, Path]] = []
    review_findings: list[tuple[list, Path]] = []
    seen_test_plan_ids: dict[str, Path] = {}
    seen_test_run_ids: dict[str, Path] = {}
    test_plans: dict[str, dict[str, Any]] = {}
    deferred_test_runs: list[tuple[Path, Path]] = []
    improvement_candidates: dict[str, tuple[Path, dict[str, Any]]] = {}
    improvement_results: dict[str, tuple[Path, dict[str, Any]]] = {}
    improvement_comparisons: list[tuple[Path, dict[str, Any]]] = []
    improvement_releases: list[tuple[Path, dict[str, Any]]] = []
    if not any(path for path in records_root.iterdir() if not path.name.startswith(".")):
        errors.append(ValidationError(str(records_root), "records directory is empty; artifacts are required"))
    for path in sorted(records_root.rglob("*")):
        relative = path.relative_to(ROOT)
        parts = relative.parts
        if any(part.startswith(".") for part in parts[1:]):
            if path.name == ".DS_Store":
                continue
            errors.append(ValidationError(str(path), "hidden record entry is not allowed"))
            continue
        if len(parts) < 2 or parts[1] not in KNOWN_RECORD_CLASSES:
            # A stray file at the top of records/ or an unknown subdirectory used to fall
            # through the parts[0:2] dispatch without any check; report it by path instead.
            if len(parts) == 2 and path.is_file() and path.name == "README.md":
                continue  # the top-level records/README.md documents the record classes
            errors.append(
                ValidationError(
                    str(path),
                    "unexpected entry under records/; record classes are bugs/, episodes/, "
                    "reviews/, plans/, improvement/, and tests/ (plus records/README.md)",
                )
            )
            continue
        if not path.is_file():
            continue
        if parts[0:2] == ("records", "bugs"):
            if path.name == "README.md":
                continue
            if parts[2:3] == (RECURRENCE_DIR,):
                if path.suffix != ".md":
                    errors.append(
                        ValidationError(str(path), "recurrence ledgers are Markdown files; unexpected non-md file")
                    )
                    continue
                ledger_errors = validate_recurrence_markdown(path)
                errors.extend(ledger_errors)
                if ledger_errors:
                    continue
                frontmatter, _, _ = load_bug_markdown(path)
                class_id = frontmatter.get("class_id") if frontmatter else None
                if isinstance(class_id, str):
                    if class_id in ledgers:
                        errors.append(
                            ValidationError(str(path), f"duplicate class_id {class_id!r} already declared in {ledgers[class_id]['path']}")
                        )
                    else:
                        ledgers[class_id] = {"path": path, "frontmatter": frontmatter}
                continue
            if path.suffix != ".md":
                errors.append(ValidationError(str(path), "bug records are Markdown files; unexpected non-md file"))
                continue
            frontmatter, body, load_errors = load_bug_markdown(path)
            if load_errors or frontmatter is None:
                errors.extend(load_errors)
                continue
            errors.extend(validate_bug_markdown(path))
            errors.extend(validate_bug_layout(frontmatter, path, relative, seen_bug_ids))
            errors.extend(validate_external_excerpts(frontmatter, body, path))
            errors.extend(validate_body_references(body, path))
            for entry in frontmatter.get("files") or []:
                # Self-contained evidence: a reference either resolves inside this repository
                # or is explicitly repo-qualified (<repo>@<revision>:<path>) — a bare path that
                # exists nowhere dangles for anyone who receives the records without the
                # other repository.
                if not isinstance(entry, str):
                    continue
                head, sep, _ = entry.partition(":")
                if sep and "@" in head:
                    continue
                if not (ROOT / entry).is_file():
                    errors.append(
                        ValidationError(
                            str(path),
                            f"files entry {entry!r} exists neither in this repository nor as a "
                            "repo-qualified reference (<repo>@<revision>:<path>)",
                        )
                    )
            status = frontmatter.get("status")
            if parts[2:3] == (BUG_ARCHIVE_DIR,):
                if status != "rejected":
                    errors.append(
                        ValidationError(str(path), "only rejected records may be archived; verified records stay in place")
                    )
            elif status == "rejected":
                errors.append(
                    ValidationError(str(path), "a rejected record must be moved into records/bugs/archive/")
                )
            bug_id = frontmatter.get("bug_id")
            version = frontmatter.get("agentflow_version")
            if isinstance(bug_id, str) and isinstance(version, str):
                record_versions[bug_id] = version
            class_id = frontmatter.get("class_id")
            if isinstance(class_id, str):
                class_records.append((class_id, frontmatter.get("occurrence"), str(bug_id or ""), path))
        elif parts[0:2] == ("records", "episodes"):
            if path.name == "README.md":
                continue
            if path.suffix != ".json":
                errors.append(ValidationError(str(path), "episode records are JSON files; unexpected non-json file"))
                continue
            episode_errors = validate_episode_document(path)
            errors.extend(episode_errors)
            if episode_errors:
                continue
            document, _ = load_json(path)
            episode_id = document.get("episode_id") if isinstance(document, dict) else None
            if isinstance(episode_id, str):
                if episode_id in seen_episode_ids:
                    errors.append(
                        ValidationError(str(path), f"duplicate episode_id {episode_id!r} already declared in {seen_episode_ids[episode_id]}")
                    )
                else:
                    seen_episode_ids[episode_id] = path
        elif parts[0:2] == ("records", "reviews"):
            if len(parts) != 4 or not re.fullmatch(
                r"review-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name
            ):
                # Only feature-directory-level review-*.md files are records; README, archived
                # evidence copies, and anything nested deeper (archive/...) are not.
                continue
            review_errors = validate_review_markdown(path, relative, seen_review_ids)
            errors.extend(review_errors)
            if review_errors:
                continue
            frontmatter, _, _ = load_bug_markdown(path)
            if frontmatter:
                review_findings.append((frontmatter.get("findings") or [], path))
        elif parts[0:2] == ("records", "tests"):
            if path.name == "README.md":
                continue
            if len(parts) != 4 or not path.is_file():
                # Evidence files and other non-record artifacts (e.g. evidence/<run-id>/…)
                # are exempt, like the review archive snapshots.
                continue
            if re.fullmatch(r"plan-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name):
                plan_errors, entry = validate_test_plan_markdown(path, relative, seen_test_plan_ids)
                errors.extend(plan_errors)
                if entry is not None:
                    test_plans[entry["frontmatter"]["test_plan_id"]] = entry
            elif re.fullmatch(r"run-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name):
                # Deferred: the referenced plan may be validated later in the same sorted pass.
                deferred_test_runs.append((path, relative))
            else:
                errors.append(
                    ValidationError(
                        str(path),
                        "unexpected file in a records/tests/ feature directory; records are "
                        "plan-*.md and run-*.md (plus README.md and evidence/ subdirectories) "
                        "— see records/tests/README.md",
                    )
                )
        elif parts[0:2] == ("records", "plans"):
            if path.name == "README.md":
                continue
            if path.suffix != ".md":
                errors.append(ValidationError(str(path), "plans are Markdown files; unexpected non-md file"))
                continue
            errors.extend(validate_plan_markdown(path, relative))
        elif parts[0:2] == ("records", "improvement"):
            if path.name == "README.md":
                continue  # the subtree README documents the artifact contracts
            if len(parts) != 4 or parts[2] not in IMPROVEMENT_SCHEMA_BY_SUBTREE:
                errors.append(
                    ValidationError(
                        str(path),
                        "unexpected entry under records/improvement/; artifacts live directly "
                        "in candidates/, evaluations/, comparisons/, or releases/ (plus "
                        "README.md) — see records/improvement/README.md",
                    )
                )
                continue
            if path.suffix != ".json":
                errors.append(
                    ValidationError(str(path), f"{parts[2]} artifacts are JSON files; unexpected non-json file")
                )
                continue
            document, artifact_errors = validate_improvement_document(path, parts[2])
            errors.extend(artifact_errors)
            if document is None or artifact_errors:
                continue
            if parts[2] == "candidates":
                version = document["candidate_version"]
                if version in improvement_candidates:
                    errors.append(
                        ValidationError(
                            str(path),
                            f"duplicate candidate_version {version!r} already declared in "
                            f"{improvement_candidates[version][0]}",
                        )
                    )
                else:
                    improvement_candidates[version] = (path, document)
            elif parts[2] == "evaluations":
                result_id = document["result_id"]
                if result_id in improvement_results:
                    errors.append(
                        ValidationError(
                            str(path),
                            f"duplicate result_id {result_id!r} already declared in "
                            f"{improvement_results[result_id][0]}",
                        )
                    )
                else:
                    improvement_results[result_id] = (path, document)
            elif parts[2] == "comparisons":
                pair = (document["baseline_result_id"], document["candidate_result_id"])
                if pair in {(c["baseline_result_id"], c["candidate_result_id"]) for _, c in improvement_comparisons}:
                    errors.append(
                        ValidationError(
                            str(path),
                            f"duplicate comparison result pair ({pair[0]!r}, {pair[1]!r})",
                        )
                    )
                else:
                    improvement_comparisons.append((path, document))
            elif parts[2] == "releases":
                improvement_releases.append((path, document))

    # Cross-check recurrence ledgers against the records they claim.
    for class_id, entry in ledgers.items():
        ledger_path = entry["path"]
        frontmatter = entry["frontmatter"]
        first_record = frontmatter.get("first_record")
        occurrences = frontmatter.get("occurrences") or []
        for bug_id in [first_record, *occurrences]:
            if isinstance(bug_id, str) and bug_id not in seen_bug_ids:
                errors.append(
                    ValidationError(str(ledger_path), f"references unknown bug_id {bug_id!r}")
                )
        if frontmatter.get("status") == "consolidated":
            for bug_id in occurrences:
                if isinstance(bug_id, str) and bug_id in seen_bug_ids and bug_id not in record_versions:
                    errors.append(
                        ValidationError(
                            str(ledger_path),
                            f"occurrence {bug_id!r} of a consolidated class must carry agentflow_version "
                            "so it can be placed before or after the consolidation",
                        )
                    )
    used_occurrences: dict[str, dict[str, Path]] = {}
    for class_id, occurrence, bug_id, path in class_records:
        if class_id not in ledgers:
            errors.append(
                ValidationError(str(path), f"class_id {class_id!r} has no ledger under records/bugs/recurrence/")
            )
            continue
        if not (isinstance(occurrence, str) and occurrence.isdigit() and int(occurrence) >= 1):
            errors.append(
                ValidationError(str(path), "a record with class_id must declare occurrence as a positive digit string")
            )
            continue
        if occurrence in used_occurrences.setdefault(class_id, {}):
            errors.append(
                ValidationError(
                    str(path),
                    f"occurrence {occurrence} of class {class_id!r} is already used by {used_occurrences[class_id][occurrence]}",
                )
            )
        used_occurrences[class_id][occurrence] = path
        listed = ledgers[class_id]["frontmatter"].get("occurrences") or []
        if bug_id not in listed:
            errors.append(
                ValidationError(str(path), f"bug_id {bug_id!r} is not listed in ledger {class_id!r}")
            )
    for findings, review_path in review_findings:
        for bug_id in findings:
            if isinstance(bug_id, str) and bug_id not in seen_bug_ids:
                errors.append(
                    ValidationError(str(review_path), f"review findings reference unknown bug_id {bug_id!r}")
                )
    for run_path, run_relative in deferred_test_runs:
        run_errors, run_findings, run_flow_findings = validate_test_run_markdown(
            run_path, run_relative, seen_test_run_ids, test_plans
        )
        errors.extend(run_errors)
        for bug_id in run_findings:
            if bug_id not in seen_bug_ids:
                errors.append(
                    ValidationError(str(run_path), f"run findings reference unknown bug_id {bug_id!r}")
                )
        for bug_id in run_flow_findings:
            if bug_id not in seen_bug_ids:
                errors.append(
                    ValidationError(str(run_path), f"run flow_findings reference unknown bug_id {bug_id!r}")
                )
    # Cross-check the improvement artifacts against each other (second pass — a comparison may
    # reference a result collected later in the same sorted rglob pass).
    errors.extend(
        validate_improvement_cross_references(
            improvement_candidates,
            improvement_results,
            improvement_comparisons,
            improvement_releases,
            seen_episode_ids,
            seen_bug_ids,
        )
    )
    return errors


ROLE_NAME_PATTERN = re.compile(r"^name:\s*([a-z0-9-]+)\s*$", re.M)
SKILL_ROLE_PATTERN = re.compile(r"agentflow:([a-z0-9-]+)")

# 0.5.0 switched plans from JSON to Markdown hybrids (records/plans/README.md); either
# stale marker in AGENTS.md signals the pre-0.5.0 contract and must fail the docs check.
PRE_050_PLAN_CONTRACT_MARKERS = ("plans are JSON", "<plan_id>.json")


def validate_agents_md_plan_contract(agents_md: Path) -> list[ValidationError]:
    """Tripwire: AGENTS.md must not carry the pre-0.5.0 JSON plan contract wording."""
    errors: list[ValidationError] = []
    text, read_errors = read_document_text(agents_md)
    if read_errors:
        return read_errors
    if any(marker in text for marker in PRE_050_PLAN_CONTRACT_MARKERS):
        errors.append(
            ValidationError(
                str(agents_md),
                "AGENTS.md carries the pre-0.5.0 JSON plan contract; plans are Markdown "
                "hybrids named <plan_id>.md — see records/plans/README.md",
            )
        )
    return errors


# Files whose prose states the plugin's current maturity. Version literals there drift on
# every bump (the 0.6.0 → 0.7.4 → 0.7.5 hand-sync family); the version lives in the five
# manifests and CHANGELOG, and these files must point at it instead of restating it.
VERSION_PROSE_FILES = (
    "README.md",
    "docs/host-native-plugin-design.md",
    "docs/self-improvement-design.md",
    "docs/agent-product-boundary.md",
)
VERSION_LITERAL_PATTERN = re.compile(r"\bv?\d+\.\d+\.\d+\b")


def validate_doc_consistency() -> list[ValidationError]:
    """Cross-check the hand-synced role/document surface (the 0.3.3 manifest-drift family).

    The role/doc surface is synced by hand across twelve agent files, two SKILLs, the roles
    reference, the records READMEs, and the root AGENTS.md — the same failure class as the
    missed manifest bump. Five assertion groups: every agent file's frontmatter name equals
    its filename; every `agentflow:<role>` referenced by a SKILL resolves to an agent file;
    every `schemas/*.schema.json` path named anywhere in the docs/records/skills/agents
    surface or in AGENTS.md exists; AGENTS.md carries no pre-0.5.0 JSON plan contract
    markers; the Chinese mirror keeps section parity with its English contract documents.
    """
    errors: list[ValidationError] = []
    agents_dir = ROOT / "agents"
    agent_files = {p.stem: p for p in sorted(agents_dir.glob("*.md"))}
    for name, path in agent_files.items():
        text, read_errors = read_document_text(path)
        if read_errors:
            errors.extend(read_errors)
            continue
        m = ROLE_NAME_PATTERN.search(text)
        if not m:
            errors.append(ValidationError(str(path), "agent file frontmatter lacks a name field"))
        elif m.group(1) != name:
            errors.append(
                ValidationError(str(path), f"frontmatter name {m.group(1)!r} does not match filename {name!r}")
            )

    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text, read_errors = read_document_text(skill)
        if read_errors:
            errors.extend(read_errors)
            continue
        for role in sorted(set(SKILL_ROLE_PATTERN.findall(text))):
            if role not in agent_files:
                errors.append(
                    ValidationError(str(skill), f"references agentflow:{role!r} but agents/{role}.md does not exist")
                )

    reference_surface = [
        ROOT / "docs",
        ROOT / "records",
        ROOT / "skills",
        ROOT / "agents",
        ROOT / "README.md",
        ROOT / "AGENTS.md",
    ]
    schema_ref_pattern = re.compile(r"schemas/([a-z0-9-]+\.schema\.json)")
    schema_dir = ROOT / "schemas"
    for base in reference_surface:
        files = base.rglob("*.md") if base.is_dir() else [base]
        for doc in sorted(files):
            text, read_errors = read_document_text(doc)
            if read_errors:
                errors.extend(read_errors)
                continue
            for schema in schema_ref_pattern.findall(text):
                if not (schema_dir / schema).is_file():
                    errors.append(
                        ValidationError(str(doc), f"references schemas/{schema!r} which does not exist")
                    )

    errors.extend(validate_agents_md_plan_contract(ROOT / "AGENTS.md"))

    # Version-in-prose guard: the current-version claims in these files were hand-synced
    # at every bump and drifted more than once (0.6.0 was still being declared after
    # 0.7.4 shipped). The manifests own the version; these files must reference it.
    for name in VERSION_PROSE_FILES:
        path = ROOT / name
        text, read_errors = read_document_text(path)
        if read_errors:
            errors.extend(read_errors)
            continue
        for match in VERSION_LITERAL_PATTERN.finditer(text):
            context = text[max(0, match.start() - 40) : match.end() + 40].replace("\n", " ")
            errors.append(
                ValidationError(
                    str(path),
                    f"version literal {match.group(0)!r} in prose ({context.strip()!r}); state "
                    "the version only in the manifests and CHANGELOG and reference them here",
                )
            )

    zh = ROOT / "docs" / "agent-roles.md"
    zh_text, zh_errors = read_document_text(zh)
    errors.extend(zh_errors)
    contracts = ROOT / "skills" / "agentflow" / "references" / "contracts.md"
    contracts_text, contracts_errors = read_document_text(contracts)
    errors.extend(contracts_errors)
    if zh_errors or contracts_errors:
        return errors
    zh_schemas = set(schema_ref_pattern.findall(zh_text))
    contracts_schemas = set(schema_ref_pattern.findall(contracts_text))
    if zh_schemas != contracts_schemas:
        only_zh = zh_schemas - contracts_schemas
        only_en = contracts_schemas - zh_schemas
        errors.append(
            ValidationError(
                str(zh),
                f"schema references diverge from {contracts.name}: zh-only={sorted(only_zh)}, en-only={sorted(only_en)}",
            )
        )
    return errors


def validate_mock_fixtures() -> list[ValidationError]:
    """Compile mock/ demo records by merging them into a throwaway repository copy.

    mock/README.md declares the fixtures as validated demo material that must stay in
    sync with the record contracts. Until 0.8.0 nothing enforced that: no check walked
    mock/, so a contract change could silently invalidate every fixture. This check
    performs exactly the merge the README describes — the repository tree is copied to a
    temporary directory (never mutated in place), mock/records is overlaid onto the
    copy's records/, and the full artifacts compile runs against the copy, where ROOT
    resolves to the copy. A fixture that no longer compiles, an id that collides with a
    real record, or a cross-reference the demo ledger declares but cannot satisfy now
    fails the gate instead of surviving until someone re-runs the manual experiment.
    """
    errors: list[ValidationError] = []
    mock_root = ROOT / "mock"
    mock_records = mock_root / "records"
    if not mock_records.is_dir():
        return [ValidationError(str(mock_records), "mock records directory is missing")]
    errors.extend(
        ValidationError(
            f"mock/{entry.name}",
            "unexpected entry under mock/; declared contents are records/ and README.md",
        )
        for entry in sorted(mock_root.iterdir())
        if entry.name not in {"records", "README.md"}
    )
    try:
        with tempfile.TemporaryDirectory(prefix="agentflow-mock-") as tmp:
            copy_root = Path(tmp) / "repo"
            shutil.copytree(
                ROOT,
                copy_root,
                # .git can be orders of magnitude larger than the tree itself; caches and
                # the disposable record-store database are regenerated artifacts.
                ignore=shutil.ignore_patterns(".git", "__pycache__", ".agentflow-records.sqlite3*"),
            )
            shutil.copytree(mock_records, copy_root / "records", dirs_exist_ok=True)
            completed = subprocess.run(
                [sys.executable, str(copy_root / "tools" / "lab" / "validate.py"), "artifacts"],
                cwd=str(copy_root),
                text=True,
                capture_output=True,
                timeout=600,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            if completed.returncode != 0:
                output = (completed.stderr.strip() or completed.stdout.strip())[:2000]
                errors.append(
                    ValidationError(
                        "mock",
                        "mock fixtures failed the merged-record compile: "
                        + (output or f"exit {completed.returncode}"),
                    )
                )
    except (OSError, subprocess.SubprocessError) as exc:
        errors.append(ValidationError("mock", f"cannot compile merged mock records: {exc}"))
    return errors


def load_protected_paths(path: Path) -> tuple[list[str], list[ValidationError]]:
    """Read protected-paths.txt: one repository-relative prefix per line."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [], [ValidationError(str(path), f"cannot read protected path list: {exc}")]
    entries: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        if entry.startswith("/") or ".." in Path(entry).parts:
            return [], [ValidationError(str(path), f"line {number}: must be a repository-relative path")]
        entries.append(entry)
    if not entries:
        return [], [ValidationError(str(path), "the protected path list is empty")]
    return entries, []


def validate_protected_paths(list_path: Path | None = None) -> list[ValidationError]:
    """Check the declared candidate gate surface still covers the required entries.

    `list_path` defaults to the repository's protected-paths.txt; the negative contract tests
    point it at a shrunken fixture copy so a lost required entry is exercised in-process.
    """
    errors: list[ValidationError] = []
    list_path = PROTECTED_PATHS_FILE if list_path is None else list_path
    if not list_path.is_file():
        return [ValidationError(str(list_path), "the protected path list is missing")]
    entries, load_errors = load_protected_paths(list_path)
    if load_errors:
        return load_errors
    normalized = {entry.strip("/") for entry in entries}
    for required in sorted(REQUIRED_PROTECTED_PATHS):
        covered = any(entry == required or required.startswith(entry + "/") for entry in normalized)
        if not covered:
            errors.append(
                ValidationError(
                    str(list_path),
                    f"required gate path {required!r} is no longer covered by any declared prefix",
                )
            )
    return errors


def manifest_value(
    name: str, pointer: tuple[Any, ...], root: Path = ROOT
) -> tuple[str | None, list[ValidationError]]:
    """Read a nested manifest value by pointer, e.g. ("plugins", 0, "version").

    `root` defaults to the repository; the negative contract tests point it at a fixture copy.
    """
    path = root / name
    if not path.is_file():
        return None, [ValidationError(name, "manifest is missing")]
    document, load_errors = load_json(path)
    if load_errors:
        return None, load_errors
    value: Any = document
    for part in pointer:
        if isinstance(part, int):
            if not isinstance(value, list) or len(value) <= part:
                return None, [ValidationError(name, f"manifest has no {'.'.join(map(str, pointer))!s}")]
            value = value[part]
        else:
            if not isinstance(value, dict) or part not in value:
                return None, [ValidationError(name, f"manifest has no {'.'.join(map(str, pointer))!s}")]
            value = value[part]
    if not isinstance(value, dict):
        return None, [ValidationError(name, "manifest entry must be an object")]
    return value, []


def validate_manifests(root: Path = ROOT) -> list[ValidationError]:
    """Require the hand-synced manifests to agree on the plugin name and version.

    `root` defaults to the repository; the negative contract tests point it at a fixture copy
    of the five manifests so a version divergence is exercised in-process.
    """
    errors: list[ValidationError] = []
    names: dict[str, str] = {}
    versions: dict[str, str] = {}
    for name, pointer in MANIFEST_POINTERS:
        entry, entry_errors = manifest_value(name, pointer, root)
        if entry_errors:
            errors.extend(entry_errors)
            continue
        version = entry.get("version")
        if not isinstance(version, str) or not version:
            errors.append(ValidationError(name, "manifest is missing a version string"))
        else:
            versions[name] = version
        plugin_name = entry.get("name")
        if not isinstance(plugin_name, str) or not plugin_name:
            errors.append(ValidationError(name, "manifest is missing a name string"))
        else:
            names[name] = plugin_name
    if len(set(versions.values())) > 1:
        reference = versions.get("plugin.json")
        for name, version in sorted(versions.items()):
            if version != reference:
                errors.append(
                    ValidationError(name, f"version {version!r} disagrees with plugin.json {reference!r}")
                )
    if len(set(names.values())) > 1:
        reference = names.get("plugin.json")
        for name, plugin_name in sorted(names.items()):
            if plugin_name != reference:
                errors.append(
                    ValidationError(name, f"name {plugin_name!r} disagrees with plugin.json {reference!r}")
                )
    return errors


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
        if entry.name in allowed:
            continue
        errors.append(
            ValidationError(
                f"tests/{entry.name}",
                "unexpected entry in the test directory; declare it here and in protected-paths.txt",
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


def plugin_identity() -> tuple[str, str, str] | None:
    """Return (marketplace, plugin, version) for the source checkout, when declared."""
    manifest, load_errors = load_json(ROOT / "plugin.json")
    if load_errors or not isinstance(manifest, dict):
        return None
    marketplace, marketplace_errors = load_json(ROOT / "marketplace.json")
    if marketplace_errors or not isinstance(marketplace, dict):
        return None
    name = manifest.get("name")
    version = manifest.get("version")
    market_name = marketplace.get("name")
    if not all(isinstance(value, str) and value for value in (name, version, market_name)):
        return None
    return market_name, name, version


def component_manifest(root: Path) -> tuple[dict[str, dict[str, object]], list[ValidationError]]:
    """Build a path-keyed manifest for the components that decide installed behavior."""
    manifest: dict[str, dict[str, object]] = {}
    errors: list[ValidationError] = []
    for component in INSTALLED_COMPONENTS:
        directory = root / component
        if not directory.is_dir():
            continue
        try:
            entries = artifact_digest.build_manifest(directory, set(artifact_digest.DEFAULT_EXCLUDES))
        except (OSError, ValueError) as exc:
            errors.append(ValidationError(str(directory), f"cannot read installed component: {exc}"))
            continue
        for entry in entries:
            manifest[f"{component}/{entry['path']}"] = entry
    for name in INSTALLED_FILES:
        path = root / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        manifest[name] = {
            "path": name,
            "mode": format(path.stat().st_mode & 0o7777, "04o"),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    return manifest, errors


def installed_plugin_roots() -> tuple[Path | None, list[Path], list[ValidationError]]:
    """Locate a ZCode local-directory install of this plugin, if one exists."""
    identity = plugin_identity()
    if identity is None:
        return None, [], [ValidationError("plugin.json", "cannot read plugin name/version for an install check")]
    marketplace, name, version = identity
    cache_root = Path.home() / ".zcode" / "cli" / "plugins" / "cache" / marketplace / name
    if not cache_root.is_dir():
        return None, [], []
    versions = sorted(path for path in cache_root.iterdir() if path.is_dir())
    for candidate in versions:
        if candidate.name == version:
            return candidate, versions, []
    return None, versions, []


def validate_installed(path_value: str | None) -> tuple[str, list[ValidationError]]:
    """Compare the runtime components of the source checkout with an installed snapshot.

    Returns ("pass" | "fail" | "skip", errors). The check stays out of `all` because it reads
    outside the repository: a clone or a candidate worktree with no local install must not fail
    repository validation. Run it before any dogfood run and after changing `agents/` or
    `skills/`, where the host loads the installed snapshot rather than the working tree.
    """
    errors: list[ValidationError] = []
    identity = plugin_identity()
    if path_value:
        installed_root = Path(path_value).expanduser().resolve()
        if not installed_root.is_dir():
            return "fail", [ValidationError(str(installed_root), "installed plugin path does not exist")]
        versions: list[Path] = []
    else:
        if identity is None:
            return "fail", [ValidationError("plugin.json", "cannot read plugin identity for an install check")]
        installed_root, versions, locate_errors = installed_plugin_roots()
        if locate_errors:
            return "fail", locate_errors
        if installed_root is None:
            if versions:
                marketplace, name, version = identity
                return "fail", [
                    ValidationError(
                        f"~/.zcode/cli/plugins/cache/{marketplace}/{name}",
                        "no snapshot for source version "
                        f"{version}; installed versions: {', '.join(item.name for item in versions)}."
                        " Refresh the marketplace and reinstall — source edits do not reach the"
                        " installed copy, so role behavior still comes from the stale snapshot.",
                    )
                ]
            return "skip", []

    source_manifest, source_errors = component_manifest(ROOT)
    if source_errors:
        return "fail", source_errors
    installed_manifest, installed_errors = component_manifest(installed_root)
    if installed_errors:
        return "fail", installed_errors

    if not installed_manifest:
        errors.append(
            ValidationError(str(installed_root), "no plugin components found in the installed copy")
        )
        return "fail", errors

    for path in sorted(set(source_manifest) - set(installed_manifest)):
        errors.append(ValidationError(path, f"missing from the installed copy at {installed_root}"))
    for path in sorted(set(installed_manifest) - set(source_manifest)):
        errors.append(ValidationError(path, "present in the installed copy but not in the source tree"))
    for path in sorted(set(source_manifest) & set(installed_manifest)):
        if source_manifest[path]["sha256"] != installed_manifest[path]["sha256"]:
            errors.append(
                ValidationError(path, f"differs between the source tree and the installed copy at {installed_root}")
            )
    return ("fail" if errors else "pass"), errors


def bug_report(
    project: str | None = None, status: str | None = None, provenance: str | None = None
) -> list[ValidationError]:
    """Print a retrospective table of all bug records, then exit.

    Optional filters narrow the table to one project, one status, or one provenance —
    the equivalent of piping through `awk -F'\\t'`, without remembering column numbers.
    """
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    bugs_root = ROOT / "records" / "bugs"
    if bugs_root.is_dir():
        for path in sorted(bugs_root.rglob("*.md")):
            if path.name == "README.md" or path.parent.name == RECURRENCE_DIR:
                continue
            frontmatter, _, errors = load_bug_markdown(path)
            if errors or not frontmatter:
                continue
            if project and frontmatter.get("project") != project:
                continue
            if status and frontmatter.get("status") != status:
                continue
            if provenance and frontmatter.get("provenance") != provenance:
                continue
            rows.append(
                (
                    str(frontmatter.get("recorded_at", "")),
                    str(frontmatter.get("bug_id", "")),
                    str(frontmatter.get("status", "")),
                    str(frontmatter.get("severity", "")),
                    str(frontmatter.get("error_kind", "")),
                    str(frontmatter.get("title", "")),
                    str(frontmatter.get("provenance", "")),
                )
            )
    rows.sort()
    for recorded, bug_id, row_status, severity, error_kind, title, row_provenance in rows:
        print(f"{recorded}\t{bug_id}\t{row_status}\t{severity}\t{error_kind}\t{title}\t{row_provenance}")
    return []


def recurrence_report() -> list[ValidationError]:
    """Print the recurrence ledger table: per class, consolidation state and recurrence tier.

    The tier is derived, not declared: `single` (one occurrence), `recurred` (two or more
    occurrences), `escalated` (at least one occurrence recorded on a version newer than the
    consolidation version). Counts use the referenced records' `agentflow_version`.
    """
    records_root = ROOT / "records" / "bugs"
    versions: dict[str, str] = {}
    for path in sorted(records_root.glob("*/*.md")):
        frontmatter, _, load_errors = load_bug_markdown(path)
        if load_errors or not frontmatter:
            continue
        bug_id = frontmatter.get("bug_id")
        version = frontmatter.get("agentflow_version")
        if isinstance(bug_id, str) and isinstance(version, str):
            versions[bug_id] = version
    rows: list[tuple[str, str, str, int, int, str]] = []
    ledger_dir = records_root / RECURRENCE_DIR
    if ledger_dir.is_dir():
        for path in sorted(ledger_dir.glob("*.md")):
            if path.name == "README.md":
                continue
            frontmatter, _, load_errors = load_bug_markdown(path)
            if load_errors or not frontmatter:
                continue
            occurrences = frontmatter.get("occurrences") or []
            consolidated_in = frontmatter.get("consolidated_in")
            post = 0
            if isinstance(consolidated_in, str):
                consolidated_key = version_tuple(consolidated_in)
                for bug_id in occurrences:
                    version = versions.get(bug_id) if isinstance(bug_id, str) else None
                    if version and version_tuple(version) > consolidated_key:
                        post += 1
            if post >= 1:
                tier = "escalated"
            elif len(occurrences) >= 2:
                tier = "recurred"
            else:
                tier = "single"
            rows.append(
                (
                    str(frontmatter.get("class_id", "")),
                    str(frontmatter.get("status", "")),
                    str(consolidated_in or "-"),
                    len(occurrences),
                    post,
                    tier,
                )
            )
    rows.sort()
    for class_id, status, consolidated_in, count, post, tier in rows:
        print(f"{class_id}\t{status}\t{consolidated_in}\t{count}\t{post}\t{tier}")
    return []


def report(label: str, errors: list[ValidationError]) -> bool:
    if errors:
        print(f"FAIL {label} ({len(errors)} error(s))")
        for error in errors:
            print(f"  - {error}")
        return False
    print(f"PASS {label}")
    return True


def main(argv: list[str] | None = None) -> int:
    # Hard floor: tests/ use PEP 604 syntax without a future import, so an
    # interpreter below 3.10 cannot run the suite — refuse loudly instead of
    # reporting 8 PASS plus a misleading tests failure.
    if sys.version_info < (3, 10):
        found = ".".join(str(part) for part in sys.version_info[:3])
        sys.stderr.write(
            f"validate.py: interpreter too old: found Python {found}, require >= 3.10. "
            "The default `python3` may be the Xcode CLT 3.9; use `python3.12` explicitly. "
            "No check was run.\n"
        )
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        choices=[
            "schemas",
            "examples",
            "evals",
            "artifacts",
            "mock",
            "protected",
            "manifests",
            "docs",
            "tests",
            "installed",
            "all",
            "report",
            "recurrence",
        ],
        help="contract set to validate, or 'report'/'recurrence' for retrospective tables",
    )
    parser.add_argument(
        "--path",
        dest="installed_path",
        help="for 'installed', compare against this plugin copy instead of the ZCode cache",
    )
    parser.add_argument("--project", dest="report_project", help="for 'report', only records of this project")
    parser.add_argument("--status", dest="report_status", help="for 'report', only records with this status")
    parser.add_argument(
        "--provenance", dest="report_provenance", help="for 'report', only records with this provenance"
    )
    args = parser.parse_args(argv)

    if args.target == "report":
        errors = bug_report(
            project=args.report_project, status=args.report_status, provenance=args.report_provenance
        )
        return 1 if errors else 0

    if args.target == "recurrence":
        errors = recurrence_report()
        return 1 if errors else 0

    if args.target == "installed":
        status, errors = validate_installed(args.installed_path)
        if status == "skip":
            print("SKIP installed (no local plugin install found; nothing to compare)")
            return 0
        return 0 if report("installed", errors) else 1

    checks = {
        "schemas": [("schemas", validate_schemas)],
        "examples": [("examples", validate_examples)],
        "evals": [("evals", validate_evals_suite)],
        "artifacts": [("artifacts", validate_workspace_artifacts)],
        "mock": [("mock", validate_mock_fixtures)],
        "protected": [("protected", validate_protected_paths)],
        "manifests": [("manifests", validate_manifests)],
        "docs": [("docs", validate_doc_consistency)],
        "tests": [("tests", validate_unit_tests)],
        "all": [
            ("schemas", validate_schemas),
            ("examples", validate_examples),
            ("evals", validate_evals_suite),
            ("artifacts", validate_workspace_artifacts),
            ("mock", validate_mock_fixtures),
            ("protected", validate_protected_paths),
            ("manifests", validate_manifests),
            ("docs", validate_doc_consistency),
            ("tests", validate_unit_tests),
        ],
    }[args.target]

    success = True
    for label, check in checks:
        success = report(label, check()) and success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
