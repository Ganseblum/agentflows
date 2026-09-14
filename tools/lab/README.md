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

`validate.py artifacts` additionally validates plan and bug-record instances actually written
under `records/` (recursive) against the same schemas and invariants; `all` includes it.
This is the compile step for supervisor artifact acceptance: run it against the real files
before accepting a worker's record, and treat failures as compile errors.

`validate.py protected` checks that [`protected-paths.txt`](../../protected-paths.txt) still covers
every required gate path — the evaluator and governor roles, the evaluation suite, the measurement
path, the release rules, and the result schemas. `all` includes it, so a candidate cannot quietly
trim the gate surface it is judged by.

`validate.py installed` compares the runtime components of the source checkout (`agents/`,
`skills/`, the manifests) against an installed plugin snapshot, defaulting to the ZCode cache for
the version in `plugin.json` (override with `--path <dir>`). A stale or absent snapshot is a
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

See [adapter-protocol.md](adapter-protocol.md) for the host adapter boundary. Candidate
worktrees and private holdouts must be outside the public repository and outside each other;
`isolation.py` checks that layout and rejects forbidden candidate paths before a release gate.
`isolation.py check-diff` reads `protected-paths.txt` by default, so the forbidden set is declared
in the repository rather than passed ad hoc; `--forbidden` overrides it and `--protected-file`
points at a different list.
