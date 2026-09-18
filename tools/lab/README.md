# Agentflow Lab

This directory contains maintenance tools for schema validation, deterministic policy checks,
and baseline/candidate evaluation tooling. Lab tools may read evidence and invoke an explicitly
isolated host runner, but they must not become a second chat CLI or model orchestration runtime.

The first dependency-free tool validates the P0 contracts and public fixtures:

```sh
python3 tools/lab/validate.py all
```

It validates the Draft 2020-12 vocabulary used by this repository, then checks record status
rules, plan dependency graphs and public fixture references. A failing check returns exit code 1.

`validate.py artifacts` additionally validates the record instances actually written under
`records/` (recursive) — bug records, recurrence ledgers, review records, episodes, and
plans — against the same schemas and body assertions; `all` includes it.
This is the compile step for supervisor artifact acceptance: run it against the real files
before accepting a worker's record, and treat failures as compile errors.

`validate.py mock` (in `all` since 0.8.0) compiles the demo fixtures under `mock/records/` the
same way: it copies the repository tree into a temporary directory, overlays `mock/records/`
onto the copy's `records/`, and runs the full artifacts check there — so a fixture that drifts
from a contract, or an id that collides with a real record, fails the gate instead of waiting
for someone to redo the manual merge experiment. The real `records/` tree is never mutated.

`validate.py protected` checks that [`protected-paths.txt`](../../protected-paths.txt) still covers
every required gate path — the evaluator and governor roles, the evaluation suite, the measurement
path, the release rules, the record schemas, and the regression tests for the gate tools. `all`
includes it, so a candidate cannot quietly trim the gate surface it is judged by.

`validate.py manifests` requires the five hand-synced manifests (`plugin.json`,
`marketplace.json`, `.zcode-plugin/`, `.claude-plugin/`, `.codex-plugin/`) to agree on the plugin
name and version; a missed bump would otherwise surface only after a host reinstall.

`validate.py tests` asserts the declared contents of `tests/` and runs
`python3 -m unittest discover -s tests` with `PYTHONDONTWRITEBYTECODE=1`. Both are in `all`. The
tests pin `validate.py` and `isolation.py`, so a failure is a gate regression. The test files are
protected individually rather than by directory prefix: protecting `tests/` outright would block on
`tests/__pycache__/*.pyc`, which any candidate carries after running the checks, and a gate that
fails honest work invites bypass. The declared-content assertion rejects every undeclared entry,
directories included, and the reason is a demonstrated bypass: `unittest discover` imports packages
found in subdirectories, and import-time code runs before any assertion — an added subdirectory
whose module replaces a pinned test method makes a broken assertion pass and the gate return PASS.
(A stray `tests/__init__.py` is inert under `discover -s tests` and only imports when discovery
starts from the repository root; the entry check rejects it regardless.) Running lab tools inside a
candidate worktree still leaves `__pycache__` entries in `check-diff`'s changed paths, because that
check includes ignored files; they are listed, not blocked.

`validate.py docs` asserts the hand-synced role/document surface: every agent file's
frontmatter name equals its filename, every `agentflow:<role>` referenced by a SKILL
resolves to an agent file, every `schemas/*.schema.json` path named in the docs/records/
skills/agents surface exists, and the Chinese mirror's schema-reference set matches
`contracts.md`'s. `all` includes it.

Two read-only retrospective tables print and exit without validating: `validate.py report
[--project X] [--status Y] [--provenance Z]` (the bug-record table, provenance as the last
column) and `validate.py recurrence` (per-class consolidation state and the derived tier —
`single` / `recurred` / `escalated`).

`validate.py installed` compares the runtime components of the source checkout (`agents/`,
`skills/`, the manifests) against an installed plugin snapshot, defaulting to the ZCode cache for
the version in `plugin.json` (override with `--path <dir>`). A stale or mismatched snapshot is a
failure; the check exits 0 with `SKIP` when no local install exists at all. It is deliberately
**not** part of `all`: it reads outside the repository, and a clone or a candidate worktree must not
fail repository validation. Run it before a dogfood run and after changing any role, because hosts
execute roles from the snapshot rather than from the working tree.

The remaining P0 tools are explicit and deterministic:

```sh
python3 tools/lab/eval_runner.py run --help
python3 tools/lab/eval_runner.py compare --help
python3 tools/lab/host_adapter.py --help
python3 tools/lab/artifact_digest.py --root .
python3 tools/lab/policy.py --help
python3 tools/lab/isolation.py --help
```

Before starting a model, validate an adapter request and inspect its resolved workspace,
permission arguments, plugin directory, and invocation count with `host_adapter.py --dry-run`.
This still refuses invalid isolation layouts and unsupported candidate bindings.

Pass `--progress <jsonl>` to append one diagnostic record per invocation (`start`,
`completed`, `failed`); the adapter also prints a stderr status line per invocation. A run
is all-or-nothing: one invocation failure aborts it, so size `--timeout-seconds` for the
slowest expected multi-agent case and use the progress file to locate a failure.

Business suites (`--suite evals/business`) add a request-level `business_root` (the pinned
read-only snapshot, fourth isolation position) and six per-case fields (`target_id`, `target_pin`,
`target_docs`, `seeds_ref`, `findings_contract`, `grading`); a real run also requires `--seed-patch`.
After every host call the adapter re-checks the snapshot's changed file set and `git diff` digest,
and `seed_grader` then overwrites the host's self-reported `accepted`/`escaped_defects`.

See [adapter-protocol.md](adapter-protocol.md) for the host adapter boundary. Candidate
worktrees and private holdouts must be outside the public repository and outside each other;
`validate-layout` accepts an optional `--business-root`, a fourth position (a business task
snapshot root) that must not overlap or nest with any of the other three. `isolation.py` checks
that layout and rejects forbidden candidate paths before a release gate.
`isolation.py check-diff` always reads `protected-paths.txt` from the trusted checker repository, parses Git paths with NUL framing, rejects overlapping checker/candidate roots, and requires
`--base <frozen-parent-revision>`. The base is mandatory so committed, staged, unstaged, deleted,
renamed, ignored, and untracked changes are all considered; there is no command-line replacement
for the protected set. Invoke the script from a trusted source checkout, not a candidate-controlled
copy of the tool or the protected list.
