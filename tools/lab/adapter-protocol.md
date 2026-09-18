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

The runner owns the execution identity and repeats it in the result manifest. Repetition numbers are exactly 1..repeat_count; skipped or fabricated repetitions are invalid, and measured latency is injected by the adapter before schema validation. `accepted` and `escaped_defects` for business cases are grader-owned, not host claims. An adapter
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

Observed host behaviors that constrain this protocol — schema meta-declaration rejection,
print-mode permission boundaries, config inheritance, gateway model-label integrity, and
per-case latency — are recorded with their evidence in
[host platform facts](../../docs/host-platform-facts.md). Update that table from real runs,
not from memory.

For longer runs, pass `host_adapter.py --progress <path>` to append one diagnostic JSONL
record per invocation (`start`, `completed`, or `failed` with elapsed time and error).
Progress records are operator diagnostics only: they are not part of the adapter result,
do not change the evaluation context, and are never consumed by `eval_runner.py`.

Some hosts reject the Draft 2020-12 `$schema`/`$id` declarations inside `--json-schema`.
The adapter strips those two keys before invoking Claude; the schema body still fully
constrains the structured output, and Codex receives the original file path.
