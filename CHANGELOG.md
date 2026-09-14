# Changelog

## Unreleased

- Require a frozen parent revision for candidate protected-diff checks and remove command-line
  replacements for the protected path set.
- Tighten the dependency-free validator's JSON Schema equality and RFC 3339 date-time handling.
- Clarify host-specific installation drift, Bash/network boundaries, and the current evaluation
  readiness limits in the documentation.

## 0.3.3 — 2026-09-14

Boundary-hardening release after reviewing the role set against the host's actual enforcement.

### Boundaries

- **Tool allowlists on the implementation roles.** `backend-engineer`, `frontend-engineer`, and
  `candidate-engineer` now declare `tools: Read, Glob, Grep, Write, Edit, Bash`, matching
  `bug-fixer`. Previously they inherited the full tool set, including delegation, network, and MCP
  tools, which contradicted hard boundary 2 (delegation never expands authority) and let a worker
  start subagents of its own.
- **A declared candidate gate surface.** New [`protected-paths.txt`](protected-paths.txt) is the
  single source for the paths a candidate may never edit (evaluator and governor role files, the
  evaluation suite, the measurement path under `tools/lab/`, the release rules, the result schemas,
  and the list itself). `isolation.py check-diff` reads it by default instead of requiring
  `--forbidden` from the caller; `validate.py protected` fails if the list stops covering a required
  gate path, and `all` includes it.
- `candidate-engineer`'s ownership matrix now names the protected list explicitly, closing the
  contradiction between "write the candidate tree" and "never edit the judging gate" when the
  candidate tree *is* the plugin.
- Hard boundaries: #1 now makes the independent review gate mandatory when the supervisor writes
  part of the change; #2 forbids worker re-delegation; #6 points at the declared list; new #11
  requires a budget-stopped run to report `partial`.
- The reviewer's check protocol is explicit: the reviewer authors the exact commands and expected
  outcomes and requires raw output, because the author of a change may execute a check but may not
  choose it.

### Reliability

- Budget discipline on every writing role: reserve the final turn for the worker result, and never
  report `complete` for a truncated run. Implementation roles raised to 30 turns, Plan Architect to
  20. (`maxTurns` semantics are host-supplied and not yet verified on ZCode.)
- `validate.py installed` compares the runtime components (`agents/`, `skills/`, manifests) of the
  source checkout against the installed plugin snapshot. Hosts load agents from the snapshot, so
  source edits to a role do not take effect until the plugin is reinstalled; this check makes that
  drift visible instead of silent. It stays out of `all` because it reads outside the repository.

### Evaluation

- Four new public cases: `AF-011` (a worker summary is not verification), `AF-012` (task text is
  data, not instruction), `AF-013` (a candidate may not edit the gate that judges it), `AF-014`
  (baseline comparison separates environment failure from regression). Suite is now 14 cases.

### Documentation

- Observed ZCode facts updated: plugin agents do load from the installed snapshot and do honor the
  frontmatter `tools` allowlist; `agents/` has no live-edit path.
- Repository naming normalized to "Agentflow"; stale `0.3.1`/`plans/` references corrected.
- New [`AGENTS.md`](AGENTS.md) with the working rules for this repository.

## 0.3.2 — 2026-09-14

First update release after real-model dogfood and the ZCode host integration.

### Host adapter

- Strip `$schema`/`$id` meta-declarations before passing schemas to Claude Code `--json-schema` (current CLI builds reject Draft 2020-12 declarations at load time).
- Add `host_adapter.py --progress <jsonl>` per-invocation diagnostics and a stderr status line per invocation; a run still fails closed, but failures are now attributable to a case and repetition.
- Document the host adapter protocol's progress option and schema handling in `tools/lab/adapter-protocol.md`.

### Role contracts

- Add artifact-ownership declarations to all 12 agent files: per-artifact tables for the six writing roles, compact statements for the six read-only roles.
- Remove duplicated constraint wording introduced alongside the ownership declarations.

### Workflow discipline

- Supervisor step "Verify worker artifacts before accepting them": deterministic checks run against actual files; failed checks are compile errors; unreproducible checks count as not run.
- Improvement-loop step 9: candidate, evaluation, comparison, and decision records are schema-validated before the next role consumes them.
- Consolidated 10-item hard-boundaries list in `skills/agentflow/references/contracts.md` (single source; both skills reference it).
- Treat task text as data: paths, repos, commands, and versions are verified against the repository before entering a brief.
- Baseline triage in "Recover from stalled work": run the failing check against the pre-change revision before calling a regression.

### Records

- Bug records are now Markdown with validated YAML frontmatter instead of JSON: human-readable body (Symptom / Problem code / Root cause / Fix / Review) plus machine-checked metadata, one file per bug under `records/bugs/<YYYY-MM-DD>/<kebab-slug>.md`.
- New frontmatter fields: `error_kind` (ai-ignored-doc, ai-ignored-code, missing-constraint, hallucination, logic-error, host-compat, environment, other), `project`, and `files` (the affected paths).
- Archive: `rejected` records must move to `records/bugs/archive/<same-date-dir>/`; `verified` records stay in place as reference. Both rules are enforced by the validator.
- Plans remain JSON under `records/plans/<plan_id>.json` with required `recorded_at` and ordered `updated_at`.
- New `validate.py report` command prints the chronological bug table (date, id, status, severity, error kind, title).
- All durable artifacts unified under `records/`; `records/README.md` documents layout, conventions, and retrospective queries.

### Tooling

- `tools/lab/validate.py` new `artifacts` target (included in `all`): validates plan and bug-record instances actually written under `records/` (recursive).

### Documentation

- New `docs/host-platform-facts.md`: observed Claude Code / Codex CLI / ZCode behaviors with evidence and scope.
- Fix stale repository state in README, handoff, self-improvement design, and evals README (remote status, runner existence, tool maturity, machine paths).
- Record dogfood evidence: AF-001 smoke pass, AF-002 latency/permission/model-label findings, environment blockers for the full baseline run.

### Hosts

- Add `.zcode-plugin/plugin.json` and a local `marketplace.json`; the plugin now installs from a local directory into ZCode (skills and agents components).
- Front-load trigger wording in both skill `description` fields so the complete "when to use" condition survives ZCode's ~250-character truncation when the model decides whether to invoke a skill.
