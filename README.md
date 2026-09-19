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
- ZCode: run `python3 packaging/build_runtime.py`, then install from the local marketplace in
  [`marketplace.json`](marketplace.json) (it points at `packaging/runtime`, not this
  directory). Skills resolve through `.zcode/skills/` symlinks, but **agents load from the
  installed snapshot** — after changing `agents/*.md`, regenerate the runtime tree, refresh the
  marketplace and reinstall, then confirm with `python3 tools/lab/validate.py installed`.

## Current maturity

The version is declared once in the five manifests and [CHANGELOG.md](CHANGELOG.md); this file never restates it. The current release provides:

- a shared development Skill and fourteen role profiles: the frontend/backend pair,
  technical director, reviewer, the Investigator → Fixer → Recorder bug chain, plan
  architect, the Test Planner/Executor chain, and the improvement loop's feedback
  analyst, candidate engineer, evaluator, and release governor;
- machine-readable bug, plan, episode, candidate, evaluation-case, evaluation-result,
  and release-record schemas;
- a business-task measurement slice (`evals/business/`) scored deterministically against
  seed defects;
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

`validate.py protected` keeps the list from being quietly trimmed. `validate.py all` runs nine
checks — schemas, examples, evals, record artifacts, the merged mock compile, the protected
list, manifest agreement, the document surface, and the repository's regression tests.

The three Bug roles are selectable capabilities, not a mandatory ceremony for every issue.
Use the full Investigator → Fixer → Reviewer → Recorder flow for material, uncertain,
recurring, cross-layer, or high-risk bugs. The supervisor may combine diagnosis or recording
for a small low-risk bug with a known reproduction, while keeping the same evidence gates.
Plan Architect writes the plan; Supervisor authorizes and coordinates execution. A separate
Execution Coordinator is reserved for a future durable control plane.

The improvement workflow is a governed skeleton. Use `python3 tools/lab/record_store.py index` to build a disposable SQLite FTS5 lexical index, then `query` for explicit retrieval; the source records remain authoritative and no vector database is used. Cross-session telemetry, persistent
retrieval, a private holdout service, canary rollout, and automatic rollback are not
implemented yet. Human approval is the default release boundary.

The workspace contains the P0 implementation slice: Bug Record and Plan contracts, sanitized
positive/negative examples, fifteen public evaluation cases, a dependency-free contract
validator (including the installed-snapshot drift check), an explicit host-adapter result protocol,
isolation checks, a fail-closed Codex/Claude host-adapter wrapper, and a deterministic policy
evaluator. Real model dogfood, private holdout service, and installation/release switch
are still intentionally pending.

## Repository layout

| Path | Contents |
| --- | --- |
| `agents/` | The fourteen role profiles a host loads (the public role surface) |
| `skills/` | `agentflow` (development workflow) and `improve` (governed self-improvement loop), plus their reference contracts |
| `schemas/` | Record and result contracts the compile step enforces (protected) |
| `evals/` | `public/` workflow-decision cases; `business/` instrumented method-measurement cases (protected) |
| `tools/lab/` | Deterministic gate and measurement tooling: `validate.py`, `eval_runner.py`, `host_adapter.py`, `isolation.py`, `policy.py`, `seed_grader.py`, `record_store.py`, `artifact_digest.py` (protected) |
| `tests/` | Pinned regression tests for the gate tools (protected) |
| `records/` | Live evidence: bugs, recurrence ledgers, plans, episodes, reviews, tests, improvement artifacts |
| `examples/` | Validator fixtures — positive, negative, and worked examples |
| `mock/` | Demo record fixtures compiled by `validate.py mock`; never production evidence |
| `docs/` | Design and operations documents; `docs/audit-2026-09-18/` archives the 2026-09-18 audit evidence |
| `packaging/` | Generated ZCode install surface (`build_runtime.py` → `runtime/`); marketplace `source` points here |
| `protected-paths.txt` | The candidate gate surface, declared once |
| manifests | `plugin.json`, `marketplace.json`, `.zcode-plugin/`, `.claude-plugin/`, `.codex-plugin/` |

`docs/audit-2026-09-18/` holds frozen evidence and is not edited; the living ledger for that
audit stays at [`docs/audit-2026-09-18-followups.md`](docs/audit-2026-09-18-followups.md).

## Business evaluation slice

`evals/business/` is the measurement surface for method-level changes — the ones that alter how
roles behave inside business repositories and have no regression signal in `evals/public/`. Three
cases ship now: `BT-001` seed-defect document review, `BT-002` internal contradiction, `BT-003`
cross-document consistency; `evals/business/README.md` documents the layout. A case points at a
pinned, read-only snapshot of a business repository, asks the agent to review a set of documents,
and expects one findings artifact per repetition at
`findings/<case_id>/rep-<n>/findings.json` in the workspace.

Scoring is deterministic and offline. Each case ships an abstracted seed list whose entries carry
the document, a category, and one or more literal anchors; a seed counts as a hit when a finding
names that document and its text contains an anchor. The grader reports `hits`, `missed`, and
`unmatched`; `accepted` becomes "hit rate at or above the case threshold" and `escaped_defects`
becomes the missed-seed count. Unmatched findings — real defects outside the seed list — are
recorded, not penalized. An unknown match strategy, or a missing or unparsable findings artifact,
fails closed instead of scoring zero.

Two parameters carry the snapshot contract. `eval_runner.py --business-root` names the fourth
isolation position (the pinned snapshot root); the adapter rejects a business request whose roots
are missing or nested. `host_adapter.py --seed-patch` names the patch the snapshot was built from:
a real business run requires it, checks the snapshot HEAD against the case `target_pin`, requires
the patch to be cleanly reversible, and re-checks the snapshot file set and the `git diff` digest after every host call.
Business requests must use a `workspace-write` permission profile because the findings artifact is
written into the workspace; the snapshot itself is made read-only when seeded, and only the
sanitized briefs and abstracted seed lists are public. Two additions in the current release
close the measurement-validity gaps: the tested workspace copy must exclude `evals/business/seeds/` —
the adapter fails closed when any `*.seeds.json` is reachable from the model's working
directory, because the answers belong to the trusted fixture root, not the tested tree — and
authoritative runs pass `--allowed-tools` plus `--isolate-host-config`, so permission
semantics and MCP/config isolation are explicit and recorded in `observed_context`.

The slice is instrument-ready, not measured: no baseline/candidate comparison has been produced
yet. The smoke run is blocked on the trusted endpoint, the measured permission profile, and the
snapshot placement decisions, so a method-level change without a matching business case still
releases as `measurement: none`.

Start with [`docs/system-guide.md`](docs/system-guide.md) for the day-to-day walkthrough — how the
workflow flows, how the improvement loop runs, what gets recorded where, and how failures are
handled (with diagrams and worked examples). Then see
[`docs/agent-product-boundary.md`](docs/agent-product-boundary.md),
[`docs/agent-roles.md`](docs/agent-roles.md),
[`docs/self-improvement-design.md`](docs/self-improvement-design.md), and
[`docs/host-platform-facts.md`](docs/host-platform-facts.md) for observed host constraints, and
[`docs/iteration-log.md`](docs/iteration-log.md) for why each version changed.

The source checkout's version lives in the manifests (`python3 tools/lab/validate.py manifests` asserts all five agree). A declared version is not by itself proof that a host is
running that version: ZCode loads installed snapshots and Codex may load a separate plugin cache.
Before dogfood, compare the actual host snapshot with `python3 tools/lab/validate.py installed
--path <installed-plugin-root>` (or the host-specific default) and record the result. Do not switch
an installation until the first human-gated dogfood run uses a verified model endpoint.
