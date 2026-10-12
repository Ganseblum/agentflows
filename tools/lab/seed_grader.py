#!/usr/bin/env python3
"""Score agent findings against one business case's seed list, deterministically.

The grader is an offline post-processing step: it reads the frozen seed list of one
business case and the findings artifacts a host wrote under
``<findings-dir>/rep-<n>/findings.json``, then reports per-repetition seed hits, recall,
acceptance, and escaped defects. It never calls a model and never touches the request
path. The scoring semantics are frozen with ``evals/business/README.md``:

- A seed is hit when a finding's ``path`` matches the seed's ``doc_ref`` as a
  component-wise suffix in either direction (``./`` segments and any absolute path
  prefix are dropped first) and the ``issue`` and ``evidence`` text, joined with a
  newline, contains at least one of the seed's ``strategy.anchors`` (``mode: "any"``).
  The separator keeps an anchor from being assembled across the two fields: it must
  appear inside one field, as written.
- ``recall`` = hits / total seeds; ``accepted`` = ``recall >= min_seed_recall``;
  ``escaped_defects`` = missed seeds. Findings that hit no seed are listed under
  ``unmatched`` and are never penalized.

Fail-closed edges (exit code 2):

- A malformed seed list, an unknown ``strategy.type`` or ``strategy.mode``, or a missing
  findings directory is an answer-key/input error: the reason goes to stderr and no
  score document is produced.
- A repetition whose ``findings.json`` is missing or does not parse as the published
  findings artifact is recorded as ``status: "failed"`` with its error message — never
  as a zero score. The document is still printed, and the exit code is 2.

Usage:

    python3 tools/lab/seed_grader.py --seeds evals/business/seeds/BT-001.seeds.json \
        --findings-dir <workspace>/findings/BT-001 --min-recall 0.5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SUPPORTED_STRATEGY_TYPES = ("path_and_anchor",)
SUPPORTED_MODES = ("any",)
REPETITION_DIR_PATTERN = re.compile(r"^rep-([1-9][0-9]*)$")
FINDINGS_FILE_NAME = "findings.json"
FINDING_FIELDS = ("path", "issue", "evidence")


class SeedGraderError(Exception):
    """The seed list or the findings directory cannot be graded as declared."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SeedGraderError(message)


MAX_FINDINGS = 200
MAX_TEXT_LENGTH = 4000
MAX_UNMATCHED_PER_DOC = 10


def normalize_path(value: str) -> tuple[str, ...]:
    """Normalize a relative POSIX path without permitting traversal."""
    raw = value.replace("\\", "/").strip()
    parts = tuple(part for part in raw.split("/") if part not in ("", "."))
    if any(part == ".." for part in parts):
        return ()
    return parts


def is_suffix(short: tuple[str, ...], long: tuple[str, ...]) -> bool:
    return len(short) <= len(long) and long[len(long) - len(short):] == short


def paths_match(finding_path: str, doc_ref: str) -> bool:
    """True when one normalized path is a component-wise suffix of the other."""
    finding = normalize_path(finding_path)
    seed = normalize_path(doc_ref)
    if not finding or not seed:
        return False
    return is_suffix(seed, finding) or is_suffix(finding, seed)


def seed_matches_finding(seed: dict[str, Any], finding: dict[str, str]) -> bool:
    """One seed hit: path rule and at least one anchor inside ``issue`` or ``evidence``.

    The two fields are joined with a newline, never concatenated bare: an anchor has to
    appear inside one field as written, so text split across the field boundary cannot
    spell one out.
    """
    if not paths_match(finding["path"], seed["doc_ref"]):
        return False
    text = f"{finding['issue']}\n{finding['evidence']}"
    return any(anchor in text for anchor in seed["strategy"]["anchors"])


def validate_seed_document(document: Any, source: str) -> dict[str, Any]:
    """Validate one seed list against the frozen matching contract; return it unchanged.

    An unknown ``strategy.type`` (or ``strategy.mode``) is an error, not a guess: the
    answer key declares how a seed may be hit, and the grader only implements the
    declared strategies. An absent ``schema_version`` is tolerated; a different one is
    not.
    """
    require(isinstance(document, dict), f"{source} must be a JSON object")
    version = document.get("schema_version")
    require(
        version is None or version == SCHEMA_VERSION,
        f"{source}: unsupported schema_version {version!r}",
    )
    case_id = document.get("case_id")
    require(isinstance(case_id, str) and case_id, f"{source}: case_id must be a non-empty string")
    seeds = document.get("seeds")
    require(isinstance(seeds, list) and seeds, f"{source}: seeds must be a non-empty array")
    seen_ids: set[str] = set()
    for index, seed in enumerate(seeds):
        require(isinstance(seed, dict), f"{source}: seeds[{index}] must be an object")
        seed_id = seed.get("seed_id")
        require(
            isinstance(seed_id, str) and seed_id,
            f"{source}: seeds[{index}].seed_id must be a non-empty string",
        )
        require(seed_id not in seen_ids, f"{source}: duplicate seed_id {seed_id!r}")
        seen_ids.add(seed_id)
        doc_ref = seed.get("doc_ref")
        require(
            isinstance(doc_ref, str) and doc_ref,
            f"{source}: seed {seed_id} must declare a non-empty doc_ref",
        )
        require(
            bool(normalize_path(doc_ref)),
            f"{source}: seed {seed_id} doc_ref {doc_ref!r} is not a usable path",
        )
        strategy = seed.get("strategy")
        require(isinstance(strategy, dict), f"{source}: seed {seed_id} must declare a strategy object")
        strategy_type = strategy.get("type")
        require(
            strategy_type in SUPPORTED_STRATEGY_TYPES,
            f"{source}: seed {seed_id} declares unknown strategy.type {strategy_type!r}; "
            f"supported types: {', '.join(SUPPORTED_STRATEGY_TYPES)} (fail-closed, no guessing)",
        )
        mode = strategy.get("mode", "any")
        require(
            mode in SUPPORTED_MODES,
            f"{source}: seed {seed_id} declares unknown strategy.mode {mode!r}; "
            f"supported modes: {', '.join(SUPPORTED_MODES)}",
        )
        anchors = strategy.get("anchors")
        require(
            isinstance(anchors, list) and anchors,
            f"{source}: seed {seed_id} must declare a non-empty strategy.anchors array",
        )
        for anchor in anchors:
            require(
                isinstance(anchor, str) and anchor,
                f"{source}: seed {seed_id} strategy.anchors must all be non-empty strings",
            )
    return document


def load_seeds(path: Path | str) -> dict[str, Any]:
    """Read and validate one seed list file."""
    source = Path(path)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SeedGraderError(f"cannot read seed list {source}: {exc}") from exc
    return validate_seed_document(document, str(source))


def load_findings(path: Path, case_id: str) -> list[dict[str, str]]:
    """Read and validate one findings artifact; raise SeedGraderError on any deviation.

    The published artifact format is an object carrying a ``findings`` array whose
    entries have string ``path``/``issue``/``evidence`` fields. ``schema_version`` and
    ``case_id``, when present, must agree with the seed list.
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SeedGraderError(f"cannot read {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise SeedGraderError(f"{path}: findings artifact must be a JSON object")
    version = document.get("schema_version")
    if version is not None and version != SCHEMA_VERSION:
        raise SeedGraderError(f"{path}: unsupported schema_version {version!r}")
    artifact_case = document.get("case_id")
    if artifact_case is not None and artifact_case != case_id:
        raise SeedGraderError(
            f"{path}: case_id {artifact_case!r} does not match the seed list case_id {case_id!r}"
        )
    findings = document.get("findings")
    if not isinstance(findings, list):
        raise SeedGraderError(f"{path}: findings artifact must carry a findings array")
    if len(findings) > MAX_FINDINGS:
        raise SeedGraderError(f"{path}: findings exceeds maximum of {MAX_FINDINGS}")
    validated: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise SeedGraderError(f"{path}: findings[{index}] must be an object")
        for field in FINDING_FIELDS:
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                raise SeedGraderError(f"{path}: findings[{index}].{field} must be a non-empty string")
            if len(finding[field]) > MAX_TEXT_LENGTH:
                raise SeedGraderError(f"{path}: findings[{index}].{field} exceeds {MAX_TEXT_LENGTH} characters")
        if not normalize_path(finding["path"]):
            raise SeedGraderError(f"{path}: findings[{index}].path must be a safe relative path")
        item = tuple(finding[field] for field in FINDING_FIELDS)
        if item in seen:
            raise SeedGraderError(f"{path}: duplicate finding at index {index}")
        seen.add(item)
        validated.append({field: finding[field] for field in FINDING_FIELDS})
    return validated


def grade_repetition(
    seeds: list[dict[str, Any]],
    case_id: str,
    findings_path: Path,
    min_seed_recall: float,
    rep: int,
    target_docs: list[str] | None = None,
    max_unmatched_per_doc: int = MAX_UNMATCHED_PER_DOC,
) -> dict[str, Any]:
    """Grade one repetition into hits/missed/unmatched, recall, acceptance, escapes.

    ``target_docs`` are the snapshot-relative documents the case asked the agent to
    review. A finding whose ``path`` does not match any of them is off-target: it is
    recorded under ``off_target`` and, per document, contributes to an unmatched cap
    that fails the repetition if exceeded. This blocks the "paste the whole document
    as evidence / spam findings" strategies without penalizing legitimate extra
    defects on the allowed documents.
    """
    try:
        findings = load_findings(findings_path, case_id)
    except SeedGraderError as exc:
        return {"rep": rep, "status": "failed", "error": str(exc)}
    if target_docs:
        allowed = [normalize_path(doc) for doc in target_docs]
    else:
        allowed = None
    hits: list[str] = []
    missed: list[str] = []
    off_target: list[dict[str, str]] = []
    unmatched_by_doc: dict[str, int] = {}
    for seed in seeds:
        if any(seed_matches_finding(seed, finding) for finding in findings):
            hits.append(seed["seed_id"])
        else:
            missed.append(seed["seed_id"])
    for finding in findings:
        if allowed is not None and not any(
            paths_match(finding["path"], doc) for doc in target_docs
        ):
            off_target.append({"path": finding["path"], "issue": finding["issue"]})
            continue
        if not any(seed_matches_finding(seed, finding) for seed in seeds):
            doc = finding["path"].replace("\\", "/")
            unmatched_by_doc[doc] = unmatched_by_doc.get(doc, 0) + 1
    if any(count > max_unmatched_per_doc for count in unmatched_by_doc.values()):
        over = {doc: count for doc, count in unmatched_by_doc.items() if count > max_unmatched_per_doc}
        return {
            "rep": rep,
            "status": "failed",
            "error": "unmatched-finding cap exceeded per target document: " + json.dumps(over, ensure_ascii=False),
        }
    recall = len(hits) / len(seeds)
    return {
        "rep": rep,
        "status": "graded",
        "hits": hits,
        "missed": missed,
        "off_target": off_target,
        "unmatched_by_doc": unmatched_by_doc,
        "recall": recall,
        "accepted": recall >= min_seed_recall,
        "escaped_defects": len(missed),
    }


def grade_case(
    seed_document: Any,
    findings_dir: Path | str,
    min_seed_recall: float,
    target_docs: list[str] | None = None,
    max_unmatched_per_doc: int = MAX_UNMATCHED_PER_DOC,
) -> dict[str, Any]:
    """Grade every repetition under ``findings_dir`` and return the result document.

    Repetitions run from 1 to the highest ``rep-<n>`` directory found; a gap is a failed
    repetition, because a missing artifact must not silently shrink a run. Repetition
    failures are data in the returned document; answer-key or input problems raise
    :class:`SeedGraderError` instead, since there is no score to report.

    ``target_docs`` are the snapshot-relative documents the agent was asked to review.
    When provided, any finding whose path does not match one of them is off-target; such
    findings do not count toward recall and, per document, contribute to an unmatched cap
    that fails the repetition when exceeded.
    """
    document = validate_seed_document(seed_document, "seed document")
    threshold = validate_min_recall(min_seed_recall)
    directory = Path(findings_dir)
    if not directory.is_dir():
        raise SeedGraderError(f"findings directory does not exist: {directory}")

    repetition_dirs: dict[int, Path] = {}
    for entry in sorted(directory.iterdir()):
        match = REPETITION_DIR_PATTERN.match(entry.name)
        if match is not None and entry.is_dir():
            repetition_dirs[int(match.group(1))] = entry
    if not repetition_dirs:
        raise SeedGraderError(f"no rep-<n> directories found under {directory}")

    seeds = document["seeds"]
    case_id = document["case_id"]
    repetitions: list[dict[str, Any]] = []
    for rep in range(1, max(repetition_dirs) + 1):
        rep_dir = repetition_dirs.get(rep)
        if rep_dir is None:
            repetitions.append(
                {
                    "rep": rep,
                    "status": "failed",
                    "error": f"repetition directory rep-{rep} is missing under {directory}",
                }
            )
            continue
        repetitions.append(
            grade_repetition(
                seeds,
                case_id,
                rep_dir / FINDINGS_FILE_NAME,
                threshold,
                rep,
                target_docs=target_docs,
                max_unmatched_per_doc=max_unmatched_per_doc,
            )
        )
    graded = sum(1 for item in repetitions if item["status"] == "graded")
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "min_seed_recall": threshold,
        "repetitions": repetitions,
        "summary": {
            "reps_graded": graded,
            "reps_failed": len(repetitions) - graded,
            "total_seeds": len(seeds),
        },
    }


def validate_min_recall(value: Any) -> float:
    """Return the acceptance threshold as a float in [0, 1]; reject anything else."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise SeedGraderError(f"min_seed_recall must be a number between 0 and 1, got {value!r}")
    return float(value)


def exit_code(document: dict[str, Any]) -> int:
    """The CLI contract shared with importers: 0 when all reps graded, 2 when any failed."""
    return 2 if document["summary"]["reps_failed"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", required=True, help="seed list JSON for one business case")
    parser.add_argument(
        "--findings-dir",
        required=True,
        help="findings directory holding rep-<n>/findings.json subdirectories",
    )
    parser.add_argument(
        "--min-recall",
        type=float,
        required=True,
        help="acceptance threshold from the case's grading.min_seed_recall (0..1)",
    )
    parser.add_argument(
        "--target-docs",
        action="append",
        default=None,
        help="snapshot-relative document the business case asked the agent to review "
        "(repeatable; taken from the case's target_docs). Off-target findings and the "
        "per-document unmatched cap only apply when this is given — omit it only for "
        "non-business grading.",
    )
    args = parser.parse_args(argv)
    try:
        seed_document = load_seeds(Path(args.seeds).expanduser().resolve())
        document = grade_case(
            seed_document,
            Path(args.findings_dir).expanduser().resolve(),
            args.min_recall,
            target_docs=args.target_docs,
        )
    except SeedGraderError as exc:
        print(f"seed grader: {exc}", file=sys.stderr)
        return 2
    for item in document["repetitions"]:
        if item["status"] == "failed":
            print(f"seed grader: repetition {item['rep']} failed: {item['error']}", file=sys.stderr)
    print(json.dumps(document, ensure_ascii=False, indent=2))
    return exit_code(document)


if __name__ == "__main__":
    raise SystemExit(main())
