#!/usr/bin/env python3
"""Isolated, standard-library CLI regressions for the 0.41.0 audit fixes.

Run from any cwd. --output must be NEW; reports never overwrite an earlier run.
--case accepts an exact Gxx group, an exact native name, or a shell glob; repeat
it to select a union. Missing new interfaces are blocked, never valid baseline
reds. This suite does not approve rule semantics, host loading, or browser apps.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Callable

PYTHON = str(Path(sys.executable).resolve())
SCRIPTS = Path("skills/agentflow/scripts")
INDEX = "# Fixture hub\n\n| 批次 | 一句话范围 | 进度板 |\n| --- | --- | --- |\n"
OLD = b"OLD_REVIEWED\n"
NEW = b"NEW_UNREVIEWED\n"
END = b"<!-- agentflow:end -->"
OWN = b"managed by init_workspace.py"
NONZERO = "nonzero"


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_state(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        return {"kind": "symlink", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "missing"}
    if path.is_dir():
        return {"kind": "directory"}
    data = path.read_bytes()
    return {"kind": "file", "bytes": len(data), "sha256": digest(data),
            "mode": stat.S_IMODE(path.stat().st_mode)}


def tree_state(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if not root.exists():
        return result
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(parent) / name
            if ".git" in path.relative_to(root).parts:
                continue
            result[path.relative_to(root).as_posix()] = file_state(path)
    return result


def copy_path(source: Path, target: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"Source symlink rejected: {source}")
    if source.is_dir():
        target.mkdir(parents=True, exist_ok=True)
        for child in sorted(source.iterdir()):
            if child.name != "__pycache__" and child.suffix != ".pyc":
                copy_path(child, target / child.name)
    elif source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    else:
        raise ValueError(f"Required regular source missing: {source}")


def payload_names(source: Path) -> list[str]:
    """Read the installer's declarations, without importing tested code here.

    Old sources keep these declarations in the builder. There is no independent
    hard-coded inventory in this test; the installer remains the one authority.
    """
    installer = source / SCRIPTS / "workflow_lib/installation.py"
    definition = installer if installer.is_file() else source / "packaging/build_runtime.py"
    module = ast.parse(definition.read_text(encoding="utf-8"), filename=str(definition))
    values: dict[str, list[str]] = {}
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {
                    "RUNTIME_DIRECTORIES", "RUNTIME_FILES", "RUNTIME_SUBTREES"
                }:
                    values[target.id] = list(ast.literal_eval(node.value))
    if not {"RUNTIME_DIRECTORIES", "RUNTIME_FILES"} <= values.keys():
        raise ValueError(f"No declared payload inventory in {definition}")
    names = [n for group in values.values() for n in group]
    # Independent product contract: packaging/README.md promises these roots.
    # Do not let expected and actual silently omit the same implementation root.
    contract_roots = {"agents", "skills", ".zcode-plugin", ".claude-plugin",
                      ".codex-plugin", ".qoder-plugin", "plugin.json", "marketplace.json"}
    if set(names) != contract_roots or len(names) != len(contract_roots):
        raise Failed(f"Runtime declarations violate frozen payload contract: {names!r}")
    if any(Path(n).is_absolute() or ".." in Path(n).parts for n in names):
        raise ValueError("Payload inventory contains escaping path")
    return names


class Blocked(Exception):
    """Missing interface/environment, not a product regression observation."""


class Failed(AssertionError):
    pass


class Case:
    def __init__(self, group: str, name: str, source: Path, temp: Path, evidence: Path,
                 tools: dict[str, str]) -> None:
        self.group, self.name, self.source = group, name, source
        self.root = temp / name
        self.root.mkdir()
        self.logs = evidence / name
        self.logs.mkdir()
        self.home, self.cwd, self.bin = (self.root / n for n in ("home", "cwd", "bin"))
        for path in (self.home, self.cwd, self.bin):
            path.mkdir()
        self.commands: list[dict[str, Any]] = []
        self.facts: list[dict[str, Any]] = []
        self.groups: dict[int, set[int]] = {}
        self.sequence = 0
        self.tools = tools
        # Only known tools enter PATH. In particular no real codex/zcode is reachable.
        for name_, executable in {**tools, "python3": PYTHON}.items():
            if executable:
                (self.bin / name_).symlink_to(executable)
        stub = (f"#!{PYTHON} -B\nimport json,os,pathlib,sys\n"
                "p=pathlib.Path(os.environ['AF_STUB_CALLS'])\n"
                "with p.open('a') as f: f.write(json.dumps(sys.argv)+'\\n')\n"
                "raise SystemExit(97)\n")
        for name_ in ("codex", "zcode", "qoder", "node"):
            if name_ == "node":
                continue
            self.stub(name_, stub)
        calls = self.root / "stub-calls.jsonl"
        calls.write_bytes(b"")
        self.env = {
            "HOME": str(self.home), "PATH": str(self.bin), "TMPDIR": str(self.root),
            "XDG_CACHE_HOME": str(self.home / "cache"),
            "XDG_CONFIG_HOME": str(self.home / "config"),
            "XDG_DATA_HOME": str(self.home / "data"),
            "CODEX_HOME": str(self.home / ".codex"),
            "ZCODE_HOME": str(self.home / ".zcode"),
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "GIT_AUTHOR_NAME": "Regression Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Regression Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
            "AGENTFLOW_ZCODE_CLI": str(self.bin / "zcode"),
            "AF_STUB_CALLS": str(calls),
        }

    def stub(self, name: str, body: str) -> None:
        path = self.bin / name
        if path.is_symlink():
            path.unlink()
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def need(self, script: str, *tokens: str) -> None:
        path = self.source / SCRIPTS / script
        if not path.is_file():
            raise Blocked(f"Missing CLI: {script}")
        probe = self.cli(script, "--help")
        if probe.returncode:
            raise Blocked(f"{script} --help failed, native={probe.returncode}")
        text = (probe.stdout + probe.stderr).decode("utf-8", "replace")
        absent = [token for token in tokens if token not in text]
        if absent:
            raise Blocked(f"Interface absent in tested source: {script} {absent}")

    def run(self, argv: list[Any], expected: int | str | None = None,
            cwd: Path | None = None, timeout: float = 30,
            assert_exit: bool = True) -> subprocess.CompletedProcess[bytes]:
        args = [str(a) for a in argv]
        self.sequence += 1
        stem = f"{self.sequence:02d}"
        out, err = self.logs / (stem + ".stdout"), self.logs / (stem + ".stderr")
        start = time.monotonic()
        process: subprocess.Popen[bytes] | None = None
        expired = False
        with out.open("wb") as stdout, err.open("wb") as stderr:
            try:
                process = subprocess.Popen(args, cwd=cwd or self.cwd, env=self.env,
                                           stdin=subprocess.DEVNULL, stdout=stdout,
                                           stderr=stderr, start_new_session=True)
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    expired = True
                    self.kill_group(process.pid)
                    process.wait(timeout=5)
            except OSError as exc:
                stderr.write((type(exc).__name__ + ": " + str(exc) + "\n").encode())
        code = process.returncode if process else None
        stdout_data, stderr_data = out.read_bytes(), err.read_bytes()
        record = {"argv": args, "cwd": str(cwd or self.cwd), "expected_exit": expected,
                  "actual_exit": code, "watchdog_timeout": expired,
                  "duration_seconds": round(time.monotonic() - start, 4),
                  "stdout": str(out), "stderr": str(err),
                  "stdout_bytes": len(stdout_data), "stderr_bytes": len(stderr_data)}
        self.commands.append(record)
        dump(self.logs / (stem + ".json"), record)
        (self.logs / (stem + ".log")).write_bytes(
            ("$ " + shlex.join(args) + "\ncwd=" + record["cwd"] + "\nSTDOUT\n").encode()
            + stdout_data + b"\nSTDERR\n" + stderr_data
            + f"\nexpected={expected!r} native_exit={code!r} watchdog={expired}\n".encode())
        if process is None or expired:
            raise Failed(f"Command unavailable/watchdog: native={code}, {args!r}")
        result = subprocess.CompletedProcess(args, code, stdout_data, stderr_data)
        if expected is not None and assert_exit:
            self.exit(result, expected)
        return result

    @staticmethod
    def kill_group(pgid: int) -> None:
        if pgid <= 1 or pgid == os.getpgrp():
            raise ValueError(f"Refuse unsafe process group: {pgid}")
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def cli(self, script: str, *args: Any, expected: int | str | None = None,
            timeout: float = 30, assert_exit: bool = True) -> subprocess.CompletedProcess[bytes]:
        return self.run([PYTHON, "-B", self.source / SCRIPTS / script, *args],
                        expected=expected, timeout=timeout, assert_exit=assert_exit)

    def exit(self, result: subprocess.CompletedProcess[bytes], expected: int | str) -> None:
        # Attach the contract even when a caller had to inspect output first.
        record = next(r for r in reversed(self.commands) if r["argv"] == result.args)
        record["expected_exit"] = expected
        stem = f"{self.commands.index(record) + 1:02d}"
        dump(self.logs / (stem + ".json"), record)
        with (self.logs / (stem + ".log")).open("ab") as stream:
            stream.write(f"assert_expected={expected!r} actual_native_exit={result.returncode}\n".encode())
        self.check((result.returncode != 0 if expected == NONZERO else result.returncode == expected),
                   "native exit", expected=expected, actual=result.returncode)

    def check(self, condition: bool, fact: str, **values: Any) -> None:
        row = {"fact": fact, **values, "pass": bool(condition)}
        self.facts.append(row)
        if not condition:
            first = self.commands[0]["actual_exit"] if self.commands else None
            detail = json.dumps(row, ensure_ascii=False)
            print(f"FAIL {self.group} {self.name}: {detail}; first_native_exit={first}", flush=True)
            raise Failed(detail)

    def bytes_equal(self, actual: bytes, expected: bytes, fact: str) -> None:
        if actual == expected:
            offset = None
        else:
            offset = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
                          min(len(actual), len(expected)))
        self.check(actual == expected, fact, expected_bytes=len(expected), actual_bytes=len(actual),
                   expected_sha256=digest(expected), actual_sha256=digest(actual),
                   first_difference=offset,
                   expected_at_difference=repr(expected[max(0, (offset or 0)-20):(offset or 0)+60]),
                   actual_at_difference=repr(actual[max(0, (offset or 0)-20):(offset or 0)+60]))

    def same_tree(self, path: Path, before: dict[str, Any], fact: str) -> None:
        after = tree_state(path)
        changes = [n for n in sorted(before.keys() | after.keys()) if before.get(n) != after.get(n)]
        self.check(not changes, fact, changed={n: {"expected": before.get(n), "actual": after.get(n)}
                                             for n in changes})

    def archive(self, path: Path, name: str) -> None:
        self.check(path.is_file(), "native artifact exists", path=str(path))
        shutil.copy2(path, self.logs / name)

    def cleanup(self) -> None:
        # A successful command's PID has already been reaped; never signal its
        # old group later. Only still-live PIDs from our fixture handshake can
        # authorize a group signal, and their command must name this case root.
        if self.groups:
            if self.tools.get("ps"):
                try:
                    table = self.run(["ps", "-A", "-o", "pid=,pgid=,stat=,command="], expected=0).stdout.decode()
                    for pgid, owned_pids in self.groups.items():
                        live = []
                        for line in table.splitlines():
                            parts = line.strip().split(None, 3)
                            if len(parts) == 4 and int(parts[1]) == pgid and not parts[2].startswith(("Z", "X")):
                                live.append((int(parts[0]), parts[3]))
                        if live:
                            if not any(pid in owned_pids and str(self.root) in command for pid, command in live):
                                raise Failed(f"Cannot establish ownership of live cleanup group {pgid}: {live}")
                            self.kill_group(pgid)
                except Exception:
                    for pgid in self.groups:
                        try:
                            self.kill_group(pgid)
                        except Exception:
                            pass
            else:
                for pgid in self.groups:
                    try:
                        self.kill_group(pgid)
                    except Exception:
                        pass
        shutil.rmtree(self.root)


def init(c: Case, target: Path, *args: Any, expected: int | str | None = None,
         assert_exit: bool = True):
    return c.cli("init_workspace.py", target, *args, expected=expected, assert_exit=assert_exit)


def own_span(data: bytes) -> tuple[int, int]:
    for match in re.finditer(rb"<!-- agentflow:begin [^\r\n]*-->", data):
        if OWN in match.group():
            end = data.find(END, match.end())
            if end != -1:
                return match.start(), end + len(END)
    raise Failed("Fixture contains no complete owned managed block")


def init_carrier_bytes(c: Case) -> None:
    target = c.root / "repo"
    target.mkdir()
    init(c, target, "--hosts", "cursor,claude", expected=0)
    c.need("init_workspace.py", "--refresh-assets")
    watched: dict[Path, tuple[bytes, bytes]] = {}
    for rel in (".cursor/rules/agentflow.mdc", "CLAUDE.md"):
        path = target / rel
        original = path.read_bytes()
        if rel.endswith(".mdc"):
            begin, end = own_span(original)
            prefix = original[:begin].replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            prefix += b"USER_HEAD  \r\n"
            suffix = b"\r\nUSER_TAIL  \r\nNO_FINAL_NEWLINE"
            path.write_bytes(prefix + original[begin:end] + suffix)
            watched[path] = prefix, suffix
        else:
            prefix, suffix = b"USER_HEAD  \r\n", b"\r\nUSER_TAIL  \r\nNO_FINAL_NEWLINE"
            path.write_bytes(prefix + original + suffix)
            watched[path] = prefix, suffix
    init(c, target, "--hosts", "cursor,claude", expected=0)
    for path, (prefix, suffix) in watched.items():
        data = path.read_bytes()
        c.bytes_equal(data[:len(prefix)], prefix, f"{path.name} prefix/CRLF")
        c.bytes_equal(data[-len(suffix):], suffix, f"{path.name} suffix/CRLF/no-final-newline")
    init(c, target, "--check", expected=0)
    before = tree_state(target)
    init(c, target, "--hosts", "cursor,claude", expected=0)
    c.same_tree(target, before, "repeat installation has identical bytes/modes")


def init_symlink_file(c: Case) -> None:
    target, outside = c.root / "repo", c.root / "outside"
    target.mkdir(); outside.mkdir()
    sentinel = outside / "AGENTS.md"
    sentinel.write_bytes(b"OUTSIDE\r\n  KEEP\n")
    (target / "AGENTS.md").symlink_to(sentinel)
    before, outside_before = tree_state(target), tree_state(outside)
    result = init(c, target, "--hosts", "zcode")
    c.same_tree(outside, outside_before, "symlink file never writes outside")
    c.same_tree(target, before, "symlink refusal is zero write")
    c.exit(result, NONZERO)


def init_symlink_ancestor(c: Case) -> None:
    target, outside = c.root / "repo", c.root / "outside"
    target.mkdir(); outside.mkdir()
    (outside / "KEEP").write_bytes(b"OUTSIDE\n")
    (target / ".cursor").symlink_to(outside, target_is_directory=True)
    before, external = tree_state(target), tree_state(outside)
    result = init(c, target, "--hosts", "cursor")
    c.same_tree(outside, external, "symlink ancestor never writes outside")
    c.same_tree(target, before, "ancestor refusal is zero write")
    c.exit(result, NONZERO)


def init_conflict_lifecycle(c: Case) -> None:
    target = c.root / "repo"; target.mkdir()
    init(c, target, "--hosts", "zcode", expected=0)
    asset = target / ".agentflow/standards/server-side.md"
    manifest = target / ".agentflow/manifest.json"
    installed = asset.read_bytes(); old_manifest = manifest.read_bytes()
    asset.write_bytes(installed + b"\nUSER_EDIT\r\n")
    before = tree_state(target)
    init(c, target, "--check", expected=NONZERO)
    result = init(c, target, "--hosts", "zcode")
    # Check preservation before exit status so a nonzero partial install is red too.
    c.bytes_equal(manifest.read_bytes(), old_manifest, "conflict preserves OLD manifest bytes")
    c.same_tree(target, before, "asset conflict is atomic zero write")
    c.exit(result, NONZERO)
    init(c, target, "--check", expected=NONZERO)
    init(c, target, "--check", expected=NONZERO)
    init(c, target, "--hosts", "zcode", "--refresh-assets", expected=0)
    c.bytes_equal(asset.read_bytes(), installed, "explicit refresh restores canonical asset")
    init(c, target, "--check", expected=0)


def init_foreign_block(c: Case) -> None:
    target = c.root / "repo"; target.mkdir()
    foreign = b"<!-- agentflow:begin v0 global -->\r\nFOREIGN  \r\n<!-- agentflow:end -->\r\n"
    path = target / "AGENTS.md"; path.write_bytes(foreign)
    init(c, target, "--hosts", "zcode", expected=0)
    first = path.read_bytes()
    init(c, target, "--hosts", "zcode", expected=0)
    second = path.read_bytes()
    c.check(first.count(OWN) == second.count(OWN) == 1, "owned blocks stay 1 -> 1",
            expected=[1, 1], actual=[first.count(OWN), second.count(OWN)])
    c.bytes_equal(second[:len(foreign)], foreign, "foreign first block preserves bytes")
    c.bytes_equal(second, first, "foreign block coexistence is idempotent")
    init(c, target, "--check", expected=0)


def init_claude_dependency(c: Case) -> None:
    target = c.root / "repo"; target.mkdir()
    init(c, target, "--hosts", "claude", expected=0)
    dependency = target / "AGENTS.md"
    c.check(dependency.is_file(), "claude-only creates AGENTS dependency", actual=file_state(dependency))
    c.check(b"@AGENTS.md" in (target / "CLAUDE.md").read_bytes(), "Claude pointer exists")
    init(c, target, "--check", expected=0)
    dependency.unlink()
    init(c, target, "--check", expected=NONZERO)


def git_repo(c: Case) -> Path:
    repo = c.root / "repo"; repo.mkdir()
    c.run(["git", "init", "-b", "feature-fixture", repo], expected=0)
    return repo


def commit_fixture(c: Case, repo: Path) -> str:
    c.run(["git", "-C", repo, "add", "."], expected=0)
    c.run(["git", "-C", repo, "commit", "--no-gpg-sign", "-m", "fixture"], expected=0)
    return c.run(["git", "-C", repo, "rev-parse", "HEAD"], expected=0).stdout.decode().strip()


def review_fixture(c: Case, committed: bool = False) -> tuple[Path, Path, Path, str | None]:
    repo = git_repo(c) if committed else c.root / "repo"
    repo.mkdir(exist_ok=True)
    (repo / "a.md").write_bytes(OLD)
    feature = c.root / "feature"; feature.mkdir()
    status_file = c.root / "tasks.txt"
    status_file.write_text("tasks: 1\nT01 | deps: - | status: ☑\n", encoding="utf-8")
    revision = commit_fixture(c, repo) if committed else None
    return repo, feature, status_file, revision


def snapshot(c: Case, repo: Path, feature: Path, *files: Any) -> Path:
    c.cli("review_snapshot.py", "--repo", repo, "--feature", feature,
          "--round", "1", "--files", *files, expected=0)
    return feature / "reviews/snapshot-1"


def brief(c: Case, repo: Path, revision: Any, tasks: Path, out: Path,
          *extra: Any, expected: int | str | None = None):
    return c.cli("gen_review_brief.py", "--repo", repo, "--files", "a.md",
                 "--out", out, "--reviewed-revision", revision, "--task-status", tasks,
                 *extra, expected=expected)


def review_snapshot_binding(c: Case) -> None:
    repo, feature, tasks, _ = review_fixture(c)
    frozen = snapshot(c, repo, feature, "a.md")
    (repo / "a.md").write_bytes(NEW)
    output = c.root / "brief.md"
    brief(c, repo, frozen, tasks, output, expected=0)
    content = output.read_bytes()
    c.check(OLD.strip() in content and NEW.strip() not in content, "snapshot brief inlines OLD only",
            expected="OLD_REVIEWED present; NEW_UNREVIEWED absent", actual=content.decode())
    c.bytes_equal((frozen / "a.md").read_bytes(), OLD, "snapshot remains frozen")
    c.archive(output, "brief.md")


def review_commit_binding(c: Case) -> None:
    repo, _, tasks, revision = review_fixture(c, committed=True)
    (repo / "a.md").write_bytes(NEW)
    output = c.root / "changed.md"
    brief(c, repo, revision, tasks, output, expected=0)
    data = output.read_bytes()
    c.check(OLD.strip() in data and NEW.strip() not in data, "commit brief reads committed OLD", actual=data.decode())
    c.archive(output, "changed.md")
    (repo / "a.md").unlink()
    output = c.root / "deleted.md"
    brief(c, repo, revision, tasks, output, expected=0)
    c.check(OLD.strip() in output.read_bytes(), "commit brief works after worktree deletion")
    c.archive(output, "deleted.md")


def review_corrupt_manifest(c: Case) -> None:
    repo, feature, tasks, _ = review_fixture(c)
    frozen = snapshot(c, repo, feature, "a.md")
    manifest = frozen / "MANIFEST.txt"
    original = manifest.read_bytes()
    output = c.root / "brief.md"; output.write_bytes(b"KEEP_EXISTING_BRIEF\n")
    for name, content in (("bad-hash", original.replace(digest(OLD).encode(), b"0" * 64)),
                          ("bad-count", original.replace(b"files: 1", b"files: 2")),
                          ("bad-line", original + b"CORRUPT MANIFEST ROW\n")):
        manifest.write_bytes(content)
        brief(c, repo, frozen, tasks, output, expected=NONZERO)
        c.bytes_equal(output.read_bytes(), b"KEEP_EXISTING_BRIEF\n", name + " preserves existing output")


def review_external_collision(c: Case) -> None:
    repo, feature, _, _ = review_fixture(c)
    files = []
    for name, content in (("one", b"FIRST\n"), ("two", b"SECOND\n")):
        path = c.root / name / "same.txt"; path.parent.mkdir(); path.write_bytes(content); files.append(path)
    result = c.cli("review_snapshot.py", "--repo", repo, "--feature", feature,
                   "--round", "1", "--files", *files)
    frozen = feature / "reviews/snapshot-1"
    if result.returncode:
        c.check(not frozen.exists(), "collision rejection leaves no partial snapshot")
        c.exit(result, NONZERO)
        return
    data = (frozen / "MANIFEST.txt").read_text(encoding="utf-8")
    rows = re.findall(r"^([0-9a-f]{64})\s+(\d+)\s+(.+)$", data, re.M)
    c.check(len(rows) == 2 and len({r[2] for r in rows}) == 2 and len({r[0] for r in rows}) == 2,
            "two external names keep two paths and two hashes", expected="2 distinct paths/hashes", actual=rows)
    copied = {(frozen / rel).read_bytes() for _, _, rel in rows}
    c.check(copied == {b"FIRST\n", b"SECOND\n"}, "external bytes both survive", actual=[repr(x) for x in copied])
    c.archive(frozen / "MANIFEST.txt", "MANIFEST.txt")


def task_map_closure(c: Case) -> None:
    c.need("gen_review_brief.py", "--task-ids")
    repo, feature, tasks, _ = review_fixture(c)
    frozen = snapshot(c, repo, feature, "a.md")
    text = ("tasks: 4\nT01 | deps: - | status: ☑\nT02 | deps: T01 | status: ☑\n"
            "T03 | deps: - | status: ☐\nT04 | deps: T02 | status: ☑\n")
    tasks.write_text(text, encoding="utf-8")
    output = c.root / "brief.md"
    brief(c, repo, frozen, tasks, output, "--task-ids", "T02", expected=0)
    c.check(output.is_file(), "selected completed closure ignores unrelated pending T03")
    c.archive(output, "brief.md")


def task_map_invalid_graph(c: Case) -> None:
    c.need("gen_review_brief.py", "--task-ids")
    repo, feature, tasks, _ = review_fixture(c)
    frozen = snapshot(c, repo, feature, "a.md")
    variants = {
        "missing": "tasks: 1\nT02 | deps: T01 | status: ☑\n",
        "pending": "tasks: 2\nT01 | deps: - | status: ☐\nT02 | deps: T01 | status: ☑\n",
        "unknown": "tasks: 2\nT01 | deps: - | status: ☑\nT02 | deps: T01 | status: ☑\n",
        "cycle": ("tasks: 4\nT01 | deps: - | status: ☑\nT02 | deps: T01 | status: ☑\n"
                  "T03 | deps: T04 | status: ☑\nT04 | deps: T03 | status: ☑\n"),
    }
    for name, text in variants.items():
        tasks.write_text(text, encoding="utf-8")
        output = c.root / (name + ".md")
        brief(c, repo, frozen, tasks, output, "--task-ids", "T99" if name == "unknown" else "T02",
              expected=NONZERO)
        c.check(not output.exists(), "invalid task graph creates no brief", variant=name)


def hub(c: Case, name: str = "hub") -> Path:
    path = c.root / name; path.mkdir(); (path / "index.md").write_text(INDEX, encoding="utf-8")
    return path


def feature(c: Case, target: Path, *args: Any, slug: str = "demo", date: str = "2026-11-05",
            expected: int | str | None = None):
    return c.cli("new_feature.py", "--hub", target, "--slug", slug, "--date", date,
                 *args, expected=expected)


def feature_tree(path: Path) -> set[str]:
    return {p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file()}


def feature_tier_required(c: Case) -> None:
    c.need("new_feature.py", "--tier", "--tracks")
    target = hub(c); before = tree_state(target)
    feature(c, target, expected=NONZERO)
    c.same_tree(target, before, "tier must be explicit; no implicit full generation")
    feature(c, target, "--tier", "full", expected=NONZERO)
    c.same_tree(target, before, "full requires explicit tracks")


def feature_light(c: Case) -> None:
    c.need("new_feature.py", "--tier")
    target = hub(c)
    feature(c, target, "--tier", "light", expected=0)
    directory = target / "features/feature-2026-11-05-demo"
    files = feature_tree(directory)
    c.check(files == {"README.md"}, "light generates README only", expected=["README.md"], actual=sorted(files))
    c.check((target / "index.md").read_text().count("features/feature-2026-11-05-demo") == 2,
            "light registers one index row")
    before = tree_state(target)
    feature(c, target, "--tier", "light", expected=NONZERO)
    c.same_tree(target, before, "duplicate leaves existing feature and index unchanged")


def feature_full_be(c: Case) -> None:
    c.need("new_feature.py", "--tier", "--tracks")
    target = hub(c)
    feature(c, target, "--tier", "full", "--tracks", "be", expected=0)
    directory = target / "features/feature-2026-11-05-demo"; files = feature_tree(directory)
    for area in ("spec", "design"):
        c.check(any(f.startswith(area + "/be/") for f in files) and
                any(f.startswith(area + "/qa/") for f in files), "BE selection auto-adds QA", area=area, actual=sorted(files))
    c.check(not any("/fe/" in f or "/ui/" in f or f.startswith("prototype/") for f in files),
            "BE full has no unselected FE/UI/prototype", actual=sorted(files))


def feature_prototype(c: Case) -> None:
    c.need("new_feature.py", "--tier", "--tracks", "--prototype")
    target = hub(c)
    feature(c, target, "--tier", "full", "--tracks", "fe", "--prototype", expected=0)
    files = feature_tree(target / "features/feature-2026-11-05-demo")
    c.check(any(f.startswith("prototype/") for f in files), "explicit FE prototype exists", actual=sorted(files))
    c.check(not any("/be/" in f or "/ui/" in f for f in files), "prototype does not add unselected tracks", actual=sorted(files))


def feature_dry_run(c: Case) -> None:
    c.need("new_feature.py", "--tier", "--tracks")
    target = hub(c); before = tree_state(target)
    for args in (("--tier", "light"), ("--tier", "full", "--tracks", "be")):
        feature(c, target, *args, "--dry-run", expected=0)
        c.same_tree(target, before, "dry-run writes no feature/index: " + repr(args))


def feature_invalid_inputs(c: Case) -> None:
    c.need("new_feature.py", "--tier")
    for i, (slug, date) in enumerate((("x/../../../ESCAPED", "2026-11-05"),
                                     ("../escape", "2026-11-05"), ("demo", "2026-02-30"),
                                     ("demo", "../date"))):
        target = hub(c, f"hub-{i}")
        before = tree_state(c.root)
        result = feature(c, target, "--tier", "light", slug=slug, date=date)
        c.same_tree(c.root, before, "bad slug/date has no writes inside or outside hub")
        c.exit(result, NONZERO)
    target = c.root / "no-index"; target.mkdir(); before = tree_state(target)
    feature(c, target, "--tier", "light", expected=NONZERO)
    c.same_tree(target, before, "missing index is zero write error")


def managed_fixture(c: Case) -> tuple[Path, Path, Path, str]:
    target, content, preview = (c.root / n for n in ("managed.md", "body.txt", "preview.json"))
    target.write_bytes(b"HEAD  \r\n<!-- af:begin v0 -->\r\nOLD\r\n<!-- af:end -->\r\nTAIL\r\n")
    content.write_bytes(b"NEW\n")
    c.cli("workflow.py", "managed-preview", "--target", target, "--content", content,
          "--output", preview, "--begin-marker", "<!-- af:begin v0 -->", "--end-marker", "<!-- af:end -->",
          "--new-begin-marker", "<!-- af:begin v1 -->", expected=0)
    return target, content, preview, json.loads(preview.read_bytes())["fingerprint"]


def managed_apply(c: Case) -> None:
    target, _, preview, fingerprint = managed_fixture(c)
    c.cli("workflow.py", "managed-apply", "--preview", preview, "--fingerprint", fingerprint, expected=0)
    expected = b"HEAD  \r\n<!-- af:begin v1 -->\nNEW\n<!-- af:end -->\r\nTAIL\r\n"
    c.bytes_equal(target.read_bytes(), expected, "managed apply preserves outer bytes")


def managed_drift(c: Case) -> None:
    target, _, preview, fingerprint = managed_fixture(c)
    target.write_bytes(target.read_bytes() + b"CONCURRENT\n"); before = tree_state(c.root)
    c.cli("workflow.py", "managed-apply", "--preview", preview, "--fingerprint", fingerprint, expected=NONZERO)
    c.same_tree(c.root, before, "target drift refuses without backup/write")


def seal(c: Case, repo: Path, request: dict[str, Any], name: str = "sealed") -> tuple[Path, str]:
    source, sealed = c.root / (name + "-request.json"), c.root / (name + ".json")
    dump(source, request)
    c.cli("workflow.py", "seal", "--root", repo, "--input", source, "--output", sealed, expected=0)
    return sealed, json.loads(sealed.read_bytes())["fingerprint"]


def workflow_run(c: Case, repo: Path, sealed: Path, fingerprint: str, output: Path,
                 phase: str = "green", expected: int | str | None = None):
    result = c.cli("workflow.py", "run", "--root", repo, "--sealed", sealed, "--fingerprint", fingerprint,
                   "--output", output, "--phase", phase, expected=expected, timeout=20)
    if (output / "result.json").is_file():
        for path in output.iterdir():
            if path.is_file():
                c.archive(path, output.name + "-" + path.name)
    return result


def execution_index_scope(c: Case) -> None:
    repo = git_repo(c)
    (repo / "plan.md").write_text("# Bound plan\n")
    outside = repo / "outside.txt"
    outside.write_text("baseline\n")
    commit_fixture(c, repo)
    request = {"plan": "plan.md", "allowed_writes": ["allowed.txt"], "tasks": [
        {"id": "check", "depends_on": [], "argv": [PYTHON, "--version"], "cwd": ".",
         "timeout_seconds": 10, "kind": "preflight", "reporter": "exit", "cases": []}
    ]}
    sealed, fingerprint = seal(c, repo, request)
    outside.write_text("staged change\n")
    c.run(["git", "add", "outside.txt"], cwd=repo, expected=0)
    outside.write_text("baseline\n")
    result = c.cli("workflow.py", "verify", "--root", repo, "--sealed", sealed,
                   "--fingerprint", fingerprint, expected=3)
    refused = json.loads(result.stdout)
    c.check(refused["error_kind"] == "out-of-scope" and "outside.txt" in refused["evidence"]["message"],
            "the seal refuses stage-only outside changes", actual=refused)
    result = c.run(["bash", c.source / SCRIPTS / "check-write-scope.sh", "HEAD", "allowed.txt"],
                   cwd=repo, expected=1)
    c.check("[暂存区] outside.txt" in result.stdout.decode(), "write-scope identifies the staged layer",
            actual=result.stdout.decode())

    sealed, fingerprint = seal(c, repo, request, "existing-index")
    allowed = repo / "allowed.txt"
    allowed.write_text("staged allowed\n")
    c.run(["git", "add", "allowed.txt"], cwd=repo, expected=0)
    allowed.unlink()
    result = c.cli("workflow.py", "verify", "--root", repo, "--sealed", sealed,
                   "--fingerprint", fingerprint, expected=0)
    observed = json.loads(result.stdout)["evidence"]
    c.check(observed["allowed_index_changes"] == ["allowed.txt"] and observed["allowed_worktree_changes"] == [],
            "prior index state is preserved as baseline and changes are reported by layer", actual=observed)

    previous = json.loads(sealed.read_text())
    previous.pop("fingerprint")
    previous["schema_version"] = 1
    old_fingerprint = "sha256:" + digest(
        json.dumps(previous, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    )
    previous["fingerprint"] = old_fingerprint
    legacy = c.root / "legacy-seal.json"
    dump(legacy, previous)
    result = c.cli("workflow.py", "verify", "--root", repo, "--sealed", legacy,
                   "--fingerprint", old_fingerprint, expected=3)
    c.check(json.loads(result.stdout)["error_kind"] == "stale-seal-format", "legacy seal requests a new seal")


def execution_ignored_link(c: Case) -> None:
    repo = git_repo(c)
    (repo / "plan.md").write_text("# Bound plan\n")
    (repo / ".gitignore").write_text(".venv/\n")
    commit_fixture(c, repo)
    environment = repo / ".venv/bin"
    environment.mkdir(parents=True)
    (environment / "generated.txt").write_text("generated fixture\n")
    link = environment / "python3"
    link.symlink_to(PYTHON)
    request = {"plan": "plan.md", "allowed_writes": [], "tasks": [
        {"id": "check", "depends_on": [], "argv": [PYTHON, "--version"], "cwd": ".",
         "timeout_seconds": 10, "kind": "preflight", "reporter": "exit", "cases": []}
    ]}
    sealed, fingerprint = seal(c, repo, request)
    rows = {row["path"]: row for row in json.loads(sealed.read_text())["baseline_inputs"]}
    observed = rows[".venv/bin/python3"]
    c.check(observed.get("kind") == "symlink" and observed.get("link_target") == PYTHON and "sha256" not in observed,
            "ignored symlink target is recorded without reading bytes through the link", actual=observed)
    c.check("sha256" in rows[".venv/bin/generated.txt"], "ignored regular inputs remain in the content snapshot")
    link.unlink()
    link.symlink_to("other-python3")
    result = c.cli("workflow.py", "verify", "--root", repo, "--sealed", sealed,
                   "--fingerprint", fingerprint, expected=3)
    c.check(json.loads(result.stdout)["error_kind"] == "out-of-scope", "ignored symlink target drift is refused")
    request["plan"] = ".venv/bin/python3"
    invalid = c.root / "link-request.json"
    dump(invalid, request)
    result = c.cli("workflow.py", "seal", "--root", repo, "--input", invalid,
                   "--output", c.root / "refused.json", expected=3)
    c.check(json.loads(result.stdout)["error_kind"] == "symlink", "declaring a symlink as a plan is still refused")


def execution_cached_go(c: Case) -> None:
    repo = git_repo(c)
    (repo / "plan.md").write_text("# Bound plan\n")
    commit_fixture(c, repo)
    package = "example.com/fixture"
    task = {"id": "go", "depends_on": [], "cwd": ".", "timeout_seconds": 10, "kind": "test", "reporter": "go",
            "cases": [{"id": "TC-1", "report_name": package + "/TestValue"}]}
    for cached in (True, False):
        lines = [{"Package": package, "Action": "start"},
                 {"Package": package, "Action": "run", "Test": "TestValue"},
                 {"Package": package, "Action": "pass", "Test": "TestValue"},
                 {"Package": package, "Action": "output", "Output": "ok  \t" + package +
                  ("\t(cached)\n" if cached else "\t0.25s\n")},
                 {"Package": package, "Action": "pass"}]
        body = "\n".join(json.dumps(line) for line in lines)
        name = "cached" if cached else "fresh"
        task["argv"] = [PYTHON, "-c", f"print({body!r})"]
        sealed, fingerprint = seal(c, repo, {"plan": "plan.md", "allowed_writes": [], "tasks": [task]}, name=name)
        result = workflow_run(c, repo, sealed, fingerprint, c.root / (name + "-output"),
                              expected=1 if cached else 0)
        row = json.loads(result.stdout)["evidence"]["tasks"][0]
        correct = row["error_kind"] == "cached-report" and not row["cases"] if cached else (
            row["error_kind"] is None and row["cases"][0]["status"] == "pass"
        )
        c.check(correct, "cached native Go report is not new case evidence", actual=row)


def descendant(c: Case, orphan: bool) -> None:
    repo = git_repo(c); (repo / "plan.md").write_text("# Bound process lifecycle fixture\n")
    commit_fixture(c, repo)
    ready, late, parent_id = (c.root / n for n in ("ready.json", "late-write", "parent.json"))
    child = ("import json,os,pathlib,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
             f"pathlib.Path({str(ready)!r}).write_text(json.dumps({{'pid':os.getpid(),'pgid':os.getpgrp()}})); "
             f"time.sleep(8); pathlib.Path({str(late)!r}).write_text('SURVIVED')")
    parent = ("import json,os,pathlib,subprocess,sys,time\n"
              f"pathlib.Path({str(parent_id)!r}).write_text(json.dumps({{'pid':os.getpid(),'pgid':os.getpgrp()}}))\n"
              f"subprocess.Popen([sys.executable,'-B','-c',{child!r}], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
              f"ready=pathlib.Path({str(ready)!r})\n"
              "until=time.monotonic()+5\n"
              "while not ready.exists() and time.monotonic()<until: time.sleep(.005)\n"
              "if not ready.exists(): raise SystemExit(91)\n"
              + ("raise SystemExit(0)\n" if orphan else "time.sleep(30)\n"))
    request = {"plan": "plan.md", "allowed_writes": [], "tasks": [{
        "id": "lifecycle", "depends_on": [], "argv": [PYTHON, "-B", "-c", parent], "cwd": ".",
        "timeout_seconds": 6, "kind": "preflight", "reporter": "exit", "cases": []}]}
    sealed, fingerprint = seal(c, repo, request)
    c.archive(c.root / "sealed-request.json", "request.json")
    c.archive(sealed, "sealed.json")
    # workflow launches a separate task session. Register its own handshake even
    # if our outer watchdog or an assertion raises, so it cannot escape cleanup.
    try:
        result = workflow_run(c, repo, sealed, fingerprint, c.root / "native")
    finally:
        for identifier in (parent_id, ready):
            if identifier.is_file():
                identity = json.loads(identifier.read_bytes())
                c.groups.setdefault(int(identity["pgid"]), set()).add(int(identity["pid"]))
                c.archive(identifier, identifier.name)
    handshake = json.loads(ready.read_bytes()) if ready.is_file() else None
    if handshake is None:
        raise Blocked("Fixture readiness handshake absent; not a valid lifecycle red")
    # Eight seconds from return covers the child's scheduled write even when the
    # tested runner returns immediately on a normal parent exit.
    deadline = time.monotonic() + 8.3
    while time.monotonic() < deadline:
        time.sleep(.05)
    c.check(handshake is not None, "child installed ignore-TERM before parent exit/timeout", actual=handshake)
    late_data = late.read_bytes() if late.is_file() else b""
    if late.exists():
        c.archive(late, "late-write")
    c.check(not late.exists(), "no descendant writes after workflow returned", expected="absent", actual=repr(late_data))
    c.exit(result, NONZERO)
    report = json.loads((c.root / "native/result.json").read_bytes())
    c.check(report["tasks"][0]["status"] == "fail", "lifecycle task classified fail", actual=report)


def execution_timeout_descendant(c: Case) -> None:
    descendant(c, orphan=False)


def execution_orphan_descendant(c: Case) -> None:
    descendant(c, orphan=True)


def execution_tap_cycle(c: Case) -> None:
    repo = git_repo(c)
    (repo / "src").mkdir(); (repo / "tests").mkdir()
    (repo / "plan.md").write_text("# Requirement\nReturn confirmed value 2.\n")
    production = repo / "src/value.cjs"; production.write_text("module.exports = 1;\n")
    (repo / "tests/value.test.cjs").write_text(
        "const test=require('node:test'); const assert=require('node:assert/strict');\n"
        "test('returns confirmed value',()=>assert.equal(require('../src/value.cjs'),2));\n")
    commit_fixture(c, repo)
    request = {"plan": "plan.md", "allowed_writes": ["src/value.cjs"], "tasks": [{
        "id": "target", "depends_on": [], "argv": ["node", "--test", "--test-reporter=tap", "tests/value.test.cjs"],
        "cwd": ".", "timeout_seconds": 10, "kind": "test", "reporter": "tap",
        "cases": [{"id": "TC-VALUE-001", "report_name": "returns confirmed value"}]}]}
    sealed, fingerprint = seal(c, repo, request)
    c.cli("workflow.py", "verify", "--root", repo, "--sealed", sealed, "--fingerprint", fingerprint, expected=0)
    for phase in ("red", "green"):
        if phase == "green":
            production.write_text("module.exports = 2;\n")
        output = c.root / phase
        workflow_run(c, repo, sealed, fingerprint, output, phase, expected=0)
        report = json.loads((output / "result.json").read_bytes())
        task = report["tasks"][0]
        c.check(task["status"] == "pass" and task["cases"][0]["report_name"] == "returns confirmed value",
                "native TAP selected case matches", phase=phase, actual=task)
        c.check(task["evidence"]["returncode"] != 0 if phase == "red" else task["evidence"]["returncode"] == 0,
                "red/green retains native Node exit", phase=phase, actual=task["evidence"]["returncode"])
    (repo / "plan.md").write_text("# Changed requirement\n")
    c.cli("workflow.py", "verify", "--root", repo, "--sealed", sealed, "--fingerprint", fingerprint, expected=NONZERO)
    workflow_run(c, repo, sealed, fingerprint, c.root / "drift", expected=NONZERO)


def install_tree(c: Case) -> Path:
    c.need("workflow.py", "install-verify", "upgrade-codex", "upgrade-zcode")
    tree = c.root / "expected"; tree.mkdir()
    for name in payload_names(c.source):
        copy_path(c.source / name, tree / name)
    return tree


def compare_install(c: Case, tree: Path, cache: Path, *extra: Any,
                    expected: int | str | None = None):
    return c.cli("workflow.py", "install-verify", "--expected-tree", tree,
                 "--installed", cache, *extra, expected=expected)


def install_payload_valid(c: Case) -> None:
    tree = install_tree(c); cache = c.root / "cache"; copy_path(tree, cache)
    compare_install(c, tree, cache, expected=0)
    cursor_rules = cache / ".cursor/rules"
    cursor_rules.mkdir(parents=True)
    compare_install(c, tree, cache, expected=NONZERO)
    # Codex may store the whole source checkout, but runtime roots stay strict.
    (cache / ".git").mkdir(); (cache / ".venv").mkdir(); (cache / ".zcode").mkdir()
    (cache / "README.md").write_bytes(b"source maintenance file\n")
    compare_install(c, tree, cache, "--codex-source", expected=0)
    user_rule = cursor_rules / "user.mdc"
    user_rule.write_bytes(b"User rule\n")
    compare_install(c, tree, cache, "--codex-source", expected=NONZERO)
    user_rule.unlink()
    cursor_rules.rmdir()
    cursor_rules.symlink_to(c.root / "outside", target_is_directory=True)
    (c.root / "outside").mkdir()
    compare_install(c, tree, cache, "--codex-source", expected=NONZERO)
    cursor_rules.unlink()
    compare_install(c, tree, cache, "--codex-source", expected=0)
    (cache / "skills/UNDECLARED.txt").write_bytes(b"extra inside payload\n")
    compare_install(c, tree, cache, "--codex-source", expected=NONZERO)


def install_payload_drift(c: Case) -> None:
    tree = install_tree(c)
    regular = next(p for p in tree.rglob("*") if p.is_file() and p.name == "SKILL.md")
    rel = regular.relative_to(tree)
    for mutation in ("missing", "extra", "changed", "execute", "symlink"):
        cache = c.root / mutation; copy_path(tree, cache)
        target = cache / rel
        if mutation == "missing":
            target.unlink()
        elif mutation == "extra":
            (cache / "skills/EXTRA.txt").write_bytes(b"extra\n")
        elif mutation == "changed":
            target.write_bytes(target.read_bytes() + b"\nSTALE\n")
        elif mutation == "execute":
            target.chmod(stat.S_IMODE(target.stat().st_mode) ^ 0o100)
        else:
            target.unlink(); target.symlink_to(regular)
        before = tree_state(cache)
        compare_install(c, tree, cache, expected=NONZERO)
        c.same_tree(cache, before, "read-only verifier preserves mutated cache")


def upgrade_fixture(c: Case, host: str) -> tuple[Path, Path]:
    c.need("workflow.py", "upgrade-" + host)
    repo = c.root / "upgrade-repo"; copy_path(c.source, repo)
    version = json.loads((repo / "plugin.json").read_bytes())["version"]
    market = c.root / "market"; market.mkdir()
    (market / "plugins").mkdir(); (market / "plugins/agentflow").symlink_to(repo, target_is_directory=True)
    dump(market / "marketplace.json", {"name": "fixture", "plugins": [
        {"name": "agentflow", "version": version, "source": "../upgrade-repo/packaging/runtime"}]})
    if host == "zcode":
        # Directory source must be lexically inside the configured marketplace.
        (market / "marketplace.json").unlink()
        market = repo / "packaging"
        dump(market / "marketplace.json", {"name": "fixture", "plugins": [
            {"name": "agentflow", "version": version, "source": "runtime"}]})
        config = c.home / ".zcode/cli/plugins"; config.mkdir(parents=True)
        dump(config / "known_marketplaces.json", {"marketplaces": [
            {"id": "fixture", "source": {"source": "directory", "path": str(market)}}]})
    cache = c.home / (".codex" if host == "codex" else ".zcode/cli") / "plugins/cache/fixture/agentflow" / version
    cache.mkdir(parents=True)
    for name in payload_names(repo):
        copy_path(repo / name, cache / name)
    stale = cache / "skills/agentflow/SKILL.md"; stale.write_bytes(stale.read_bytes() + b"\nSTALE_CACHE\n")
    if host == "zcode":
        dump(c.home / ".zcode/cli/plugins/installed_plugins.json", {"plugins": [
            {"id": "agentflow@fixture", "version": version, "installPath": str(cache)}]})
    stub = (f"#!{PYTHON} -B\nimport json,os,pathlib,sys\n"
            "with pathlib.Path(os.environ['AF_STUB_CALLS']).open('a') as f: f.write(json.dumps(sys.argv)+'\\n')\n"
            + (f"if sys.argv[1:]==['plugin','marketplace','list']: print('fixture '+{str(market)!r})\n" if host == "codex" else "")
            + "print('MOCK HOST CLI: success without cache update')\nraise SystemExit(0)\n")
    c.stub(host, stub)
    return repo, cache


def upgrade(c: Case, host: str, repo: Path, *args: Any, expected: int | str | None = None):
    # Exercise the public workflow adapter; no real host path is in argv or PATH.
    return c.cli("workflow.py", "upgrade-" + host, "--repo", repo, "--marketplace", "fixture",
                 "--plugin", "agentflow", *args, expected=expected, timeout=45)


def stale_upgrade(c: Case, host: str) -> None:
    repo, cache = upgrade_fixture(c, host)
    before = tree_state(cache)
    result = upgrade(c, host, repo, "--mode", "local")
    calls = [json.loads(line) for line in (c.root / "stub-calls.jsonl").read_text().splitlines()]
    expected_command = ["plugin", "add", "agentflow@fixture"] if host == "codex" else ["plugins", "update", "agentflow@fixture"]
    c.check(any(row[1:] == expected_command for row in calls), "successful mock install CLI was reached",
            expected=expected_command, actual=calls)
    c.same_tree(cache, before, "mock install actually leaves stale cache unchanged")
    c.exit(result, NONZERO)
    text = result.stdout + result.stderr
    c.check(b"installation-mismatch" in text or b"CHANGED" in text or b"differs" in text,
            "upgrade rejects payload mismatch after mock CLI success", actual=text.decode("utf-8", "replace"))


def install_upgrade_codex_stale(c: Case) -> None:
    stale_upgrade(c, "codex")


def install_upgrade_zcode_stale(c: Case) -> None:
    stale_upgrade(c, "zcode")


def install_upgrade_modes(c: Case) -> None:
    # Each host gets a fresh case-owned HOME/config; no real host is contacted.
    for host in ("codex", "zcode"):
        sub = c.root / host; sub.mkdir()
        child = Case(c.group, host + "-modes", c.source, sub, c.logs, {
            n: str((c.bin / n).resolve()) for n in ("node", "git", "bash", "ps") if (c.bin / n).exists()})
        try:
            repo, cache = upgrade_fixture(child, host)
            for mode in ("auto", "local", "remote"):
                before = tree_state(child.root)
                upgrade(child, host, repo, "--mode", mode, "--dry-run", expected=0 if mode != "remote" else NONZERO)
                # CLI listing is an observation, not an install; exclude its own log.
                after = tree_state(child.root)
                changed = [p for p in before.keys() | after.keys()
                           if before.get(p) != after.get(p) and p != "stub-calls.jsonl"]
                child.check(not changed, "dry-run/mode mismatch makes no source/cache writes", mode=mode, actual=changed)
            rules = repo / ".cursor/rules"
            rules.mkdir(parents=True)
            (rules / "user.mdc").write_bytes(b"User rule outside the payload\n")
            before_cache = tree_state(cache)
            call_log = child.root / "stub-calls.jsonl"
            before_calls = call_log.read_bytes() if call_log.exists() else b""
            result = upgrade(child, host, repo, "--mode", "local", expected=NONZERO)
            after_calls = call_log.read_bytes() if call_log.exists() else b""
            new_calls = [json.loads(line)[1:] for line in after_calls[len(before_calls):].splitlines()]
            child.check(new_calls == ([["plugin", "marketplace", "list"]] if host == "codex" else []),
                        "unexpected source rules stop upgrade before host install", actual=new_calls)
            child.check(b"extra=['.cursor']" in result.stdout + result.stderr, "source preflight reports the extra root")
            child.same_tree(cache, before_cache, "source preflight leaves the existing host cache unchanged")
            c.facts.extend(child.facts)
            c.commands.extend(child.commands)
        finally:
            dump(child.logs / "case.json", {"commands": child.commands, "assertions": child.facts})
            child.cleanup()


def json_invalid_inputs(c: Case) -> None:
    repo = git_repo(c); (repo / "plan.md").write_text("# JSON request fixture\n")
    commit_fixture(c, repo)
    for name, body in (("duplicate", '{"plan":"plan.md","plan":"other.md","allowed_writes":[],"tasks":[]}'),
                       ("nan", '{"value":NaN}'), ("infinity", '{"value":Infinity}'), ("list", '[]')):
        source, sealed = c.root / (name + "-request.json"), c.root / (name + "-sealed.json")
        source.write_text(body)
        result = c.cli("workflow.py", "seal", "--root", repo, "--input", source, "--output", sealed, expected=2)
        native = json.loads(result.stdout)
        c.check(native.get("error_kind") == "invalid-json", "strict JSON rejects before request validation",
                variant=name, actual=native)
        c.check(not sealed.exists(), "invalid JSON creates no sealed output", variant=name)


def execution_inspector_failure(c: Case) -> None:
    code = r'''
import json,pathlib,subprocess,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
from workflow_lib import execution as e
from workflow_lib.snapshots import WorkflowError
base=pathlib.Path(sys.argv[2]);out=base/'native';out.mkdir();late=base/'late-write'
argv=[sys.executable,'-I','-B','-c',f'import pathlib,time;time.sleep(1);pathlib.Path({str(late)!r}).write_text("SURVIVED")']
real_group=e._group_members;real_popen=e.subprocess.Popen;calls=0;children=[]
def inspect(pgid):
 global calls
 calls+=1
 if calls==1:return real_group(pgid)
 raise WorkflowError('process-cleanup-failed','fixture: ps unavailable after startup',3)
def spawn(*args,**kwargs):
 proc=real_popen(*args,**kwargs)
 if args and args[0]==argv:children.append(proc)
 return proc
try:
 with patch.object(e,'_group_members',side_effect=inspect),patch.object(e.subprocess,'Popen',side_effect=spawn):
  try:e._command({'id':'target','argv':argv,'cwd':'.','timeout_seconds':.1},base,out);raised=None
  except WorkflowError as exc:raised=exc.kind
 running=bool(children and children[0].poll() is None)
 for proc in children:proc.wait(timeout=4)
 print(json.dumps({'error_kind':raised,'running_at_return':running,'late_write':late.exists()}))
 assert raised=='process-cleanup-failed' and not running and not late.exists()
finally:
 for proc in children:
  if proc.poll() is None:proc.kill();proc.wait(timeout=3)
'''
    result = c.run([PYTHON, "-I", "-B", "-c", code, c.source / SCRIPTS, c.root], expected=0)
    observed = json.loads(result.stdout)
    c.check(not observed["running_at_return"] and not observed["late_write"],
            "inspector failure still terminates owned group before refusal", actual=observed)


def installation_timeout_json(c: Case) -> None:
    code = r'''
import contextlib,io,json,pathlib,subprocess,sys
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
from workflow_lib import cli
for host in ('codex','zcode'):
 out,err=io.StringIO(),io.StringIO()
 with patch('workflow_lib.cli.upgrade',side_effect=subprocess.TimeoutExpired([host,'install'],90)),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
  status=cli.main(['upgrade-'+host,'--repo',sys.argv[2],'--dry-run'])
 result=json.loads(out.getvalue())
 print(json.dumps({'host':host,'returned_exit':status,'result':result,'stderr':err.getvalue()}))
 assert status==1 and result['exit_code']==1 and result['error_kind']=='command-timeout'
'''
    result = c.run([PYTHON, "-I", "-B", "-c", code, c.source / SCRIPTS, c.root], expected=0)
    c.check(len(result.stdout.splitlines()) == 2, "both host timeout paths retain classified JSON")


# Each native case belongs to one goal group. Adjacent coverage is documented by
# the case name; rule-only goals and four browser task cards remain supervisor work.
CASES: list[tuple[str, str, Callable[[Case], None]]] = [
    ("G01", "init.carrier-bytes", init_carrier_bytes),
    ("G02", "init.symlink-file", init_symlink_file),
    ("G02", "init.symlink-ancestor", init_symlink_ancestor),
    ("G03", "init.conflict-lifecycle", init_conflict_lifecycle),
    ("G08", "init.foreign-block", init_foreign_block),
    ("G08", "init.claude-dependency", init_claude_dependency),
    ("G04", "review.snapshot-binding", review_snapshot_binding),
    ("G04", "review.commit-binding", review_commit_binding),
    ("G04", "review.corrupt-manifest", review_corrupt_manifest),
    ("G04", "review.external-collision", review_external_collision),
    ("G10", "task-map.closure", task_map_closure),
    ("G10", "task-map.invalid-graph", task_map_invalid_graph),
    ("G09", "feature.tier-required", feature_tier_required),
    ("G09", "feature.light", feature_light),
    ("G09", "feature.full-be", feature_full_be),
    ("G09", "feature.prototype", feature_prototype),
    ("G09", "feature.dry-run", feature_dry_run),
    ("G02", "feature.invalid-inputs", feature_invalid_inputs),
    ("G01", "managed.apply", managed_apply),
    ("G01", "managed.drift", managed_drift),
    ("G05", "execution.timeout-descendant", execution_timeout_descendant),
    ("G05", "execution.orphan-descendant", execution_orphan_descendant),
    ("G05", "execution.tap-cycle", execution_tap_cycle),
    ("G02", "execution.index-scope", execution_index_scope),
    ("G21", "execution.ignored-link", execution_ignored_link),
    ("G06", "execution.cached-go", execution_cached_go),
    ("G12", "install.payload-valid", install_payload_valid),
    ("G12", "install.payload-drift", install_payload_drift),
    ("G12", "install.upgrade-codex-stale", install_upgrade_codex_stale),
    ("G12", "install.upgrade-zcode-stale", install_upgrade_zcode_stale),
    ("G12", "install.upgrade-modes", install_upgrade_modes),
    ("G05", "json.invalid-inputs", json_invalid_inputs),
    ("G05", "execution.inspector-failure", execution_inspector_failure),
    ("G12", "install.timeout-json", installation_timeout_json),
]


def preflight(output: Path) -> dict[str, str]:
    tools: dict[str, str] = {}
    failures = []
    for name, flags in (("node", ["--version"]), ("git", ["--version"]), ("bash", ["--version"])):
        executable = shutil.which(name)
        if executable is None:
            failures.append(name + " not on PATH (no dependencies are installed)")
            continue
        tools[name] = str(Path(executable).resolve())
        try:
            result = subprocess.run([tools[name], *flags], stdin=subprocess.DEVNULL, capture_output=True,
                                    timeout=10, cwd=output)
            (output / ("preflight-" + name + ".stdout")).write_bytes(result.stdout)
            (output / ("preflight-" + name + ".stderr")).write_bytes(result.stderr)
            dump(output / ("preflight-" + name + ".json"), {
                "argv": [tools[name], *flags], "actual_exit": result.returncode})
            print(f"PREFLIGHT {name} native_exit={result.returncode} {result.stdout.decode(errors='replace').splitlines()[:1]}", flush=True)
            if result.returncode:
                failures.append(name + " version probe failed")
        except OSError as exc:
            failures.append(f"{name} probe failed ({exc})")

    # ps is an environment monitoring helper; sandbox restrictions may block /bin/ps
    executable = shutil.which("ps")
    if executable:
        try:
            ps_path = str(Path(executable).resolve())
            result = subprocess.run([ps_path, "-p", str(os.getpid()), "-o", "pid=,pgid=,stat="],
                                    stdin=subprocess.DEVNULL, capture_output=True, timeout=10, cwd=output)
            if result.returncode == 0:
                tools["ps"] = ps_path
                (output / "preflight-ps.stdout").write_bytes(result.stdout)
                (output / "preflight-ps.stderr").write_bytes(result.stderr)
                dump(output / "preflight-ps.json", {"argv": [ps_path, "-p", str(os.getpid())], "actual_exit": 0})
                print(f"PREFLIGHT ps native_exit=0 {result.stdout.decode(errors='replace').splitlines()[:1]}", flush=True)
            else:
                print(f"PREFLIGHT ps probe returned {result.returncode}; process checks degraded", flush=True)
        except OSError as exc:
            print(f"PREFLIGHT ps unavailable in sandbox ({exc}); process checks degraded", flush=True)

    if os.name != "posix":
        failures.append("POSIX process-group tests require a POSIX host")
    if failures:
        raise Blocked("; ".join(failures))
    for name in ("mktemp", "rm"):
        executable = shutil.which(name)
        if executable is None:
            raise Blocked(f"{name} not on PATH (required by the write scope fixture)")
        tools[name] = str(Path(executable).resolve())
    return tools


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="Cases (G group / native name):\n" + "\n".join(
                                         f"  {group}  {name}" for group, name, _ in CASES))
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[3],
                        help="Source project root to COPY and test (default: script parents[3])")
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory; existing paths rejected")
    parser.add_argument("--case", action="append", default=[], metavar="PATTERN",
                        help="Exact Gxx group or native name/glob; repeat for union (default: all)")
    args = parser.parse_args()
    selected = [case for case in CASES if not args.case or any(
        pattern == case[0] or fnmatch.fnmatchcase(case[1], pattern) for pattern in args.case)]
    for pattern in args.case:
        if not any(pattern == group or fnmatch.fnmatchcase(name, pattern) for group, name, _ in CASES):
            parser.error(f"--case matches no group/case: {pattern!r}")
    source = args.source_root.expanduser().resolve()
    if not (source / SCRIPTS / "workflow.py").is_file():
        parser.error(f"Not an Agentflow source root: {source}")
    output = Path(os.path.abspath(args.output.expanduser()))
    if output.exists() or output.is_symlink():
        parser.error(f"--output must be NEW: {output}")
    if output == source or source in output.parents:
        parser.error("Evidence must be outside tested source")
    output.mkdir(parents=True, mode=0o700)
    results: list[dict[str, Any]] = []
    report: dict[str, Any] = {"schema_version": 1, "task_id": "FIX-REGRESSION", "source_root": str(source),
                              "patterns": args.case, "selected_cases": len(selected), "cases": results,
                              "scope": "isolated native CLI fixtures; not rule approval, host loading or four browser apps"}
    try:
        tools = preflight(output)
        with tempfile.TemporaryDirectory(prefix="af-tools-regressions-", dir="/tmp") as temporary:
            temp = Path(temporary).resolve()
            staged = temp / "source"; staged.mkdir()
            for name in [*payload_names(source), "packaging/build_runtime.py"]:
                copy_path(source / name, staged / name)
            report["staged_source"] = str(staged)
            for group, name, fn in selected:
                case = Case(group, name, staged, temp, output, tools)
                row: dict[str, Any] = {"group": group, "name": name, "status": "not-run",
                                       "commands": case.commands, "assertions": case.facts}
                results.append(row)
                print(f"RUN {group} {name}", flush=True)
                try:
                    fn(case)
                    row["status"] = "pass"
                except Blocked as exc:
                    row.update(status="blocked", reason=str(exc))
                except Exception as exc:
                    row.update(status="fail", reason=str(exc), exception=type(exc).__name__)
                    (case.logs / "exception.txt").write_text(traceback.format_exc(), encoding="utf-8")
                finally:
                    row["first_native_exit"] = case.commands[0]["actual_exit"] if case.commands else None
                    try:
                        case.cleanup()
                    except Exception as exc:
                        row.update(status="fail", cleanup_error=repr(exc))
                    dump(case.logs / "case.json", row)
                    dump(output / "report.json", report)
                print(f"{row['status'].upper()} {group} {name} first_native_exit={row['first_native_exit']}"
                      + (" " + row["reason"] if "reason" in row else ""), flush=True)
    except Exception as exc:
        report.update(status="blocked", preflight_error=f"{type(exc).__name__}: {exc}")
        (output / "preflight-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        for group, name, _ in selected:
            if not any(row["name"] == name for row in results):
                results.append({"group": group, "name": name, "status": "blocked", "reason": str(exc),
                                "commands": [], "assertions": [], "first_native_exit": None})
    counts = {status: sum(row["status"] == status for row in results)
              for status in ("pass", "fail", "blocked", "not-run")}
    report["counts"] = counts
    report["status"] = "fail" if counts["fail"] else "blocked" if counts["blocked"] or counts["not-run"] else "pass"
    code = 1 if report["status"] == "fail" else 2 if report["status"] == "blocked" else 0
    report["exit_code"] = code
    dump(output / "report.json", report)
    print(json.dumps({"status": report["status"], "counts": counts, "report": str(output / "report.json"),
                      "exit_code": code}, ensure_ascii=False), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
