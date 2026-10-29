"""Constants and regexes for the doc-chain linter (shared across docchain.* modules).

Check catalogue (C1–C26). The full prose lives in skills/agentflow/references/document-chain.md;
this is the quick-reference summary the linter enforces.

  C1  structure        every stage directory holds at least one real document (no .gitkeep only),
                       unless the batch README's 段落映射 table names a landing for that stage
                       (non-empty and not 「—」); when README.md is absent AND HISTORY.md is present
                       (single-ledger mode, see C24), HISTORY.md serves as the chain's entry and C1
                       does not require README.md
  C2  entry gates      README (or HISTORY.md in single-ledger mode, see C24) carries the
                       requirement-review and design-review gate entries
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
                       references are not time-checked (declared per repo scope). A row carrying no
                       explicit 核验 date opts into "trust git": its baseline is auto-collected from
                       the latest commit touching any referenced in-repo path, so it can never be
                       flagged stale — removing the manual-date drift friction.
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
  C24 history-ledger    file-presence mode (HISTORY.md present, README.md absent — not a marker
                       opt-in, unlike C15/C16/C18): single-ledger mode. HISTORY.md carries the entry
                       gates (需求评审 / 技术方案评审) and, when C22 is in scope, the 目标承接 mark and
                       table. Purely additive: a batch that also has README.md is NOT in this mode
                       (README governs unchanged; any HISTORY.md present is treated as an ordinary
                       stage document, not a ledger).
"""

from __future__ import annotations

import re
from pathlib import Path

MERMAID_KINDS = ("sequenceDiagram", "flowchart", "erDiagram", "stateDiagram")
BOX_CHARS = ("┌", "└", "├", "│")
# Repository root, used to resolve C9 code-location paths. Overridable with --root (self-test
# fixtures and validate.py's live pass pass their own root explicitly).
REPO_ROOT = Path(__file__).resolve().parents[3]

# C26 compact profile: explicit eligibility, substantive acceptance/tasks, completed evidence;
# declarations and tables inside fenced examples do not grant an exemption from full checks.

# C12 stale-time reference: claim words whose truth depends on the world, not the text — a
# line claiming one of these while pointing at a target that already exists on disk (markdown
# link OR backtick code path — the 2026-09-18 corpus used the backtick form) has rotted.
STALE_WORDS = ("待产出", "尚未产出", "待补充", "待生成")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+\.md)\)")
BT_PATH_RE = re.compile(r"`([^`\n]+\.md)`")

# C25 closure-claim (the machine-checkable half of chain-closure gate 6, 2026-10-26 audit G06).
# Gate 6 is the "read the whole chain end-to-end before declaring done" pass. It had a prose
# definition and zero machine judgments — a dead clause. C25 turns its core promise into a
# check: a document that declares the closure marker commits to having been read through, so it
# must not still contain a stale-time claim (STALE_WORDS) whose target already exists on disk —
# that residue is exactly the "claimed pending, but it's here" rot gate 6 exists to catch. The
# marker is opt-in so the linter stays safe to run over the whole repo, and unmarked documents
# are untouched (the prose definition in document-chain.md still governs them).
CLOSURE_MARKER = "agentflow 链路收口"

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
# 单一定义处（2026-10-29，收口 2026-10-26 审核记录的字形映射双拷贝）：字形→词映射在这里定义一次，
# gate/plan.py 导入同一份，不再各写一份再靠注释维持同步。docchain 是随插件单独交付的那一侧
# （RUNTIME_SUBTREES 只发 doc_chain.py 与 docchain/），所以真源放这里而不是 gate/。
TASK_STATUS_GLYPHS = {"☐": "未开始", "◐": "进行中", "☑": "已完成", "⚠": "阻塞", "—": "本期不做"}
TASK_STATUS_WORDS = tuple(TASK_STATUS_GLYPHS.values())
TASK_STATUS_ENUM = tuple(f"{glyph} {word}" for glyph, word in TASK_STATUS_GLYPHS.items())
# Bare-glyph dialect (2026-10-21 gate change, user-authorized): the labelled form and the bare
# glyph are both legal — gate/plan.py already reads the status cell by its first character and
# maps the bare marks, so C9 was the stricter of the two gates and the mismatch turned every
# bare-glyph plan table into noise (160 findings on one cross-repo corpus). A bare 「—」 counts
# as 本期不做, consistent with TASK_STATUS_GLYPHS（同一份定义）.
TASK_STATUS_BARE = frozenset(TASK_STATUS_GLYPHS)
# 两种写法都合法的合集：带词形与裸字形（C26 轻量档与 C9 共用，不再各自枚举一遍）。
TASK_STATUS_ACCEPTED = frozenset(TASK_STATUS_ENUM) | TASK_STATUS_BARE

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



