"""Runtime payload inventory and explicit local-host installation adapters."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .snapshots import WorkflowError, no_symlinks

RUNTIME_DIRECTORIES = (
    "agents", "skills", ".zcode-plugin", ".claude-plugin", ".codex-plugin", ".qoder-plugin",
)
RUNTIME_FILES = ("plugin.json", "marketplace.json")
# Codex's existing local source is the whole checkout. These roots are explicitly
# outside the plugin payload; extra files *inside* a declared runtime root fail.
CODEX_SOURCE_EXTRAS = frozenset({
    ".git", ".gitignore", ".mypy_cache", ".ruff_cache", ".venv", ".workbuddy", ".zcode",
    ".workbuddy-ai", ".agentflow-records.sqlite3", "AGENTS.md", "CHANGELOG.md",
    "README.md", "index.md", "docs", "packaging", "references",
})


def read_object(path: Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def inventory(root: Path, *, codex_source: bool = False) -> dict[str, Any]:
    root = no_symlinks(root)
    if not root.is_dir():
        raise ValueError(f"Payload directory is missing: {root}")
    expected_roots = set(RUNTIME_DIRECTORIES) | set(RUNTIME_FILES)
    names = {p.name for p in root.iterdir()}
    missing = expected_roots - names
    extra = names - expected_roots - (CODEX_SOURCE_EXTRAS if codex_source else set())
    if missing or extra:
        raise ValueError(f"Payload roots missing={sorted(missing)} extra={sorted(extra)}")
    entries: dict[str, Any] = {}
    for name in RUNTIME_DIRECTORIES:
        directory = no_symlinks(root / name)
        if not directory.is_dir():
            raise ValueError(f"Runtime directory required: {name}")
        for path in sorted(directory.rglob("*")):
            rel = path.relative_to(root).as_posix()
            path = no_symlinks(path)
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError(f"Regular runtime file required: {rel}")
            entries[rel] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "executable": stat.S_IMODE(path.stat().st_mode) & 0o111}
    for name in RUNTIME_FILES:
        path = no_symlinks(root / name)
        if not path.is_file():
            raise ValueError(f"Regular runtime file required: {name}")
        entries[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "executable": stat.S_IMODE(path.stat().st_mode) & 0o111}
    version = read_object(root / "plugin.json").get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("Plugin version is missing")
    return {"schema_version": 1, "version": version, "files": entries}


def verify_inventory(expected: dict[str, Any], root: Path, *, codex_source: bool = False) -> None:
    actual = inventory(root, codex_source=codex_source)
    a, b = expected["files"], actual["files"]
    missing, extra = sorted(a.keys() - b.keys()), sorted(b.keys() - a.keys())
    changed = sorted(key for key in a.keys() & b.keys() if a[key] != b[key])
    for label, paths in (("MISSING", missing), ("EXTRA", extra), ("CHANGED", changed)):
        for path in paths:
            print(f"{label} {path}")
    if missing or extra or changed or actual["version"] != expected["version"]:
        raise WorkflowError("installation-mismatch", f"Installed payload differs: version={actual['version']}, "
                            f"expected={expected['version']}, missing={len(missing)}, "
                            f"extra={len(extra)}, changed={len(changed)}", 1)
    print(f"PASS payload {actual['version']}: {len(a)}/{len(a)} files, bytes and execute bits match")


def command(argv: list[str], *, cwd: Path | None = None) -> str:
    print("$ " + " ".join(argv), flush=True)
    result = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=90)
    print(result.stdout, end="", flush=True)
    print(f"exit={result.returncode}", flush=True)
    if result.returncode:
        raise ValueError(f"Command failed ({result.returncode}): {argv[0]}")
    return result.stdout


def zcode_command() -> list[str]:
    override = os.environ.get("AGENTFLOW_ZCODE_CLI")
    if override:
        return [override]
    app = Path("/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs")
    if app.is_file():
        return ["node", str(app)]
    if shutil.which("zcode"):
        return ["zcode"]
    raise ValueError("ZCode CLI is unavailable")


def zcode_market(home: Path, market: str, plugin: str, repo: Path) -> str:
    data = read_object(home / ".zcode/cli/plugins/known_marketplaces.json")
    matches = [m for m in data.get("marketplaces", []) if m.get("id") == market]
    if len(matches) != 1:
        raise ValueError(f"One configured marketplace required: {market}")
    source = matches[0].get("source", {})
    kind = source.get("source")
    if kind == "directory":
        source_root = Path(source["path"]).expanduser().resolve()
        catalog = read_object(source_root / "marketplace.json")
        entries = [p for p in catalog.get("plugins", []) if p.get("name") == plugin]
        if len(entries) != 1 or not isinstance(entries[0].get("source"), str):
            raise ValueError("One local plugin entry with a relative source is required")
        declared = entries[0]["source"]
        if Path(declared).is_absolute() or ".." in Path(declared).parts:
            raise ValueError("Marketplace plugin source escapes its root")
        if (source_root / declared).resolve() != (repo / "packaging/runtime").resolve():
            raise ValueError("ZCode marketplace does not point at this repository runtime")
        return "local"
    if kind in {"git", "github"}:
        remote = command(["git", "-C", str(repo), "remote", "get-url", "origin"]).strip()
        url = source.get("url") if kind == "git" else "https://github.com/" + source["repo"] + ".git"
        if remote.removesuffix(".git") != str(url).removesuffix(".git"):
            raise ValueError("Configured Git marketplace differs from repository origin")
        return "remote"
    raise ValueError(f"Unsupported marketplace source: {kind}")


def upgrade(host: str, repo: Path, market: str, plugin: str, mode: str, dry_run: bool) -> None:
    repo = repo.resolve()
    home = Path.home()
    if read_object(repo / "plugin.json").get("name") != plugin:
        raise ValueError("Requested plugin differs from this source repository")
    if host == "codex":
        listing = command(["codex", "plugin", "marketplace", "list"])
        roots = [line.split(None, 1)[1].strip() for line in listing.splitlines()
                 if len(line.split(None, 1)) == 2 and line.split(None, 1)[0] == market]
        if len(roots) != 1 or (Path(roots[0]) / "plugins" / plugin).resolve() != repo:
            raise ValueError("Codex local marketplace does not point at this repository")
        catalog_path = Path(roots[0]) / ".agents/plugins/marketplace.json"
        if catalog_path.is_file():
            catalog = read_object(catalog_path)
            entries = [p for p in catalog.get("plugins", []) if p.get("name") == plugin]
            if len(entries) != 1:
                raise ValueError("Codex plugin catalog entry is missing or ambiguous")
        actual_mode, cli = "local", ["codex"]
    else:
        actual_mode, cli = zcode_market(home, market, plugin, repo), zcode_command()
    if mode != "auto" and actual_mode != mode:
        raise ValueError(f"Requested mode={mode}, configured source={actual_mode}; source not changed")
    print(f"Host={host}, marketplace={market}, source={actual_mode}, repository={repo}")
    if actual_mode == "remote":
        dirty = command(["git", "-C", str(repo), "status", "--porcelain"])
        if dirty.strip():
            raise ValueError("Remote installation requires a clean committed source")
        head = command(["git", "-C", str(repo), "rev-parse", "HEAD"]).strip()
        upstream = command(["git", "-C", str(repo), "rev-parse", "@{u}"]).strip()
        if head != upstream:
            raise ValueError("Remote source is not the current upstream; no push is performed")
    if dry_run:
        print("dry-run: source checked; no build, marketplace refresh or installation performed")
        return
    command([sys.executable, str(repo / "packaging/build_runtime.py")], cwd=repo)
    expected_root = repo / "packaging/runtime"
    expected = inventory(expected_root)
    version = expected["version"]
    if host == "zcode":
        command(cli + ["plugins", "marketplace", "update", market], cwd=repo)
        cache_catalog = home / ".zcode/cli/plugins/marketplaces" / market / "marketplace.json"
        if cache_catalog.is_file():
            catalog = read_object(cache_catalog)
            entries = [p for p in catalog.get("plugins", []) if p.get("name") == plugin]
            if len(entries) != 1 or entries[0].get("version") != version:
                raise ValueError("Refreshed marketplace does not contain the expected plugin version")
        command(cli + ["plugins", "update", plugin + "@" + market], cwd=repo)
        registry = read_object(home / ".zcode/cli/plugins/installed_plugins.json")
        records = [p for p in registry.get("plugins", []) if p.get("id") == plugin + "@" + market]
        if len(records) != 1 or records[0].get("version") != version:
            raise ValueError("Installed ZCode registration does not match the requested version")
        installed = Path(records[0]["installPath"])
        cache_parent = (home / ".zcode/cli/plugins/cache" / market / plugin).resolve()
        if installed.resolve().parent != cache_parent or installed.name != version:
            raise ValueError("Installed ZCode path is outside the configured plugin cache")
    else:
        command(cli + ["plugin", "add", plugin + "@" + market], cwd=repo)
        installed = home / ".codex/plugins/cache" / market / plugin / version
    verify_inventory(expected, installed, codex_source=host == "codex")
    verify_inventory(expected, expected_root)
    # The generator copy is not enough: source changes during host installation
    # must also invalidate the claimed result.
    verify_inventory(expected, repo, codex_source=True)
    print(f"Installed payload verified: {installed}")
    print("Session loading is unverified; open a new session (ZCode may require restart).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    compare = commands.add_parser("compare")
    compare.add_argument("--expected-tree", required=True)
    compare.add_argument("--installed", required=True)
    compare.add_argument("--codex-source", action="store_true")
    for host in ("codex", "zcode"):
        sub = commands.add_parser("upgrade-" + host)
        sub.add_argument("--repo", required=True)
        sub.add_argument("--marketplace", default="personal" if host == "codex" else "agentflow-local")
        sub.add_argument("--plugin", default="agentflow")
        sub.add_argument("--mode", choices=("auto", "local", "remote"), default="auto")
        sub.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.operation == "compare":
            expected = inventory(Path(args.expected_tree))
            verify_inventory(expected, Path(args.installed), codex_source=args.codex_source)
        else:
            upgrade(args.operation.removeprefix("upgrade-"), Path(args.repo),
                    args.marketplace, args.plugin, args.mode, args.dry_run)
    except (WorkflowError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL installation: {exc}", file=sys.stderr)
        return 1
    return 0
