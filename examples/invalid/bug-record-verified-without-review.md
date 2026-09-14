---
bug_id: BUG-INVALID-001
title: Verified record without independent review
status: verified
severity: low
error_kind: other
attribution: workflow_policy
project: example-project
files:
  - examples/invalid/bug-record-verified-without-review.md
recorded_at: 2026-09-14T08:00:00Z
agentflow_version: 0.2.0
---

## Symptom

The record claims verification.

## Root cause

Demonstrates that a verified bug requires independent evidence: this record omits the reviewer,
review decision, and regression status that the schema demands for `status: verified`.

## Fix

Not applicable — this is an intentionally invalid example; the validator must reject it.
