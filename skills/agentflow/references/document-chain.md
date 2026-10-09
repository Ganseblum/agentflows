# Document delivery chain

Contract for tasks whose deliverable is a **document set** — a feature's requirement proposal,
spec, technical design, and implementation plan — rather than code. It also applies when a
feature starts from documents and the code work will follow them.

Status note (honest): this chain supersedes the earlier trade that absorbed only review
criteria and deliberately did not rebuild a template system. That trade left document quality
to per-session discipline, which is inconsistent with how every other surface of this method is
governed. The user reversed it on 2026-09-20; the reversal is recorded as D12 in this repo's
product design. Target repositories that already run their own template system keep it — this
contract is the **floor when none exists or the user asks for this method's chain**, never a
replacement for a working convention. Adjudication when they collide: a target template's
structural requirements never override this contract's quality clauses — when a template
demands what a quality clause forbids (per-row adjudication pointers, per-line authority
declarations and the like), keep the template's skeleton, collapse the conflict per the
quality clauses, and record the trim as a one-line 「结构性裁剪声明」 in the document head.

## When to use

- The user asks for 需求提案 / 规格 / 技术方案 / 实施计划 as the deliverable, or asks to
  "起文档" for a feature.
- A feature kicks off with a document phase before code (proposal → spec → design → plan →
  implement), and no target-repo convention says otherwise.

When NOT to use: the target repository already has a template system its teams follow — use
theirs, and apply this contract's **gates and quality criteria** on top; a single-doc quick
answer; documents that are evidence records (those follow the record contracts; their landing
spots are the batch directories, `issues/` and `releases/`).

## Directory layout (target repository, when no convention exists)

Two shapes, chosen by the target repository:

- **Document hub repository** — a standalone docs/meta repository (the `<project>-workflow-ai`
  pattern). The stages sit at the hub root, one directory per feature, next to the defect stream,
  the release records, the templates and the frozen archive:

```text
features/feature-<date>-<topic>/
  README.md          single entry: meta + progress board with stage gates
  proposal/          why: background, goals, scope (incl. NOT doing), principles, open questions
  spec/{be,fe,qa}/   what it must finally behave like (+ re-audit checklist of the proposal)
  design/{be,fe,qa}/ how: decision table, challenges, architecture, impact assessment, verification
  plan/{be,fe,qa}/   execution contract (follow the target repo's plan convention if any)
issues/              defects and items (numbered, board README, archive/)
releases/            release records (todo + pending-test)
templates/           copy-first skeletons
_archive/            frozen history (read-only)
index.md             the single document index
```

- **Ordinary business repository** (no separate hub): the chain stays inside the repository —
  default `docs/features/feature-<slug>/`, with the same stage skeleton.

One directory per feature. The README is the only entry point and carries the progress board
with stage gates — checkboxes move only with a document link, `N/A: reason` for skips, and
review gates checked only by the independent reviewer. A batch that needs only the entry
document and a proposal (no separate spec or design tracks) declares it in the README meta
line (`轻量模式：无 spec/design 轨`); undeclared batches keep the full-chain requirement.

File naming inside the chain: each role track is a directory at both stages, mirroring each
other — `spec/be/backend.md` ↔ `design/be/backend.md`, `spec/fe/frontend.md` ↔
`design/fe/frontend.md`, `spec/qa/acceptance.md` ↔ `design/qa/testing.md`, `spec/ui/visual.md` ↔
`design/ui/visual.md` (`design/be/` and `design/fe/` as directories are hard-required by the
linter; the rest mirror them, so a role's read scope is exactly one directory per stage).
Single-document stages keep one file: `proposal/prd.md`, `plan/execution.md`. A `be/be.md`
double-write is a naming defect — fix it before the closure pass, not in review.

## Stage skeletons

Fill-in templates with **fixed heading literals** live in
[`../templates/README.md`](../templates/README.md) — one file per stage, listed in the
manifest; copy the template, fill the
placeholders, do not rename or drop sections (the record contracts' fixed-heading approach,
applied to doc chains). Adding domain-specific sections is allowed; the template core is not
optional. A chain that declares itself in its README with the marker line 「本 feature 文档链
由 agentflow 文档链方法生成（<日期>）」 opts into the linter's structure check (C11: the
fixed design headings must be present). A stage document missing a section is incomplete, and
a section with no content says "N/A: reason".

- **proposal**: 文档信息（原文出处与版本）· 背景与目标（含本期不包含）· 产品定位与核心
  原则 · 用户与场景 · 范围决策表（含"明确不做"）· 待冻结问题台账（每项 owner + 关闭条件）。
  原始需求文本**逐字保留**并标注版本，改写发生在后续层，不在原文上。
- **spec**: §0 反审 checklist（对照 proposal 逐节挑缺口，阻塞项全关才能进 design）· 行为
  条目（陈述 → 验收口径 → 标尺）· 条目索引。验收口径必须可判定；"标尺"指会失败的
  具体检查（测试、脚本、评审门），写不出标尺的条目诚实标注。
- **design**: 0. 先说结论（问题→结论速览表）· 关键决策速览（编号 D1..Dn：结论 + 一句话
  理由 + 详见交叉引用）· 技术挑战（优先级 + 应对）· 架构图（每张图只回答一个问题）·
  **主链路 S 步骤表**（每步：调用方→承接方 / 动作输入输出 / 状态数据变化 / 失败处理 /
  观测点）· 组件负责/**不负责**表 · 核心算法（判断顺序 + 伪代码 + 代码职责落点 + 不变式）·
  **存储设计：新增表必须给字段级 DDL**（每个字段的类型/空性/默认值/注释/索引，迁移文件
  命名与回滚方式）· 详细接口设计（清单表 + 每接口请求/响应字段与错误 + 运行逻辑 +
  错误幂等状态约束表）· 验证与灰度 · 失败模式与回滚 · **影响面评估**（L0–L3 定级 +
  变更兼容性分类 + 影响面 checklist + 消费方清单与结论）·
  监控告警（编号 + 阈值）与问题定位预案（现象→首查→日志→原因→动作）· 评审前自检
  checklist。推翻既有决策时留翻案记录（改了什么结论、原前提为何不成立、何时定稿）。
- **design（前端）**: 技术挑战表 · 分层职责表（视图/hooks/store 各自边界）·
  **文件落点表**（每个新增/修改文件的精确路径，路径未核实的挂显式核实项）· **S 步骤表**
  （每步：视图层状态 / hooks 编排 / store 读写 / 服务端调用 / 成功异常去向 / 观测点）·
  组件复用边界与 **data-testid 清单**（QA 可测性）· 核心逻辑带语言级伪代码 ·
  **类型/接口契约**（请求响应的 TS/interface 定义）· **字段映射处理表**（服务端字段 →
  前端模型 → UI 展示 → 可空默认 → 非法枚举处理）· 错误重试并发表 · Mock/联调/接口未就绪
  方案 · 评审前自检。
- **design（UI 轨，可选扩展）**: 目标仓有独立设计流（设计稿评审、品牌/多站点规范）时，在
  spec 与 design 各加一份 ui 文档（`spec/ui` + `design/ui`，骨架见模板），与 fe 同构但只装
  视觉/交互/可达性内容——布局断点、token 纪律、组件视觉状态表、线框真源声明、用户迭代
  变更记录；proposal 保持单一不分角色，ui 分歧从 spec/ui 开始。linter 对 ui 轨仅做存在性与
  围栏/时效性检查（C1/C3/C10/C12–C14 会扫到 ui 文件），不做形态/密度检查（C4–C8/C11），
  ui 轨的待核实项也不进 C9 闭合——其质量靠 §0 反审 checklist、与 spec/fe 的真源声明
  （引用不复制）和 README 门禁记录兜底；启用与否在 README 元信息里声明一行。
- **线框/原型**: ASCII 线框保底（diff 友好、linter 可查）或 feature 目录内静态
  `prototype/*.html`（浏览器直开、CSS 自由；不引入 MDX/构建链）。两者择一即可，均须
  标注「结构稿，非最终视觉」。它同时是提问出口：谈不出来的问题（长什么样 / 怎么感觉）
  用一次性原型回答，**结论（哪个方案对、为什么）写回台账**——结论是交付物；原型按本条
  存放位置留作证据，不作为文档链的交付物，也不在结论落账后删除。
- **plan**: the target repo's execution-plan contract; when none exists, reuse this repo's
  hybrid shape (envelope + progress overview + task table with status/evidence write-back +
  interfaces and shared mechanisms + verification commands) per `plans/README.md`.

## Intake interview (proposal stage)

The proposal is collected through rounds, not one sitting. Model the open decisions as a design
tree: each decision branches into the decisions that hang off it. The **frontier** is every
decision whose prerequisites are already settled. Ask the whole frontier in one round — numbered,
each with a recommended answer and the reason that recommends it, worded so "yes" accepts the
recommendation — then wait for the answers before computing the next frontier. A question that
depends on a decision still open in this round belongs to a later round, not this one.

Facts are the author's job, never the owner's: anything findable in the repositories, the
environment, or the platform's documentation is looked up rather than asked, and an unresolved
lookup blocks only the questions downstream of it — keep asking the rest of the frontier. The
decisions are the owner's: put each to them and wait; never fill one in and record it as closed.
An open question that only a product owner can answer never rides into the spec as an assumption.

The interview is done when the frontier is empty — every branch visited, nothing silently
assumed — and the owner confirms the shared understanding; only then does the proposal freeze.
There is no question-count limit: the frontier is the bound, not a number. When the frontier
keeps expanding past a few rounds, the scope is too large — split the feature rather than
compressing the rounds.

**Question format.** Ask the question in one line, then at most three options — normally the
status quo, the cheapest workable path, and the recommendation — each with one line of applying
condition and price, never a pros-and-cons essay. Mark the recommendation and name the condition
under which it is the wrong pick; a fourth option appears only when it is genuinely independent,
and when no engineering preference exists the recommendation says so ("no engineering difference;
choose on product preference") instead of disappearing. The detailed comparison — compliance
citations, failure modes, rejected alternatives — belongs to the design's decision table; the
question points at it rather than restating it. Every question accepts a free-form answer, stated
once for the round: pick one; pick one and amend it; or none of them, which re-opens the branch
instead of adding options. Option letters are round-local labels — the ledger and every downstream
document write the outcome in plain words (白话（代号）).

**Challenge the answer.** When an answer conflicts with the frozen original text, an existing
glossary or spec term, or what the repositories' code actually does, put the conflict back in the
same round (「文档写 X，你说 Y，哪个为准」) and record which one won and why. An answer that
contradicts already-frozen text without being flagged is a defect, not a note.

**Ungrillable questions.** A question that talking cannot settle — what it should look like, how
it should feel — is not asked again: build the cheapest throwaway artifact that answers it (the
wireframe / prototype route above), answer it there, and record the verdict next to the question;
the artifact stays where that route stores it, as the verdict's evidence.

**Ledger write-back.** Every answer lands in the proposal's 待冻结问题台账 as a row whose closure
condition is decidable (「做了」 is not a closure condition), dated, with who confirmed it. A
question that cannot yet be phrased sharply goes to the 「未成型」 list with what blocks it, and
graduates into a row or a 范围决策表 entry as the frontier advances — it is never dropped and
never sharpened by guesswork.

## Gates

1. **Spec re-audit gate** — spec's §0 checklist registers every gap found against the
   proposal; blocking items close by fixing the proposal, being absorbed by a spec item, or
   being ledgered. A blocking item that is a **product decision** (semantics the requirement
   owner must choose, e.g. conflicting states or undefined first-fire timing) is put to the
   owner as an explicit question with a recommended default — the spec author never fills it
   in unilaterally and calls it closed — put per the intake interview above (whole frontier per
   round, facts looked up rather than asked, answer conflicts adjudicated in the round they
   arrive). Design work does not start with a blocking item open.
2. **Requirement review gate** — the independent reviewer runs the document review modes
   (proposal/PRD and spec) over the frozen candidates. Blocking findings close before design
   freezes.
3. **Design review gate** — the independent reviewer runs the design mode. After approval the
   design is frozen; later changes are design-change records with a reversal note, not silent
   edits.
4. **Plan precondition** — a plan cites frozen design conclusions; when a cited decision is
   later reversed, the plan row is corrected with a note.
5. **Design carries contracts** — the design stage includes field-level API contracts
   (method, path, request/response fields, error semantics per call) and at least one sequence
   diagram covering the main path **with its failure branches**; a design that defers all
   contracts to "after review" is incomplete. Facts blocked on unread code go on an explicit
   to-verify list with what each item blocks — they defer precision, never the contract's
   existence.
6. **链路收口通读（chain-closure pass）** — after the chain's last document lands and before
   completion is declared, a **non-author** reads the whole chain end to end and checks:
   ① 时效性引用 — a sentence claiming a target is 「待产出 / 尚未产出 / 待补充 / 待生成」 while the
   target it points at already exists is a finding; delete the claim or re-point it;
   ② 流程角色词 — session-bound process words (supervisor, 评审人缩写, TD, 本轮, 本次会话 …) never
   appear in a formal document; replace with the concrete role name or delete;
   ③ 会话材料落仓 — a session artifact a formal document cites (decision notes, recon reports)
   is archived into the feature directory before it is cited; otherwise remove the citation
   and make the body self-sufficient;
   ④ the machine-checkable part of ①② plus the 代号裸用 form is carried by
   `tools/lab/doc_chain.py` — run `python3 tools/lab/doc_chain.py <feature-dir>` (C12 时效性引用,
   C13 会话角色词, C14 代号裸用) and fix or explicitly gate every finding; a standalone session
   deliverable gets the same text-form pass via `python3 tools/lab/doc_chain.py --file <路径>`.

7. **Review landing and acceptance vocabulary** — every review round's conclusion lands as a
   record file in the batch's `reviews/` (or `reviews/<project>-<feature-slug>/` when this repo
   reviews another repository's documents); a conclusion that exists only in a plan's prose is a
   defect. A release carries a 待验证清单 (pending-test) that separates "code landed" from
   "verified"; marking 已实现 as 已验证 without the verification evidence is a defect.

## Quality density floor (machine-checked)

Born from the 2026-09-20 failure: a full chain was produced where every stage "existed" but
design carried no API contracts, no failure-branch diagrams, no wireframes, and plans carried
no file targets — and nothing failed, because nothing checked. Before declaring a chain
complete, run the deterministic linter and fix or explicitly gate every finding:

```sh
python3 tools/lab/doc_chain.py <feature-dir>
```

It fails the chain when: a stage directory is `.gitkeep`-only; the README lacks the review
gates; the spec lacks the re-audit checklist or leaves a blocking row open (☐); design/be
lacks a failure-branch sequence diagram (`alt`), a flowchart, an ER or state diagram, or the
field-level API contract table; contract interface ids are missing from design/fe; design/fe
lacks the success/failure exception matrix, at least two text wireframes, or its
flow/sequence/state diagrams; plan task rows carry neither a code-location path nor an
explicit to-verify reference; a plan lacks a branch-strategy declaration; a plan task row
stays blocking with no evidence written back; an open mermaid fence is left unclosed; a
stage document claims a target is pending while a target it points at (markdown link or
backtick code path) already exists (时效性引用失实, C12), carries a session-bound process
word (会话角色词, C13), or uses a bare letter code as a standing prose subject away from its
definition site (代号裸用, C14); or a design's open V-items are unreferenced by any plan. The
self-test fixtures pin the checker itself: `python3 tools/lab/doc_chain.py --self-test`.

Expectations beyond what the linter can parse (review-gate material, not optional): state
machines as state diagrams, one figure answers one question with a figure directory, plans
carry rollback points, core algorithms carry pseudocode.

**Depth-first scoping** — when the code facts a design needs are unread, stop before design
and demand them (read the repositories or get them from the owner). A thin full chain is a
worse deliverable than a deep half chain sitting correctly behind its gates; a to-verify list
defers precision, it never substitutes for a contract's existence.

The author is not the verifier (hard boundary 1): whoever wrote a stage document never checks
its gate. When the target repository is external to this one, review evidence lands through the
second-pass review bridge (feature-anchored `reviews/<project>-<feature-slug>/`
directory, verbatim archive per round, findings as bug records with provenance/attribution).

## Quality criteria (checkable, per document)

- Scope always includes an explicit "not doing" list with one-line reasons.
- Every decision has a stated rationale and a cross-reference; no naked conclusions.
- Impact assessment is explicit: rated L0–L3 with justification,
  per-change compatibility classification (breaking / non-breaking), what changes and what
  explicitly does not per repository/IDL/config, and a consumer list with dependency strength.
- New tables carry field-level DDL (type/nullability/default/comment/index per column);
  new interfaces carry request/response fields and per-call error semantics; frontend designs
  carry the field-mapping table and testid list.
- Responsible / not-responsible tables bound every component or role introduced.
- Open questions live in a ledger with owner and closure condition — never scattered in prose.
- Original requirement text is preserved verbatim; changelogs record who changed what when.
- **表达纪律（术语）**: no invented jargon, no compressed words whose referent depends on the
  reader (the 基线/现网 class). Fix priority is 换 > 释 > 删 — replace with the plain term
  first; an in-place one-line explanation only when no plain term exists; over-explanation is
  itself a reading-burden defect. A term only the author can resolve is a finding, not style.
  流程角色词与会话指称 (supervisor, TD, 本轮, 本次会话 …) follow the same discipline
  (换 > 释 > 删): their referent lives in the session, not the text, so they hide even better
  than domain jargon — the devices are a pre-write pass against the word list, plus review
  that reports each occurrence on citation. 两个语料新形态（2026-09-22 反馈）适用同一纪律：
  **代号裸用** —— 代号/编号（桶号、组号、字母代号）只可出现在定义处（口径表、图例、首次括注）；
  正文一律用白话状态词作主词，代号以括注成对形式伴随出现——「白话（代号）」或「代号（白话）」；
  机器豁免即此两形，无括号的并排写法不算豁免。判据：
  读者不回翻定义表、不记忆映射，能读懂任意一段正文；自造代号整个弃用（取 换 > 释 > 删 的「换」）。
  **模式词分域** —— 数据库表名、字段枚举值、内部状态字（`status='prepared'` 的 prepared、
  `agent_run` 的 Run）保留在代码、SQL、日志语境（反引号或代码块内）；散文正文用业务白话
  （「前端预建的空会话」「单次执行」），必要时括注原标识符——正文用「执行」，代码和 SQL 里
  保留 `Run`。作用域：本节纪律适用于文档链全部文档，且同等适用于会话中交付给用户的其他书面
  产物（数据分析报告、状态汇报、交付说明）——这类产物没有模板与机器门兜底，交付前必须对照
  本节做一次写前自查，单文件可用 `python3 tools/lab/doc_chain.py --file <路径>` 做机器自查
  （C12–C14 文本形态检查）；材料性交付物可指派 reviewer 评审。
- **plan ↔ design traceability**: the plan task table carries a 「关联 design 条目」 column
  (design section/decision ids) and, for frontend, a 「计划验证方式/验收标准」 column; when
  landing on existing code, a 落点校对表 (file:line anchors against the real tree) is the
  single source for code locations.
- **错误码表**: a unified table (code / fixed copy / retryable-yes-no / client action) instead
  of per-interface scatter, when a feature introduces new error semantics.
- **OQ/冻结台账**: each open question carries Owner, what it blocks (design? plan? release?),
  and a closure condition; frozen decisions are recorded with date and who confirmed.
- **契约先核实（写前）**: before writing any new interface contract, verify the platform's
  existing conventions — response envelope, error-code system (errno table / gate tests),
  auth, openapi/IDL location — and state the contract source (契约真源) once at the top of the
  design's interface section; inventing an envelope or a code table is a defect.
- **主线与克制**: every design document can answer "in what order does a reader read this, and
  what question does each section answer"; the data section opens with a lifecycle narrative
  (when each table's rows are written, and why) before DDL; interfaces are grouped by user
  journey instead of flat listings; a document running more than three numbering systems opens
  with a legend; adjudication/authority rules are stated once, never repeated per row.
- **存在性 ≠ 形态**: passing the linter's existence checks is not the form standard. An
  index-style summary table (契约总表 / 清单表) is navigation only; the form baseline for a
  field-level contract is per-field columns or a code block with per-field comments — cramming
  fields into a wide summary table is the same defect (the BUG-20260920-07 fix extended).
- **QA layer**: module acceptance blocks (M0*-AC-*), coverage mapping, and a conclusion grade
  (通过/有条件通过/不通过); marking QA "N/A" requires a stated reason pointing at where the
  acceptance criteria DO live — an empty QA layer under a progressing README is a defect.
- **文档治理反模式**（语料普查 2026-09-20 提炼，出现即缺陷）: 整表「待补充」占位常态化；
  文档头声明与实际产出脱节（如「本期不产出 QA」却存在 QA 文档）；下游文档落后上游已冻结
  结论不回写；同一结论双源并存（两处 DDL/两套错误码）不声明取舍；决策编号断档；单文件
  巨石（design 单文件超 ~1500 行应拆模块篇）；README 进度与产物脱节（空层照列步骤）；
  第三方附件整篇搬运不裁剪不标注适用范围；同一文档编号体系过载（超过三套）且无图例；
  元话语（关于文档的流程叙述）成段出现、或裁决规则逐行重复。
- Status lines are honest: `待评审` / `待验证` / `未实施` stay until the gate or evidence
  exists; strength of claim never exceeds strength of evidence.

## Role wiring

- The supervisor collects the proposal by running the intake interview (rounds over the decision
  frontier; facts resolved by the author, decisions put to the owner; answer conflicts surfaced
  and adjudicated in the round they arrive) and preserves originals verbatim.
- Spec and design may be drafted by the supervisor (single-layer document work) or delegated to
  `plan-architect` (plan layer only writes; never approves) and, for cross-layer features,
  bounded by a `technical-director` interface decision first.
- The independent `reviewer` owns all three review gates, using this repo's document review
  modes with citations to the reviewed text.
- Evidence for every round lands in the target repository when it owns the documents, and
  through the review bridge into `reviews/` when this repo is the second-pass reviewer.
- **Brief hygiene**: the delegation brief is upstream of document wording and follows the same
  expression discipline — no session-bound process words (supervisor / TD / 本轮 / 本次会话 …);
  any decision or fact material a brief cites is given as a path already archived inside the
  feature directory (archive first, cite after), never a temp path.

## Episode signal integrity (doc chains)

When a doc-chain session is captured as an improvement episode, any method-effect signal must
state its verification status: an observation without a check is recorded as unverified, never as
"no recurrence". Claims about what the runtime had installed are anchored by
`python3 tools/lab/validate.py installed` output captured during the run.
