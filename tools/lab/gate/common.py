"""Shared primitives for the gate checks: paths, record parsing, and date/id helpers."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


BUG_RECORD_SCHEMA = ROOT / "schemas" / "bug-record.schema.json"


RECURRENCE_SCHEMA = ROOT / "schemas" / "recurrence.schema.json"


REVIEW_SCHEMA = ROOT / "schemas" / "review.schema.json"


TEST_PLAN_SCHEMA = ROOT / "schemas" / "test-plan.schema.json"


TEST_RUN_SCHEMA = ROOT / "schemas" / "test-run.schema.json"


EPISODE_SCHEMA = ROOT / "skills" / "improve" / "references" / "episode.schema.json"


PROTECTED_PATHS_FILE = ROOT / "protected-paths.txt"


# The minimum gate surface protected-paths.txt must still cover. Editing this set is a release
# policy change and requires explicit human review; it is not something a candidate may arrange
# around. Keep it in sync with the inclusion rule documented in protected-paths.txt.
REQUIRED_PROTECTED_PATHS = {
    "agents/evaluator.md",
    "agents/release-governor.md",
    "schemas/bug-record.schema.json",
    "schemas/recurrence.schema.json",
    "schemas/review.schema.json",
    "schemas/plan.schema.json",
    "schemas/test-plan.schema.json",
    "schemas/test-run.schema.json",
    "skills/improve/references/evidence-and-release.md",
    "skills/improve/references/episode.schema.json",
    "skills/improve/references/candidate.schema.json",
    "skills/improve/references/release-record.schema.json",
    "tests/test_gate_schema.py",
    "tests/test_gate_integrity.py",
    "tests/test_gate_records.py",
    "tests/test_doc_chain.py",
    "tests/test_record_store.py",
    "tests/test_workflow.py",
    "tests/test_pre_push.py",
    "tools/lab/artifact_digest.py",
    "tools/lab/counts.py",
    "tools/lab/doc_chain.py",
    "tools/lab/docchain/__init__.py",
    "tools/lab/docchain/constants.py",
    "tools/lab/docchain/checks.py",
    "tools/lab/docchain/selftest.py",
    "tools/lab/docchain/cli.py",
    "tools/lab/gate/checks.py",
    "tools/lab/gate/common.py",
    "tools/lab/gate/docs.py",
    "tools/lab/gate/examples.py",
    "tools/lab/gate/installed.py",
    "tools/lab/gate/manifests.py",
    "tools/lab/gate/plan.py",
    "tools/lab/gate/records.py",
    "tools/lab/gate/reports.py",
    "tools/lab/gate/schema.py",
    "tools/lab/gate/testing.py",
    "tools/lab/gate/workspace.py",
    "tools/lab/isolation.py",
    "tools/lab/mutate.py",
    "tools/lab/record_store.py",
    "tools/lab/trend.py",
    "tools/lab/validate.py",
    "packaging/build_runtime.py",
    "skills/agentflow/scripts/check-write-scope.sh",
    "skills/agentflow/scripts/workflow.py",
    "skills/agentflow/scripts/workflow_lib",
    "skills/agentflow/references/contracts.md",
    "protected-paths.txt",
    ".github/workflows/validate.yml",
}


# Declared contents of `tests/`. The directory is not a protected prefix — generated
# `__pycache__` entries there would otherwise block every candidate that ran the checks — so the
# pinned test files are protected individually and this list asserts nothing else appears. A new
# test file is a human-authored change to this list plus the protection entry above.
EXPECTED_TEST_FILES = (
    "test_gate_schema.py",
    "test_gate_integrity.py",
    "test_gate_records.py",
    "test_doc_chain.py",
    "test_record_store.py",
    "test_workflow.py",
    "test_pre_push.py",
)


# Live record roots (2026-10-12 slimming batch, phase 4): the top-level plans/ root was
# dissolved — plans live inside their feature batch (docs/features/<batch>/plan/), matching
# youc-workflow-ai / aiwork-workflow-ai where a feature owns its plan/spec/design segments.
# Five record zones now: docs/issues, docs/releases (working files only; per-version release
# JSON was retired with the 0.8.x records, the improvements/ three-subtree by user decision),
# docs/features (batch directories; only plan/*.md carries a machine contract here), plus
# episodes/ and reviews/ at the root. The cross-batch decision queue sits at
# docs/PENDING-DECISIONS.md, outside any record root.
# `validate_workspace_artifacts` walks each root and compiles what it holds.
LIVE_RECORD_ROOTS = ("docs/issues", "docs/releases", "docs/features", "episodes", "reviews")


# 2026-10-12 slimming batch (user-authorized gate change, ISS-2026-047): the frozen `_archive/`
# tree was removed outright — the repository keeps no archive bucket. Its former exemptions
# (scan exclusions, the handoff-pointer waiver) are deleted with it, and the retired doc
# carriers `docs/iteration-log.md` / `docs/agent-roles.md` joined RETIRED_PATH_TOKENS below so
# recreating them fails the residue scan instead of drifting back in.


# Floor for the regression suite size, parsed from the unittest "Ran N tests" summary. The
# floor is set far below the suite's steady state but far above a trivial suite, so deleting
# or gutting the tests cannot yield a green gate — shrinking the suite becomes a deliberate
# gate change that must be reviewed, not an accident that passes. (A hardcoded current count
# went stale here once already — BUG-era finding N7 — so the suite size is asserted by the
# run itself, never restated in prose.)
MIN_UNIT_TEST_COUNT = 20


# Floor for the doc-chain linter's discrimination self-test, parsed from the linter's
# "N/M self-test cases pass" summary. Same bargain as MIN_UNIT_TEST_COUNT: the floor stays
# far below the linter's steady state and far above a trivial suite, so gutting the checker's
# own discrimination matrix cannot yield a green gate.
MIN_DOC_CHAIN_SELF_TEST_CASES = 20


# Every manifest that carries the plugin name and version. They are bumped by hand, so a missed
# bump would otherwise surface only after a host reinstall. The pointer locates the value.
MANIFEST_POINTERS = (
    ("plugin.json", ()),
    ("marketplace.json", ("plugins", 0)),
    (".zcode-plugin/plugin.json", ()),
    (".claude-plugin/plugin.json", ()),
    (".codex-plugin/plugin.json", ()),
)


# Components whose content decides installed plugin behavior. Anything outside this list
# (docs, record artifacts) may legitimately differ between a source checkout and a snapshot.
INSTALLED_COMPONENTS = ("agents", "skills")


INSTALLED_FILES = (
    "plugin.json",
    "marketplace.json",
    "protected-paths.txt",
    ".zcode-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
)


class ValidationError:
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def load_json(path: Path) -> tuple[Any | None, list[ValidationError]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, [ValidationError(str(path), f"invalid JSON: {exc}")]


def read_document_text(path: Path) -> tuple[str, list[ValidationError]]:
    """Read a Markdown/text document for a doc-surface check; read failures are structured.

    Mirrors `load_json` for text: UnicodeDecodeError is a ValueError, not an OSError, so a
    file saved in a non-UTF-8 encoding (or a missing document) must surface as a
    ValidationError instead of an uncaught traceback escaping the check. On failure the text
    is the empty string and the error list is non-empty, so callers that check `read_errors`
    first never observe the empty text.
    """
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeDecodeError) as exc:
        return "", [ValidationError(str(path), f"cannot read document: {exc}")]


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    """Parse a '---' delimited frontmatter block of flat scalars and simple lists.

    Accepts exactly: blank lines, `key: value` scalars, `key:` starting a list of
    `  - item` lines, and `key: [a, b]` inline lists. Anything else is an error —
    nested mappings are deliberately unsupported so the contract stays flat.
    """
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "", ["frontmatter block is missing"]
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, "", ["frontmatter block is not closed"]

    data: dict[str, Any] = {}
    list_key: str | None = None
    for lineno, raw in enumerate(lines[1:end], start=2):
        line = raw.rstrip()
        if not line.strip():
            continue
        if "\t" in line:
            errors.append(f"frontmatter line {lineno}: tabs are not allowed")
            continue
        if line.startswith("  - "):
            if list_key is None:
                errors.append(f"frontmatter line {lineno}: list item without a key")
                continue
            data[list_key].append(line[4:].strip())
            continue
        if line.startswith("- "):
            errors.append(f"frontmatter line {lineno}: list items must be indented under a key")
            continue
        if line.startswith("  "):
            errors.append(f"frontmatter line {lineno}: nested mappings are not supported")
            continue
        if ":" not in line:
            errors.append(f"frontmatter line {lineno}: expected 'key: value'")
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            errors.append(f"frontmatter line {lineno}: empty key")
            continue
        if key in data:
            errors.append(f"frontmatter line {lineno}: duplicate key {key!r}")
            continue
        if value == "":
            data[key] = []
            list_key = key
            continue
        list_key = None
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [item.strip() for item in inner.split(",") if item.strip()]
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            data[key] = value
    body = "\n".join(lines[end + 1 :])
    return data, body, errors


def load_record_markdown(path: Path) -> tuple[dict[str, Any] | None, str, list[ValidationError]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError is a ValueError, not an OSError: a non-UTF-8 record must
        # surface as a structured ValidationError (mirrors read_document_text), not an
        # uncaught traceback escaping the check.
        return None, "", [ValidationError(str(path), f"unreadable file: {exc}")]
    frontmatter, body, parse_errors = parse_frontmatter(text)
    if parse_errors:
        return None, "", [ValidationError(str(path), message) for message in parse_errors]
    if not isinstance(frontmatter, dict) or not frontmatter:
        return None, "", [ValidationError(str(path), "frontmatter is empty")]
    return frontmatter, body, []


def heading_present(body: str, heading: str) -> bool:
    return any(line.strip() == heading for line in body.splitlines())


def json_equal_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def json_values_equal(left: Any, right: Any) -> bool:
    """Compare JSON values using JSON Schema equality (booleans are not numbers)."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


RFC3339_DATE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)


def parse_rfc3339_date_time(value: str) -> dt.datetime:
    """Parse the RFC 3339 subset supported by the standard library.

    Repository artifacts accept either case for the RFC 3339 ``T``/``Z`` separators.
    Leap-second values (``:60``) remain intentionally unsupported because Python's
    ``datetime`` cannot represent them.
    """
    if RFC3339_DATE_TIME.fullmatch(value) is None:
        raise ValueError("must be an RFC 3339 date-time")
    parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00" if value[-1] in "Zz" else value)
    if parsed.tzinfo is None:
        raise ValueError("must include a timezone offset")
    return parsed


def is_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def path_inside_root(relative_ref: str) -> Path | None:
    candidate = (ROOT / relative_ref).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def files_entry_errors(entry: str, path: Path) -> list[ValidationError]:
    """A `files:` entry is a repository-relative path inside ROOT, or a repo-qualified reference.

    Absolute paths and `../` climbs are rejected: the bare is_file() check resolved (ROOT / entry),
    which ignores ROOT for an absolute entry and walks out of it for `../`.
    """
    head, separator, _ = entry.partition(":")
    if separator and "@" in head:
        return []  # repo-qualified address; its evidence is checked by the external-excerpt rule
    if Path(entry).is_absolute():
        return [ValidationError(str(path), f"files entry {entry!r} must be repository-relative, not absolute")]
    if path_inside_root(entry) is None:
        return [ValidationError(str(path), f"files entry {entry!r} resolves outside the repository")]
    if not (ROOT / entry).is_file():
        return [
            ValidationError(
                str(path),
                f"files entry {entry!r} exists neither in this repository nor as a "
                "repo-qualified reference (<repo>@<revision>:<path>)",
            )
        ]
    return []


def validate_timestamp_order(document: dict[str, Any], path: Path) -> list[ValidationError]:
    recorded = document.get("recorded_at")
    updated = document.get("updated_at")
    if not isinstance(recorded, str):
        return []
    timestamps: list[tuple[str, str]] = [("recorded_at", recorded)]
    if isinstance(updated, str):
        timestamps.append(("updated_at", updated))
    parsed: dict[str, dt.datetime] = {}
    for name, raw in timestamps:
        try:
            parsed[name] = parse_rfc3339_date_time(raw)
        except ValueError:
            return [ValidationError(str(path), f"{name} must be an RFC 3339 date-time value")]
    now = dt.datetime.now(dt.UTC)
    for name, value in parsed.items():
        if value > now + dt.timedelta(minutes=5):
            errors = [ValidationError(str(path), f"{name} is in the future; stamps must reflect real time")]
            return errors
    if "updated_at" in parsed and parsed["updated_at"] < parsed["recorded_at"]:
        return [ValidationError(str(path), "updated_at must not precede recorded_at")]
    return []


def record_date_of(frontmatter: dict[str, Any]) -> dt.date | None:
    """Calendar date of recorded_at, or None when it is absent or does not parse."""
    recorded = frontmatter.get("recorded_at")
    if not isinstance(recorded, str):
        return None
    try:
        return dt.datetime.fromisoformat(recorded.replace("Z", "+00:00")).date()  # noqa: FURB162
    except ValueError:
        return None


def dated_id_errors(
    path: Path, frontmatter: dict[str, Any], match: re.Match[str], stem_prefix: str, id_field: str
) -> list[ValidationError]:
    """Filename stem and recorded_at date must agree with a dated id (<PREFIX>-YYYYMMDD-NNN).

    `match` is the fullmatch of that id. Shared by review, test-plan and test-run records; the
    caller keeps the id-shape decision and any fallback message for ids that do not match.
    """
    errors: list[ValidationError] = []
    expected_stem = f"{stem_prefix}-{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
    if path.stem != expected_stem:
        errors.append(
            ValidationError(
                str(path),
                f"filename must be {expected_stem}.md to match {id_field} {frontmatter.get(id_field)!r}",
            )
        )
    recorded_date = record_date_of(frontmatter)
    if recorded_date is not None and recorded_date.strftime("%Y%m%d") != "".join(match.group(1, 2, 3)):
        errors.append(
            ValidationError(
                str(path),
                f"{id_field} date must match recorded_at date {recorded_date.isoformat()}",
            )
        )
    return errors


def is_separator_row(line: str) -> bool:
    """True for a Markdown table separator row (---|:---:|...)."""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return bool(cells) and all(set(cell) <= {"-", ":", " "} and cell for cell in cells)


def parse_plan_task_row(line: str) -> dict[str, list[str]] | None:
    """Parse one Markdown table row of the plan task table into its cells."""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if len(cells) < 3:
        return None
    if all(set(cell) <= {"-", ":", " "} for cell in cells):
        return None  # separator row
    return {"cells": cells}


def version_tuple(value: str) -> tuple[int, int, int]:
    """Numeric ordering key for the semver-like versions the schemas enforce."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


QUALIFIED_REF_PATTERN = re.compile(r"[A-Za-z0-9_.\-]+@[A-Za-z0-9_.\-]+:\S+")
