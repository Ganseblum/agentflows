"""Manifest agreement and the protected-path coverage check."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (MANIFEST_POINTERS, PROTECTED_PATHS_FILE, REQUIRED_PROTECTED_PATHS, ROOT, ValidationError, load_json)


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
    # Coverage alone is a string comparison: a typo, a renamed file, or a path that never existed
    # still "covers" the required entry because the prefix text matches. The 2026-10-13 audit
    # flagged this — the list could protect nothing while every check stayed green. Every declared
    # entry must resolve to something real in this repository.
    for entry in sorted(normalized):
        if not (ROOT / entry).exists():
            errors.append(
                ValidationError(
                    str(list_path),
                    f"declared protected path {entry!r} does not exist in this repository — "
                    "the gate surface cannot protect a path that is not there",
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
