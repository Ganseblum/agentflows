# Delegation contracts

Use these fields as a compact checklist rather than ceremonial paperwork. Omit a field only when it truly does not apply.

## Worker task brief

```yaml
objective: concrete result the worker must produce
scope: files, modules, or questions the worker owns
constraints: repository rules, compatibility, and actions that need approval
deliverable: code, findings, or a proposed change
verification: commands or evidence that prove the result
dependencies: inputs that must exist before this work starts
```

Give one worker one primary objective. Include exact repository paths when they are known. For investigation, make the scope read-only. For implementation, state whether the worker owns edits and avoid assigning the same files to another active writer.

## Worker result

```yaml
status: complete | partial | blocked
summary: what was established or changed
files: inspected or changed paths
checks: commands and outcomes
risks: unresolved issues or assumptions
next_action: smallest useful follow-up
```

The supervisor verifies the shared workspace because worker summaries can be stale, incomplete, or based on an unsuccessful command.

## Review result

```yaml
decision: approved | changes_requested | blocked
evidence: concrete findings tied to code or command output
required_changes: minimal changes needed for approval
residual_risks: limits that remain even if approved
```

A reviewer should prioritize correctness, regressions, security boundaries, state recovery, and missing verification. Style-only feedback should not block approval unless the repository enforces it.

## Final decision record

Report:

- outcome: complete, partial, or blocked;
- implementation: the user-visible or architectural result;
- verification: the checks that passed and any that could not run;
- review: the independent decision, when review was warranted;
- remaining work: only material limitations or the next concrete milestone.
