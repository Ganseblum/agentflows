"""Plan binding, project snapshots, and structural backfill inventories."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


class WorkflowError(Exception):
    """A classified, user-visible failure with no silent fallback."""

    def __init__(self, kind: str, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.kind = kind
        self.code = code


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()


def fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def envelope(
    operation: str,
    evidence: Any,
    code: int = 0,
    kind: str | None = None,
    next_action: str = "review_evidence",
) -> dict[str, Any]:
    return {
        "operation": operation,
        "status": {0: "pass", 1: "fail", 2: "invalid", 3: "refused", 4: "partial"}[
            code
        ],
        "error_kind": kind,
        "evidence": evidence,
        "next_action": next_action,
        "exit_code": code,
    }


def read_json(path: Path | str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorkflowError("invalid-json", f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowError("invalid-json", f"JSON object required: {path}")
    return value


def no_symlinks(path: Path | str) -> Path:
    """Reject existing symlink components; return an absolute lexical path."""
    absolute = Path(os.path.abspath(Path(path).expanduser()))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            # macOS exposes these root-owned system directories through stable aliases.
            # Canonicalize those aliases; project/user-controlled links still fail closed.
            system_aliases = {
                Path("/tmp"): Path("/private/tmp"),
                Path("/var"): Path("/private/var"),
            }
            if (
                current in system_aliases
                and current.resolve() == system_aliases[current]
            ):
                current = current.resolve()
            else:
                raise WorkflowError(
                    "symlink", f"Symlink path is not allowed: {current}", 3
                )
        if getattr(current, "is_junction", lambda: False)():
            raise WorkflowError(
                "symlink", f"Junction path is not allowed: {current}", 3
            )
    return current


def write_json_new(path: Path | str, value: Any) -> Path:
    target = no_symlinks(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError as exc:
        raise WorkflowError(
            "evidence-exists", f"Evidence cannot overwrite {target}", 3
        ) from exc
    return target


def relative_name(value: Any, allow_dot: bool = False) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise WorkflowError("invalid-path", f"Relative POSIX path required: {value!r}")
    if value == "." and allow_dot:
        return value
    parts = value.split("/")
    if (
        value.startswith("/")
        or any(x in {"", ".", ".."} for x in parts)
        or ":" in parts[0]
    ):
        raise WorkflowError("path-escape", f"Unsafe project path: {value!r}", 3)
    return PurePosixPath(value).as_posix()


def project_path(
    root: Path, value: Any, must_exist: bool = False, directory: bool = False
) -> Path:
    name = relative_name(value, allow_dot=directory)
    path = no_symlinks(root / name)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise WorkflowError("path-escape", f"Path leaves project: {value}", 3) from exc
    if must_exist and not path.exists():
        raise WorkflowError("missing-path", f"Project input is missing: {name}")
    if path.exists() and directory and not path.is_dir():
        raise WorkflowError("invalid-path", f"Directory required: {name}")
    if path.exists() and not directory and not path.is_file():
        raise WorkflowError("invalid-path", f"Regular file required: {name}")
    return path


def git(root: Path, *args: str) -> bytes:
    try:
        command = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=False
        )
    except OSError as exc:
        raise WorkflowError("git-unavailable", str(exc), 3) from exc
    if command.returncode:
        raise WorkflowError(
            "git-failed", command.stderr.decode(errors="replace").strip(), 3
        )
    return command.stdout


def project_root(value: Path | str) -> Path:
    root = no_symlinks(value)
    if not root.is_dir():
        raise WorkflowError("invalid-root", f"Project directory is missing: {root}")
    actual = Path(
        os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()
    ).resolve()
    if actual != root:
        raise WorkflowError("invalid-root", "--root must be the Git worktree root")
    return root


def git_files(root: Path) -> set[str]:
    """Include tracked, untracked and ignored files; Git administrative data is not source."""
    names: set[str] = set()
    for args in [
        ("ls-files", "--cached", "--others", "--exclude-standard", "-z"),
        ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
    ]:
        names.update(os.fsdecode(raw) for raw in git(root, *args).split(b"\0") if raw)
    return names


def tracked_files(root: Path) -> set[str]:
    return {
        os.fsdecode(raw)
        for raw in git(root, "ls-files", "--cached", "-z").split(b"\0")
        if raw
    }


def file_entry(root: Path, name: str) -> dict[str, Any]:
    path = project_path(root, name)
    if not path.exists():
        return {"path": name, "exists": False}
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise WorkflowError("special-file", f"Not a regular project file: {name}", 3)
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {
        "path": name,
        "exists": True,
        "mode": "0755" if info.st_mode & 0o111 else "0644",
        "size": size,
        "sha256": digest.hexdigest(),
    }


def snapshot(
    root: Path,
    excluded_files: set[str] | None = None,
    excluded_directory: str | None = None,
) -> list[dict[str, Any]]:
    exclusions = excluded_files or set()
    result = []
    for name in sorted(git_files(root)):
        if name in exclusions:
            continue
        if excluded_directory and (
            name == excluded_directory or name.startswith(excluded_directory + "/")
        ):
            continue
        result.append(file_entry(root, name))
    return result


def changed_paths(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> list[str]:
    left = {row["path"]: row for row in before}
    right = {row["path"]: row for row in after}
    return sorted(
        name for name in left.keys() | right.keys() if left.get(name) != right.get(name)
    )


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError("invalid-input", f"{label} must be a non-empty string")
    return value


def task_order(
    tasks: list[dict[str, Any]], dependency_key: str = "depends_on"
) -> list[dict[str, Any]]:
    by_id = {task["id"]: task for task in tasks}
    if len(by_id) != len(tasks):
        raise WorkflowError("duplicate-id", "Task/batch IDs must be unique")
    remaining = list(tasks)
    output: list[dict[str, Any]] = []
    done: set[str] = set()
    while remaining:
        ready = [task for task in remaining if set(task[dependency_key]) <= done]
        if not ready:
            raise WorkflowError(
                "dependency-cycle", "Dependencies are cyclic or unresolved"
            )
        for task in ready:
            if any(dep not in by_id for dep in task[dependency_key]):
                raise WorkflowError(
                    "unknown-dependency", f"Unknown dependency for {task['id']}"
                )
            output.append(task)
            done.add(task["id"])
            remaining.remove(task)
    return output


def validate_request(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    if set(request) != {"plan", "allowed_writes", "tasks"}:
        raise WorkflowError(
            "invalid-request", "Request fields must be plan, allowed_writes, tasks"
        )
    plan = relative_name(request["plan"])
    project_path(root, plan, must_exist=True)
    writes = request["allowed_writes"]
    if (
        not isinstance(writes, list)
        or any(not isinstance(x, str) for x in writes)
        or len(writes) != len(set(writes))
    ):
        raise WorkflowError(
            "invalid-request", "allowed_writes must be a unique path list"
        )
    for path in writes:
        project_path(root, path)
        if path == plan or path == ".git" or path.startswith(".git/"):
            raise WorkflowError(
                "protected-input",
                f"The plan/Git metadata cannot be writable: {path}",
                3,
            )
    tasks = request["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise WorkflowError("invalid-request", "tasks must be a non-empty array")
    case_ids: set[str] = set()
    report_paths: set[str] = set()
    for task in tasks:
        required = {
            "id",
            "depends_on",
            "argv",
            "cwd",
            "timeout_seconds",
            "kind",
            "reporter",
            "cases",
        }
        if (
            not isinstance(task, dict)
            or not required <= task.keys()
            or task.keys() - required - {"report_path"}
        ):
            raise WorkflowError("invalid-task", "Invalid task fields")
        identifier = _string(task["id"], "task id")
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", identifier)
            or ".." in identifier
        ):
            raise WorkflowError("invalid-task", f"Unsafe task ID: {identifier}")
        deps = task["depends_on"]
        if (
            not isinstance(deps, list)
            or any(not isinstance(x, str) for x in deps)
            or len(set(deps)) != len(deps)
        ):
            raise WorkflowError("invalid-task", "depends_on must be a unique ID list")
        argv = task["argv"]
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(x, str) or "\x00" in x for x in argv)
            or not argv[0]
        ):
            raise WorkflowError("invalid-task", "argv must be a non-empty string array")
        project_path(root, task["cwd"], must_exist=True, directory=True)
        timeout = task["timeout_seconds"]
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not 0 < timeout <= 3600
        ):
            raise WorkflowError(
                "invalid-task", "timeout_seconds must be positive and at most 3600"
            )
        if task["kind"] not in {"test", "preflight"} or task["reporter"] not in {
            "tap",
            "junit",
            "go",
            "jest",
            "exit",
        }:
            raise WorkflowError("invalid-task", "Unsupported kind or reporter")
        if not isinstance(task["cases"], list):
            raise WorkflowError("invalid-task", "cases must be an array")
        if task["reporter"] == "exit" and task["cases"]:
            raise WorkflowError(
                "invalid-task", "Exit-only preflight cannot claim behavior cases"
            )
        if task["kind"] == "test" and (not task["cases"] or task["reporter"] == "exit"):
            raise WorkflowError(
                "invalid-task", "Behavior tests need named cases and a native reporter"
            )
        names: set[str] = set()
        for case in task["cases"]:
            if not isinstance(case, dict) or set(case) != {"id", "report_name"}:
                raise WorkflowError(
                    "invalid-case", "Case fields must be id and report_name"
                )
            cid, name = (
                _string(case["id"], "case id"),
                _string(case["report_name"], "report name"),
            )
            if cid in case_ids or name in names:
                raise WorkflowError(
                    "duplicate-case",
                    "Case IDs and per-task report names must be unique",
                )
            case_ids.add(cid)
            names.add(name)
        if "report_path" in task:
            path = relative_name(task["report_path"])
            project_path(root, path)
            if (
                path in tracked_files(root)
                or (root / path).exists()
                or path == plan
                or path in writes
                or path in report_paths
            ):
                raise WorkflowError(
                    "invalid-report-path",
                    f"Report path is an input or duplicate: {path}",
                    3,
                )
            report_paths.add(path)
    task_order(tasks)
    return request


def _relative_inside(root: Path, path: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def seal_plan(
    root: Path | str, input_path: Path | str, output_path: Path | str
) -> dict[str, Any]:
    root = project_root(root)
    input_path = no_symlinks(input_path)
    output_path = no_symlinks(output_path)
    if input_path == output_path or output_path.exists():
        raise WorkflowError(
            "evidence-exists", "Sealed evidence needs a new output path", 3
        )
    request = validate_request(root, read_json(input_path))
    output_relative = _relative_inside(root, output_path)
    if output_relative and (
        output_relative in tracked_files(root)
        or output_relative in request["allowed_writes"]
    ):
        raise WorkflowError(
            "evidence-is-input", "Sealed output cannot hide a tracked/writable input", 3
        )
    excluded = set([output_relative] if output_relative else [])
    excluded.update(
        task["report_path"] for task in request["tasks"] if "report_path" in task
    )
    bundle: dict[str, Any] = {
        "schema_version": 1,
        "kind": "execution",
        "root": str(root),
        "request": request,
        "request_source": str(input_path),
        "request_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "head": os.fsdecode(git(root, "rev-parse", "HEAD")).strip(),
        "excluded_files": sorted(excluded),
        "baseline_inputs": snapshot(root, excluded),
    }
    bundle["fingerprint"] = fingerprint(bundle)
    write_json_new(output_path, bundle)
    return envelope(
        "seal",
        {
            "fingerprint": bundle["fingerprint"],
            "sealed": str(output_path),
            "input_count": len(bundle["baseline_inputs"]),
        },
        next_action="verify_before_work",
    )


def check_bound_inputs(
    root: Path, sealed: dict[str, Any], sealed_path: Path | str
) -> None:
    """Recheck bindings that Git's source-file snapshot cannot represent."""
    if os.fsdecode(git(root, "rev-parse", "HEAD")).strip() != sealed["head"]:
        raise WorkflowError("head-drift", "HEAD changed; seal a new plan", 3)
    try:
        source = no_symlinks(sealed["request_source"])
        source_matches = source.is_file() and (
            hashlib.sha256(source.read_bytes()).hexdigest() == sealed["request_sha256"]
        )
    except (OSError, WorkflowError) as exc:
        raise WorkflowError("request-drift", f"Cannot recheck request source: {exc}", 3) from exc
    if not source_matches:
        raise WorkflowError("request-drift", "The request source changed after sealing", 3)
    try:
        current = read_json(no_symlinks(sealed_path))
    except WorkflowError as exc:
        raise WorkflowError("sealed-drift", f"Cannot recheck sealed carrier: {exc}", 3) from exc
    if current != sealed:
        raise WorkflowError("sealed-drift", "The sealed carrier changed during verification", 3)


def load_sealed(
    root: Path | str, sealed_path: Path | str, expected: str
) -> tuple[Path, dict[str, Any]]:
    root = project_root(root)
    sealed = read_json(no_symlinks(sealed_path))
    unsigned = {key: value for key, value in sealed.items() if key != "fingerprint"}
    actual = fingerprint(unsigned)
    if (
        expected.removeprefix("sha256:") != actual.removeprefix("sha256:")
        or sealed.get("fingerprint") != actual
    ):
        raise WorkflowError(
            "fingerprint-mismatch", "The supplied plan fingerprint does not match", 3
        )
    if (
        sealed.get("schema_version") != 1
        or sealed.get("kind") != "execution"
        or sealed.get("root") != str(root)
    ):
        raise WorkflowError(
            "invalid-sealed-plan",
            "Sealed evidence belongs to a different root or protocol",
            3,
        )
    validate_request(root, sealed["request"])
    check_bound_inputs(root, sealed, sealed_path)
    return root, sealed


def verified_snapshot(
    root: Path, sealed: dict[str, Any], output_directory: str | None = None
) -> list[dict[str, Any]]:
    current = snapshot(root, set(sealed["excluded_files"]), output_directory)
    changed = changed_paths(sealed["baseline_inputs"], current)
    plan = sealed["request"]["plan"]
    if plan in changed:
        raise WorkflowError("plan-drift", f"The Markdown plan changed: {plan}", 3)
    outside = sorted(set(changed) - set(sealed["request"]["allowed_writes"]))
    if outside:
        raise WorkflowError(
            "out-of-scope",
            "Changed files outside allowed_writes: " + ", ".join(outside),
            3,
        )
    return current


def verify_plan(
    root: Path | str, sealed_path: Path | str, expected: str
) -> dict[str, Any]:
    root, sealed = load_sealed(root, sealed_path, expected)
    current = verified_snapshot(root, sealed)
    return envelope(
        "verify",
        {
            "fingerprint": sealed["fingerprint"],
            "allowed_changes": changed_paths(sealed["baseline_inputs"], current),
            "execution_snapshot": fingerprint(current),
        },
        next_action="run_verification",
    )


def inventory(root: Path | str, input_path: Path | str) -> dict[str, Any]:
    root = project_root(root)
    mapping = read_json(no_symlinks(input_path))
    if set(mapping) != {"files", "features", "batches"} or any(
        not isinstance(mapping[k], list) for k in mapping
    ):
        raise WorkflowError(
            "invalid-inventory", "Inventory requires files, features and batches arrays"
        )
    files: dict[str, str] = {}
    for item in mapping["files"]:
        if (
            not isinstance(item, dict)
            or not {"path", "kind"} <= item.keys()
            or item.keys() - {"path", "kind", "reason"}
        ):
            raise WorkflowError("invalid-inventory", "Invalid file classification")
        path = relative_name(item["path"])
        project_path(root, path)
        if path in files or item["kind"] not in {
            "production",
            "test",
            "infrastructure",
            "excluded",
        }:
            raise WorkflowError(
                "invalid-inventory", "Duplicate path or unknown file kind"
            )
        if item["kind"] == "excluded":
            _string(item.get("reason"), "excluded file reason")
        files[path] = item["kind"]
    actual = git_files(root)
    if set(files) != actual:
        raise WorkflowError(
            "incomplete-census",
            f"Missing files: {sorted(actual - set(files))}; extra files: {sorted(set(files) - actual)}",
        )
    features: dict[str, dict[str, Any]] = {}
    covered: set[str] = set()
    all_cases: set[str] = set()
    for feature in mapping["features"]:
        required = {
            "id",
            "entrypoint",
            "acceptance",
            "source_files",
            "tests",
            "not_applicable",
        }
        if not isinstance(feature, dict) or set(feature) != required:
            raise WorkflowError("invalid-feature", "Invalid feature fields")
        fid = _string(feature["id"], "feature id")
        if fid in features:
            raise WorkflowError("duplicate-feature", f"Duplicate feature {fid}")
        _string(feature["entrypoint"], "feature entrypoint")
        acceptance = feature["acceptance"]
        if isinstance(acceptance, list):
            if not acceptance:
                raise WorkflowError("invalid-feature", "Acceptance cannot be empty")
            for entry in acceptance:
                _string(entry, "acceptance")
        else:
            _string(acceptance, "acceptance")
        sources = feature["source_files"]
        if (
            not isinstance(sources, list)
            or not sources
            or len(set(sources)) != len(sources)
        ):
            raise WorkflowError(
                "invalid-feature", "source_files must be a non-empty unique list"
            )
        for name in sources:
            if files.get(name) != "production":
                raise WorkflowError(
                    "invalid-feature",
                    f"Feature source is not classified production: {name}",
                )
            project_path(root, name, must_exist=True)
            covered.add(name)
        tests, exemptions = feature["tests"], feature["not_applicable"]
        if (
            not isinstance(tests, list)
            or not tests
            or not isinstance(exemptions, dict)
            or exemptions.keys() - {"integration", "e2e"}
        ):
            raise WorkflowError("invalid-feature", "Invalid tests or layer exemptions")
        layers: set[str] = set()
        for case in tests:
            if not isinstance(case, dict) or set(case) != {
                "id",
                "name",
                "path",
                "layer",
                "planned",
            }:
                raise WorkflowError("invalid-case", "Invalid inventory test fields")
            cid = _string(case["id"], "test id")
            _string(case["name"], "test name")
            if (
                cid in all_cases
                or case["layer"] not in {"unit", "integration", "e2e"}
                or not isinstance(case["planned"], bool)
            ):
                raise WorkflowError(
                    "invalid-case", "Duplicate case or invalid layer/planned flag"
                )
            all_cases.add(cid)
            test_path = project_path(root, case["path"], must_exist=not case["planned"])
            if test_path.exists() and files.get(case["path"]) != "test":
                raise WorkflowError(
                    "invalid-case", "Existing tests must have the test file role"
                )
            if case["planned"] and files.get(case["path"]) == "production":
                raise WorkflowError(
                    "production-write",
                    "Planned tests cannot replace production files",
                    3,
                )
            layers.add(case["layer"])
        if "unit" not in layers:
            raise WorkflowError(
                "missing-unit", f"Feature {fid} needs a named unit test"
            )
        for layer in ("integration", "e2e"):
            if layer not in layers:
                _string(exemptions.get(layer), f"{fid} {layer} not-applicable reason")
            elif layer in exemptions:
                raise WorkflowError(
                    "contradictory-layer", f"{fid}: {layer} is both tested and exempt"
                )
        features[fid] = feature
    production = {name for name, kind in files.items() if kind == "production"}
    if covered != production or not features:
        raise WorkflowError(
            "unmapped-production",
            f"Unmapped production files: {sorted(production - covered)}",
        )
    assigned: set[str] = set()
    for batch in mapping["batches"]:
        if not isinstance(batch, dict) or set(batch) != {
            "id",
            "features",
            "depends_on",
        }:
            raise WorkflowError("invalid-batch", "Invalid batch fields")
        _string(batch["id"], "batch id")
        members, deps = batch["features"], batch["depends_on"]
        if (
            not isinstance(members, list)
            or not members
            or not isinstance(deps, list)
            or any(not isinstance(x, str) for x in deps)
        ):
            raise WorkflowError(
                "invalid-batch", "Batch members/dependencies must be lists"
            )
        for fid in members:
            if fid not in features or fid in assigned:
                raise WorkflowError(
                    "invalid-batch", "Unknown or multiply assigned feature"
                )
            assigned.add(fid)
    if assigned != set(features):
        raise WorkflowError(
            "incomplete-batches", "Batches must cover every feature exactly once"
        )
    task_order(mapping["batches"])
    return envelope(
        "inventory",
        {
            "coverage_status": "needs_review",
            "file_count": len(files),
            "feature_count": len(features),
            "case_count": len(all_cases),
            "batch_count": len(mapping["batches"]),
        },
        next_action="review_feature_and_assertion_coverage",
    )
