# Evidence and release rules

## Evidence hierarchy

Prefer externally observable signals over an Agent's self-assessment:

1. user acceptance, rejection, correction, or rollback;
2. deterministic tests and acceptance checks;
3. independent reviewer decisions with file-level evidence;
4. task completion, tool errors, retries, latency, and cost;
5. the executing Agent's own summary.

Keep positive and negative episodes. Do not train the workflow only on failures or only on tasks that reached completion.

An episode should record this logical shape. `revision`, `run`, `claims`, and `evidence` make the outcome independently checkable; a `complete` run must not be inferred from an agent summary alone:

```json
{
  "schema_version": 1,
  "episode_id": "stable-id",
  "revision": {"source": "git:<revision>", "base": "git:<parent>"},
  "run": {"run_id": "run-id", "started_at": "2026-09-18T00:00:00Z", "ended_at": "2026-09-18T00:01:00Z", "status": "complete"},
  "claims": [{"claim_id": "C-1", "claim": "the stated outcome", "status": "verified", "check": "command or reviewer", "evidence_ref": "E-1"}],
  "evidence": [{"evidence_id": "E-1", "kind": "test", "ref": "path:line or command output"}],
  "source_type": "user_feedback | acceptance | test | review | incident | rollback",
  "objective": "what the task was expected to achieve",
  "outcome": "accepted | rejected | partial | failed | unknown",
  "signals": [],
  "feedback_summary": "sanitized factual summary",
  "agentflow_version": "0.2.0",
  "host": "codex | claude-code | other",
  "provenance": {"carrier": "<session carrier>", "sanitized": true},
  "redactions": []
}
```

The machine-readable contract is [episode.schema.json](episode.schema.json).

Use stable references to source evidence. Do not store secrets, raw credentials, or unnecessary full transcripts.

## Failure attribution

Classify each material failure before proposing a change:

- `workflow_policy`: role choice, delegation, gate, retry, or decision rule;
- `role_prompt`: one specialist misunderstood its responsibility;
- `context`: required project or task information was absent;
- `tool_or_host`: a host tool, sandbox, permission, or integration failed;
- `model_limit`: the selected model could not reliably perform the task;
- `product_code`: the repository itself was defective;
- `evaluation`: the rubric, fixture, or judge was invalid;
- `unknown`: evidence is insufficient.

Only the first two normally justify changing Agentflow instructions. A context failure may justify a new intake check. Other classes need a fix at their own boundary.

## Release record

The completed release gate produces a record of this shape:

```json
{
  "schema_version": 1,
  "candidate_version": "0.3.0-rc.1",
  "parent_version": "0.2.0",
  "source_revision": "immutable revision",
  "artifact_digest": "sha256:immutable artifact digest",
  "hypothesis": "one falsifiable improvement claim",
  "evidence_ids": [],
  "changed_components": [],
  "risk_class": "low | medium | high",
  "evaluation_suite_revision": "immutable revision",
  "baseline_results": {},
  "candidate_results": {},
  "measurement": {"status": "complete | none", "basis": "business slice or explicit reason"},
  "decision": "promote | revise | reject | rollback",
  "approvals": [],
  "rollout": {},
  "rollback_to": "previous immutable version",
  "protected_slices": ["task-slice-id"]
}
```

Use [candidate.schema.json](candidate.schema.json) for the predeclared candidate,
[eval-case.schema.json](eval-case.schema.json) for frozen cases,
[release-record.schema.json](release-record.schema.json) for the completed gate, and
[comparison.schema.json](../../../schemas/comparison.schema.json) for the runner's
baseline/candidate comparison.

Bind the record to exact source and evaluation revisions and an immutable artifact digest. Do not
reuse results from another candidate. Protected slices are evaluated independently; aggregate
improvement cannot hide a regression in a declared slice.

## Evaluation isolation

- Define the rubric and thresholds before implementing the candidate.
- Keep holdout answers unavailable to the candidate engineer.
- Do not let the same change modify both Agentflow behavior and the gate that judges it.
- Compare baseline and candidate with the same host, model, permissions, fixtures, and repeat count.
- Evaluate by task slice so an average cannot hide a critical regression.
- Treat evaluator disagreement and small samples as uncertainty, not as candidate success.

Recommended primary measures are task acceptance rate, first-pass reviewer approval, correction count, and escaped defects. Guardrails include permission violations, critical regressions, cost, latency, tool failures, and unnecessary delegation.

## Release gate

A candidate may be promoted only when:

- the declared primary metric improves or the candidate fixes a critical defect;
- no protected task slice or safety/permission guardrail regresses beyond its threshold;
- required deterministic checks pass;
- independent evaluation is complete;
- its risk class permits the selected rollout mode;
- a rollback target is available and verified;
- the required human approval is recorded.

Prompt wording and role descriptions may become canary-eligible after the process is proven. Permissions, tools, hooks, MCP, evaluator rules, release rules, and automatic thresholds remain human-gated.

## Version and rollback

Store source in Git and publish immutable semantic versions. Promote by changing an installation or release pointer to an already evaluated version. Roll back by repointing to the recorded parent or rollback version; do not repair the live installation in place.

Keep release records append-only. A later correction creates a new record rather than rewriting the evidence for an earlier decision.
