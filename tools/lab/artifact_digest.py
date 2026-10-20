#!/usr/bin/env python3
"""Compute a deterministic SHA-256 digest for an Agentflow source tree.

The digest covers normalized relative POSIX paths, regular-file mode bits, byte size,
and file content hashes. Symlinks are rejected so a candidate cannot silently change
the artifact through an external target. Git metadata and generated Python caches are
excluded by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_EXCLUDES = {".git", "__pycache__"}


def should_exclude(relative: Path, excludes: set[str]) -> bool:
    return any(part in excludes for part in relative.parts)


def build_manifest(root: Path, excludes: set[str]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if should_exclude(relative, excludes):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed in an artifact: {relative.as_posix()}")
        if not path.is_file():
            continue
        data = path.read_bytes()
        # Git preserves only the executable bit, not the full mode: recording the whole
        # S_IMODE made the "deterministic" digest depend on the creating umask (0644 vs
        # 0664 for the same commit on two machines). Normalize to exec-bit / no-exec-bit.
        mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
        entries.append(
            {
                "path": relative.as_posix(),
                "mode": format(mode, "04o"),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    if not entries:
        raise ValueError("artifact root contains no regular files")
    return entries


def digest_manifest(manifest: list[dict[str, object]]) -> str:
    encoded = "".join(
        f"{item['path']}\0{item['mode']}\0{item['size']}\0{item['sha256']}\n" for item in manifest
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--manifest-output")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    excludes = DEFAULT_EXCLUDES | set(args.exclude)
    try:
        manifest = build_manifest(root, excludes)
        digest = digest_manifest(manifest)
    except (OSError, ValueError) as exc:
        print(f"artifact digest failed: {exc}", file=sys.stderr)
        return 1
    if args.manifest_output:
        output = Path(args.manifest_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps({"root": str(root), "digest": digest, "files": manifest}, indent=2) + "\n",
            encoding="utf-8",
        )
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
