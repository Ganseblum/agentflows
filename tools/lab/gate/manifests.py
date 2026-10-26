"""Manifest agreement and the protected-path coverage check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import re

from .common import (
    MANIFEST_POINTERS,
    PROTECTED_PATHS_FILE,
    REQUIRED_PROTECTED_PATHS,
    ROOT,
    ValidationError,
    load_json,
)


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
) -> tuple[Any, list[ValidationError]]:
    """Read a nested manifest value by pointer, e.g. ("plugins", 0, "version").

    `root` defaults to the repository; the negative contract tests point it at a fixture copy.
    """
    path = root / name
    if not path.is_file():
        return {}, [ValidationError(name, "manifest is missing")]
    document, load_errors = load_json(path)
    if load_errors:
        return {}, load_errors
    value: Any = document
    for part in pointer:
        if isinstance(part, int):
            if not isinstance(value, list) or len(value) <= part:
                return {}, [ValidationError(name, f"manifest has no {'.'.join(map(str, pointer))!s}")]
            value = value[part]
        else:
            if not isinstance(value, dict) or part not in value:
                return {}, [ValidationError(name, f"manifest has no {'.'.join(map(str, pointer))!s}")]
            value = value[part]
    if not isinstance(value, dict):
        return {}, [ValidationError(name, "manifest entry must be an object")]
    return value, []


def _relative_files(base: Path) -> set[str]:
    """All regular files under `base`, repository-relative, without build caches."""
    files: set[str] = set()
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(base)
        if "__pycache__" in relative.parts:
            continue
        files.add(relative.as_posix())
    return files


def _drift(path: str, detail: str, hint: str) -> ValidationError:
    return ValidationError(path, f"{detail} — {hint}")


def _runtime_tracking_errors(root: Path) -> list[ValidationError]:
    """Require `packaging/runtime` to be tracked by git when the repo is a git checkout.

    2026-10-26: the directory sat in `.gitignore`, so every GitHub clone lacked it while
    `marketplace.json` pointed at `./packaging/runtime` — the git marketplace could not resolve
    the plugin source and install failed with "Unsupported or missing plugin source". Freshness
    alone could not catch this: an absent tree made the check skip (the fresh-checkout branch),
    and the source tree itself looked healthy. Tracking is the property that matters for a
    git-distributed plugin, so it gets its own assertion.
    """
    runtime = root / "packaging" / "runtime"
    if not runtime.is_dir():
        return []
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "packaging/runtime/plugin.json"],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return []  # no git available: the distributed-surface question cannot be answered here
    if proc.returncode == 0:
        return []
    combined = (proc.stdout + proc.stderr).lower()
    if "not a git repository" in combined:
        return []  # running from an exported tree or a fixture copy
    hint = "add packaging/runtime to version control (it is what the git marketplace installs)"
    return [
        _drift(
            "packaging/runtime",
            "the snapshot exists but is not tracked by git",
            hint,
        )
    ]


def validate_runtime_freshness(root: Path = ROOT) -> list[ValidationError]:
    """Require the generated packaging/runtime snapshot to match the source surface.

    `marketplace.json` installs from `packaging/runtime`, so a stale snapshot ships outdated
    role and skill text while every other check stays green — the 2026-10-19 audit found that
    tree stuck at 0.10.0 with thirteen drifted agents and no check watching it. The directory
    is a build product: when absent (fresh checkout, CI) the check skips, because
    packaging/build_runtime.py already verifies its own output; when present it must agree with
    the source byte for byte, limited to the same whitelist the builder copies.
    """
    runtime = root / "packaging" / "runtime"
    if not runtime.is_dir():
        return []
    errors: list[ValidationError] = _runtime_tracking_errors(root)
    # Single source of truth for the whitelist: the builder decides what the snapshot contains,
    # so the freshness check must not grow its own copy of that list.
    packaging_dir = Path(__file__).resolve().parents[3] / "packaging"
    if str(packaging_dir) not in sys.path:
        sys.path.insert(0, str(packaging_dir))
    import build_runtime

    hint = "packaging/runtime is stale — run `python3 packaging/build_runtime.py` to regenerate it"

    for name, pointer in MANIFEST_POINTERS:
        source_entry, source_errors = manifest_value(name, pointer, root)
        if source_errors:
            continue  # the source pass in validate_manifests already reports these
        runtime_entry, runtime_errors = manifest_value(name, pointer, runtime)
        if runtime_errors:
            errors.append(_drift(f"packaging/runtime/{name}", "snapshot manifest is missing or unreadable", hint))
            continue
        for field in ("name", "version"):
            source_value = source_entry.get(field)
            runtime_value = runtime_entry.get(field)
            if runtime_value != source_value:
                errors.append(
                    _drift(
                        f"packaging/runtime/{name}",
                        f"{field} {runtime_value!r} disagrees with source {source_value!r}",
                        hint,
                    )
                )

    for name in build_runtime.RUNTIME_DIRECTORIES:
        source_dir = root / name
        if not source_dir.is_dir():
            continue  # a missing source component is the build script's and docs gate's business
        runtime_dir = runtime / name
        source_files = _relative_files(source_dir)
        runtime_files = _relative_files(runtime_dir) if runtime_dir.is_dir() else set()
        missing = sorted(source_files - runtime_files)
        extra = sorted(runtime_files - source_files)
        if missing:
            preview = ", ".join(missing[:5]) + ("…" if len(missing) > 5 else "")
            errors.append(_drift(f"packaging/runtime/{name}", f"{len(missing)} file(s) missing from snapshot: {preview}", hint))
        if extra:
            preview = ", ".join(extra[:5]) + ("…" if len(extra) > 5 else "")
            errors.append(_drift(f"packaging/runtime/{name}", f"{len(extra)} extra file(s) no longer in source: {preview}", hint))
        for relative in sorted(source_files & runtime_files):
            if (source_dir / relative).read_bytes() != (runtime_dir / relative).read_bytes():
                errors.append(_drift(f"packaging/runtime/{name}/{relative}", "content differs from source", hint))

    for name in build_runtime.RUNTIME_FILES:
        source_file = root / name
        if not source_file.is_file():
            continue
        runtime_file = runtime / name
        if not runtime_file.is_file():
            errors.append(_drift(f"packaging/runtime/{name}", "file missing from snapshot", hint))
        elif source_file.read_bytes() != runtime_file.read_bytes():
            errors.append(_drift(f"packaging/runtime/{name}", "content differs from source", hint))

    # Shipped-surface link integrity (2026-10-26 audit G15): the installed plugin is the
    # runtime subset, so a relative Markdown link inside it must resolve *within that subset*,
    # not just in the full source repo. Links to directories that the builder never copies
    # (reviews/, the root templates/ hub) were dead in every installed copy while the source
    # gate — which scans the whole repo — stayed green. Fail any relative .md link whose target
    # is absent under the runtime tree; http/mailto/anchor-only links are not path checks.
    RUNTIME_LINK_RE = re.compile(r"\]\(([^)]+)\)")
    for md in sorted(runtime.rglob("*.md")):
        text = md.read_text(encoding="utf-8", errors="ignore")
        base = md.parent
        for target in RUNTIME_LINK_RE.findall(text):
            tail = target.split("#", 1)[0].strip()
            if not tail or tail.startswith(("http://", "https://", "mailto:", "/")):
                continue
            if not (base / tail).exists():
                errors.append(
                    _drift(
                        f"packaging/runtime/{md.relative_to(runtime).as_posix()}",
                        f"shipped link target missing from install tree: {target!r}",
                        "point the link at a path present in packaging/runtime, or make it "
                        "repo-relative prose instead of a hyperlink",
                    )
                )

    # Shipped checker (RUNTIME_SUBTREES): a stale copy here means every installed user runs an
    # older doc-chain linter than the one the source tree's own gates exercised.
    for name in build_runtime.RUNTIME_SUBTREES:
        source_path = root / name
        if not source_path.exists():
            continue
        snapshot_path = runtime / name
        if source_path.is_file():
            if not snapshot_path.is_file():
                errors.append(_drift(f"packaging/runtime/{name}", "file missing from snapshot", hint))
            elif source_path.read_bytes() != snapshot_path.read_bytes():
                errors.append(_drift(f"packaging/runtime/{name}", "content differs from source", hint))
            continue
        source_files = _relative_files(source_path)
        snapshot_files = _relative_files(snapshot_path) if snapshot_path.is_dir() else set()
        missing = sorted(source_files - snapshot_files)
        extra = sorted(snapshot_files - source_files)
        if missing:
            preview = ", ".join(missing[:5]) + ("…" if len(missing) > 5 else "")
            errors.append(_drift(f"packaging/runtime/{name}", f"{len(missing)} file(s) missing from snapshot: {preview}", hint))
        if extra:
            preview = ", ".join(extra[:5]) + ("…" if len(extra) > 5 else "")
            errors.append(_drift(f"packaging/runtime/{name}", f"{len(extra)} extra file(s) no longer in source: {preview}", hint))
        for relative in sorted(source_files & snapshot_files):
            if (source_path / relative).read_bytes() != (snapshot_path / relative).read_bytes():
                errors.append(_drift(f"packaging/runtime/{name}/{relative}", "content differs from source", hint))
    return errors


def validate_manifests(root: Path = ROOT) -> list[ValidationError]:
    """Require the hand-synced manifests to agree on the plugin name and version.

    Also enforces freshness of the generated packaging/runtime snapshot when it exists, so the
    local marketplace cannot silently install a stale role/skill surface.

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
    errors.extend(validate_runtime_freshness(root))
    return errors
