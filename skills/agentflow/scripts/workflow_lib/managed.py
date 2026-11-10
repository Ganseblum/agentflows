"""Single-file managed previews with stale-input checks and atomic replacement."""

from __future__ import annotations

import base64
import hashlib
import os
import stat
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .snapshots import (
    WorkflowError,
    envelope,
    fingerprint,
    no_symlinks,
    read_json,
    write_json_new,
)


def file_state(path: Path | str) -> dict[str, Any]:
    """Capture the optimistic single-file guard without following user symlinks."""
    path = no_symlinks(path)
    if not path.exists():
        return {"exists": False}
    if not path.is_file():
        raise WorkflowError(
            "invalid-target", f"Regular target file required: {path}", 3
        )
    data = path.read_bytes()
    return {
        "exists": True,
        "mode": stat.S_IMODE(path.stat().st_mode),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _state(path: Path) -> dict[str, Any]:
    """Compatibility alias for existing managed-preview callers."""
    return file_state(path)


def locate_managed_block(
    original: bytes, begin: bytes, end: bytes, *,
    begin_prefix: bytes | None = None, owner: bytes | None = None,
) -> tuple[int, int] | None:
    """Locate one complete owned block; offsets exclude its trailing newline.

    Exact markers retain the CLI contract. A marker family (begin_prefix) pairs
    each owner's begin with the shared end, so foreign blocks do not inflate the
    owned end count. Malformed, nested and duplicate blocks fail closed.
    """
    markers = [begin, end] + ([begin_prefix] if begin_prefix is not None else [])
    if any(not value or b"\n" in value or b"\r" in value for value in markers):
        raise WorkflowError("invalid-markers", "Markers must be nonempty single lines", 3)
    if begin == end or begin in end or end in begin:
        raise WorkflowError("invalid-markers", "Markers cannot overlap", 3)
    if owner is not None and (not owner or begin_prefix is None):
        raise WorkflowError("invalid-markers", "An owner requires a begin marker family", 3)
    opened: tuple[int, bool] | None = None
    found: tuple[int, int] | None = None
    offset = 0
    # Split only on LF: bytes.splitlines() also splits user control characters.
    for raw in original.split(b"\n"):
        line = raw[:-1] if raw.endswith(b"\r") else raw
        is_begin = line.startswith(begin_prefix) if begin_prefix is not None else line == begin
        if is_begin:
            if begin_prefix is not None and begin.endswith(b"-->") and not line.endswith(b"-->"):
                raise WorkflowError("invalid-markers", "Managed begin marker is incomplete", 3)
            if opened is not None:
                raise WorkflowError("invalid-markers", "Managed blocks cannot be nested", 3)
            owned = owner in line if owner is not None else line == begin
            opened = (offset, owned)
        elif line == end:
            if opened is None:
                raise WorkflowError("invalid-markers", "Managed end marker has no begin", 3)
            start, owned = opened
            if owned:
                if found is not None:
                    raise WorkflowError("invalid-markers", "Owned managed block is duplicated", 3)
                found = (start, offset + len(line))
            opened = None
        elif begin in line or end in line or (begin_prefix is not None and begin_prefix in line):
            raise WorkflowError("invalid-markers", "Managed markers must occupy complete lines", 3)
        offset += len(raw) + 1
    if opened is not None:
        raise WorkflowError("invalid-markers", "Managed begin marker has no end", 3)
    return found


def _replacement(
    original: bytes, content: bytes, begin: str | None, end: str | None,
    new_begin: str | None = None,
) -> bytes:
    if begin is None and end is None:
        if new_begin is not None:
            raise WorkflowError("invalid-markers", "A replacement begin marker needs existing markers")
        return content
    if not begin or not end or begin == end or "\n" in begin or "\n" in end:
        raise WorkflowError(
            "invalid-markers", "Two distinct single-line markers are required"
        )
    start_marker, end_marker = begin.encode(), end.encode()
    replacement_start = start_marker
    if new_begin is not None:
        if not new_begin or "\n" in new_begin or "\r" in new_begin:
            raise WorkflowError("invalid-markers", "Replacement begin must be one complete line")
        replacement_start = new_begin.encode()
        if replacement_start in end_marker or end_marker in replacement_start:
            raise WorkflowError("invalid-markers", "Replacement begin and end markers overlap")
    if start_marker in end_marker or end_marker in start_marker:
        raise WorkflowError("invalid-markers", "Markers cannot contain one another")
    if start_marker in content or end_marker in content or replacement_start in content:
        raise WorkflowError(
            "nested-markers", "--content must contain only the managed block body", 3
        )
    family = b"<!-- agentflow:begin " if start_marker.startswith(b"<!-- agentflow:begin ") else None
    span = locate_managed_block(original, start_marker, end_marker, begin_prefix=family)
    block = replacement_start + b"\n" + content
    if not block.endswith(b"\n"):
        block += b"\n"
    block += end_marker
    if span is None:
        separator = b"\n" if original and not original.endswith(b"\n") else b""
        return original + separator + block + b"\n"
    start, finish = span
    return original[:start] + block + original[finish:]


def preview_managed(
    target: Path | str,
    content: Path | str,
    output: Path | str,
    begin_marker: str | None = None,
    end_marker: str | None = None,
    new_begin_marker: str | None = None,
) -> dict[str, Any]:
    target, content, output = (
        no_symlinks(target),
        no_symlinks(content),
        no_symlinks(output),
    )
    if target == content or output in {target, content}:
        raise WorkflowError(
            "input-output-overlap", "Target, content and preview must be distinct", 3
        )
    if not target.parent.is_dir() or not content.is_file():
        raise WorkflowError("missing-path", "Target parent and content file must exist")
    expected = _state(target)
    original = target.read_bytes() if expected["exists"] else b""
    content_bytes = content.read_bytes()
    desired = _replacement(original, content_bytes, begin_marker, end_marker, new_begin_marker)
    bundle: dict[str, Any] = {
        "schema_version": 1,
        "kind": "managed",
        "target": str(target),
        "expected": expected,
        "content_source": str(content),
        "content_sha256": hashlib.sha256(content_bytes).hexdigest(),
        "begin_marker": begin_marker,
        "end_marker": end_marker,
        "new_begin_marker": new_begin_marker,
        "desired_base64": base64.b64encode(desired).decode("ascii"),
        "desired_sha256": hashlib.sha256(desired).hexdigest(),
        "desired_mode": expected.get("mode", 0o644),
    }
    bundle["fingerprint"] = fingerprint(bundle)
    write_json_new(output, bundle)
    action = (
        "create"
        if not expected["exists"]
        else "same"
        if original == desired
        else "replace"
    )
    return envelope(
        "managed-preview",
        {
            "fingerprint": bundle["fingerprint"],
            "preview": str(output),
            "target": str(target),
            "action": action,
            "original": expected,
            "desired_sha256": bundle["desired_sha256"],
        },
        next_action="apply_same_preview_if_authorized",
    )


def apply_managed(preview: Path | str, expected_fingerprint: str) -> dict[str, Any]:
    bundle = read_json(no_symlinks(preview))
    unsigned = {key: value for key, value in bundle.items() if key != "fingerprint"}
    actual_fingerprint = fingerprint(unsigned)
    if bundle.get(
        "fingerprint"
    ) != actual_fingerprint or expected_fingerprint.removeprefix(
        "sha256:"
    ) != actual_fingerprint.removeprefix("sha256:"):
        raise WorkflowError(
            "fingerprint-mismatch", "Managed preview fingerprint does not match", 3
        )
    if bundle.get("schema_version") != 1 or bundle.get("kind") != "managed":
        raise WorkflowError("invalid-preview", "Unsupported managed preview")
    target, source = (
        no_symlinks(bundle["target"]),
        no_symlinks(bundle["content_source"]),
    )
    if _state(target) != bundle["expected"]:
        raise WorkflowError(
            "target-drift", "Target content, existence or mode changed since preview", 3
        )
    if (
        not source.is_file()
        or hashlib.sha256(source.read_bytes()).hexdigest() != bundle["content_sha256"]
    ):
        raise WorkflowError(
            "content-drift", "Proposed content changed since preview", 3
        )
    try:
        desired = base64.b64decode(bundle["desired_base64"], validate=True)
    except (ValueError, TypeError) as exc:
        raise WorkflowError(
            "invalid-preview", "Preview content is not valid base64"
        ) from exc
    if hashlib.sha256(desired).hexdigest() != bundle["desired_sha256"]:
        raise WorkflowError(
            "invalid-preview", "Preview content hash is inconsistent", 3
        )
    original = target.read_bytes() if bundle["expected"]["exists"] else b""
    regenerated = _replacement(
        original, source.read_bytes(), bundle["begin_marker"], bundle["end_marker"],
        bundle.get("new_begin_marker"),
    )
    if regenerated != desired:
        raise WorkflowError(
            "invalid-preview", "Managed replacement does not match the preview", 3
        )
    result = write_managed_file(target, desired, bundle["expected"], bundle["desired_mode"])
    return envelope(
        "managed-apply", result, next_action="verify_host_loading_separately",
    )


def write_managed_file(
    target: Path | str, desired: bytes, expected: dict[str, Any],
    mode: int | None = None,
) -> dict[str, Any]:
    """Write one preflighted file with backup and an optimistic atomic guard.

    This is shared by init and v1 managed previews. It deliberately creates no
    preview artifact and is not a multi-file transaction or a concurrent lock.
    The caller creates missing parent directories after its full preflight.
    """
    target = no_symlinks(target)
    if file_state(target) != expected:
        raise WorkflowError("target-drift", f"Target changed before write: {target}", 3)
    if not target.parent.is_dir():
        raise WorkflowError("missing-path", f"Target parent must exist: {target.parent}")
    original = target.read_bytes() if expected["exists"] else b""
    desired_sha256 = hashlib.sha256(desired).hexdigest()
    desired_mode = expected.get("mode", 0o644) if mode is None else mode
    if expected["exists"] and original == desired and expected["mode"] == desired_mode:
        return {"target": str(target), "action": "same", "backup": None, "sha256": desired_sha256}
    backup: Path | None = None
    temporary: Path | None = None
    try:
        if expected["exists"]:
            backup = target.with_name(
                target.name + ".agentflow-backup-" + uuid.uuid4().hex
            )
            descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        descriptor, name = tempfile.mkstemp(
            prefix=".agentflow-write-", dir=target.parent
        )
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(desired)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, desired_mode)
        # Single-file optimistic guard; not a lock against hostile processes.
        if file_state(target) != expected:
            raise WorkflowError("target-drift", "Target changed while preparing the replacement", 3)
        if expected["exists"]:
            os.replace(temporary, target)
        else:
            try:
                os.link(temporary, target)
            except FileExistsError as exc:
                raise WorkflowError("target-drift", "Target appeared after preview", 3) from exc
            temporary.unlink()
        temporary = None
        state = file_state(target)
        if state.get("sha256") != desired_sha256 or state.get("mode") != desired_mode:
            raise WorkflowError("readback-failed", "Replacement verification failed", 1)
    except WorkflowError as exc:
        raise WorkflowError(exc.kind, f"{exc}; target={target}; backup={backup}", exc.code) from exc
    except OSError as exc:
        raise WorkflowError(
            "managed-write-failed", f"Write failed; target={target}; backup={backup}: {exc}", 1
        ) from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return {
        "target": str(target),
        "action": "replace" if expected["exists"] else "create",
        "backup": str(backup) if backup else None,
        "sha256": desired_sha256,
    }
