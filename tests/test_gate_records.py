import argparse
import contextlib
import datetime as _dt
import io
import json
import os
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "tools" / "lab"
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import artifact_digest  # noqa: E402
import doc_chain  # noqa: E402
import isolation  # noqa: E402
import validate  # noqa: E402



class TestRecordContractTests(unittest.TestCase):
    """Test records under features/<batch>/testing/ (0.7.0): plan registry contract and run invariants."""

    PLAN_MD = """---
test_plan_id: TP-20260917-001
title: 登录用例
project: demo-webapp
feature: feature-login
target_revision: 9f2c1a7
credentials: session-injected env
case_count: "{case_count}"
test_version: "1"
status: active
recorded_at: "2026-09-17T15:00:00Z"
---

## 用例

| 用例 ID | 级别 | 优先级 | 标题 |
| --- | --- | --- | --- |
| TC-LOGIN-001 | smoke | P0 | 登录成功 |
| TC-LOGIN-002 | e2e | P0 | 空密码拦截 |

### TC-LOGIN-001 登录成功

步骤表（略）。

### TC-LOGIN-002 空密码拦截

步骤表（略）。

## 边界覆盖

| 边界类 | 覆盖用例 | 说明 |
| --- | --- | --- |
| 空输入 | TC-LOGIN-002 | 必填校验 |

## 流程疑点

- Q1：密码长度上限未声明，待产品确认。
"""

    RUN_MD = """---
test_run_id: TR-20260917-001
title: 首轮执行
project: demo-webapp
test_plan_id: TP-20260917-001
test_plan_version: "1"
target_revision: 9f2c1a7
environment: staging
credentials: session-injected env
summary_pass: "{p}"
summary_fail: "{f}"
summary_blocked: "0"
summary_not_run: "0"
decision: {decision}
recorded_at: "2026-09-17T16:00:00Z"
---

## 结果

| 用例 ID | 状态 | 证据 | 说明 |
| --- | --- | --- | --- |
| TC-LOGIN-001 | pass | — | ok |
{row2}

## 证据

无

## 结论

结论。
"""

    @staticmethod
    def _write(path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    @staticmethod
    def _messages(errors: list[Any]) -> list[str]:
        return [error.message for error in errors]

    def _plan_entry(self, root: str, **overrides: str) -> dict[str, Any]:
        path = self._write(
            Path(root) / "features/feature-2026-09-17-demo/testing/demo-webapp-feature-login/plan-2026-09-17-001.md",
            self.PLAN_MD.format(**{"case_count": "2", **overrides}),
        )
        errors, entry = validate.validate_test_plan_markdown(path, path.relative_to(root), {})
        self.assertEqual([], errors)
        assert entry is not None
        return entry

    def _run_errors(self, root: str, plans: dict[str, Any], **overrides: str) -> list[Any]:
        fields = {
            "row2": "| TC-LOGIN-002 | pass | — | ok |",
            "p": "2",
            "f": "0",
            "decision": "pass",
            **overrides,
        }
        path = self._write(
            Path(root) / "features/feature-2026-09-17-demo/testing/demo-webapp-feature-login/run-2026-09-17-001.md",
            self.RUN_MD.format(**fields),
        )
        errors, _, _ = validate.validate_test_run_markdown(path, path.relative_to(root), {}, plans)
        return errors

    def test_valid_plan_and_run_examples_pass(self) -> None:
        plan_path = ROOT / "examples" / "testing" / "plan-2026-09-17-001.md"
        errors, entry = validate.validate_test_plan_markdown(plan_path, plan_path.relative_to(ROOT), {})
        self.assertEqual([], errors)
        self.assertIsNotNone(entry)
        run_path = ROOT / "examples" / "testing" / "run-2026-09-17-001.md"
        errors, _, _ = validate.validate_test_run_markdown(
            run_path, run_path.relative_to(ROOT), {}, validate.example_test_plans()
        )
        self.assertEqual([], errors)

    def test_negative_run_example_with_unknown_status_is_rejected(self) -> None:
        errors = validate.validate_invalid_test_run_example(
            ROOT / "examples" / "invalid" / "test-run-bad-status.md"
        )
        self.assertTrue(any("must be one of" in message for message in self._messages(errors)))

    def test_case_count_mismatch_is_rejected_and_blocks_the_plan_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write(
                Path(temporary) / "features/feature-2026-09-17-demo/testing/demo-webapp-feature-login/plan-2026-09-17-001.md",
                self.PLAN_MD.format(case_count="5"),
            )
            errors, entry = validate.validate_test_plan_markdown(path, path.relative_to(temporary), {})
            self.assertTrue(any("case_count" in message for message in self._messages(errors)))
            self.assertIsNone(entry)

    def test_run_with_summary_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-20260917-001": self._plan_entry(temporary)}
            errors = self._run_errors(temporary, plans, p="3")
            self.assertTrue(any("summary_pass" in message for message in self._messages(errors)))

    def test_run_referencing_unknown_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            errors = self._run_errors(temporary, {})
            self.assertTrue(any("does not resolve" in message for message in self._messages(errors)))

    def test_fail_row_requires_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-20260917-001": self._plan_entry(temporary)}
            errors = self._run_errors(
                temporary, plans, row2="| TC-LOGIN-002 | fail | — | 提示缺失 |", p="1", f="1", decision="partial"
            )
            self.assertTrue(any("must carry evidence" in message for message in self._messages(errors)))

    def test_result_row_outside_the_plan_registry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-20260917-001": self._plan_entry(temporary)}
            errors = self._run_errors(temporary, plans, row2="| TC-OTHER-009 | pass | — | ok |")
            self.assertTrue(any("not in plan" in message for message in self._messages(errors)))

    def test_current_version_run_must_account_for_every_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-20260917-001": self._plan_entry(temporary)}
            errors = self._run_errors(temporary, plans, row2="", p="1")
            self.assertTrue(any("does not account for cases" in message for message in self._messages(errors)))

    def test_decision_pass_with_failures_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-20260917-001": self._plan_entry(temporary)}
            errors = self._run_errors(
                temporary, plans, row2="| TC-LOGIN-002 | fail | 见证据块 1 | 提示缺失 |", p="1", f="1"
            )
            self.assertTrue(any("zero fail and zero blocked" in message for message in self._messages(errors)))

    def test_dated_identity_messages_for_plans_and_runs_are_pinned(self) -> None:
        # Item F (helper extraction): the id/filename/recorded_at agreement messages for test
        # plans and runs must keep their exact wording after the shared helper is extracted.
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = Path(temporary) / "features/feature-2026-09-17-demo/testing/demo-webapp-feature-login"
            plan_path = self._write(
                plan_dir / "plan-2026-09-17-002.md",
                self.PLAN_MD.format(case_count="2"),
            )
            errors, _ = validate.validate_test_plan_markdown(plan_path, plan_path.relative_to(temporary), {})
            self.assertIn(
                "filename must be plan-2026-09-17-001.md to match test_plan_id 'TP-20260917-001'",
                self._messages(errors),
            )
            drifted_plan = self._write(
                plan_dir / "plan-2026-09-17-001.md",
                self.PLAN_MD.format(case_count="2").replace(
                    'recorded_at: "2026-09-17T15:00:00Z"', 'recorded_at: "2026-09-18T15:00:00Z"'
                ),
            )
            errors, _ = validate.validate_test_plan_markdown(drifted_plan, drifted_plan.relative_to(temporary), {})
            self.assertIn(
                "test_plan_id date must match recorded_at date 2026-09-18", self._messages(errors)
            )
            drifted_run = self._write(
                plan_dir / "run-2026-09-17-001.md",
                self.RUN_MD.format(
                    row2="| TC-LOGIN-002 | pass | — | ok |", p="2", f="0", decision="pass"
                ).replace('recorded_at: "2026-09-17T16:00:00Z"', 'recorded_at: "2026-09-18T16:00:00Z"'),
            )
            errors, _, _ = validate.validate_test_run_markdown(
                drifted_run, drifted_run.relative_to(temporary), {}, {}
            )
            self.assertIn(
                "test_run_id date must match recorded_at date 2026-09-18", self._messages(errors)
            )

    def test_live_record_roots_are_the_five_record_zones(self) -> None:
        # 2026-10-12 slimming batch phases 3/4: the top-level plans/ root was dissolved into
        # the feature batches; five live zones remain — docs/issues, docs/releases,
        # docs/features, episodes/, reviews/. Test records under features/<batch>/testing/
        # stay unwalked, so no "tests" root appears here.
        self.assertEqual(
            validate.LIVE_RECORD_ROOTS,
            ("docs/issues", "docs/releases", "docs/features", "episodes", "reviews"),
        )




class ArtifactDigestDeterminismTests(unittest.TestCase):
    """B15 (audit report 2 §6): the digest must not depend on the creating umask.

    Git preserves only the executable bit; recording the whole S_IMODE made the same
    commit produce different digests on machines with different group-write defaults.
    """

    def _digest(self, root: Path) -> str:
        return artifact_digest.digest_manifest(artifact_digest.build_manifest(root, set()))

    def test_non_exec_mode_bits_do_not_change_the_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first = base / "first"
            second = base / "second"
            for root in (first, second):
                (root / "agents").mkdir(parents=True)
                (root / "agents" / "role.md").write_text("content\n", encoding="utf-8")
            first.joinpath("agents/role.md").chmod(0o644)
            second.joinpath("agents/role.md").chmod(0o664)
            self.assertEqual(self._digest(first), self._digest(second))

    def test_exec_bit_still_changes_the_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first = base / "first"
            second = base / "second"
            for root in (first, second):
                (root / "tools").mkdir(parents=True)
                (root / "tools" / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            first.joinpath("tools/run.sh").chmod(0o644)
            second.joinpath("tools/run.sh").chmod(0o755)
            self.assertNotEqual(self._digest(first), self._digest(second))



