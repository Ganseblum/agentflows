"""Doc-chain linter package.

Split out of the former monolithic tools/lab/doc_chain.py (2272 lines) so the
per-C checks, the discrimination self-test, and the CLI each live in their own
module. The thin launcher tools/lab/doc_chain.py still exposes the same
`python doc_chain.py ...` CLI and the same importable names, so gate/checks.py,
gate/examples.py and the protected self-test corpus keep working unchanged.
"""

from __future__ import annotations

from .checks import (
    batch_traceability_findings,
    decision_record_findings,
    evidence_carriers,
    evidence_presence_findings,
    find_stage,
    git_available,
    goal_traceability_findings,
    ledger_index_findings,
    lint,
    ownership_findings,
    read,
    repo_policy_findings,
    staleness_findings,
    text_form_findings,
)
from .cli import lint_file, main
from .constants import REPO_ROOT
from .selftest import self_test

__all__ = [
    "REPO_ROOT",
    "batch_traceability_findings",
    "decision_record_findings",
    "evidence_carriers",
    "evidence_presence_findings",
    "find_stage",
    "git_available",
    "goal_traceability_findings",
    "ledger_index_findings",
    "lint",
    "lint_file",
    "main",
    "ownership_findings",
    "read",
    "repo_policy_findings",
    "self_test",
    "staleness_findings",
    "text_form_findings",
]
