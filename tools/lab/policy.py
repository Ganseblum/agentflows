#!/usr/bin/env python3
"""Apply deterministic promotion rules to a candidate and frozen results.

This tool produces a decision proposal from machine-readable evidence. It never installs,
publishes, or replaces an active Plugin, and it always reports that human approval remains
required for release.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from eval_runner import load_result, summarize  # noqa: E402
from validate import ROOT, SchemaValidator, ValidationError, load_json  # noqa: E402


CANDIDATE_SCHEMA = ROOT / "skills" / "improve" / "references" / "candidate.schema.json"
HIGHER_IS_BETTER = {"acceptance_rate", "first_pass_review_rate"}
LOWER_IS_BETTER = {
    "correction_count",
    "escaped_defects",
    "permission_violations",
    "unnecessary_delegation_count",
    "tool_failures",
    "latency_ms",
}
KNOWN_METRICS = HIGHER_IS_BETTER | LOWER_IS_BETTER


def load_candidate(path_value: str) -> tuple[dict[str, Any] | None, list[ValidationError]]:
    path = Path(path_value).resolve()
    document, errors = load_json(path)
    if errors:
        return None, errors
    if not isinstance(document, dict):
        return None, [ValidationError(str(path), "candidate must be a JSON object")]
    try:
        errors.extend(SchemaValidator(CANDIDATE_SCHEMA).validate(document))
    except (OSError, ValueError) as exc:
        errors.append(ValidationError(str(CANDIDATE_SCHEMA), f"validator setup failed: {exc}"))
    return document, errors


def load_policy(path_value: str | None) -> dict[str, Any]:
    if not path_value:
        return {"guardrail_tolerances": {metric: 0 for metric in KNOWN_METRICS}}
    document, errors = load_json(Path(path_value).resolve())
    if errors:
        raise ValueError(str(errors[0]))
    if not isinstance(document, dict):
        raise ValueError("policy must be a JSON object")
    tolerances = document.get("guardrail_tolerances", {})
    if not isinstance(tolerances, dict):
        raise ValueError("guardrail_tolerances must be an object")
    for metric, value in tolerances.items():
        if metric not in KNOWN_METRICS or not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"invalid guardrail tolerance for {metric!r}")
    return {"guardrail_tolerances": {metric: tolerances.get(metric, 0) for metric in KNOWN_METRICS}}


def compare_direction(metric: str, baseline: float, candidate: float) -> str:
    if metric in HIGHER_IS_BETTER:
        if candidate > baseline:
            return "improved"
        if candidate < baseline:
            return "regressed"
        return "unchanged"
    if candidate < baseline:
        return "improved"
    if candidate > baseline:
        return "regressed"
    return "unchanged"


def decide(
    candidate_record: dict[str, Any],
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    reasons: list[str] = []
    invalid = False

    if baseline.get("source_kind") != "baseline":
        reasons.append("baseline result must have source_kind=baseline")
        invalid = True
    if candidate.get("source_kind") != "candidate":
        reasons.append("candidate result must have source_kind=candidate")
        invalid = True
    if candidate.get("source_revision") != candidate_record.get("source_revision"):
        reasons.append("candidate result source_revision does not match candidate record")
        invalid = True
    if candidate.get("artifact_digest") != candidate_record.get("artifact_digest"):
        reasons.append("candidate result artifact_digest does not match candidate record")
        invalid = True
    if baseline.get("artifact_digest") == candidate.get("artifact_digest"):
        reasons.append("candidate artifact_digest must differ from the baseline artifact")
        invalid = True
    if candidate.get("agentflow_version") != candidate_record.get("candidate_version"):
        reasons.append("candidate result agentflow_version does not match candidate version")
        invalid = True
    if baseline.get("agentflow_version") != candidate_record.get("parent_version"):
        reasons.append("baseline result agentflow_version does not match candidate parent version")
        invalid = True
    if candidate.get("suite_revision") != candidate_record.get("evaluation_suite_revision"):
        reasons.append("candidate result suite_revision does not match candidate record")
        invalid = True
    for field in ("suite_revision", "host", "model", "permissions_profile", "fixture_revision", "repeat_count", "suite_case_count"):
        if baseline.get(field) != candidate.get(field):
            reasons.append(f"baseline and candidate {field} must match")
            invalid = True
    for field in ("host", "model", "permissions_profile", "fixture_revision"):
        if baseline.get("observed_context", {}).get(field) != candidate.get("observed_context", {}).get(field):
            reasons.append(f"baseline and candidate observed_context.{field} must match")
            invalid = True
    if baseline.get("case_results", []) and candidate.get("case_results", []):
        base_cases = [(item["case_id"], item["slice"], item["holdout"]) for item in baseline["case_results"]]
        candidate_cases = [(item["case_id"], item["slice"], item["holdout"]) for item in candidate["case_results"]]
        if base_cases != candidate_cases:
            reasons.append("baseline and candidate case/slice coverage must match")
            invalid = True

    primary_metrics = candidate_record.get("primary_metrics", [])
    guardrails = candidate_record.get("guardrails", [])
    unknown_metrics = sorted(set(primary_metrics + guardrails) - KNOWN_METRICS)
    if unknown_metrics:
        reasons.append(f"candidate names unknown metrics: {', '.join(unknown_metrics)}")
        invalid = True

    metric_results: dict[str, dict[str, Any]] = {}
    for metric in sorted(set(primary_metrics + guardrails)):
        baseline_value = baseline["summary"].get(metric)
        candidate_value = candidate["summary"].get(metric)
        if not isinstance(baseline_value, (int, float)) or not isinstance(candidate_value, (int, float)):
            reasons.append(f"metric {metric!r} is missing or non-numeric")
            invalid = True
            continue
        metric_results[metric] = {
            "baseline": baseline_value,
            "candidate": candidate_value,
            "delta": candidate_value - baseline_value,
            "direction": compare_direction(metric, baseline_value, candidate_value),
        }

    guardrail_failures: list[str] = []
    tolerances = policy["guardrail_tolerances"]
    for metric in guardrails:
        if metric not in metric_results:
            continue
        result = metric_results[metric]
        tolerance = tolerances.get(metric, 0)
        if metric in HIGHER_IS_BETTER:
            regressed = result["candidate"] < result["baseline"] - tolerance
        else:
            regressed = result["candidate"] > result["baseline"] + tolerance
        if regressed:
            guardrail_failures.append(metric)
    if guardrail_failures:
        reasons.append(f"guardrails regressed: {', '.join(guardrail_failures)}")

    primary_directions = [metric_results[metric]["direction"] for metric in primary_metrics if metric in metric_results]
    primary_improved = bool(primary_directions) and any(direction == "improved" for direction in primary_directions)
    primary_regressed = any(direction == "regressed" for direction in primary_directions)

    available_slices = {item["slice"] for item in baseline.get("case_results", [])}
    protected_slices = candidate_record.get("protected_slices") or sorted(available_slices)
    slice_metrics: dict[str, dict[str, dict[str, Any]]] = {}
    slice_failures: list[str] = []
    for slice_name in protected_slices:
        baseline_cases = [item for item in baseline.get("case_results", []) if item["slice"] == slice_name]
        candidate_cases = [item for item in candidate.get("case_results", []) if item["slice"] == slice_name]
        if not baseline_cases or not candidate_cases:
            reasons.append(f"protected slice {slice_name!r} is missing from baseline or candidate")
            invalid = True
            continue
        baseline_slice = summarize(baseline_cases)
        candidate_slice = summarize(candidate_cases)
        slice_metrics[slice_name] = {}
        for metric in sorted(set(primary_metrics + guardrails)):
            direction = compare_direction(metric, baseline_slice[metric], candidate_slice[metric])
            slice_metrics[slice_name][metric] = {
                "baseline": baseline_slice[metric],
                "candidate": candidate_slice[metric],
                "delta": candidate_slice[metric] - baseline_slice[metric],
                "direction": direction,
            }
            tolerance = tolerances.get(metric, 0)
            if metric in guardrails:
                if metric in HIGHER_IS_BETTER:
                    regressed = candidate_slice[metric] < baseline_slice[metric] - tolerance
                else:
                    regressed = candidate_slice[metric] > baseline_slice[metric] + tolerance
            else:
                regressed = direction == "regressed"
            if regressed:
                slice_failures.append(f"{slice_name}:{metric}")
    if slice_failures:
        reasons.append(f"protected slice regressions: {', '.join(slice_failures)}")

    if invalid:
        evaluation_result = "invalid"
        decision = "reject"
    elif guardrail_failures or primary_regressed or slice_failures:
        evaluation_result = "worse"
        decision = "reject"
    elif primary_improved:
        evaluation_result = "better"
        decision = "promote"
        reasons.append("all declared primary metrics are non-regressing and at least one improved")
    else:
        evaluation_result = "neutral"
        decision = "revise"
        reasons.append("no declared primary metric improved")

    return {
        "schema_version": 1,
        "candidate_version": candidate_record["candidate_version"],
        "parent_version": candidate_record["parent_version"],
        "evaluation_result": evaluation_result,
        "decision": decision,
        "metrics": metric_results,
        "protected_slice_metrics": slice_metrics,
        "reasons": reasons,
        "required_human_approval": True,
        "rollback_target": candidate_record.get("parent_version"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-record", required=True)
    parser.add_argument("--baseline-result", required=True)
    parser.add_argument("--candidate-result", required=True)
    parser.add_argument("--policy")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    candidate_record, candidate_errors = load_candidate(args.candidate_record)
    baseline, baseline_errors = load_result(args.baseline_result)
    candidate, result_errors = load_result(args.candidate_result)
    errors = candidate_errors + baseline_errors + result_errors
    if errors or candidate_record is None or baseline is None or candidate is None:
        print("FAIL policy inputs", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    try:
        policy = load_policy(args.policy)
        decision = decide(candidate_record, baseline, candidate, policy)
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL policy evaluation: {exc}", file=sys.stderr)
        return 1

    encoded = json.dumps(decision, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
        print(f"WROTE {output}")
    else:
        print(encoded, end="")
    # A reject is a valid policy outcome but must fail the calling gate closed.
    return 1 if decision["decision"] == "reject" else 0 if decision["decision"] in {"promote", "revise"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
