# Host adapter protocol

`eval_runner.py run` sends one JSON request to an explicitly supplied adapter command.
The repository includes `host_adapter.py`, which translates that request to either
`codex exec` or `claude --print` when invoked explicitly.

The Claude path can load the candidate worktree with `--plugin-dir`. The Codex CLI path
is intentionally fail-closed for `source_kind=candidate` because the current CLI exposes
no per-invocation local Plugin source binding; it must not silently evaluate an installed
baseline while labeling the result as a candidate.
The adapter runs the requested host/model/permission configuration and returns one JSON
object on stdout:

```json
{
  "observed_context": {
    "host": "codex",
    "model": "example-model",
    "permissions_profile": "read-write-workspace",
    "fixture_revision": "fixture-001",
    "evidence_refs": ["adapter://codex/smoke-001"]
  },
  "case_results": [
    {
      "case_id": "AF-001",
      "slice": "role-selection",
      "holdout": false,
      "protected_guardrails": ["permission_violations", "escaped_defects"],
      "repetitions": [
        {
          "accepted": true,
          "first_pass_review": true,
          "correction_count": 0,
          "escaped_defects": 0,
          "permission_violations": 0,
          "unnecessary_delegation": false,
          "tool_failures": 0,
          "latency_ms": 1200,
          "evidence_refs": ["result://AF-001/1"]
        }
      ]
    }
  ]
}
```

The runner owns the execution identity and repeats it in the result manifest. An adapter
cannot change the declared host, model, permissions profile, fixture revision, suite
revision, or repeat count. Baseline and Candidate results are comparable only when these
fields match exactly.

The runner also sends `holdout: false` and the exact per-case repeat count. Holdout cases
are rejected before they reach an adapter. The Adapter response must cover every frozen
case exactly once, preserve its slice/guardrail metadata, provide every repetition, and
return at least one evidence reference for each repetition and the observed context.

Use `eval_runner.py compare` to produce metric deltas, then use `policy.py` with a
predeclared candidate record. The policy result is evidence for a human release gate; it
does not install or publish anything.

Candidate `artifact_digest` values are produced by `artifact_digest.py`. The digest
includes normalized relative paths, regular-file mode bits, sizes, and content hashes;
`.git` and Python cache directories are excluded, symlinks are rejected, and the manifest
format is deterministic.
