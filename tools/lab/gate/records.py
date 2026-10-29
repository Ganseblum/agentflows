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


# Issue records are flat: issues/ISS-<YYYY-MM-DD>-<slug>.md, the id being the whole stem. Only
# rejected records live under issues/归档/<YYYY-MM-DD>/; recurrence ledgers live under
# issues/recurrence/. The date in the id is the record's own recorded_at date.
BUG_ARCHIVE_DIR = "归档"


RECURRENCE_DIR = "recurrence"


BUG_FILENAME_PATTERN = re.compile(
    r"^ISS-(\d{4})-(\d{2})-(\d{2})-[A-Za-z0-9\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff-]*$"
)


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


# `N/A:` alone is not an exemption; it has to carry the reason, mirroring C23's 证据载体口径
# (skills/agentflow/references/document-chain.md 的门 8).
NA_REASON_PATTERN = re.compile(r"N/A[:：]\s*\S")  # 与链侧 C23 同一条：认全角冒号、不锚定行首


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
    errors.extend(validate_episode_references(document, path))
    return errors


# Field-level evidence pointers in episodes. The schema only requires these strings to be
# non-empty, so a pointer to a file that no longer exists compiled happily: plan evidence
# columns have had a presence check since C23 (2026-10-23) while episodes — the archive the
# same chain relies on — had none (docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md §二 B1 的同一
# 形态). Scope is deliberately narrower than the prose check below:叙述字段（claims/signals）
# 里的退役路径是当年的引文，改了就是篡改证据（AGENTS.md「历史条目按原样保留」）。
EPISODE_EVIDENCE_FIELDS = ("evidence_ref", "ref", "path", "artifact")


def iter_evidence_values(node: Any, fields: tuple[str, ...]) -> list[tuple[str, str]]:
    """Collect `(field, value)` pairs stored under one of `fields`, at any depth.

    字段名跟着值一起走：只报「某个指针不成立」，读者还得在一条有十几条 claims 的记录里
    自己再找一遍（评审 P2-3）。
    """
    values: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, child in node.items():
            if key in fields:
                if isinstance(child, str):
                    values.append((key, child))
                elif isinstance(child, list):
                    values.extend((key, item) for item in child if isinstance(item, str))
            values.extend(iter_evidence_values(child, fields))
    elif isinstance(node, list):
        for item in node:
            values.extend(iter_evidence_values(item, fields))
    return values


def validate_episode_references(document: dict[str, Any], path: Path) -> list[ValidationError]:
    """A pointer field must point at something a later session can still open — or say it cannot.

    Two honest spellings are accepted for an object that is gone: `N/A: <reason>` and a
    repository-qualified `repo@revision:path`. Anything shaped like an in-repo path that no
    longer resolves is a finding, so the record cannot quietly claim evidence that evaporated.
    """
    errors: list[ValidationError] = []
    repo_root = ROOT.resolve()
    for field, value in iter_evidence_values(document, EPISODE_EVIDENCE_FIELDS):
        token = value.strip()
        if NA_REASON_PATTERN.search(token):
            continue
        bare = token.strip(":： ").upper()
        if bare in {"N/A", "N/A：", "N/A "}:
            # 裸 N/A 不是豁免：C23 对计划证据列要求「N/A: 理由」，同一口径不能在这里松掉，
            # 否则「写个 N/A 就当没有证据这回事」会变成新的绕过路径。
            errors.append(
                ValidationError(
                    str(path),
                    f"{field}: bare 'N/A' is not an exemption — write 'N/A: <reason>' naming "
                    "what carried the evidence away (same carrier rule as C23's evidence column)",
                )
            )
            continue
        cleaned = URL_PATTERN.sub(" ", QUALIFIED_REF_PATTERN.sub(" ", token))
        if re.search(r"(?:^|[\s(（{])/(?:tmp|private|Users|home)/", cleaned):
            errors.append(
                ValidationError(
                    str(path),
                    f"{field}: pointer {token[:60]!r} names an ephemeral absolute path — "
                    "只在 /tmp 存在过的证据不可复核（与 C23 同口径），改写为 'N/A: 理由 + 出处'",
                )
            )
            continue
        # 一个字段值里可以并列好几条路径（「A；B；C」形态），必须逐条判定；
        # 原先要求整值成形状才判，这类值整体跳过，于是「失效指针 0 条」与「一条没少」同时为真。
        for ref in BODY_PATH_PATTERN.findall(cleaned):
            repo_candidate = (ROOT / ref).resolve()
            local_candidate = (path.parent / ref).resolve()
            if repo_candidate.is_file() and repo_candidate.is_relative_to(repo_root):
                continue
            if local_candidate.is_file() and local_candidate.is_relative_to(repo_root):
                continue
            errors.append(
                ValidationError(
                    str(path),
                    f"{field}: evidence pointer {ref!r} resolves neither in this repository nor "
                    "next to the record — carry it, or write 'N/A: <reason>' / "
                    "'<repo>@<revision>:<path>' for an object that is gone",
                )
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


def review_tier_findings(frontmatter: dict[str, Any], path: Path) -> list[ValidationError]:
    """A declared L0 must carry the dispatch errors that made it true.

    `skills/agentflow/references/contracts.md` states the rule ("`review_tier: L0` 而
    `dispatch_errors` 为空，是伪降级，同样无效") but nothing enforced it until 2026-10-29
    (docs/PENDING-DECISIONS.md 第 17 条 的同一条欠账). The schema's `allOf` keeps the shape;
    this check exists so the finding names the record. A record without `review_tier` at all is
    标注为未声明 — neither green nor red — because back-fitting the tier would be inventing
    evidence for rounds nobody probed.
    """
    tier = frontmatter.get("review_tier")
    if not isinstance(tier, str):
        return []  # 未声明：不判红也不判绿（历史记录不被追溯打红）
    if tier not in ("L0", "L1", "L2"):
        return [ValidationError(str(path), f"review_tier {tier!r} must be one of ('L0', 'L1', 'L2')")]
    if tier != "L0":
        return []
    errors_field = frontmatter.get("dispatch_errors")
    if isinstance(errors_field, list) and any(str(item).strip() for item in errors_field):
        return []
    if isinstance(errors_field, str) and errors_field.strip():
        return []
    return [
        ValidationError(
            str(path),
            "伪降级：review_tier 声明 L0 却没有 dispatch_errors——降级要留下失败派发的原始"
            "返回，否则「主审自审」与「独立评审」在记录上无法区分",
        )
    ]


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
    # 伪降级判定必须先于 schema 早退（2026-10-29 独立评审 P1-1）：allOf 与这条判据吃同一个
    # 形态，放在早退之后就是不可达代码——门只会报「$: missing required property 'dispatch_errors'」，
    # 不说是哪份记录在伪降级；而「finding 指向记录」正是 spec M-D-02 与 design §7.3 的验收口径。
    errors.extend(review_tier_findings(frontmatter, path))
    if errors:
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
            m = re.fullmatch(r"REV-(\d{4})-(\d{2})-(\d{2})-(\d{3})", review_id)
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


# G09: closure_criteria historically embedded brittle source line numbers
# (e.g. `document-chain.md:284-286`) that silently drift as the target file edits.
# The contract value is the clause/identifier, not a line — a line ref stops being
# verifiable the moment the cited file is edited. This weak check flags the pattern so
# drift stops being silent; the records themselves carry the clause name instead.
CLOSURE_LINE_REF = re.compile(r"[^\s:（）()，、|]+\.(?:md|py|json|go|ts|js):\d+(?:-\d+)?")


def closure_criteria_line_ref_errors(frontmatter: dict[str, Any], path: Path) -> list[ValidationError]:
    """G09 — closure_criteria must not pin a source line number.

    A line number is a snapshot that rots on the next edit to the cited file; the
    contract value is the clause name (and a path, which git-history can audit via C17).
    Flag any `path.ext:NN` reference so drift becomes an explicit, greppable finding
    instead of a silently-stale verification claim.
    """
    value = frontmatter.get("closure_criteria")
    if not isinstance(value, str):
        return []
    refs = CLOSURE_LINE_REF.findall(value)
    if not refs:
        return []
    return [
        ValidationError(
            str(path),
            "closure_criteria 不应钉死源文件行号（"
            + "、".join(refs)
            + "）——行号随引用文件编辑悄悄过期；改为写明条款名 + 路径，行号由 git 历史（C17）审计",
        )
    ]


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
    errors.extend(closure_criteria_line_ref_errors(frontmatter, path))

    for heading in BUG_REQUIRED_HEADINGS:
        if not heading_present(body, heading):
            errors.append(ValidationError(str(path), f"body section {heading!r} is required"))
    if frontmatter.get("status") != "open" and not heading_present(body, "## 修复"):
        errors.append(ValidationError(str(path), "body section '## 修复' is required unless the bug is open"))
    if frontmatter.get("status") == "verified" and not heading_present(body, "## 审查"):
        errors.append(ValidationError(str(path), "body section '## 审查' is required for a verified record"))
    if frontmatter.get("status") != "open" and not heading_present(body, "## 变更记录"):
        errors.append(
            ValidationError(str(path), "body section '## 变更记录' is required once a record leaves open")
        )
    return errors


def validate_bug_layout(frontmatter: dict[str, Any], path: Path, relative: Path, seen_ids: dict[str, Path]) -> list[ValidationError]:
    """Validate filename shape and bug_id uniqueness for one record.

    Live records are flat: issues/ISS-<YYYY-MM-DD>-<slug>.md; the stem is the id, so it must
    equal bug_id, and its date must equal recorded_at's date. Archived (rejected) records keep
    a date directory: issues/归档/<YYYY-MM-DD>/ISS-<YYYY-MM-DD>-<slug>.md.
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
    filename_match = BUG_FILENAME_PATTERN.match(path.stem)
    if not filename_match:
        errors.append(
            ValidationError(
                str(path),
                "filename must be ISS-<YYYY-MM-DD>-<slug> "
                "(letters, digits, Chinese, hyphens) — e.g. ISS-2026-09-14-claude-json-schema-被拒.md",
            )
        )
    else:
        if isinstance(bug_id, str) and bug_id != path.stem:
            errors.append(
                ValidationError(
                    str(path),
                    f"filename stem must equal bug_id {bug_id!r} (the stem is the record id)",
                )
            )
        recorded_date = record_date_of(frontmatter)
        if recorded_date is not None and recorded_date.isoformat() != "-".join(filename_match.group(1, 2, 3)):
            errors.append(
                ValidationError(
                    str(path),
                    f"filename date must match recorded_at date {recorded_date.isoformat()}",
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
            ValidationError(str(path), "live issue records live directly under docs/issues/ (docs/issues/ISS-<YYYY-MM-DD>-<slug>.md)")
        )
    return errors
