---
bug_id: BUG-API-001
title: Reviewer accepted a changed error shape without checking the client contract
status: verified
severity: medium
error_kind: ai-ignored-doc
attribution: role_prompt
project: example-project
files:
  - services/api/orders.go
  - clients/web/src/api/orders.ts
affected_slices:
  - review
  - cross-layer
  - api-contract
recorded_at: 2026-09-13T23:40:00Z
updated_at: 2026-09-14T10:00:00Z
agentflow_version: 0.2.0
reviewer: independent-review-example
review_decision: approved
regression_status: pass
---

## Symptom

A reviewer approved a backend change that altered the error response of the orders API even
though the frontend client still parsed the old shape. The plan explicitly required error-shape
compatibility; the reviewer reported only on the success response.

## Problem code

```go
// services/api/orders.go — error envelope changed from {"error": "..."} to {"code": ..., "message": ...}
func writeError(w http.ResponseWriter, err error) {
    json.NewEncoder(w).Encode(map[string]any{"code": "ORD-ERR", "message": err.Error()})
}
```

## Root cause

The reviewer role prompt described "check the implementation" but did not explicitly require
checking declared error contracts against consumers, so the reviewer validated the success path
only. Classified `ai-ignored-doc`: an existing documented contract was not enforced by the role.

## Fix

The reviewer contract and the public evaluation case now explicitly require error-shape and
compatibility checks (see `skills/agentflow/references/contracts.md` and `evals/public/AF-003.json`).

## Regression check

- pass: `python3 tools/lab/validate.py evals` — the API contract review case enforces error-shape checking.

## Review

- reviewer: independent-review-example
- decision: approved
- evidence: review record E-API-REVIEW; regression check above passed after the fix.

## Notes

Sanitized example record.
