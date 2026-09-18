# Records

Single root for durable, retrospective evidence produced by Agentflow roles. Everything a role
writes for later review lives here; each role's artifact-ownership matrix names exactly which
subtree it may touch.

| Subtree | Writer | Format | Purpose |
| --- | --- | --- | --- |
| [`bugs/YYYY-MM-DD/*.md`](bugs/README.md) | bug-recorder | Markdown + frontmatter | Bug archive: symptom, problem code, root cause, fix, priority grade, error kind, provenance, files |
| [`bugs/recurrence/<class_id>.md`](bugs/README.md) | bug-recorder | Markdown + frontmatter | Recurrence ledger: one file per failure class that recurred or was consolidated — consolidation state, version, occurrence list |
| [`reviews/<project>-<feature-slug>/`](reviews/README.md) | supervisor | Markdown + frontmatter + archived copies | Second-pass reviews of documents authored under another system's rules: review record, verbatim snapshot, findings linkage |
| [`episodes/YYYY-MM-DD/<EP-id>.json`](episodes/README.md) | supervisor | JSON | Durable capture of one task's final decision record — required for every material change since 0.7.2, review round-trips included; the improvement loop's task-level evidence, written before the session ends |
| [`plans/<plan_id>.md`](plans/README.md) | plan-architect | Markdown + frontmatter | Versioned execution plans (hybrid): progress overview, task board with status + evidence write-back, contracts, gates, rollback points |
| [`tests/<project>-<feature-slug>/`](tests/README.md) | test-planner + test-executor | Markdown + frontmatter | Automated-testing evidence: case library (plan) and per-round run records with per-case results, evidence, and findings that feed the bug chain |
| [`improvement/{candidates,evaluations,comparisons,releases}/*.json`](improvement/README.md) | supervisor + eval_runner tooling | JSON | Improvement-loop artifacts: predeclared candidate, frozen runner evaluation result, baseline/candidate comparison, audited release decision — filename = identity, cross-validated |
| [`bugs/archive/`](bugs/README.md) | — | same | Retired `rejected` records, moved out of the active tree |

The improvement control plane's artifact handoff is implemented: candidate records, evaluation
results, runner comparisons, and release records live under
[`records/improvement/`](improvement/README.md) with their own schemas and cross-document
checks — no longer planned, part of the validated tree.

Bug records are Markdown so people can read the narrative and the problem code; the machine
contract lives in the YAML frontmatter and is fully validated (schema, status rules, date
directory, filename slug, id uniqueness, timestamp order). Plans are Markdown too: the
frontmatter envelope carries the machine contract and the body board is the human-readable
progress surface (shape: [plans/README.md](plans/README.md)).

## Conventions

- The supervisor assigns each record path explicitly; a role never picks its own path.
- **Bugs**: one file per bug under `records/bugs/<YYYY-MM-DD>/<kebab-slug>.md`; the date
  directory must match `recorded_at` (UTC). Recommended id shape `BUG-<YYYYMMDD>-<NN>`. The id
  is assigned once and never changes; status transitions edit the file in place and refresh
  `updated_at`. `rejected` records move to `records/bugs/archive/<date-dir>/`; `verified`
  records stay in place as reference.
- **Plans**: one Markdown file per plan, named exactly `<plan_id>.md` — frontmatter envelope
  (`plan_id`/`plan_version`/`status`/`objective`/timestamps) plus the body board (进展概览 /
  任务清单 with per-task status and evidence write-back / 验证命令). The checker asserts:
  task IDs unique, dependencies resolve and are acyclic, task statuses are the fixed enum,
  and a blocking 未决项 that is not closed blocks `status: approved`. Progress write-back is
  minimal-diff (状态 + 证据 columns only).
- **Reviews**: a second-pass review of documents authored under another system's rules lives at
  `records/reviews/<project>-<feature-slug>/` — one directory per reviewed feature, anchored on
  the feature rather than the date, because the same feature may be reviewed repeatedly. Each
  round is one `review-<YYYY-MM-DD>-<NNN>.md` file (filename equals review_id) with its own
  verbatim snapshot subdirectory `archive/<date>-<NNN>/`. `source_revision` pins the target
  repository's commit; `findings` lists the bug records filed from the review (validated to
  exist). Findings carry `provenance`: `external` findings (a template or rule gap in the
  target system) are the evidence pool for upgrading that system's rules/templates; `agentflow`
  findings mean this repo's review contract missed it. See
  [reviews/README.md](reviews/README.md) for the bridge workflow and the attribution table.
- **Self-contained references**: a `files` entry either resolves inside this repository or is
  repo-qualified as `<repo>@<revision>:<path>` (the validator rejects bare paths that exist
  nowhere — they dangle for anyone who receives the records without the other repository). For
  external references the record body embeds the decisive snippet or quoted sentence: the
  qualified path is the address, the embedded content is the evidence.
- **Tests**: automated-testing evidence lives at `records/tests/<project>-<feature-slug>/` —
  one directory per tested feature, holding the case library (`plan-*.md`, revised in place
  with a `test_version` bump) and one `run-*.md` per execution round. A run pins the plan id
  and version it executed plus the `target_revision` actually tested; failed cases carry
  reproduction-ready findings that become bug records; `credentials` declares the injection
  method and never a value. See [tests/README.md](tests/README.md).
- **Recurrence**: a failure class that recurred or was consolidated into Agentflow gets one
  ledger at `records/bugs/recurrence/<class_id>.md`; its records carry `class_id` + `occurrence`.
  Consolidation state (`unconsolidated` / `consolidated` + `consolidated_in`) is set from the
  actual release, never inferred. The tier — `single` / `recurred` / `escalated` — is derived by
  the validator from the occurrence records' `agentflow_version`; `escalated` (a recurrence on a
  version newer than the consolidation) is the aggravated marker and triggers the improve-loop
  escalation. The ledger and its records are cross-validated: an occurrence must exist, be listed
  in the ledger, and use a unique occurrence number.
- **Improvement artifacts**: the improve loop's handoff plane lives at
  `records/improvement/{candidates,evaluations,comparisons,releases}/` — one JSON artifact per
  file, filename = identity (a candidate record's stem is its `candidate_version`, an
  evaluation result's stem is its `result_id`). Producer split: tool output is tool-written
  (the frozen runner writes evaluation results and comparisons verbatim), human rulings are
  supervisor-written (candidate records, release records). Every cross-document claim is
  compiled — a comparison's results must exist with matching `source_kind` and context, a
  release must embed a candidate JSON-equal (value equality, independent of key order and
  whitespace) to the candidate record and point at a compared result pair, and
  `evidence_ids` resolve into the episode/bug pools. See
  [improvement/README.md](improvement/README.md) for the contracts and the schema split.
- **Language**: the machine layer is English/ASCII — frontmatter keys and enum values, file
  slugs, ids, paths, and the `project` slug. The body headings are fixed literals too, in
  Chinese: `## 现象`, `## 根因`, `## 修复`, `## 问题代码`, `## 审查` — the validator matches
  them exactly, so they are not translated per record. The human layer — `title` and body prose —
  uses **one language per record**, and the title must match the body's language; the default is
  Chinese, the working language of the operator and of the business projects whose sessions
  produce most records, with code, commands, and technical identifiers keeping their original
  form inside Chinese prose. Records written before 2026-09-16 were normalized to this form on
  2026-09-16 — titles and section headings to Chinese, each edit refreshing `updated_at` — and the
  format example under `examples/bug-records/` follows the same convention.
- **Visual annotations** (0.7.2): records may use two renderer-safe emphasis devices on top of
  the semantic layer. GFM callouts with a **fixed vocabulary** — `> [!IMPORTANT]` marks an
  unresolved divergence or a blocked item（未决分歧/阻塞）, `> [!WARNING]` marks a residual risk
  or a known gap（残余风险/已知缺口）, `> [!NOTE]` marks an interpretation or clarification
  （口径澄清） — and ` ```diff ` fences for before/after or option-A/B comparisons (red/green
  on GitHub and VS Code, plain fence in a terminal). The fixed literal prefix keeps callouts
  greppable (`grep -rn '\[!WARNING\]' records/`), and the semantic layer stays authoritative:
  frontmatter enums and fixed sections carry the state, callouts only decorate it. Inline HTML
  colors, custom `[!...]` alert types, and styling-only emphasis are rejected — they do not
  survive renderers and pollute the machine-greppable layer.
- A record is accepted only after `python3 tools/lab/validate.py artifacts` passes against the
  actual file. A failed check is a compile error, not a discussion.
- Records are append-only history: corrections update the record and its `updated_at`; past
  evidence is never rewritten to improve the story.

## Explicit lexical retrieval

The files under `records/` remain authoritative. For Intake, build a disposable SQLite FTS5 read-side index and query it explicitly; this is lexical retrieval only and does not introduce a vector database:

```sh
python3 tools/lab/record_store.py index
python3 tools/lab/record_store.py query "permission regression" --limit 20
```

The index database is local disposable state and is not a record artifact.

## Retrospective

Full table (date, id, status, severity, error kind, title, provenance), sorted chronologically:

```sh
python3 tools/lab/validate.py report
```

Agentflow-owned records only — the ones that may drive a source change:

```sh
python3 tools/lab/validate.py report | awk -F'\t' '$7=="agentflow"'
```

Error-kind distribution — which class of mistake keeps recurring:

```sh
python3 tools/lab/validate.py report | cut -f5 | sort | uniq -c | sort -rn
```

Open bugs only:

```sh
python3 tools/lab/validate.py report | awk -F'\t' '$3=="open" || $3=="fixed-pending-review"'
```

Recurrence ledger — per class: consolidation state, version, occurrence count, recurrence tier:

```sh
python3 tools/lab/validate.py recurrence
```

Bugs touching a file or project:

```sh
grep -rl "tools/lab/host_adapter.py" records/bugs --include="*.md"
```

Plans by state (`draft`, `proposed`, `approved`, `superseded`):

```sh
grep -H -E "^(plan_id|plan_version|status):" records/plans/*.md
```
