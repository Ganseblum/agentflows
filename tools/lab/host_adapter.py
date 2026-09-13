#!/usr/bin/env python3
"""Concrete Codex/Claude host adapter for the frozen Agentflow eval protocol.

The adapter is intentionally explicit: it reads one runner request from stdin, invokes
the selected host once per case/repetition, and emits case results on stdout. It never
chooses a release decision, changes an installation, or receives private holdout cases.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from isolation import layout_errors  # noqa: E402
from validate import SchemaValidator, ValidationError, load_json  # noqa: E402


CASE_RESULT_SCHEMA = REPO_ROOT / "schemas" / "adapter-case-result.schema.json"


def error(message: str) -> None:
    print(f"host adapter: {message}", file=sys.stderr)


def load_request() -> dict[str, Any]:
    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise ValueError(f"request is not JSON: {exc}") from exc
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    return request


def require_string(request: dict[str, Any], field: str) -> str:
    value = request.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def validate_request(request: dict[str, Any], selected_host: str) -> tuple[Path, list[dict[str, Any]]]:
    if request.get("protocol_version") != 1:
        raise ValueError("unsupported protocol_version")
    if request.get("host") != selected_host:
        raise ValueError("selected host does not match request host")
    for field in (
        "source_kind",
        "source_revision",
        "artifact_digest",
        "result_id",
        "agentflow_version",
        "suite_revision",
        "host",
        "model",
        "permissions_profile",
        "fixture_revision",
        "repository_root",
        "workspace_root",
        "holdout_root",
    ):
        require_string(request, field)
    if selected_host == "codex" and request["source_kind"] == "candidate":
        raise ValueError(
            "Codex CLI cannot bind an uninstalled candidate Plugin source; use a reviewed host installation adapter"
        )
    repeat_count = request.get("repeat_count")
    if not isinstance(repeat_count, int) or isinstance(repeat_count, bool) or repeat_count < 1:
        raise ValueError("repeat_count must be a positive integer")

    repository = Path(request["repository_root"]).resolve()
    workspace = Path(request["workspace_root"]).resolve()
    holdout = Path(request["holdout_root"]).resolve()
    isolation_errors = layout_errors(repository, workspace, holdout)
    if repository == workspace:
        isolation_errors.append("workspace must be separate from repository")
    if isolation_errors:
        raise ValueError("invalid isolation layout: " + "; ".join(isolation_errors))
    if not repository.is_dir() or not workspace.is_dir() or not holdout.is_dir():
        raise ValueError("repository, workspace, and holdout_root must be existing directories")

    cases = request.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty array")
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}] must be an object")
        for field in ("case_id", "slice", "objective", "input_ref"):
            if not isinstance(case.get(field), str) or not case[field]:
                raise ValueError(f"cases[{index}].{field} must be a non-empty string")
        if case.get("holdout") is not False:
            raise ValueError(f"refusing to expose holdout case {case.get('case_id')!r}")
        if case.get("repeat_count") != repeat_count:
            raise ValueError(f"case {case['case_id']!r} repeat_count does not match request")
        input_path = (repository / case["input_ref"]).resolve()
        try:
            input_path.relative_to(repository)
        except ValueError as exc:
            raise ValueError(f"input_ref escapes repository: {case['input_ref']!r}") from exc
        if not input_path.is_file():
            raise ValueError(f"input_ref does not exist: {case['input_ref']!r}")
    return workspace, cases


def permission_args(host: str, profile: str) -> list[str]:
    if host == "codex":
        if profile == "read-only":
            return ["--sandbox", "read-only"]
        if profile in {"workspace-write", "read-write-workspace"}:
            return ["--sandbox", "workspace-write"]
    if host == "claude":
        if profile == "read-only":
            return ["--permission-mode", "plan", "--disallowed-tools", "Bash", "Write", "Edit"]
        if profile in {"workspace-write", "read-write-workspace"}:
            return ["--permission-mode", "acceptEdits"]
    raise ValueError(f"unsupported {host} permissions_profile: {profile!r}")


def prompt_for_case(request: dict[str, Any], case: dict[str, Any], input_text: str, repetition: int) -> str:
    acceptance = "\n".join(f"- {item}" for item in case.get("acceptance_criteria", []))
    guardrails = "\n".join(f"- {item}" for item in case.get("protected_guardrails", []))
    return f"""You are executing one frozen Agentflow evaluation case.

Case: {case['case_id']} (repetition {repetition}/{request['repeat_count']})
Objective: {case['objective']}

Input fixture:
{input_text}

Acceptance criteria:
{acceptance}

Protected guardrails:
{guardrails}

Execution boundaries:
- Work only in the supplied workspace; do not inspect or access the holdout directory.
- Follow the host's actual permission mode; do not claim checks you did not perform.
- Do not publish, install, commit, or modify release policy.
- Return only the JSON object required by the adapter result schema.
- evidence_refs must point to observable output, checks, or files from this repetition.

After doing the task, report the structured result. Treat acceptance and review as
evidence-based outcomes, not intentions.
"""


def parse_structured_output(host: str, stdout: str) -> dict[str, Any]:
    try:
        raw = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{host} output is not JSON: {exc}") from exc
    payload: Any = raw
    if host == "claude" and isinstance(raw, dict) and isinstance(raw.get("result"), str):
        try:
            payload = json.loads(raw["result"])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Claude result field is not structured JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("host output must be a JSON object")
    errors = SchemaValidator(CASE_RESULT_SCHEMA).validate(payload)
    if errors:
        raise ValueError("host output failed adapter-case-result schema: " + "; ".join(str(item) for item in errors))
    return payload


def run_codex(request: dict[str, Any], prompt: str, workspace: Path, schema: Path, timeout: int) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(prefix="agentflow-codex-result-", suffix=".json", delete=True) as output:
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--cd",
            str(workspace),
            "--model",
            request["model"],
            *permission_args("codex", request["permissions_profile"]),
            "--output-schema",
            str(schema),
            "--output-last-message",
            output.name,
            prompt,
        ]
        started = time.monotonic()
        completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        elapsed = (time.monotonic() - started) * 1000
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or f"codex exited with {completed.returncode}")
        payload = json.loads(output.read_text(encoding="utf-8"))
    payload["latency_ms"] = elapsed
    return parse_structured_output("codex", json.dumps(payload))


def run_claude(request: dict[str, Any], prompt: str, workspace: Path, schema: Path, timeout: int) -> dict[str, Any]:
    schema_text = schema.read_text(encoding="utf-8")
    command = [
        "claude",
        "--print",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--json-schema",
        schema_text,
        "--model",
        request["model"],
        "--plugin-dir",
        str(workspace),
        *permission_args("claude", request["permissions_profile"]),
        prompt,
    ]
    started = time.monotonic()
    completed = subprocess.run(command, cwd=workspace, text=True, capture_output=True, timeout=timeout, check=False)
    elapsed = (time.monotonic() - started) * 1000
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"claude exited with {completed.returncode}")
    payload = parse_structured_output("claude", completed.stdout)
    payload["latency_ms"] = elapsed
    return parse_structured_output("claude", json.dumps(payload))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["codex", "claude"], required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args(argv)

    try:
        request = load_request()
        workspace, cases = validate_request(request, args.host)
        results: list[dict[str, Any]] = []
        for case in cases:
            input_path = (Path(request["repository_root"]) / case["input_ref"]).resolve()
            input_text = input_path.read_text(encoding="utf-8")
            repetitions: list[dict[str, Any]] = []
            for repetition in range(1, request["repeat_count"] + 1):
                prompt = prompt_for_case(request, case, input_text, repetition)
                if args.host == "codex":
                    result = run_codex(request, prompt, workspace, CASE_RESULT_SCHEMA, args.timeout_seconds)
                else:
                    result = run_claude(request, prompt, workspace, CASE_RESULT_SCHEMA, args.timeout_seconds)
                repetitions.append(result)
            results.append(
                {
                    "case_id": case["case_id"],
                    "slice": case["slice"],
                    "holdout": case["holdout"],
                    "protected_guardrails": case.get("protected_guardrails", []),
                    "repetitions": repetitions,
                }
            )
        print(
            json.dumps(
                {
                    "observed_context": {
                        "host": request["host"],
                        "model": request["model"],
                        "permissions_profile": request["permissions_profile"],
                        "fixture_revision": request["fixture_revision"],
                        "evidence_refs": [f"adapter://{args.host}/{request['result_id']}"],
                    },
                    "case_results": results,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
