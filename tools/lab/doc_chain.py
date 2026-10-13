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
                       status from the fixed enum, and a code location that is a repository path
                       (every path token must exist) or carries 「待核实」 in the location cell;
                       every plan file has a 「分支策略」 section; design's V-n open items are
                       referenced by some plan
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

Usage:
    python3 tools/lab/doc_chain.py [--root <repo-dir>] <feature-dir>
    python3 tools/lab/doc_chain.py --file <single-markdown-path>
    python3 tools/lab/doc_chain.py --self-test

Exit code 0 = all checks pass; 1 = findings; 2 = usage error. --file runs only the text-form
checks (C12/C13/C14) against one standalone markdown file — a session deliverable handed to
the user (analysis report, status report) has no feature-directory shape, so every structure
check (C1–C11) is skipped by design; --file and a positional feature dir are mutually exclusive.
"""

from __future__ import annotations

import re
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
ROLE_WORD_RE = re.compile(r"supervisor|coordinator", re.I)
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
TASK_ID_RE = re.compile(r"^(?:FT?\d{2}|T\d{1,2})$")
PLACEHOLDER = "待核实"
# 「分支策略」 section: a heading at level 2-4, optionally numbered ("## 分支策略", "### 0. 分支策略").
BRANCH_HEADING_RE = re.compile(r"^#{2,4}\s+(?:\d+\.\s*)?分支策略(?:\s|$)", re.M)
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

# C15 (schema words in prose — 「prepared 会话」「单次 Run 积分」) is deliberately NOT
# implemented. The closed-set heuristic the improvement brief allowed (prepared/pending/
# running/failed/… + CJK, outside code) was validated against a real reviewed chain and
# flooded: state→visual mapping rows (「queued 灰 / running 蓝 / succeeded 绿」) are the
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
                role_line = re.sub(re.escape(phrase), " ", role_line, flags=re.I)
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
    blocks, lines, inside, buf = [], text.splitlines(), False, []
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


def plan_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C9 task-row grounding for one plan file: ID shape, status enum, code location."""
    errors: list[str] = []

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
            if not any(status.startswith(s) for s in TASK_STATUS_ENUM):
                errors.append(f"C9 plan 状态: {label} {task_id} 状态「{status}」不在固定枚举内")
            if status.startswith("— 本期不做"):
                continue
            loc = at(row, loc_i)
            if PLACEHOLDER in loc:
                continue
            cands = path_candidates(loc)
            if not cands:
                errors.append(f"C9 plan 落点: {label} {task_id} 代码落点无仓库内路径且无「待核实」标记")
                continue
            for cand in sorted(cands):
                if not (repo_root / cand.rstrip("/")).exists():
                    errors.append(f"C9 plan 落点: {label} {task_id} 代码落点路径不存在: {cand}")
    return errors


def find_stage(files: list[Path], *parts: str) -> list[Path]:
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

    # C1 structure: a stage directory may be empty only when the batch README's 段落映射 names a
    # landing for it (non-empty and not 「—」); otherwise it must hold a real document.
    landing = stage_landing(all_text.get(readme, "")) if readme.is_file() else {}
    for stage in STAGE_DIRS:
        stage_files = [f for f in md_files if stage in f.relative_to(feature_dir).parts]
        if stage_files:
            continue
        if landing.get(stage, "") not in ("", "—"):
            continue  # 段落映射豁免
        errors.append(f"C1 结构: {stage}/ 下没有任何有效文档（仅 .gitkeep 占位），且 README 段落映射未写明落点")
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
            # accepted tolerance (review note b): the whole-line 非阻塞 skip can also
            # suppress a 阻塞-status row whose text merely mentions 非阻塞 —
            # false-negative direction, acceptable for a floor linter
            if "非阻塞" in line:
                continue  # non-blocking rows may stay open pending review confirmation
            if line.lstrip().startswith("|") and "阻塞" in line and "☐" in line:
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

    if be_applies:
        kinds = mermaid_kinds(be_text)
        seq_with_alt = [b for b in kinds.get("sequenceDiagram", []) if re.search(r"^\s*alt\b", b, re.M)]
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
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", be_text, re.M):
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
        wireframes = [
            b
            for b in re.findall(r"```text\n(.*?)```", fe_text, re.S)
            if any(c in b for c in BOX_CHARS)
        ]
        has_prototype = any(f.suffix == ".html" and "prototype" in str(f.relative_to(feature_dir)).lower()
                            for f in md_files + [x for x in files if x.is_file() and x.suffix == ".html"])
        if len(wireframes) < 2 and not has_prototype:
            errors.append(f"C7 design/fe: 工程线框不足 2 张（现 {len(wireframes)}）且无 prototype HTML 原型")
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", fe_text, re.M):
            header = table.splitlines()[0]
            if ("成功" in header or "正常" in header) and ("失败" in header or "异常" in header):
                break
        else:
            errors.append("C6 design/fe: 缺少接口异常边界矩阵（表头需同时覆盖 成功 与 失败/异常）")

    # C9 plan grounding
    plan_files = find_stage(md_files, feature_dir / "plan")
    plan_text = "\n".join(all_text[f] for f in plan_files) if plan_files else ""
    if plan_files:
        for f in plan_files:
            rel = str(f.relative_to(feature_dir))
            errors.extend(plan_findings(rel, all_text[f], repo_root))
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
        if not _re.search(r"^##+ .*(先说结论|关键决策速览|结论先行)", be_heads, _re.M):
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
        rel = f.relative_to(feature_dir)
        errors.extend(text_form_findings(str(rel), all_text[f], [f.parent, feature_dir]))

    # C10 mermaid fence balance
    for f in md_files:
        text = all_text[f]
        opened = sum(1 for line in text.splitlines() if line.strip() == "```mermaid")
        blocks = len(mermaid_blocks(text))
        if opened != blocks:
            errors.append(f"C10 mermaid: {f.relative_to(feature_dir)} 有 {opened} 个 mermaid 围栏但仅 {blocks} 个闭合")

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
    CODE_SUBJECT_RE).
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
            "| ID | 任务 | 代码落点 | 依赖 | 状态 |\n| --- | --- | --- | --- | --- |\n"
            "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |\n\n"
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
            capture_output=True, text=True,
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
        f["design/fe/f.md"] = re.sub(r"```text\n.*?```", "", f["design/fe/f.md"], flags=re.S)
        f["design/fe/prototype.html"] = "<html>定时任务原型</html>"
        return f
    run_case("18 html prototype alone satisfies C7", 0, ["PASS doc-chain"], strip_wireframes, results)

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
        r = subprocess.run(cmd, capture_output=True, text=True)
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

    # --- C4/C5/C8 applicability (cases 44–46): a role's checks apply when spec/<role>/ or
    # design/<role>/ holds a document, so an empty design/<role>/ cannot skip them.
    def m_spec_be_only(f):
        f.pop("design/be/b.md")
        f["spec/be/s.md"] = "# be spec\n"
        return f
    run_case("44 C4 applies when only spec/be holds a document and design/be is empty", 1,
             ["C4 design/be: 缺少含失败分支（alt）的时序图"], m_spec_be_only, results)

    def m_empty_be(f):
        f.pop("design/be/b.md")
        f["design/be/.gitkeep"] = ""
        return f
    run_case("45 C4 does NOT apply when design/be and spec/be are both empty", 0,
             ["PASS doc-chain"], m_empty_be, results)

    def m_spec_fe_only(f):
        f.pop("design/fe/f.md")
        f["spec/fe/s.md"] = "# fe spec\n"
        return f
    run_case("46 C8 applies when only spec/fe holds a document and design/fe is empty", 1,
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
