"""Comparison of the source checkout with an installed plugin snapshot."""

from __future__ import annotations

import hashlib
from pathlib import Path
import artifact_digest

from .common import (INSTALLED_COMPONENTS, INSTALLED_FILES, ROOT, ValidationError, load_json)


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
