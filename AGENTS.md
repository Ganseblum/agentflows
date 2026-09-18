# Agentflow repository rules

Rules for any agent working in this repository. They apply to every session, whether or not the
`agentflow` skill is active.

## Before accepting any artifact

Run the deterministic checks against the actual files — not against a summary:

```sh
python3 tools/lab/validate.py all
```

`all` covers the schemas, the examples, the public evaluation cases, the records under `records/`,
the integrity of the protected gate list, manifest name/version agreement across the five
manifests, and the repository's own regression tests under `tests/`. A failing check is a compile
error: fix it or return it to the worker with the output. A check you cannot reproduce counts as
not run, never as a pass.

The tests can also be run directly while iterating:

```sh
python3 -m unittest discover -s tests
```

## Editing a role or a skill

- `agents/*.md` and `skills/**` are loaded by a host from its **installed plugin snapshot**, not
  from this working tree. A source edit does not change what a host runs until the plugin is
  reinstalled. Check for drift with:

  ```sh
  python3 tools/lab/validate.py installed
  ```

  It reports a stale or absent install as a failure and compares the runtime components file by
  file. Run it before any dogfood run and after changing a role.
- The same check exits 0 with `SKIP` when no local install exists (a clone, a CI job, a candidate
  worktree), so it is safe to run anywhere.
- Frontmatter fields are host features: `tools` and `disallowedTools` are enforced by the host,
  `maxTurns` is declared but unverified. Do not add a field expecting enforcement without evidence.

## Never edit the gate

[`protected-paths.txt`](protected-paths.txt) declares the paths a candidate may not edit: the
evaluator and governor role files, the evaluation suite, the measurement path under `tools/lab/`,
the release rules, the record schemas under `schemas/`, the pinned regression test, and the list
itself. `tools/lab/isolation.py check-diff` enforces it against a candidate diff, and
`validate.py protected` fails if the list stops covering a required entry.

Changing a protected path, the required-entry set in `tools/lab/validate.py`, or the release policy
is a gate change and requires explicit human review. Do not route around the check. Because
`schemas/` and the pinned test are inside the gate, a legitimate contract change or a gate-tool fix
is a human-authored change; a candidate proposes it instead of making it. Adding a test file — or
any other entry in `tests/`, including a subdirectory — means declaring it in `EXPECTED_TEST_FILES`
in `validate.py` and protecting it in `protected-paths.txt` in the same change.

## Working in this repository

- Records live under `records/`; see [records/README.md](records/README.md) for layout and queries.
- Bug records and plans are Markdown with validated YAML frontmatter. A plan file is named
  exactly `<plan_id>.md` (shape: `records/plans/README.md`); a bug record file is a kebab-case
  slug under `records/bugs/<YYYY-MM-DD>/`. The supervisor assigns every record path explicitly.
- Do not commit, push, or publish unless the user asks. Do not claim a walkthrough of host behavior
  you have not observed — record it in [docs/host-platform-facts.md](docs/host-platform-facts.md)
  with its evidence, scope, and a re-verification method instead.

## Experiments and recovery

These rules came from BUG-20260915-002; they are process controls, not suggestions.

- Fault injection and mutation testing run only on a throwaway copy (`cp -r` the checkout to
  `/tmp`), never on the working tree.
- Never use `git checkout` / `git restore` to undo an experiment on the real tree. On a tracked
  file they reset to the committed version and silently discard uncommitted work — the exact
  opposite of an undo.
- A recovery or restore counts only after the relevant check has been re-run and observed green.
  An unobserved recovery is not a recovery, exactly as an unreproducible check counts as not run.
- Do not suppress command output (`2>/dev/null` and friends) on any command whose success you
  intend to claim. A claim about how a tool behaves needs the exit code and verbatim output, not
  reasoning (hard boundary 12).
