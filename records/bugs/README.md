# Bug records

Human-readable bug archive, one Markdown file per bug, grouped by the UTC date the bug was
recorded:

```text
records/bugs/
  2026-09-14/
    claude-json-schema-rejected.md
  archive/                    # closed and retired records keep their date directory
    2026-08-01/
      stale-flaky-test.md
```

Each file is YAML frontmatter (the machine-checked contract,
[`schemas/bug-record.schema.json`](../../schemas/bug-record.schema.json)) plus a Markdown body
for humans. Required body sections: `## Symptom`, `## Root cause`, and `## Fix` (except for
`open` bugs); `## Problem code` is recommended whenever a code snippet exists, and `## Review`
is required once a record is `verified`.

Frontmatter fields: `bug_id`, `title`, `status` (open / fixed-pending-review / verified /
rejected), `severity`, `error_kind` (ai-ignored-doc / ai-ignored-code / missing-constraint /
hallucination / logic-error / host-compat / environment / other), `attribution`, `project`,
`files`, `recorded_at`, `updated_at`; `reviewer` + `review_decision` + `regression_status`
when verified; `rejection_reason` when rejected.

Archive rule: a `rejected` record must be moved into `records/bugs/archive/<same-date-dir>/`;
`verified` records stay in place as reference. The parent
[records index](../README.md) documents conventions and retrospective queries.
