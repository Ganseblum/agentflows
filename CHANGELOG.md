# Changelog

## 0.7.5 — 2026-09-18

Audit-driven hardening: gate, evaluation identity, scoring, role/loop contracts, episode/release
consistency, and a first local read-side for `records/`. Method-level change, no behavior change
with an instrumented business task; `measurement: none`.

- **Gate now runs and is fail-closed.** `.github/workflows/validate.yml` runs
  `isolation.py check-diff` from a trusted checkout against a frozen base revision and protects
  `.github/`; `isolation.changed_paths` switched to NUL-delimited Git output so spaces,
  quoting, newlines and non-ASCII paths no longer evade the protected-prefix check, and the
  checker refuses to run when its own root is the candidate or nested with it.
- **`validate.py` fail-closed.** `artifacts` errors when `records/` is missing or empty; the
  records walker rejects hidden entries except `.DS_Store`; the regression-suite gate now parses
  the final `Ran N tests` summary, rejects any `skipped > 0`, and keeps the floor. Added
  `tests/test_record_store.py` to the pinned test list and `REQUIRED_PROTECTED_PATHS`.
- **Deterministic policy/adapter fixes.** `policy.main` returns non-zero on `reject`; the Codex
  and Claude adapters now parse the host JSON first, inject `latency_ms` once, validate once, and
  convert non-object payloads into structured failures instead of tracebacks; `eval_runner` keeps
  `suite` inside the repository and unifies the baseline/candidate case-coverage key to
  `(case_id, slice, holdout)`.
- **Business scoring can no longer be gamed.** `seed_grader` rejects path traversal and
  off-target findings, caps total findings and per-field length, dedupes findings, and enforces a
  per-target-document unmatched cap; findings outside `target_docs` are recorded as `off_target`
  and do not affect recall. `evals/business/README.md` documents the anti-gaming constraints.
- **Episode/release integrity and read-side.** Episode schema gained `revision`, `run`, `claims`
  and `evidence`; release schema added a structured `measurement` (`status` + `basis` +
  `business_case_ids`) and tighter promotion constraints so a `promote` requires `better` and an
  approval, while measurement-`none` releases cannot be misrecorded as verified improvements. New
  `tools/lab/record_store.py` gives a disposable SQLite FTS5 read-side over `records/`; Intake is
  documented to retrieve with it before briefing.
- **Role/loop contract convergence.** Routing, `roles.md`, `docs/agent-roles.md` and the SKILLs
  now agree that a Supervisor-only small change still passes a non-waivable independent reviewer;
  `test-executor` distinguishes scripted headless browser automation from host-interactive
  browser automation; worker briefs and results carry `task_id`/`baseline_revision` and a
  separated `status: partial` semantic; `plan-architect`/`test-planner`/`bug-recorder` got the
  `Edit` their contracts require; missing improvement-role bindings were added; improvement
  SKILL/roles name the Supervisor as the sole writer of plan status/evidence during execution.

## 0.7.4 — 2026-09-18

Wording-cleanup pass, closing the reviewer residuals carried from 0.7.2/0.7.3:

- `records/README.md` episode row now states the widened trigger — required for every material
  change since 0.7.2, review round-trips included — the last doc surface still carrying the
  old improvement-loop-only framing.
- `mock/README.md` episode row synced to the same framing (material 改动必写，含
  `review_roundtrips`).
- `PLAN-BUSINESS-EVAL-001` frontmatter `plan_version` aligned with its latest revision line
  (0.2.3 → 0.2.5); no task-row or content changes.
- Docs-only; no code, schema, seed, or case changes. Measurement state unchanged (still
  U-01-blocked).

## 0.7.3 — 2026-09-18

Jargon-discipline criterion widened from user feedback: the 术语歧义 (terminology-ambiguity)
category now explicitly covers the high-frequency variant — habitual compressed terms
(基线 / 现网 class) whose referent varies by reader and drifts with time — not only invented
undefined terms. The fix discipline is ranked **换 > 释 > 删**: substitute the concrete object
first (commit, version, environment, value — usually shorter, zero reading burden); a one-line
in-place definition only when the term must stay; drop the word and state the behavior
otherwise. Over-explaining counts as a reading-burden defect. Seed-planting note updated for
the variant: the anchor is a unique existing fragment of the target text, no planting needed.
Case and seed files unchanged; new variant seeds land with the S phase once U-01 clears.
Gate change (protected path `evals/business/README.md`), human-authorized in session;
measurement state unchanged (instrument built, not yet run — U-01/U-08 still gate S).

## 0.7.2 — 2026-09-18

Divergence-auditability slice: mid-flow review disagreement gets a durable, machine-checked
carrier, and records get a renderer-safe visual layer. **Gate change, human-authorized in
session**: `skills/improve/references/episode.schema.json` (inside `protected-paths.txt`)
gains one optional field — no other gate path is touched.

- **Episodes carry review round-trips.** `review_roundtrips[]` (at / reviewer / decision /
  finding / resolution / evidence_ref, `additionalProperties: false`) records every
  independent-review round — the rounds that returned `changes_requested`, what the
  disagreement was, how it was resolved. The episode trigger is widened: every **material**
  change (anything that opened the review gate) lands an episode before the session ends, not
  only improvement-loop candidates. Mid-flow review divergence stays auditable after the
  conversation is gone, not only the final verdict.
- **Visual annotation conventions** (`records/README.md`): GFM callouts with a fixed
  vocabulary — `> [!IMPORTANT]` 未决分歧/阻塞, `> [!WARNING]` 残余风险/已知缺口, `> [!NOTE]`
  口径澄清 — plus ` ```diff ` fences for before/after or A/B comparisons. Fixed literal
  prefixes keep callouts greppable; frontmatter enums and fixed sections stay the
  authoritative semantic layer. Inline HTML colors and custom `[!...]` alert types are
  rejected (not renderer-portable, pollute the greppable layer).
- Examples demonstrate the conventions: the bug-record example gains a `> [!WARNING]`
  residual-risk callout, the plan example gains `> [!WARNING]` (external dependency risk) and
  `> [!NOTE]` (non-blocking open item) — mirrored into `mock/`.
- Docs synced: `docs/agent-roles.md` (episode trigger + annotation conventions),
  `records/episodes/README.md` (field list + trigger), both SKILL.md copies (step 10).
- Measurement: none — documentation conventions plus one optional schema field; no behavior
  change with an instrumented business task.

## 0.7.1 — 2026-09-18

Absorption pass on the testing roles, from business-side admission standards and an existing
YAML-driven Playwright suite (the material is summarized in EP-20260918-001): the case library
now speaks the target engine's vocabulary, execution validates collection before a browser
opens, and failures are classified before anything reaches the bug chain. Method-level change,
no gate change — `schemas/`, `tools/lab/`, and the pinned tests are untouched.

- `test-planner` gains four disciplines: an **admission check** before case authoring (missing
  routes, expected results, prerequisites, roles/data are registered as numbered gaps in
  `## 流程疑点` — never invented, never dressed up as a weaker assertion); **target-engine
  alignment** (elements referenced by registry alias, actions and expected results in the
  engine's split, reusable preconditions referenced not copy-pasted, environment values as
  variables, project-declared file names only); **session ordering** (logout / clear-cookie
  cases last or isolated, never mixed into a logged-in session); and a **capability-boundary
  rule** (a behavior outside the framework's documented capability is marked TODO /
  不可自动化 with the reason). A delivery **self-check list** mirrors what the reviewer will
  check.
- `test-executor` gains target-runner adaptation and failure triage: **collection dry run
  first** (`--collect-only`-style — catches broken references before a browser opens, and a
  case directory without a registry entry is silently never collected; the suite is registered
  before its case files exist); **evidence in the runner's order of resolution** (run report →
  failure screenshots → logs, citing the specific artifact per row); a registry gap is recorded
  in the conclusion instead of inlining a raw locator; and every failure is **classified before
  filing** — product defect → bug chain; case/registry drift → registry update + rerun;
  environment/data → `blocked` — each naming the fix location so the bug pool stays free of
  noise.
- `records/tests/README.md` gains the **Target-project mapping** section: the alignment chain
  (frontend test ids ↔ locator registry ↔ case library ↔ engine cases ↔ flows ↔ suite registry
  ↔ environment config) with, per link, what must agree and where a change lands — the same
  table that routes failure repairs.
- `docs/agent-roles.md` (Chinese mirror) records the alignment chain and failure triage.
- `measurement: none (method-level change, no instrumented business task)` — same class as
  0.7.0; not a verified improvement.

## 0.7.0 — 2026-09-18

Automated-testing capability slice — user-visible features can now be tested end to end by the
method itself: a case library with executable steps and boundary coverage, execution with
evidence, failures filed into the bug chain, and a flow-reasonableness review over the run.
Triggered by explicit user feedback (EP-20260917-003): real browser automation (host browser
MCP / Playwright), credentials injected at runtime, detailed boundary cases, run reports, and
smoke/e2e grading.

- New `test-planner` role (`agents/test-planner.md`): designs the case library at an explicit
  `records/tests/<project>-<feature-slug>/plan-*.md` path — case registry with levels
  smoke/e2e/api/boundary and priorities P0–P3, per-case step tables whose assertions are
  observable by an operator who never read the code (element text, navigation, whether a
  network request fires), a boundary-coverage matrix (empty input, invalid format, overlong
  input, special characters, duplicate submit, expired session, absent data, network failure —
  uncovered classes declared, never silent), and `## 流程疑点` registering behaviors the spec
  does not define. Credentials appear only as an injection method, never a value.
- New `test-executor` role (`agents/test-executor.md`): executes an approved plan — scripted
  automation first (Playwright headless), API cases via commands, and host-browser UI steps
  compiled into a step script the supervisor performs in the main conversation (browser
  automation is main-conversation-only on Claude Code and ZCode), judging pass/fail only from
  raw evidence returned. Writes one `run-*.md` per round with per-case results (fixed enum
  `pass / fail / blocked / not-run`, evidence required on fail/blocked rows), flat summary
  counts, a decision, and reproduction-ready findings. `Edit` is disallowed: run records are
  append-only history. Smoke first; a broken build stops the full set.
- New record class `records/tests/` (contract: `records/tests/README.md`): feature-anchored
  directories holding the plan (revised in place, `test_version` bump) and per-round run
  records pinning the plan id/version and the `target_revision` actually tested. Run
  `findings` / `flow_findings` reference existing bug records; the run record's raw evidence
  doubles as the review gate's end-to-end-path evidence.
- New schemas `schemas/test-plan.schema.json` and `schemas/test-run.schema.json`. The
  validator wires the class in: layout and filename↔id agreement, case-registry parsing
  (unique `TC-*` ids, level/priority enums, `case_count` equality, one detail heading per
  case), run result-table checks (enum, evidence on fail/blocked, ids resolve in the plan's
  registry, summary counts equal the table, `decision: pass` requires zero fail/blocked),
  plan resolution in the same feature directory, full-case accounting when the run pins the
  current plan version, and findings resolving into the bug pool. Valid plan/run examples live
  under `examples/test-records/`; the result-enum negative under `examples/invalid/`.
- Role/method augmentations: `plan-architect` now requires a test-design task (assigned to
  `test-planner`) in every plan with user-visible behavior and references the smoke set in
  验证命令; the `reviewer` gains the *Flow reasonableness (test evidence)* specialist mode
  (undefined timeout/duplicate-submit/interruption paths, cross-surface error-message
  consistency, unreachable states — "should have failed but did not" is a finding); the
  agentflow skill gains the *Automated testing* workflow section and the two host-binding role
  lists now name both new agents; `roles.md` and the Chinese mirror (`docs/agent-roles.md`)
  carry the routing rows and profiles.
- Pinned regression tests grow to 118 (10 new): the shipped examples pass, the negative is
  rejected, and the plan/run invariants are exercised per rule (case_count mismatch, summary
  mismatch, unknown plan, evidence-less fail row, out-of-registry row, missing case coverage,
  pass-decision-with-failures).
- Gate change, human-directed: `schemas/` (two new record contracts), `tools/lab/validate.py`,
  and `tests/test_lab_contracts.py` were edited to land this batch, with the user's explicit
  approval in-session (0.6.0 precedent).
- Independent evaluation and release decision: an independent evaluator verified all eight
  acceptance criteria against the files (verdict `neutral` — real, internally consistent, and
  gate-enforced exactly as claimed; unmeasured by policy), and the release governor returned
  `promote` with conditions (measurement:none carried unchanged; reinstall gated on user
  approval; follow-ups before the next method-level release). Post-review follow-ups landed in
  this entry: the smoke-first ordering sentence in the agentflow skill's Automated testing
  section, the case detail-heading scan narrowed to the `## 用例` section with an
  empty-heading guard, and the executor's `scratch/` directory declared in the tests contract
  table.
- `measurement: none (method-level change, no instrumented business task)` — `evals/` has no
  login-flow slice; the release must not be described as a verified improvement. A seeded
  business slice (a snapshot with a planted validation defect) is the natural future
  instrument for this capability.

## 0.6.0 — 2026-09-17

First measurement surface for method-level changes — changes that alter how roles behave inside
business repositories and have no regression signal in `evals/public/`. Three document-review
cases run against a pinned snapshot of a real enterprise repository that is made read-only when
seeded and re-checked after every host call; a deterministic grader scores the agent's findings
against defects planted before the run. The public surface carries only sanitized briefs and
abstracted seed lists — the snapshot, the seed patch, the symbol-to-path mapping, and all raw
results stay local.

- New `evals/business/` suite: `BT-001` seed-defect document review, `BT-002` internal
  contradiction, `BT-003` cross-document consistency, each with a sanitized brief under `inputs/`
  and an abstracted seed list under `seeds/`. A seed counts as a hit only when one finding names
  the seeded document and its text contains one of the seed's literal anchors.
- New `skills/improve/references/business-case.schema.json`: the eval-case contract plus
  `target_id`, `target_pin` (full sha), `target_docs`, `seeds_ref`, `findings_contract`, and
  `grading.min_seed_recall`. The target fields are structure-checked only, deliberately — the
  public validator must not depend on the private snapshot being present.
- New `tools/lab/seed_grader.py`: deterministic offline scoring into `hits` / `missed` /
  `unmatched`; `accepted` is overwritten as "seed recall at or above the case threshold" and
  `escaped_defects` as the missed-seed count. Unmatched findings are recorded, not penalized. An
  unknown match strategy or a missing/unparsable findings artifact fails closed (exit code 2)
  instead of scoring zero.
- Runner and adapter business surface: `eval_runner.py --business-root`; the host adapter's
  business request branch requires the six business case fields, one shared pin, and a
  `workspace-write` permission profile (a read-only profile cannot write the findings artifact);
  a real run also requires `--seed-patch`, checks the snapshot HEAD against `target_pin`, requires
  the seed patch to be cleanly reversible, and re-checks the snapshot file set and the `git diff`
  digest after every host
  call. `isolation.py layout_errors` gains an optional fourth position for the snapshot root.
- `validate.py` wires `evals/business/` into the schema map and `validate_business_evals`, and
  `tools/lab/seed_grader.py` joins the protected gate list. The pinned test file gains 39 tests
  (58 total).
- Gate change, human-directed: `validate.py`, `eval_runner.py`, `host_adapter.py`,
  `isolation.py`, `protected-paths.txt`, and `tests/test_lab_contracts.py` were edited to land
  this batch.
- Post-review follow-ups (human-directed): the judgement words that decide whether a gate
  applies are now defined in the agentflow skill (`small change`, `risky work`, `the same
  cause`) and mirrored in `docs/agent-roles.md`; the improvement episode schema constrains
  `provenance` (required `carrier` and `sanitized`, no extra keys); `validate.py`'s duplicate
  `docs` CLI choice is removed; a GitHub Actions workflow runs the deterministic checks on
  push and pull requests; two diagnostic defects are fixed — `run_codex` now reads the result
  file by path (its `NamedTemporaryFile` handle had no `read_text`, so every codex run failed),
  and a failed claude invocation now reports the error from its stdout JSON instead of the
  harmless stderr warning that used to mask it; a business run also passes
  `--add-dir <snapshot root>` (resolved to an absolute path) because claude's `--print` mode
  scopes tool file access to the working directory, so the first smoke attempts could not read
  the snapshot at all — covered by two argv regression tests and a host-platform-facts row.
- Development release: no baseline/candidate evaluation evidence. The business smoke run is
  blocked on three open P0 items — trusted endpoint (U-01), measured permission profile (U-02),
  snapshot placement (U-03) — so the `measurement: none` transitional state for method-level
  changes is **not** retired by this release. The installed host snapshot lags the source until
  the marketplace is refreshed and the plugin is reinstalled.

## 0.5.2 — 2026-09-17

Self-audit of the 0.5.0/0.5.1 surface: one silent gate gap, one dead code path, five stale
wording sites, and two stale documentation surfaces fixed.

- Silent gap (the important one): the invalid plan example was **never exercised** — the
  examples checker matched a lowercase `plan-` prefix while the file is `PLAN-INVALID-002.md`,
  and the combined "invalid sets required" assertion was satisfied by the bug-record negative
  alone. The match is now case-insensitive, and a missing valid or invalid plan example fails
  the check outright. Verified on a throwaway copy: making the negative example valid yields
  "expected invalid example to be rejected", deleting it yields "a valid plan example and an
  invalid plan example are both required". Pinned regression test added (19 total).
- Dead code: `schema_for` still mapped `examples/invalid/plan-*` to the plan schema after plan
  validation moved to the Markdown path; removed.
- Stale wording swept (the `parallel lanes` era): plan-architect's description, the SKILL
  planning paragraph, the roles-reference plan profile, the Chinese mirror's
  `shared_mechanisms[]` sentence (now the 接口与共享机制 table with registration points), and
  the plans README structure block — which now also names review gates (评审门) inside
  `## 接口与共享机制`.
- Stale surfaces: records/README's plan query used `jq … records/plans/*.json` (JSON era) and
  now greps the Markdown frontmatter; tools/lab/README documents that `artifacts` covers all
  five record kinds and describes the `docs`, `report`, and `recurrence` targets.
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.5.1 — 2026-09-17

Document review modes: absorb the *quality criteria* of the proposal/spec/design pipeline, not
its template system (user question: should spec/design/proposal be absorbed — and how to make
it convenient in later use). The bridge already reviews externally authored documents; what was
missing was a fixed, per-document-type checklist.

- `agents/reviewer.md` gains **Document review modes** for external documents, each grounded in
  the reviewed system's own template requirements plus this repo's disciplines:
  - *Proposal / PRD*: in/out scope written and checkable (an unfalsifiable out-of-scope claim
    is a defect), decidable success criterion, concrete scenario split, explicit not-doing
    list, explicit link to existing capability.
  - *Spec*: frozen field semantics / boundary rules / exception branches; stated adjudication
    rules (which result wins, what forces recomputation, what history may not be used to infer
    eligibility); defaults and degradation; boundary scenarios (just-succeeded / just-expired /
    empty / invalid enum / dirty history); upstream gaps registered and blocking entries closed
    before the spec counts as frozen.
  - *Design*: the design-completeness artifacts (timing step table, exception matrix with the
    retry four-part rule, release order × rollback, impact grading), contract compatibility +
    idempotency/concurrency/transaction boundaries, observability, and acceptance criteria
    pointing at the spec/QA source instead of a second invented set.
  - *Plan*: this repo's own contract — no external mode.
  Every item passes only with a citation to the original sentence or `path:line`; a "missing"
    item is itself a finding when the checklist requires it.
- The bridge workflow (`records/reviews/README.md`, SKILL step 2, roles reference) now names
  the mode selection: the brief names the document type, the reviewer applies the matching
  checklist. The demo review mock shows the applied mode line.
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.5.0 — 2026-09-17

Plan contract redesign: the execution plan becomes a **Markdown hybrid** (user chose option A
after comparing the aiwork-workflow-ai Markdown plans with the agentflow JSON contract — the
former reads better for humans, the latter validates better; the hybrid keeps both). No
migration was needed: `records/plans/` held no real plans.

- New plan shape `records/plans/<plan_id>.md`: frontmatter envelope (`plan_id` / `plan_version`
  / `status` draft→proposed→approved→superseded / `objective` / timestamps / `superseded_by`)
  plus a body board absorbed from aiwork's plan discipline — `## 进展概览` (one progress line
  + a three-audience overview table: 业务侧解读 / 技术侧解读 / 交付效果 + 我们在哪/下一步/
  阻塞), `## 任务清单` (task table with ID/任务/优先级/代码落点/依赖/状态/证据回写 and
  `### 未决项`), optional `## 接口与共享机制` (contracts + exception matrix + release order
  × rollback points), `## 验证命令`.
- Machine assertions kept and extended (`validate_plan_markdown`): filename = plan_id; task IDs
  unique; 依赖 references resolve and are acyclic; task statuses are the fixed enum
  ☐ 未开始 / ◐ 进行中 / ☑ 已完成 / ⚠ 阻塞 / — 本期不做 (free text rejected); **a blocking
  未决项 that is not closed blocks `status: approved`** (aiwork's gap-registration gate,
  absorbed); required sections exist. The old JSON invariants (work-package cycles, lane
  coverage) are replaced by the task-table equivalents; the old `validate_plan_invariants`
  removed.
- Progress write-back discipline (aiwork's board model): the plan is the progress surface —
  after a task completes only its 状态 and 证据回写 columns change (minimal diff); completed
  rows are never rewritten. The session-death resume protocol now reads this board.
- Examples replaced: a realistic positive plan (`PLAN-DEMO-SHARE-001`, modelled on the real
  对话分享 plan density) and a multi-defect negative (`PLAN-INVALID-002`: cycle, duplicate ID,
  illegal status, open blocking decision). Pinned tests 18 (two new: envelope enum/superseded,
  task-table rejections). `plan-architect` rewritten for the hybrid; plans README, records
  index, SKILL resume note, and the Chinese mirror updated.
- Gate change, human-directed: plan schema rewritten, plan validation rewritten, examples
  replaced. Verified by unit tests and a throwaway-copy experiment (cycle + illegal status +
  open blocking decision each rejected in isolation).
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.4.2 — 2026-09-17

Three workflow-policy gaps filed as BUG-20260917-01/02/03 by a sibling session working in the
`infinite-canvas` repository, fixed here as user-directed rule patches (the fixes the records
themselves propose):

- **Integration needs authorization** (BUG-20260917-01): hard boundary 3 and the SKILL control
  section now cover `git merge` / `rebase` / `cherry-pick` and pulling remote changes into a
  shared branch — per-instance user authorization, because which method and which conflict side
  wins is the user's decision. The default on a rejected push is a read-only report
  (`fetch` + `log`/`diff`: added commits, changed files, overlap); choosing an integration
  method and pushing is not the supervisor's call.
- **Git-layer write isolation** (BUG-20260917-02): the delegate step notes that disjoint files
  do not isolate commits/rebases/pushes — parallel writers get separate branches or worktrees,
  one writer holds a branch at a time, and a writer finding its target occupied (uncommitted
  edits from another session, new commits on the branch) stops and reports.
- **Status claims need repository evidence** (BUG-20260917-03): intake now requires status
  conclusions (what is done, what is next) to be calibrated with `git fetch` plus
  `log`/`status`, carrying the evidence command — session memory is not a repo fact and goes
  stale the moment another writer pushes.
- The three records moved `open` → `fixed-pending-review` with `regression_status: not-run`
  (documented: rule-text changes have no executable regression surface; an independent
  reviewer must name the check that would prove the constraint holds before `verified`).
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.4.1 — 2026-09-17

Documentation-drift gate and the improvement loop's missing fuel, both long-standing P1 items.

- New `validate.py docs` target (in `all`, now eight checks): asserts that every agent file's
  frontmatter name equals its filename; every `agentflow:<role>` referenced by a SKILL resolves
  to an agent file; every `schemas/*.schema.json` path named anywhere in
  docs/records/skills/agents/README exists; the Chinese mirror's schema-reference set matches
  `contracts.md`'s. It caught a real drift on its first run (hard boundary 6 did not name the
  new record schemas; fixed by rewriting boundary 6 to cite all four record-contract paths).
  Pinned test asserts the current tree passes; throwaway-copy experiments verified all three
  rejection paths.
- Minimal episode persistence (P1's first item, closing the "improvement loop has no fuel"
  gap): `records/episodes/<YYYY-MM-DD>/<EP-id>.json` — the supervisor captures a task's final
  decision record (objective, outcome, claims, review decision, cost) before the session ends.
  The contract is **reused** from the improvement loop's protected
  `skills/improve/references/episode.schema.json` rather than introducing a parallel carrier
  (an "extension inventory" catch on my own first draft). The validator compiles episodes
  (schema, filename = episode_id, ids globally unique); SKILL step 10 now names the exact
  destination; a first real episode records the 0.4.0 aiwork-absorption session.
- `validate.py report --project/--status/--provenance`: filters without remembering column
  numbers.
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.4.0 — 2026-09-16

Absorbed from a systematic review of `aiwork-workflow-ai` (its design templates, issue records,
and spec-first workflow), at explicit user direction — as disciplines and contracts, not
templates, keeping this repo's single-plan-contract shape.

Batch 1 — design completeness and issue-record merits:

- New "design completeness for material features" discipline in `contracts.md` (and the
  plan-architect / technical-director prompts, plus the Chinese mirror): (1) critical-path
  timing with the step table as the baseline and a mermaid sequence diagram only as a companion
  that must agree (disagreement makes the diagram the defect; process steps never pile into the
  architecture diagram); (2) an exception matrix per critical path — timeout, duplicate request,
  state conflict, callback failure — each row answering detection, handling, retry
  owner/count/backoff, idempotency precondition, user-visible result; a retry without those
  specifics, or a blanket "fail-safe fallback", is a defect; `N/A` with reason, never blank;
  (3) a release order with every step paired to its rollback point. These complement the
  existing implicit-behavior check (that one guards cross-cutting mechanisms; these guard the
  declared flow).
- `closure_criteria` (required for `verified`): a measurable closure condition — named metric,
  log absence, or check output; "works as expected" is not a criterion.
- `fix_revision`: where the fix landed (commit/PR/release, repo-qualified when cross-repo).
- `## 变更记录` body convention: one appended line per state transition, so history survives
  the single `updated_at` timestamp.
- Gate change, human-directed: two schema fields + the verified conditional; pinned tests
  extended (closure criteria required, verified sample updated).

Batch 2 — the external-document review bridge:

- New record subtree `records/reviews/<YYYY-MM-DD>/<project>-<slug>/` (contract
  `schemas/review.schema.json`): `review.md` plus verbatim snapshots of the reviewed documents
  in `archive/`, with `source_revision` pinning the target repository's commit.
- The bridge workflow (SKILL "Second-pass review of external documents", routing-table row,
  `records/reviews/README.md`, Chinese mirror): archive first, review the snapshot, file each
  finding as a bug record, then cross-link. `provenance` splits the upgrade loops — `external`
  findings are the evidence pool for upgrading the target system's rules/templates (the stated
  use case: `aiwork-workflow-ai`), `agentflow` findings upgrade this repo's review contract;
  `fix_revision` closes the loop when the target system's upgrade lands.
- Gate change, human-directed: validator walks `records/reviews/` (review records validated;
  archived evidence copies accepted as-is), cross-checks that every `reviewed_docs` entry
  exists on disk and every `findings` bug_id exists under `records/bugs/`; the review schema
  joins the required protected set.
- Review layout is feature-anchored, not date-anchored (user correction before release): one
  directory per reviewed feature (`<project>-<feature-slug>`), one `review-<YYYY-MM-DD>-<NNN>.md`
  file per round (filename equals review_id), one `archive/<date>-<NNN>/` snapshot subdirectory
  per round — the same feature may be reviewed repeatedly, and rounds stack in one directory
  instead of scattering across dates.
- Self-contained references (user-raised portability gap: records given to someone without the
  other repository must stay readable): a `files` entry either resolves inside this repository
  or is repo-qualified as `<repo>@<revision>:<path>`; bare paths that exist nowhere are rejected
  by the validator. A repo-qualified reference is an address, not evidence: the record body
  must embed the decisive fragment (fenced code block for code, blockquote for document
  passages) and cite the qualified address next to it — both enforced by the validator, with a
  pinned regression test. For findings from a second-pass review, the preferred `files` entry
  is the archived snapshot inside `records/reviews/.../archive/` (the verbatim copy already
  lives in this repository); whole-document copies are the review archive's job, records embed
  fragments.
- Body-reference rules (user direction: ban dangling references everywhere, records must carry
  real evidence): in plain prose, every doc/code path is the record's own claim — it must
  resolve in this repository (or next to the record) or be repo-qualified. Fenced blocks and
  inline code are quotations — verbatim evidence including historical paths — and are exempt.
  Personal absolute paths (`/Users/...`, `~/...`) are banned outright; URLs cannot be validated
  and are supplementary at most, never the evidence. Enforced by `validate_body_references` on
  bug records, review records, and recurrence ledgers; the existing corpus passes with zero
  false positives (its three historical paths live inside quotations and stay untouched);
  pinned tests cover rejection, exemption, and resolution.
- Self-review round on the same batch fixed four defects before release: the body-path
  pattern now recognizes CJK path tokens (the dominant form in the aiwork use case) while
  still ignoring version-like slashes (`0.3.4/0.3.5` is not a path); the review walker only
  treats `review-*.md` at the feature-directory level as records (an identically named
  snapshot deeper under `archive/` was previously mis-validated); `review_id` is now globally
  unique across reviews; and `review_id`'s date must match `recorded_at`. All verified by
  pinned tests and throwaway-copy experiments.
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.3.9 — 2026-09-16

Provenance: a required field that answers "is this Agentflow's problem", at explicit user
direction. Without it, a defect produced by the agent's own ad-hoc plan or analysis could be
consumed by the improvement loop as evidence about Agentflow.

- New required frontmatter field `provenance`: `agentflow` (Agentflow's own surface — clause,
  role, gate, evaluation, brief discipline, `tools/lab/` tools), `session-artifact` (ad-hoc
  session output no clause covers — the agent's own plan, analysis, decision, or code),
  `user-input`, `external` (pre-existing product code, host, tool, environment), `undetermined`
  (the missing evidence must be named). All six records and both examples migrated.
- Schema-enforced contradiction guard: `attribution: workflow_policy` or `role_prompt` forces
  `provenance: agentflow` — an Agentflow policy cannot own a defect whose carrier was not
  Agentflow's.
- Improvement-loop filter (improve SKILL steps 2 and 4, feedback-analyst prompt): only
  `agentflow` records are candidate evidence about Agentflow itself; `session-artifact`,
  `user-input`, and `external` are context and counterexamples; `undetermined` must have its
  provenance resolved before entering a cluster.
- `validate.py report` appends provenance as column 7; existing column positions are unchanged
  (`cut -f5` still selects error kind). Filter with
  `python3 tools/lab/validate.py report | awk -F'\t' '$7=="agentflow"'`.
- Gate change, human-directed: schema field, guard rule, report column, and pinned tests (the
  required field, the contradiction rejection, and non-Agentflow values accepted). Negative test
  on a throwaway copy: a record missing `provenance` is rejected; `attribution: workflow_policy`
  with `provenance: external` is rejected; `session-artifact` with an unrelated attribution
  passes.
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.3.8 — 2026-09-16

Recurrence tracking and P-grade severity, at explicit user direction. A bug and its later
relapse had no machine-visible link, and "which upgrade absorbed this class, and has it come
back since" lived only in prose.

- `severity` now uses priority grades — `P0` (critical: data loss, security, release blocker),
  `P1` (high), `P2` (medium), `P3` (low) — replacing low/medium/high/critical; `validate.py
  report` prints the grade directly. All six records and both examples migrated.
- New recurrence ledger: `records/bugs/recurrence/<class_id>.md` (contract
  `schemas/recurrence.schema.json`) — one file per failure class that recurred or was
  consolidated; plain single-occurrence bugs get none. `status` is `unconsolidated`（未归纳升级）
  or `consolidated`（已归纳升级）with `consolidated_in` naming the absorbing release;
  `occurrences` lists record ids, and versions are read from the records themselves. Records of
  a class carry `class_id` + `occurrence`.
- The tier is derived, never hand-marked: `validate.py recurrence` prints `single` / `recurred` /
  `escalated`, where `escalated` means an occurrence recorded on a version newer than the
  consolidation — the aggravated marker that triggers the improve-loop escalation (re-consolidate
  with an eval case; the improve SKILL treats the ledger as a first-class episode source).
- Gate change, human-directed: the validator walks and cross-checks the ledger — referenced
  records must exist, a record with `class_id` must have its ledger and be listed, occurrence
  numbers must be unique, and a consolidated class's records must carry `agentflow_version`.
  `schemas/recurrence.schema.json` joins the required protected set; pinned tests extended
  (severity grades, consolidation requirement, filename/class_id agreement). Negative tests on a
  throwaway copy: legacy `severity: high` rejected; ledger-less `class_id` rejected; unlisted
  occurrence rejected; consolidated occurrence without a version rejected; a structurally valid
  post-consolidation occurrence reports `escalated`.
- First ledger backfilled: `unverified-behavior-claims` (consolidated in 0.3.4 via hard boundary
  12, zero recurrences since).
- Roles and docs: `bug-recorder` (grades, ledger duties, consolidation written only from an
  actual release), `bug-investigator` (checks the ledger first, proposes class + occurrence),
  both records READMEs, the roles reference, and the Chinese mirror.
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.3.7 — 2026-09-16

Record language convention, executed at explicit user direction. The archive mixed languages
inside each file (English titles over Chinese bodies) and the required body headings were English
literals; records produced elsewhere had already chosen Chinese titles.

- New convention (`records/README.md`): the machine layer stays English/ASCII — frontmatter keys
  and enum values, slugs, ids, paths, `project`. Body section headings are fixed literals too, in
  Chinese — `## 现象`, `## 根因`, `## 修复`, `## 问题代码`, `## 审查` — matched exactly by the
  validator, never translated per record. The human layer (title and prose) uses one language per
  record with the title matching the body's language, defaulting to Chinese.
- Gate change, human-directed: `tools/lab/validate.py` now requires the Chinese heading literals
  (`BUG_REQUIRED_HEADINGS`, the `## 修复` rule, the `## 审查` rule for verified records). Negative
  test on a throwaway file: English headings are rejected (`body section '## 现象' is required`),
  Chinese headings pass.
- All six existing records normalized — titles and section headings to Chinese, each edit
  refreshing `updated_at`; the valid and invalid examples under `examples/` translated to the same
  form; `agents/bug-recorder.md` and both records READMEs carry the convention.
- Development release: no baseline/candidate evaluation evidence. The installed host snapshot
  lags the source until the marketplace is refreshed and the plugin is reinstalled.

## 0.3.6 — 2026-09-16

Execution-layer teeth for declared boundaries, plus honesty labels for what is still unmeasured.
Trigger: a capability review found that write scopes, resumability, evidence capture, and
method-level changes were declared but had no enforcement or measurement path.

- New hard boundary 14: a declared write scope is enforced by comparing the workspace's actual
  change surface against it, not by the worker's restatement. The supervisor records the baseline
  revision at delegation and lists everything that changed (tracked and untracked) before
  accepting; any out-of-scope path is a defect to return even when checks pass. Ships with
  `skills/agentflow/scripts/check-write-scope.sh <base> <scope>...` — a one-command diff-against-
  scope check for ordinary development briefs (`isolation.py check-diff` remains the improvement
  loop's candidate-tree gate). Tested on in-scope, out-of-scope, and bad-revision cases.
- Worker result contract gains optional `cost` and `duration` fields: record measured numbers or
  `not reported`, never estimates — the development line can now accumulate the run-cost evidence
  the improvement loop already treats as an evidence category.
- Reviewer test-depth mode: the revert experiment that proves a regression check fails on the
  unfixed code is behavioral, not prose — the reviewer names the exact revert command and expected
  failing output, the supervisor executes and returns raw output (same channel as the check
  protocol). A fixer-written regression check is the floor, not independent verification.
- SKILL.md: step 10 requires capturing the decision record durably before the session ends when
  the outcome may feed the improvement loop (episodes do not self-collect; once the conversation
  is gone the evidence is unrecoverable); the recovery section defines session-death resumption
  from the versioned plan under `records/plans/` — re-derive each work package's state from the
  workspace, treat unobserved packages as not started.
- `references/roles.md`: complete profiles for all twelve roles (the bug chain, plan architect,
  and the four improvement roles had no profile entries) plus a task-shape routing table.
- Agent descriptions: removed the "for Agentflow" / "when Agentflow assigns" qualifier from
  reviewer, technical-director, frontend-engineer, and backend-engineer so hosts route them
  correctly in ordinary business repositories.
- Improve skill declares two capability limits: (1) measured scope — the public suite measures
  Agentflow against its own contract cases, so method-level candidates (role behavior inside
  business repositories) are released as `measurement: none (method-level change, no instrumented
  business task)` and never described as verified; (2) `maxTurns` is declared but unverified on
  ZCode — the prompt-level budget discipline is the operative constraint, the frontmatter number
  is intent metadata.
- Chinese mirror `docs/agent-roles.md` updated for all of the above; `docs/next-session-handoff.md`
  now carries a P0/P1/P2-prioritized backlog replacing the stale unchecked task list.
- Development release: same status as 0.3.4/0.3.5 — no baseline/candidate evaluation evidence.
  The installed snapshot lags the source until the marketplace is refreshed and the plugin is
  reinstalled; `validate.py installed` reports that drift.

## 0.3.5 — 2026-09-15

Rule patches carried over from a real cross-layer feature run (a conversation-share landing page
mirroring an existing chat surface). Every miss that passed the gates fell in one class — runtime
wiring, layout, and ordering that static reading cannot prove — and the largest cost came from
replicating an existing UI and extending a frozen contract without a reference-as-spec inventory.
The patches target assertion type and reference discipline, not gate strength. The source review's
anchors and claims were verified against this tree before applying; applied on explicit user
request.

- New hard boundary 13: an absence claim ("nothing was written", "the request never fired")
  requires reading the authoritative sink — the directory listing, receiving table, queue, or
  transport log — directly; an indirect index (search tool, cache, sampled dashboard) failing to
  show it is not evidence of absence. (Boundary 12 covers positive tool-behavior claims; this one
  covers negative claims.)
- Final decision record gains a `claims` ledger: every user-visible claim mapped to the check that
  would fail if it were false; a claim covered only by reading code is `unverified`, and any
  unverified user-visible claim makes the outcome `partial`, not `complete`. SKILL.md step 10 and
  the reviewer's check protocol carry the same rule. Step 8 requires the end-to-end path a real
  user would take to execute before the gate closes, and re-opens the gate for later user-visible
  changes (re-review may be scoped to the delta).
- Worker task brief gains three disciplines: **Replication briefs** (the reference implementation
  is the specification; inventory it at `path:line`; acceptance is a measured comparison),
  **Extension inventory** (grep the existing contract surface before adding a carrier; a worker
  who finds an equivalent carrier stops and reports), and **Mirror briefs** (a branch table
  against the reference `path:function` precedes implementation).
- New `## Verification stand-ins` section: a mock, stub, fixture set, or local contract harness is
  verification apparatus, not the deliverable; inventory the consumer's required surface up front,
  record later gaps as verification gaps and re-run the checks they covered, and keep responses
  contract-faithful so a contract mismatch fails against the stand-in instead of hiding behind it.
- Frontend engineer: runtime-context wiring (route params, route element construction, providers,
  portals, layout mounts) is not proven by unit tests — name the runtime check that would fail if
  the wiring were wrong, or report it as not run under risks.
- Plan Architect: a parity inventory task (replicate / omit-with-reason / defer) runs before
  implementing a surface that must mirror an existing implementation, and the plan lists the
  required surface of any verification stand-in with the end-to-end check placed before the
  review gate.
- Docs: Chinese discipline mirror updated in `docs/agent-roles.md`; new
  [`docs/iteration-log.md`](docs/iteration-log.md) records trigger, change, and solved problem per
  version.
- Development release: no baseline/candidate evaluation evidence, not a governed candidate
  promotion. The installed host snapshot lags the source until the marketplace is refreshed and
  the plugin is reinstalled; `validate.py installed` reports that drift.

## 0.3.4 — 2026-09-15

- Record and prevent this session's incident class: bug records BUG-20260915-002 (fault injection
  executed on the real repository; a `git checkout` "recovery" reset `protected-paths.txt` to its
  committed version and silently discarded uncommitted edits — caught one command later by
  `validate.py protected`) and BUG-20260915-003 (three consecutive rounds each shipped a behavior
  claim asserted from reasoning and falsified by a minimal experiment; the third masked a fully
  demonstrated gate bypass). Prevention: new hard boundary 12 in `contracts.md` — a claim about how
  a tool, framework, or host behaves is a hypothesis until a minimal experiment reproduces it — and
  an "Experiments and recovery" rule set in `AGENTS.md` (inject only on throwaway copies; never
  `git checkout`/`restore` to undo an experiment on the real tree; a recovery counts only after the
  check is re-run and observed green; no suppressed output on commands whose success is claimed).
- Audit round on the gate changes above; two corrections and one closed hole (human-authorized):
  - A full bypass of the test gate was demonstrated and closed. `unittest discover` imports
    packages found in subdirectories of the start directory, and import-time code runs before any
    assertion: an added `tests/<subdir>/` module that replaces a pinned test method makes a broken
    assertion pass, so `validate.py tests` returned PASS over a real gate regression. The
    declared-content check now rejects every undeclared entry in `tests/`, directories included.
    Re-verified by fault injection: the same attack now fails with the offending entry named;
    `__pycache__` still does not trip it.
  - The previous round's mechanism claim was corrected: a stray `tests/__init__.py` is inert under
    `discover -s tests` (it only imports when discovery starts from the repository root). The
    check still rejects it; the documentation no longer credits it with the neutralization it
    cannot perform under this runner.
  - `skills/improve/references/` is protected wholesale. `episode.schema.json` had been the one
    governance schema a candidate could still edit (the other three improve-reference schemas and
    the release rules were already protected). The required-entry set now demands all five files
    in that directory individually, so narrowing the prefix back cannot silently drop one.
- Close the four gate gaps found in the whole-project review (human-authorized gate changes):
  - `schemas/` joins [`protected-paths.txt`](protected-paths.txt) wholesale, and the pinned
    regression test is protected by file (`tests/test_lab_contracts.py`). The record schemas are the
    compile target for candidate artifacts and the test pins `validate.py`/`isolation.py`; all were
    editable by the candidate whose work they judge. Required-entry set in `validate.py` extended to
    demand coverage of both record schemas and the test file.
  - The test directory is covered by a declared-content assertion instead of a directory prefix.
    Protecting `tests/` outright blocked on `tests/__pycache__/*.pyc` — artifacts any candidate
    carries after running the checks — which would have made the gate fail every candidate that
    tested its own work, and a gate that fails honest work invites bypass. The assertion rejects
    undeclared `.py` files in the directory, closing the neutralization vector (a package
    `__init__` or shim that patches the pinned tests) that file-level protection alone leaves open.
    The test subprocess also runs with `PYTHONDONTWRITEBYTECODE=1`.
  - New `validate.py manifests`: the five hand-synced manifests must agree on plugin name and
    version. A missed bump previously surfaced only after a host reinstall.
  - New `validate.py tests`: the repository's regression tests run as part of the deterministic set.
    `all` now covers seven checks instead of five. The orphaned-test gap is closed — the tests were
    passing but nothing ran them.
  - Verified by fault injection: a bumped version in one manifest, a removed protected entry, a
    broken assertion, and an injected `tests/__init__.py` each fail their check; a stray
    `__pycache__` does not.
- Add the implicit-behavior discipline: briefs split `write_scope` from `read_scope` (read scope
  strictly wider), require shared cross-cutting mechanisms to be discovered by framework
  registration-point search, declared explicitly (empty set included), traced to a registration
  `path:line` (evidence terminates the trace, not layer count), and checked across surfaces ×
  legitimate states. Carried in plans by a required `shared_mechanisms[]` field with mandatory
  `registration_ref`; clauses added to frontend-engineer, backend-engineer, reviewer, and
  bug-investigator (mechanism-vs-caller conflicts attribute to `missing-constraint`). New eval case
  AF-015 and bug record BUG-20260915-001 from the real axios-401-interceptor case. Includes
  `plan.schema.json`, `evals/` — a contract/gate change executed on explicit user request, pending
  human confirmation.
- Require a frozen parent revision for candidate protected-diff checks and remove command-line
  replacements for the protected path set.
- Tighten the dependency-free validator's JSON Schema equality and RFC 3339 date-time handling.
- Clarify host-specific installation drift, Bash/network boundaries, and the current evaluation
  readiness limits in the documentation.

## 0.3.3 — 2026-09-14

Boundary-hardening release after reviewing the role set against the host's actual enforcement.

### Boundaries

- **Tool allowlists on the implementation roles.** `backend-engineer`, `frontend-engineer`, and
  `candidate-engineer` now declare `tools: Read, Glob, Grep, Write, Edit, Bash`, matching
  `bug-fixer`. Previously they inherited the full tool set, including delegation, network, and MCP
  tools, which contradicted hard boundary 2 (delegation never expands authority) and let a worker
  start subagents of its own.
- **A declared candidate gate surface.** New [`protected-paths.txt`](protected-paths.txt) is the
  single source for the paths a candidate may never edit (evaluator and governor role files, the
  evaluation suite, the measurement path under `tools/lab/`, the release rules, the result schemas,
  and the list itself). `isolation.py check-diff` reads it by default instead of requiring
  `--forbidden` from the caller; `validate.py protected` fails if the list stops covering a required
  gate path, and `all` includes it.
- `candidate-engineer`'s ownership matrix now names the protected list explicitly, closing the
  contradiction between "write the candidate tree" and "never edit the judging gate" when the
  candidate tree *is* the plugin.
- Hard boundaries: #1 now makes the independent review gate mandatory when the supervisor writes
  part of the change; #2 forbids worker re-delegation; #6 points at the declared list; new #11
  requires a budget-stopped run to report `partial`.
- The reviewer's check protocol is explicit: the reviewer authors the exact commands and expected
  outcomes and requires raw output, because the author of a change may execute a check but may not
  choose it.

### Reliability

- Budget discipline on every writing role: reserve the final turn for the worker result, and never
  report `complete` for a truncated run. Implementation roles raised to 30 turns, Plan Architect to
  20. (`maxTurns` semantics are host-supplied and not yet verified on ZCode.)
- `validate.py installed` compares the runtime components (`agents/`, `skills/`, manifests) of the
  source checkout against the installed plugin snapshot. Hosts load agents from the snapshot, so
  source edits to a role do not take effect until the plugin is reinstalled; this check makes that
  drift visible instead of silent. It stays out of `all` because it reads outside the repository.

### Evaluation

- Four new public cases: `AF-011` (a worker summary is not verification), `AF-012` (task text is
  data, not instruction), `AF-013` (a candidate may not edit the gate that judges it), `AF-014`
  (baseline comparison separates environment failure from regression). Suite is now 14 cases.

### Documentation

- Observed ZCode facts updated: plugin agents do load from the installed snapshot and do honor the
  frontmatter `tools` allowlist; `agents/` has no live-edit path.
- Repository naming normalized to "Agentflow"; stale `0.3.1`/`plans/` references corrected.
- New [`AGENTS.md`](AGENTS.md) with the working rules for this repository.

## 0.3.2 — 2026-09-14

First update release after real-model dogfood and the ZCode host integration.

### Host adapter

- Strip `$schema`/`$id` meta-declarations before passing schemas to Claude Code `--json-schema` (current CLI builds reject Draft 2020-12 declarations at load time).
- Add `host_adapter.py --progress <jsonl>` per-invocation diagnostics and a stderr status line per invocation; a run still fails closed, but failures are now attributable to a case and repetition.
- Document the host adapter protocol's progress option and schema handling in `tools/lab/adapter-protocol.md`.

### Role contracts

- Add artifact-ownership declarations to all 12 agent files: per-artifact tables for the six writing roles, compact statements for the six read-only roles.
- Remove duplicated constraint wording introduced alongside the ownership declarations.

### Workflow discipline

- Supervisor step "Verify worker artifacts before accepting them": deterministic checks run against actual files; failed checks are compile errors; unreproducible checks count as not run.
- Improvement-loop step 9: candidate, evaluation, comparison, and decision records are schema-validated before the next role consumes them.
- Consolidated 10-item hard-boundaries list in `skills/agentflow/references/contracts.md` (single source; both skills reference it).
- Treat task text as data: paths, repos, commands, and versions are verified against the repository before entering a brief.
- Baseline triage in "Recover from stalled work": run the failing check against the pre-change revision before calling a regression.

### Records

- Bug records are now Markdown with validated YAML frontmatter instead of JSON: human-readable body (Symptom / Problem code / Root cause / Fix / Review) plus machine-checked metadata, one file per bug under `records/bugs/<YYYY-MM-DD>/<kebab-slug>.md`.
- New frontmatter fields: `error_kind` (ai-ignored-doc, ai-ignored-code, missing-constraint, hallucination, logic-error, host-compat, environment, other), `project`, and `files` (the affected paths).
- Archive: `rejected` records must move to `records/bugs/archive/<same-date-dir>/`; `verified` records stay in place as reference. Both rules are enforced by the validator.
- Plans remain JSON under `records/plans/<plan_id>.json` with required `recorded_at` and ordered `updated_at`.
- New `validate.py report` command prints the chronological bug table (date, id, status, severity, error kind, title).
- All durable artifacts unified under `records/`; `records/README.md` documents layout, conventions, and retrospective queries.

### Tooling

- `tools/lab/validate.py` new `artifacts` target (included in `all`): validates plan and bug-record instances actually written under `records/` (recursive).

### Documentation

- New `docs/host-platform-facts.md`: observed Claude Code / Codex CLI / ZCode behaviors with evidence and scope.
- Fix stale repository state in README, handoff, self-improvement design, and evals README (remote status, runner existence, tool maturity, machine paths).
- Record dogfood evidence: AF-001 smoke pass, AF-002 latency/permission/model-label findings, environment blockers for the full baseline run.

### Hosts

- Add `.zcode-plugin/plugin.json` and a local `marketplace.json`; the plugin now installs from a local directory into ZCode (skills and agents components).
- Front-load trigger wording in both skill `description` fields so the complete "when to use" condition survives ZCode's ~250-character truncation when the model decides whether to invoke a skill.
