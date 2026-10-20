"""The Draft 2020-12 subset validator and the schema-set check."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .common import (
    ROOT,
    ValidationError,
    is_type,
    json_equal_key,
    json_values_equal,
    load_json,
    parse_rfc3339_date_time,
)

SCHEMA_PATHS = [
    ROOT / "schemas",
    ROOT / "skills" / "improve" / "references",
]


IMPROVEMENT_SCHEMA_NAMES = {
    "candidate.schema.json",
    "episode.schema.json",
    "release-record.schema.json",
}


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
        pointer = fragment.removeprefix("#")
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
                matched_count = sum(1 for item in instance if self._matches(item, schema["contains"], schema_path))
                minimum = schema.get("minContains", 1)
                if matched_count < minimum:
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

        # then/else apply only as the branches of an if; a bare else or then is inert.
        if "if" in schema:
            branch = "then" if self._matches(instance, schema["if"], schema_path) else "else"
            branch_schema = schema.get("then") if branch == "then" else schema.get("else")
            if branch_schema is not None:
                errors.extend(self._validate(instance, branch_schema, path, schema_path))

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
        errors.extend(validate_schema_shape(document, path))
        errors.extend(check_schema_keywords(document, path))
    return errors


def validate_schema_shape(document: dict[str, Any], path: Path) -> list[ValidationError]:
    """Check a record contract's own shape, not just its meta-declarations.

    The 2026-10-13 audit found this check shallow: it only confirmed `$schema`, `$id` and that
    `$ref` targets exist, so a contract could drop every required key, accept arbitrary extra
    keys, or stop being an object contract at all and still pass. These are the properties that
    make a contract a contract — and the ones a candidate has an incentive to loosen, since the
    compile step measures candidate records against them (hard boundary 6).
    """
    errors: list[ValidationError] = []
    if document.get("type") != "object":
        errors.append(ValidationError(str(path), "must declare type: object"))
    properties = document.get("properties")
    if not isinstance(properties, dict) or not properties:
        errors.append(ValidationError(str(path), "must declare a non-empty properties map"))
    required = document.get("required")
    if (
        not isinstance(required, list)
        or not required
        or not all(isinstance(item, str) and item for item in required)
    ):
        errors.append(
            ValidationError(str(path), "must declare a non-empty required list of property names")
        )
    if document.get("additionalProperties") is not False:
        errors.append(
            ValidationError(
                str(path),
                "must set additionalProperties: false — a contract that silently accepts extra "
                "keys can be loosened without the compile step noticing",
            )
        )
    if isinstance(properties, dict) and isinstance(required, list):
        for name in required:
            if isinstance(name, str) and name not in properties:
                errors.append(
                    ValidationError(str(path), f"required property {name!r} is not declared in properties")
                )
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


# Keywords the hand-written SchemaValidator implements — mirrors the ``if ... in schema``
# dispatch in SchemaValidator._validate — plus the annotation keywords JSON Schema lets
# validators ignore. A schema using a validation keyword outside this set would be
# silently skipped by the subset validator, so the gate must refuse it instead of
# pretending to check it (fail-closed). Extend only together with a matching _validate
# branch; a typo like ``minLenght`` lands here too, which is the point.
SUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        # reference and metadata
        "$ref",
        "$id",
        "$schema",
        "$comment",
        "$defs",
        "definitions",
        # annotations: validators ignore them, so they cannot hide a missing check
        "title",
        "description",
        "default",
        "examples",
        "deprecated",
        "readOnly",
        "writeOnly",
        # validation keywords implemented by SchemaValidator._validate
        "type",
        "enum",
        "const",
        "format",
        "pattern",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "items",
        "minItems",
        "maxItems",
        "uniqueItems",
        "contains",
        "minContains",
        "properties",
        "additionalProperties",
        "required",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "if",
        "then",
        "else",
    }
)

# Positions whose value is itself a schema, a map of schemas, or a list of schemas.
# The walker visits schema positions only: the values of ``const``/``enum``/``default``/
# ``examples`` are data, not schemas, so their keys must never be read as keywords.
_SCHEMA_VALUE_KEYWORDS = (
    "additionalProperties",
    "items",
    "contains",
    "not",
    "if",
    "then",
    "else",
    "propertyNames",
    "unevaluatedItems",
    "unevaluatedProperties",
)
_SCHEMA_MAP_KEYWORDS = ("properties", "patternProperties", "dependentSchemas", "$defs", "definitions")
_SCHEMA_LIST_KEYWORDS = ("allOf", "anyOf", "oneOf", "prefixItems")


def check_schema_keywords(value: Any, schema_path: Path, location: str = "$") -> list[ValidationError]:
    """Reject validation keywords the hand-written validator does not implement.

    JSON Schema says validators ignore unknown keywords; this subset validator really
    does, which turns ``exclusiveMinimum``/``patternProperties`` (or a misspelled
    ``minLenght``) into a constraint that is declared but never enforced. Walking every
    schema position keeps that class of silent gap a compile error. The same walk covers
    ``format`` values: only ``date-time`` has an implementation, so any other value would
    be skipped rather than checked (the 2026-10-19 audit's G14).
    """
    errors: list[ValidationError] = []
    if not isinstance(value, dict):
        return errors
    items = value.get("items")
    if isinstance(items, list):
        # Array-form items is the Draft-07 tuple spelling; Draft 2020-12 (which the gate
        # enforces) uses prefixItems. Reject it instead of walking a form the subset
        # validator never executes.
        errors.append(
            ValidationError(
                str(schema_path),
                f"{location}.items: array-form items is Draft-07; use prefixItems (Draft 2020-12)",
            )
        )
    for key, sub_value in value.items():
        if key not in SUPPORTED_SCHEMA_KEYWORDS:
            errors.append(
                ValidationError(
                    str(schema_path),
                    f"{location}: unsupported keyword {key!r}: the subset validator "
                    "would silently skip it",
                )
            )
        elif key == "format" and sub_value != "date-time":
            errors.append(
                ValidationError(
                    str(schema_path),
                    f"{location}.format: unsupported format value {sub_value!r}: the subset "
                    "validator implements only 'date-time'",
                )
            )
    for key in _SCHEMA_VALUE_KEYWORDS:
        if key in value:
            errors.extend(check_schema_keywords(value[key], schema_path, f"{location}.{key}"))
    for key in _SCHEMA_MAP_KEYWORDS:
        child = value.get(key)
        if isinstance(child, dict):
            for name, sub in child.items():
                errors.extend(check_schema_keywords(sub, schema_path, f"{location}.{key}.{name}"))
    for key in _SCHEMA_LIST_KEYWORDS:
        child = value.get(key)
        if isinstance(child, list):
            for index, sub in enumerate(child):
                errors.extend(check_schema_keywords(sub, schema_path, f"{location}.{key}[{index}]"))
    return errors
