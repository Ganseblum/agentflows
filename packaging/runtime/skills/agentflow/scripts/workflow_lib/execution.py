"""Bounded commands with dependency-aware evidence and execution snapshots."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from .reports import parse_report
from .snapshots import (
    WorkflowError,
    changed_paths,
    check_bound_inputs,
    envelope,
    fingerprint,
    load_sealed,
    no_symlinks,
    project_path,
    snapshot,
    task_order,
    tracked_files,
    verified_snapshot,
    write_json_new,
)

MAX_OUTPUT_BYTES = 8 * 1024 * 1024


def _stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=1)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait()


def _command(task: dict[str, Any], root: Path, output: Path) -> dict[str, Any]:
    stdout_path, stderr_path = (
        output / f"{task['id']}.stdout",
        output / f"{task['id']}.stderr",
    )
    evidence: dict[str, Any] = {"stdout": str(stdout_path), "stderr": str(stderr_path)}
    start = time.monotonic()
    # No environment values are copied into plan/result JSON. Avoid generating Python cache
    # files inside source snapshots while using the caller's existing runtime authority.
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    reason: str | None = None
    returncode: int | None = None
    out_fd = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    err_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(out_fd, "wb") as stdout, os.fdopen(err_fd, "wb") as stderr:
        try:
            process = subprocess.Popen(
                task["argv"],
                cwd=project_path(root, task["cwd"], True, True),
                stdout=stdout,
                stderr=stderr,
                stdin=subprocess.DEVNULL,
                shell=False,
                env=environment,
                start_new_session=os.name != "nt",
            )
        except OSError as exc:
            evidence["process_error"] = str(exc)
            reason = "command-unavailable"
        else:
            while process.poll() is None:
                if time.monotonic() - start >= task["timeout_seconds"]:
                    reason = "command-timeout"
                    _stop(process)
                    break
                if (
                    stdout_path.stat().st_size + stderr_path.stat().st_size
                    > MAX_OUTPUT_BYTES
                ):
                    reason = "output-limit"
                    _stop(process)
                    break
                time.sleep(0.02)
            returncode = process.wait()
    if stdout_path.stat().st_size + stderr_path.stat().st_size > MAX_OUTPUT_BYTES:
        reason = "output-limit"
    evidence.update(
        {
            "returncode": returncode,
            "duration_seconds": round(time.monotonic() - start, 6),
        }
    )
    return {
        "id": task["id"],
        "status": "fail" if reason else "not-run",
        "cases": [],
        "error_kind": reason,
        "evidence": evidence,
    }


def _report(
    task: dict[str, Any], result: dict[str, Any], root: Path, phase: str
) -> None:
    if result["error_kind"]:
        return
    if task["reporter"] == "exit":
        result["status"] = "pass" if result["evidence"]["returncode"] == 0 else "fail"
        result["error_kind"] = None if result["status"] == "pass" else "command-failed"
        return
    report_path = (
        project_path(root, task["report_path"], must_exist=True)
        if "report_path" in task
        else Path(result["evidence"]["stdout"])
    )
    result["evidence"]["report"] = str(report_path)
    if report_path.stat().st_size > MAX_OUTPUT_BYTES:
        raise WorkflowError("output-limit", "Native report exceeds output limit", 1)
    try:
        cases = parse_report(task["reporter"], report_path.read_text(encoding="utf-8"))
    except (UnicodeError, OSError) as exc:
        raise WorkflowError(
            "invalid-report", f"Cannot read current report: {exc}", 1
        ) from exc
    discovered = {case["name"]: case["status"] for case in cases}
    selected = []
    for expected in task["cases"]:
        name = expected["report_name"]
        if name not in discovered:
            raise WorkflowError(
                "missing-case", f"Current report does not contain {name!r}", 1
            )
        selected.append({**expected, "status": discovered[name]})
    result["cases"] = selected
    result["evidence"]["discovered_cases"] = cases
    code = result["evidence"]["returncode"]
    if phase == "red" and task["kind"] == "test":
        passed = code not in {0, None} and all(
            case["status"] == "fail" for case in selected
        )
        result["evidence"]["failure_cause_review"] = "required"
    else:
        passed = code == 0 and all(case["status"] == "pass" for case in cases)
    result["status"] = "pass" if passed else "fail"
    result["error_kind"] = None if passed else "unexpected-test-result"


def run_plan(
    root: Path | str,
    sealed_path: Path | str,
    expected: str,
    output_dir: Path | str,
    phase: str = "green",
) -> dict[str, Any]:
    if phase not in {"green", "red"}:
        raise WorkflowError("invalid-phase", "Phase must be green or red")
    root, sealed = load_sealed(root, sealed_path, expected)
    if phase == "red" and not any(
        task["kind"] == "test" for task in sealed["request"]["tasks"]
    ):
        raise WorkflowError("invalid-phase", "Red observation requires a behavior test")
    output = no_symlinks(output_dir)
    try:
        output_relative = output.relative_to(root).as_posix()
    except ValueError:
        output_relative = None
    if output_relative is not None:
        inputs = {entry["path"] for entry in sealed["baseline_inputs"]} | tracked_files(
            root
        )
        inputs.add(sealed["request"]["plan"])
        inputs.update(sealed["request"]["allowed_writes"])
        if output_relative == "." or any(
            name == output_relative or name.startswith(output_relative + "/")
            for name in inputs
        ):
            raise WorkflowError(
                "evidence-is-input",
                "Output directory contains tracked/production inputs",
                3,
            )
        # A new untracked input may have appeared after sealing. It cannot be hidden by
        # subsequently calling that directory evidence.
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            raise WorkflowError(
                "evidence-exists", f"Output directory is not empty: {output}", 3
            )
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise WorkflowError(
            "evidence-exists", f"Use a new/empty evidence directory: {output}", 3
        )
    initial = verified_snapshot(root, sealed, output_relative)
    for task in sealed["request"]["tasks"]:
        if "report_path" in task and project_path(root, task["report_path"]).exists():
            raise WorkflowError(
                "stale-report",
                f"Report must be newly produced: {task['report_path']}",
                3,
            )
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    tasks = task_order(sealed["request"]["tasks"])
    results: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    refusal: str | None = None
    for task in tasks:
        if refusal:
            result = {
                "id": task["id"],
                "status": "not-run",
                "cases": [],
                "error_kind": refusal,
                "evidence": {"reason": "Earlier execution input drift"},
            }
        elif any(by_id[dep]["status"] != "pass" for dep in task["depends_on"]):
            result = {
                "id": task["id"],
                "status": "blocked",
                "cases": [],
                "error_kind": "dependency-failed",
                "evidence": {"depends_on": task["depends_on"]},
            }
        else:
            try:
                check_bound_inputs(root, sealed, sealed_path)
                before = snapshot(root, set(sealed["excluded_files"]), output_relative)
                if changed_paths(initial, before):
                    raise WorkflowError(
                        "execution-drift", "Inputs changed before the next command", 3
                    )
                # Recheck the report directly before its command, not just once per run.
                if (
                    "report_path" in task
                    and project_path(root, task["report_path"]).exists()
                ):
                    raise WorkflowError(
                        "stale-report",
                        "A report existed before its producer command",
                        3,
                    )
                result = _command(task, root, output)
                check_bound_inputs(root, sealed, sealed_path)
                after = snapshot(root, set(sealed["excluded_files"]), output_relative)
                changed = changed_paths(initial, after)
                if changed:
                    raise WorkflowError(
                        "execution-drift",
                        "Inputs changed during execution: " + ", ".join(changed),
                        3,
                    )
                _report(task, result, root, phase)
            except WorkflowError as exc:
                if "result" not in locals() or result.get("id") != task["id"]:
                    result = {"id": task["id"], "cases": [], "evidence": {}}
                result.update({"status": "fail", "error_kind": exc.kind})
                result["evidence"]["reason"] = str(exc)
                if exc.code == 3:
                    refusal = exc.kind
        result["kind"] = task["kind"]
        results.append(result)
        by_id[task["id"]] = result
    finalization_error: str | None = None
    try:
        check_bound_inputs(root, sealed, sealed_path)
        final = snapshot(root, set(sealed["excluded_files"]), output_relative)
        changed = changed_paths(initial, final)
        if changed:
            raise WorkflowError(
                "execution-drift", "Inputs changed before finalization: " + ", ".join(changed), 3
            )
    except WorkflowError as exc:
        refusal = refusal or exc.kind
        finalization_error = str(exc)
    if refusal:
        code, state = 3, "refused"
    elif any(row["status"] == "fail" for row in results):
        code, state = 1, "fail"
    elif any(row["status"] in {"blocked", "not-run"} for row in results):
        code, state = 4, "partial"
    else:
        code, state = 0, "pass"
    result_document = {
        "schema_version": 1,
        "phase": phase,
        "execution_status": state,
        "coverage_status": "needs_review",
        "fingerprint": sealed["fingerprint"],
        "execution_snapshot": fingerprint(initial),
        "tasks": results,
    }
    if finalization_error:
        result_document["finalization_error"] = finalization_error
    result_path = write_json_new(output / "result.json", result_document)
    return envelope(
        "run",
        {**result_document, "result_file": str(result_path)},
        code,
        kind=refusal or ("verification-failed" if code == 1 else None),
        next_action="review_coverage"
        if code == 0
        else "resolve_failed_or_blocked_tasks",
    )
