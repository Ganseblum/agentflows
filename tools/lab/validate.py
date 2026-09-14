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
import re
import sys
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import artifact_digest  # noqa: E402  (sibling module, standard library only)


ROOT = Path(__file__).resolve().parents[2]
BUG_RECORD_SCHEMA = ROOT / "schemas" / "bug-record.schema.json"
PROTECTED_PATHS_FILE = ROOT / "protected-paths.txt"
SCHEMA_PATHS = [
    ROOT / "schemas",
    ROOT / "skills" / "improve" / "references",
]
IMPROVEMENT_SCHEMA_NAMES = {
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
    "skills/improve/references/evidence-and-release.md",
    "schemas/evaluation-result.schema.json",
    "tools/lab/artifact_digest.py",
    "tools/lab/eval_runner.py",
    "tools/lab/host_adapter.py",
    "tools/lab/isolation.py",
    "tools/lab/policy.py",
    "tools/lab/validate.py",
    "protected-paths.txt",
}

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
    except (OSError, json.JSONDecodeError) as exc:
        return None, [ValidationError(str(path), f"invalid JSON: {exc}")]


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
    except OSError as exc:
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

        if "const" in schema and instance != schema["const"]:
            errors.append(ValidationError(path, f"must equal {schema['const']!r}"))

        if "enum" in schema and instance not in schema["enum"]:
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
                    dt.datetime.fromisoformat(instance.replace("Z", "+00:00"))
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
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "plans":
        return ROOT / "schemas" / "plan.schema.json"
    if len(parts) >= 2 and parts[0] == "records" and parts[1] == "plans":
        return ROOT / "schemas" / "plan.schema.json"
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "invalid":
        if relative_path.name.startswith("plan-"):
            return ROOT / "schemas" / "plan.schema.json"
    if len(parts) >= 2 and parts[0] == "evals" and parts[1] == "public":
        return ROOT / "skills" / "improve" / "references" / "eval-case.schema.json"
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
            parsed[name] = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return [ValidationError(str(path), f"{name} must be an ISO 8601 date-time value")]
    now = dt.datetime.now(dt.timezone.utc)
    for name, value in parsed.items():
        if value > now + dt.timedelta(minutes=5):
            errors = [ValidationError(str(path), f"{name} is in the future; stamps must reflect real time")]
            return errors
    if "updated_at" in parsed and parsed["updated_at"] < parsed["recorded_at"]:
        return [ValidationError(str(path), "updated_at must not precede recorded_at")]
    return []


BUG_REQUIRED_HEADINGS = ("## Symptom", "## Root cause")
BUG_ARCHIVE_DIR = "archive"
BUG_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


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
    if frontmatter.get("status") != "open" and not heading_present(body, "## Fix"):
        errors.append(ValidationError(str(path), "body section '## Fix' is required unless the bug is open"))
    if frontmatter.get("status") == "verified" and not heading_present(body, "## Review"):
        errors.append(ValidationError(str(path), "body section '## Review' is required for a verified record"))
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


def validate_plan_invariants(document: dict[str, Any], path: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    errors.extend(validate_timestamp_order(document, path))
    packages = document.get("work_packages", [])
    package_ids = [package.get("package_id") for package in packages]
    known = set(package_ids)
    if len(package_ids) != len(known):
        errors.append(ValidationError(str(path), "work_package package_id values must be unique"))

    graph: dict[str, list[str]] = {package_id: [] for package_id in known}
    for package in packages:
        package_id = package.get("package_id")
        for dependency in package.get("depends_on", []):
            if dependency not in known:
                errors.append(
                    ValidationError(
                        f"{path}:$.work_packages[{package_id}]",
                        f"unknown work-package dependency {dependency!r}",
                    )
                )
            else:
                graph[package_id].append(dependency)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(ValidationError(str(path), f"work-package dependency cycle includes {node!r}"))
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for package_id in known:
        visit(package_id)

    lanes = document.get("parallel_lanes", [])
    lane_ids = [lane.get("lane_id") for lane in lanes]
    if len(lane_ids) != len(set(lane_ids)):
        errors.append(ValidationError(str(path), "parallel lane IDs must be unique"))
    assigned: list[str] = []
    for lane in lanes:
        assigned.extend(lane.get("work_package_ids", []))
        for package_id in lane.get("work_package_ids", []):
            if package_id not in known:
                errors.append(ValidationError(str(path), f"parallel lane references unknown package {package_id!r}"))
    if len(assigned) != len(set(assigned)):
        errors.append(ValidationError(str(path), "each work package may appear in only one parallel lane"))
    if set(assigned) != known:
        errors.append(ValidationError(str(path), "parallel lanes must cover every work package exactly once"))

    for field in ("acceptance_criteria", "verification", "review_gates", "rollback_points"):
        items = document.get(field, [])
        id_field = {
            "acceptance_criteria": "criterion_id",
            "verification": "check_id",
            "review_gates": "gate_id",
            "rollback_points": "point_id",
        }[field]
        ids = [item.get(id_field) for item in items]
        if len(ids) != len(set(ids)):
            errors.append(ValidationError(str(path), f"{field} identifiers must be unique"))
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
        if record_parts == ("examples", "plans") or record_parts == ("records", "plans") or (
            relative.parts[0:2] == ("examples", "invalid") and path.name.startswith("plan-")
        ):
            errors.extend(validate_plan_invariants(document, path))
        elif relative.parts[0:2] == ("evals", "public"):
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


def validate_examples() -> list[ValidationError]:
    errors: list[ValidationError] = []
    bug_paths = sorted((ROOT / "examples" / "bug-records").glob("*.md"))
    valid_paths = sorted((ROOT / "examples" / "plans").glob("*.json"))
    valid_paths += sorted((ROOT / "examples" / "evaluation-results").glob("*.json"))
    invalid_json = sorted(
        p for p in (ROOT / "examples" / "invalid").glob("*.json") if p.name.startswith("plan-")
    )
    invalid_md = sorted(
        p for p in (ROOT / "examples" / "invalid").glob("*.md") if p.name.startswith("bug-record")
    )
    if not bug_paths or not valid_paths or not (invalid_json + invalid_md):
        errors.append(ValidationError("examples", "valid and invalid example sets are all required"))
    for path in bug_paths:
        document_errors = validate_bug_markdown(path)
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    for path in valid_paths:
        document_errors = validate_document(path)
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    for path in invalid_json:
        document_errors = validate_document(path)
        if not document_errors:
            errors.append(ValidationError(str(path), "expected invalid example to be rejected"))
    for path in invalid_md:
        document_errors = validate_bug_markdown(path)
        if not document_errors:
            errors.append(ValidationError(str(path), "expected invalid example to be rejected"))
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


def validate_workspace_artifacts() -> list[ValidationError]:
    """Validate record instances under records/ (Markdown bug records, JSON plans)."""
    errors: list[ValidationError] = []
    records_root = ROOT / "records"
    if not records_root.is_dir():
        return errors
    seen_bug_ids: dict[str, Path] = {}
    for path in sorted(records_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        parts = relative.parts
        if parts[0:2] == ("records", "bugs"):
            if path.name == "README.md":
                continue
            if path.suffix != ".md":
                errors.append(ValidationError(str(path), "bug records are Markdown files; unexpected non-md file"))
                continue
            frontmatter, _, load_errors = load_bug_markdown(path)
            if load_errors or frontmatter is None:
                errors.extend(load_errors)
                continue
            errors.extend(validate_bug_markdown(path))
            errors.extend(validate_bug_layout(frontmatter, path, relative, seen_bug_ids))
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
        elif parts[0:2] == ("records", "plans"):
            if path.name == "README.md":
                continue
            if path.suffix != ".json":
                errors.append(ValidationError(str(path), "plans are JSON files; unexpected non-json file"))
                continue
            document_errors = validate_document(path)
            if document_errors:
                errors.extend(document_errors)
                continue
            document, load_errors = load_json(path)
            if load_errors or not isinstance(document, dict):
                errors.extend(load_errors)
                continue
            expected_id = document.get("plan_id")
            if isinstance(expected_id, str) and path.stem != expected_id:
                errors.append(
                    ValidationError(str(path), f"filename stem must equal the record id {expected_id!r}")
                )
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


def validate_protected_paths() -> list[ValidationError]:
    """Check the declared candidate gate surface still covers the required entries."""
    errors: list[ValidationError] = []
    if not PROTECTED_PATHS_FILE.is_file():
        return [ValidationError(str(PROTECTED_PATHS_FILE), "the protected path list is missing")]
    entries, load_errors = load_protected_paths(PROTECTED_PATHS_FILE)
    if load_errors:
        return load_errors
    normalized = {entry.strip("/") for entry in entries}
    for required in sorted(REQUIRED_PROTECTED_PATHS):
        covered = any(entry == required or required.startswith(entry + "/") for entry in normalized)
        if not covered:
            errors.append(
                ValidationError(
                    str(PROTECTED_PATHS_FILE),
                    f"required gate path {required!r} is no longer covered by any declared prefix",
                )
            )
    return errors


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


def bug_report() -> list[ValidationError]:
    """Print a retrospective table of all bug records, then exit."""
    rows: list[tuple[str, str, str, str, str, str]] = []
    bugs_root = ROOT / "records" / "bugs"
    if bugs_root.is_dir():
        for path in sorted(bugs_root.rglob("*.md")):
            if path.name == "README.md":
                continue
            frontmatter, _, errors = load_bug_markdown(path)
            if errors or not frontmatter:
                continue
            rows.append(
                (
                    str(frontmatter.get("recorded_at", "")),
                    str(frontmatter.get("bug_id", "")),
                    str(frontmatter.get("status", "")),
                    str(frontmatter.get("severity", "")),
                    str(frontmatter.get("error_kind", "")),
                    str(frontmatter.get("title", "")),
                )
            )
    rows.sort()
    for recorded, bug_id, status, severity, error_kind, title in rows:
        print(f"{recorded}\t{bug_id}\t{status}\t{severity}\t{error_kind}\t{title}")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        choices=["schemas", "examples", "evals", "artifacts", "protected", "installed", "all", "report"],
        help="contract set to validate, or 'report' to list bug records",
    )
    parser.add_argument(
        "--path",
        dest="installed_path",
        help="for 'installed', compare against this plugin copy instead of the ZCode cache",
    )
    args = parser.parse_args(argv)

    if args.target == "report":
        errors = bug_report()
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
        "evals": [("evals", validate_evals)],
        "artifacts": [("artifacts", validate_workspace_artifacts)],
        "protected": [("protected", validate_protected_paths)],
        "all": [
            ("schemas", validate_schemas),
            ("examples", validate_examples),
            ("evals", validate_evals),
            ("artifacts", validate_workspace_artifacts),
            ("protected", validate_protected_paths),
        ],
    }[args.target]

    success = True
    for label, check in checks:
        success = report(label, check()) and success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
