#!/usr/bin/env python3
"""Validate Agentflow contracts, examples, and record artifacts.

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
    "candidate.schema.json",
    "episode.schema.json",
    "release-record.schema.json",
}

# The minimum gate surface protected-paths.txt must still cover. Editing this set is a release
# policy change and requires explicit human review; it is not something a candidate may arrange
# around. Keep it in sync with the inclusion rule documented in protected-paths.txt.
REQUIRED_PROTECTED_PATHS = {
    "agents/evaluator.md",
    "agents/release-governor.md",
    "schemas/bug-record.schema.json",
    "schemas/recurrence.schema.json",
    "schemas/review.schema.json",
    "schemas/plan.schema.json",
    "schemas/test-plan.schema.json",
    "schemas/test-run.schema.json",
    "skills/improve/references/evidence-and-release.md",
    "skills/improve/references/episode.schema.json",
    "skills/improve/references/candidate.schema.json",
    "skills/improve/references/release-record.schema.json",
    "tests/test_lab_contracts.py",
    "tests/test_record_store.py",
    "tools/lab/artifact_digest.py",
    "tools/lab/doc_chain.py",
    "tools/lab/isolation.py",
    "tools/lab/validate.py",
    "protected-paths.txt",
    ".github/workflows/validate.yml",
}

# Declared contents of `tests/`. The directory is not a protected prefix — generated
# `__pycache__` entries there would otherwise block every candidate that ran the checks — so the
# pinned test files are protected individually and this list asserts nothing else appears. A new
# test file is a human-authored change to this list plus the protection entry above.
EXPECTED_TEST_FILES = ("test_lab_contracts.py", "test_record_store.py")

# Live record roots (2026-10-12 slimming batch, phase 4): the top-level plans/ root was
# dissolved — plans live inside their feature batch (docs/features/<batch>/plan/), matching
# youc-workflow-ai / aiwork-workflow-ai where a feature owns its plan/spec/design segments.
# Five record zones now: docs/issues, docs/releases (working files only; per-version release
# JSON was retired with the 0.8.x records, the improvements/ three-subtree by user decision),
# docs/features (batch directories; only plan/*.md carries a machine contract here), plus
# episodes/ and reviews/ at the root. The cross-batch decision queue sits at
# docs/PENDING-DECISIONS.md, outside any record root.
# `validate_workspace_artifacts` walks each root and compiles what it holds.
LIVE_RECORD_ROOTS = ("docs/issues", "docs/releases", "docs/features", "episodes", "reviews")

# 2026-10-12 slimming batch (user-authorized gate change, ISS-2026-047): the frozen `_archive/`
# tree was removed outright — the repository keeps no archive bucket. Its former exemptions
# (scan exclusions, the handoff-pointer waiver) are deleted with it, and the retired doc
# carriers `docs/iteration-log.md` / `docs/agent-roles.md` joined RETIRED_PATH_TOKENS below so
# recreating them fails the residue scan instead of drifting back in.


# Floor for the regression suite size, parsed from the unittest "Ran N tests" summary. The
# floor is set far below the suite's steady state but far above a trivial suite, so deleting
# or gutting the tests cannot yield a green gate — shrinking the suite becomes a deliberate
# gate change that must be reviewed, not an accident that passes. (A hardcoded current count
# went stale here once already — BUG-era finding N7 — so the suite size is asserted by the
# run itself, never restated in prose.)
MIN_UNIT_TEST_COUNT = 20

# Floor for the doc-chain linter's discrimination self-test, parsed from the linter's
# "N/M self-test cases pass" summary. Same bargain as MIN_UNIT_TEST_COUNT: the floor stays
# far below the linter's steady state and far above a trivial suite, so gutting the checker's
# own discrimination matrix cannot yield a green gate.
MIN_DOC_CHAIN_SELF_TEST_CASES = 20

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
# (docs, record artifacts) may legitimately differ between a source checkout and a snapshot.
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
# Issue records are flat: issues/ISS-<YYYY>-<NNN>-<slug>.md. Only rejected records live under
# issues/归档/<YYYY-MM-DD>/; recurrence ledgers live under issues/recurrence/.
BUG_ARCHIVE_DIR = "归档"
RECURRENCE_DIR = "recurrence"
BUG_FILENAME_PATTERN = re.compile(r"^ISS-\d{4}-\d{3,}-[a-z0-9][a-z0-9-]*$")

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

    Layout: reviews/<project>-<feature-slug>/review-<YYYY-MM-DD>-<NNN>.md — the
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
    parts = relative.parts  # ("reviews", "<project>-<feature-slug>", "review-<date>-<NNN>.md")
    if len(parts) != 3:
        errors.append(
            ValidationError(str(path), "review records live in reviews/<project>-<feature-slug>/")
        )
    else:
        if "-" not in parts[1] or parts[1].startswith("-") or parts[1].endswith("-"):
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

    Home (2026-10 structural overhaul): features/<batch>/testing/<project>-<feature-slug>/
    plan-<YYYY-MM-DD>-<NNN>.md — feature-anchored directory, filename matches test_plan_id,
    revised in place (test_version bump). The artifacts walk deliberately does not patrol the
    feature batch directories yet, so callers in examples/ still exercise this function while
    the layout check stays deferred to that separately reviewed change. Body contract: the
    用例 registry table (unique TC ids, level/priority enums, case_count equality, one detail
    heading per case) plus the 边界覆盖 and 流程疑点 sections.
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
    # Layout note (deferred): test plans now land in the feature batch directory
    # (features/<batch>/testing/<project>-<feature-slug>/plan-<date>-<seq>.md). The artifacts
    # walk does not patrol features/ yet — that patrol is a separately reviewed change — so no
    # directory-shape check is applied here; this function validates the frontmatter/body
    # contract only.
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
    # Layout note (deferred): test runs now land in the feature batch directory
    # (features/<batch>/testing/<project>-<feature-slug>/run-<date>-<seq>.md). As with test
    # plans, the artifacts walk does not patrol features/ yet, so no directory-shape check is
    # applied here; this function validates the frontmatter/body contract only.
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
    """Validate filename shape and bug_id uniqueness for one record.

    Live records are flat: issues/ISS-<YYYY>-<NNN>-<slug>.md. Archived (rejected) records keep
    a date directory: issues/归档/<YYYY-MM-DD>/ISS-<YYYY>-<NNN>-<slug>.md.
    """
    errors: list[ValidationError] = []
    bug_id = frontmatter.get("bug_id")
    if isinstance(bug_id, str):
        if bug_id in seen_ids:
            errors.append(
                ValidationError(str(path), f"duplicate bug_id {bug_id!r} already recorded in {seen_ids[bug_id]}")
            )
        else:
            seen_ids[bug_id] = path
    if not BUG_FILENAME_PATTERN.match(path.stem):
        errors.append(
            ValidationError(
                str(path),
                "filename must be ISS-<YYYY>-<NNN>-<kebab-case-slug> "
                "(lowercase letters, digits, hyphens) — e.g. ISS-2026-001-claude-json-schema-rejected.md",
            )
        )

    parts = relative.parts  # ("docs", "issues", "ISS-…-slug.md") or ("docs", "issues", "归档", "YYYY-MM-DD", "ISS-…-slug.md")
    if BUG_ARCHIVE_DIR in parts:
        date_parts = [part for part in parts[3:] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", part)]
        if not date_parts:
            errors.append(
                ValidationError(str(path), "archived records live in a YYYY-MM-DD directory under docs/issues/归档/")
            )
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
    elif len(parts) != 3:
        errors.append(
            ValidationError(str(path), "live issue records live directly under docs/issues/ (docs/issues/ISS-<YYYY>-<NNN>-<slug>.md)")
        )
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
    """Test plan entries parsed from examples/testing for standalone run-example validation."""
    plans: dict[str, dict[str, Any]] = {}
    for plan_path in sorted((ROOT / "examples" / "testing").glob("plan-*.md")):
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
    return errors


# Every path under a live record root is a stray file or an unknown subdirectory and must fail
# the artifacts check explicitly instead of falling through the root dispatch silently.

def validate_workspace_artifacts() -> list[ValidationError]:
    """Validate record instances under the live record roots.

    Issue records (with their recurrence ledgers and rejected-record archive under
    docs/issues/), JSON episodes, the batch directories under docs/features/ (their
    plan/<plan_id>.md hybrids only), the working files under docs/releases/, and review
    records with their archive snapshots. The improve-loop artifact subtrees and the
    per-version release records were retired by the 2026-10-12 slimming batches.
    """
    errors: list[ValidationError] = []
    seen_bug_ids: dict[str, Path] = {}
    seen_review_ids: dict[str, Path] = {}
    seen_episode_ids: dict[str, Path] = {}
    record_versions: dict[str, str] = {}
    ledgers: dict[str, dict[str, Any]] = {}
    class_records: list[tuple[str, Any, str, Path]] = []
    review_findings: list[tuple[list, Path]] = []
    live_roots: list[str] = []
    for root_name in LIVE_RECORD_ROOTS:
        root = ROOT / root_name
        if not root.is_dir():
            errors.append(
                ValidationError(str(root), f"{root_name} directory is missing; artifacts are required")
            )
            continue
        live_roots.append(root_name)
        if not any(entry for entry in root.iterdir() if not entry.name.startswith(".")):
            errors.append(
                ValidationError(str(root), f"{root_name} directory is empty; artifacts are required")
            )
    for root_name in live_roots:
        root = ROOT / root_name
        kind = root_name.rsplit("/", 1)[-1]
        base = len(root_name.split("/"))  # path depth of the root itself
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(ROOT)
            parts = relative.parts
            under = parts[base:]  # entry path relative to the record root
            n = len(under)
            if any(part.startswith(".") for part in under):
                if path.name == ".DS_Store":
                    continue
                errors.append(ValidationError(str(path), "hidden record entry is not allowed"))
                continue
            if kind == "issues":
                if n == 1 and path.is_file() and under[0] == "README.md":
                    continue  # the class README documents the numbering and archive rules
                if (
                    n == 1
                    and not path.is_file()
                    and under[0] not in (RECURRENCE_DIR, BUG_ARCHIVE_DIR)
                ):
                    errors.append(
                        ValidationError(
                            str(path),
                            "unexpected entry under issues/; live issue records are "
                            "ISS-<YYYY>-<NNN>-<slug>.md directly under issues/, with 归档/ and "
                            "recurrence/ the only subdirectories — see issues/README.md",
                        )
                    )
                    continue
                if under[0] == RECURRENCE_DIR:
                    if not path.is_file():
                        continue
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
                archived = under[0] == BUG_ARCHIVE_DIR
                if n > 1 and not archived:
                    errors.append(
                        ValidationError(
                            str(path),
                            "unexpected entry under issues/; only issues/<ISS-…>.md, "
                            "issues/归档/<YYYY-MM-DD>/ and issues/recurrence/ are record locations "
                            "— see issues/README.md",
                        )
                    )
                    continue
                if not path.is_file():
                    continue
                if path.suffix != ".md":
                    errors.append(ValidationError(str(path), "issue records are Markdown files; unexpected non-md file"))
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
                if archived:
                    if status != "rejected":
                        errors.append(
                            ValidationError(str(path), "only rejected records may be archived; verified records stay in place")
                        )
                elif status == "rejected":
                    errors.append(
                        ValidationError(str(path), "a rejected record must be moved into issues/归档/")
                    )
                bug_id = frontmatter.get("bug_id")
                version = frontmatter.get("agentflow_version")
                if isinstance(bug_id, str) and isinstance(version, str):
                    record_versions[bug_id] = version
                class_id = frontmatter.get("class_id")
                if isinstance(class_id, str):
                    class_records.append((class_id, frontmatter.get("occurrence"), str(bug_id or ""), path))
            elif kind == "episodes":
                if n == 1 and path.is_file() and under[0] == "README.md":
                    continue
                if not path.is_file():
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
            elif kind == "reviews":
                if n != 2 or not path.is_file() or not re.fullmatch(
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
            elif kind == "features":
                # Batch directories: only <batch>/plan/<plan_id>.md carries a machine contract
                # here (the plan hybrid). README / proposal / spec / design segments are
                # governed by the doc-chain linter, not by this walk.
                if n != 3 or under[1] != "plan" or not path.is_file() or path.suffix != ".md":
                    continue
                errors.extend(validate_plan_markdown(path, relative))
            elif kind == "releases":
                # 2026-10-12: per-version release JSON was retired — this root holds only the
                # batch todo / pending-test working files, not records.
                if n == 1 and path.is_file() and under[0] in ("todo.md", "pending-test.md"):
                    continue
                errors.append(
                    ValidationError(
                        str(path),
                        "unexpected entry under docs/releases/; per-version release records were "
                        "retired (version history lives in CHANGELOG.md) — only todo.md and "
                        "pending-test.md working files belong here",
                    )
                )
                continue

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
                ValidationError(str(path), f"class_id {class_id!r} has no ledger under issues/recurrence/")
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
    # Test records (test plans and runs) moved to features/<batch>/testing/ with the 2026-10
    # structural overhaul. The artifacts walk patrols only <batch>/plan/ inside docs/features/
    # — the testing/ patrol, including the run-findings bug-id cross-check below, is deferred
    # to a separately reviewed change; validate_test_plan_markdown / validate_test_run_markdown
    # stay exercised through the example fixtures. The improve-loop artifact cross-checks were
    # retired with the improvements/ three-subtree (2026-10-12, user decision).
    return errors


ROLE_NAME_PATTERN = re.compile(r"^name:\s*([a-z0-9-]+)\s*$", re.M)
SKILL_ROLE_PATTERN = re.compile(r"agentflow:([a-z0-9-]+)")

# 0.5.0 switched plans from JSON to Markdown hybrids (plans/README.md); either
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
                "hybrids named <plan_id>.md — see plans/README.md",
            )
        )
    return errors


# Files whose prose states the plugin's current maturity. Version literals there drift on
# every bump (the 0.6.0 → 0.7.4 → 0.7.5 hand-sync family); the version lives in the five
# manifests and CHANGELOG, and these files must point at it instead of restating it.
VERSION_PROSE_FILES = (
    "README.md",
    "docs/design-decisions.md",
)
VERSION_LITERAL_PATTERN = re.compile(r"\bv?\d+\.\d+\.\d+\b")


# Retired-path residue on the live document surface (2026-10-09 cleanup batch). The 2026-10
# structural overhaul mechanically re-pointed existing references, but nothing kept NEW prose
# from naming a retired path again — the same reliance-on-memory gap this check family exists to
# close. Two classes are machine-checkable: a relative Markdown link whose target does not
# resolve, and a retired path token in prose. Fenced blocks and inline code are quotations, not
# claims (the record contracts' 引文 exemption) — but a mermaid diagram is content, not a
# quotation, so diagrams stay scanned. The generated `packaging/runtime/` tree is out of both
# scans; `CHANGELOG.md` is exempt from the token scan only — its entries describe the layout of
# their own time and keep retired paths verbatim. The 2026-10-12 slimming batch removed the
# frozen `_archive/` bucket and the migration-record exemption with it: those paths are now
# residue like any other, and the two retired doc carriers joined the token list.
RETIRED_PATH_TOKENS = (
    "records/",
    "bugs/",
    "improvement/",
    "docs/audit-2026-09-18",
    "next-session-handoff",
    "docs/iteration-log",
    "docs/agent-roles",
)
HISTORICAL_DOC_CARRIERS = ("CHANGELOG.md",)
FENCED_BLOCK_PATTERN = re.compile(r"```(?P<info>[^\n`]*)\n.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")
LINK_TARGET_PATTERN = re.compile(r"\]\(([^)]+)\)")


def strip_quotation_fences(text: str) -> str:
    """Remove fenced blocks except mermaid diagrams; a diagram is content, not a quotation."""
    def keep_mermaid(match: re.Match) -> str:
        return match.group(0) if match.group("info").strip().startswith("mermaid") else ""

    return FENCED_BLOCK_PATTERN.sub(keep_mermaid, text)


def live_doc_paths(root: Path) -> list[Path]:
    """Every *.md outside the generated runtime tree."""
    paths: list[Path] = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if relative.as_posix().startswith("packaging/runtime/"):
            continue
        paths.append(path)
    return sorted(paths)


def validate_live_doc_references(root: Path = ROOT) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for path in live_doc_paths(root):
        relative = path.relative_to(root)
        text, read_errors = read_document_text(path)
        if read_errors:
            errors.extend(read_errors)
            continue
        link_scan_text = INLINE_CODE_PATTERN.sub("", strip_quotation_fences(text))
        for match in LINK_TARGET_PATTERN.finditer(link_scan_text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#", "<", "/")):
                continue
            target_path = target.split("#", 1)[0].strip()
            if not target_path or target_path.startswith("<"):
                continue
            if not (path.parent / target_path).exists():
                errors.append(ValidationError(str(relative), f"broken relative link: {target}"))
        if relative.as_posix() in HISTORICAL_DOC_CARRIERS:
            continue
        inside_fence: str | None = None
        for number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("```"):
                fence_info = line.lstrip()[3:].strip()
                inside_fence = None if inside_fence is not None else fence_info
                continue
            if inside_fence is not None and not inside_fence.startswith("mermaid"):
                continue
            # A repo-qualified reference (<repo>@<revision>:<path>) is an address, not a
            # claim — the record contracts accept it verbatim in prose and frontmatter, so
            # the token scan strips it before matching (agentflows@0.8.2:docs/agent-roles.md
            # must stay citable inside a record even after docs/agent-roles was retired).
            scan = QUALIFIED_REF_PATTERN.sub(" ", INLINE_CODE_PATTERN.sub("", line))
            for token in RETIRED_PATH_TOKENS:
                index = scan.find(token)
                while index != -1:
                    preceded_by_word = index > 0 and (
                        scan[index - 1].isalnum() or scan[index - 1] == "_"
                    )
                    if not preceded_by_word:
                        errors.append(
                            ValidationError(
                                str(relative),
                                f"retired path in prose (line {number}): {token!r}",
                            )
                        )
                    index = scan.find(token, index + 1)
    return errors


def validate_doc_consistency() -> list[ValidationError]:
    """Cross-check the hand-synced role/document surface (the 0.3.3 manifest-drift family).

    The role/doc surface is synced by hand across twelve agent files, two SKILLs, the roles
    reference, the class READMEs under the live record roots, and the root AGENTS.md — the same
    failure class as the missed manifest bump. Five assertion groups: every agent file's
    frontmatter name equals its filename; every `agentflow:<role>` referenced by a SKILL
    resolves to an agent file; every `schemas/*.schema.json` path named anywhere in the
    docs/live-roots/skills/agents surface or in AGENTS.md exists; AGENTS.md carries no
    pre-0.5.0 JSON plan contract markers; the Chinese mirror keeps section parity with its
    English contract documents. Two live-surface scans close the 2026-10 residue classes:
    relative Markdown links must resolve, and prose must not name a retired path (fenced and
    inline code are quotations — except mermaid diagrams, which are content — and
    `CHANGELOG.md` keeps its historical entries verbatim).
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
        *(ROOT / name for name in LIVE_RECORD_ROOTS),
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

    errors.extend(validate_live_doc_references())
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
    issues_root = ROOT / "docs" / "issues"
    if issues_root.is_dir():
        for path in sorted(issues_root.rglob("*.md")):
            if path.name == "README.md" or RECURRENCE_DIR in path.relative_to(issues_root).parts:
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
    issues_root = ROOT / "docs" / "issues"
    versions: dict[str, str] = {}
    for path in sorted(issues_root.rglob("*.md")):
        if path.name == "README.md" or RECURRENCE_DIR in path.relative_to(issues_root).parts:
            continue
        frontmatter, _, load_errors = load_bug_markdown(path)
        if load_errors or not frontmatter:
            continue
        bug_id = frontmatter.get("bug_id")
        version = frontmatter.get("agentflow_version")
        if isinstance(bug_id, str) and isinstance(version, str):
            versions[bug_id] = version
    rows: list[tuple[str, str, str, int, int, str]] = []
    ledger_dir = issues_root / RECURRENCE_DIR
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
                    "artifacts",
            "protected",
            "manifests",
            "docs",
            "tests",
            "doc_chain",
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
        "artifacts": [("artifacts", validate_workspace_artifacts)],
        "protected": [("protected", validate_protected_paths)],
        "manifests": [("manifests", validate_manifests)],
        "docs": [("docs", validate_doc_consistency)],
        "tests": [("tests", validate_unit_tests)],
        "doc_chain": [("doc_chain", validate_doc_chain)],
        "all": [
            ("schemas", validate_schemas),
            ("examples", validate_examples),
            ("artifacts", validate_workspace_artifacts),
            ("protected", validate_protected_paths),
            ("manifests", validate_manifests),
            ("docs", validate_doc_consistency),
            ("tests", validate_unit_tests),
            ("doc_chain", validate_doc_chain),
        ],
    }[args.target]

    success = True
    for label, check in checks:
        success = report(label, check()) and success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
