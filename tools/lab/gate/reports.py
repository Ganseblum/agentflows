"""Retrospective tables (`report` and `recurrence` subcommands)."""

from __future__ import annotations

from .common import ROOT, ValidationError, load_record_markdown, version_tuple
from .records import RECURRENCE_DIR


def bug_report(
    project: str | None = None, status: str | None = None, provenance: str | None = None
) -> list[ValidationError]:
    """Print a retrospective table of all bug records, then exit.

    Optional filters narrow the table to one project, one status, or one provenance —
    the equivalent of piping through `awk -F'\\t'`, without remembering column numbers.
    """
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    issues_root = ROOT / "docs" / "issues"
    if issues_root.is_dir():
        for path in sorted(issues_root.rglob("*.md")):
            if path.name == "README.md" or RECURRENCE_DIR in path.relative_to(issues_root).parts:
                continue
            frontmatter, _, errors = load_record_markdown(path)
            if errors or not frontmatter:
                continue
            if project and frontmatter.get("project") != project:
                continue
            if status and frontmatter.get("status") != status:
                continue
            if provenance and frontmatter.get("provenance") != provenance:
                continue
            rows.append(
                (
                    str(frontmatter.get("recorded_at", "")),
                    str(frontmatter.get("bug_id", "")),
                    str(frontmatter.get("status", "")),
                    str(frontmatter.get("severity", "")),
                    str(frontmatter.get("error_kind", "")),
                    str(frontmatter.get("title", "")),
                    str(frontmatter.get("provenance", "")),
                )
            )
    rows.sort()
    for recorded, bug_id, row_status, severity, error_kind, title, row_provenance in rows:
        print(f"{recorded}\t{bug_id}\t{row_status}\t{severity}\t{error_kind}\t{title}\t{row_provenance}")
    return []


def recurrence_report() -> list[ValidationError]:
    """Print the recurrence ledger table: per class, consolidation state and recurrence tier.

    The tier is derived, not declared: `single` (one occurrence), `recurred` (two or more
    occurrences), `escalated` (at least one occurrence recorded on a version newer than the
    consolidation version). Counts use the referenced records' `agentflow_version`.
    """
    issues_root = ROOT / "docs" / "issues"
    versions: dict[str, str] = {}
    for path in sorted(issues_root.rglob("*.md")):
        if path.name == "README.md" or RECURRENCE_DIR in path.relative_to(issues_root).parts:
            continue
        frontmatter, _, load_errors = load_record_markdown(path)
        if load_errors or not frontmatter:
            continue
        bug_id = frontmatter.get("bug_id")
        version = frontmatter.get("agentflow_version")
        if isinstance(bug_id, str) and isinstance(version, str):
            versions[bug_id] = version
    rows: list[tuple[str, str, str, int, int, str]] = []
    ledger_dir = issues_root / RECURRENCE_DIR
    if ledger_dir.is_dir():
        for path in sorted(ledger_dir.glob("*.md")):
            if path.name == "README.md":
                continue
            frontmatter, _, load_errors = load_record_markdown(path)
            if load_errors or not frontmatter:
                continue
            occurrences = frontmatter.get("occurrences") or []
            consolidated_in = frontmatter.get("consolidated_in")
            post = 0
            if isinstance(consolidated_in, str):
                consolidated_key = version_tuple(consolidated_in)
                for bug_id in occurrences:
                    version = versions.get(bug_id) if isinstance(bug_id, str) else None
                    if version and version_tuple(version) > consolidated_key:
                        post += 1
            if post >= 1:
                tier = "escalated"
            elif len(occurrences) >= 2:
                tier = "recurred"
            else:
                tier = "single"
            rows.append(
                (
                    str(frontmatter.get("class_id", "")),
                    str(frontmatter.get("status", "")),
                    str(consolidated_in or "-"),
                    len(occurrences),
                    post,
                    tier,
                )
            )
    rows.sort()
    for class_id, status, consolidated_in, count, post, tier in rows:
        print(f"{class_id}\t{status}\t{consolidated_in}\t{count}\t{post}\t{tier}")
    return []
