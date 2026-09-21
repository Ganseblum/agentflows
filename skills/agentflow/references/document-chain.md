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
answer; documents that are evidence records (those follow `records/` contracts in this repo).

## Directory layout (target repository, when no convention exists)

```text
docs/features/feature-<slug>/
  README.md          single entry: meta + progress board with stage gates
  proposal/          why: background, goals, scope (incl. NOT doing), principles, open questions
  spec/              what it must finally behave like (+ re-audit checklist of the proposal)
  design/            how: decision table, challenges, architecture, impact assessment, verification
  plan/              execution contract (follow the target repo's plan convention if any)
```

One directory per feature. The README is the only entry point and carries the progress board
with stage gates — checkboxes move only with a document link, `N/A: reason` for skips, and
review gates checked only by the independent reviewer.

## Stage skeletons

Fill-in templates with **fixed heading literals** live in
[document-chain-templates.md](document-chain-templates.md) — copy the template, fill the
placeholders, do not rename or drop sections (the records contract's fixed-heading approach,
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
- **线框/原型**: ASCII 线框保底（diff 友好、linter 可查）或 feature 目录内静态
  `prototype/*.html`（浏览器直开、CSS 自由；不引入 MDX/构建链）。两者择一即可，均须
  标注「结构稿，非最终视觉」。
- **plan**: the target repo's execution-plan contract; when none exists, reuse this repo's
  hybrid shape (envelope + progress overview + task table with status/evidence write-back +
  interfaces and shared mechanisms + verification commands) per `records/plans/README.md`.

## Gates

1. **Spec re-audit gate** — spec's §0 checklist registers every gap found against the
   proposal; blocking items close by fixing the proposal, being absorbed by a spec item, or
   being ledgered. A blocking item that is a **product decision** (semantics the requirement
   owner must choose, e.g. conflicting states or undefined first-fire timing) is put to the
   owner as an explicit question with a recommended default — the spec author never fills it
   in unilaterally and calls it closed. Design work does not start with a blocking item open.
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
   ④ the machine-checkable part of ①② is carried by `tools/lab/doc_chain.py` — run
   `python3 tools/lab/doc_chain.py <feature-dir>` (C12 时效性引用, C13 会话角色词) and fix or
   explicitly gate every finding.

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
backtick code path) already exists (时效性引用失实, C12) or carries a session-bound process
word (会话角色词, C13); or a design's open V-items are unreferenced by any plan. The
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
second-pass review bridge (feature-anchored `records/reviews/<project>-<feature-slug>/`
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
  that reports each occurrence on citation.
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

- The supervisor collects the proposal with the user and preserves originals verbatim.
- Spec and design may be drafted by the supervisor (single-layer document work) or delegated to
  `plan-architect` (plan layer only writes; never approves) and, for cross-layer features,
  bounded by a `technical-director` interface decision first.
- The independent `reviewer` owns all three review gates, using this repo's document review
  modes with citations to the reviewed text.
- Evidence for every round lands in the target repository when it owns the documents, and
  through the review bridge into `records/reviews/` when this repo is the second-pass reviewer.
- **Brief hygiene**: the delegation brief is upstream of document wording and follows the same
  expression discipline — no session-bound process words (supervisor / TD / 本轮 / 本次会话 …);
  any decision or fact material a brief cites is given as a path already archived inside the
  feature directory (archive first, cite after), never a temp path.

## Episode signal integrity (doc chains)

When a doc-chain session is captured as an improvement episode, any method-effect signal must
state its verification status: an observation without a check is recorded as unverified, never as
"no recurrence". Claims about what the runtime had installed are anchored by
`python3 tools/lab/validate.py installed` output captured during the run.
