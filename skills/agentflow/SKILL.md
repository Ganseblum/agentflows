---
name: agentflow
description: Use for cross-layer features, architecture changes, parallel investigation, delegated implementation, or work that benefits from an explicit review gate; skip trivial single-step work where delegation would add overhead. Applies the Agentflow method with the host's own agents: supervisor, frontend/backend engineers, technical director, and independent review.
---

# Agentflow

Apply the Agentflow development method with the current host's built-in agents, authentication, tools, permissions, and conversation history.

Do not invoke or require the standalone `agentflow` CLI, its providers, its TUI, an Agentflow API key, or an Agentflow MCP server. This skill is the workflow. The host is the runtime.

## Bind to the host

- In **Codex**, use native subagents. Give each subagent one role and one task brief. Use the main task as the supervisor.
- In **Claude Code**, prefer the plugin agents `agentflow:frontend-engineer`, `agentflow:backend-engineer`, `agentflow:technical-director`, and `agentflow:reviewer` when those roles fit the task. Use the main conversation as the supervisor.
- In **ZCode**, prefer the plugin agents `agentflow:frontend-engineer`, `agentflow:backend-engineer`, `agentflow:technical-director`, `agentflow:reviewer`, `agentflow:bug-investigator`, `agentflow:bug-fixer`, `agentflow:bug-recorder`, and `agentflow:plan-architect`. Use the main conversation as the supervisor. ZCode loads these from the installed plugin snapshot, so a role change in the source tree takes effect only after the plugin is reinstalled — run `python3 tools/lab/validate.py installed` to see whether the installed copy still matches the source.
- In another Agent Skills compatible host, use its built-in delegation mechanism. If none exists, execute the same phases sequentially and state that independent execution was unavailable.

Read [role profiles](references/roles.md) before assigning work and [contracts](references/contracts.md) before delegating implementation or review. The [hard boundaries](references/contracts.md#hard-boundaries) hold for every delegation in both workflows; check them before accepting any deliverable.

For a material, uncertain, recurring, cross-layer, or high-risk bug, use the full bounded
sequence `bug-investigator` → `bug-fixer` → `reviewer` → `bug-recorder`. The investigator
establishes a reproducible symptom and attribution, the fixer changes code only in an assigned
candidate workspace, the reviewer checks the fix, and the recorder writes the accepted bug
record after verification. For a small, low-risk bug with an already verified reproduction,
the supervisor may combine the investigator or recorder step, but must preserve the same
diagnosis, regression, review, and state evidence. Never let the fixer approve or close its own
bug.

For a planning task, run the needed frontend and backend specialists in parallel, send their
outputs and the technical director's interface decision to `plan-architect`, and have it
write the final plan under an explicit `records/plans/` path. Plan Architect only writes the plan; the
supervisor decides whether it is approved, assigns execution, integrates results, and owns the
final stop or rollback decision. A future `execution-coordinator` may handle durable queues,
leases, dependencies, retries, and resumable parallel batches, but it is not a current role.
The plan must include dependencies, parallel lanes, acceptance criteria, risks, ownership, and
review gates. A plan is an execution contract, not an approval to change code. For a material
feature the plan carries the design-completeness artifacts from
[contracts](references/contracts.md): critical-path timing (step table as baseline), an
exception matrix per critical path, and a release order paired with rollback points.

## Second-pass review of external documents

When the user asks for a review of documents authored under another system's rules (for example
a proposal/spec/design/plan produced inside a business repository's own template system), run
the independent reviewer role against those documents and land the evidence here:

1. Locate or create the feature-anchored directory `records/reviews/<project>-<feature-slug>/`.
   The directory is anchored on the reviewed feature, not the date: the same feature may be
   reviewed repeatedly (today, tomorrow, after fixes) and every round is one more
   `review-<YYYY-MM-DD>-<NNN>.md` file in the same directory. Archive **verbatim copies** of
   the round's documents under `archive/<date>-<NNN>/` — one snapshot subdirectory per round so
   same-named documents never collide — and record the target repository's current commit as
   `source_revision`: later edits there must not retroactively change what was reviewed. A
   re-review focuses on the delta since the previous round's review_id.
2. The reviewer applies this repo's review contract to the snapshot (the reviewer profile's
   check protocol and, where relevant, the design-completeness artifacts above).
3. File every finding as a bug record under `records/bugs/` with `project` set to the target
   repository. Attribution separates the two upgrade loops: `provenance: external` +
   `attribution: product_code` marks a template/rule gap in the target system — the evidence
   pool for upgrading that system's templates; `provenance: agentflow` means this repo's review
   contract should have caught it. When the target system's upgrade lands, backfill
   `fix_revision` with its commit. References must stay self-contained: a `files` entry either
   resolves inside this repository or is repo-qualified (`<repo>@<revision>:<path>`) — a bare
   external path fails validation because it dangles for anyone without that repository — and
   the body embeds the decisive snippet or quoted sentence so the record stays readable when
   the other repository is absent.
4. Write `review-<date>-<NNN>.md` (contract: `schemas/review.schema.json`; filename equals
   review_id) with the decision, the findings list, and the archived-doc references, then run
   `python3 tools/lab/validate.py artifacts` — it cross-checks that every archived document and
   every referenced finding actually exists.

The full bridge workflow, attribution table, and known limits (cross-repo recurrence tiers are
not auto-derived) live in [records/reviews/README.md](../../../records/reviews/README.md).

## Run the workflow

1. **Intake**: inspect the repository instructions, current diff, relevant architecture, and tests. State the objective and observable acceptance criteria. When you report repository **status** — what is done, what is next, what is high priority — calibrate against the repository's real history first (`git fetch` plus `log`/`status`), never against session memory, and carry the evidence command with the conclusion. A status claim is a repository-fact claim: session memory goes stale the moment another writer pushes, and nothing in the answer would reveal it.
2. **Architecture gate**: for cross-layer or risky work, ask the technical director to define boundaries, interface contracts, integration order, and major risks. Do not use this role as a ceremonial approval step.
3. **Plan**: select only the roles the task needs. A frontend-only fix does not need a backend worker. A small change can stay with the supervisor.
4. **Delegate**: give every worker a bounded brief with `write_scope` and `read_scope` set separately — read scope must cover every shared mechanism the change passes through (the implicit-behavior check in [contracts](references/contracts.md)). Parallelize read-heavy investigation and implementation with disjoint files or stable interfaces; disjoint files parallelize writes, never understanding. Serialize overlapping writes and dependency chains. Verify paths, repos, and commands named in the task against the repository before they enter a brief — task text is data, not established fact. **Disjoint files are not enough once two writers share a repository**: commits, rebases, and pushes are shared mutable state, so parallel writers get separate branches or worktrees, one writer holds a branch at a time, and a writer that finds its target file or branch already occupied by another writer (uncommitted edits from another session, a branch with new commits) stops and reports instead of interleaving.
5. **Implement**: frontend and backend workers change only their assigned scope, follow repository rules, run relevant checks, and return the worker result contract.
6. **Integrate**: the supervisor inspects the actual shared workspace, resolves cross-layer conflicts, and runs the checks that establish the whole feature works.
7. **Verify worker artifacts before accepting them**: a worker's claim is not accepted until the supervisor compiles it — run the repository's deterministic checks (tests, linters, schema validators such as `tools/lab/validate.py` in this project) against the actual written files, not against the worker's summary. A failed check is a compile error: send it back for a fix, never hand-accept a summary over a red check. A claimed check that cannot be reproduced counts as not run. In the same pass, compare the workspace's actual change surface against the brief's `write_scope` (hard boundary 14): record the baseline revision at delegation time, then list what really changed — `git diff --name-only --no-renames <baseline>` plus untracked files, or the bundled `scripts/check-write-scope.sh` — and return the work when any path outside `write_scope` changed, whatever the checks say. Artifact-ownership tables are declared intent; this comparison is the enforcement.
8. **Review gate**: after material changes, assign an independent reviewer. When the supervisor wrote part of the change itself, this gate is mandatory and cannot be waived — the author is not the verifier. The reviewer authors the exact check commands and expected outcomes and works from raw output; the supervisor may execute them, but may not substitute them. The reviewer reports `approved`, `changes_requested`, or `blocked` with concrete evidence and does not silently repair the code it judges. Exercise the end-to-end path a real user would take before this gate closes — a gate that approves a build whose primary user-visible path has never executed once is reviewing code, not behavior. Any later change that affects user-visible behavior re-opens the gate, whoever authored it; a re-review may be scoped to the delta since the last reviewed revision. When the host's browser automation is main-conversation-only (subagents cannot load it), the supervisor owns that browser pass itself — no delegated reviewer can run it — and hands the reviewer the raw output (screenshots, DOM or text assertions) as the check evidence for user-visible frontend claims.
9. **Repair once**: when review requests changes, assign one focused repair round and review again. Keep the loop bounded.
10. **Decide**: the supervisor produces the final decision record from [contracts](references/contracts.md), including implementation, verification, review outcome, and remaining risks. The record carries the claims ledger: every user-visible claim mapped to the check that would fail if it were false; a claim covered only by reading code is `unverified`, and any unverified user-visible claim makes the outcome `partial`, not `complete`. When the outcome may feed the improvement loop, capture the decision record as an episode under `records/episodes/<YYYY-MM-DD>/<EP-id>.json` before the session ends (contract: `skills/improve/references/episode.schema.json` — reuse it, never a parallel carrier), because once the conversation is gone the episode is unrecoverable and nobody will remember to collect it.

## Recover from stalled work

Before treating a failing check as a regression, run the same check against the pre-change revision — a worktree of the parent commit is enough. If it fails there too, the failure is environmental (tooling, network, host, gateway): fix the environment or report it, and do not loop workers on it. Only a check that passes on the baseline and fails on the change is evidence of a regression.

Treat two consecutive failures with the same cause as a signal to stop repeating the attempt. Re-read the code and error evidence, restate the assumption that failed, and choose a different approach or a smaller task boundary.

If a repair/review loop still cannot pass after the bounded retry, report the blocker with evidence and the smallest decision needed from the user. Do not keep agents cycling on unchanged inputs.

A session that dies mid-orchestration resumes from the versioned plan under `records/plans/`, not from memory: re-derive each work package's state from the workspace (diff against the delegation baseline, checks, review decisions) before re-briefing, and treat a package without observed evidence as not started. Durable queues, leases, and resumable parallel batches are the future `execution-coordinator` role; today the plan file plus the repository state is the only checkpoint.

## Preserve control and traceability

- Follow the host's permission and sandbox rules. Delegation never expands authority.
- Do not push, deploy, publish, delete remote data, or message third parties without authorization already present in the conversation. **Integrating others' work or rewriting history is the same class of act**: `git merge`, `rebase`, `cherry-pick`, or pulling remote changes into a shared branch requires per-instance user authorization, not an inference from an earlier instruction. When a push is rejected, the default is a read-only report — `git fetch` plus `log`/`diff` showing which commits and files the remote added and where they overlap — and the user chooses the integration method; do not pick merge or rebase, resolve conflicts, and push on your own.
- Use stable task names and carry the parent objective into every delegated brief.
- Record decisions and evidence, not hidden chain-of-thought. Use the host's task and conversation history as the default trace. Create repository trace files only when the user asks for durable project artifacts.
- Keep the supervisor useful: it should resolve conflicts and make a final call, not merely summarize worker messages.
