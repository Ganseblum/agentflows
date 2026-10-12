# Test records

Automated-testing evidence for user-visible features: the case library a `test-planner` writes
and the run records a `test-executor` produces. The chain is user-initiated or plan-carried
(see the agentflow skill's *Automated testing* section); records here feed the bug chain and the
review gate's end-to-end-path evidence.

| Artifact | Writer | Format | Purpose |
| --- | --- | --- | --- |
| `<project>-<feature-slug>/plan-<YYYY-MM-DD>-<NNN>.md` | test-planner | Markdown + frontmatter | Case library: registry with levels (smoke/e2e/api/boundary) and priorities, executable step tables, boundary coverage, 流程疑点 |
| `<project>-<feature-slug>/run-<YYYY-MM-DD>-<NNN>.md` | test-executor | Markdown + frontmatter | One execution round: per-case results with evidence, summary counts, decision, reproduction-ready findings |
| `<project>-<feature-slug>/evidence/` | test-executor | files | Screenshots, traces, response dumps — referenced by run records, never hand-edited |
| `<project>-<feature-slug>/scratch/` | test-executor | files | Disposable automation scripts written during a run (e.g. Playwright specs); not records |

## Contracts

Schemas: `schemas/test-plan.schema.json` and `schemas/test-run.schema.json` (frontmatter
envelopes; frontmatter values are flat strings — the parser deliberately does not nest).
Cross-checks the validator enforces beyond the schemas:

- **Layout**: both records live at `features/<batch>/testing/<project>-<feature-slug>/`; the filename
  matches the id (`TP-<YYYYMMDD>-<NNN>` → `plan-<YYYY-MM-DD>-<NNN>.md`,
  `TR-<YYYYMMDD>-<NNN>` → `run-<YYYY-MM-DD>-<NNN>.md`), and the id date matches
  `recorded_at`'s date. The directory is anchored on the tested feature, not the date: the same
  feature accumulates plan revisions and run rounds in one place. Unexpected files directly in
  the feature directory are rejected; `README.md` and `evidence/` are exempt.
- **Plan body**: `## 用例` opens with the registry table (`| 用例 ID | 级别 | 优先级 | 标题 |`)
  and carries one `### <case id>` detail heading per case; case ids (`TC-*`) are unique; levels
  and priorities are fixed enums; `case_count` equals the registry row count. `## 边界覆盖` and
  `## 流程疑点` are required sections. The plan is revised in place — bump `test_version`.
- **Run body**: `## 结果` is the result table (`| 用例 ID | 状态 | 证据 | 说明 |`); statuses are
  the fixed enum `pass / fail / blocked / not-run`; a `fail` or `blocked` row carries evidence;
  result case ids must exist in the referenced plan's registry; the flat `summary_*` counts
  equal the table; `decision: pass` requires zero fail and zero blocked. `## 证据` and
  `## 结论` are required. Each round is one new file — corrections edit the record and refresh
  `updated_at` (append-only history: past evidence is never rewritten to improve the story).
- **Plan resolution**: a run's `test_plan_id` must resolve to a plan record in the same feature
  directory, with a matching `project`. When the run pins the plan's current `test_version`,
  every registry case is accounted for in the result table (a run against an older version
  records its own coverage instead).
- **Findings**: `findings` / `flow_findings` list `BUG-*` ids that must exist under
  `issues/`. Failed cases carry reproduction-ready findings (steps, expected vs actual,
  evidence refs) so the supervisor can file the bug record without re-deriving it; attribution
  follows the standard rules (`external` for target-project defects, `agentflow` for gaps in
  Agentflow's own method).

## Target-project mapping

When the target project has its own case engine (a locator registry, reusable flows, a suite
registry, per-environment config — for example a YAML-driven Playwright suite), the run
record's conclusion routes each failure along this alignment chain; each link names what must
agree and where a change lands, so a repair touches one file:

| Chain link | What must agree | Where a change lands |
| --- | --- | --- |
| frontend test ids ↔ locator registry | the testid string or dynamic prefix | FE rename → the registry only; cases keep their logical names |
| registry ↔ plan's case library | every element a case references exists as an alias | new alias declared with the case; no literal locators in cases |
| case library ↔ engine cases | step/expected semantics land as the engine's actions and assertions | executor lands them; no new vocabulary invented |
| cases ↔ shared flows | reusable preconditions are referenced, not copy-pasted | shared precondition change → the flow registry, once |
| cases ↔ suite registry | suite id, case directory, and runner registry agree — a mismatch is a silent no-collection | register the suite before creating its case files |
| cases ↔ environment config | origins, accounts, and keys resolve per environment; values never inside cases | environment change → the config only |

Failure routing follows the same table: product behavior contradicting an expected result →
the bug chain; element/registry drift → a registry update plus rerun; environment or data
problems → `blocked` with the reason. A capability the framework documents as unsupported is
declared TODO or 不可自动化 in the plan — never weakened into a passing assertion. The concrete
registry file names are the target project's own; they are declared per project, never
hard-coded into another project's cases or into this contract.

## Credentials

Credentials are supplied per session and injected at runtime (env, session, gitignored file) —
the `credentials` frontmatter field declares the **method in one line** and never a value.
Passwords, tokens, and real account values are forbidden anywhere in these records; the
executor enters them through masked inputs and flags any trace or screenshot that captured a
secret so the supervisor can treat that artifact as sensitive.

A record is accepted only after `python3 tools/lab/validate.py artifacts` passes against the
actual file.
