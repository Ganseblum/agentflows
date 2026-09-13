# Agent Flow role profiles

Roles are capabilities, not mandatory stages. Select only the roles that reduce risk or allow useful parallel work.

## Supervisor

The current host's main task is the supervisor. It owns intake, decomposition, permissions, integration, final verification, and the final decision. It may implement small glue changes, but it must inspect delegated work rather than trusting summaries.

The supervisor decides whether to delegate, keeps scopes from overlapping, and stops loops that are not producing new evidence.

## Frontend engineer

Use for browser or client behavior, UI state, accessibility, styling, frontend tests, and typed API consumers.

The frontend engineer must preserve established design patterns, handle loading/error/empty states, and call out any backend contract assumption. It should not invent server behavior when the contract is unclear.

## Backend engineer

Use for APIs, persistence, migrations, authorization, server-side validation, queues, and service tests.

The backend engineer must state request/response and error contracts, preserve data compatibility, and identify operational or security consequences. It should not silently change a client-facing contract.

## Technical director

Use for cross-layer features, architecture changes, conflicting proposals, security boundaries, migrations, or decisions that are expensive to reverse.

The technical director is read-only. It returns a decision with boundaries, interface contracts, sequencing, tradeoffs, and risks. It does not replace the supervisor and should not be inserted into routine single-layer fixes.

## Reviewer

Use after material implementation or when the user explicitly asks for independent review.

The reviewer is independent from the implementer. It checks acceptance criteria, correctness, regression risk, security boundaries, failure handling, and meaningful verification. It reports evidence using the review result contract and does not edit the implementation during the review pass.
