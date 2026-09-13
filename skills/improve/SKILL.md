---
name: improve
description: Improve Agentflow itself from explicit user feedback and real task outcomes through evidence triage, bounded candidate changes, independent baseline comparison, and auditable release or rollback decisions. Use only when the user asks to evolve, optimize, evaluate, version, promote, or roll back the Agentflow plugin or its role instructions.
---

# Agentflow Improve

Run a controlled improvement cycle for the Agentflow plugin. The current host supplies the model, tools, permissions, and agents. Do not invoke the standalone Agentflow CLI.

The executing Agent may discover problems and create a candidate, but it must not approve its own evidence or silently replace the installed plugin. Keep analysis, candidate implementation, evaluation, and release decisions as separate roles.

Read [evidence and release rules](references/evidence-and-release.md) before creating a candidate.

## Bind roles to the host

- Use the main task as the **improvement supervisor**.
- Assign a read-only **feedback analyst** to normalize evidence and identify failure patterns.
- Assign a **candidate engineer** to implement one bounded hypothesis in plugin source.
- Assign a read-only **evaluator** that did not implement the candidate.
- Assign a read-only **release governor** to decide whether evidence satisfies the declared gate.
- In Claude Code, prefer `agentflow:feedback-analyst`, `agentflow:candidate-engineer`, `agentflow:evaluator`, and `agentflow:release-governor`.

If the host cannot provide independent agents, prepare a proposal but do not claim independent evaluation or automatic promotion.
Treat role separation as procedural unless the host actually enforces separate tool allowlists and workspaces. Never claim the candidate is isolated merely because its prompt says not to edit protected files.

## Run the improvement loop

1. **Freeze the baseline**: identify the current plugin version, source revision, relevant Skill and Agent files, evaluation suite revision, and host/model settings.
2. **Collect episodes**: use explicit user feedback, acceptance results, test outcomes, reviewer decisions, regressions, reversions, incidents, and available task summaries. Absence of complaints is not success. Do not claim access to past sessions the host cannot expose.
3. **Protect the corpus**: remove credentials and unnecessary personal or project data. Preserve source and consent metadata without copying sensitive transcript content into the plugin.
4. **Attribute failures**: separate prompt or role-policy failures from missing context, tool failure, model limits, repository defects, and environment failure. Change Agentflow only when evidence points to Agentflow.
5. **Write one hypothesis**: state the observed pattern, proposed mechanism, affected files, expected improvement, regression risk, and rejection criteria.
6. **Predeclare evaluation**: choose primary success metrics, guardrails, task slices, minimum evidence, and the holdout cases before implementing the candidate.
7. **Create a candidate**: edit the canonical source or an isolated branch/worktree. Do not edit the installed live copy. Keep evaluator rules and holdout answers outside the candidate's write scope.
8. **Compare fairly**: have an isolated runner execute baseline and candidate on the same cases and settings. Include representative successes, known failures, edge cases, and adversarial cases. Give the evaluator immutable result records rather than permission to run candidate-controlled commands. Record task-level results, cost/latency when available, and uncertainty.
9. **Independent review**: the evaluator reports evidence without repairing the candidate. The release governor returns `promote`, `revise`, `reject`, or `rollback`.
10. **Prepare the release**: bump version, record parent version, changed components, evidence, evaluation results, approvals, rollout policy, and rollback target.
11. **Request the gate**: in the default mode, present the complete candidate and evaluation to the user for one final promotion decision. Do not publish, reinstall, or replace the active version before that approval.
12. **Monitor after promotion**: compare canary outcomes with the baseline guardrails. Roll back to the immutable previous version when a declared threshold fails.

## Promotion modes

- **proposal**: analyze evidence and propose a hypothesis; make no source change.
- **human-gated**: create and evaluate a candidate, then wait for the user to promote it. Use this by default.
- **canary**: automatically expose an approved low-risk candidate to a bounded task slice with predetermined rollback thresholds.
- **automatic**: reserve for mature, statistically supported workflows. Do not enable it merely because a few tasks succeeded.

Changes to permissions, tool access, hooks, MCP connections, release policy, evaluator instructions, holdout data, or automatic-promotion thresholds always require human review. Never let a candidate relax the gate used to approve itself.

## Stop bad loops

If two candidate cycles fail for the same reason, stop generating variants. Revisit attribution, data quality, evaluator validity, and whether the host or model is the real constraint.

Prefer no release over a weakly supported release. A neutral result is not an improvement.
