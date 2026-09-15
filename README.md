# Agentflow

Agentflow is a host-native multi-agent development workflow for Codex, Claude Code, ZCode,
and compatible Agent Skills hosts. The host owns models, authentication, tools,
permissions, conversation history, and agent execution. Agentflow supplies role
contracts, delegation rules, independent review, and a governed improvement method.

It does not invoke or require the standalone `agentflow` CLI.

## Use

- Codex: install the Plugin and invoke `$agentflow`. Select **Agentflow Improve** or
  invoke `$improve` only when improving Agentflow itself.
- Claude Code: start development with `claude --plugin-dir .`, then invoke
  `/agentflow:agentflow` or `/agentflow:improve`.
- ZCode: install the plugin from the local marketplace in [`marketplace.json`](marketplace.json)
  (it points at this directory). Skills resolve through `.zcode/skills/` symlinks, but **agents
  load from the installed snapshot** — after changing `agents/*.md`, refresh the marketplace and
  reinstall, then confirm with `python3 tools/lab/validate.py installed`.

## Current maturity

Version `0.3.5` provides:

- a shared development Skill;
- frontend, backend, technical-director, reviewer, bug-investigator, bug-fixer,
  bug-recorder, and plan-architect roles;
- a feedback-analysis, candidate, evaluation, and release-governance workflow;
- machine-readable bug, plan, episode, candidate, evaluation-case, evaluation-result,
  and release-record schemas;
- Codex, Claude Code, ZCode, and portable Agent Plugin manifests.

Implementation roles declare an explicit tool allowlist (`Read, Glob, Grep, Write, Edit, Bash`), so
a worker does not receive the host's native delegation or MCP tools through that allowlist. Bash
still follows the host's sandbox and may have capabilities that are not implied by the tool names;
network isolation must be verified from the host, not inferred from this list.
`bug-recorder` writes only the explicitly assigned sanitized record under `records/bugs/`, and
`plan-architect` writes only the explicitly assigned plan under `records/plans/`. Neither role can
close a bug, authorize code execution, or publish a Plugin. The supervisor must inspect the
resulting paths and verification evidence because the host does not enforce arbitrary path
constraints on the `Write` tool; see [AGENTS.md](AGENTS.md).

The candidate gate surface — the evaluator and governor role files, the evaluation suite, the
measurement path, the release rules, the record schemas under `schemas/`, the pinned regression
test, and the list itself — is declared once in [`protected-paths.txt`](protected-paths.txt).
`isolation.py check-diff` rejects a candidate diff that touches it. Run it from the trusted source
checkout with the frozen parent revision:

```sh
python3 tools/lab/isolation.py check-diff \
  --candidate <tree> \
  --base <frozen-parent-revision>
```

`validate.py protected` keeps the list from being quietly trimmed, and `validate.py all` now also
requires the five manifests to agree on name and version and runs the repository's regression tests.

The three Bug roles are selectable capabilities, not a mandatory ceremony for every issue.
Use the full Investigator → Fixer → Reviewer → Recorder flow for material, uncertain,
recurring, cross-layer, or high-risk bugs. The supervisor may combine diagnosis or recording
for a small low-risk bug with a known reproduction, while keeping the same evidence gates.
Plan Architect writes the plan; Supervisor authorizes and coordinates execution. A separate
Execution Coordinator is reserved for a future durable control plane.

The improvement workflow is a governed skeleton. Cross-session telemetry, persistent
retrieval, a private holdout service, canary rollout, and automatic rollback are not
implemented yet. Human approval is the default release boundary.

The workspace contains the P0 implementation slice: Bug Record and Plan contracts, sanitized
positive/negative examples, fifteen public evaluation cases, a dependency-free contract
validator (including the installed-snapshot drift check), an explicit host-adapter result protocol,
isolation checks, a fail-closed Codex/Claude host-adapter wrapper, and a deterministic policy
evaluator. Real model dogfood, private holdout service, and installation/release switch
are still intentionally pending.

See [`docs/agent-product-boundary.md`](docs/agent-product-boundary.md),
[`docs/agent-roles.md`](docs/agent-roles.md),
[`docs/self-improvement-design.md`](docs/self-improvement-design.md), and
[`docs/host-platform-facts.md`](docs/host-platform-facts.md) for observed host constraints, and
[`docs/iteration-log.md`](docs/iteration-log.md) for why each version changed.

The source checkout currently declares version `0.3.5`. This is not by itself proof that a host is
running that version: ZCode loads installed snapshots and Codex may load a separate plugin cache.
Before dogfood, compare the actual host snapshot with `python3 tools/lab/validate.py installed
--path <installed-plugin-root>` (or the host-specific default) and record the result. Do not switch
an installation until the first human-gated dogfood run uses a verified model endpoint.
