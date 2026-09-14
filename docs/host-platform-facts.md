# Host platform facts

Every row below was observed directly on this machine unless its evidence is marked `doc`;
`doc` rows come from the host's official guide and have not been exercised by a run. Each row
names its evidence and its scope. Do not generalize a fact beyond its scope row. Re-verify by
re-running the named check, not by editing this file.

Last verified: 2026-09-14. Hosts: Claude Code `2.1.268`, Codex CLI `0.154.0`, ZCode (desktop).

## ZCode (desktop)

| # | Fact | Evidence | Scope | Consequence |
| --- | --- | --- | --- | --- |
| Z1 | A plugin installs from a local-directory marketplace and is cached as a version-keyed snapshot copy; source edits do not update the installed copy. | Observed: `known_marketplaces.json` records `source: directory`; cache holds `agentflow-local/agentflow/0.3.1/`; installed and source files differ in inode while byte-identical. | ZCode desktop, local directory marketplace | Updating requires refreshing the marketplace and reinstalling; the workspace skill symlinks (`<repo>/.zcode/skills/`) remain the live-edit path for **skills only**. Run `python3 tools/lab/validate.py installed` to see the drift. |
| Z2 | Skill discovery order puts workspace `.zcode/skills/` above plugin-provided skill roots, and the first same-named skill wins. | `doc` (ZCode configuration guide) + observed symlink layout | ZCode | In this repository the workspace copy hides the installed plugin's copies of `agentflow`/`improve`; test the plugin copy in another workspace. |
| Z3 | Skill triggering is model-decided from `name`, `description` (truncated to ~250 characters when presented) and `when_to_use`; there is no keyword matcher. | `doc` (diagnosing-skills) | ZCode | Trigger wording must be front-loaded within the first ~250 characters; a description over 1024 characters drops the skill entirely. |
| Z4 | Plugin-provided agents **do** surface as subagents, and the frontmatter `tools` allowlist **is** enforced: the host presents `bug-fixer` with `(Tools: Read, Glob, Grep, Write, Edit, Bash)` while the three agents that declare no `tools` field are presented with the full tool set. Both the namespaced (`agentflow:bug-fixer`) and the bare name are registered. | Observed: host subagent registry listing, session of 2026-09-14 (resolves the earlier conflicting `doc` rows) | ZCode desktop, plugin install | A role without a `tools` allowlist inherits delegation (`Agent`), network, and MCP tools. Declare `tools:` on every role that should not have them. |
| Z5 | Agents load from the installed plugin snapshot, and `agents/` has **no** workspace live-edit path (no `.zcode/agents/`, and `config.json` has no `agents` key). A stale snapshot is therefore invisible while a role runs. | Observed: source-vs-cache diff (all 12 agents and both skills differed); `validate.py installed` reproduces it. | ZCode desktop, plugin install | A role edit does not take effect until the plugin is reinstalled. Treat "the role behaves as before" as unverified until `validate.py installed` passes. |
| Z6 | `maxTurns` in agent frontmatter is declared but its enforcement on this host is unverified; the field is carried over from the Claude Code agent format. | Not exercised — no observed truncation | ZCode desktop | Do not treat a turn cap as a safety control until a run demonstrates truncation. Budget discipline in the role contracts covers the gap. |

## Claude Code

| # | Fact | Evidence | Scope | Consequence |
| --- | --- | --- | --- | --- |
| C1 | `--json-schema` rejects a schema document that carries the Draft 2020-12 `$schema`/`$id` declaration. | Adapter smoke failed in ~1 s with `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`; stripping `$schema`/`$id` before passing the schema succeeded (`host_adapter.host_output_schema`). | `claude --print` with `--json-schema` | Pass structured-output schemas without meta-declarations; the schema body still fully constrains output. |
| C2 | In `--print` mode, `--permission-mode acceptEdits` does not auto-approve sensitive-path writes or approval-gated Bash. | AF-002 diagnostic: subagent `Write` to a `plans/…json` path returned `classified as sensitive and not created`; a validator `Bash` call returned `required approval and was not run`. | `--print` eval invocations | The `read-write-workspace` profile does not guarantee write access to `plans/` in evaluations; profile semantics must be aligned (e.g. explicit tool permissions) before results from plan-writing cases are meaningful. |
| C3 | `claude --print` inherits user-level configuration: connected MCP servers and global slash commands appear in the session `init` event. | AF-002 stream: `mastergo-magic-mcp` connected, ~40 global slash commands listed. | Any invocation on this machine | Evaluation runs carry user-config noise (latency, cost, reproducibility) until isolated; `--strict-mcp-config` and `--setting-sources` exist (`flag`, unverified) as candidate isolation flags. |
| C4 | Structured output via `--output-format json` returns the constrained object inside `.result` as a JSON string. | Adapter `parse_structured_output` unwraps it; AF-001/AF-002 runs produced valid objects. | `--print` + `--json-schema` | Adapters must parse the `result` field, not the raw stdout object. |
| C5 | A single case can take minutes to tens of minutes and spawn subagents. | AF-001: 137–212 s per invocation. AF-002: ~23.8 min, 40 turns, 4 subagents, ~$4.05. | This machine's gateway (`api.360.cn` ccmax), `fable`/opus-class routing; not a Claude Code property | Per-invocation timeouts must cover the slowest multi-agent case (900 s was insufficient); the adapter aborts a whole run on one timeout (all-or-nothing). |
| C6 | Model labels cannot be trusted through a custom gateway: assistant events reported `model: gpt-5.5` while CLI `modelUsage` recorded `anthropic-ccmax/claude-opus-4-6` for the same run. | AF-002 stream analysis (157 assistant events vs. final `modelUsage`). | This machine's gateway only | Treat model labels as unverified; record the observed context; do not claim comparable baseline/candidate results from this environment. |
| C7 | Agent-frontmatter tool allowlists (`tools`, `disallowedTools`) are tool-level only; the format has no path scoping. | Frontmatter format in `agents/*.md`; no path syntax exists in the declaration. | Plugin agent format | Path boundaries (e.g. "only `records/bugs/`") cannot be host-enforced per agent; they remain role-matrix + supervisor diff checks. |

## Codex CLI

| # | Fact | Evidence | Scope | Consequence |
| --- | --- | --- | --- | --- |
| X1 | `codex exec` supports `--ephemeral`, `--skip-git-repo-check`, `--cd`, `--model`, `--sandbox`, `--output-schema`, `--output-last-message`, `--color`. | `codex exec --help` on 0.154.0 (`flag` for combination use). | `codex exec` | The adapter command shape is compatible; a real Codex model run has not been executed yet (dogfood pending). |
| X2 | Codex has no per-invocation local plugin binding; candidate-source evaluation fails closed by design. | `host_adapter.validate_request` refuses `source_kind=candidate` on codex; documented in `tools/lab/adapter-protocol.md`. | Current Codex CLI | Codex can evaluate installed baselines only; never label an installed-source result as a candidate result. |

## Re-verification

- C1/C4: re-run the adapter smoke (`tools/lab/host_adapter.py --host claude` with a one-case request).
- C2/C3/C5/C6: re-run one case with `--output-format stream-json` and inspect the `init` event, tool results, and final `modelUsage`.
- X1: `codex exec --help`; X2: attempt a `source_kind=candidate` request against the codex adapter.
- Z1/Z4/Z5: `python3 tools/lab/validate.py installed` (fails while the snapshot lags the source); inspect the subagent registry to re-check the `tools` allowlist.
- Z6: run a role with a deliberately large task and observe whether the host stops it at `maxTurns`.
