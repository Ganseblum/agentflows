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
replacement for a working convention.

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
  design/            how: decision table, challenges, architecture, blast radius, verification
  plan/              execution contract (follow the target repo's plan convention if any)
```

One directory per feature. The README is the only entry point and carries the progress board
with stage gates — checkboxes move only with a document link, `N/A: reason` for skips, and
review gates checked only by the independent reviewer.

## Stage skeletons

Keep skeletons as section lists, not prose templates. Each stage states its sections; a stage
document missing a section is incomplete, and a section with no content says "N/A: reason".

- **proposal**: 文档信息（原文出处与版本）· 背景与目标（含本期不包含）· 产品定位与核心
  原则 · 用户与场景 · 范围决策表（含"明确不做"）· 待冻结问题台账（每项 owner + 关闭条件）。
  原始需求文本**逐字保留**并标注版本，改写发生在后续层，不在原文上。
- **spec**: §0 反审 checklist（对照 proposal 逐节挑缺口，阻塞项全关才能进 design）· 行为
  条目（陈述 → 验收口径 → 标尺）· 条目索引。验收口径必须可判定；"标尺"指会失败的
  具体检查（测试、脚本、评审门），写不出标尺的条目诚实标注。
- **design**: 0. 关键决策速览（编号 D1..Dn：结论 + 一句话理由 + 详见交叉引用）· 技术挑战
  （优先级 + 应对）· 架构图（每张图只回答一个问题）· 组件负责/**不负责**表 ·
  爆炸半径声明（改什么、明确不改什么）· 验证与灰度 · 失败模式与回滚。推翻既有决策时
  留翻案记录（改了什么结论、原前提为何不成立、何时定稿）。
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
stays blocking with no evidence written back; an open mermaid fence is left unclosed; or a
design's open V-items are unreferenced by any plan. The
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
- Blast radius is explicit: what changes, what explicitly does not, per repository/IDL/config.
- Responsible / not-responsible tables bound every component or role introduced.
- Open questions live in a ledger with owner and closure condition — never scattered in prose.
- Original requirement text is preserved verbatim; changelogs record who changed what when.
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
