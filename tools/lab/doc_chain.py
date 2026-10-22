#!/usr/bin/env python3
"""Deterministic cross-closure linter for feature document chains.

Born from the 2026-09-20 quality failure: a full proposal -> spec -> design -> plan chain
was generated where every stage "existed" but design carried no API contracts, no failure
sequence diagrams, no state-machine diagrams, no wireframes, and plans carried no file
targets — and nothing failed, because no check existed. This tool is that check.

Scope and assumptions (honest): this linter checks the doc-chain conventions shared by this
repository's contract (skills/agentflow/references/document-chain.md) and the business
repositories that adopt it — the feature-directory layout (README + proposal/ + spec/ +
design/{be,fe}/ + plan/{be,fe}/). It is a FLOOR check, not a quality verdict: passing means
the structural density bar is met, not that the content is correct. Content correctness
still belongs to the review gates.

Checks:
  C1  structure        every stage directory holds at least one real document (no .gitkeep only),
                       unless the batch README's 段落映射 table names a landing for that stage
                       (non-empty and not 「—」)
  C2  entry gates      README carries the requirement-review and design-review gate entries
  C3  spec re-audit    a spec file contains the re-audit checklist; no blocking row left open (☐)
  C4  design/be figures  >=1 sequenceDiagram WITH an alt failure branch, >=1 flowchart,
                       >=1 erDiagram or stateDiagram
  C5  contract closure every interface id declared in design/be's contract table appears
                       in design/fe (its exception matrix or elsewhere)
  C6  fe exception matrix  design/fe has a table whose header covers success AND failure
  C7  fe wireframes    >=2 text wireframes (box-drawing frames) in design/fe
  C8  design/fe figures  >=1 flowchart, >=1 sequenceDiagram, >=1 stateDiagram
                       C4/C5/C8 apply to a role when spec/<role>/ or design/<role>/ holds any .md
  C9  plan grounding   every task row (table whose first header is ID) has a valid T/FT id, a
                       status from the fixed enum — the labelled form (「☑ 已完成」) or the bare
                       glyph (☑); a bare 「—」 counts as 本期不做, matching gate/plan.py — and a
                       code location that is a repository path (every path token must exist,
                       resolved against the README's declared 落点基准, repo root by default)
                       or carries 「待核实」 in the location cell; every plan file has a
                       「分支策略」 section; design's V-n open items are referenced by some plan
  C10 mermaid fences   every ```mermaid block is closed
  C11 structure template  chains whose README declares the agentflow marker carry the fixed
                       design headings (先说结论 / 影响面评估 / 评审前自检 / data-testid)
  C12 stale references  a stage-document line claims a target is still 待产出-style while a
                       markdown link or backtick code path on that line already resolves on
                       disk — the claim rotted
  C13 session role words  stage documents carry session-bound process words (supervisor /
                       coordinator case-insensitive; literal TD 开放问题 / 本轮评审 /
                       本次会话 / 本轮会话 / 本会话) — replace with a concrete role name or
                       delete; skipped only on the files listed in C13_EXEMPT_FILES
  C14 bare code subjects  a stage document uses a single uppercase letter as a standing prose
                       subject with the 桶 classifier (「A 桶」「D 桶」, spaced or not) away from
                       its definition site — codes pair with the plain word (白话（代号）) in
                       prose; the schema-word form (「prepared 会话」) is C15 and is deliberately
                       clause-governed, not machine-checked (see the note at CODE_SUBJECT_RE)
  C15 ledger-index     opt-in (file carries 「agentflow 问题台账」): a ledger row may not carry a
                       status word (仍存在/已修复/…) unless it links an ISS; every ISS link in a
                       row must resolve to docs/issues/<id>.md. Status lives only in the record.
  C16 decision-record  opt-in (file carries 「agentflow 决策记录」): every decision-record table
                       (header ⊇ 来源/待决问题/现状核验/推荐/关闭条件/优先级/影响范围/自动决策)
                       must be machine-judgable — source resolves or is external, ≥2 options with
                       cost, 核验 has date+command, 关闭条件 non-empty, P0–P3, 影响范围 lists
                       concrete modules/projects, 自动决策 Y only on P3 with a rule recorded.
  C17 staleness        opt-in (same marker as C16): an in-repo path referenced by a decision that
                       was committed after its 核验 date is stale and must be re-verified. External
                       references are not time-checked (declared per repo scope).
  C18 ownership        opt-in (batch README carries 「agentflow 决策归属」): every open issue must
                       appear in a batch 承接表 or carry disposition deferred/not-doing.
  C19 qa acceptance    spec/ holds any document but spec/qa/ holds no acceptance document
                       (declaration-gated exemption: README says 「qa 不适用」/「无 qa 轨」)
  C20 埋点贯通        opt-in (README 埋点 row declares 本期新增): proposal carries a 埋点决策
                       heading, spec carries a 埋点 heading, design/fe carries a 埋点 heading —
                       the three-place tracking contract must exist before implementation
  C21 ui-track prototype  opt-in (README UI 轨 row declares 已启用): a real prototype (≥64-byte
                       .html named *prototype*) or ≥2 design/fe wireframes must exist
  C22 goal-traceability  opt-in (batch README carries 「agentflow 目标承接」): the batch README's
                       承接表 (目标/spec 承接/plan 任务/状态) closes the chain both ways — every
                       G-number declared in proposal/ appears in the table and vice versa, cited
                       modules and AC ids exist in spec/, cited task ids exist in the plan board,
                       every completed or blocked task row is cited by some row, and the table's
                       status agrees with the board's glyphs (a README claiming done over ☐ rows
                       fails the same day)
  C23 evidence-presence  for rows marked ☑ 已完成 in the batch's plan/ files: the evidence cell
                       must hold one of four re-checkable carriers — a repo path that exists, a
                       repo-qualified `repo@rev:path`, a commit sha git can resolve, or an
                       explicit `N/A: reason`. A /tmp path that has been cleaned away is not a
                       carrier; no git means a sha claim fails closed rather than passing silently

Usage:
    python3 tools/lab/doc_chain.py [--root <repo-dir>] <feature-dir>
    python3 tools/lab/doc_chain.py --file <single-markdown-path>
    python3 tools/lab/doc_chain.py --repo <repo-dir>
    python3 tools/lab/doc_chain.py --self-test

Exit code 0 = all checks pass; 1 = findings; 2 = usage error. --file runs only the text-form
checks (C12/C13/C14) against one standalone markdown file — a session deliverable handed to
the user (analysis report, status report) has no feature-directory shape, so every structure
check (C1–C11) is skipped by design; --file and a positional feature dir are mutually exclusive.
"""

from __future__ import annotations

import datetime as _dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

MERMAID_KINDS = ("sequenceDiagram", "flowchart", "erDiagram", "stateDiagram")
BOX_CHARS = ("┌", "└", "├", "│")
# Repository root, used to resolve C9 code-location paths. Overridable with --root (self-test
# fixtures and validate.py's live pass pass their own root explicitly).
REPO_ROOT = Path(__file__).resolve().parents[2]

# C12 stale-time reference: claim words whose truth depends on the world, not the text — a
# line claiming one of these while pointing at a target that already exists on disk (markdown
# link OR backtick code path — the 2026-09-18 corpus used the backtick form) has rotted.
STALE_WORDS = ("待产出", "尚未产出", "待补充", "待生成")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+\.md)\)")
BT_PATH_RE = re.compile(r"`([^`\n]+\.md)`")

# C13 session role words: a formal document must be readable without the session that wrote
# it. Case-insensitive process-role names plus the literal session-bound phrases seen in the
# 2026-09-21 corpus (TD 开放问题 etc.).
ROLE_WORD_RE = re.compile(r"supervisor|coordinator", re.IGNORECASE)
ROLE_PHRASES = ("TD 开放问题", "本轮评审", "本次会话", "本轮会话", "本会话")

# C13 exemptions are per FILE, never per prefix. A listed file either defines the process role
# names it uses (the defined term is its own subject) or is an immutable review record (verbatim
# history; 硬边界 8 forbids rewriting it). Every other file is checked. Adding an entry needs the
# same reason; a new file that merely contains the words does not qualify.
C13_EXEMPT_FILES: dict[str, str] = {
    # role files: each defines the role it describes; Supervisor is the defined delegator
    "agents/backend-engineer.md": "角色定义",
    "agents/bug-fixer.md": "角色定义",
    "agents/bug-investigator.md": "角色定义",
    "agents/bug-recorder.md": "角色定义",
    "agents/candidate-engineer.md": "角色定义",
    "agents/frontend-engineer.md": "角色定义",
    "agents/plan-architect.md": "角色定义",
    "agents/release-governor.md": "角色定义",
    "agents/reviewer.md": "角色定义；列举被禁止的会话词本身",
    "agents/technical-director.md": "角色定义",
    "agents/test-executor.md": "角色定义",
    "agents/test-planner.md": "角色定义",
    # shipped skill text: defines the method's roles, and the clause that forbids the words
    "skills/agentflow/SKILL.md": "方法定义（角色与流程）",
    "skills/agentflow/references/contracts.md": "方法定义（角色契约）",
    "skills/agentflow/references/roles.md": "方法定义（角色表）",
    "skills/agentflow/references/document-chain.md": "方法定义；条款本身引用被禁止的词",
    "skills/agentflow/references/test-records.md": "方法定义（角色交接）",
    "skills/improve/SKILL.md": "方法定义（改进环角色）",
    "reviews/README.md": "方法定义（评审流程）",
    # product design: the glossary entry 「Supervisor = 主会话」 and the role table
    "docs/product/design/product-design.md": "术语定义表",
    # immutable review records and their snapshots
    "reviews/agentflow-product-chain/review-2026-10-10-001.md": "评审记录（不可改写）",
    "reviews/agentflow-product-chain/archive/2026-10-10-001/proposal.md": "评审快照（不可改写）",
    "reviews/agentflow-product-chain/archive/2026-10-10-001/method-spec.md": "评审快照（不可改写）",
    "reviews/agentflow-product-chain/archive/2026-10-10-001/acceptance-matrix.md": "评审快照（不可改写）",
    "reviews/infinite-canvas-office-agent-plan/review-2026-09-19-001.md": "评审记录（不可改写）",
}

# A planned-but-absent component name is not a session word: 「Execution Coordinator」 names a
# future role in the workflow (PLAN-PRODUCT-001 lists it as 本期不做), resolved by the sentence
# around it, not by the session. Stripped before matching so the bare-word rule keeps its teeth.
ROLE_WORD_EXEMPT_PHRASES = ("Execution Coordinator", "execution-coordinator")

# C12/C13/C14 scan stage documents only: proposal/spec/design/plan. The README progress log and
# .gitkeep placeholders are out of scope (progress-log wording is not document wording).
STAGE_DIRS = ("proposal", "spec", "design", "plan")

# C9 plan task rows: the fixed status enum and ID shape (docs/features/README.md 计划形态).
TASK_STATUS_ENUM = ("☐ 未开始", "◐ 进行中", "☑ 已完成", "⚠ 阻塞", "— 本期不做")
# Bare-glyph dialect (2026-10-21 gate change, user-authorized): the labelled form and the bare
# glyph are both legal — gate/plan.py already reads the status cell by its first character and
# maps the bare marks, so C9 was the stricter of the two gates and the mismatch turned every
# bare-glyph plan table into noise (160 findings on one cross-repo corpus). A bare 「—」 counts
# as 本期不做, consistent with PLAN_TASK_STATUS_MARKS.
TASK_STATUS_BARE = frozenset({"☐", "◐", "☑", "⚠", "—"})

# README 落点基准 declaration: the directory C9 code-location paths resolve against. Values:
# 「.」/「主实施仓根」/「仓根」/「目标仓根」 → repo root (default when undeclared);
# 「本批次目录」 → the feature dir; anything else → a repo-root-relative directory that must
# exist. An unfilled template placeholder (leading 「<」) is not a declaration.
LOCATION_BASE_RE = re.compile(r"落点基准[：:]\s*([^\n]+)")
UI_TRACK_RE = re.compile(r"UI 轨[：:]\s*([^\n]+)")
TRACKING_RE = re.compile(r"埋点[：:]\s*([^\n]+)")
QA_EXEMPT_RE = re.compile(r"qa 不适用|无 qa 轨")
TASK_ID_RE = re.compile(r"^(?:FT?\d{2}|T\d{1,2})$")
PLACEHOLDER = "待核实"
# 「分支策略」 section: a heading at level 2-4, optionally numbered ("## 分支策略", "### 0. 分支策略").
BRANCH_HEADING_RE = re.compile(r"^#{2,4}\s+(?:\d+\.\s*)?分支策略(?:\s|$)", re.MULTILINE)
SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
BARE_PATH_RE = re.compile(
    r"(?<![\w./-])[\w.\-]+(?:/[\w.\-]+)*\.(?:go|ts|tsx|vue|sql|py|md|json|sh|html|yml|yaml|toml|txt|js|css)\b"
)

# C14 bare code subjects: single uppercase letter + optional (half/full-width) space + 桶, the
# 2026-09-22 report corpus form — the report defined every bucket in its §1 glossary yet kept
# 「A 桶/D 桶/G 桶」 as bare prose subjects (「D 桶积分中断」「A 桶：36 会话」). Tight by design;
# the two near-misses in the wild both need a constraint below: 「IP 桶」(rate-limit bucket) is
# saved by the no-ASCII-alnum lookbehind, 「office 桶」 by uppercase-only. 组/档 stay out — both
# are productive ordinary classifiers (A 组对照组 / A 档价位) with real false-positive surface.
# Exempt, matching the clause's sanctioned sites (document-chain.md 表达纪律（术语）): table rows
# (口径表/图例 are the definition site — bare codes inside body tables stay clause-governed, the
# accepted false-negative direction for a floor linter), code fences and inline code spans, and
# the two paired forms — the code inside （…） (白话（代号）) or directly glossed by （…）
# (代号（白话）). A prose legend like 「A 桶=交付」 is still reported (tolerance; the compliant
# legend shape is the paired form).
CODE_SUBJECT_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z])[ \u3000]?桶")

# 模式词分域（散文里的 schema 词 — 「prepared 会话」「单次 Run 积分」）刻意**不**实现为机器检查。
# 注意编号歧义：本文件的检查号 C15 指的是 ledger-index（台账行不得自带状态词），与这里说的
# 模式词分域不是同一条，两者只在「靠条款而非靠正则」这一点上同法。2026-10-23 走查发现同一个
# C15 在本文件里被两种含义使用，故此处改名并保留说明。原闭集启发式（prepared/pending/
# running/failed/… + 中文，且不在代码语境）在一条真实被评审过的链上验证过，结果洪水：
# state→visual mapping rows (「queued 灰 / running 蓝 / succeeded 绿」) are the
# legend-class site the clause sanctions, while 「running 中禁发」「failed 可重试」 one line
# away is the defect — a line-local heuristic cannot tell them apart without punishing one
# side. The form stays governed by the clause text (document-chain.md 模式词分域), the
# pre-write pass, and the reviewer's per-occurrence citation; self-test case 34 pins the
# boundary (schema-word prose exits 0).



def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def fenced_lines(text: str) -> set[int]:
    """Line numbers inside or on a ``` fence (the toggle lines themselves included)."""
    inside, out = False, set()
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            inside = not inside
            out.add(i)
        elif inside:
            out.add(i)
    return out


def strip_inline_code(line: str) -> str:
    """Drop `...` spans (even segments after a backtick split); unbalanced tail reads as code."""
    return "".join(line.split("`")[0::2])


def inside_parens(s: str, idx: int) -> bool:
    """True when s[idx] sits inside a （…）/ (…) span of its own line (depth counting, no nesting)."""
    depth = 0
    for ch in s[:idx]:
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            depth = max(0, depth - 1)
    return depth > 0


def c13_checked(label: str) -> bool:
    """False only for the files listed in C13_EXEMPT_FILES, matched on the path's tail.

    Tail matching lets --file (the path as given, possibly absolute) and the feature-chain pass
    (labels relative to the feature dir) resolve the same listing.
    """
    posix = label.replace("\\", "/")
    return not any(posix == name or posix.endswith("/" + name) for name in C13_EXEMPT_FILES)


def text_form_findings(label: str, text: str, resolve_roots: list[Path]) -> list[str]:
    """C12/C13/C14 — the text-form checks that need no feature-directory shape.

    Shared by the feature-chain pass (label = repo-relative path; link targets resolve against
    the document's directory and the feature root) and --file mode (label = the path as given;
    targets resolve against the file's own directory).
    """
    errors: list[str] = []
    fences = fenced_lines(text)
    check_c13 = c13_checked(label)
    for i, line in enumerate(text.splitlines(), 1):
        # C12 stale-time reference: the line claims a target is still pending while the
        # markdown link OR backtick code path on the same line already resolves on disk —
        # delete the claim or re-point it. Both pointee forms share one resolution pass,
        # deduped per line.
        if any(w in line for w in STALE_WORDS):
            seen: set[str] = set()
            for target in MD_LINK_RE.findall(line) + BT_PATH_RE.findall(line):
                t = target.split("#", 1)[0].split("?", 1)[0].strip()
                if not t or t in seen or t.startswith(("/", "http:", "https:", "mailto:")):
                    continue
                seen.add(t)
                if any((root / t).is_file() for root in resolve_roots):
                    errors.append(
                        f"C12 时效性引用: {label}:{i} 声称待产出但目标已存在: {t}"
                    )
        # C13 session role words: replace with the concrete role name, or delete the clause so
        # the body stands on its own. Skipped whole on the method-self-description surfaces —
        # there the words are defined terms or quoted examples (reviewer.md lists 「supervisor、
        # TD、本轮、本次会话一类」 as the very thing the clause forbids), and no line-local rule
        # can tell a mention from a use.
        if check_c13:
            role_line = line
            for phrase in ROLE_WORD_EXEMPT_PHRASES:
                role_line = re.sub(re.escape(phrase), " ", role_line, flags=re.IGNORECASE)
            hits = [w for w in ROLE_PHRASES if w in line] + ROLE_WORD_RE.findall(role_line)
            for w in sorted(set(hits)):
                errors.append(f"C13 会话角色词: {label}:{i} {w}")
        # C14 bare code subjects: codes pair with the plain word in prose; the definition
        # site, code spans/fences, and the two paired forms are exempt (see CODE_SUBJECT_RE).
        if i not in fences and not line.lstrip().startswith("|"):
            prose = strip_inline_code(line)
            for m in CODE_SUBJECT_RE.finditer(prose):
                glossed = prose[m.end():].lstrip(" \u3000").startswith(("（", "("))
                if glossed or inside_parens(prose, m.start()):
                    continue
                errors.append(f"C14 代号裸用: {label}:{i} {m.group(0)}")
    return errors


def mermaid_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    lines = text.splitlines()
    inside = False
    buf: list[str] = []
    for line in lines:
        if line.strip() == "```mermaid":
            inside, buf = True, []
        elif inside and line.strip() == "```":
            inside = False
            blocks.append("\n".join(buf))
        elif inside:
            buf.append(line)
    return blocks  # unclosed fences simply never land here; C10 counts them separately


def mermaid_kinds(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for block in mermaid_blocks(text):
        for kind in MERMAID_KINDS:
            if kind in block:
                out.setdefault(kind, []).append(block)
                break
    return out


# A prototype HTML file must carry at least this many bytes to exempt the C7 wireframe floor.
# A name is not a prototype; a placeholder file must not be able to buy an exemption.
PROTOTYPE_MIN_BYTES = 64


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Pipe tables as (header cells, body rows): a pipe line followed by a separator line."""
    lines = text.splitlines()
    out: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and "-" in lines[i + 1] and SEP_RE.match(lines[i + 1]):
            header = split_row(lines[i])
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            out.append((header, rows))
            i = j
        else:
            i += 1
    return out


def stage_landing(readme_text: str) -> dict[str, str]:
    """Batch README 段落映射: stage -> 落点 cell, read from any table with a 落点 column."""
    out: dict[str, str] = {}
    for header, rows in md_tables(readme_text):
        if "落点" not in header:
            continue
        col = header.index("落点")
        for row in rows:
            if not row:
                continue
            stage = row[0].strip("`* ").lower()
            if stage in STAGE_DIRS and col < len(row):
                out[stage] = row[col].strip()
    return out


def path_candidates(cell: str) -> set[str]:
    """Repository-path tokens in a cell: path-like code spans plus bare paths with a known suffix."""
    found: set[str] = set()
    for span in re.findall(r"`([^`\n]+)`", cell):
        s = span.strip()
        if re.fullmatch(r"[\w.\-]+(?:/[\w.\-]+)*/?", s) and ("/" in s or re.search(r"\.[A-Za-z]{1,5}$", s)):
            found.add(s)
    found.update(BARE_PATH_RE.findall(cell))
    return found


def body_text(text: str) -> str:
    """The text with fenced code blocks removed: an id inside a code sample is not prose."""
    fences = fenced_lines(text)
    return "\n".join(line for i, line in enumerate(text.splitlines(), 1) if i not in fences)


def _declared_base(value: str, repo_root: Path, feature_dir: Path) -> Path | None:
    """Resolve a README 落点基准 value to a directory, or None when undeclared/placeholder."""
    v = value.split("｜")[0].split("|")[0].strip()
    # 元信息常把多个字段写在同一行（`- UI 轨：未启用；落点基准：.（默认）；最后更新时间：…`）；
    # 捕获到行尾会把后半句当成目录名，把合法声明判成假红，所以先按分号截断。
    v = v.split("；")[0].split(";")[0].strip()
    if not v or v.startswith("<"):
        return None  # unfilled template placeholder is not a declaration
    v = re.sub(r"[（(][^）)]*[）)]\s*$", "", v).strip().rstrip("/")
    if v in ("本批次目录",):
        return feature_dir
    if v in (".", "主实施仓根", "仓根", "目标仓根"):
        return repo_root
    return repo_root / v


def location_base(readme_text: str, repo_root: Path, feature_dir: Path) -> tuple[Path, list[str]]:
    """C9 落点基准: the directory code-location paths resolve against, plus declaration errors."""
    errors: list[str] = []
    base = repo_root
    m = LOCATION_BASE_RE.search(readme_text)
    if m:
        declared = _declared_base(m.group(1), repo_root, feature_dir)
        if declared is not None and not declared.is_dir():
            errors.append(f"C9 落点基准: README 声明的落点基准 {m.group(1).strip()} "
                          f"在目标仓根下不存在（路径按声明的基准解析，基准目录必须真实在盘）")
        elif declared is not None:
            base = declared
    return base, errors


def plan_findings(label: str, text: str, repo_root: Path, loc_base: Path | None = None) -> list[str]:
    """C9 task-row grounding for one plan file: ID shape, status enum, code location."""
    errors: list[str] = []
    base = loc_base if loc_base is not None else repo_root

    def at(row: list[str], i: int) -> str:
        return row[i] if i < len(row) else ""

    for header, rows in md_tables(text):
        if not header or header[0] != "ID":
            continue
        if "代码落点" not in header or "状态" not in header:
            errors.append(f"C9 plan: {label} 任务表缺少「代码落点」或「状态」列")
            continue
        loc_i, status_i = header.index("代码落点"), header.index("状态")
        for row in rows:
            task_id = at(row, 0).strip("`* ")
            if not TASK_ID_RE.match(task_id):
                errors.append(
                    f"C9 plan 任务表: {label} ID 列非法「{task_id}」（须为 T/FT 编号，「待核实」不得占 ID 列）"
                )
                continue
            status = at(row, status_i)
            if not (any(status.startswith(s) for s in TASK_STATUS_ENUM) or status in TASK_STATUS_BARE):
                errors.append(f"C9 plan 状态: {label} {task_id} 状态「{status}」不在固定枚举内")
            if status.startswith("— 本期不做") or status == "—":
                continue
            loc = at(row, loc_i)
            if PLACEHOLDER in loc:
                continue
            cands = path_candidates(loc)
            if not cands:
                errors.append(f"C9 plan 落点: {label} {task_id} 代码落点无仓库内路径且无「待核实」标记")
                continue
            for cand in sorted(cands):
                if not (base / cand.rstrip("/")).exists():
                    errors.append(f"C9 plan 落点: {label} {task_id} 代码落点路径不存在: {cand}")
    return errors


def find_stage(files: list[Path], *parts: str | Path) -> list[Path]:
    """All non-gitkeep .md files under <feature>/<parts...> (recursively)."""
    base = Path(*parts)
    return [
        f
        for f in files
        if f.parent == base or base in f.parents
        if f.suffix == ".md" and f.name != ".gitkeep"
    ]


def lint(feature_dir: Path, repo_root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    if not feature_dir.is_dir():
        return [f"{feature_dir}: 目录不存在"]

    files = sorted(feature_dir.rglob("*"))
    md_files = [f for f in files if f.is_file() and f.suffix == ".md" and f.name != ".gitkeep"]
    readme = feature_dir / "README.md"
    all_text = {f: read(f) for f in md_files}

    # C1 structure — two exemptions the chain contract allows, both declaration-gated:
    #   * 轻量模式：无 spec/design 轨 in the README meta line narrows the stage set to
    #     proposal + plan. Until 2026-10-13 C1 demanded all four stage directories
    #     unconditionally, so every such batch failed the very linter the contract told it to
    #     run before declaring the chain done: the降级 path existed on paper only. The exemption
    #     is declaration-gated (the README must say so), never inferred from emptiness — and it
    #     narrows the stage requirement, it does not switch C1 off.
    #   * a stage directory may be empty when the README's 段落映射 table names a landing for it
    #     (non-empty and not 「—」); otherwise it must hold a real document.
    readme_text = all_text.get(readme, "")
    lightweight = bool(re.search(r"轻量模式[：:][^\n]*无\s*spec/design\s*轨", readme_text))
    required_stages = ("proposal", "plan") if lightweight else STAGE_DIRS
    landing = stage_landing(readme_text) if readme.is_file() else {}
    for stage in required_stages:
        stage_files = [f for f in md_files if stage in f.relative_to(feature_dir).parts]
        if stage_files:
            continue
        if landing.get(stage, "") not in ("", "—"):
            continue  # 段落映射豁免
        suffix = "（已声明轻量模式）" if lightweight else "，且 README 段落映射未写明落点"
        errors.append(f"C1 结构: {stage}/ 下没有任何有效文档（仅 .gitkeep 占位）{suffix}")
    if not readme.is_file():
        errors.append("C1 结构: 缺少 README.md 唯一入口")

    # C2 entry gates
    if readme.is_file():
        rtext = all_text.get(readme, "")
        for gate in ("需求评审", "技术方案评审"):
            if gate not in rtext:
                errors.append(f"C2 入口门禁: README 未声明「{gate}」门禁条目")

    # C3 spec re-audit + blocking closed
    spec_files = find_stage(md_files, feature_dir / "spec")
    audit_found = False
    for f in spec_files:
        text = all_text[f]
        if ("不合规项" in text) or ("反审" in text):
            audit_found = True
        for line in text.splitlines():
            if not (line.lstrip().startswith("|") and "阻塞" in line and "☐" in line):
                continue
            # The exemption is a status-cell claim, not a whole-line keyword. Until 2026-10-13
            # the check dropped any line containing 非阻塞 anywhere, so a row whose status cell
            # read 阻塞 but whose prose merely mentioned 非阻塞 was silently exempt — a false
            # negative the checker's own comment admitted and its self-test then pinned as
            # correct behaviour. Only a cell that starts with 非阻塞 exempts the row.
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if any(cell.startswith("非阻塞") for cell in cells):
                continue  # non-blocking rows may stay open pending review confirmation
            errors.append(f"C3 反审门: {f.relative_to(feature_dir)} 存在未关闭的阻塞项: {line.strip()[:80]}")
    if spec_files and not audit_found:
        errors.append("C3 反审门: spec/ 下没有任何文件包含「不合规项/反审」checklist")

    # C4/C5/C6/C7/C8 per-side design requirements
    be_files = find_stage(md_files, feature_dir / "design" / "be")
    fe_files = find_stage(md_files, feature_dir / "design" / "fe")
    # C4/C5/C8 apply to a role when spec/<role>/ or design/<role>/ holds any document. An empty
    # design/<role>/ therefore no longer skips the role's checks when the spec side has content.
    be_applies = bool(be_files or find_stage(md_files, feature_dir / "spec" / "be"))
    fe_applies = bool(fe_files or find_stage(md_files, feature_dir / "spec" / "fe"))
    be_text = "\n".join(all_text[f] for f in be_files) if be_files else ""
    fe_text = "\n".join(all_text[f] for f in fe_files) if fe_files else ""

    # Wireframe/prototype state is shared by C7 (fe track) and C21 (UI-track gate), so it is
    # computed once here regardless of whether the fe track applies.
    wireframes = [
        b
        for b in re.findall(r"```text\n(.*?)```", fe_text, re.DOTALL)
        if any(c in b for c in BOX_CHARS)
    ]
    has_prototype = any(
        x.is_file()
        and x.suffix == ".html"
        and "prototype" in str(x.relative_to(feature_dir)).lower()
        and x.stat().st_size >= PROTOTYPE_MIN_BYTES
        for x in files
    )

    if be_applies:
        kinds = mermaid_kinds(be_text)
        seq_with_alt = [b for b in kinds.get("sequenceDiagram", []) if re.search(r"^\s*alt\b", b, re.MULTILINE)]
        if not seq_with_alt:
            errors.append("C4 design/be: 缺少含失败分支（alt）的时序图")
        if "flowchart" not in kinds:
            errors.append("C4 design/be: 缺少架构/流程 flowchart")
        spec_kinds = mermaid_kinds("\n".join(all_text[f] for f in spec_files) if spec_files else "")
        if not (kinds.get("erDiagram") or kinds.get("stateDiagram")
                or spec_kinds.get("erDiagram") or spec_kinds.get("stateDiagram")):
            errors.append("C4 design/be: 缺少 ER 图或状态机图（design/be 或 spec）")
        if not re.search(r"\|\s*#?\s*接口.*\|.*请求字段.*响应字段|\|.*请求字段.*\|.*响应字段", be_text):
            errors.append("C4 design/be: 缺少字段级 API 契约表（请求字段/响应字段列表头）")
        # C5: ids declared in the CONTRACT TABLE's first column must appear in design/fe
        contract_ids: set[str] = set()
        # row pattern is strictly per-line: a `\s*$\n?` variant would bridge one blank
        # line and swallow the NEXT table (decision ids misread as contract ids).
        # accepted tolerance (review note): a table ending at EOF without a trailing
        # newline drops its last row's id here — false-negative direction, floor-safe
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", be_text, re.MULTILINE):
            header = table.splitlines()[0]
            if "请求字段" in header and "响应字段" in header:
                for row in table.splitlines()[2:]:
                    first = row.strip("|").split("|")[0].strip()
                    m = re.match(r"^([A-Za-z]{1,3}\d{1,3})\b", first)
                    if m:
                        contract_ids.add(m.group(1).upper())
        fe_body = "\n".join(body_text(all_text[f]) for f in fe_files)
        fe_ids = set(re.findall(r"\b([A-Za-z]{1,3}\d{1,3})\b", fe_body))
        # accepted tolerance (review note a): \b fails on CJK-adjacent ids (e.g. `A1的`),
        # which over-reports C5 — the safe direction for a floor linter
        fe_ids = {i.upper() for i in fe_ids}
        missing = sorted(contract_ids - fe_ids)
        if contract_ids and missing:
            errors.append(f"C5 契约闭合: design/be 契约表声明的接口 {missing} 未在 design/fe 出现（缺异常矩阵行或调用）")
    if fe_applies:
        kinds = mermaid_kinds(fe_text)
        for kind in ("flowchart", "sequenceDiagram", "stateDiagram"):
            if kind not in kinds:
                errors.append(f"C8 design/fe: 缺少 {kind}")
        # A prototype exempts the wireframe floor only if it is a prototype: until 2026-10-13 any
        # zero-byte file named *prototype*.html satisfied it, because the check tested the path
        # name and never looked at the bytes.
        if len(wireframes) < 2 and not has_prototype:
            errors.append(f"C7 design/fe: 工程线框不足 2 张（现 {len(wireframes)}）且无 prototype HTML 原型")
        matrix = False
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", fe_text, re.MULTILINE):
            rows = table.splitlines()
            header = rows[0]
            if (
                ("成功" in header or "正常" in header)
                and ("失败" in header or "异常" in header)
                and any(SEP_RE.match(row.strip()) is None for row in rows[1:])
            ):
                matrix = True  # a data row below the header separator: the matrix has content
                break
        if not matrix:
            errors.append("C6 design/fe: 缺少接口异常边界矩阵（表头需同时覆盖 成功 与 失败/异常，且至少一行数据）")

    # C19 qa acceptance (2026-10-21 gate change, user-authorized): a spec that carries any
    # content but no qa acceptance document is a chain that cannot be accepted. C1 only catches
    # an EMPTY stage directory — it is silent when spec/ holds be/fe or unstructured docs while
    # spec/qa is empty, which is exactly the half-gap the cross-repo review corpus fell into
    # (one batch: spec holds one unstructured doc, qa empty). Exemption is declaration-gated
    # (README says 「qa 不适用」/「无 qa 轨」), never inferred.
    if not lightweight and spec_files:
        qa_files = find_stage(md_files, feature_dir / "spec" / "qa")
        if not qa_files and not (readme.is_file() and QA_EXEMPT_RE.search(readme_text)):
            errors.append(
                "C19 qa 验收: spec/ 有内容而 spec/qa/ 下没有任何验收文档"
                "（README 声明「qa 不适用」或「无 qa 轨」可豁免）"
            )

    # C20 埋点贯通 / C21 ui 轨 (2026-10-21 gate change, user-authorized): opt-in via the README
    # 元信息 rows the feature template ships. An unfilled placeholder (leading 「<」) is not a
    # declaration and never fires, so legacy chains without those rows are unaffected.
    if readme.is_file():
        m_track = TRACKING_RE.search(readme_text)
        if m_track and m_track.group(1).strip().startswith("本期新增"):
            spec_text_all = "\n".join(all_text[f] for f in spec_files) if spec_files else ""
            proposal_files = find_stage(md_files, feature_dir / "proposal")
            proposal_text = "\n".join(all_text[f] for f in proposal_files) if proposal_files else ""
            if not re.search(r"^#{2,6} .*埋点决策", proposal_text, re.MULTILINE):
                errors.append("C20 埋点贯通: proposal 缺「埋点决策」节（提案不问要不要埋，落地自然跳过）")
            if not re.search(r"^#{2,6} .*埋点", spec_text_all, re.MULTILINE):
                errors.append("C20 埋点贯通: spec 缺埋点验收草案节（spec/fe §4）")
            if not re.search(r"^#{2,6} .*埋点", fe_text, re.MULTILINE):
                errors.append("C20 埋点贯通: design/fe 缺埋点事件契约节（§1.7）")
        m_ui = UI_TRACK_RE.search(readme_text)
        if (
            m_ui
            and m_ui.group(1).strip().startswith("已启用")
            and len(wireframes) < 2
            and not has_prototype
        ):
            errors.append(
                "C21 ui 轨: README 声明 UI 轨已启用，但既无可直开原型"
                "（prototype/*.html 且 ≥64 字节）也无 ≥2 张 design/fe 工程线框"
            )

    # C9 plan grounding
    plan_files = find_stage(md_files, feature_dir / "plan")
    plan_text = "\n".join(all_text[f] for f in plan_files) if plan_files else ""
    if plan_files:
        loc_base, base_errors = location_base(readme_text, repo_root, feature_dir)
        errors.extend(base_errors)
        for f in plan_files:
            rel = str(f.relative_to(feature_dir))
            errors.extend(plan_findings(rel, all_text[f], repo_root, loc_base))
            if not BRANCH_HEADING_RE.search(all_text[f]):
                errors.append(f"C9 plan: {rel} 未声明分支策略（需以「分支策略」为标题的节）")
        v_ids = set(re.findall(r"\bV-F?\d+\b", be_text + fe_text))
        for vid in sorted(v_ids):
            # no heading-anchored exemption: any V-id declared anywhere in design must be
            # referenced by some plan, or C9 fails (F2 fix — the old `### 1.3` split
            # silently disabled this check for designs numbered differently)
            if vid not in plan_text:
                errors.append(f"C9 待核实闭合: design 声明的 {vid} 未被任何 plan 引用")
        for f in plan_files:
            for line in all_text[f].splitlines():
                if line.lstrip().startswith("|") and "⚠ 阻塞" in line and "☐" in line:
                    errors.append(f"C9 plan: {f.relative_to(feature_dir)} 存在未回写证据的阻塞任务行")

    # C11 template structure (marker-gated): chains declaring the agentflow doc-chain
    # marker in README must carry the fixed design headings (heading literals, like the
    # records contract) — prose skeletons alone allow generation drift.
    if readme.is_file() and "agentflow 文档链方法生成" in all_text.get(readme, ""):
        be_heads = "\n".join(all_text[f] for f in be_files) if be_files else ""
        fe_heads = "\n".join(all_text[f] for f in fe_files) if fe_files else ""
        import re as _re
        if not _re.search(r"^##+ .*(先说结论|关键决策速览|结论先行)", be_heads, _re.MULTILINE):
            errors.append("C11 结构模板: design/be 缺固定标题（先说结论/关键决策速览）")
        if "影响面评估" not in be_heads:
            errors.append("C11 结构模板: design/be 缺「影响面评估」章")
        for fname, head in (("design/be", be_heads), ("design/fe", fe_heads)):
            if "评审前自检" not in head:
                errors.append(f"C11 结构模板: {fname} 缺「评审前自检」章")
        if fe_files and "data-testid" not in fe_heads:
            errors.append("C11 结构模板: design/fe 缺 data-testid 可测性清单")

    # C12/C13/C14 chain-closure pass (machine-checkable part of closure gate 6): a stage document
    # must stay true over time, readable without the session that wrote it, and free of bare code
    # subjects away from their definition site.
    stage_files = sorted(
        {f for stage in STAGE_DIRS for f in find_stage(md_files, feature_dir / stage)}
    )
    for f in stage_files:
        rel = str(f.relative_to(feature_dir))
        errors.extend(text_form_findings(rel, all_text[f], [f.parent, feature_dir]))

    # C10 mermaid fence balance
    for f in md_files:
        text = all_text[f]
        opened = sum(1 for line in text.splitlines() if line.strip() == "```mermaid")
        blocks = len(mermaid_blocks(text))
        if opened != blocks:
            errors.append(f"C10 mermaid: {f.relative_to(feature_dir)} 有 {opened} 个 mermaid 围栏但仅 {blocks} 个闭合")

    # C22/C23 (2026-10-23 gate change, user-authorized): goal traceability and evidence presence.
    # Both entry points call the same implementation, so a batch cannot pass the directory run and
    # then fail the repo run — two readings of one contract is exactly the defect this batch fixes.
    errors.extend(batch_traceability_findings(feature_dir, repo_root))

    return errors


# --- Decision-traceability checks (C15-C18). Marker-gated and opt-in, mirroring how C11
# gates the design-heading checks: a file only enters these checks when it carries the
# matching marker. This keeps the linter safe to run over the whole repo — a decision ledger
# that has not adopted the eight-column shape is not force-rewritten, and an open issue
# without a batch attachment does not flood the gate. The mechanism is pinned by --self-test
# and demonstrated on the opt-in example files (examples/decisions/).

DECISION_MARKER = "agentflow 决策记录"
LEDGER_MARKER = "agentflow 问题台账"
OWNERSHIP_MARKER = "agentflow 决策归属"
ISS_RE = re.compile(r"ISS-\d{4}-\d{3}(?:-[^\s|]+)?")

DECISION_COLUMNS = ["来源", "待决问题", "现状核验", "推荐", "关闭条件", "优先级", "影响范围", "自动决策"]
LEDGER_STATUS_WORDS = ("仍存在", "已修复", "已关闭", "已失效", "已修", "待修")
PRIORITY_RE = re.compile(r"\bP[0-3]\b")
LEVEL_RE = re.compile(r"(单功能|单模块|多模块|跨项目)")
# 影响范围 must be 级别(具体模块/项目) — a level word alone (no parenthesised name) is a finding.
IMPACT_RE = re.compile(r"(单功能|单模块|多模块|跨项目)\s*\(([^)]+)\)")
OPTION_RE = re.compile(r"[A-C][\u3000\s]")
AUTO_Y_RE = re.compile(r"自动规则|触发条件|判定结论")
DATE_CMD_RE = re.compile(r"\d{4}-\d{2}-\d{2}.*`[^`]+`")


def _ref_is_in_repo(repo_root: Path, path: str) -> bool | None:
    """True if path's first segment is a real entry of this repo (so a missing file is a real
    rot, not an external reference); False if it names a directory this repo does not have
    (treat as a foreign-repo source and accept it without resolution); None if no first segment.
    """
    seg = path.split("/")[0].split(":")[0].split("#")[0].split("?")[0].strip()
    if not seg:
        return None
    return (repo_root / seg).exists()


def _source_refs(cell: str, repo_root: Path) -> tuple[list[str], list[str]]:
    """Return (in_repo_missing, external) reference tokens from a 来源 cell.

    A backtick path or an ``ISS-`` link is an "external" reference when its first segment is
    not a real entry of this repo (e.g. ``planning/...`` belongs to another repo) and is
    accepted without resolution. An in-repo path that does not exist on disk is "missing" and
    must be reported. Cross-repo sources are legitimate — the decision's origin can live in a
    different repository.
    """
    missing: list[str] = []
    external: list[str] = []
    for span in re.findall(r"`([^`\n]+)`", cell):
        tok = span.strip()
        if ISS_RE.search(tok):
            target = repo_root / "docs" / "issues" / tok
            if not target.is_file():
                external.append(tok)
            continue
        p = tok.split("#")[0].split("?")[0].split(":")[0].strip()
        if not p or p.startswith(("/", "http:", "https:", "mailto:")):
            continue
        in_repo = _ref_is_in_repo(repo_root, p)
        if in_repo is None:
            continue
        if in_repo:
            if not (repo_root / p).exists():
                missing.append(tok)
        else:
            external.append(tok)
    for m in ISS_RE.findall(cell):
        full = m + ".md"
        if not (repo_root / "docs" / "issues" / full).is_file() and full not in external:
            external.append(full)
    return missing, external


def decision_record_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C16 — every decision-record table (header ⊇ DECISION_COLUMNS) must be machine-judgable."""
    errors: list[str] = []
    for header, rows in md_tables(text):
        if not all(col in header for col in DECISION_COLUMNS):
            continue  # not a decision-record table; leave 选项对比 / before-after tables alone
        for row in rows:
            cells = {header[i]: (row[i] if i < len(row) else "") for i in range(len(header))}
            src = cells.get("来源", "")
            pend = cells.get("待决问题", "")
            verify = cells.get("现状核验", "")
            rec = cells.get("推荐", "")
            close = cells.get("关闭条件", "")
            prio = cells.get("优先级", "")
            impact = cells.get("影响范围", "")
            auto = cells.get("自动决策", "")
            if not (re.search(r"`[^`]+`", src) or ISS_RE.search(src)):
                errors.append(f"C16 decision-record {label} 决策行缺「来源」（须有 path:line 或 ISS 编号）")
            else:
                missing, _ext = _source_refs(src, repo_root)
                for m in missing:
                    errors.append(f"C16 decision-record {label} 来源引用在盘上不存在: {m}")
            if len(OPTION_RE.findall(pend)) < 2:
                errors.append(f"C16 decision-record {label} 待决问题少于 2 个选项（须 A/B/C… 且各带代价）")
            if not DATE_CMD_RE.search(verify):
                errors.append(f"C16 decision-record {label} 现状核验缺「日期 + 反引号命令」")
            if not close.strip() or close.strip() in ("—", "无", "-"):
                errors.append(f"C16 decision-record {label} 关闭条件为空或为「无」")
            if not PRIORITY_RE.search(prio):
                errors.append(f"C16 decision-record {label} 优先级非 P0–P3")
            if not IMPACT_RE.search(impact):
                if LEVEL_RE.search(impact):
                    errors.append(
                        f"C16 decision-record {label} 影响范围只写级别词未列具体模块/项目"
                        f"（须 级别(具体模块/项目)，如 多模块(youc-admin 订单筛选页 + youc-canvas 支付组件)）"
                    )
                else:
                    errors.append(f"C16 decision-record {label} 影响范围格式非法（须 级别(具体模块/项目)）")
            am = auto.strip().upper()
            if am not in ("Y", "N"):
                errors.append(f"C16 decision-record {label} 自动决策须为 Y/N")
            elif am == "Y":
                if prio.strip() != "P3":
                    errors.append(f"C16 decision-record {label} 自动决策=Y 仅允许 P3（现 {prio.strip() or '空'}）")
                if not AUTO_Y_RE.search(rec):
                    errors.append(
                        f"C16 decision-record {label} 自动决策=Y 但推荐列缺「自动规则/触发条件/判定结论」"
                    )
    return errors


def _last_commit(repo_root: Path, rel_path: str) -> tuple[int, str] | None:
    """(commit epoch, short sha) of the last commit touching rel_path, or None if git/absent."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ct %h", "--", rel_path],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    parts = r.stdout.strip().splitlines()[0].split(None, 1)
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), parts[1]
    except ValueError:
        return None


def staleness_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C17 — a decision's referenced in-repo path modified after its 核验 date is stale."""
    errors: list[str] = []
    for header, rows in md_tables(text):
        if not all(col in header for col in DECISION_COLUMNS):
            continue
        for row in rows:
            cells = {header[i]: (row[i] if i < len(row) else "") for i in range(len(header))}
            verify = cells.get("现状核验", "")
            m = re.search(r"(\d{4}-\d{2}-\d{2})", verify)
            if not m:
                continue
            try:
                v_date = _dt.datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            for span in re.findall(r"`([^`\n]+)`", cells.get("来源", "")):
                p = span.strip().split("#")[0].split("?")[0].split(":")[0].strip()
                if not p or p.startswith(("/", "http:", "https:", "mailto:")):
                    continue
                if _ref_is_in_repo(repo_root, p) is not True:
                    continue  # external refs are not time-checked (declared per repo scope)
                if not (repo_root / p).exists():
                    continue
                commit = _last_commit(repo_root, p)
                if not commit:
                    continue
                # 日粒度比较。用秒比对会把「当天写核验、当天又改到被引用文件」永远判过期，
                # 于是 2026-10-23 的门在数学上不可能同日转绿（独立评审第二轮 P1-1 实证）；
                # 条款要防的是「拿几天前的清单来问人拍板」，不是同批次内的正常推进。
                c_date = _dt.datetime.fromtimestamp(commit[0]).date()
                if c_date > v_date:
                    errors.append(
                        f"C17 staleness {label} 引用 {p} 在核验（{m.group(1)}）之后的日期被修改: "
                        f"{commit[1]} {c_date.isoformat()} —— 须重跑核验命令并刷新日期"
                    )
    return errors


def ledger_index_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C15 — a ledger row may not carry a status word unless it links an ISS; ISS links resolve."""
    errors: list[str] = []
    for _header, rows in md_tables(text):
        for row in rows:
            joined = " | ".join(row)
            if any(w in joined for w in LEDGER_STATUS_WORDS) and not ISS_RE.search(joined):
                errors.append(
                    f"C15 ledger-index {label} 台账行自带状态词且无 ISS 链接"
                    f"（状态只能写在记录 frontmatter）"
                )
            for iss in ISS_RE.findall(joined):
                if not (repo_root / "docs" / "issues" / (iss + ".md")).is_file():
                    errors.append(f"C15 ledger-index {label} 台账行引用 {iss} 但记录文件不存在")
    return errors


def _record_status(rec_text: str) -> tuple[str, str]:
    """(status, disposition) from a record's YAML-ish frontmatter (no yaml dep)."""
    if not rec_text.startswith("---"):
        return "", ""
    end = rec_text.find("\n---", 3)
    if end == -1:
        return "", ""
    fm = rec_text[3:end]
    st = re.search(r"^status:\s*(\S+)", fm, re.MULTILINE)
    disp = re.search(r"^disposition:\s*(\S+)", fm, re.MULTILINE)
    return (st.group(1) if st else ""), (disp.group(1) if disp else "")


def ownership_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C18 — every open issue must be attached to a batch 承接表 or carry deferred/not-doing."""
    errors: list[str] = []
    covered: set[str] = set()
    for header, rows in md_tables(text):
        cell = None
        if _has_columns(header, ["记录编号", "任务号"]):
            for row in rows:
                cell = _cells(header, row)
                covered.update(ISS_RE.findall(_col(cell, "记录编号")))
    issues_dir = repo_root / "docs" / "issues"
    if not issues_dir.is_dir():
        return errors
    for rec in sorted(issues_dir.glob("ISS-*.md")):
        body = rec.read_text(encoding="utf-8", errors="ignore")
        status, disp = _record_status(body)
        if status != "open":
            continue
        iss_id = rec.stem  # e.g. ISS-2026-010-office计划缺异常矩阵
        if iss_id in covered:
            continue
        if disp in ("deferred", "not-doing"):
            continue
        errors.append(
            f"C18 ownership {label} {iss_id} 状态 open，但未出现在任何批次承接表，"
            f"也无 deferred/not-doing 声明（须归属，否则登记当天即红）"
        )
    return errors


# --- Traceability and evidence-presence checks (C22-C23). Marker-gated like C15-C18: a batch
# opts in by carrying 「agentflow 目标承接」 in its README. What differs from the 2026-10-21
# batch is adoption: this repo's live batches opt in on the day the check ships, so the gate
# bites real files instead of only the fixtures under examples/ — the 2026-10-22 walkthrough
# found a proposal goal (CI on a real runner) that vanished from spec, acceptance points and
# the plan task table with nothing turning red, and two ☑ rows whose only evidence was a
# /tmp path that had already been cleaned away.

TRACE_MARKER = "agentflow 目标承接"
TRACE_COLUMNS = ["目标", "spec 承接", "plan 任务", "状态"]
GOAL_RE = re.compile(r"\bG\d+\b")
def trace_task_ids(cell: str) -> set[str]:
    """任务号引用列里的编号集合，方言与 C9 的 `TASK_ID_RE` 同一条（T / FT 前缀都认）。

    独立一份正则会造出「承接表能写、看板认不出」的空洞，所以这里只做切分与全匹配筛选。
    """
    return {tok for tok in re.split(r"[^0-9A-Za-z_-]+", cell) if TASK_ID_RE.fullmatch(tok)}
MODULE_RE = re.compile(r"\bM-[A-Z]\b")
AC_ID_RE = re.compile(r"\bG\d+-AC-\d+\b")
DONE_GLYPH = "☑"
TODO_GLYPH = "☐"
BLOCKED_GLYPH = "⚠"
SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{7,40}(?![0-9a-fA-F])")
REPO_REV_RE = re.compile(r"[\w.-]+@[0-9a-f]{7,40}:[^\s|`]+")
NA_RE = re.compile(r"N/A[:：]\s*\S")


def git_available() -> bool:
    return shutil.which("git") is not None


def _git_commit_present(repo_root: Path, sha: str) -> bool:
    """True only when git resolves sha as a commit object. No git means not verifiable: the
    check fails closed rather than letting an unverifiable claim pass on a machine without git."""
    try:
        r = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        )
    except OSError:
        return False
    return r.returncode == 0


def _tables_with_columns(text: str, cols: list[str]) -> list[tuple[list[str], list[list[str]]]]:
    """Every table whose (markup-normalised) header covers cols."""
    return [hd for hd in md_tables(text) if _has_columns(hd[0], cols)]


def _norm_col(name: str) -> str:
    """Column label without markup, so `**目标**`, `` `ID` `` and 「目标 」name the same column."""
    return name.strip().strip("`* ").replace(" ", "").replace("　", "")


def _col(cell: dict[str, str], name: str) -> str:
    """Read a column by label through the same normalisation the header match uses."""
    return cell.get(_norm_col(name), "")


def _has_columns(header: list[str], cols: list[str]) -> bool:
    wanted = {_norm_col(c) for c in cols}
    return wanted.issubset({_norm_col(h) for h in header})


def _cells(header: list[str], row: list[str]) -> dict[str, str]:
    return {_norm_col(h): (row[i] if i < len(row) else "") for i, h in enumerate(header)}


def plan_task_rows(text: str) -> dict[str, tuple[str, str]]:
    """task id -> (status cell, evidence cell) for every table with an ID and a 状态 column.

    The evidence column may be named 证据 or 证据回写; when absent the pair's second element is
    empty, which C23 reads as "no evidence" for a completed row rather than as a parse failure.
    """
    out: dict[str, tuple[str, str]] = {}
    for header, rows in md_tables(text):
        labels = {_norm_col(h) for h in header}
        if "ID" not in labels or "状态" not in labels:
            continue  # 列名按同一归一化匹配：装饰过的表头不得让整张表静默不可见
        ev_col = next((c for c in ("证据", "证据回写") if _norm_col(c) in labels), None)
        for row in rows:
            cell = _cells(header, row)
            tid = _col(cell, "ID").strip().strip("`* ")
            if not TASK_ID_RE.match(tid):  # 任务号方言单点取自 C9，不在这里另立一套
                continue
            out[tid] = (_col(cell, "状态"), _col(cell, ev_col) if ev_col else "")
    return out


def evidence_carriers(cell: str, repo_root: Path, batch_dir: Path | None = None) -> list[str]:
    """Which verifiable carriers this evidence cell holds: repo path, repo-qualified ref,
    resolvable commit sha, or an explicit N/A with a reason. /tmp and absolute paths never count.

    Paths resolve against the repo root *and* the batch directory, because evidence cells are
    written both ways in practice (`reviews/review-…md` relative to the batch, `docs/issues/…`
    relative to the repo). Reading only the repo root called correctly-written evidence missing —
    the over-wide judgement this batch's own exception matrix predicted and required narrowing.
    """
    roots = [repo_root] + ([batch_dir] if batch_dir is not None else [])
    kinds: list[str] = []
    own = {repo_root.name, "agentflow", "agentflows"}
    for m in REPO_REV_RE.finditer(cell):
        repo = m.group(0).split("@", 1)[0]
        if repo not in own:
            kinds.append("仓限定引用")
            continue
        # 本仓名也可以用仓限定写法，但那就得按本仓核：rev 可解析且路径在盘，否则是自己写的假地址
        rev, _, tail = m.group(0).split("@", 1)[1].partition(":")
        if tail and _git_commit_present(repo_root, rev) and (repo_root / tail).exists():
            kinds.append("本仓限定引用（已核）")
    # 路径 token 复用 C9 的 path_candidates：反引号内与裸写的带后缀路径都算，
    # 否则按契约（spec/be §6.2「反引号内或裸写」）正确写下的证据会被判成无载体。
    tokens = sorted(path_candidates(cell)) + [g for g in re.findall(r"\]\(([^)\s]+)\)", cell)]
    for tok in tokens:
        p = tok.strip().strip("（）()「」\"'[]").split("#")[0].split("§")[0]
        if not p or p.startswith(("/", "~", "http:", "https:", "mailto:")):
            continue
        if "@" in p or ":" in p:
            continue  # repo-qualified refs are handled above
        if any(_ref_is_in_repo(r, p) is True and (r / p).exists() for r in roots):
            kinds.append("仓内路径")
            break
    for sha in SHA_RE.findall(cell):
        if _git_commit_present(repo_root, sha):
            kinds.append("提交号")
            break
    if NA_RE.search(cell):
        kinds.append("显式不适用")
    return sorted(set(kinds))


def evidence_presence_findings(
    label: str, plan_text: str, repo_root: Path, batch_dir: Path | None = None
) -> list[str]:
    """C23 — a row marked 已完成 must carry something a third party can re-check on disk."""
    errors: list[str] = []
    rows = plan_task_rows(plan_text)
    for task_id, (status, evidence) in sorted(rows.items()):
        if not status.strip().startswith(DONE_GLYPH):
            continue  # 进行中 / 未开始 / 阻塞 / 本期不做 carry no evidence duty yet
        if evidence_carriers(evidence, repo_root, batch_dir):
            continue
        if not evidence.strip():
            detail = "证据列为空"
        elif SHA_RE.search(evidence) and not git_available():
            detail = "环境无 git，提交号不可核（失败关闭：无 git 时提交号不算可复核载体）"
        elif "/tmp/" in evidence or re.search(r"(^|[\s`])/(Users|home|var)/", evidence):
            detail = "证据只指向临时目录或机器绝对路径，已不在盘"
        else:
            detail = "证据列无可复核载体（路径不存在、提交号不可解析、也不是仓限定引用）"
        errors.append(
            f"C23 证据在场: {label} {task_id} 标为已完成但{detail}"
            f"（四类载体之一即可：仓内存在的路径 / 仓库@修订:路径 / 可解析提交号 / N/A: 理由）"
        )
    return errors


def _heading_sections(text: str) -> list[str]:
    """Markdown chunks of (heading line + body up to the next heading)."""
    chunks: list[str] = []
    cur: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line):
            if cur:
                chunks.append("\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def trace_tables(readme_text: str) -> list[tuple[list[str], list[list[str]]]]:
    """The 承接 tables sitting under a heading that names 目标承接.

    Heading scoping is not decoration: a table with the same four columns placed anywhere else in
    the README would otherwise satisfy the check while the real 承接表 stayed unread.
    """
    out: list[tuple[list[str], list[list[str]]]] = []
    for section in _heading_sections(readme_text):
        if "目标承接" in section.splitlines()[0]:
            out.extend(_tables_with_columns(section, TRACE_COLUMNS))
    return out


def goal_traceability_findings(feature_dir: Path, repo_root: Path) -> list[str]:
    """C22 — every proposal goal must land in spec and plan, and nothing may cite a phantom.

    Bidirectional on purpose: a one-way check (targets must appear downstream) is satisfied by
    writing anything downstream, while the reverse direction catches citations that no upstream
    goal ever declared. Status is compared with the plan board's glyphs, so a README claiming a
    goal is done while its tasks are still ☐ fails the same day it is written.
    """
    readme = feature_dir / "README.md"
    if not readme.is_file():
        return []
    readme_text = read(readme)
    if TRACE_MARKER not in readme_text:
        return []
    batch = feature_dir.name
    tables = trace_tables(readme_text)
    if not tables:
        return [
            (
                f"C22 目标承接: {batch} 打了 {TRACE_MARKER} 标记，但「目标承接」标题下没有承接表"
                f"（必需列：{' / '.join(TRACE_COLUMNS)}）；补表，不许摘标记"
            )
        ]
    md_files = [f for f in sorted(feature_dir.rglob("*.md")) if f.name != ".gitkeep"]
    stage_text = {
        "proposal": "\n".join(read(f) for f in find_stage(md_files, feature_dir / "proposal")),
        "spec": "\n".join(read(f) for f in find_stage(md_files, feature_dir / "spec")),
    }
    plan_rows: dict[str, tuple[str, str]] = {}
    for f in find_stage(md_files, feature_dir / "plan"):
        plan_rows.update(plan_task_rows(read(f)))

    def _resolves(token: str) -> bool:
        p = token.strip().split("#")[0].split("§")[0].strip()
        if not p or p.startswith(("/", "http:", "https:", "mailto:")) or "@" in p:
            return True  # 非仓内路径写法不在本判据射程内（外链与跨仓引用另有口径）
        return (feature_dir / p).exists() or (repo_root / p).exists()

    errors: list[str] = []
    table_goals: set[str] = set()
    referenced: set[str] = set()
    for header, rows in tables:
        for row in rows:
            cell = _cells(header, row)
            goals = set(GOAL_RE.findall(_col(cell, "目标")))
            if not goals:
                errors.append(f"C22 目标承接: {batch} 承接行「{_col(cell, '目标')[:24] or '空'}」没有目标编号 G n")
            table_goals |= goals
            tag = "/".join(sorted(goals)) or _col(cell, "目标")[:24]

            for mid in sorted(set(MODULE_RE.findall(_col(cell, "spec 承接")))):
                if mid not in stage_text["spec"]:
                    errors.append(f"C22 目标承接: {tag} 声明由 {mid} 承接，但 spec/ 文本里找不到 {mid}")
            for ac in sorted(set(AC_ID_RE.findall(_col(cell, "spec 承接")))):
                if ac not in stage_text["spec"]:
                    errors.append(f"C22 目标承接: {tag} 引用的验收点 {ac} 不在 spec/ 文本中")
            # 出处列同样要能在盘上解析——声明了「路径须可解析」却从不校验，就是第二条空转判据
            cited = _col(cell, "proposal 出处") + _col(cell, "spec 承接")
            for p in sorted(path_candidates(cited)):
                if not _resolves(p):
                    errors.append(f"C22 目标承接: {tag} 的出处 {p} 不在盘（批次目录与仓根各试一次）")

            tids = trace_task_ids(_col(cell, "plan 任务"))
            if not tids:
                errors.append(f"C22 目标承接: {tag} 未给出任何 plan 任务号")
            for t in sorted(tids):
                if t not in plan_rows:
                    errors.append(f"C22 目标承接: {tag} 引用的任务号 {t} 不在计划任务表（幻影引用）")
            referenced |= tids

            glyph = _col(cell, "状态").strip()[:1]
            real = {plan_rows[t][0].strip()[:1] for t in tids if t in plan_rows}
            if glyph == DONE_GLYPH and real and real != {DONE_GLYPH}:
                errors.append(
                    f"C22 目标承接: {tag} 承接表标已完成，所引任务行的字形是 {'/'.join(sorted(real))}"
                )
            if glyph in (TODO_GLYPH, "◐", BLOCKED_GLYPH) and real == {DONE_GLYPH}:
                errors.append(
                    f"C22 目标承接: {tag} 承接表状态是「{glyph}」，但所引任务行已全部完成（未回写）"
                )

    declared = set(GOAL_RE.findall(stage_text["proposal"]))
    for g in sorted(declared - table_goals):
        errors.append(f"C22 目标承接: 提案声明的目标 {g} 未进入承接表（缺承接）")
    for g in sorted(table_goals - declared):
        errors.append(f"C22 目标承接: 承接表引用了提案中不存在的目标 {g}（幻影目标）")
    for task_id, (status, _ev) in sorted(plan_rows.items()):
        if status.strip()[:1] in (DONE_GLYPH, BLOCKED_GLYPH) and task_id not in referenced:
            errors.append(
                f"C22 目标承接: {batch} 计划任务 {task_id} 已是完成或阻塞状态，"
                f"却没有被任何承接行引用（孤儿任务，须说明它服务哪个目标）"
            )
    return errors


def batch_traceability_findings(batch_dir: Path, repo_root: Path) -> list[str]:
    """C22 + C23 for one batch directory; the single entry both modes call.

    The plan glob is recursive on purpose: batches put plans under `plan/` and sometimes one level
    deeper (`plan/be/`), and a non-recursive read silently reports "no evidence problems" for every
    nested plan — the vacuous-check failure mode this whole batch exists to close.
    """
    errors = goal_traceability_findings(batch_dir, repo_root)
    plan_dir = batch_dir / "plan"
    if not plan_dir.is_dir():
        return errors
    for f in sorted(plan_dir.rglob("*.md")):
        if f.name == ".gitkeep":
            continue
        rel = f.relative_to(repo_root).as_posix() if f.is_relative_to(repo_root) else f.name
        errors.extend(evidence_presence_findings(rel, read(f), repo_root, batch_dir))
    return errors


def repo_policy_findings(repo_root: Path) -> list[str]:
    """Run C15-C18 over opt-in files. Marker-gated so the whole repo can be scanned safely."""
    errors: list[str] = []
    skip_dirs = (repo_root / ".git", repo_root / "packaging" / "runtime")
    md_files: list[Path] = []
    for p in repo_root.rglob("*.md"):
        if p.parent == skip_dirs[1] or any(s in p.parents for s in skip_dirs):
            continue
        md_files.append(p)
    for p in md_files:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = p.relative_to(repo_root).as_posix()
        if DECISION_MARKER in t:
            errors.extend(decision_record_findings(rel, t, repo_root))
            errors.extend(staleness_findings(rel, t, repo_root))
        if LEDGER_MARKER in t:
            errors.extend(ledger_index_findings(rel, t, repo_root))
    for batch in sorted(p for p in repo_root.glob("docs/features/*") if p.is_dir()):
        readme = batch / "README.md"
        t = read(readme) if readme.is_file() else ""
        if OWNERSHIP_MARKER in t:
            errors.extend(ownership_findings(readme.relative_to(repo_root).as_posix(), t, repo_root))
        # The batch set is every directory, not only those that already have a README: two modes
        # sharing one implementation is worthless if they disagree about which batches exist.
        errors.extend(batch_traceability_findings(batch, repo_root))
    return errors


def self_test() -> int:
    """Per-check discrimination fixtures (reviewer-authored matrix, 2026-09-20).

    One dense chain must pass; one mutation per check must fail with that check id; the
    AC3 non-regression classes (非阻塞 rows, decision-table ids, design ledger rows) must
    NOT trip. Fixes review finding F1 ("self-test vacuous for most checks"). Cases 27–34
    pin C14's positive/negative surface (paired forms, definition rows, code spans, the
    real-corpus 「IP 桶」 near-miss); cases 35–38 pin the --file text-form mode and its
    mutual exclusion with the positional feature dir; cases 39–43 pin C13's per-file exemption
    and the planned-role exemption; cases 44–48 pin the C4/C8 applicability rule and C1's
    段落映射豁免; cases 49–54 pin C9's task-row and 分支策略 rules; cases 55–56 pin C5's
    prose-only id scan; case 34 documents why C15 stays clause-governed (see the note at
    CODE_SUBJECT_RE); cases 73–85 pin the 2026-10-21 gate change (bare-glyph status dialect,
    README 落点基准, C19 qa acceptance, C20 埋点贯通, C21 ui 轨, placeholder non-firing);
    cases 86–97 pin the 2026-10-23 gate change (C22 goal traceability — missing carrier row,
    phantom task id, status over-claim, orphan task, marker-without-table, opt-in respected;
    C23 evidence presence — /tmp-only, empty cell, repo-qualified and N/A carriers, and the
    repo scan applying C23 to every batch while C22 stays marker-gated).
    """
    import subprocess
    import tempfile

    linter = Path(__file__).resolve()
    base = {
        "README.md": "# feature\n\n## 需求评审门\n## 技术方案评审门\n",
        "proposal/p.md": "# proposal\n",
        "spec/s.md": (
            "# spec\n\n## 3.0 不合规项（反审 checklist）\n\n"
            "| # | 缺口 | 阻塞 | 状态 |\n| --- | --- | --- | --- |\n"
            "| B-1 | x | 阻塞 | ☑ 已关闭 |\n"
            "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n"
        ),
        "spec/qa/acceptance.md": (
            "# qa\n\n## 1. 验收口径\n\n- AC-01 登录成功后跳转工作台\n"
        ),
        "design/be/b.md": (
            "# be\n\n"
            "| 接口 | 请求字段 | 响应字段 |\n| --- | --- | --- |\n| A1 | d(string,Y) | uid |\n\n"
            "| # | 决策 | 结论 |\n| --- | --- | --- |\n| D6 | 决策六 | 方案二 |\n| D10 | 决策十 | 方案三 |\n\n"
            "### 1.3 待核实清单\n\n"
            "| # | 事项 | 影响 |\n| --- | --- | --- |\n| V-9 | 外部接口形态 | T02 |\n\n"
            "```mermaid\nsequenceDiagram\n    A->>B: go\n    alt 失败\n        B-->>A: err\n    end\n```\n"
            "```mermaid\nflowchart TB\n    A --> B\n```\n"
            "```mermaid\nerDiagram\n    t1 ||--o{ t2 : has\n```\n"
        ),
        "design/fe/f.md": (
            "# fe\n\nA1 调用见异常矩阵\n\n"
            "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n| A1 | ok | 412 |\n\n"
            "```mermaid\nflowchart LR\n    L --> D\n```\n"
            "```mermaid\nsequenceDiagram\n    U->>L: click\n```\n"
            "```mermaid\nstateDiagram-v2\n    [*] --> S1\n```\n"
            "```text\n┌─列表──┐\n│ 卡片  │\n└──────┘\n```\n"
            "```text\n┌─弹窗──┐\n│ 字段  │\n└──────┘\n```\n"
        ),
        "plan/be/p.md": (
            "# plan\n\n## 0. 分支策略 feature-x\n\n"
            "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n| --- | --- | --- | --- | --- | --- |\n"
            "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 | `migrations/x.sql` |\n\n"
            "V-9 由 T02 承接\n"
        ),
        # "@root/" keys are written under the fixture repo root (the feature dir's parent), so C9
        # code-location paths resolve against a real file, not against this repository.
        "@root/migrations/x.sql": "-- x\n",
    }

    def rep(files: dict, rel: str, old: str, new: str) -> dict:
        assert old in files[rel], "mutation anchor missing in " + rel
        files[rel] = files[rel].replace(old, new)
        return files

    def run_case(name: str, expect_rc: int, want: list[str], mutate=None, results=None) -> None:
        files = dict(base)
        if mutate:
            files = mutate(dict(base))
        d = Path(tempfile.mkdtemp()) / "feature"
        for rel, text in files.items():
            p = d.parent / rel[len("@root/"):] if rel.startswith("@root/") else d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(linter), "--root", str(d.parent), str(d)],
            capture_output=True, text=True, check=False,
        )
        out = r.stdout + r.stderr
        ok = r.returncode == expect_rc and all(w in out for w in want)
        results.append((name, ok))
        if not ok:
            print(f"  wanted {want}, exit={r.returncode}, got:\n{out}")

    ALT = "    alt 失败\n        B-->>A: err\n    end\n"
    CONTRACT = "| 接口 | 请求字段 | 响应字段 |\n| --- | --- | --- |\n| A1 | d(string,Y) | uid |\n\n"
    WF2 = "```text\n┌─弹窗──┐\n│ 字段  │\n└──────┘\n```\n"
    results: list[tuple[str, bool]] = []

    run_case("01 good dense chain passes (D6/D10 never C5; design ledger never C9)", 0,
             ["PASS doc-chain"], results=results)

    def m_thin(f):
        rep(f, "design/be/b.md", CONTRACT, "")
        rep(f, "design/be/b.md", ALT, "")
        rep(f, "design/fe/f.md", WF2, "")
        rep(f, "plan/be/p.md", "`migrations/x.sql`", "迁移三张表")
        return f
    run_case("02 original-thin chain fails C4-contract/C4-alt/C7/C9", 1,
             ["缺少字段级 API 契约表", "缺少含失败分支（alt）的时序图",
              "C7 design/fe: 工程线框不足 2 张（现 1）", "C9 plan 落点"],
             m_thin, results)
    run_case("03 open 非阻塞 row does NOT trip C3", 0, ["PASS doc-chain"],
             lambda f: rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                           "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n| B-9 | z | 非阻塞 | ☐ 待评审确认 |\n"),
             results)
    run_case("04 open 阻塞 row trips C3", 1, ["C3 反审门"],
             lambda f: rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                           "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n| B-9 | z | 阻塞 | ☐ 待评审确认 |\n"),
             results)
    run_case("05 C5 contract-table id absent from fe trips C5", 1, ["C5 契约闭合"],
             lambda f: rep(f, "design/be/b.md", "| A1 | d(string,Y) | uid |\n",
                           "| A1 | d(string,Y) | uid |\n| B2 | e(string,Y) | x |\n"),
             results)
    run_case("06 C1 stage without a real doc trips C1", 1, ["C1 结构"],
             lambda f: (f.pop("plan/be/p.md"), f)[1], results)
    run_case("07 C2 README missing gate trips C2", 1, ["C2 入口门禁"],
             lambda f: f.update({"README.md": "# feature\n\n## 需求评审门\n"}) or f, results)
    run_case("08 C4 missing flowchart trips C4", 1, ["缺少架构/流程 flowchart"],
             lambda f: rep(f, "design/be/b.md", "```mermaid\nflowchart TB\n    A --> B\n```\n", ""),
             results)
    run_case("09 C4 missing ER/state trips C4", 1, ["缺少 ER 图或状态机图"],
             lambda f: rep(f, "design/be/b.md", "```mermaid\nerDiagram\n    t1 ||--o{ t2 : has\n```\n", ""),
             results)
    run_case("10 C7 single wireframe trips C7", 1, ["C7 design/fe: 工程线框不足 2 张（现 1）"],
             lambda f: rep(f, "design/fe/f.md", WF2, ""), results)
    run_case("11 C8 missing stateDiagram trips C8", 1, ["C8 design/fe: 缺少 stateDiagram"],
             lambda f: rep(f, "design/fe/f.md", "```mermaid\nstateDiagram-v2\n    [*] --> S1\n```\n", ""),
             results)
    run_case("12 C6 fe missing exception matrix trips C6", 1, ["C6 design/fe: 缺少接口异常边界矩阵"],
             lambda f: rep(f, "design/fe/f.md",
                           "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n| A1 | ok | 412 |\n\n", ""),
             results)
    run_case("12b C6 header-only matrix does NOT satisfy C6 (matrix needs a data row)", 1,
             ["C6 design/fe: 缺少接口异常边界矩阵"],
             lambda f: rep(f, "design/fe/f.md",
                           "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n| A1 | ok | 412 |\n\n",
                           "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n\n"),
             results)
    run_case("13 C10 unclosed mermaid fence trips C10", 1, ["C10 mermaid"],
             lambda f: f.update({"design/be/b.md": f["design/be/b.md"] + "```mermaid\nflowchart X\n"}) or f,
             results)
    run_case("14 C9 missing branch strategy trips C9", 1, ["未声明分支策略"],
             lambda f: rep(f, "plan/be/p.md", "## 0. 分支策略 feature-x", "## 0. 执行顺序"), results)
    run_case("15 C9 design V-item unreferenced by plan trips C9", 1, ["C9 待核实闭合"],
             lambda f: rep(f, "plan/be/p.md", "V-9 由 T02 承接\n", ""), results)
    run_case("16 C9 open blocking plan row trips C9", 1, ["未回写证据的阻塞任务行"],
             lambda f: f.update({"plan/be/p.md": f["plan/be/p.md"] + "| T99 | 修复 | `fix/x.go` | — | ⚠ 阻塞 ☐ |\n"}) or f,
             results)
    def strip_wireframes(f):
        # remove all text-wireframe blocks (fence-to-fence), keep everything else
        f["design/fe/f.md"] = re.sub(r"```text\n.*?```", "", f["design/fe/f.md"], flags=re.DOTALL)
        f["design/fe/prototype.html"] = (
            "<html>\n<body>\n<div data-testid=\"task-list\">定时任务列表原型</div>\n"
            "<div data-testid=\"task-retry\">重试</div>\n</body>\n</html>\n"
        )
        return f
    run_case("18 a real html prototype alone satisfies C7", 0, ["PASS doc-chain"],
             strip_wireframes, results)

    def empty_prototype(f):
        f = strip_wireframes(dict(base))
        f["design/fe/prototype.html"] = ""
        return f
    run_case("58 a zero-byte prototype.html no longer buys the C7 exemption (the name is not "
             "the artefact)", 1, ["C7 design/fe"], empty_prototype, results)
    run_case("59 a 阻塞-status row whose prose mentions 非阻塞 still trips C3 (the exemption is "
             "a status-cell claim, not a whole-line keyword)", 1, ["C3 反审门"],
             lambda f: rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                           "| B-2 | y | 阻塞（非阻塞项已另行列示） | ☐ 待评审确认 |\n"),
             results)

    def add_marker(f):
        f["README.md"] = f["README.md"] + "\n本 feature 文档链由 agentflow 文档链方法生成（2026-09-20）\n"
        return f
    run_case("19 marker without fixed headings trips C11", 1, ["C11 结构模板"], add_marker, results)

    def add_marker_and_heads(f):
        f = add_marker(f)
        f["design/be/b.md"] += "\n## 0. 先说结论\n| 问题 | 结论 |\n\n## 1.6 兼容性思考 & 影响面评估\n\n## 4. Design 评审前自检\n"
        f["design/fe/f.md"] += "\n## 4. Design 评审前自检\n\n| data-testid | 节点 | 出现条件 |\n| --- | --- | --- |\n| x-card | 卡片 | 列表 |\n"
        return f
    run_case("20 marker with fixed headings passes C11", 0, ["PASS doc-chain"], add_marker_and_heads, results)
    run_case("17 task-like row inside a DESIGN table is never a C9 task row", 0, ["PASS doc-chain"],
             lambda f: rep(f, "design/be/b.md", "| V-9 | 外部接口形态 | T02 |\n",
                           "| V-9 | 外部接口形态 | T02 |\n| T99 | 待核实事项 | — |\n"),
             results)

    def add_stale_existing_link(f):
        # claim word + link that resolves from spec/ -> design/be/b.md exists on disk
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n详设 [设计文档](../design/be/b.md) 尚未产出\n")
    run_case("21 C12 stale claim with an existing linked target trips C12", 1,
             ["C12 时效性引用: spec/s.md", "声称待产出但目标已存在: ../design/be/b.md"],
             add_stale_existing_link, results)

    def add_stale_absent_link(f):
        # same claim words, but the linked target does not exist — an honest pending claim
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n错误码表 [草案](./errata-draft.md) 待产出\n")
    run_case("22 C12 stale claim with an absent target does NOT trip", 0, ["PASS doc-chain"],
             add_stale_absent_link, results)

    def add_role_word(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n按 supervisor 的本轮评审意见执行\n")
    run_case("23 C13 session role word trips C13 (both the name and the session phrase)", 1,
             ["C13 会话角色词: proposal/p.md", "supervisor", "本轮评审"],
             add_role_word, results)

    def add_formal_role_name(f):
        # formal role names outside the closed word list never trip C13
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n由独立评审人与技术负责人收口\n")
    run_case("24 C13 formal role names do NOT trip", 0, ["PASS doc-chain"],
             add_formal_role_name, results)

    def add_stale_backtick_path(f):
        # claim word + backtick code path to a target that exists (the corpus's other form)
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n设计稿见 `../design/be/b.md`，待补充\n")
    run_case("25 C12 stale claim with an existing backtick path trips C12", 1,
             ["C12 时效性引用: spec/s.md", "声称待产出但目标已存在: ../design/be/b.md"],
             add_stale_backtick_path, results)

    def add_stale_backtick_absent(f):
        # same claim words, backtick form, but the path does not exist — honest pending claim
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n验收脚本 `./qa-check.md` 待补充\n")
    run_case("26 C12 stale backtick path with an absent target does NOT trip", 0, ["PASS doc-chain"],
             add_stale_backtick_absent, results)

    # --- C14 bare code subjects + --file mode. C15 (schema words in prose) is deliberately
    # NOT implemented — the closed-set heuristic flooded a real reviewed chain's legend rows;
    # case 34 pins that boundary. See the note at CODE_SUBJECT_RE for the full trade. ---

    def add_bare_bucket(f):
        return rep(f, "design/be/b.md", "### 1.3 待核实清单\n",
                   "### 1.3 待核实清单\n\nD 桶积分中断时对账回滚\n")
    run_case("27 C14 bare code subject in prose trips (D 桶)", 1,
             ["C14 代号裸用: design/be/b.md", "D 桶"], add_bare_bucket, results)

    def add_bare_bucket_heading(f):
        return rep(f, "proposal/p.md", "# proposal\n", "# proposal\n\n### A 桶：36 会话\n")
    run_case("28 C14 bare code subject as a heading trips (A 桶：36 会话)", 1,
             ["C14 代号裸用: proposal/p.md", "A 桶"], add_bare_bucket_heading, results)

    def add_bold_definition_row(f):
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n| **A** 交付 .pptx |\n")
    run_case("29 C14 bold-code definition row (口径表 form) never matches", 0,
             ["PASS doc-chain"], add_bold_definition_row, results)

    def add_paired_forms(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n交付桶（A 桶）承接演示物；A 桶（交付 .pptx）已就绪\n")
    run_case("30 C14 sanctioned paired forms 白话（代号）/代号（白话） do NOT trip", 0,
             ["PASS doc-chain"], add_paired_forms, results)

    def add_backtick_bucket(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n跑批脚本按 `A 桶` 过滤，日志另记\n")
    run_case("31 C14 inside an inline code span does NOT trip", 0,
             ["PASS doc-chain"], add_backtick_bucket, results)

    def add_glossary_row(f):
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n| A 桶 | 交付 .pptx 的会话集合 |\n| --- | --- |\n")
    run_case("32 C14 glossary table rows are the sanctioned definition site", 0,
             ["PASS doc-chain"], add_glossary_row, results)

    def add_ip_bucket(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n限流口径：验证码与找回共用同一个 IP 桶\n")
    run_case("33 C14 real-corpus near-miss IP 桶 (letter run, not a lone code) does NOT trip", 0,
             ["PASS doc-chain"], add_ip_bucket, results)

    def add_schema_word(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n单次执行积分按 prepared 会话口径统计\n")
    run_case("34 schema-word prose (prepared 会话) stays clause-governed — C15 deliberately "
             "not implemented (closed-set heuristic flooded a real chain's legend rows)", 0,
             ["PASS doc-chain"], add_schema_word, results)

    def run_file_case(name: str, expect_rc: int, want: list[str], text: str,
                      argv: list[str] | None = None, sub: str = "deliverable.md") -> None:
        d = Path(tempfile.mkdtemp()) / sub
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(text, encoding="utf-8")
        cmd = [sys.executable, str(linter)] + (argv if argv is not None else ["--file", str(d)])
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
        out = r.stdout + r.stderr
        ok = r.returncode == expect_rc and all(w in out for w in want)
        results.append((name, ok))
        if not ok:
            print(f"  wanted {want}, exit={r.returncode}, got:\n{out}")

    run_file_case("35 --file mode: session deliverable hitting C13+C14 exits 1", 1,
                  ["C14 代号裸用", "C13 会话角色词", "D 桶"],
                  "# 数据分析报告\n\n## 口径表\n\n| 代号 | 白话 |\n| --- | --- |\n| D | 中断桶 |\n\n"
                  "## 结论\n\nD 桶积分中断最多，本轮评审已确认。\n")
    run_file_case("36 --file mode: clean deliverable exits 0", 0, ["PASS doc-chain --file"],
                  "# 状态汇报\n\n全部检查通过，剩余两例行已排期。\n")
    run_file_case("37 --file together with a positional feature dir is a usage error", 2,
                  ["Usage"], "# 报告\n",
                  argv=[str(Path(tempfile.mkdtemp())), "--file", "deliverable.md"])
    run_file_case("38 --file without a path is a usage error", 2, ["Usage"], "# 报告\n",
                  argv=["--file"])

    # --- C13 scope + the planned-role exemption (cases 39–43). C13 is a defect in a deliverable;
    # it is skipped only on the files listed in C13_EXEMPT_FILES, one by one. The same sentence
    # must flip verdict on the file alone, and a planned role name (Execution Coordinator) is
    # neither a session word nor a reason to exempt.
    run_file_case("39 C13 role word passes in an exempt defining file (product-design.md)",
                  0, ["PASS doc-chain --file"],
                  "# product design\n\n| Supervisor（主会话） | 收口、委派 |\n",
                  sub="docs/product/design/product-design.md")
    run_file_case("40 C13 exempt file may quote the session words it defines as forbidden", 0,
                  ["PASS doc-chain --file"],
                  "# product design\n\n表达纪律禁止 supervisor、TD、本轮评审 一类会话词。\n",
                  sub="docs/product/design/product-design.md")
    run_file_case("41 Execution Coordinator is a planned role name, not a session word", 0,
                  ["PASS doc-chain --file"],
                  "# 计划\n\n未来的 Execution Coordinator 负责持久队列，本期不做。\n")
    run_file_case("42 C13 exemption is per file: an unlisted skills/ file with a role word trips",
                  1, ["C13 会话角色词"],
                  "# 说明\n\n按 supervisor 的指示执行。\n",
                  sub="skills/agentflow/references/unlisted.md")
    run_file_case("43 C13 exemption is per file: a non-exempt docs/product stage doc trips",
                  1, ["C13 会话角色词", "method-spec.md"],
                  "# method spec\n\nspec 由 supervisor 起草。\n",
                  sub="docs/product/spec/method-spec.md")

    # --- C4/C5/C8 applicability (cases 60–62): a role's checks apply when spec/<role>/ or
    # design/<role>/ holds a document, so an empty design/<role>/ cannot skip them.
    def m_spec_be_only(f):
        f.pop("design/be/b.md")
        f["spec/be/s.md"] = "# be spec\n"
        return f
    run_case("60 C4 applies when only spec/be holds a document and design/be is empty", 1,
             ["C4 design/be: 缺少含失败分支（alt）的时序图"], m_spec_be_only, results)

    def m_empty_be(f):
        f.pop("design/be/b.md")
        f["design/be/.gitkeep"] = ""
        return f
    run_case("61 C4 does NOT apply when design/be and spec/be are both empty", 0,
             ["PASS doc-chain"], m_empty_be, results)

    def m_spec_fe_only(f):
        f.pop("design/fe/f.md")
        f["spec/fe/s.md"] = "# fe spec\n"
        return f
    run_case("62 C8 applies when only spec/fe holds a document and design/fe is empty", 1,
             ["C8 design/fe: 缺少 flowchart"], m_spec_fe_only, results)

    # --- C1 段落映射豁免 (cases 47–48): an empty stage passes only with a named landing.
    def m_landing_design(f):
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        f["README.md"] += (
            "\n| 链阶段 | 落点 | 说明 |\n| --- | --- | --- |\n"
            "| design | `docs/product/design/product-design.md` | 产品设计 |\n"
        )
        return f
    run_case("47 C1 段落映射豁免: empty design/ passes when README names a landing", 0,
             ["PASS doc-chain"], m_landing_design, results)

    def m_landing_dash(f):
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        f["README.md"] += (
            "\n| 链阶段 | 落点 | 说明 |\n| --- | --- | --- |\n"
            "| design | — | 待定 |\n"
        )
        return f
    run_case("48 C1: empty design/ with a 「—」 landing still trips C1", 1,
             ["C1 结构: design/"], m_landing_dash, results)

    # --- C9 task rows and branch section (cases 49–54).
    run_case("49 C9 task row with 待核实 in the ID column is invalid", 1,
             ["ID 列非法"],
             lambda f: rep(f, "plan/be/p.md", "| T01 | 迁移 |", "| 待核实 | 迁移 |"), results)
    run_case("50 C9 status outside the fixed enum trips", 1,
             ["不在固定枚举内"],
             lambda f: rep(f, "plan/be/p.md", "☐ 未开始 |", "完成 |"), results)
    run_case("51 C9 code path that does not exist trips", 1,
             ["代码落点路径不存在: migrations/nope.sql"],
             lambda f: rep(f, "plan/be/p.md", "`migrations/x.sql`", "`migrations/nope.sql`"), results)
    run_case("52 C9 待核实 in the location cell passes without a real path", 0,
             ["PASS doc-chain"],
             lambda f: rep(f, "plan/be/p.md", "`migrations/x.sql` | — | ☐ 未开始 |",
                           "待核实 `db/schema.sql` | — | ☐ 未开始 |"), results)
    run_case("53 C9 待核实 outside the location cell does NOT rescue an empty location", 1,
             ["无仓库内路径且无「待核实」标记"],
             lambda f: rep(f, "plan/be/p.md", "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |",
                           "| T01 | 待核实迁移 | — | — | ☐ 未开始 |"), results)

    run_case("57 C9 本期不做 row needs no landing; its ID and status are still checked", 0,
             ["PASS doc-chain"],
             lambda f: rep(f, "plan/be/p.md", "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |",
                           "| T01 | 迁移 | — | — | — 本期不做 |"), results)

    def add_plan_without_branch(f):
        f["plan/be/q.md"] = "# plan q\n\n无任务表\n"
        return f
    run_case("54 C9 every plan file needs its own 分支策略 section", 1,
             ["plan/be/q.md 未声明分支策略"], add_plan_without_branch, results)

    # --- C5 ids counted from prose only (cases 55–56).
    def m_id_only_in_fence(f):
        rep(f, "design/fe/f.md", "A1 调用见异常矩阵\n", "")
        rep(f, "design/fe/f.md", "| A1 | ok | 412 |", "| X1 | ok | 412 |")
        f["design/fe/f.md"] += "```text\nA1 示例\n```\n"
        return f
    run_case("55 C5 contract id that appears only inside a code fence does NOT close", 1,
             ["C5 契约闭合", "A1"], m_id_only_in_fence, results)

    run_case("56 C5 contract id in fe prose closes (table row removed, prose mention kept)", 0,
             ["PASS doc-chain"],
             lambda f: rep(f, "design/fe/f.md", "| A1 | ok | 412 |", "| X1 | ok | 412 |"), results)

    def m_lightweight(f):
        f.pop("spec/s.md")
        f.pop("spec/qa/acceptance.md")
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        f["README.md"] = base["README.md"] + "\n轻量模式：无 spec/design 轨\n"
        return f
    run_case("42 declared lightweight chain (no spec/design track) passes C1", 0,
             ["PASS doc-chain"], m_lightweight, results)

    def m_lightweight_no_proposal(f):
        f = m_lightweight(dict(base))
        f.pop("proposal/p.md")
        return f
    run_case("43 declared lightweight chain still trips C1 when proposal is missing "
             "(the exemption narrows the stage set, it does not switch C1 off)", 1,
             ["C1 结构"], m_lightweight_no_proposal, results)

    def m_undeclared_thin(f):
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        return f
    run_case("63 an undeclared chain whose design track is empty still trips C1 (the exemption "
             "is declaration-gated, never inferred from emptiness)", 1,
             ["C1 结构"], m_undeclared_thin, results)

    # --- C15-C18 decision traceability (marker-gated, 2026-10-21). Each case builds a tiny
    # repo root with opt-in marker files and asserts repo_policy_findings discriminates. The
    # proposal's self-prove section requires the gate to bite its own examples: good passes,
    # mutations fail with the right check id.
    def run_repo_case(name: str, expect: int, want: list[str], files: dict,
                      with_issues: dict | None = None) -> None:
        d = Path(tempfile.mkdtemp()) / "repo"
        d.mkdir(parents=True, exist_ok=True)
        for rel, text in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        if with_issues:
            idir = d / "docs" / "issues"
            idir.mkdir(parents=True, exist_ok=True)
            for rel, text in with_issues.items():
                (idir / rel).write_text(text, encoding="utf-8")
        errs = repo_policy_findings(d)
        ok = (len(errs) == expect) and all(w in "\n".join(errs) for w in want)
        results.append((name, ok))
        if not ok:
            print(f"  wanted {expect} findings containing {want}, got {len(errs)}:\n"
                  + "\n".join(f"  - {e}" for e in errs))

    DEC_HEAD = ("| 来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    DEC_GOOD_ROW = ("| `docs/features/x/README.md:10` | A 改一 B 改二 | 2026-10-21 `grep x` | 选 A | 批次 T01 | "
                    "P2 | 多模块(youc-admin 订单筛选 + youc-canvas 支付) | N |\n")

    def dec_file(body: str) -> str:
        return ("# 决策\n\n本文件由 agentflow 决策记录方法生成（2026-10-21）\n\n" + body)

    run_repo_case("64 C16 compliant decision-record table passes", 0, [],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW)})
    run_repo_case("65 C16 missing 来源 trips C16", 1, ["C16 decision-record", "缺「来源」"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW.replace(
                      "`docs/features/x/README.md:10`", ""))})
    run_repo_case("66 C16 impact level word without module name trips C16", 1,
                  ["C16 decision-record", "只写级别词未列具体模块"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW.replace(
                      "多模块(youc-admin 订单筛选 + youc-canvas 支付)", "多模块"))})
    run_repo_case("67 C16 auto=Y on non-P3 trips C16", 1,
                  ["C16 decision-record", "自动决策=Y 仅允许 P3"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW
                      .replace("P2", "P2").replace(" | N |", " | Y |")
                      .replace("选 A", "选 A（自动规则 R1；触发条件 X；判定结论 Y）"))})
    run_repo_case("68 C16 missing verify date trips C16", 1,
                  ["C16 decision-record", "现状核验缺"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW.replace(
                      "2026-10-21 `grep x`", "`grep x`"))})

    def ledger_file(body: str) -> str:
        return ("# 台账\n\n本文件由 agentflow 问题台账方法生成\n\n" + body)

    LED_HEAD = ("| 编号 | 一句话 | 记录链接 | 归属 |\n| --- | --- | --- | --- |\n")
    run_repo_case("69 C15 ledger row with status word and no ISS trips C15", 1,
                  ["C15 ledger-index", "台账行自带状态词"],
                  {"docs/issues/README.md": ledger_file(LED_HEAD + "| #1 | 渠道知识已修复 |  | 批次 T07 |\n")},
                  with_issues={"ISS-2026-001-x.md": "---\nstatus: fixed\n---\n"})
    run_repo_case("70 C15 compliant ledger row (ISS link resolves) passes", 0, [],
                  {"docs/issues/README.md": ledger_file(LED_HEAD + "| #1 | 渠道知识 | ISS-2026-001-x | 批次 T07 |\n")},
                  with_issues={"ISS-2026-001-x.md": "---\nstatus: fixed\n---\n"})

    OWN_HEAD = ("| 记录编号 | 任务号 | 说明 |\n| --- | --- | --- |\n")
    run_repo_case("71 C18 open issue not attached to a batch 承接表 trips C18", 1,
                  ["C18 ownership", "ISS-2026-001-x"],
                  {"docs/features/batch-a/README.md":
                   "# 批次\n\n本文件由 agentflow 决策归属方法生成\n\n" + OWN_HEAD + "| — | T01 | 收尾 |\n"},
                  with_issues={"ISS-2026-001-x.md": "---\nstatus: open\n---\n"})
    run_repo_case("72 C18 open issue covered by 承接表 passes", 0, [],
                  {"docs/features/batch-a/README.md":
                   "# 批次\n\n本文件由 agentflow 决策归属方法生成\n\n" + OWN_HEAD
                   + "| ISS-2026-001-x | T01 | 收尾 |\n"},
                  with_issues={"ISS-2026-001-x.md": "---\nstatus: open\n---\n"})

    # --- C9 dialect / 落点基准 and C19-C21 (2026-10-21 gate change, user-authorized).
    # Cases 73-84 pin: the bare-glyph status dialect (aligned with gate/plan.py's first-char
    # read), the README 落点基准 declaration, the qa-acceptance presence check, and the two
    # opt-in README-row gates (埋点贯通 / ui 轨原型).
    def m_bare_status(f):
        return rep(f, "plan/be/p.md", "| ☐ 未开始 |", "| ☑ |")
    run_case("73 C9 bare-glyph status is legal (aligned with gate/plan.py first-char read)", 0,
             ["PASS doc-chain"], m_bare_status, results)

    def m_bare_dash(f):
        return rep(f, "plan/be/p.md", "| ☐ 未开始 |", "| — |")
    run_case("74 C9 bare dash counts as 本期不做 (no landing required)", 0,
             ["PASS doc-chain"], m_bare_dash, results)

    def m_free_text_status(f):
        return rep(f, "plan/be/p.md", "| ☐ 未开始 |", "| 已完成 |")
    run_case("75 C9 free-text status without a glyph still trips", 1,
             ["不在固定枚举内"], m_free_text_status, results)

    def m_base_ok(f):
        f["@root/lib/util.py"] = "-- util\n"
        f = rep(f, "plan/be/p.md", "`migrations/x.sql`", "`util.py`")
        f["README.md"] = f["README.md"] + "\n- 落点基准：lib\n"
        return f
    run_case("76 C9 落点基准 declaration redirects path resolution", 0,
             ["PASS doc-chain"], m_base_ok, results)

    def m_base_missing(f):
        f["@root/lib/util.py"] = "-- util\n"
        return rep(f, "plan/be/p.md", "`migrations/x.sql`", "`util.py`")
    run_case("77 C9 without a 落点基准 declaration the same cell trips", 1,
             ["代码落点路径不存在: util.py"], m_base_missing, results)

    def m_base_bad(f):
        f["README.md"] = f["README.md"] + "\n- 落点基准：no-such-dir/\n"
        return f
    run_case("78 C9 落点基准 pointing at a missing directory trips", 1,
             ["C9 落点基准"], m_base_bad, results)

    def m_no_qa(f):
        f.pop("spec/qa/acceptance.md")
        return f
    run_case("79 C19 spec with be/fe content but no qa acceptance trips", 1,
             ["C19 qa 验收"], m_no_qa, results)

    def m_no_qa_declared(f):
        f.pop("spec/qa/acceptance.md")
        f["README.md"] = f["README.md"] + "\n- 备注：qa 不适用（纯后端批）\n"
        return f
    run_case("80 C19 declared qa exemption passes", 0,
             ["PASS doc-chain"], m_no_qa_declared, results)

    def m_ui_track_bare(f):
        f = rep(f, "design/fe/f.md", WF2, "")
        f["README.md"] = f["README.md"] + "\n- UI 轨：已启用（spec/ui/visual.md + design/ui/visual.md）\n"
        return f
    run_case("81 C21 UI 轨 enabled without prototype or >=2 wireframes trips", 1,
             ["C21 ui 轨"], m_ui_track_bare, results)

    def m_ui_track_proto(f):
        f = rep(f, "design/fe/f.md", WF2, "")
        f["README.md"] = f["README.md"] + "\n- UI 轨：已启用（spec/ui/visual.md + design/ui/visual.md）\n"
        f["prototype/index.html"] = "<!doctype html>\n<html><body>" + "x" * 80 + "</body></html>\n"
        return f
    run_case("82 C21 UI 轨 enabled with a real prototype passes", 0,
             ["PASS doc-chain"], m_ui_track_proto, results)

    def m_track_bare(f):
        f["README.md"] = f["README.md"] + "\n- 埋点：本期新增 2 个事件（design/fe §1.7）\n"
        return f
    run_case("83 C20 埋点新增 declared without the three sections trips", 1,
             ["C20 埋点贯通"], m_track_bare, results)

    def m_track_ok(f):
        f["README.md"] = f["README.md"] + "\n- 埋点：本期新增 2 个事件（design/fe §1.7）\n"
        f["proposal/p.md"] = f["proposal/p.md"] + "\n## 6.2 埋点决策\n"
        f["spec/s.md"] = f["spec/s.md"] + "\n### 4. 埋点验收草案\n"
        f["design/fe/f.md"] = f["design/fe/f.md"] + "\n### 1.7 埋点事件契约\n"
        return f
    run_case("84 C20 埋点新增 with the three sections passes", 0,
             ["PASS doc-chain"], m_track_ok, results)

    # unfilled template placeholders never fire the opt-in gates
    def m_track_placeholder(f):
        f["README.md"] = f["README.md"] + "\n- 埋点：<本期新增 n 个事件（design/fe §1.7）｜复用既有事件 <事件名>｜N/A: 理由>\n- UI 轨：<已启用（spec/ui/visual.md + design/ui/visual.md）｜未启用>\n- 落点基准：<.（主实施仓根，默认）｜<相对目标仓根的路径>｜本批次目录>\n"
        return f
    run_case("85 unfilled README 落点基准/埋点/UI 轨 placeholders never fire", 0,
             ["PASS doc-chain"], m_track_placeholder, results)

    # --- C22 goal traceability and C23 evidence presence (2026-10-23 gate change,
    # user-authorized). Cases 86-95 pin the four C22 directions (missing carrier row, phantom
    # task id, status over-claim, orphan completed task), the marker-without-table case, the
    # four evidence carriers, the /tmp-only failure, and that an unmarked batch is untouched.
    TRACE_README = (
        "# feature\n\n## 需求评审门\n## 技术方案评审门\n\n"
        "本批次启用 agentflow 目标承接 标记，承接表如下。\n\n"
        "## 目标承接表\n\n"
        "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "{rows}"
    )
    TRACE_ROW_OK = ("| G1 目标一 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n")
    TRACE_SPEC = (
        "# spec\n\n## 3.0 不合规项（反审 checklist）\n\n"
        "| # | 缺口 | 阻塞 | 状态 |\n| --- | --- | --- | --- |\n| B-1 | x | 阻塞 | ☑ 已关闭 |\n\n"
        "### M-A 模块一\n\n| 验收点 | 来源 |\n| --- | --- |\n| G1-AC-01 | proposal §1.2 G1 |\n"
    )

    def trace_plan(evidence: str, status: str = "☑ 已完成") -> str:
        return (
            "# plan\n\n## 0. 分支策略 feature-x\n\n"
            "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| T01 | 迁移 | `migrations/x.sql` | — | {status} | {evidence} |\n\n"
            "V-9 由 T01 承接\n"
        )

    def trace_files(rows: str = TRACE_ROW_OK, evidence: str = "`migrations/x.sql` 在盘",
                    status: str = "☑ 已完成") -> dict:
        return {
            "README.md": TRACE_README.format(rows=rows),
            "proposal/p.md": "# proposal\n\n目标：G1 目标一（可判定）。\n",
            "spec/s.md": TRACE_SPEC,
            "plan/be/p.md": trace_plan(evidence, status),
            "@root/migrations/x.sql": "-- x\n",
        }

    def m_trace_ok(f):
        f.update(trace_files())
        return f
    run_case("86 C22 marked batch with a closed 承接表 passes", 0,
             ["PASS doc-chain"], m_trace_ok, results)

    def m_trace_missing_goal(f):
        f.update(trace_files(rows="| G2 目标二 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n"))
        return f
    run_case("87 C22 a goal declared upstream but absent from the table trips", 1,
             ["C22 目标承接", "未进入承接表"], m_trace_missing_goal, results)

    def m_trace_phantom_task(f):
        f.update(trace_files(rows=TRACE_ROW_OK.replace("T01", "T99")))
        return f
    run_case("88 C22 a task id cited by the table but missing from the plan trips", 1,
             ["C22 目标承接", "不在计划任务表"], m_trace_phantom_task, results)

    def m_trace_status_lie(f):
        f.update(trace_files(rows=TRACE_ROW_OK.replace("☑ 已完成", "☑ 已完成"),
                              status="☐ 未开始"))
        return f
    run_case("89 C22 table claims done while the board row is still 未开始 trips", 1,
             ["C22 目标承接", "承接表标已完成"], m_trace_status_lie, results)

    def m_trace_orphan_done(f):
        files = trace_files(rows=TRACE_ROW_OK.replace("T01", "—"))
        files["README.md"] = files["README.md"].replace("| T01 |", "| — |")
        f.update(files)
        return f
    run_case("90 C22 a completed task nobody claims trips as an orphan", 1,
             ["C22 目标承接", "孤儿任务"], m_trace_orphan_done, results)

    def m_trace_no_table(f):
        f["README.md"] = "# feature\n\n## 需求评审门\n## 技术方案评审门\n\n本批启用 agentflow 目标承接 标记。\n"
        return f
    run_case("91 C22 marker without a table trips instead of silently skipping", 1,
             ["C22 目标承接", "没有承接表"], m_trace_no_table, results)

    def m_trace_unmarked(f):
        f.update(trace_files())
        f["README.md"] = f["README.md"].replace("agentflow 目标承接", "目标承接")
        return f
    run_case("92 C22/C23 never fire on a batch that did not opt in (no false positives)", 0,
             ["PASS doc-chain"], m_trace_unmarked, results)

    def m_trace_tmp_evidence(f):
        f.update(trace_files(evidence="`/tmp/baseline.txt`（已随临时目录清理）"))
        return f
    run_case("93 C23 a ☑ row whose only evidence is a cleaned /tmp path trips", 1,
             ["C23 证据在场", "T01"], m_trace_tmp_evidence, results)

    def m_trace_repo_ref(f):
        f.update(trace_files(evidence="youc@1a2b3c4:docs/x.md 与 `N/A: 无额外产物`"))
        return f
    run_case("94 C23 repo-qualified refs and explicit N/A with reason are carriers", 0,
             ["PASS doc-chain"], m_trace_repo_ref, results)

    def m_trace_empty_evidence(f):
        f.update(trace_files(evidence=""))
        return f
    run_case("95 C23 an empty evidence cell on a ☑ row trips", 1,
             ["C23 证据在场", "证据列为空"], m_trace_empty_evidence, results)

    # Repo-scan side: C23 applies to every batch (the evidence duty belongs to the plan
    # contract, not to the opt-in marker), while C22 only bites opted-in batches.
    PLAN_TMP = (
        "# plan\n\n## 0. 分支策略 feature-x\n\n"
        "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n| --- | --- | --- | --- | --- | --- |\n"
        "| T01 | 迁移 | `a.py` | — | ☑ 已完成 | `/tmp/x.txt` 已清理 |\n"
    )
    UNMARKED_TRACE_README = (
        "# 批次\n\n## 需求评审门\n## 技术方案评审门\n\n目标承接如下（未打启用标记）。\n\n"
        "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| G1 目标一 | — | M-A | T01 | ☑ 已完成 |\n"
    )
    run_repo_case("96 C23 catches cleaned /tmp evidence in a batch that did not opt in", 1,
                  ["C23 证据在场", "T01"],
                  {"docs/features/b/README.md": "# 批次\n\n## 需求评审门\n",
                   "docs/features/b/plan/p.md": PLAN_TMP})
    run_repo_case("97 C22 skips an unmarked batch in the repo scan (opt-in preserved)", 0, [],
                  {"docs/features/b/README.md": UNMARKED_TRACE_README,
                   "docs/features/b/plan/p.md": trace_plan("N/A: 夹具，无额外产物")})

    def m_base_inline_default(f):
        # 元信息写在同一行、且声明的就是默认值：不得凭空造出一个不存在的目录
        f["README.md"] = (f["README.md"]
                          + "\n- UI 轨：未启用；落点基准：.（主实施仓根，默认）；最后更新时间：2026-10-23\n")
        return f
    run_case("98 C9 落点基准 declared inline as the default value never invents a missing dir", 0,
             ["PASS doc-chain"], m_base_inline_default, results)

    # --- 2026-10-23 独立评审 findings 的回归夹具（100-106）：每条都对应评审指出的一个
    # 「声明了但没校验」或「判据静默失明」的空洞。
    def m_evid_backticked_task_id(f):
        files = trace_files(evidence="`/tmp/x.txt`（已清理）")
        files["plan/be/p.md"] = files["plan/be/p.md"].replace("| T01 |", "| `T01` |")
        f.update(files)
        return f
    run_case("100 C23 reads backtick-quoted task ids (the dialect that once made it blind)", 1,
             ["C23 证据在场", "T01"], m_evid_backticked_task_id, results)

    def m_evid_bare_path(f):
        files = trace_files(evidence="docs/x.md 的原始输出已入库")
        files["@root/docs/x.md"] = "# x\n"
        f.update(files)
        return f
    run_case("101 C23 accepts a bare written repo path, as the contract states", 0,
             ["PASS doc-chain"], m_evid_bare_path, results)

    def m_trace_phantom_source(f):
        f.update(trace_files(rows="| G1 目标一 | `proposal/NOPE.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n"))
        return f
    run_case("102 C22 validates the 出处 column, not just the spec column", 1,
             ["C22 目标承接", "proposal/NOPE.md 不在盘"], m_trace_phantom_source, results)

    def m_trace_decoy_placement(f):
        files = trace_files()
        files["README.md"] = files["README.md"].replace("## 目标承接表", "## 随便一张同形表")
        files["@root/README-decoy.md"] = ""
        f.update(files)
        return f
    run_case("103 C22 reads only the table under the 目标承接 heading (decoy elsewhere trips)", 1,
             ["C22 目标承接", "标题下没有承接表"], m_trace_decoy_placement, results)

    def m_trace_decorated_header(f):
        files = trace_files()
        files["README.md"] = files["README.md"].replace(
            "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n",
            "| **目标** | `proposal 出处` | **spec 承接** | plan 任务 | 状态 |\n")
        f.update(files)
        return f
    run_case("104 C22 matches decorated column labels instead of reporting 缺表", 0,
             ["PASS doc-chain"], m_trace_decorated_header, results)

    def m_trace_status_stale(f):
        f.update(trace_files(rows="| G1 目标一 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ◐ 进行中 |\n",
                             status="☑ 已完成"))
        return f
    run_case("105 C22 catches a 进行中 row whose tasks are all done (both directions)", 1,
             ["C22 目标承接", "未回写"], m_trace_status_stale, results)

    def m_evid_self_repo_ref(f):
        f.update(trace_files(evidence="agentflow@0000000:zzz.md"))
        return f
    run_case("106 C23 verifies a ref qualified with this repo's own name instead of waving it through", 1,
             ["C23 证据在场", "T01"], m_evid_self_repo_ref, results)

    def m_ft_task_id(f):
        # C9 的任务号方言：FT 前缀与一两位数字都必须合法（曾被 C22 的同名常量遮蔽）
        return rep(f, "plan/be/p.md", "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |",
                              "| FT01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |")
    run_case("99 C9 still accepts the FT-prefixed task id dialect (constant shadowing guard)", 0,
             ["PASS doc-chain"], m_ft_task_id, results)

    ok = all(passed for _, passed in results)
    for name, passed in results:
        print(("PASS " if passed else "FAIL ") + name)
    print(f"{sum(p for _, p in results)}/{len(results)} self-test cases pass")
    return 0 if ok else 1


def lint_file(path: Path) -> int:
    """--file mode: text-form checks only (C12/C13/C14) against one standalone markdown file."""
    if not path.is_file():
        print("FAIL doc-chain --file (1 findings)")
        print(f"  - 文件不存在: {path}")
        return 1
    errors = text_form_findings(str(path), read(path), [path.parent])
    if errors:
        print(f"FAIL doc-chain --file {path} ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS doc-chain --file {path}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 1 and argv[0] == "--self-test":
        return self_test()
    root = REPO_ROOT
    if argv[:1] == ["--root"]:
        if len(argv) < 2 or argv[2:3] == ["--file"]:
            print(__doc__)
            return 2
        root, argv = Path(argv[1]), argv[2:]
    if argv and argv[0] == "--file":
        if len(argv) != 2:
            print(__doc__)
            return 2
        return lint_file(Path(argv[1]))
    if argv and argv[0] == "--repo":
        if len(argv) != 2:
            print(__doc__)
            return 2
        root = Path(argv[1])
        if not root.is_dir():
            print(f"FAIL decision-gate: 目录不存在: {root}")
            return 1
        errors = repo_policy_findings(root)
        if errors:
            print(f"FAIL decision-gate ({len(errors)} findings)")
            for e in errors:
                print(f"  - {e}")
            return 1
        print("PASS decision-gate")
        return 0
    if len(argv) != 1:
        print(__doc__)
        return 2
    errors = lint(Path(argv[0]), root)
    if errors:
        print(f"FAIL doc-chain ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS doc-chain {argv[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
