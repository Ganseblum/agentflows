#!/usr/bin/env python3
"""Validate Agentflow contracts, examples, and public evaluation fixtures.

This intentionally uses only the Python standard library. It implements the small
Draft 2020-12 vocabulary used by the repository's contracts and adds explicit
cross-document checks that JSON Schema cannot express conveniently.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
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
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "bug-records":
        return ROOT / "schemas" / "bug-record.schema.json"
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "plans":
        return ROOT / "schemas" / "plan.schema.json"
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "invalid":
        if relative_path.name.startswith("bug-record"):
            return ROOT / "schemas" / "bug-record.schema.json"
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


def validate_bug_invariants(document: dict[str, Any], path: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    evidence_ids = {item["evidence_id"] for item in document.get("evidence", []) if isinstance(item, dict)}
    if len(evidence_ids) != len(document.get("evidence", [])):
        errors.append(ValidationError(str(path), "evidence_id values must be unique"))

    for index, check in enumerate(document.get("regression_checks", [])):
        for ref in check.get("evidence_refs", []):
            if ref not in evidence_ids:
                errors.append(
                    ValidationError(
                        f"{path}:$.regression_checks[{index}].evidence_refs",
                        f"unknown evidence reference {ref!r}",
                    )
                )

    status = document.get("status")
    if status == "verified":
        if any(check.get("status") != "pass" for check in document.get("regression_checks", [])):
            errors.append(ValidationError(str(path), "verified bugs must have only passing regression checks"))
        review = document.get("review", {})
        if review.get("decision") != "approved":
            errors.append(ValidationError(str(path), "verified bugs require an approved independent review"))
    return errors


def validate_plan_invariants(document: dict[str, Any], path: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
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
        if relative.parts[0:2] == ("examples", "bug-records") or (
            relative.parts[0:2] == ("examples", "invalid") and path.name.startswith("bug-record")
        ):
            errors.extend(validate_bug_invariants(document, path))
        elif relative.parts[0:2] == ("examples", "plans") or (
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
    valid_paths = sorted((ROOT / "examples" / "bug-records").glob("*.json"))
    valid_paths += sorted((ROOT / "examples" / "plans").glob("*.json"))
    valid_paths += sorted((ROOT / "examples" / "evaluation-results").glob("*.json"))
    invalid_paths = sorted((ROOT / "examples" / "invalid").glob("*.json"))
    if not valid_paths or not invalid_paths:
        errors.append(ValidationError("examples", "both valid and invalid example sets are required"))
    for path in valid_paths:
        document_errors = validate_document(path)
        if document_errors:
            errors.extend(ValidationError(str(path), f"expected valid example: {error.message}") for error in document_errors)
    for path in invalid_paths:
        document_errors = validate_document(path)
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
        choices=["schemas", "examples", "evals", "all"],
        help="contract set to validate",
    )
    args = parser.parse_args(argv)

    checks = {
        "schemas": [("schemas", validate_schemas)],
        "examples": [("examples", validate_examples)],
        "evals": [("evals", validate_evals)],
        "all": [
            ("schemas", validate_schemas),
            ("examples", validate_examples),
            ("evals", validate_evals),
        ],
    }[args.target]

    success = True
    for label, check in checks:
        success = report(label, check()) and success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
