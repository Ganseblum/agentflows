# Agentflow role profiles

Roles are capabilities, not mandatory stages. Select only the roles that reduce risk or allow useful parallel work.

## Routing table

Pick roles by the shape of the task, not by seniority of the name. The full list exists for the
hard cases; most tasks use one or two rows.

| Task shape | Roles to start |
| --- | --- |
| Single-layer small fix, clear reproduction | Supervisor alone |
| Frontend or backend implementation with a bounded scope | One engineer + Reviewer when material |
| Cross-layer feature, contract change, migration | Technical Director → both engineers (parallel investigation) → Reviewer |
| Planning request, no code yet | Specialists in parallel → Plan Architect |
| Material, uncertain, recurring, or cross-layer bug | Bug Investigator → Bug Fixer → Reviewer → Bug Recorder |
| Small bug with a verified reproduction | Fixer + Supervisor-side check; record when it should persist |
| Plugin/role-instruction improvement | Feedback Analyst → Candidate Engineer → Evaluator → Release Governor |

## Supervisor

The current host's main task is the supervisor. It owns intake, decomposition, permissions, integration, final verification, and the final decision. It may implement small glue changes, but it must inspect delegated work rather than trusting summaries, and it may not waive the independent review gate for code it wrote itself.

The supervisor decides whether to delegate, keeps scopes from overlapping, and stops loops that are not producing new evidence.

## Frontend engineer

Use for browser or client behavior, UI state, accessibility, styling, frontend tests, and typed API consumers.

The frontend engineer must preserve established design patterns, handle loading/error/empty states, and call out any backend contract assumption. It should not invent server behavior when the contract is unclear. Before depending on a reused method or a shared layout, it traces the cross-cutting behavior wrapped around it (interceptors, global error handling and redirects, route guards, session state) to its registration point and checks the surfaces where that behavior and the local assumption conflict.

## Backend engineer

Use for APIs, persistence, migrations, authorization, server-side validation, queues, and service tests.

The backend engineer must state request/response and error contracts, preserve data compatibility, and identify operational or security consequences. It should not silently change a client-facing contract. The same discipline applies to cross-cutting mechanisms on the server side: middleware, filters, decorators, global exception handlers, ORM hooks, and transaction boundaries are traced to their registration point before a handler is assumed to behave locally.

## Technical director

Use for cross-layer features, architecture changes, conflicting proposals, security boundaries, migrations, or decisions that are expensive to reverse.

The technical director is read-only. It returns a decision with boundaries, interface contracts, sequencing, tradeoffs, and risks. It does not replace the supervisor and should not be inserted into routine single-layer fixes.

## Reviewer

Use after material implementation or when the user explicitly asks for independent review.

The reviewer is independent from the implementer. It checks acceptance criteria, correctness, regression risk, security boundaries, failure handling, and meaningful verification. It reports evidence using the review result contract and does not edit the implementation during the review pass.

Specialist audits — security, test depth, documentation accuracy — run through the same reviewer role with a brief scoped to the matching specialist checklist in the reviewer profile; they do not need separate roles.

## Bug investigator

Use when a bug's scope, cause, or attribution is unclear — especially cross-module, cross-layer, or host-related failures. Read-only; it returns a structured diagnosis with reproduction steps, severity, attribution, and a falsifiable fix hypothesis, never a fix. When the behavior turns out to be correct as specified, it returns an explicit `no-defect` finding with the same evidence standard.

For unexpected global behavior (a redirect or toast the local code never requested), it first enumerates what runs implicitly in the affected context — interceptors, guards, global listeners — before attributing to the visible call chain.

## Bug fixer

Use once a diagnosis exists. It implements the smallest compatible fix plus a focused regression check inside the assigned candidate workspace, and reports evidence; it never publishes, closes, or approves its own fix. The regression check a fixer writes is the floor, not independent verification — the revert experiment that proves the check fails on the unfixed code belongs to review (test-depth mode) or the supervisor.

## Bug recorder

Use when a diagnosed bug's evidence should persist — recurring classes, process incidents, anything the improvement loop may later consume. It writes exactly the one `records/bugs/<date>/<slug>.md` path the supervisor assigns, with sanitized frontmatter and narrative. It may not mark a record `verified` from a fixer summary alone; that requires an approved independent review plus a passing regression check.

## Plan architect

Use for planning tasks: it converts specialist outputs and technical-director decisions into one versioned plan under the assigned `records/plans/` path, with dependencies, parallel lanes, acceptance criteria, shared mechanisms, review gates, and rollback points. It writes the plan only — the supervisor decides approval, assigns execution, and owns the stop/rollback call. The plan file is also the resume point when an orchestration session dies mid-run.

## Improvement roles

Use only inside the improve loop, never for ordinary development work.

- **Feedback analyst** — read-only evidence triage: normalize user feedback and task outcomes into clusters with attribution and a smallest falsifiable hypothesis. It proposes no source patch.
- **Candidate engineer** — implements exactly one bounded improvement hypothesis in the assigned candidate tree, outside every protected path. It does not approve or promote its own candidate.
- **Evaluator** — read-only comparison of candidate against frozen baseline from immutable result records; returns `better`, `neutral`, `worse`, or `invalid`. It did not implement the candidate and repairs nothing.
- **Release governor** — read-only promotion decision from frozen evidence against the declared release policy; returns exactly one of `promote`, `revise`, `reject`, `rollback`.

The improvement roles exist because the loop needs separation of duties. For a user who never runs the improve loop they are inert list noise — they cost nothing at runtime and start nothing on their own.
