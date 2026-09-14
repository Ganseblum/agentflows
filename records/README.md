# Records

Single root for durable, retrospective evidence produced by Agentflow roles. Everything a role
writes for later review lives here; each role's artifact-ownership matrix names exactly which
subtree it may touch.

| Subtree | Writer | Format | Purpose |
| --- | --- | --- | --- |
| [`bugs/YYYY-MM-DD/*.md`](bugs/README.md) | bug-recorder | Markdown + frontmatter | Bug archive: symptom, problem code, root cause, fix, severity, error kind, files |
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
- A record is accepted only after `python3 tools/lab/validate.py artifacts` passes against the
  actual file. A failed check is a compile error, not a discussion.
- Records are append-only history: corrections update the record and its `updated_at`; past
  evidence is never rewritten to improve the story.

## Retrospective

Full table (date, id, status, severity, error kind, title), sorted chronologically:

```sh
python3 tools/lab/validate.py report
```

Error-kind distribution — which class of mistake keeps recurring:

```sh
python3 tools/lab/validate.py report | cut -f5 | sort | uniq -c | sort -rn
```

Open bugs only:

```sh
python3 tools/lab/validate.py report | awk -F'\t' '$3=="open" || $3=="fixed-pending-review"'
```

Bugs touching a file or project:

```sh
grep -rl "tools/lab/host_adapter.py" records/bugs --include="*.md"
```

Plans by state (`draft`, `proposed`, `approved`, `superseded`):

```sh
jq -r '[.recorded_at, .plan_id, .status, .plan_version] | @tsv' records/plans/*.json | sort
```
