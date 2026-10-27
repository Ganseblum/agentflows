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


def _state(path: Path) -> dict[str, Any]:
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
    starts, ends = original.count(start_marker), original.count(end_marker)
    block = replacement_start + b"\n" + content
    if not block.endswith(b"\n"):
        block += b"\n"
    block += end_marker
    if starts == 0 and ends == 0:
        separator = b"\n" if original and not original.endswith(b"\n") else b""
        return original + separator + block + b"\n"
    if starts != 1 or ends != 1:
        raise WorkflowError(
            "invalid-markers", "Managed markers are incomplete or duplicated", 3
        )
    start, finish = original.index(start_marker), original.index(end_marker)
    if start >= finish:
        raise WorkflowError(
            "invalid-markers", "Managed markers are reversed or crossed", 3
        )
    # Markers must occupy full lines, so text that merely quotes one is not a managed block.
    for position, marker in [(start, start_marker), (finish, end_marker)]:
        before = original[position - 1 : position] if position else b"\n"
        after = original[position + len(marker) : position + len(marker) + 1]
        if before != b"\n" or after not in {b"", b"\n", b"\r"}:
            raise WorkflowError(
                "invalid-markers", "Managed markers must occupy complete lines", 3
            )
    return original[:start] + block + original[finish + len(end_marker) :]


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
    if bundle["expected"]["exists"] and original == desired:
        return envelope(
            "managed-apply",
            {
                "target": str(target),
                "action": "same",
                "backup": None,
                "sha256": bundle["desired_sha256"],
            },
            next_action="verify_host_loading_separately",
        )
    backup: Path | None = None
    temporary: Path | None = None
    try:
        if bundle["expected"]["exists"]:
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
        os.chmod(temporary, bundle["desired_mode"])
        # Recheck immediately before replacement. This is a single-file optimistic guard,
        # not a transaction or a lock against hostile concurrent processes.
        if _state(target) != bundle["expected"]:
            raise WorkflowError(
                "target-drift", "Target changed while preparing the replacement", 3
            )
        if bundle["expected"]["exists"]:
            os.replace(temporary, target)
        else:
            # A create must remain no-overwrite even if another writer races after the
            # final state check. The fully written temporary file lives on this filesystem.
            try:
                os.link(temporary, target)
            except FileExistsError as exc:
                raise WorkflowError("target-drift", "Target appeared after preview", 3) from exc
            temporary.unlink()
        temporary = None
        state = _state(target)
        if (
            state.get("sha256") != bundle["desired_sha256"]
            or state.get("mode") != bundle["desired_mode"]
        ):
            raise WorkflowError(
                "readback-failed",
                f"Replacement verification failed; backup={backup}",
                1,
            )
    except OSError as exc:
        raise WorkflowError(
            "managed-write-failed", f"Write failed; backup={backup}: {exc}", 1
        ) from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return envelope(
        "managed-apply",
        {
            "target": str(target),
            "action": "replace" if bundle["expected"]["exists"] else "create",
            "backup": str(backup) if backup else None,
            "sha256": bundle["desired_sha256"],
        },
        next_action="verify_host_loading_separately",
    )
