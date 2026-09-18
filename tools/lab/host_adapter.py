#!/usr/bin/env python3
"""Concrete Codex/Claude host adapter for the frozen Agentflow eval protocol.

The adapter is intentionally explicit: it reads one runner request from stdin, invokes
the selected host once per case/repetition, and emits case results on stdout. It never
chooses a release decision, changes an installation, or receives private holdout cases.

A request carrying ``business_root`` is a business request: the root is the pinned
read-only snapshot (fourth isolation position), the host writes one findings artifact per
repetition under the workspace, and ``seed_grader`` re-scores the case afterwards,
overwriting the host's self-reported ``accepted``/``escaped_defects``. A case carrying
business fields without a request-level ``business_root`` is rejected instead of being
treated as a public case. A real business run also checks the snapshot HEAD against
``target_pin`` and that the seed patch it was built from is cleanly reversible, and
re-checks the snapshot file set and the snapshot ``git diff`` digest after every host call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import seed_grader  # noqa: E402
from isolation import layout_errors  # noqa: E402
from validate import SchemaValidator, ValidationError, load_json  # noqa: E402


CASE_RESULT_SCHEMA = REPO_ROOT / "schemas" / "adapter-case-result.schema.json"

# Business request contract (PLAN-BUSINESS-EVAL-001 T08): a request carrying
# ``business_root`` must carry these six case fields, one shared snapshot pin, and a
# permission profile that can write the findings artifact. The findings artifact shape is
# frozen by ``findings_contract`` in the case and by evals/business/README.md.
BUSINESS_CASE_FIELDS = (
    "target_id",
    "target_pin",
    "target_docs",
    "seeds_ref",
    "findings_contract",
    "grading",
)
BUSINESS_PERMISSION_PROFILES = ("workspace-write", "read-write-workspace")
BUSINESS_TARGET_PIN_PATTERN = re.compile(r"^[0-9a-f]{40}$")
FINDINGS_PATH_PATTERN = "findings/{case_id}/rep-{rep}/findings.json"
FINDINGS_FORMAT = "json"
FINDINGS_REQUIRED_FIELDS = ["path", "issue", "evidence"]


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


def is_business_request(request: dict[str, Any]) -> bool:
    """A request carrying ``business_root`` is a business request; public requests never do.

    The branch is keyed on the request-level field alone. A case that carries business
    fields while the request has no ``business_root`` is rejected by
    :func:`validate_request` rather than waved through as a public case.
    """
    return "business_root" in request


def run_git(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run one read-only git command; callers decide what a non-zero exit means."""
    return subprocess.run(["git", *arguments], text=True, capture_output=True, check=False)


def snapshot_head(business_root: Path) -> str:
    """The commit the business snapshot is checked out at (the dirty tree keeps it pinned)."""
    completed = run_git(["-C", str(business_root), "rev-parse", "HEAD"])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git rev-parse exited with {completed.returncode}"
        raise ValueError(f"cannot read the business snapshot HEAD: {detail}")
    return completed.stdout.strip()


def require_seed_patch_reversible(business_root: Path, seed_patch: Path) -> None:
    """The seed patch must already be applied: reversed cleanly, with HEAD unchanged."""
    completed = run_git(["-C", str(business_root), "apply", "--check", "--reverse", str(seed_patch)])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git apply exited with {completed.returncode}"
        raise ValueError(f"seed patch is not cleanly applied to the business snapshot: {detail}")


def seed_patch_paths(business_root: Path, seed_patch: Path) -> list[str]:
    """Files the seed patch touches, read from the patch itself (nothing is written)."""
    completed = run_git(["-C", str(business_root), "apply", "--numstat", "-z", str(seed_patch)])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git apply --numstat exited with {completed.returncode}"
        raise ValueError(f"cannot read the seed patch file list: {detail}")
    return [record.split("\t", 2)[2] for record in completed.stdout.split("\0") if record]


def parse_status_paths(document: str) -> list[str]:
    """Paths in ``git status --porcelain -z`` output, sorted.

    Each record is ``XY<space>path``; a rename or copy record carries the source path as
    one extra NUL-separated field, which is consumed here (a rename is already a mismatch
    against a seed patch that only rewrites document content).
    """
    fields = document.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        if not entry:
            continue
        status = entry[:2]
        if status[0] in "RC" or status[1] in "RC":
            index += 1
        path = entry[3:]
        if path:
            paths.append(path)
    return sorted(paths)


def snapshot_status_paths(business_root: Path) -> list[str]:
    """Every path the snapshot reports as changed, untracked files included."""
    completed = run_git(
        ["-C", str(business_root), "status", "--porcelain", "-z", "--untracked-files=all"]
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git status exited with {completed.returncode}"
        raise ValueError(f"cannot read the business snapshot status: {detail}")
    return parse_status_paths(completed.stdout)


def snapshot_diff_digest(business_root: Path) -> str:
    """Digest of the snapshot's ``git diff``, i.e. of what the seeded files currently hold.

    ``snapshot_status_paths`` only sees *which* paths changed; this digest sees *what they
    changed to*, so a host that rewrites the content of an already-seeded file (same file
    set, different bytes) is caught instead of passing the per-invocation check.
    """
    completed = run_git(["-C", str(business_root), "diff", "--no-color", "--no-ext-diff"])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git diff exited with {completed.returncode}"
        raise ValueError(f"cannot read the business snapshot diff: {detail}")
    return hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest()


def snapshot_mismatch_errors(expected: list[str], actual: list[str]) -> list[str]:
    """Differences between the seed patch's file set and the snapshot's changed file set.

    A missing entry means the host restored or reverted a seeded file; an extra entry
    means the host changed the snapshot beyond the seed patch. Both fail the run closed.
    """
    errors: list[str] = []
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        errors.append("seeded files no longer show as changed: " + ", ".join(missing))
    if extra:
        errors.append("snapshot changed beyond the seed patch: " + ", ".join(extra))
    return errors


def validate_request(
    request: dict[str, Any],
    selected_host: str,
    seed_patch: Path | None = None,
    dry_run: bool = False,
) -> tuple[Path, list[dict[str, Any]]]:
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
    business_root: Path | None = None
    if is_business_request(request):
        business_root_value = request["business_root"]
        if not isinstance(business_root_value, str) or not business_root_value:
            raise ValueError("business_root must be a non-empty string")
        business_root = Path(business_root_value).resolve()
        if not business_root.is_dir():
            raise ValueError("business_root must be an existing directory")
    isolation_errors = layout_errors(repository, workspace, holdout, business_root)
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
        if not is_business_request(request):
            business_fields = [field for field in BUSINESS_CASE_FIELDS if field in case]
            if business_fields:
                raise ValueError(
                    f"case {case['case_id']!r} carries business field(s) "
                    f"{', '.join(business_fields)} but the request has no business_root; "
                    "business cases require business_root"
                )
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
    if business_root is not None:
        validate_business_request(request, business_root, cases, seed_patch, dry_run)
    return workspace, cases


def validate_findings_contract(case_id: str, contract: Any) -> None:
    """The adapter writes exactly the findings contract the case publishes; else fail closed."""
    if not isinstance(contract, dict):
        raise ValueError(f"business case {case_id!r} findings_contract must be an object")
    if contract.get("path_pattern") != FINDINGS_PATH_PATTERN:
        raise ValueError(
            f"business case {case_id!r} findings_contract.path_pattern must be {FINDINGS_PATH_PATTERN!r}"
        )
    if contract.get("format") != FINDINGS_FORMAT:
        raise ValueError(
            f"business case {case_id!r} findings_contract.format must be {FINDINGS_FORMAT!r}"
        )
    if contract.get("required_fields") != FINDINGS_REQUIRED_FIELDS:
        raise ValueError(
            f"business case {case_id!r} findings_contract.required_fields must be "
            f"{FINDINGS_REQUIRED_FIELDS!r}"
        )


def validate_business_request(
    request: dict[str, Any],
    business_root: Path,
    cases: list[dict[str, Any]],
    seed_patch: Path | None,
    dry_run: bool,
) -> None:
    """Business branch of :func:`validate_request`; every deviation raises ``ValueError``.

    A dry run stops after structure and layout (no snapshot access at all); a real run
    additionally requires ``--seed-patch``, the snapshot HEAD at the shared ``target_pin``,
    and a seed patch that is cleanly reversible on the snapshot. ``target_docs`` entries
    must be snapshot-relative POSIX paths: absolute paths and ``..`` segments are rejected
    lexically in both modes, without touching the snapshot.
    """
    profile = request["permissions_profile"]
    if profile not in BUSINESS_PERMISSION_PROFILES:
        raise ValueError(
            f"business requests require permissions_profile "
            f"{' or '.join(BUSINESS_PERMISSION_PROFILES)}; got {profile!r} "
            "(a read-only profile cannot write the findings artifact)"
        )
    pins: set[str] = set()
    for case in cases:
        case_id = case["case_id"]
        for field in BUSINESS_CASE_FIELDS:
            if field not in case:
                raise ValueError(f"business case {case_id!r} is missing the required field {field!r}")
        if not isinstance(case["target_id"], str) or not case["target_id"]:
            raise ValueError(f"business case {case_id!r} target_id must be a non-empty string")
        pin = case["target_pin"]
        if not isinstance(pin, str) or not BUSINESS_TARGET_PIN_PATTERN.match(pin):
            raise ValueError(
                f"business case {case_id!r} target_pin must be a 40-character lowercase hex revision"
            )
        pins.add(pin)
        target_docs = case["target_docs"]
        if (
            not isinstance(target_docs, list)
            or not target_docs
            or not all(isinstance(document, str) and document for document in target_docs)
        ):
            raise ValueError(
                f"business case {case_id!r} target_docs must be a non-empty array of non-empty strings"
            )
        # Path safety is lexical and runs in both modes: PurePosixPath never touches the
        # filesystem, so a dry run keeps its "no snapshot access" semantics.
        for doc in target_docs:
            if PurePosixPath(doc).is_absolute():
                raise ValueError(
                    f"business case {case_id!r} target_docs entry {doc!r} must be "
                    "a snapshot-relative POSIX path, not an absolute path"
                )
            if any(part == ".." for part in PurePosixPath(doc).parts):
                raise ValueError(
                    f"business case {case_id!r} target_docs entry {doc!r} must be "
                    "a snapshot-relative POSIX path without '..' segments"
                )
        if not isinstance(case["seeds_ref"], str) or not case["seeds_ref"]:
            raise ValueError(f"business case {case_id!r} seeds_ref must be a non-empty string")
        validate_findings_contract(case_id, case["findings_contract"])
        grading = case["grading"]
        if not isinstance(grading, dict):
            raise ValueError(f"business case {case_id!r} grading must be an object")
        min_seed_recall = grading.get("min_seed_recall")
        if (
            isinstance(min_seed_recall, bool)
            or not isinstance(min_seed_recall, (int, float))
            or not 0 <= min_seed_recall <= 1
        ):
            raise ValueError(
                f"business case {case_id!r} grading.min_seed_recall must be a number between 0 and 1"
            )
    if len(pins) != 1:
        raise ValueError("all business cases must share the same target_pin")
    target_pin = pins.pop()
    if dry_run:
        return
    if seed_patch is None:
        raise ValueError("a business real run requires --seed-patch <path>")
    if not seed_patch.is_file():
        raise ValueError(f"seed patch does not exist: {seed_patch}")
    head = snapshot_head(business_root)
    if head != target_pin:
        raise ValueError(f"business snapshot HEAD {head} does not match target_pin {target_pin}")
    require_seed_patch_reversible(business_root, seed_patch)


def permission_args(host: str, profile: str) -> list[str]:
    if host == "codex":
        if profile == "read-only":
            return ["--sandbox", "read-only"]
        if profile in {"workspace-write", "read-write-workspace"}:
            return ["--sandbox", "workspace-write"]
    if host == "claude":
        if profile == "read-only":
            return ["--permission-mode", "plan", "--disallowed-tools=Bash,Write,Edit"]
        if profile in {"workspace-write", "read-write-workspace"}:
            return ["--permission-mode", "acceptEdits"]
    raise ValueError(f"unsupported {host} permissions_profile: {profile!r}")


def findings_directory(workspace: Path, case_id: str) -> Path:
    """The per-case findings directory the host writes ``rep-<n>/findings.json`` into."""
    return workspace / "findings" / case_id


def business_prompt_block(case: dict[str, Any], repetition: int, business_root: Path) -> str:
    """The business additions: read-only snapshot, target documents, findings contract."""
    documents = "\n".join(f"- {document}" for document in case["target_docs"])
    findings_path = f"findings/{case['case_id']}/rep-{repetition}/findings.json"
    findings_shape = (
        f'{{"schema_version": 1, "case_id": "{case["case_id"]}", "findings": '
        '[{"path": "<snapshot-relative document path>", "issue": "<one-line problem statement>", '
        '"evidence": "<verbatim quote from that document>"}]}'
    )
    return f"""Business review task:
- Read-only target snapshot (absolute path): {business_root}
- The snapshot is read-only input: never modify, create, rename, or delete anything under it.
- Review exactly these documents inside the snapshot:
{documents}
- Report each defect you find in those documents with the document path, a one-line issue,
  and a verbatim quote from that document.

Findings artifact:
- Write your findings to {findings_path}, relative to your working directory.
- Use exactly this JSON shape (an empty findings array is allowed when you found nothing):
  {findings_shape}
- "path" is the snapshot-relative document path, not a path in your working directory."""


def prompt_for_case(
    request: dict[str, Any],
    case: dict[str, Any],
    input_text: str,
    repetition: int,
    business_root: Path | None = None,
) -> str:
    acceptance = "\n".join(f"- {item}" for item in case.get("acceptance_criteria", []))
    guardrails = "\n".join(f"- {item}" for item in case.get("protected_guardrails", []))
    business = ""
    if business_root is not None:
        business = "\n" + business_prompt_block(case, repetition, business_root)
    return f"""You are executing one frozen Agentflow evaluation case.

Case: {case['case_id']} (repetition {repetition}/{request['repeat_count']})
Objective: {case['objective']}

Input fixture:
{input_text}
{business}
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
        try:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"codex timed out after {timeout} seconds") from exc
        elapsed = (time.monotonic() - started) * 1000
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or f"codex exited with {completed.returncode}")
        # NamedTemporaryFile yields a file object without read_text; codex wrote the result to
        # the path it was handed via --output-last-message, so read that path (still inside the
        # context manager, before the temporary file is deleted).
        try:
            result_text = Path(output.name).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read the codex result file {output.name}: {exc}") from exc
        try:
            payload = json.loads(result_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"codex output is not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("codex output must be a JSON object")
    payload["latency_ms"] = elapsed
    return parse_structured_output("codex", json.dumps(payload))


def host_output_schema(schema: Path) -> str:
    """Return the case-result schema without meta-schema declarations some hosts reject."""
    document = json.loads(schema.read_text(encoding="utf-8"))
    for key in ("$schema", "$id"):
        document.pop(key, None)
    return json.dumps(document, separators=(",", ":"))


def claude_failure_detail(stdout: str, stderr: str, returncode: int) -> str:
    """Error text for a failed claude invocation, preferring an explicit error on stdout.

    claude writes harmless warnings to stderr even on a successful run, so taking stderr
    first drops the error object claude writes to stdout when ``--output-format json``
    fails. That stdout payload is read only when it declares itself an error: ``is_error``
    is ``true`` or an ``error`` field is present. Valid JSON without that marker — for
    example a success result carrying ``result`` text, with ``is_error: false`` or no
    ``is_error`` key at all — is not an error report, and a non-zero exit then has another
    cause; quoting its ``result`` text would present the model's answer as the failure
    detail. stderr and the raw stdout text are the fallbacks in that case.
    """
    detail = ""
    try:
        payload: Any = json.loads(stdout)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and (payload.get("is_error") is True or "error" in payload):
        for field in ("result", "error"):
            value = payload.get(field)
            if isinstance(value, str) and value.strip():
                detail = value.strip()
                break
            if isinstance(value, dict):
                message = value.get("message")
                if isinstance(message, str) and message.strip():
                    detail = message.strip()
                    break
    if not detail:
        detail = stderr.strip() or stdout.strip()
    return detail[:2000] or f"claude exited with {returncode}"


def claude_add_dir_args(request: dict[str, Any]) -> list[str]:
    """The ``--add-dir`` pair for a business request, empty for a public one.

    ``claude --print`` scopes its tool file access to the working directory (the adapter runs
    it with ``cwd=workspace``), so a business run cannot read the read-only snapshot root
    without an explicit additional directory: Read answered ``permission not granted`` and
    Bash ``only files under <cwd> are permitted`` for the snapshot, while
    ``permission_denials`` stayed empty. The flag is added only when the request carries a
    non-empty string ``business_root``; a missing, empty, or non-string value is a request
    the validation layer already rejected, so no fallback is defined here. The value is
    resolved to an absolute path: ``run_claude`` runs with ``cwd=workspace``, so a relative
    root would be re-interpreted against the workspace and silently reproduce the very
    denial this flag exists to prevent.
    """
    business_root = request.get("business_root")
    if isinstance(business_root, str) and business_root:
        return ["--add-dir", str(Path(business_root).resolve())]
    return []


def run_claude(request: dict[str, Any], prompt: str, workspace: Path, schema: Path, timeout: int) -> dict[str, Any]:
    schema_text = host_output_schema(schema)
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
        *claude_add_dir_args(request),
        *permission_args("claude", request["permissions_profile"]),
        prompt,
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=workspace, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"claude timed out after {timeout} seconds") from exc
    elapsed = (time.monotonic() - started) * 1000
    if completed.returncode != 0:
        raise RuntimeError(
            claude_failure_detail(completed.stdout, completed.stderr, completed.returncode)
        )
    try:
        raw_payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"claude output is not JSON: {exc}") from exc
    if not isinstance(raw_payload, dict):
        raise ValueError("claude output must be a JSON object")
    payload: Any = raw_payload
    if isinstance(raw_payload.get("result"), str):
        try:
            payload = json.loads(raw_payload["result"])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Claude result field is not structured JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Claude structured result must be a JSON object")
    payload["latency_ms"] = elapsed
    return parse_structured_output("claude", json.dumps(payload))


def dry_run_document(
    request: dict[str, Any],
    cases: list[dict[str, Any]],
    workspace: Path,
    host: str,
    business_root: Path | None = None,
    seed_patch: Path | None = None,
) -> dict[str, Any]:
    """Return the validated execution plan without starting a host process.

    A business plan also shows the snapshot root, the seed patch given on the command
    line, the target documents and findings paths of every case, and the prompt of the
    first repetition, so the business prompt can be reviewed without a model call. The
    dry run deliberately checks no snapshot content: no HEAD comparison, no seed patch
    replay, no per-invocation file set or content check.
    """
    document: dict[str, Any] = {
        "dry_run": True,
        "host": host,
        "model": request["model"],
        "permissions_profile": request["permissions_profile"],
        "workspace_root": str(workspace),
        "plugin_dir": str(workspace) if host == "claude" else None,
        "permission_args": permission_args(host, request["permissions_profile"]),
        "invocation_count": len(cases) * request["repeat_count"],
        "cases": [
            {
                "case_id": case["case_id"],
                "repeat_count": request["repeat_count"],
                "input_ref": case["input_ref"],
            }
            for case in cases
        ],
    }
    if business_root is None:
        return document
    document["business_root"] = str(business_root)
    document["seed_patch"] = str(seed_patch) if seed_patch is not None else None
    document["skipped_checks"] = [
        "snapshot HEAD equals target_pin",
        "seed patch applies cleanly in reverse (git apply --check --reverse)",
        "snapshot file set equals the seed patch file set after each host call",
        "snapshot git diff digest equals the seeded state after each host call",
    ]
    for entry, case in zip(document["cases"], cases):
        input_path = (Path(request["repository_root"]) / case["input_ref"]).resolve()
        entry["target_docs"] = list(case["target_docs"])
        entry["findings_pattern"] = case["findings_contract"]["path_pattern"]
        entry["findings_directory"] = str(findings_directory(workspace, case["case_id"]))
        entry["prompt"] = prompt_for_case(
            request, case, input_path.read_text(encoding="utf-8"), 1, business_root
        )
    return document


def grade_case_findings(
    repository: Path,
    workspace: Path,
    case: dict[str, Any],
    repetitions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Score one business case with ``seed_grader`` and overwrite the grader-owned metrics.

    ``accepted`` and ``escaped_defects`` come from the deterministic grader, never from the
    host: the host's self-reported values stay in the progress JSONL only. The grading
    document is written to ``<workspace>/findings/<case_id>/grading.json`` and every
    repetition gets one ``grading://`` evidence reference.

    The graded repetition set must equal the run's repetition set exactly. An ungradable
    repetition, or an extra ``rep-<n>`` directory the run did not ask for, raises
    ``ValueError`` after the grading document is written: no path returns a case without
    the grader having covered every repetition, because a returned document whose
    repetitions were left untouched would let the caller report the host's self-reported
    values as a scored success.
    """
    case_id = case["case_id"]
    seeds_ref = case["seeds_ref"]
    seeds_path = (repository / seeds_ref).resolve()
    try:
        seeds_path.relative_to(repository)
    except ValueError as exc:
        raise ValueError(f"seeds_ref escapes repository: {seeds_ref!r}") from exc
    directory = findings_directory(workspace, case_id)
    try:
        seed_document = seed_grader.load_seeds(seeds_path)
        document = seed_grader.grade_case(
            seed_document,
            directory,
            case["grading"]["min_seed_recall"],
            target_docs=case.get("target_docs"),
        )
    except seed_grader.SeedGraderError as exc:
        raise ValueError(f"cannot grade {case_id!r}: {exc}") from exc
    grading_path = directory / "grading.json"
    grading_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    graded = {item["rep"]: item for item in document["repetitions"] if item["status"] == "graded"}
    expected = set(range(1, len(repetitions) + 1))
    if set(graded) != expected:
        # Fail closed on any coverage mismatch: this is the path that used to return the
        # document unscored while the caller saw no failed repetition and reported the
        # host's self-reported accepted/escaped_defects as a scored success.
        missing = sorted(expected - set(graded))
        extra = sorted(set(graded) - expected)
        detail = []
        if missing:
            detail.append(f"ungradable repetitions {missing}")
        if extra:
            detail.append(f"unrequested repetitions {extra}")
        raise ValueError(
            f"cannot score business case {case_id!r}: grading covered repetitions "
            f"{sorted(graded)} but the run produced {sorted(expected)} "
            f"({'; '.join(detail)}); see {grading_path}"
        )
    for index, repetition in enumerate(repetitions, start=1):
        item = graded[index]
        repetition["accepted"] = item["accepted"]
        repetition["escaped_defects"] = item["escaped_defects"]
        repetition["evidence_refs"] = list(
            dict.fromkeys([*repetition["evidence_refs"], f"grading://{case_id}/rep-{index}"])
        )
    return document


def write_progress(path: Path | None, record: dict[str, Any]) -> None:
    """Append one diagnostic progress line; never part of the evaluation result."""
    if path is None:
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["codex", "claude"], required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument(
        "--progress",
        help="append per-invocation progress and failure records to this JSONL file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the request and print the host invocation plan without starting a model",
    )
    parser.add_argument(
        "--seed-patch",
        help="business runs only: the seed patch the snapshot was built from; required for a "
        "business real run, where it must be cleanly reversible (git apply --check --reverse) "
        "and its file set is re-checked after every host call",
    )
    args = parser.parse_args(argv)
    progress_path = Path(args.progress).expanduser().resolve() if args.progress else None
    seed_patch = Path(args.seed_patch).expanduser().resolve() if args.seed_patch else None

    try:
        request = load_request()
        workspace, cases = validate_request(
            request, args.host, seed_patch=seed_patch, dry_run=args.dry_run
        )
        business_root = (
            Path(request["business_root"]).resolve() if is_business_request(request) else None
        )
        if args.dry_run:
            print(
                json.dumps(
                    dry_run_document(request, cases, workspace, args.host, business_root, seed_patch),
                    ensure_ascii=False,
                )
            )
            return 0
        expected_snapshot_paths: list[str] | None = None
        expected_snapshot_digest: str | None = None
        if business_root is not None:
            if seed_patch is None:  # validate_request rejects this; kept as an explicit invariant
                raise ValueError("a business real run requires --seed-patch <path>")
            # Recorded once, after the HEAD and seed-patch checks in validate_request, and
            # re-compared after every host call: the file set alone cannot see a host that
            # rewrites the content of a file the seed patch already touched.
            expected_snapshot_paths = seed_patch_paths(business_root, seed_patch)
            expected_snapshot_digest = snapshot_diff_digest(business_root)
        results: list[dict[str, Any]] = []
        for case in cases:
            input_path = (Path(request["repository_root"]) / case["input_ref"]).resolve()
            input_text = input_path.read_text(encoding="utf-8")
            repetitions: list[dict[str, Any]] = []
            for repetition in range(1, request["repeat_count"] + 1):
                if business_root is not None:
                    (findings_directory(workspace, case["case_id"]) / f"rep-{repetition}").mkdir(
                        parents=True, exist_ok=True
                    )
                prompt = prompt_for_case(request, case, input_text, repetition, business_root)
                started = time.monotonic()
                write_progress(
                    progress_path,
                    {"event": "start", "case_id": case["case_id"], "repetition": repetition},
                )
                try:
                    if args.host == "codex":
                        result = run_codex(request, prompt, workspace, CASE_RESULT_SCHEMA, args.timeout_seconds)
                    else:
                        result = run_claude(request, prompt, workspace, CASE_RESULT_SCHEMA, args.timeout_seconds)
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    write_progress(
                        progress_path,
                        {
                            "event": "failed",
                            "case_id": case["case_id"],
                            "repetition": repetition,
                            "elapsed_ms": round((time.monotonic() - started) * 1000),
                            "error": str(exc),
                        },
                    )
                    error(f"{case['case_id']} repetition {repetition} failed: {exc}")
                    raise
                elapsed_ms = round((time.monotonic() - started) * 1000)
                if business_root is not None and expected_snapshot_paths is not None:
                    mismatches = snapshot_mismatch_errors(
                        expected_snapshot_paths, snapshot_status_paths(business_root)
                    )
                    if expected_snapshot_digest is not None:
                        actual_digest = snapshot_diff_digest(business_root)
                        if actual_digest != expected_snapshot_digest:
                            mismatches.append(
                                "snapshot content drifted in the seeded files: the git diff "
                                f"digest changed from {expected_snapshot_digest} to {actual_digest}"
                            )
                    if mismatches:
                        detail = (
                            "business snapshot status does not match the seed patch: "
                            + "; ".join(mismatches)
                        )
                        write_progress(
                            progress_path,
                            {
                                "event": "failed",
                                "case_id": case["case_id"],
                                "repetition": repetition,
                                "elapsed_ms": elapsed_ms,
                                "error": detail,
                            },
                        )
                        raise ValueError(detail)
                completed_record = {
                    "event": "completed",
                    "case_id": case["case_id"],
                    "repetition": repetition,
                    "elapsed_ms": elapsed_ms,
                    "accepted": result.get("accepted"),
                }
                if business_root is not None:
                    # The grader overwrites accepted/escaped_defects later; the host's raw
                    # self-report stays here, next to the other per-invocation diagnostics.
                    completed_record["first_pass_review"] = result.get("first_pass_review")
                write_progress(progress_path, completed_record)
                print(
                    f"host adapter: {case['case_id']} repetition {repetition} completed in {elapsed_ms} ms",
                    file=sys.stderr,
                )
                repetitions.append(result)
            if business_root is not None:
                try:
                    grading_document = grade_case_findings(
                        Path(request["repository_root"]).resolve(), workspace, case, repetitions
                    )
                except (OSError, ValueError) as exc:
                    write_progress(
                        progress_path,
                        {
                            "event": "failed",
                            "case_id": case["case_id"],
                            "repetition": None,
                            "error": str(exc),
                        },
                    )
                    raise
                ungraded = [
                    item for item in grading_document["repetitions"] if item["status"] != "graded"
                ]
                if ungraded:
                    for item in ungraded:
                        write_progress(
                            progress_path,
                            {
                                "event": "failed",
                                "case_id": case["case_id"],
                                "repetition": item["rep"],
                                "error": "grading failed: " + item["error"],
                            },
                        )
                    raise ValueError(
                        f"{case['case_id']} could not be graded for {len(ungraded)} repetition(s); "
                        f"see {findings_directory(workspace, case['case_id']) / 'grading.json'}"
                    )
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
