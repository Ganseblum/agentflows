# Records

Single root for durable, retrospective evidence produced by Agentflow roles. Everything a role
writes for later review lives here; each role's artifact-ownership matrix names exactly which
subtree it may touch.

| Subtree | Writer | Format | Purpose |
| --- | --- | --- | --- |
| [`bugs/YYYY-MM-DD/*.md`](bugs/README.md) | bug-recorder | Markdown + frontmatter | Bug archive: symptom, problem code, root cause, fix, priority grade, error kind, provenance, files |
| [`bugs/recurrence/<class_id>.md`](bugs/README.md) | bug-recorder | Markdown + frontmatter | Recurrence ledger: one file per failure class that recurred or was consolidated — consolidation state, version, occurrence list |
| [`reviews/YYYY-MM-DD/<project>-<slug>/`](reviews/README.md) | supervisor | Markdown + frontmatter + archived copies | Second-pass reviews of documents authored under another system's rules: review record, verbatim snapshot, findings linkage |
| [`episodes/YYYY-MM-DD/<EP-id>.json`](episodes/README.md) | supervisor | JSON | Durable capture of one task's final decision record — the improvement loop's task-level evidence, written before the session ends |
| [`plans/<plan_id>.json`](plans/README.md) | plan-architect | JSON | Versioned execution plans: work packages, lanes, gates, rollback points |
| [`bugs/archive/`](bugs/README.md) | — | same | Retired `rejected` records, moved out of the active tree |

Planned (not implemented): evaluation results and release records join the same root when the
improvement control plane lands.

Bug records are Markdown so people can read the narrative and the problem code; the machine
contract lives in the YAML frontmatter and is fully validated (schema, status rules, date
directory, filename slug, id uniqueness, timestamp order). Plans stay JSON because they are
structured execution contracts consumed by tooling.

## Conventions

- The supervisor assigns each record path explicitly; a role never picks its own path.
- **Bugs**: one file per bug under `records/bugs/<YYYY-MM-DD>/<kebab-slug>.md`; the date
  directory must match `recorded_at` (UTC). Recommended id shape `BUG-<YYYYMMDD>-<NN>`. The id
  is assigned once and never changes; status transitions edit the file in place and refresh
  `updated_at`. `rejected` records move to `records/bugs/archive/<date-dir>/`; `verified`
  records stay in place as reference.
- **Plans**: one file per plan, named exactly `<plan_id>.json`, carrying `recorded_at` and
  `updated_at`.
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
- **Recurrence**: a failure class that recurred or was consolidated into Agentflow gets one
  ledger at `records/bugs/recurrence/<class_id>.md`; its records carry `class_id` + `occurrence`.
  Consolidation state (`unconsolidated` / `consolidated` + `consolidated_in`) is set from the
  actual release, never inferred. The tier — `single` / `recurred` / `escalated` — is derived by
  the validator from the occurrence records' `agentflow_version`; `escalated` (a recurrence on a
  version newer than the consolidation) is the aggravated marker and triggers the improve-loop
  escalation. The ledger and its records are cross-validated: an occurrence must exist, be listed
  in the ledger, and use a unique occurrence number.
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
- A record is accepted only after `python3 tools/lab/validate.py artifacts` passes against the
  actual file. A failed check is a compile error, not a discussion.
- Records are append-only history: corrections update the record and its `updated_at`; past
  evidence is never rewritten to improve the story.

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
jq -r '[.recorded_at, .plan_id, .status, .plan_version] | @tsv' records/plans/*.json | sort
```
