import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "tools" / "lab"
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import artifact_digest
import validate


class TestRecordContractTests(unittest.TestCase):
    """Test records under features/<batch>/testing/ (0.7.0): plan registry contract and run invariants."""

    PLAN_MD = """---
test_plan_id: TP-2026-09-17-001
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
test_run_id: TR-2026-09-17-001
title: 首轮执行
project: demo-webapp
test_plan_id: TP-2026-09-17-001
test_plan_version: "{v}"
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
{row1}
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
            "row1": "| TC-LOGIN-001 | pass | — | ok |",
            "row2": "| TC-LOGIN-002 | pass | — | ok |",
            "p": "2",
            "f": "0",
            "v": "1",
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

    def test_plan_case_source_column_must_not_be_empty(self) -> None:
        # T10 / G3-AC-01: the 来源 column was declared required but never read. A case with no
        # source (or a bare 无 without a reason) is now a compile error; the positive shape is
        # covered by the template and the valid example.
        text = (
            self.PLAN_MD.format(case_count="2")
            .replace("| 用例 ID | 级别 | 优先级 | 标题 |", "| 用例 ID | 级别 | 优先级 | 标题 | 来源 |")
            .replace("| --- | --- | --- | --- |", "| --- | --- | --- | --- | --- |")
            .replace("| TC-LOGIN-001 | smoke | P0 | 登录成功 |", "| TC-LOGIN-001 | smoke | P0 | 登录成功 |  |")
            .replace("| TC-LOGIN-002 | e2e | P0 | 空密码拦截 |", "| TC-LOGIN-002 | e2e | P0 | 空密码拦截 | G2-AC-01 |")
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write(Path(temporary) / "plan.md", text)
            errors, _ = validate.validate_test_plan_markdown(path, path.relative_to(temporary), {})
        messages = self._messages(errors)
        self.assertTrue(any("来源 must name its acceptance origin" in m for m in messages), messages)

    def test_run_actual_result_column_must_record_the_observation(self) -> None:
        # T10 / G3-AC-01: the 实际结果 column was declared required but never read.
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
            text = (
                self.RUN_MD.format(
                    row1="| TC-LOGIN-001 | pass | — |  |",
                    row2="| TC-LOGIN-002 | pass | — | 登录页正常跳转 |",
                    p="2",
                    f="0",
                    v="1",
                    decision="pass",
                )
                .replace("| 用例 ID | 状态 | 证据 | 说明 |", "| 用例 ID | 状态 | 证据 | 实际结果 | 说明 |")
                .replace("| --- | --- | --- | --- |", "| --- | --- | --- | --- | --- |")
            )
            path = self._write(
                Path(temporary) / "features/feature-2026-09-17-demo/testing/demo-webapp-feature-login/run-2026-09-17-001.md",
                text,
            )
            errors, _, _ = validate.validate_test_run_markdown(path, path.relative_to(temporary), {}, plans)
        messages = self._messages(errors)
        self.assertTrue(any("实际结果 must record the observed behaviour" in m for m in messages), messages)

    def test_run_with_summary_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
            errors = self._run_errors(temporary, plans, p="3")
            self.assertTrue(any("summary_pass" in message for message in self._messages(errors)))

    def test_zero_case_pass_run_is_rejected(self) -> None:
        # T06: an empty 结果 table used to be exempt whenever the run pinned a non-current plan
        # version, so a run that observed nothing could declare `pass`. The floor is now
        # unconditional: at least one case row and a non-zero summary total.
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
            errors = self._run_errors(
                temporary,
                plans,
                row1="",
                row2="",
                p="0",
                f="0",
                v="0",
            )
        messages = self._messages(errors)
        self.assertTrue(any("at least one case row" in m for m in messages), messages)

    def test_run_pinning_a_plan_version_that_never_existed_is_rejected(self) -> None:
        # T06: `test_plan_version` must match a version the plan actually had.
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
            errors = self._run_errors(temporary, plans, v="9")
        messages = self._messages(errors)
        self.assertTrue(any("never had" in m for m in messages), messages)

    def test_run_referencing_unknown_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            errors = self._run_errors(temporary, {})
            self.assertTrue(any("does not resolve" in message for message in self._messages(errors)))

    def test_fail_row_requires_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
            errors = self._run_errors(
                temporary, plans, row2="| TC-LOGIN-002 | fail | — | 提示缺失 |", p="1", f="1", decision="partial"
            )
            self.assertTrue(any("must carry evidence" in message for message in self._messages(errors)))

    def test_result_row_outside_the_plan_registry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
            errors = self._run_errors(temporary, plans, row2="| TC-OTHER-009 | pass | — | ok |")
            self.assertTrue(any("not in plan" in message for message in self._messages(errors)))

    def test_current_version_run_must_account_for_every_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
            errors = self._run_errors(temporary, plans, row2="", p="1")
            self.assertTrue(any("does not account for cases" in message for message in self._messages(errors)))

    def test_decision_pass_with_failures_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plans = {"TP-2026-09-17-001": self._plan_entry(temporary)}
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
                "filename must be plan-2026-09-17-001.md to match test_plan_id 'TP-2026-09-17-001'",
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
                    row1="| TC-LOGIN-001 | pass | — | ok |",
                    row2="| TC-LOGIN-002 | pass | — | ok |",
                    p="2",
                    f="0",
                    v="1",
                    decision="pass",
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




class ReviewTierEnforcementTests(unittest.TestCase):
    """拍板口与降级留痕的机器判据（2026-10-29 门变更，用户授权）。

    `skills/agentflow/references/contracts.md` 早就写着「`review_tier: L0` 而 `dispatch_errors`
    为空，是伪降级，同样无效」，但 2026-10-28 实测全仓零校验器读它（docs/PENDING-DECISIONS.md
    第 17 条）。这组用例钉住判据本身，尤其钉住「存量记录不被追溯打红」——否则新判据的第一件事
    就是把历史评审全部染红，逼人摘掉判据。
    """

    def _messages(self, errors: list[Any]) -> list[str]:
        return [error.message for error in errors]

    def test_l0_without_dispatch_errors_is_a_pseudo_downgrade(self) -> None:
        errors = validate.review_tier_findings({"review_tier": "L0"}, Path("reviews/r.md"))
        self.assertEqual(1, len(errors))
        self.assertIn("伪降级", errors[0].message)

    def test_l0_with_verbatim_dispatch_errors_passes(self) -> None:
        frontmatter = {"review_tier": "L0", "dispatch_errors": ["model concurrency limit exceeded"]}
        self.assertEqual([], validate.review_tier_findings(frontmatter, Path("reviews/r.md")))

    def test_empty_dispatch_error_list_is_still_a_pseudo_downgrade(self) -> None:
        errors = validate.review_tier_findings(
            {"review_tier": "L0", "dispatch_errors": []}, Path("reviews/r.md")
        )
        self.assertIn("伪降级", self._messages(errors)[0])

    def test_l1_and_l2_pass_and_absent_tier_is_neither_green_nor_red(self) -> None:
        for tier in ("L1", "L2"):
            self.assertEqual([], validate.review_tier_findings({"review_tier": tier}, Path("r.md")))
        # 未声明：存量记录（本仓 12 份评审记录都没有该字段）不得被追溯打红
        self.assertEqual([], validate.review_tier_findings({"decision": "approved"}, Path("r.md")))

    def test_tier_outside_the_enum_is_rejected(self) -> None:
        errors = validate.review_tier_findings({"review_tier": "L3"}, Path("r.md"))
        self.assertIn("review_tier", self._messages(errors)[0])

    def test_shipped_review_schema_declares_both_fields_and_the_guard(self) -> None:
        schema = json.loads((ROOT / "schemas" / "review.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(["L0", "L1", "L2"], schema["properties"]["review_tier"]["enum"])
        self.assertEqual("array", schema["properties"]["dispatch_errors"]["type"])
        self.assertEqual("string", schema["properties"]["dispatch_errors"]["items"]["type"])
        guard = schema["allOf"][0]
        self.assertEqual("L0", guard["if"]["properties"]["review_tier"]["const"])
        self.assertEqual(["dispatch_errors"], guard["then"]["required"])
        self.assertEqual(1, guard["then"]["properties"]["dispatch_errors"]["minItems"])

    def test_the_gate_path_blocks_a_pseudo_downgrade_record(self) -> None:
        """接线判据：把 schema 与校验器都削弱掉才能让这条转绿。

        直接测 `review_tier_findings` 只钉住函数存在，钉不住它被 `validate_review_markdown` 调用——
        本轮反证就在一次性副本上实测到这一点：删掉调用点后，八条逐函数用例仍全绿。
        2026-10-28 的 ISS-2026-10-23-新判据声明了却不被校验的六处 记的就是同一种失败。
        """
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "reviews" / "agentflow-demo"
            directory.mkdir(parents=True)
            (directory / "archive-2026-10-29-902").mkdir()
            (directory / "archive-2026-10-29-902" / "snapshot.md").write_text("# 快照\n", encoding="utf-8")
            body = (
                "---\n"
                "review_id: REV-2026-10-29-902\n"
                "title: 接线反证记录\n"
                "target_project: agentflows\n"
                "target_feature: feature-demo\n"
                "source_revision: 6229a65\n"
                "reviewed_docs:\n  - archive-2026-10-29-902/snapshot.md\n"
                "decision: approved\n"
                "reviewer: reviewer\n"
                "review_tier: L0\n"
                "recorded_at: 2026-10-29T01:50:00+08:00\n"
                "---\n\n## 结论\n\n反证。\n"
            )
            path = directory / "review-2026-10-29-902.md"
            path.write_text(body, encoding="utf-8")
            errors = validate.validate_review_markdown(path, path.relative_to(root), {})
            messages = self._messages(errors)
            # 只认 Python 层独有的措辞：schema 的 allOf 也报「missing required property
            # 'dispatch_errors'」，接受那个词就等于允许接线点被删掉而用例照绿（评审 P1-1）。
            self.assertTrue(any("伪降级" in message for message in messages), messages)
            # 补上失败派发的原始留痕后，同一条记录必须转绿
            path.write_text(
                body.replace("review_tier: L0\n",
                             "review_tier: L0\ndispatch_errors:\n  - model concurrency limit exceeded\n"),
                encoding="utf-8",
            )
            self.assertEqual([], validate.validate_review_markdown(path, path.relative_to(root), {}))


class CarrierMapVerificationTests(unittest.TestCase):
    """归属表核验断言（2026-10-29 评审 P1-4 补）：删掉接线或削弱判定都必须能被抓住。"""

    HEADER = "| 规则 | 权威载体 | 锚点 | 副本处置 |\n| --- | --- | --- | --- |\n"

    def _root(self, rows: str):
        root = Path(tempfile.mkdtemp())
        (root / "skills/agentflow/references").mkdir(parents=True)
        (root / "agents").mkdir()
        (root / "skill.md").write_text("# x\n", encoding="utf-8")
        (root / "skills/agentflow/references/carrier-map.md").write_text(
            "# 表\n\n" + self.HEADER + rows, encoding="utf-8"
        )
        return root

    def _rows(self, extra: list[str]) -> str:
        base = [f"| 规则{i} | `skill.md` | # x | 只此一份 |\n" for i in range(12)]
        return "".join(base + extra)

    def test_missing_carrier_path_is_reported_with_the_rule_name(self) -> None:
        root = self._root(self._rows(["| 坏载体 | `nope.md` | # x | 只此一份 |\n"]))
        messages = [e.message for e in validate.validate_carrier_map(root)]
        self.assertTrue(any("does not exist" in m and "坏载体" in m for m in messages), messages)

    def test_anchor_absent_from_the_carrier_is_reported(self) -> None:
        root = self._root(self._rows(["| 坏锚点 | `skill.md` | ## 不存在的节 | 只此一份 |\n"]))
        messages = [e.message for e in validate.validate_carrier_map(root)]
        self.assertTrue(any("is not a literal inside" in m and "坏锚点" in m for m in messages), messages)

    def test_malformed_row_cannot_escape_the_checks_by_adding_a_column(self) -> None:
        root = self._root(self._rows(["| 夹带一行 | `skill.md` | # x | 只此一份 | 多出来的一列 |\n"]))
        messages = [e.message for e in validate.validate_carrier_map(root)]
        self.assertTrue(any("4 required columns" in m for m in messages), messages)

    def test_the_docs_gate_path_actually_calls_the_verification(self) -> None:
        """接线判据：归属表核验必须真被 `validate.py docs` 调用。

        逐函数用例（上面三条）钉不住调用点——反证实测：删掉 `validate_doc_consistency`
        里的 `errors.extend(validate_carrier_map())` 后，逐函数四条照绿（评审 P1-4 的同一形态，
        与本批 `episode` 判据当初犯的是同一个错）。这条用替换返回值的方式把接线本身钉住。
        """
        sentinel = validate.ValidationError("carrier-map", "sentinel wiring probe")
        import gate.docs as gate_docs
        with mock.patch.object(gate_docs, "validate_carrier_map", return_value=[sentinel]):
            messages = [e.message for e in validate.validate_doc_consistency()]
        self.assertIn("sentinel wiring probe", messages)

    def test_a_clean_map_passes(self) -> None:
        root = self._root(self._rows([]))
        self.assertEqual([], [e.message for e in validate.validate_carrier_map(root)])


class EpisodeEvidencePointerTests(unittest.TestCase):
    """episode 的指针字段必须指向还开得了的对象（2026-10-29 门变更）。

    计划的证据列自 2026-10-23 起有 C23 存在性判据，而同一条链上的档案载体 episode 的
    `evidence_ref` 只过 schema 的 minLength——2026-10-28 评测报告记为「可复核性只做了一半」，
    实测 445 条字段值里有 14 条指向已不在盘上的对象。范围刻意窄于散文检查：
    叙述字段里的退役路径是当年的引文，改了就是篡改证据。
    """

    def _findings(self, document: dict[str, Any]) -> list[Any]:
        return validate.validate_episode_references(document, ROOT / "episodes" / "x.json")

    def test_pointer_to_a_vanished_repo_path_trips(self) -> None:
        errors = self._findings({"claims": [{"evidence_ref": "docs/does-not-exist.md"}]})
        self.assertEqual(1, len(errors))
        self.assertIn("evidence pointer", errors[0].message)

    def test_live_repo_path_passes(self) -> None:
        self.assertEqual([], self._findings({"claims": [{"evidence_ref": "index.md"}]}))

    def test_na_with_reason_and_repo_qualified_ref_are_carriers(self) -> None:
        document = {
            "claims": [
                {"evidence_ref": "N/A: 随 2026-10-12 评测装置裁撤删除，出处见 CHANGELOG 同日节"},
                {"ref": "youc@1a2b3c4:docs/x.md"},
            ]
        }
        self.assertEqual([], self._findings(document))

    def test_bare_na_is_not_an_exemption(self) -> None:
        errors = self._findings({"claims": [{"evidence_ref": "N/A"}]})
        self.assertEqual(1, len(errors))
        self.assertIn("bare 'N/A'", errors[0].message)

    def test_narrative_fields_are_not_scanned(self) -> None:
        # check/signals 里写命令与退役路径是引文，不是指针；判据过宽会让首轮误报被整体放行
        document = {
            "signals": [{"check": "python3 tools/lab/eval_runner.py --help；退役路径 docs/agent-roles.md"}],
            "claims": [{"resolution": "见 plans/PENDING-DECISIONS.md 旧路径（当时如此）"}],
        }
        self.assertEqual([], self._findings(document))

    def test_directory_urls_and_command_text_are_skipped(self) -> None:
        document = {
            "claims": [
                {"evidence_ref": "docs/features/feature-2026-10-26-L3工作流增强/reviews/"},
                {"ref": "https://example.com/a.md"},
                {"path": "python3 tools/lab/validate.py all 输出"},
            ]
        }
        self.assertEqual([], self._findings(document))

    def test_field_whitelist_is_a_single_definition(self) -> None:
        self.assertEqual(("evidence_ref", "ref", "path", "artifact"), validate.EPISODE_EVIDENCE_FIELDS)

    def test_iter_evidence_values_carries_the_field_name(self) -> None:
        document = {"a": [{"evidence_ref": "x.md"}, {"b": {"ref": ["y.md", 3]}}]}
        self.assertEqual(
            [("evidence_ref", "x.md"), ("ref", "y.md")],
            validate.iter_evidence_values(document, ("evidence_ref", "ref")),
        )

    def test_finding_names_the_field_and_every_path_in_a_multi_path_value(self) -> None:
        # 评审 P1-3/P2-3：整值成形状才判会让「A；B」式取值整体跳过，且不报字段名等于让读者再找一遍
        errors = self._findings({"claims": [{"evidence_ref": "docs/gone-a.md；docs/gone-b.md"}]})
        self.assertEqual(2, len(errors))
        for message in (e.message for e in errors):
            self.assertIn("evidence_ref:", message)
        self.assertIn("docs/gone-b.md", errors[1].message)


    def test_the_artifacts_path_trips_on_a_stale_episode_pointer(self) -> None:
        """接线判据：门走 `validate_episode_document` 时必须真的调用指针校验。

        同上一条理由——逐函数用例钉不住调用点，本轮反证实测到删掉调用后逐函数仍全绿。
        """
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "EP-2026-01-01-009.json"
            claims: list[dict[str, str]] = [
                {
                    "claim_id": "C-1",
                    "claim": "门全绿",
                    "status": "verified",
                    "check": "python3 tools/lab/validate.py all",
                    "evidence_ref": "docs/this-file-was-cleaned-up.md",
                }
            ]
            record: dict[str, object] = {
                "schema_version": 1,
                "episode_id": "EP-2026-01-01-009",
                "source_type": "acceptance",
                "objective": "o",
                "outcome": "partial",
                "signals": [{"kind": "tests", "value": "ok"}],
                "feedback_summary": "f",
                "agentflow_version": "0.4.0",
                "host": "other",
                "provenance": {"carrier": "session", "sanitized": True},
                "redactions": [],
                "review_roundtrips": [],
                "claims": claims,
            }
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = validate.validate_episode_document(path)
            self.assertTrue(
                any("evidence pointer" in error.message for error in errors),
                [error.message for error in errors],
            )
            claims[0]["evidence_ref"] = "index.md"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual([], validate.validate_episode_document(path))


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



