"""Record-instance checks: issue, recurrence, episode and review records."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import (
    BUG_RECORD_SCHEMA,
    EPISODE_SCHEMA,
    QUALIFIED_REF_PATTERN,
    RECURRENCE_SCHEMA,
    REVIEW_SCHEMA,
    ROOT,
    ValidationError,
    dated_id_errors,
    heading_present,
    load_json,
    load_record_markdown,
    record_date_of,
    validate_timestamp_order,
)
from .schema import SchemaValidator

BUG_REQUIRED_HEADINGS = ("## 现象", "## 根因")


# Issue records are flat: issues/ISS-<YYYY>-<NNN>-<slug>.md. Only rejected records live under
# issues/归档/<YYYY-MM-DD>/; recurrence ledgers live under issues/recurrence/.
BUG_ARCHIVE_DIR = "归档"


RECURRENCE_DIR = "recurrence"


BUG_FILENAME_PATTERN = re.compile(r"^ISS-\d{4}-\d{3,}-[A-Za-z0-9\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff-]*$")


def validate_recurrence_markdown(path: Path) -> list[ValidationError]:
    """Validate one recurrence ledger: schema, timestamp order, filename/class_id agreement."""
    frontmatter, body, errors = load_record_markdown(path)
    if errors or frontmatter is None:
        return errors
    try:
        validator = SchemaValidator(RECURRENCE_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors
    errors.extend(validate_timestamp_order(frontmatter, path))
    errors.extend(validate_body_references(body, path))
    if path.stem != frontmatter.get("class_id"):
        errors.append(
            ValidationError(str(path), "ledger filename must equal class_id")
        )
    return errors


BODY_PATH_PATTERN = re.compile(
    r"(?:\.\./|\./)?[\w.][\w.\-]*(?:/[\w.\-]+)+\.[A-Za-z]{2,8}"
)


URL_PATTERN = re.compile(r"https?://\S+")


def prose_without_quotations(body: str) -> str:
    """Plain prose only: fenced blocks and inline code spans are quotations, not claims."""
    segments: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            segments.append(line)
    prose = "\n".join(segments)
    return re.sub(r"`[^`]*`", " ", prose)


def validate_body_references(body: str, path: Path) -> list[ValidationError]:
    """Every doc/code path the record itself claims must resolve; quotations are exempt.

    A path in plain prose is the record's own reference: it must exist in this repository
    (or next to the record) or be a repo-qualified reference. Fenced blocks and inline code
    are quotations — evidence quoted verbatim, including historical paths — and are not
    scanned. Personal absolute paths are banned outright: they are neither portable nor
    evidence. URLs cannot be validated and are supplementary at most, never the evidence.
    """
    errors: list[ValidationError] = []
    prose = prose_without_quotations(body)
    if re.search(r"/Users/|/home/|(?<![A-Za-z0-9_.])~/", prose):
        errors.append(
            ValidationError(
                str(path),
                "personal absolute path in prose — records are portable evidence; "
                "use a repo-relative or repo-qualified reference",
            )
        )
    cleaned = URL_PATTERN.sub(" ", prose)
    cleaned = QUALIFIED_REF_PATTERN.sub(" ", cleaned)
    for token in BODY_PATH_PATTERN.findall(cleaned):
        # Containment, not just existence: the pattern admits "../" prefixes, and the old
        # bare is_file() check resolved `(ROOT / "../secret.md")` OUTSIDE the repository —
        # an escape that passed as if it were portable evidence. Both anchors are
        # repository-inside directories, so a reference is accepted only when the resolved
        # path stays inside the repository (relative climbs between record directories
        # stay legal) and the file exists.
        repo_candidate = (ROOT / token).resolve()
        local_candidate = (path.parent / token).resolve()
        repo_root = ROOT.resolve()
        if repo_candidate.is_file() and repo_candidate.is_relative_to(repo_root):
            continue
        if local_candidate.is_file() and local_candidate.is_relative_to(repo_root):
            continue
        errors.append(
            ValidationError(
                str(path),
                f"body references {token!r} which exists neither in this repository nor next "
                "to the record — carry the evidence (quote it, archive it, or use a "
                "repo-qualified reference)",
            )
        )
    return errors


def validate_episode_document(path: Path) -> list[ValidationError]:
    """Validate one episode record: improve-loop episode schema, timestamp, filename=id."""
    document, load_errors = load_json(path)
    if load_errors or not isinstance(document, dict):
        return load_errors or [ValidationError(str(path), "episode record is not a JSON object")]
    try:
        validator = SchemaValidator(EPISODE_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors = validator.validate(document)
    if errors:
        return errors
    expected_id = document.get("episode_id")
    if isinstance(expected_id, str) and path.stem != expected_id:
        errors.append(
            ValidationError(str(path), f"filename stem must equal episode_id {expected_id!r}")
        )
    return errors


def excerpt_follows_citation(lines: list[str], index: int) -> bool:
    """True when the citation on lines[index] carries its own excerpt.

    The citation counts when it sits inside a blockquote or a fenced block, or when the next
    non-blank line after it opens a fenced block or a blockquote. A fragment elsewhere in the body
    does not satisfy it.
    """
    if lines[index].lstrip().startswith(">"):
        return True
    fences_before = sum(1 for prior in lines[:index] if prior.lstrip().startswith("```"))
    if fences_before % 2 == 1:
        return True
    for following in lines[index + 1 :]:
        if following.strip():
            return following.lstrip().startswith(("```", ">"))
    return False


def validate_external_excerpts(
    frontmatter: dict[str, Any], body: str, path: Path
) -> list[ValidationError]:
    """External references must carry their evidence: an embedded fragment, cited at its address.

    A repo-qualified reference is an address, not evidence — the record must embed the decisive
    fragment (a fenced code block for code, a blockquote for document passages) and cite the
    qualified address in the body next to it, so the record stays readable and checkable when
    the other repository is absent.
    """
    errors: list[ValidationError] = []
    external = [
        entry
        for entry in frontmatter.get("files") or []
        if isinstance(entry, str) and "@" in entry.partition(":")[0] and ":" in entry
    ]
    if not external:
        return errors
    lines = body.splitlines()
    for entry in external:
        citations = [index for index, line in enumerate(lines) if entry in line]
        if not citations:
            errors.append(
                ValidationError(
                    str(path),
                    f"external reference {entry!r} must be cited in the body next to its excerpt",
                )
            )
        if not any(excerpt_follows_citation(lines, index) for index in citations):
            errors.append(
                ValidationError(
                    str(path),
                    f"external reference {entry!r} requires an embedded fragment next to its citation "
                    "(fenced code block for code, blockquote for document passages); a fragment "
                    "elsewhere in the body does not count",
                )
            )
    return errors


def validate_review_markdown(
    path: Path, relative: Path, seen_review_ids: dict[str, Path]
) -> list[ValidationError]:
    """Validate one review record: schema, timestamp order, layout, archived-doc existence.

    Layout: reviews/<project>-<feature-slug>/review-<YYYY-MM-DD>-<NNN>.md — the
    directory is anchored on the reviewed feature (the same feature may be reviewed many
    times), and the filename must equal the review_id so rounds sort chronologically.
    """
    frontmatter, body, errors = load_record_markdown(path)
    if errors or frontmatter is None:
        return errors
    try:
        validator = SchemaValidator(REVIEW_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors
    errors.extend(validate_timestamp_order(frontmatter, path))
    errors.extend(validate_body_references(body, path))
    review_id = frontmatter.get("review_id")
    if isinstance(review_id, str):
        if review_id in seen_review_ids:
            errors.append(
                ValidationError(
                    str(path),
                    f"duplicate review_id {review_id!r} already declared in {seen_review_ids[review_id]}",
                )
            )
        else:
            seen_review_ids[review_id] = path
    parts = relative.parts  # ("reviews", "<project>-<feature-slug>", "review-<date>-<NNN>.md")
    if len(parts) != 3:
        errors.append(
            ValidationError(str(path), "review records live in reviews/<project>-<feature-slug>/")
        )
    else:
        if "-" not in parts[1] or parts[1].startswith("-") or parts[1].endswith("-"):
            errors.append(
                ValidationError(str(path), "review directory must be named <project>-<feature-slug>")
            )
        if isinstance(review_id, str):
            m = re.fullmatch(r"REV-(\d{4})(\d{2})(\d{2})-(\d{3})", review_id)
            if m:
                errors.extend(dated_id_errors(path, frontmatter, m, "review", "review_id"))
            elif path.stem != review_id:
                errors.append(
                    ValidationError(str(path), "review record filename must match its review_id date and seq")
                )
    for doc in frontmatter.get("reviewed_docs") or []:
        if isinstance(doc, str) and not (path.parent / doc).is_file():
            errors.append(
                ValidationError(str(path), f"archived document {doc!r} not found next to the review record")
            )
    return errors


def validate_bug_markdown(path: Path) -> list[ValidationError]:
    """Validate one Markdown bug record: frontmatter schema, body sections, state rules."""
    frontmatter, body, errors = load_record_markdown(path)
    if errors or frontmatter is None:
        return errors
    try:
        validator = SchemaValidator(BUG_RECORD_SCHEMA)
    except (OSError, ValueError) as exc:
        return [ValidationError(str(path), f"validator setup failed: {exc}")]
    errors.extend(validator.validate(frontmatter))
    if errors:
        return errors
    errors.extend(validate_timestamp_order(frontmatter, path))

    for heading in BUG_REQUIRED_HEADINGS:
        if not heading_present(body, heading):
            errors.append(ValidationError(str(path), f"body section {heading!r} is required"))
    if frontmatter.get("status") != "open" and not heading_present(body, "## 修复"):
        errors.append(ValidationError(str(path), "body section '## 修复' is required unless the bug is open"))
    if frontmatter.get("status") == "verified" and not heading_present(body, "## 审查"):
        errors.append(ValidationError(str(path), "body section '## 审查' is required for a verified record"))
    return errors


def validate_bug_layout(frontmatter: dict[str, Any], path: Path, relative: Path, seen_ids: dict[str, Path]) -> list[ValidationError]:
    """Validate filename shape and bug_id uniqueness for one record.

    Live records are flat: issues/ISS-<YYYY>-<NNN>-<slug>.md. Archived (rejected) records keep
    a date directory: issues/归档/<YYYY-MM-DD>/ISS-<YYYY>-<NNN>-<slug>.md.
    """
    errors: list[ValidationError] = []
    bug_id = frontmatter.get("bug_id")
    if isinstance(bug_id, str):
        if bug_id in seen_ids:
            errors.append(
                ValidationError(str(path), f"duplicate bug_id {bug_id!r} already recorded in {seen_ids[bug_id]}")
            )
        else:
            seen_ids[bug_id] = path
    if not BUG_FILENAME_PATTERN.match(path.stem):
        errors.append(
            ValidationError(
                str(path),
                "filename must be ISS-<YYYY>-<NNN>-<slug> "
                "(letters, digits, Chinese, hyphens) — e.g. ISS-2026-001-claude-json-schema-被拒.md",
            )
        )

    parts = relative.parts  # ("docs", "issues", "ISS-…-slug.md") or ("docs", "issues", "归档", "YYYY-MM-DD", "ISS-…-slug.md")
    if BUG_ARCHIVE_DIR in parts:
        date_parts = [part for part in parts[3:] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", part)]
        if not date_parts:
            errors.append(
                ValidationError(str(path), "archived records live in a YYYY-MM-DD directory under docs/issues/归档/")
            )
            return errors
        recorded_date = record_date_of(frontmatter)
        if recorded_date is not None and date_parts[-1] != recorded_date.isoformat():
            errors.append(
                ValidationError(
                    str(path),
                    f"date directory {date_parts[-1]!r} does not match recorded_at date {recorded_date.isoformat()}",
                )
            )
    elif len(parts) != 3:
        errors.append(
            ValidationError(str(path), "live issue records live directly under docs/issues/ (docs/issues/ISS-<YYYY>-<NNN>-<slug>.md)")
        )
    return errors
