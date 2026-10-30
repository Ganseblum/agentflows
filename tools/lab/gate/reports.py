"""Retrospective tables (`report`, `recurrence` and `review_debt` subcommands)."""

from __future__ import annotations

import re

from .common import ROOT, ValidationError, load_record_markdown, version_tuple
from .records import RECURRENCE_DIR


def review_debt_report(root=ROOT) -> list[str]:
    """Print the derived review-debt set (G2-AC-01), never a hand-maintained table.

    ① a batch whose README/plan declares L0 but has no review record; ② an issue still
    fixed-pending-review without a reviewer. The manual todo mirror is checked as a subset
    by the spec, not used as the source.
    """
    lines: list[str] = []
    features = root / "docs" / "features"
    if features.is_dir():
        for batch in sorted(path for path in features.iterdir() if path.is_dir()):
            texts: list[str] = []
            readme = batch / "README.md"
            if readme.is_file():
                texts.append(readme.read_text(encoding="utf-8", errors="ignore"))
            plan_dir = batch / "plan"
            if plan_dir.is_dir():
                texts.extend(
                    path.read_text(encoding="utf-8", errors="ignore")
                    for path in sorted(plan_dir.glob("*.md"))
                )
            blob = "\n".join(texts)
            if not re.search(r"review_tier\s*[:：]\s*L0|评审档位[^\n]*\bL0\b", blob):
                continue
            reviews = batch / "reviews"
            has_record = False
            if reviews.is_dir():
                for candidate in reviews.rglob("*.md"):
                    if not candidate.is_file() or candidate.name == "README.md":
                        continue
                    frontmatter, _, read_errors = load_record_markdown(candidate)
                    if not read_errors and frontmatter and (
                        frontmatter.get("review_id") or frontmatter.get("review_tier")
                    ):
                        has_record = True
                        break
            if not has_record:
                lines.append(f"batch: {batch.relative_to(root).as_posix()}")
    issues = root / "docs" / "issues"
    if issues.is_dir():
        for path in sorted(issues.glob("ISS-*.md")):
            frontmatter, _, read_errors = load_record_markdown(path)
            if read_errors or not frontmatter:
                continue
            if frontmatter.get("status") == "fixed-pending-review" and not frontmatter.get("reviewer"):
                lines.append(f"issue: {path.stem}")
    return lines


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


def review_debt_mirror_findings(lines: list[str], root=ROOT) -> list[str]:
    """G2-AC-01 ③: a derived debt may not be marked settled in the human mirror."""
    derived = {line.split(": ", 1)[1] for line in lines if line.startswith("issue: ")}
    todo = root / "docs" / "releases" / "todo.md"
    if not todo.is_file():
        return []
    errors: list[str] = []
    for line in todo.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[1].startswith("已清偿"):
            continue
        if cells[0] in derived:
            errors.append(f"镜像把派生欠账 {cells[0]} 标成已清偿")
    return errors
