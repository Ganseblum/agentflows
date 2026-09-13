# Agentflow

Agentflow is a host-native multi-agent development workflow for Codex, Claude Code,
and compatible Agent Skills hosts. The host owns models, authentication, tools,
permissions, conversation history, and agent execution. Agentflow supplies role
contracts, delegation rules, independent review, and a governed improvement method.

It does not invoke or require the standalone `agentflow` CLI.

## Use

- Codex: install the Plugin and invoke `$agentflow`. Select **Agentflow Improve** or
  invoke `$improve` only when improving Agentflow itself.
- Claude Code: start development with `claude --plugin-dir .`, then invoke
  `/agentflow:agentflow` or `/agentflow:improve`.

## Current maturity

Version `0.3.1` provides:

- a shared development Skill;
- frontend, backend, technical-director, reviewer, bug-investigator, bug-fixer,
  bug-recorder, and plan-architect roles;
- a feedback-analysis, candidate, evaluation, and release-governance workflow;
- machine-readable bug, plan, episode, candidate, evaluation-case, evaluation-result,
  and release-record schemas;
- Codex, Claude Code, and portable Agent Plugin manifests.

`bug-recorder` writes only the explicitly assigned sanitized record under `records/bugs/`,
and `plan-architect` writes only the explicitly assigned plan under `plans/`. Neither role
can close a bug, authorize code execution, or publish a Plugin. The supervisor must inspect
the resulting paths and verification evidence because the current host does not enforce
arbitrary path constraints on the `Write` tool.

The three Bug roles are selectable capabilities, not a mandatory ceremony for every issue.
Use the full Investigator → Fixer → Reviewer → Recorder flow for material, uncertain,
recurring, cross-layer, or high-risk bugs. The supervisor may combine diagnosis or recording
for a small low-risk bug with a known reproduction, while keeping the same evidence gates.
Plan Architect writes the plan; Supervisor authorizes and coordinates execution. A separate
Execution Coordinator is reserved for a future durable control plane.

The improvement workflow is a governed skeleton. Cross-session telemetry, persistent
retrieval, concrete Codex/Claude host adapters, private holdout service, canary rollout,
and automatic rollback are not implemented yet. Human approval is the default release
boundary.

The standalone workspace now contains the first P0 implementation slice: Bug Record and
Plan contracts, sanitized positive/negative examples, ten public evaluation cases, a
dependency-free contract validator, an explicit host-adapter result protocol, isolation
checks, a fail-closed Codex/Claude host-adapter wrapper, and a deterministic policy
evaluator. Real model dogfood, private holdout service, and installation/release switch
are still intentionally pending.

See [`docs/agent-product-boundary.md`](docs/agent-product-boundary.md),
[`docs/agent-roles.md`](docs/agent-roles.md), and
[`docs/self-improvement-design.md`](docs/self-improvement-design.md).

The local Git baseline is now initialized after the initial role and evaluation contract
review. No remote repository or active host installation has been changed.
