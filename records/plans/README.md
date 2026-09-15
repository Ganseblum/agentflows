# Plans

`plan-architect` writes versioned execution plans here only when the supervisor supplies an
explicit output path. Plans record specialist evidence, the shared mechanisms a change passes
through (`shared_mechanisms[]`, each cited at its registration point), dependencies, parallel lanes,
gates, verification, and rollback points; they do not authorize implementation by themselves.

Instances are JSON validated against [`schemas/plan.schema.json`](../../schemas/plan.schema.json);
the file is named `<plan_id>.json` and carries `recorded_at`/`updated_at` timestamps. The parent
[records index](../README.md) documents the layout, conventions, and retrospective queries.
