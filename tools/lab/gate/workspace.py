"""The live record-root walk that compiles every artifact instance."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import (
    LIVE_RECORD_ROOTS,
    ROOT,
    ValidationError,
    files_entry_errors,
    load_json,
    load_record_markdown,
)
from .plan import validate_plan_markdown
from .records import (
    BUG_ARCHIVE_DIR,
    RECURRENCE_DIR,
    validate_body_references,
    validate_bug_layout,
    validate_bug_markdown,
    validate_episode_document,
    validate_external_excerpts,
    validate_recurrence_markdown,
    validate_review_markdown,
)
from .testing import validate_test_plan_markdown, validate_test_run_markdown

# Segment directories a feature batch may hold (docs/features/README.md tree). The walk accepts only
# these and README.md inside a batch; anything else under docs/features/ fails explicitly.
FEATURE_SEGMENTS = ("proposal", "spec", "design", "plan", "reviews", "testing")


def is_project_feature_slug(name: str) -> bool:
    """<project>-<feature-slug>: hyphenated, with no leading or trailing hyphen."""
    return "-" in name and not name.startswith("-") and not name.endswith("-")


def validate_workspace_artifacts() -> list[ValidationError]:
    """Validate record instances under the live record roots.

    Issue records (with their recurrence ledgers and rejected-record archive under
    docs/issues/), JSON episodes, the batch directories under docs/features/ (their
    plan/<plan_id>.md hybrids only), the working files under docs/releases/, and review
    records with their archive snapshots. The improve-loop artifact subtrees and the
    per-version release records were retired by the 2026-10-12 slimming batches.
    """
    errors: list[ValidationError] = []
    seen_bug_ids: dict[str, Path] = {}
    seen_review_ids: dict[str, Path] = {}
    seen_episode_ids: dict[str, Path] = {}
    record_versions: dict[str, str] = {}
    ledgers: dict[str, dict[str, Any]] = {}
    class_records: list[tuple[str, Any, str, Path]] = []
    review_findings: list[tuple[list, Path]] = []
    testing_plans: list[Path] = []
    testing_runs: list[Path] = []
    live_roots: list[str] = []
    for root_name in LIVE_RECORD_ROOTS:
        root = ROOT / root_name
        if not root.is_dir():
            errors.append(
                ValidationError(str(root), f"{root_name} directory is missing; artifacts are required")
            )
            continue
        live_roots.append(root_name)
        if not any(entry for entry in root.iterdir() if not entry.name.startswith(".")):
            errors.append(
                ValidationError(str(root), f"{root_name} directory is empty; artifacts are required")
            )
    for root_name in live_roots:
        root = ROOT / root_name
        kind = root_name.rsplit("/", 1)[-1]
        base = len(root_name.split("/"))  # path depth of the root itself
        # Every path under a live record root is a stray file or an unknown subdirectory and must
        # fail explicitly instead of falling through the root dispatch silently.
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(ROOT)
            parts = relative.parts
            under = parts[base:]  # entry path relative to the record root
            n = len(under)
            if any(part.startswith(".") for part in under):
                if path.name == ".DS_Store":
                    continue
                errors.append(ValidationError(str(path), "hidden record entry is not allowed"))
                continue
            if kind == "issues":
                if n == 1 and path.is_file() and under[0] == "README.md":
                    continue  # the class README documents the numbering and archive rules
                if (
                    n == 1
                    and not path.is_file()
                    and under[0] not in (RECURRENCE_DIR, BUG_ARCHIVE_DIR)
                ):
                    errors.append(
                        ValidationError(
                            str(path),
                            "unexpected entry under issues/; live issue records are "
                            "ISS-<YYYY>-<NNN>-<slug>.md directly under issues/, with 归档/ and "
                            "recurrence/ the only subdirectories — see issues/README.md",
                        )
                    )
                    continue
                if under[0] == RECURRENCE_DIR:
                    if not path.is_file():
                        continue
                    if path.suffix != ".md":
                        errors.append(
                            ValidationError(str(path), "recurrence ledgers are Markdown files; unexpected non-md file")
                        )
                        continue
                    ledger_errors = validate_recurrence_markdown(path)
                    errors.extend(ledger_errors)
                    if ledger_errors:
                        continue
                    frontmatter, _, _ = load_record_markdown(path)
                    class_id = frontmatter.get("class_id") if frontmatter else None
                    if isinstance(class_id, str):
                        if class_id in ledgers:
                            errors.append(
                                ValidationError(str(path), f"duplicate class_id {class_id!r} already declared in {ledgers[class_id]['path']}")
                            )
                        else:
                            ledgers[class_id] = {"path": path, "frontmatter": frontmatter}
                    continue
                archived = under[0] == BUG_ARCHIVE_DIR
                if n > 1 and not archived:
                    errors.append(
                        ValidationError(
                            str(path),
                            "unexpected entry under issues/; only issues/<ISS-…>.md, "
                            "issues/归档/<YYYY-MM-DD>/ and issues/recurrence/ are record locations "
                            "— see issues/README.md",
                        )
                    )
                    continue
                if not path.is_file():
                    continue
                if path.suffix != ".md":
                    errors.append(ValidationError(str(path), "issue records are Markdown files; unexpected non-md file"))
                    continue
                frontmatter, body, load_errors = load_record_markdown(path)
                if load_errors or frontmatter is None:
                    errors.extend(load_errors)
                    continue
                errors.extend(validate_bug_markdown(path))
                errors.extend(validate_bug_layout(frontmatter, path, relative, seen_bug_ids))
                errors.extend(validate_external_excerpts(frontmatter, body, path))
                errors.extend(validate_body_references(body, path))
                for entry in frontmatter.get("files") or []:
                    # Self-contained evidence: a reference either resolves inside this repository
                    # or is explicitly repo-qualified (<repo>@<revision>:<path>) — a bare path that
                    # exists nowhere dangles for anyone who receives the records without the
                    # other repository.
                    if isinstance(entry, str):
                        errors.extend(files_entry_errors(entry, path))
                status = frontmatter.get("status")
                if archived:
                    if status != "rejected":
                        errors.append(
                            ValidationError(str(path), "only rejected records may be archived; verified records stay in place")
                        )
                elif status == "rejected":
                    errors.append(
                        ValidationError(str(path), "a rejected record must be moved into issues/归档/")
                    )
                bug_id = frontmatter.get("bug_id")
                version = frontmatter.get("agentflow_version")
                if isinstance(bug_id, str) and isinstance(version, str):
                    record_versions[bug_id] = version
                class_id = frontmatter.get("class_id")
                if isinstance(class_id, str):
                    class_records.append((class_id, frontmatter.get("occurrence"), str(bug_id or ""), path))
            elif kind == "episodes":
                if n == 1 and path.is_file() and under[0] == "README.md":
                    continue
                if not path.is_file():
                    continue
                if path.suffix != ".json":
                    errors.append(ValidationError(str(path), "episode records are JSON files; unexpected non-json file"))
                    continue
                episode_errors = validate_episode_document(path)
                errors.extend(episode_errors)
                if episode_errors:
                    continue
                document, _ = load_json(path)
                episode_id = document.get("episode_id") if isinstance(document, dict) else None
                if isinstance(episode_id, str):
                    if episode_id in seen_episode_ids:
                        errors.append(
                            ValidationError(str(path), f"duplicate episode_id {episode_id!r} already declared in {seen_episode_ids[episode_id]}")
                        )
                    else:
                        seen_episode_ids[episode_id] = path
            elif kind == "reviews":
                # Everything under reviews/ is accounted for: the root README, feature directories,
                # review-<date>-<NNN>.md records one level down, and evidence snapshots under
                # <feature>/archive/ (copies of reviewed documents, not records).
                if len(under) >= 2 and under[1] == "archive":
                    continue
                if n == 1 and (path.is_dir() or under[0] == "README.md"):
                    continue
                if n != 2 or not path.is_file() or not re.fullmatch(
                    r"review-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name
                ):
                    errors.append(
                        ValidationError(
                            str(path),
                            "unexpected entry under reviews/; only README.md at the root, feature "
                            "directories, review-<date>-<NNN>.md records and archive/ snapshots belong here",
                        )
                    )
                    continue
                review_errors = validate_review_markdown(path, relative, seen_review_ids)
                errors.extend(review_errors)
                if review_errors:
                    continue
                frontmatter, _, _ = load_record_markdown(path)
                if frontmatter:
                    review_findings.append((frontmatter.get("findings") or [], path))
            elif kind == "features":
                # Whitelist: docs/features/README.md and batch directories at the root; inside a
                # batch, README.md and the FEATURE_SEGMENTS directories; segment files are Markdown.
                # Only <batch>/plan/<plan_id>.md is a machine contract here (the plan hybrid); other
                # nested Markdown is doc-chain material; <batch>/testing/ records are collected and
                # validated after the walk.
                if n == 1:
                    if path.is_dir() or under[0] == "README.md":
                        continue
                    errors.append(
                        ValidationError(str(path), "unexpected file under docs/features/; only README.md and batch directories belong at this level")
                    )
                    continue
                if n == 2:
                    if path.is_dir() and under[1] in FEATURE_SEGMENTS:
                        continue
                    if path.is_file() and under[1] == "README.md":
                        continue
                    errors.append(
                        ValidationError(str(path), f"unexpected entry in a feature batch; allowed are README.md and the directories {', '.join(FEATURE_SEGMENTS)}")
                    )
                    continue
                segment = under[1]
                if segment not in FEATURE_SEGMENTS:
                    errors.append(
                        ValidationError(str(path), f"unknown segment {segment!r} in a feature batch; allowed are {', '.join(FEATURE_SEGMENTS)}")
                    )
                    continue
                if segment == "testing":
                    if n == 3 and path.is_dir() and is_project_feature_slug(under[2]):
                        continue
                    if n == 4 and path.is_file() and path.suffix == ".md":
                        if re.fullmatch(r"plan-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name):
                            testing_plans.append(path)
                            continue
                        if re.fullmatch(r"run-\d{4}-\d{2}-\d{2}-\d{3}\.md", path.name):
                            testing_runs.append(path)
                            continue
                    errors.append(
                        ValidationError(
                            str(path),
                            "unexpected entry under testing/; records are testing/<project>-<feature-slug>/"
                            "plan-<date>-<NNN>.md and run-<date>-<NNN>.md",
                        )
                    )
                    continue
                if path.is_dir():
                    continue
                if path.suffix != ".md":
                    errors.append(ValidationError(str(path), "feature segment files are Markdown; unexpected non-md file"))
                    continue
                if segment == "plan" and n == 3:
                    errors.extend(validate_plan_markdown(path))
            elif kind == "releases":
                # 2026-10-12: per-version release JSON was retired — this root holds only the
                # batch todo / pending-test working files, not records.
                if n == 1 and path.is_file() and under[0] in ("todo.md", "pending-test.md"):
                    continue
                errors.append(
                    ValidationError(
                        str(path),
                        "unexpected entry under docs/releases/; per-version release records were "
                        "retired (version history lives in CHANGELOG.md) — only todo.md and "
                        "pending-test.md working files belong here",
                    )
                )
                continue

    # Test records under features/<batch>/testing/: plans first, so each run can resolve its plan.
    # The run-findings bug-id cross-check is still deferred (see the note at the end of this function).
    seen_plan_ids: dict[str, Path] = {}
    seen_run_ids: dict[str, Path] = {}
    test_plans: dict[str, dict[str, Any]] = {}
    for path in testing_plans:
        plan_errors, entry = validate_test_plan_markdown(path, path.relative_to(ROOT), seen_plan_ids)
        errors.extend(plan_errors)
        if entry is not None:
            test_plans[entry["frontmatter"]["test_plan_id"]] = entry
    for path in testing_runs:
        run_errors, _, _ = validate_test_run_markdown(path, path.relative_to(ROOT), seen_run_ids, test_plans)
        errors.extend(run_errors)

    # Cross-check recurrence ledgers against the records they claim.
    for class_id, entry in ledgers.items():
        ledger_path = entry["path"]
        frontmatter = entry["frontmatter"]
        first_record = frontmatter.get("first_record")
        occurrences = frontmatter.get("occurrences") or []
        for bug_id in [first_record, *occurrences]:
            if isinstance(bug_id, str) and bug_id not in seen_bug_ids:
                errors.append(
                    ValidationError(str(ledger_path), f"references unknown bug_id {bug_id!r}")
                )
        if frontmatter.get("status") == "consolidated":
            for bug_id in occurrences:
                if isinstance(bug_id, str) and bug_id in seen_bug_ids and bug_id not in record_versions:
                    errors.append(
                        ValidationError(
                            str(ledger_path),
                            f"occurrence {bug_id!r} of a consolidated class must carry agentflow_version "
                            "so it can be placed before or after the consolidation",
                        )
                    )
    used_occurrences: dict[str, dict[str, Path]] = {}
    for class_id, occurrence, bug_id, path in class_records:
        if class_id not in ledgers:
            errors.append(
                ValidationError(str(path), f"class_id {class_id!r} has no ledger under issues/recurrence/")
            )
            continue
        if not (isinstance(occurrence, str) and occurrence.isdigit() and int(occurrence) >= 1):
            errors.append(
                ValidationError(str(path), "a record with class_id must declare occurrence as a positive digit string")
            )
            continue
        if occurrence in used_occurrences.setdefault(class_id, {}):
            errors.append(
                ValidationError(
                    str(path),
                    f"occurrence {occurrence} of class {class_id!r} is already used by {used_occurrences[class_id][occurrence]}",
                )
            )
        used_occurrences[class_id][occurrence] = path
        listed = ledgers[class_id]["frontmatter"].get("occurrences") or []
        if bug_id not in listed:
            errors.append(
                ValidationError(str(path), f"bug_id {bug_id!r} is not listed in ledger {class_id!r}")
            )
    for findings, review_path in review_findings:
        for bug_id in findings:
            if isinstance(bug_id, str) and bug_id not in seen_bug_ids:
                errors.append(
                    ValidationError(str(review_path), f"review findings reference unknown bug_id {bug_id!r}")
                )
    # Test records under features/<batch>/testing/ are walked and validated above. Still deferred to
    # a separately reviewed change: the run-findings bug-id cross-check (a run's findings and
    # flow_findings must resolve to issue records), which validate_test_run_markdown returns but
    # this walk does not yet compare. The improve-loop artifact cross-checks were retired with the
    # improvements/ three-subtree (2026-10-12, user decision).
    return errors
