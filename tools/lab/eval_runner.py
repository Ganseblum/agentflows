#!/usr/bin/env python3
"""Run an explicit Agentflow host adapter and compare frozen results.

The runner owns the evaluation context and result normalization. It does not start a
model loop itself: an adapter command supplied by the caller receives a JSON request
on stdin and returns ``{"case_results": [...]}`` on stdout.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate import (  # noqa: E402
    ROOT,
    SchemaValidator,
    ValidationError,
    load_json,
    validate_document,
    validate_evaluation_result_invariants,
    validate_evals,
)
from isolation import layout_errors  # noqa: E402


RESULT_SCHEMA = ROOT / "schemas" / "evaluation-result.schema.json"
BUSINESS_CASE_SCHEMA = ROOT / "skills" / "improve" / "references" / "business-case.schema.json"
BUSINESS_CASE_FIELDS = (
    "target_id",
    "target_pin",
    "target_docs",
    "seeds_ref",
    "findings_contract",
    "grading",
)
METRIC_NAMES = (
    "acceptance_rate",
    "first_pass_review_rate",
    "correction_count",
    "escaped_defects",
    "permission_violations",
    "unnecessary_delegation_count",
    "tool_failures",
    "latency_ms",
)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def is_public_suite(suite_dir: Path) -> bool:
    """Only the repository's own evals/public directory uses the public suite contract."""
    return suite_dir.resolve() == (ROOT / "evals" / "public").resolve()


def validate_document_against(schema_path: Path, document: Any, path: Path) -> list[ValidationError]:
    """Validate one document against an explicit schema path.

    Business cases carry their own contract (``business-case.schema.json``); the repository
    schema map used by ``validate_document`` does not cover ``evals/business``, so the
    suite passes the schema path explicitly instead.
    """
    try:
        errors = SchemaValidator(schema_path).validate(document)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(schema_path), f"validator setup failed: {exc}")]
    return errors


def validate_result(document: Any) -> list[ValidationError]:
    try:
        errors = SchemaValidator(RESULT_SCHEMA).validate(document)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(RESULT_SCHEMA), f"validator setup failed: {exc}")]
    if not errors and isinstance(document, dict):
        errors.extend(validate_evaluation_result_invariants(document, RESULT_SCHEMA))
    return errors


def print_errors(errors: list[ValidationError]) -> None:
    for error in errors:
        print(f"  - {error}", file=sys.stderr)


def load_suite(suite_dir: Path) -> list[dict[str, Any]]:
    suite_dir = suite_dir.resolve()
    try:
        suite_dir.relative_to(ROOT.resolve())
    except ValueError:
        print(f"suite directory must be inside the repository: {suite_dir}", file=sys.stderr)
        raise SystemExit(1)
    if not suite_dir.is_dir():
        print(f"suite directory does not exist: {suite_dir}", file=sys.stderr)
        raise SystemExit(1)
    cases: list[dict[str, Any]] = []
    public_suite = is_public_suite(suite_dir)
    pattern = "AF-*.json" if public_suite else "BT-*.json"
    for path in sorted(suite_dir.glob(pattern)):
        document, load_errors = load_json(path)
        if load_errors or not isinstance(document, dict):
            print_errors(load_errors)
            raise SystemExit(1)
        if public_suite:
            contract_errors = validate_document(path)
        else:
            contract_errors = validate_document_against(BUSINESS_CASE_SCHEMA, document, path)
        if contract_errors:
            print(f"invalid evaluation case: {path}", file=sys.stderr)
            print_errors(contract_errors)
            raise SystemExit(1)
        if document.get("holdout") is True:
            print(f"refusing to expose holdout case to an adapter: {path}", file=sys.stderr)
            raise SystemExit(1)
        cases.append(document)
    if not cases:
        print(f"suite contains no {pattern} cases: {suite_dir}", file=sys.stderr)
        raise SystemExit(1)
    if public_suite:
        errors = validate_evals()
        if errors:
            print("public evaluation suite is invalid", file=sys.stderr)
            print_errors(errors)
            raise SystemExit(1)
    return cases


def summarize(case_results: list[dict[str, Any]]) -> dict[str, int | float]:
    repetitions = [rep for case in case_results for rep in case["repetitions"]]
    count = len(repetitions)
    if count == 0:
        raise ValueError("at least one repetition is required")
    accepted = sum(1 for rep in repetitions if rep["accepted"])
    first_pass = sum(1 for rep in repetitions if rep["first_pass_review"])
    return {
        "acceptance_rate": accepted / count,
        "first_pass_review_rate": first_pass / count,
        "correction_count": sum(rep["correction_count"] for rep in repetitions),
        "escaped_defects": sum(rep["escaped_defects"] for rep in repetitions),
        "permission_violations": sum(rep["permission_violations"] for rep in repetitions),
        "unnecessary_delegation_count": sum(1 for rep in repetitions if rep["unnecessary_delegation"]),
        "tool_failures": sum(rep["tool_failures"] for rep in repetitions),
        "latency_ms": sum(rep["latency_ms"] for rep in repetitions) / count,
    }


def build_request(
    args: argparse.Namespace,
    cases: list[dict[str, Any]],
    business: bool | None = None,
) -> dict[str, Any]:
    if business is None:
        business = any("target_id" in case for case in cases)
    business_root = getattr(args, "business_root", None)
    if business and not business_root:
        raise ValueError("a business suite requires --business-root")
    request: dict[str, Any] = {
        "protocol_version": 1,
        "source_kind": args.source_kind,
        "source_revision": args.source_revision,
        "artifact_digest": args.artifact_digest,
        "result_id": args.result_id,
        "agentflow_version": args.agentflow_version,
        "suite_revision": args.suite_revision,
        "host": args.host,
        "model": args.model,
        "permissions_profile": args.permissions_profile,
        "fixture_revision": args.fixture_revision,
        "repeat_count": args.repeat_count,
        "repository_root": str(Path(args.repository).resolve()),
        "workspace_root": str(Path(args.workspace).resolve()),
        "holdout_root": str(Path(args.holdout_root).resolve()),
    }
    allowed_tools = getattr(args, "allowed_tools", None)
    if allowed_tools:
        request["allowed_tools"] = [tool.strip() for tool in allowed_tools.split(",") if tool.strip()]
    if getattr(args, "isolate_host_config", False):
        request["isolate_host_config"] = True
    if business:
        request["business_root"] = str(Path(business_root).resolve())
    # A case's repeat_count is frozen in the suite file: --repeat-count must agree with
    # every declared value, otherwise the run silently overwrites the frozen value and
    # baseline/candidate runs stop being comparable.
    frozen_mismatches: list[str] = []
    for case in cases:
        if "repeat_count" not in case:
            # A case that omits repeat_count would silently inherit --repeat-count below,
            # which is exactly the overwrite the frozen-value check exists to prevent.
            frozen_mismatches.append(
                f"case {case['case_id']!r} does not declare repeat_count; "
                "every case must freeze its repetition count in the suite file"
            )
        elif case["repeat_count"] != args.repeat_count:
            frozen_mismatches.append(
                f"case {case['case_id']!r} declares repeat_count {case['repeat_count']!r} but "
                f"--repeat-count is {args.repeat_count!r}"
            )
    if frozen_mismatches:
        raise ValueError("; ".join(frozen_mismatches) + "; a run must use the frozen case value")
    request_cases: list[dict[str, Any]] = []
    for case in cases:
        entry = {
            "case_id": case["case_id"],
            "slice": case["slice"],
            "objective": case["objective"],
            "input_ref": case["input_ref"],
            "acceptance_criteria": case["acceptance_criteria"],
            "protected_guardrails": case["protected_guardrails"],
            "holdout": case["holdout"],
            "repeat_count": args.repeat_count,
        }
        if business:
            for field in BUSINESS_CASE_FIELDS:
                entry[field] = case[field]
        request_cases.append(entry)
    request["cases"] = request_cases
    return request


def validate_adapter_response(
    adapter_result: Any,
    cases: list[dict[str, Any]],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]] | None, list[ValidationError]]:
    errors: list[ValidationError] = []
    if not isinstance(adapter_result, dict):
        return None, [ValidationError("adapter", "response must be an object")]

    observed = adapter_result.get("observed_context")
    if not isinstance(observed, dict):
        errors.append(ValidationError("adapter.observed_context", "required object is missing"))
    else:
        expected_observed = {
            "host": args.host,
            "model": args.model,
            "permissions_profile": args.permissions_profile,
            "fixture_revision": args.fixture_revision,
        }
        for field, expected in expected_observed.items():
            if observed.get(field) != expected:
                errors.append(ValidationError(f"adapter.observed_context.{field}", "does not match the declared run context"))
        if not isinstance(observed.get("evidence_refs"), list) or not observed["evidence_refs"]:
            errors.append(ValidationError("adapter.observed_context.evidence_refs", "must contain at least one reference"))

    actual_results = adapter_result.get("case_results")
    if not isinstance(actual_results, list):
        errors.append(ValidationError("adapter.case_results", "required array is missing"))
        return None, errors

    expected_by_id = {case["case_id"]: case for case in cases}
    actual_by_id: dict[str, dict[str, Any]] = {}
    for index, result in enumerate(actual_results):
        if not isinstance(result, dict):
            errors.append(ValidationError(f"adapter.case_results[{index}]", "must be an object"))
            continue
        case_id = result.get("case_id")
        if case_id in actual_by_id:
            errors.append(ValidationError(f"adapter.case_results[{index}].case_id", "duplicate case_id"))
        if case_id not in expected_by_id:
            errors.append(ValidationError(f"adapter.case_results[{index}].case_id", "unknown case_id"))
        else:
            actual_by_id[case_id] = result

    ordered: list[dict[str, Any]] = []
    required_metrics = {
        "accepted",
        "first_pass_review",
        "correction_count",
        "escaped_defects",
        "permission_violations",
        "unnecessary_delegation",
        "tool_failures",
        "latency_ms",
        "evidence_refs",
    }
    for index, case in enumerate(cases):
        case_id = case["case_id"]
        result = actual_by_id.get(case_id)
        if result is None:
            errors.append(ValidationError(f"adapter.case_results[{index}]", f"missing case_id {case_id!r}"))
            continue
        for field in ("slice", "holdout", "protected_guardrails"):
            if result.get(field) != case[field]:
                errors.append(ValidationError(f"adapter.case_results[{case_id}].{field}", "does not match the frozen suite"))
        repetitions = result.get("repetitions")
        if not isinstance(repetitions, list) or len(repetitions) != args.repeat_count:
            errors.append(ValidationError(f"adapter.case_results[{case_id}].repetitions", f"must contain exactly {args.repeat_count} items"))
        else:
            for repetition_index, repetition in enumerate(repetitions):
                if not isinstance(repetition, dict):
                    errors.append(ValidationError(f"adapter.case_results[{case_id}].repetitions[{repetition_index}]", "must be an object"))
                    continue
                missing = sorted(required_metrics - repetition.keys())
                if missing:
                    errors.append(ValidationError(f"adapter.case_results[{case_id}].repetitions[{repetition_index}]", f"missing {missing!r}"))
                if not isinstance(repetition.get("evidence_refs"), list) or not repetition["evidence_refs"]:
                    errors.append(ValidationError(f"adapter.case_results[{case_id}].repetitions[{repetition_index}].evidence_refs", "must contain at least one reference"))
        ordered.append(result)
    if set(actual_by_id) != set(expected_by_id):
        errors.append(ValidationError("adapter.case_results", "case coverage does not exactly match the frozen suite"))
    return (ordered if not errors else None), errors


def run_adapter(args: argparse.Namespace) -> int:
    suite_dir = (ROOT / args.suite).resolve()
    public_suite = is_public_suite(suite_dir)
    cases = load_suite(suite_dir)
    repository = Path(args.repository).resolve()
    workspace = Path(args.workspace).resolve()
    holdout_root = Path(args.holdout_root).resolve()
    business_root_value = getattr(args, "business_root", None)
    if not public_suite and not business_root_value:
        print(f"--business-root is required for the suite: {suite_dir}", file=sys.stderr)
        return 1
    business_root = Path(business_root_value).resolve() if business_root_value else None
    if public_suite:
        isolation_errors = layout_errors(repository, workspace, holdout_root)
    else:
        isolation_errors = layout_errors(repository, workspace, holdout_root, business_root)
    if repository == workspace:
        isolation_errors.append("adapter workspace must be separate from the public repository")
    if isolation_errors:
        print("invalid evaluation isolation layout", file=sys.stderr)
        for error in isolation_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    request = build_request(args, cases, business=not public_suite)
    command = shlex.split(args.adapter)
    if not command:
        print("adapter command must not be empty", file=sys.stderr)
        return 1
    completed = subprocess.run(
        command,
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0:
        print(f"adapter exited with {completed.returncode}", file=sys.stderr)
        if completed.stderr:
            print(completed.stderr.rstrip(), file=sys.stderr)
        return completed.returncode or 1
    try:
        adapter_result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        print(f"adapter stdout is not JSON: {exc}", file=sys.stderr)
        return 1
    normalized_cases, conformance_errors = validate_adapter_response(adapter_result, cases, args)
    if conformance_errors:
        print("adapter response failed conformance checks", file=sys.stderr)
        print_errors(conformance_errors)
        return 1

    result = {
        "schema_version": 1,
        "result_id": args.result_id,
        "source_kind": args.source_kind,
        "source_revision": args.source_revision,
        "artifact_digest": args.artifact_digest,
        "agentflow_version": args.agentflow_version,
        "suite_revision": args.suite_revision,
        "host": args.host,
        "model": args.model,
        "permissions_profile": args.permissions_profile,
        "fixture_revision": args.fixture_revision,
        "repeat_count": args.repeat_count,
        "suite_case_count": len(cases),
        "observed_context": adapter_result["observed_context"],
        "case_results": normalized_cases,
        "summary": summarize(normalized_cases),
        "generated_at": now_utc(),
    }
    errors = validate_result(result)
    if errors:
        print("normalized adapter result is invalid", file=sys.stderr)
        print_errors(errors)
        return 1
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"WROTE {output}")
    return 0


def load_result(path_value: str) -> tuple[dict[str, Any] | None, list[ValidationError]]:
    path = Path(path_value).resolve()
    document, errors = load_json(path)
    if errors:
        return None, errors
    if not isinstance(document, dict):
        return None, [ValidationError(str(path), "result must be a JSON object")]
    errors.extend(validate_result(document))
    return document, errors


def validate_command(args: argparse.Namespace) -> int:
    document, errors = load_result(args.result)
    if errors:
        print("FAIL result", file=sys.stderr)
        print_errors(errors)
        return 1
    assert document is not None
    print(f"PASS result {document['result_id']}")
    return 0


def compare_command(args: argparse.Namespace) -> int:
    baseline, baseline_errors = load_result(args.baseline)
    candidate, candidate_errors = load_result(args.candidate)
    errors = baseline_errors + candidate_errors
    if baseline is None or candidate is None or errors:
        print("FAIL comparison inputs", file=sys.stderr)
        print_errors(errors)
        return 1
    if baseline["source_kind"] != "baseline":
        errors.append(ValidationError("baseline", "source_kind must be baseline"))
    if candidate["source_kind"] != "candidate":
        errors.append(ValidationError("candidate", "source_kind must be candidate"))
    for field in ("suite_revision", "host", "model", "permissions_profile", "fixture_revision", "repeat_count", "suite_case_count"):
        if baseline[field] != candidate[field]:
            errors.append(ValidationError(field, "baseline and candidate execution context must match"))
    for field in ("host", "model", "permissions_profile", "fixture_revision"):
        if baseline["observed_context"][field] != candidate["observed_context"][field]:
            errors.append(ValidationError(f"observed_context.{field}", "baseline and candidate observed contexts must match"))
    baseline_cases = [(item["case_id"], item["slice"], item["holdout"]) for item in baseline["case_results"]]
    candidate_cases = [(item["case_id"], item["slice"], item["holdout"]) for item in candidate["case_results"]]
    if baseline_cases != candidate_cases:
        errors.append(ValidationError("case_results", "baseline and candidate cases/slices must match in order"))
    if errors:
        print("FAIL comparison inputs", file=sys.stderr)
        print_errors(errors)
        return 1

    deltas = {
        metric: candidate["summary"][metric] - baseline["summary"][metric]
        for metric in METRIC_NAMES
    }
    comparison = {
        "schema_version": 1,
        "baseline_result_id": baseline["result_id"],
        "candidate_result_id": candidate["result_id"],
        "context": {
            field: baseline[field]
            for field in ("suite_revision", "host", "model", "permissions_profile", "fixture_revision", "repeat_count", "suite_case_count")
        },
        "deltas": deltas,
        "baseline_summary": baseline["summary"],
        "candidate_summary": candidate["summary"],
    }
    encoded = json.dumps(comparison, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
        print(f"WROTE {output}")
    else:
        print(encoded, end="")
    return 0


def add_context_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--suite", default="evals/public", help="public suite directory relative to the repository")
    parser.add_argument("--source-kind", choices=["baseline", "candidate"], required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--agentflow-version", required=True)
    parser.add_argument("--suite-revision", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--permissions-profile", required=True)
    parser.add_argument("--fixture-revision", required=True)
    parser.add_argument("--repeat-count", type=int, required=True)
    parser.add_argument("--result-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--holdout-root", required=True)
    parser.add_argument(
        "--business-root",
        default=None,
        help="business task snapshot root (fourth isolation position); required for a "
        "business suite such as evals/business and unused by evals/public",
    )
    parser.add_argument(
        "--allowed-tools",
        default=None,
        help="comma-separated host tool specs pre-approved for the run (--allowed-tools); "
        "authoritative runs should scope this explicitly instead of relying on the profile, "
        "which print mode may override with permission denials",
    )
    parser.add_argument(
        "--isolate-host-config",
        action="store_true",
        help="run the host with no operator MCP configuration (--strict-mcp-config) and a "
        "scratch CLAUDE_CONFIG_DIR; required for reproducible authoritative runs",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run one explicit host adapter")
    add_context_arguments(run_parser)
    run_parser.add_argument("--adapter", required=True, help="adapter command; JSON request is sent on stdin")
    run_parser.add_argument("--output", required=True)
    run_parser.set_defaults(handler=run_adapter)

    validate_parser = subparsers.add_parser("validate", help="validate a result manifest")
    validate_parser.add_argument("--result", required=True)
    validate_parser.set_defaults(handler=validate_command)

    compare_parser = subparsers.add_parser("compare", help="compare baseline and candidate result manifests")
    compare_parser.add_argument("--baseline", required=True)
    compare_parser.add_argument("--candidate", required=True)
    compare_parser.add_argument("--output")
    compare_parser.set_defaults(handler=compare_command)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
