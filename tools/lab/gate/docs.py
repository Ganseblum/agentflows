"""Role/document surface, version-prose guard and retired-path residue scans."""

from __future__ import annotations

import re
from pathlib import Path

from .common import (
    LIVE_RECORD_ROOTS,
    QUALIFIED_REF_PATTERN,
    ROOT,
    ValidationError,
    read_document_text,
)

ROLE_NAME_PATTERN = re.compile(r"^name:\s*([a-z0-9-]+)\s*$", re.MULTILINE)


SKILL_ROLE_PATTERN = re.compile(r"agentflow:([a-z0-9-]+)")


# 0.5.0 switched plans from JSON to Markdown hybrids (plans/README.md); either
# stale marker in AGENTS.md signals the pre-0.5.0 contract and must fail the docs check.
PRE_050_PLAN_CONTRACT_MARKERS = ("plans are JSON", "<plan_id>.json")


def validate_agents_md_plan_contract(agents_md: Path) -> list[ValidationError]:
    """Tripwire: AGENTS.md must not carry the pre-0.5.0 JSON plan contract wording."""
    errors: list[ValidationError] = []
    text, read_errors = read_document_text(agents_md)
    if read_errors:
        return read_errors
    if any(marker in text for marker in PRE_050_PLAN_CONTRACT_MARKERS):
        errors.append(
            ValidationError(
                str(agents_md),
                "AGENTS.md carries the pre-0.5.0 JSON plan contract; plans are Markdown "
                "hybrids named <plan_id>.md — see docs/features/README.md",
            )
        )
    return errors


# Files whose prose states the plugin's current maturity. Version literals there drift on
# every bump (the 0.6.0 → 0.7.4 → 0.7.5 hand-sync family); the version lives in the five
# manifests and CHANGELOG, and these files must point at it instead of restating it.
VERSION_PROSE_FILES = (
    "README.md",
    "docs/design-decisions.md",
)


VERSION_LITERAL_PATTERN = re.compile(r"\bv?\d+\.\d+\.\d+\b")


# Retired-path residue on the live document surface (2026-10-09 cleanup batch). The 2026-10
# structural overhaul mechanically re-pointed existing references, but nothing kept NEW prose
# from naming a retired path again — the same reliance-on-memory gap this check family exists to
# close. Two classes are machine-checkable: a relative Markdown link whose target does not
# resolve, and a retired path token in prose. Fenced blocks and inline code are quotations, not
# claims (the record contracts' 引文 exemption) — but a mermaid diagram is content, not a
# quotation, so diagrams stay scanned. The generated `packaging/runtime/` tree is out of both
# scans; `CHANGELOG.md` is exempt from the token scan only — its entries describe the layout of
# their own time and keep retired paths verbatim. The 2026-10-12 slimming batch removed the
# frozen `_archive/` bucket and the migration-record exemption with it: those paths are now
# residue like any other, and the two retired doc carriers joined the token list.
RETIRED_PATH_TOKENS = (
    "records/",
    "bugs/",
    "improvement/",
    "improvements/",
    "docs/audit-2026-09-18",
    "next-session-handoff",
    "docs/iteration-log",
    "docs/agent-roles",
)


# Migrated, not deleted (2026-10-12 phased overhaul, ISS-2026-048 / ISS-2026-049). A migration
# differs from a retired tree only in what the old spelling leaves behind: the two plural moves
# issues/ -> docs/issues/ and releases/ -> docs/releases/ survive as the live path's own
# suffix, so a bare token would punish the new path — those are deliberately NOT tokens. The one
# migration with no live descendant is the top-level plans/ root, which dissolved into the
# *singular* docs/features/<batch>/plan/. It is written `docs/plans` (not `plans/`) so it cannot
# collide with examples/plans/, a live fixture directory.
MIGRATED_PATH_TOKENS = ("docs/plans",)


PATH_RESIDUE_TOKENS = RETIRED_PATH_TOKENS + MIGRATED_PATH_TOKENS


HISTORICAL_DOC_CARRIERS = ("CHANGELOG.md",)


FENCED_BLOCK_PATTERN = re.compile(r"```(?P<info>[^\n`]*)\n.*?```", re.DOTALL)


# Inline code runs on a single line: a backtick never pairs across a newline. The DOTALL-style
# `[^`]*` predecessor let one "inline code" span swallow whole paragraphs when backticks were
# unbalanced, hiding every link on the way (2026-10-20 evaluation G16 — CHANGELOG's four
# relative links were invisible to this gate).
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]*`")


LINK_TARGET_PATTERN = re.compile(r"\]\(([^)]+)\)")


def strip_quotation_fences(text: str) -> str:
    """Remove fenced blocks except mermaid diagrams; a diagram is content, not a quotation."""
    def keep_mermaid(match: re.Match) -> str:
        return match.group(0) if match.group("info").strip().startswith("mermaid") else ""

    return FENCED_BLOCK_PATTERN.sub(keep_mermaid, text)


def live_doc_paths(root: Path) -> list[Path]:
    """Every *.md outside the generated runtime tree."""
    paths: list[Path] = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if relative.as_posix().startswith("packaging/runtime/"):
            continue
        paths.append(path)
    return sorted(paths)


def validate_live_doc_references(root: Path = ROOT) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for path in live_doc_paths(root):
        relative = path.relative_to(root)
        text, read_errors = read_document_text(path)
        if read_errors:
            errors.extend(read_errors)
            continue
        link_scan_text = INLINE_CODE_PATTERN.sub("", strip_quotation_fences(text))
        for match in LINK_TARGET_PATTERN.finditer(link_scan_text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#", "<", "/")):
                continue
            target_path = target.split("#", 1)[0].strip()
            if not target_path or target_path.startswith("<"):
                continue
            if not (path.parent / target_path).exists():
                errors.append(ValidationError(str(relative), f"broken relative link: {target}"))
        if relative.as_posix() in HISTORICAL_DOC_CARRIERS:
            continue
        inside_fence: str | None = None
        for number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("```"):
                fence_info = line.lstrip()[3:].strip()
                inside_fence = None if inside_fence is not None else fence_info
                continue
            if inside_fence is not None and not inside_fence.startswith("mermaid"):
                continue
            # A repo-qualified reference (<repo>@<revision>:<path>) is an address, not a
            # claim — the record contracts accept it verbatim in prose and frontmatter, so
            # the token scan strips it before matching (agentflows@0.8.2:docs/agent-roles.md
            # must stay citable inside a record even after docs/agent-roles was retired).
            scan = QUALIFIED_REF_PATTERN.sub(" ", INLINE_CODE_PATTERN.sub("", line))
            for token in PATH_RESIDUE_TOKENS:
                index = scan.find(token)
                while index != -1:
                    preceded_by_word = index > 0 and (
                        scan[index - 1].isalnum() or scan[index - 1] == "_"
                    )
                    if not preceded_by_word:
                        errors.append(
                            ValidationError(
                                str(relative),
                                f"retired path in prose (line {number}): {token!r}",
                            )
                        )
                    index = scan.find(token, index + 1)
    return errors


def validate_doc_consistency() -> list[ValidationError]:
    """Cross-check the hand-synced role/document surface (the 0.3.3 manifest-drift family).

    The role/doc surface is synced by hand across twelve agent files, two SKILLs, the roles
    reference, the class READMEs under the live record roots, and the root AGENTS.md — the same
    failure class as the missed manifest bump. Four assertion groups: every agent file's
    frontmatter name equals its filename; every `agentflow:<role>` referenced by a SKILL
    resolves to an agent file; every `schemas/*.schema.json` path named anywhere in the
    docs/live-roots/skills/agents surface or in AGENTS.md exists; AGENTS.md carries no
    pre-0.5.0 JSON plan contract markers. (A fifth group — "the Chinese mirror keeps section
    parity with its English contract documents" — was claimed here until 2026-10-20 but never
    implemented; the claim was removed rather than the check invented, evaluation G05.)
    Two live-surface scans close the 2026-10 residue classes:
    relative Markdown links must resolve, and prose must not name a retired path (fenced and
    inline code are quotations — except mermaid diagrams, which are content — and
    `CHANGELOG.md` keeps its historical entries verbatim).
    """
    errors: list[ValidationError] = []
    agents_dir = ROOT / "agents"
    if not agents_dir.is_dir():
        errors.append(ValidationError(str(agents_dir), "agents/ directory is missing; the role surface is required"))
    agent_files = {p.stem: p for p in sorted(agents_dir.glob("*.md"))}
    if agents_dir.is_dir() and not agent_files:
        errors.append(ValidationError(str(agents_dir), "agents/ holds no role files; the role surface is required"))
    for name, path in agent_files.items():
        # The directory entry-point document (agents/README.md) carries no role frontmatter —
        # it is the index, not a role. Every actual role file still must match name == filename.
        if name == "README":
            continue
        text, read_errors = read_document_text(path)
        if read_errors:
            errors.extend(read_errors)
            continue
        m = ROLE_NAME_PATTERN.search(text)
        if not m:
            errors.append(ValidationError(str(path), "agent file frontmatter lacks a name field"))
        elif m.group(1) != name:
            errors.append(
                ValidationError(str(path), f"frontmatter name {m.group(1)!r} does not match filename {name!r}")
            )

    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        errors.append(ValidationError(str(skills_dir), "skills/ directory is missing; the skill surface is required"))
    for skill in sorted(skills_dir.glob("*/SKILL.md")):
        text, read_errors = read_document_text(skill)
        if read_errors:
            errors.extend(read_errors)
            continue
        for role in sorted(set(SKILL_ROLE_PATTERN.findall(text))):
            if role not in agent_files:
                errors.append(
                    ValidationError(str(skill), f"references agentflow:{role!r} but agents/{role}.md does not exist")
                )

    reference_surface = [
        ROOT / "docs",
        *(ROOT / name for name in LIVE_RECORD_ROOTS),
        ROOT / "skills",
        ROOT / "agents",
        ROOT / "README.md",
        ROOT / "AGENTS.md",
    ]
    schema_ref_pattern = re.compile(r"schemas/([a-z0-9-]+\.schema\.json)")
    schema_dir = ROOT / "schemas"
    for base in reference_surface:
        files = base.rglob("*.md") if base.is_dir() else [base]
        for doc in sorted(files):
            text, read_errors = read_document_text(doc)
            if read_errors:
                errors.extend(read_errors)
                continue
            for schema in schema_ref_pattern.findall(text):
                if not (schema_dir / schema).is_file():
                    errors.append(
                        ValidationError(str(doc), f"references schemas/{schema!r} which does not exist")
                    )

    errors.extend(validate_agents_md_plan_contract(ROOT / "AGENTS.md"))

    # Version-in-prose guard: the current-version claims in these files were hand-synced
    # at every bump and drifted more than once (0.6.0 was still being declared after
    # 0.7.4 shipped). The manifests own the version; these files must reference it.
    for name in VERSION_PROSE_FILES:
        path = ROOT / name
        text, read_errors = read_document_text(path)
        if read_errors:
            errors.extend(read_errors)
            continue
        errors.extend(version_prose_errors(path, text))

    errors.extend(validate_live_doc_references(ROOT))
    return errors


def version_prose_errors(path: Path, text: str) -> list[ValidationError]:
    """Flag an x.y.z version literal in the version-guarded prose files."""
    errors: list[ValidationError] = []
    for match in VERSION_LITERAL_PATTERN.finditer(text):
        context = text[max(0, match.start() - 40) : match.end() + 40].replace("\n", " ")
        errors.append(
            ValidationError(
                str(path),
                f"version literal {match.group(0)!r} in prose ({context.strip()!r}); state "
                "the version only in the manifests and CHANGELOG and reference them here",
            )
        )
    return errors
