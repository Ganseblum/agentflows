#!/usr/bin/env python3
"""Decision-ledger tooling: the cross-batch decision queue as a parseable ledger.

This module is the machine half of the D8 decision system (proposal §4.2, G7-AC-01..05).
The ledger lives at ``docs/PENDING-DECISIONS.md`` and follows the "只追加、永不移出"
rule: a decision, once recorded as ``DEC-YYYY-NNN``, is never removed. It advances by
revision (``r1``, ``r2`` …), a revision may be withdrawn, and the current revision may
declare ``equivalent_to`` an earlier one so downstream pins do not go stale on a
text-only change.

Three subcommands:

* ``view``        — render the *pending* view (only still-active decisions), replacing the
                    old manual row-carry where resolved rows were lifted out by hand.
* ``check``       — scan every downstream document's ``decision_deps`` frontmatter, compute
                    the reverse index, and report only the documents truly affected by a
                    decision revision. Pinning a withdrawn revision is red; pinning an
                    ``equivalent_to`` revision stays green; an affected doc may register a
                    ``stale_reason`` + ``review_date`` to stay green; pinning only an
                    invariant stays green while the invariant still holds.
* ``index --write`` — regenerate ``docs/decisions/index.md`` (a generated file; hand-edits
                      are caught by the gate's digest assertion).

The module is standard-library only so the gate can import it without side effects.
"""

from __future__ import annotations

import hashlib
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PENDING_DECISIONS = ROOT / "docs" / "PENDING-DECISIONS.md"
DECISIONS_INDEX = ROOT / "docs" / "decisions" / "index.md"

# Columns the decision-record table must carry (mirrors docchain C16's DECISION_COLUMNS so
# the same table serves both the human queue and this tool). The revision-tracking columns
# are appended after the human columns and are read only by this tool.
DECISION_COLUMNS = [
    "来源",
    "待决问题",
    "现状核验",
    "推荐",
    "关闭条件",
    "优先级",
    "影响范围",
    "自动决策",
]

DEC_ID_RE = re.compile(r"^DEC-(\d{4})-(\d{3})$")
REV_TOKEN_RE = re.compile(r"^r(\d+)$")
REV_INLINE_RE = re.compile(r"(\d+)")
DIGEST_RE = re.compile(r"<!--\s*decision-index-digest:\s*([0-9a-f]{64})\s*-->")

# decision_deps frontmatter token forms (flat, inline-list so the gate's flat frontmatter
# parser accepts them without a nested-mapping error):
#   DEC-YYYY-NNN#rN                       pin a revision
#   DEC-YYYY-NNN#invariant=<text>         pin an invariant (text must still appear)
#   DEC-YYYY-NNN#rN#stale_reason=<...>#review_date=YYYY-MM-DD   tolerated stale pin
DEP_TOKEN_RE = re.compile(r"^(DEC-\d{4}-\d{3})#(.+)$")


# --------------------------------------------------------------------------- #
# Ledger parsing
# --------------------------------------------------------------------------- #
def _split_row(line: str) -> list[str]:
    """Split a Markdown table row into cells (outer pipes optional, trimmed)."""
    text = line.strip().removeprefix("|").removesuffix("|")
    return [cell.strip() for cell in text.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(set(cell) <= {"-", ":", " "} and cell for cell in cells)


def parse_ledger(text: str) -> dict[str, dict[str, Any]]:
    """Parse the decision-record table in ``docs/PENDING-DECISIONS.md``.

    Returns ``{decision_id: record}`` where each record has: rev (int), withdrawn (set[int]),
    equivalent_to (set[int]), terminal (str), status (str), text (str), row (dict[str,str]).
    Only rows whose ``#`` (or ``DEC编号``) cell matches ``DEC-YYYY-NNN`` enter the ledger.
    """
    records: dict[str, dict[str, Any]] = {}
    lines = text.splitlines()
    header: dict[str, int] | None = None
    for raw in lines:
        if not raw.strip().startswith("|"):
            continue
        cells = _split_row(raw)
        if header is None:
            # Identify the decision-record table by its columns.
            if all(col in cells for col in DECISION_COLUMNS):
                header = {name: i for i, name in enumerate(cells) if name}
            continue
        if _is_separator(cells):
            continue
        id_col = header.get("DEC编号", header.get("#", -1))
        if id_col is None or id_col < 0 or id_col >= len(cells):
            continue
        dec_id = cells[id_col].strip()
        if not DEC_ID_RE.match(dec_id):
            continue
        row = {name: (cells[i] if i < len(cells) else "") for name, i in header.items()}

        def _rev_value(name: str, row: dict[str, str] = row) -> int:
            raw_val = row.get(name, "").strip()
            if not raw_val:
                return 0
            m = REV_TOKEN_RE.match(raw_val)
            if m:
                return int(m.group(1))
            m = REV_INLINE_RE.search(raw_val)
            return int(m.group(1)) if m else 0

        def _rev_set(name: str, row: dict[str, str] = row) -> set[int]:
            raw_val = row.get(name, "").strip()
            out: set[int] = set()
            for tok in re.split(r"[,\s]+", raw_val):
                tok = tok.strip()
                if not tok:
                    continue
                m = REV_TOKEN_RE.match(tok)
                if m:
                    out.add(int(m.group(1)))
                else:
                    m = REV_INLINE_RE.search(tok)
                    if m:
                        out.add(int(m.group(1)))
            return out

        terminal = row.get("终态", "").strip().lower()
        terminal_known = not terminal or terminal in ("superseded", "withdrawn", "deferred")
        records[dec_id] = {
            "id": dec_id,
            "rev": _rev_value("修订") or 1,
            "withdrawn": _rev_set("撤回"),
            "equivalent_to": _rev_set("等价"),
            "terminal": terminal,
            "terminal_known": terminal_known,
            "status": row.get("状态", "").strip(),
            "text": " ".join(row.values()),
            "row": row,
        }
    return records


def load_ledger(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    path = root / "docs" / "PENDING-DECISIONS.md"
    if not path.is_file():
        return {}
    return parse_ledger(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# decision_deps parsing (downstream frontmatter)
# --------------------------------------------------------------------------- #
def parse_dep_token(token: str) -> dict[str, Any]:
    """Parse one ``decision_deps`` token into a structured dependency."""
    m = DEP_TOKEN_RE.match(token.strip())
    if not m:
        return {"raw": token.strip(), "valid": False}
    dec_id, rest = m.group(1), m.group(2)
    dep: dict[str, Any] = {"id": dec_id, "valid": True}
    # Split the rest on '#' so an invariant or stale metadata can follow.
    parts = rest.split("#")
    primary = parts[0]
    rev_m = REV_TOKEN_RE.match(primary)
    if rev_m:
        dep["rev"] = int(rev_m.group(1))
    elif primary.startswith("invariant="):
        invariant = primary[len("invariant="):]
        if not invariant.strip():
            return {"raw": token.strip(), "valid": False, "reason": "不变式为空"}
        dep["invariant"] = invariant
    for part in parts[1:]:
        if part.startswith("stale_reason="):
            dep["stale_reason"] = part[len("stale_reason="):]
        elif part.startswith("review_date="):
            dep["review_date"] = part[len("review_date="):]
    return dep


def extract_decision_deps(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    """Read ``decision_deps`` from a parsed frontmatter mapping.

    Accepts the inline-list string form (``[a, b]``) produced by the gate's flat parser.
    """
    raw = frontmatter.get("decision_deps")
    if raw is None:
        return []
    if isinstance(raw, str):
        # inline list already split by the gate parser may arrive as a single string of
        # comma-separated tokens; split defensively.
        tokens = [t.strip() for t in raw.strip("[]").split(",") if t.strip()]
    elif isinstance(raw, list):
        tokens = [str(t).strip() for t in raw if str(t).strip()]
    else:
        return []
    deps = [parse_dep_token(t) for t in tokens]
    return deps


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #
def _today() -> date:
    return datetime.now(timezone.utc).date()


def _review_date_valid(review_date: str | None) -> bool:
    if not review_date:
        return False
    try:
        return datetime.strptime(review_date, "%Y-%m-%d").date() >= _today()
    except ValueError:
        return False


def evaluate_dep(dep: dict[str, Any], decision: dict[str, Any] | None) -> str | None:
    """Return an error string if the dependency is stale/red, else None (green).

    Implements G7-AC-02 (withdrawn revision → red), G7-AC-03 (equivalent_to → green),
    G7-AC-04 (stale_reason + review_date → green; bare exempt → red), G7-AC-05
    (invariant still present → green).
    """
    if not dep.get("valid"):
        reason = dep.get("reason")
        suffix = f"（{reason}）" if reason else ""
        return f"decision_deps 含不可解析的条目 {dep.get('raw', '')!r}{suffix}"
    dec_id = dep["id"]
    if decision is None:
        return f"依赖未立账的决策 {dec_id}（该 DEC 编号不存在于台账）"
    if not decision.get("terminal_known", True):
        return (
            f"决策 {dec_id} 的终态词 {decision['terminal']!r} 无法识别"
            "（须 superseded / withdrawn / deferred）"
        )

    # A terminal decision is dead even when the downstream pins its *current* revision or an
    # invariant: the number stays citable, but it is no longer an actionable dependency. A
    # registered stale_reason + future review date is the only tolerated exemption (G7-AC-04).
    if decision["terminal"] in ("superseded", "withdrawn", "deferred"):
        if dep.get("stale_reason") and _review_date_valid(dep.get("review_date")):
            return None
        return f"依赖 {dec_id} 但该决策已终态（{decision['terminal']}），须更新或登记豁免"

    if dep.get("invariant") is not None:
        if dep["invariant"] in decision["text"]:
            return None
        return f"依赖 {dec_id} 钉定的不变式「{dep['invariant']}」已不在决策正文中（当前修订 r{decision['rev']}）"

    pinned = dep.get("rev")
    if pinned is None:
        return f"依赖 {dec_id} 既未钉定修订也未钉定不变式"
    current = decision["rev"]
    if pinned == current:
        if pinned in decision["withdrawn"]:
            return f"依赖 {dec_id} 钉定 r{pinned}，但该修订已被撤回（当前 r{current}）"
        return None
    if pinned > current:
        return f"依赖 {dec_id} 钉定了不存在的修订 r{pinned}（当前仅到 r{current}）"
    # pinned < current
    # Exemption override (G7-AC-04): a registered stale_reason + still-valid review date
    # keeps any lagging pin green — including a withdrawn-revision pin. Without it the pin is
    # judged on its own merits below: `#exempt=true` is not a legal token and is ignored.
    if dep.get("stale_reason") and _review_date_valid(dep.get("review_date")):
        return None  # tolerated stale pin
    if pinned in decision["withdrawn"]:
        return (
            f"依赖 {dec_id} 钉定 r{pinned}，但该修订已被撤回（当前 r{current}）"
            f"——须更新钉定或登记 stale_reason + 复核日期"
        )
    if pinned in decision["equivalent_to"]:
        return None  # current revision is equivalent to the pinned one (G7-AC-03)
    return (
        f"依赖 {dec_id} 钉定 r{pinned} 已过期（当前 r{current}，且既非撤回等价也非已登记豁免）"
    )


def check(root: Path = ROOT) -> list[str]:
    """Scan the repo for ``decision_deps`` and report only truly affected documents."""
    ledger = load_ledger(root)
    ledger_path = root / "docs" / "PENDING-DECISIONS.md"
    errors: list[str] = []
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("|") and "DEC编号" in line:
                for column in ("DEC编号", "修订", "撤回", "等价", "终态"):
                    if column not in line:
                        errors.append(f"台账表头缺列 {column!r}（parse_ledger 会静默用默认修订）")
                break
    # Append-only ledger: an id that was issued once must remain citable. issued.txt is the
    # machine-side witness; deleting a row from the Markdown ledger is then a red, not a
    # silent loss (P2-3).
    issued_path = root / "docs" / "decisions" / "issued.txt"
    if issued_path.is_file():
        for line in issued_path.read_text(encoding="utf-8").splitlines():
            dec_id = line.strip()
            if not dec_id or dec_id.startswith("#"):
                continue
            if dec_id not in ledger:
                errors.append(f"已发放编号 {dec_id} 从台账消失（issued.txt 只追加，不得移除）")
    ledger_text = ledger_path.read_text(encoding="utf-8") if ledger_path.is_file() else ""
    if "DEC-" in ledger_text and not ledger:
        errors.append("台账含 DEC 编号但解析为 0 条（表头缺失或格式无法识别）")
    if "DEC-" in ledger_text and not issued_path.is_file():
        errors.append("台账含 DEC 编号但 docs/decisions/issued.txt 缺失（发放见证不可省）")
    if issued_path.is_file():
        issued_ids = {
            line.strip()
            for line in issued_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        for dec_id in ledger:
            if dec_id not in issued_ids:
                errors.append(f"台账编号 {dec_id} 未登记进 issued.txt（新编号须追加见证）")
    # Walk Markdown documents; the ledger file itself carries no decision_deps.
    for path in sorted(root.rglob("*.md")):
        if path.resolve() == ledger_path.resolve():
            continue
        relative_parts = path.relative_to(root).parts
        if "packaging" in relative_parts and "runtime" in relative_parts:
            continue  # generated byte-for-byte copy; the source document is the authority
        if any(part.startswith(".") for part in relative_parts):
            continue  # .git / .venv / .workbuddy-ai and other hidden tool directories
        rel = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "decision_deps" not in text:
            continue
        fm = _parse_flat_frontmatter(text)
        deps = extract_decision_deps(fm)
        if "decision_deps" in fm and not deps:
            errors.append(
                f"{rel}: decision_deps 存在但解析不出任何条目"
                "（须为行内列表，合法形态 DEC-YYYY-NNN#rN 或 #invariant=原文）"
            )
            continue
        if not deps:
            continue
        for dep in deps:
            verdict = evaluate_dep(dep, ledger.get(dep.get("id", "")))
            if verdict:
                errors.append(f"{rel}: {verdict}")
    return errors


def _parse_flat_frontmatter(text: str) -> dict[str, Any]:
    """Minimal frontmatter reader that tolerates the flat ``decision_deps`` inline list.

    The gate's own parser rejects nested mapping lines; downstream docs therefore encode
    decision_deps as a flat inline list (no nested objects), which this reader handles. We
    keep this local so we never depend on the gate's stricter parser for the dependency scan.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}
    data: dict[str, Any] = {}
    list_key: str | None = None
    for raw in lines[1:end]:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - "):
            if list_key:
                data[list_key].append(line[4:].strip())
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value == "":
            data[key] = []
            list_key = key
        else:
            list_key = None
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                data[key] = [t.strip() for t in inner.split(",") if t.strip()]
            else:
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                    value = value[1:-1]
                data[key] = value
    return data


# --------------------------------------------------------------------------- #
# view
# --------------------------------------------------------------------------- #
def view(root: Path = ROOT) -> str:
    """Render the pending view: decisions that are still active (no terminal state)."""
    ledger = load_ledger(root)
    active = [
        rec
        for rec in ledger.values()
        if not rec["terminal"]
    ]
    active.sort(key=lambda r: r["id"])
    out: list[str] = []
    out.append("# 决策待办视图（由 decisions.py view 生成，禁止手改）")
    out.append("")
    out.append("> 本视图只列出尚未进入终态（superseded / withdrawn / deferred）的决策；")
    out.append("> 终态条目保留在台账 `docs/PENDING-DECISIONS.md` 中，按「只追加、永不移出」规则不移除。")
    out.append("")
    if not active:
        out.append("_当前无未决决策。_")
        out.append("")
        return "\n".join(out)
    out.append("| DEC 编号 | 修订 | 状态 | 待决问题（摘要） |")
    out.append("| --- | --- | --- | --- |")
    for rec in active:
        problem = rec["row"].get("待决问题", "").replace("\n", " ")
        problem = (problem[:40] + "…") if len(problem) > 41 else problem
        out.append(f"| {rec['id']} | r{rec['rev']} | {rec['status']} | {problem} |")
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# index (generated file with digest)
# --------------------------------------------------------------------------- #
def render_index_body(root: Path = ROOT) -> str:
    ledger = load_ledger(root)
    out: list[str] = []
    out.append("# 决策台账索引（由 decisions.py index --write 生成，禁止手改）")
    out.append("")
    out.append("> 生成文件。任何手工修改都会使摘要校验失败（门随即转红）。重新生成：")
    out.append("> `python3 tools/lab/decisions.py index --write`。")
    out.append("")
    out.append("| DEC 编号 | 当前修订 | 终态 | 撤回 | 等价 | 状态 |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for dec_id in sorted(ledger):
        rec = ledger[dec_id]
        withdrawn = ",".join(f"r{r}" for r in sorted(rec["withdrawn"])) or "—"
        equiv = ",".join(f"r{r}" for r in sorted(rec["equivalent_to"])) or "—"
        out.append(
            f"| {dec_id} | r{rec['rev']} | {rec['terminal'] or '—'} | {withdrawn} | {equiv} | {rec['status']} |"
        )
    out.append("")
    return "\n".join(out)


def render_index(root: Path = ROOT) -> str:
    """Full index content including the digest footer (deterministic)."""
    body = render_index_body(root)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"{body}<!-- decision-index-digest: {digest} -->\n"


def write_index(root: Path = ROOT) -> Path:
    path = DECISIONS_INDEX if root == ROOT else root / "docs" / "decisions" / "index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_index(root), encoding="utf-8")
    return path


def verify_index(root: Path = ROOT) -> list[str]:
    """Validate the committed index.md against what the generator would produce."""
    path = DECISIONS_INDEX if root == ROOT else root / "docs" / "decisions" / "index.md"
    if not path.is_file():
        return [f"{path.relative_to(root)}: 决策索引缺失（运行 decisions.py index --write 生成）"]
    content = path.read_text(encoding="utf-8")
    canonical = render_index(root)
    if content != canonical:
        return [
            (
                f"{path.relative_to(root)}: 决策索引是生成文件，禁止手改——内容与生成器不符"
                f"（运行 decisions.py index --write 重新生成）"
            )
        ]
    return []


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    command = args[0] if args else "check"
    rest = args[1:]

    root = ROOT
    if "--root" in rest:
        idx = rest.index("--root")
        root = Path(rest[idx + 1]).resolve()
        rest = rest[:idx] + rest[idx + 2:]

    if command == "view":
        sys.stdout.write(view(root))
        sys.stdout.write("\n")
        return 0
    if command == "check":
        errors = check(root)
        if errors:
            for e in errors:
                print(f"STALE {e}")
            return 1
        print("OK decisions: 无过期决策依赖")
        return 0
    if command == "index":
        if "--write" in rest:
            path = write_index(root)
            print(f"wrote {path.relative_to(root)}")
            return 0
        if "--verify" in rest:
            errors = verify_index(root)
            for e in errors:
                print(f"FAIL {e}")
            return 1 if errors else 0
        # default: print canonical content to stdout (used by the gate compare)
        sys.stdout.write(render_index(root))
        return 0
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
