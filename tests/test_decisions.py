"""Tests for tools/lab/decisions.py — the D8 decision system (G7-AC-01..05).

Three fixture groups:
  * positive          — dependencies that must stay GREEN (current rev, equivalent_to,
                        invariant present, tolerated stale pin).
  * breaking          — dependencies that must go RED (withdrawn rev, stale rev, unknown
                        decision, missing invariant, bare exempt, terminal decision).
  * non-false-positive — documents the checker must NOT flag (no deps, unrelated doc,
                        pin at current rev, equivalent pin below current).

The hand-edit case (T30) is covered by the index digest assertion.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "tools" / "lab"
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import decisions
import validate


def _ledger_text() -> str:
    """A ledger with one decision: DEC-2026-001 at r4, r2 withdrawn, r4 equivalent_to r1.

    Its body text carries the invariant "登录须二次验证" so the invariant pin can be tested
    both ways.
    """
    return (
        "# 待拍板事项\n\n"
        "| # | 来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策 | 状态 | DEC编号 | 修订 | 撤回 | 等价 | 终态 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| 1 | `docs/x.md` | A 登录要不要二次验证 B 不要 | 2026-10-29 `echo ok` | A 登录须二次验证 | 用户确认 | P2 | 多模块(登录组件) | N | 已拍板（2026-10-29） | DEC-2026-001 | r4 | r2 | r1 |  |\n"
    )


def _terminal_ledger() -> str:
    return _ledger_text().replace("| r1 |  |", "| r1 | superseded |")


def _make_root(deps_docs: dict[str, str]) -> Path:
    """Build a temp root: docs/PENDING-DECISIONS.md + the given downstream docs."""
    root = Path(tempfile.mkdtemp())
    (root / "docs").mkdir()
    (root / "docs" / "PENDING-DECISIONS.md").write_text(_ledger_text(), encoding="utf-8")
    (root / "docs" / "decisions").mkdir()
    (root / "docs" / "decisions" / "issued.txt").write_text("DEC-2026-001\n", encoding="utf-8")
    for rel, content in deps_docs.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


class DecisionLedgerTests(unittest.TestCase):
    def test_parse_ledger_reads_revision_columns(self):
        ledger = decisions.parse_ledger(_ledger_text())
        self.assertIn("DEC-2026-001", ledger)
        rec = ledger["DEC-2026-001"]
        self.assertEqual(rec["rev"], 4)
        self.assertEqual(rec["withdrawn"], {2})
        self.assertEqual(rec["equivalent_to"], {1})
        self.assertEqual(rec["terminal"], "")
        self.assertIn("登录须二次验证", rec["text"])

    # ------------------------------------------------------------------ #
    # positive (must stay GREEN)
    # ------------------------------------------------------------------ #
    def test_positive_pin_current_rev(self):
        root = _make_root(
            {"docs/features/f1/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r4]\n---\nbody\n"}
        )
        self.assertEqual(decisions.check(root), [])

    def test_positive_pin_equivalent_rev(self):
        # pin r1 while current r4 declares equivalent_to r1 -> green (G7-AC-03)
        root = _make_root(
            {"docs/features/f2/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r1]\n---\nbody\n"}
        )
        self.assertEqual(decisions.check(root), [])

    def test_positive_pin_invariant_present(self):
        root = _make_root(
            {
                "docs/features/f3/plan/P.md": (
                    "---\ndecision_deps: [DEC-2026-001#invariant=登录须二次验证]\n---\nbody\n"
                )
            }
        )
        self.assertEqual(decisions.check(root), [])

    def test_positive_tolerated_stale_pin(self):
        # affected but registered stale_reason + future review_date -> green (G7-AC-04)
        root = _make_root(
            {
                "docs/features/f4/plan/P.md": (
                    "---\ndecision_deps: "
                    "[DEC-2026-001#r2#stale_reason=历史快照滞后#review_date=2099-12-31]\n---\nbody\n"
                )
            }
        )
        self.assertEqual(decisions.check(root), [])

    # ------------------------------------------------------------------ #
    # breaking (must go RED)
    # ------------------------------------------------------------------ #
    def test_breaking_pin_withdrawn_rev(self):
        # pin r2, but r2 was withdrawn and current is r4 -> red (G7-AC-02)
        root = _make_root(
            {"docs/features/b1/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r2]\n---\nbody\n"}
        )
        errors = decisions.check(root)
        self.assertEqual(len(errors), 1)
        self.assertIn("r2", errors[0])
        self.assertIn("撤回", errors[0])

    def test_breaking_pin_stale_rev_no_exempt(self):
        # pin r3 (< current r4, not withdrawn, not equivalent, no exempt) -> red
        root = _make_root(
            {"docs/features/b2/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r3]\n---\nbody\n"}
        )
        self.assertEqual(len(decisions.check(root)), 1)

    def test_breaking_unknown_decision(self):
        root = _make_root(
            {"docs/features/b3/plan/P.md": "---\ndecision_deps: [DEC-2026-999#r1]\n---\nbody\n"}
        )
        errors = decisions.check(root)
        self.assertEqual(len(errors), 1)
        self.assertIn("未立账", errors[0])

    def test_breaking_invariant_missing(self):
        root = _make_root(
            {
                "docs/features/b4/plan/P.md": (
                    "---\ndecision_deps: [DEC-2026-001#invariant=手机号必须保留]\n---\nbody\n"
                )
            }
        )
        errors = decisions.check(root)
        self.assertEqual(len(errors), 1)
        self.assertIn("不变式", errors[0])

    def test_breaking_terminal_decision_pinned_current_rev(self):
        # P1-1: the terminal gate must run before the "pinned == current" fast path.
        root = _make_root(
            {"docs/features/b5/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r4]\n---\nbody\n"}
        )
        (root / "docs" / "PENDING-DECISIONS.md").write_text(_terminal_ledger(), encoding="utf-8")
        errors = decisions.check(root)
        self.assertTrue(any("已终态" in error for error in errors), errors)

    def test_breaking_deferred_decision_pinned_current_rev(self):
        # deferred is a terminal state too; it must not remain an actionable dependency.
        root = _make_root(
            {"docs/features/b5/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r4]\n---\nbody\n"}
        )
        (root / "docs" / "PENDING-DECISIONS.md").write_text(
            _terminal_ledger().replace("| superseded |", "| deferred |"), encoding="utf-8"
        )
        errors = decisions.check(root)
        self.assertTrue(any("已终态" in error for error in errors), errors)

    def test_breaking_withdrawn_current_revision_is_red(self):
        # A pin equal to the current revision must still be red when that revision is withdrawn.
        root = _make_root(
            {"docs/features/b5/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r2]\n---\nbody\n"}
        )
        (root / "docs" / "PENDING-DECISIONS.md").write_text(
            _ledger_text().replace("| r4 | r2 |", "| r2 | r2 |"), encoding="utf-8"
        )
        errors = decisions.check(root)
        self.assertTrue(any("已被撤回" in error for error in errors), errors)

    def test_breaking_issued_witness_file_missing(self):
        root = _make_root({})
        (root / "docs" / "decisions" / "issued.txt").unlink()
        errors = decisions.check(root)
        self.assertTrue(any("issued.txt 缺失" in error for error in errors), errors)

    def test_breaking_ledger_id_missing_from_issued_witness(self):
        root = _make_root({})
        (root / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "decisions" / "issued.txt").write_text("DEC-2026-999\n", encoding="utf-8")
        errors = decisions.check(root)
        self.assertTrue(any("未登记进 issued.txt" in error for error in errors), errors)

    def test_breaking_ledger_without_recognisable_table(self):
        root = _make_root({})
        (root / "docs" / "PENDING-DECISIONS.md").write_text("DEC-2026-001\n", encoding="utf-8")
        errors = decisions.check(root)
        self.assertTrue(any("解析为 0 条" in error for error in errors), errors)

    def test_breaking_terminal_decision_pinned_invariant(self):
        # P1-1: an invariant pin must not keep a terminal decision green either.
        root = _make_root(
            {
                "docs/features/b5/plan/P.md": (
                    "---\ndecision_deps: [DEC-2026-001#invariant=登录须二次验证]\n---\nbody\n"
                )
            }
        )
        (root / "docs" / "PENDING-DECISIONS.md").write_text(_terminal_ledger(), encoding="utf-8")
        errors = decisions.check(root)
        self.assertTrue(any("已终态" in error for error in errors), errors)

    def test_breaking_empty_invariant_is_rejected(self):
        # P1-2: "" in text is always true; an empty #invariant= must not be a free pass.
        root = _make_root(
            {"docs/features/b5/plan/P.md": "---\ndecision_deps: [DEC-2026-001#invariant=]\n---\nbody\n"}
        )
        errors = decisions.check(root)
        self.assertTrue(any("不变式为空" in error for error in errors), errors)

    def test_breaking_unknown_terminal_word_is_rejected(self):
        # P1-1: an unrecognised terminal word must not be normalised to "still active".
        root = _make_root(
            {"docs/features/b5/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r4]\n---\nbody\n"}
        )
        (root / "docs" / "PENDING-DECISIONS.md").write_text(
            _terminal_ledger().replace("| superseded |", "| 已撤回 |"), encoding="utf-8"
        )
        errors = decisions.check(root)
        self.assertTrue(any("终态词" in error for error in errors), errors)

    def test_breaking_ledger_header_missing_revision_column_is_rejected(self):
        # P2-8: a missing 修订 column used to default to r1 and pass silently.
        root = _make_root({})
        ledger = _ledger_text().replace(" | 修订 | 撤回 | 等价 | 终态 |", " | 撤回 | 等价 | 终态 |", 1)
        ledger = ledger.replace("| DEC-2026-001 | r4 | r2 | r1 |  |", "| DEC-2026-001 | r2 | r1 |  |", 1)
        (root / "docs" / "PENDING-DECISIONS.md").write_text(ledger, encoding="utf-8")
        errors = decisions.check(root)
        self.assertTrue(any("表头缺列" in error for error in errors), errors)

    def test_breaking_issued_id_missing_from_ledger_is_rejected(self):
        # P2-3: issued.txt is the append-only witness; deleting a ledger row must go red.
        root = _make_root({})
        (root / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "decisions" / "issued.txt").write_text("DEC-2026-999\n", encoding="utf-8")
        errors = decisions.check(root)
        self.assertTrue(any("从台账消失" in error for error in errors), errors)

    def test_breaking_malformed_decision_deps_is_rejected(self):
        # P2-1: a frontmatter key that parses to zero tokens must not be silently ignored.
        root = _make_root(
            {
                "docs/features/b5/plan/P.md": (
                    "---\ndecision_deps:\n    - DEC-2026-001#r4\n---\nbody\n"
                )
            }
        )
        errors = decisions.check(root)
        self.assertTrue(any("解析不出任何条目" in error for error in errors), errors)

    def test_breaking_bare_exempt_without_reason(self):
        # `#exempt=true` is not a legal token; a stale pin must still be red.
        root = _make_root(
            {
                "docs/features/b5/plan/P.md": (
                    "---\ndecision_deps: [DEC-2026-001#r3#exempt=true]\n---\nbody\n"
                )
            }
        )
        errors = decisions.check(root)
        self.assertEqual(len(errors), 1)
        self.assertIn("已过期", errors[0])

    def test_breaking_exempt_past_review_date(self):
        # stale_reason present but review_date in the past -> not a valid exemption -> red
        root = _make_root(
            {
                "docs/features/b6/plan/P.md": (
                    "---\ndecision_deps: "
                    "[DEC-2026-001#r2#stale_reason=滞后#review_date=2000-01-01]\n---\nbody\n"
                )
            }
        )
        self.assertEqual(len(decisions.check(root)), 1)

    # ------------------------------------------------------------------ #
    # non-false-positive (must NOT be flagged)
    # ------------------------------------------------------------------ #
    def test_non_false_positive_no_deps(self):
        root = _make_root({"docs/features/n1/plan/P.md": "---\ntitle: x\n---\nbody\n"})
        self.assertEqual(decisions.check(root), [])

    def test_non_false_positive_unrelated_doc(self):
        root = _make_root(
            {
                "docs/features/n2/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r4]\n---\nbody\n",
                "docs/features/n2/plan/Q.md": "no frontmatter here\n",
            }
        )
        self.assertEqual(decisions.check(root), [])

    def test_non_false_positive_equivalent_pin_below_current(self):
        # pinning r1 (below current r4) is green because r4 equivalent_to r1 (G7-AC-03 mirror).
        root = _make_root(
            {"docs/features/n3/plan/P.md": "---\ndecision_deps: [DEC-2026-001#r1]\n---\nbody\n"}
        )
        self.assertEqual(decisions.check(root), [])

    def test_non_false_positive_view_excludes_terminal(self):
        ledger = (
            "# 待拍板事项\n\n"
            "| # | 来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策 | 状态 | DEC编号 | 修订 | 撤回 | 等价 | 终态 |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| 1 | `a` | A B | 2026-10-29 `x` | A | c | P2 | 多模块(m) | N | 已拍板 | DEC-2026-001 | r4 | r2 | r1 |  |\n"
            "| 2 | `b` | A B | 2026-10-29 `x` | A | c | P2 | 多模块(m) | N | 已撤回 | DEC-2026-002 | r1 |  |  | withdrawn |\n"
        )
        root = Path(tempfile.mkdtemp())
        (root / "docs").mkdir()
        (root / "docs" / "PENDING-DECISIONS.md").write_text(ledger, encoding="utf-8")
        out = decisions.view(root)
        self.assertIn("DEC-2026-001", out)
        self.assertNotIn("DEC-2026-002", out)

    def test_positive_terminal_decision_with_registered_exemption_stays_green(self):
        # The terminal gate still honours stale_reason + a future review_date.
        root = _make_root(
            {
                "docs/features/f/plan/P.md": (
                    "---\ndecision_deps: "
                    "[DEC-2026-001#r4#stale_reason=历史#review_date=2099-01-01]\n---\nbody\n"
                )
            }
        )
        (root / "docs" / "PENDING-DECISIONS.md").write_text(_terminal_ledger(), encoding="utf-8")
        self.assertEqual(decisions.check(root), [])

    # ------------------------------------------------------------------ #
    # T30 — generated index + hand-edit digest assertion
    # ------------------------------------------------------------------ #
    def test_index_is_generated_and_deterministic(self):
        root = _make_root({})
        first = decisions.render_index(root)
        second = decisions.render_index(root)
        self.assertEqual(first, second)
        self.assertIn("decision-index-digest:", first)
        self.assertIn("DEC-2026-001", first)

    def test_index_hand_edit_trips_digest(self):
        root = _make_root({})
        canonical = decisions.render_index(root)
        edited = canonical.replace("| r4 |", "| r9 |")
        self.assertNotEqual(edited, canonical)
        index_path = root / "docs" / "decisions" / "index.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(edited, encoding="utf-8")
        errors = decisions.verify_index(root)
        self.assertEqual(len(errors), 1)
        self.assertIn("禁止手改", errors[0])

    def test_decision_gate_runs_dependency_and_index_checks_even_when_linter_is_green(self):
        # T29/T30 wiring: the gate used to return early on a green doc-chain linter, so both
        # the decision_deps reverse index and the generated-index digest assertion never ran.
        completed = subprocess.CompletedProcess([], 0, "", "")
        with (
            mock.patch("gate.checks.subprocess.run", return_value=completed),
            mock.patch.object(decisions, "check", return_value=["dep-stale"]),
            mock.patch.object(decisions, "verify_index", return_value=["index-stale"]),
        ):
            errors = validate.validate_decision_gate(ROOT)
        messages = [error.message for error in errors]
        self.assertIn("dep-stale", messages)
        self.assertIn("index-stale", messages)


if __name__ == "__main__":
    unittest.main()
