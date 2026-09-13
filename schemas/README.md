# Agentflow contracts

This directory contains the cross-host contracts that are shared by the Agentflow
workflow, maintenance tools, and evaluation fixtures.

The improvement-specific contracts remain under
`skills/improve/references/` because the Improve Skill links to them directly. The
validator loads both locations and checks cross-document invariants where a single
JSON Schema cannot express them.

These contracts describe evidence and execution plans. A plan is not, by itself,
authorization to modify code or release a Plugin.

Evaluation results are bound to an artifact digest, suite cardinality, observed execution
context, and per-case holdout/repetition metadata. The runner rejects Adapter output that
does not cover the frozen suite exactly.
