---
name: improve
description: Use only when the user asks to evolve, optimize, evaluate, version, promote, or roll back the Agentflow plugin or its role instructions. Runs a governed improvement cycle from explicit user feedback and real task outcomes: evidence triage, one bounded candidate, independent baseline comparison, and an auditable release or rollback decision.
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
- In ZCode, prefer the same plugin agents (`agentflow:feedback-analyst`, `agentflow:candidate-engineer`, `agentflow:evaluator`, `agentflow:release-governor`) plus `agentflow:bug-investigator` when evidence collection needs a read-only diagnosis. Agent roles load from the installed plugin snapshot, so a role-instrument change is only observable after a reinstall; check `python3 tools/lab/validate.py installed`.

If the host cannot provide independent agents, prepare a proposal but do not claim independent evaluation or automatic promotion.
Treat role separation as procedural unless the host actually enforces separate tool allowlists and workspaces. Never claim the candidate is isolated merely because its prompt says not to edit protected files.

The candidate write scope excludes every path declared in [`protected-paths.txt`](../../protected-paths.txt) — the evaluator and governor role files, the evaluation suite, the measurement path under `tools/lab/`, the release rules, the result schemas, and the list itself. Enforce it with `isolation.py check-diff` before the candidate is evaluated, not by reading the candidate's summary. Session-enforced tool allowlists (`tools:` in the agent frontmatter) are the second layer; path exclusions still depend on this check plus a supervisor diff review.

## Run the improvement loop

1. **Freeze the baseline**: identify the current plugin version, source revision, relevant Skill and Agent files, evaluation suite revision, and host/model settings.
2. **Collect episodes**: use explicit user feedback, acceptance results, test outcomes, reviewer decisions, regressions, reversions, incidents, and available task summaries. Absence of complaints is not success. Do not claim access to past sessions the host cannot expose.
3. **Protect the corpus**: remove credentials and unnecessary personal or project data. Preserve source and consent metadata without copying sensitive transcript content into the plugin.
4. **Attribute failures**: separate prompt or role-policy failures from missing context, tool failure, model limits, repository defects, and environment failure. Change Agentflow only when evidence points to Agentflow.
5. **Write one hypothesis**: state the observed pattern, proposed mechanism, affected files, expected improvement, regression risk, and rejection criteria.
6. **Predeclare evaluation**: choose primary success metrics, guardrails, task slices, minimum evidence, and the holdout cases before implementing the candidate.
7. **Create a candidate**: edit the canonical source or an isolated branch/worktree. Do not edit the installed live copy. Keep evaluator rules, the declared protected paths, and holdout answers outside the candidate's write scope. Freeze the parent revision first, then run `isolation.py check-diff --candidate <tree> --base <frozen-parent-revision>` from the trusted source checkout before evaluation so committed, staged, unstaged, deleted, renamed, ignored, and untracked changes are all compared. The check always reads the trusted checkout's `protected-paths.txt`, so the gate surface is declared rather than recalled; changing the protected-file source or using an override policy is itself a human-reviewed gate change.
8. **Compare fairly**: have an isolated runner execute baseline and candidate on the same cases and settings. Include representative successes, known failures, edge cases, and adversarial cases. Give the evaluator immutable result records rather than permission to run candidate-controlled commands. Record task-level results, cost/latency when available, and uncertainty.
9. **Compile artifacts before consuming them**: every record the loop exchanges — candidate record, evaluation result, comparison, release decision — is validated against its schema (`tools/lab/validate.py`, `eval_runner.py validate`) before the next role reads it. An invalid record is a compile error: fix the record, never quote or forward it as evidence. A result that cannot be produced by the frozen runner counts as no result.
10. **Independent review**: the evaluator reports evidence without repairing the candidate. The release governor returns `promote`, `revise`, `reject`, or `rollback`.
11. **Prepare the release**: bump version, record parent version, changed components, evidence, evaluation results, approvals, rollout policy, and rollback target.
12. **Request the gate**: in the default mode, present the complete candidate and evaluation to the user for one final promotion decision. Do not publish, reinstall, or replace the active version before that approval.
13. **Monitor after promotion**: compare canary outcomes with the baseline guardrails. Roll back to the immutable previous version when a declared threshold fails.

## Promotion modes

- **proposal**: analyze evidence and propose a hypothesis; make no source change.
- **human-gated**: create and evaluate a candidate, then wait for the user to promote it. Use this by default.
- **canary**: automatically expose an approved low-risk candidate to a bounded task slice with predetermined rollback thresholds.
- **automatic**: reserve for mature, statistically supported workflows. Do not enable it merely because a few tasks succeeded.

Changes to permissions, tool access, hooks, MCP connections, release policy, evaluator instructions, holdout data, or automatic-promotion thresholds always require human review. Never let a candidate relax the gate used to approve itself.

The hard-boundary list in the agentflow skill's [contracts](../agentflow/references/contracts.md#hard-boundaries) applies to every improvement role as well.

## Stop bad loops

If two candidate cycles fail for the same reason, stop generating variants. Revisit attribution, data quality, evaluator validity, and whether the host or model is the real constraint.

Prefer no release over a weakly supported release. A neutral result is not an improvement.
