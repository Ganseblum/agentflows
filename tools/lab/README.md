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

The remaining P0 tools are explicit and deterministic:

```sh
python3 tools/lab/eval_runner.py run --help
python3 tools/lab/eval_runner.py compare --help
python3 tools/lab/host_adapter.py --help
python3 tools/lab/artifact_digest.py --root .
python3 tools/lab/policy.py --help
python3 tools/lab/isolation.py --help
```

See [adapter-protocol.md](adapter-protocol.md) for the host adapter boundary. Candidate
worktrees and private holdouts must be outside the public repository and outside each other;
`isolation.py` checks that layout and rejects forbidden candidate paths before a release gate.
