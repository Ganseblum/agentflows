"""Public CLI regressions for execution evidence and document profiles."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "agentflow" / "scripts" / "workflow.py"


class WorkflowCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agentflow-workflow-test-",
                                                dir="/tmp" if Path("/tmp").is_dir() else None)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "project"
        self.repo.mkdir()
        (self.repo / "src").mkdir()
        (self.repo / "tests").mkdir()
        (self.repo / "src" / "logic.py").write_text("VALUE = 1\n")
        (self.repo / "tests" / "unit.py").write_text("# test source\n")
        (self.repo / "plan.md").write_text("# Confirmed behavior\nReturn the configured value.\n")
        (self.repo / ".gitignore").write_text("__pycache__/\nignored-input.txt\n")
        self.git("init")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "core.hooksPath=/dev/null", "commit", "-m", "fixture")
        self.request = self.base / "request.json"
        self.sealed = self.base / "sealed.json"
        self.output = self.base / "evidence"

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def cli(self, *args):
        result = subprocess.run([sys.executable, str(CLI), *map(str, args)], text=True,
                                capture_output=True, timeout=30, check=False)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"CLI did not return JSON: {result.returncode}\n{result.stdout}\n{result.stderr}")
        return result.returncode, payload

    def task(self, name="one", *, reporter="tap", text=None, code=None, depends=None, task_id="test"):
        if code is None:
            report = text if text is not None else f"TAP version 13\nok 1 - {name}\n1..1"
            code = "print(" + repr(report) + ")"
        return {"id": task_id, "depends_on": depends or [], "argv": [sys.executable, "-c", code],
                "cwd": ".", "timeout_seconds": 5, "kind": "test", "reporter": reporter,
                "cases": [{"id": "TC-" + task_id.upper(), "report_name": name}]}

    def seal(self, *, tasks=None, allowed=None):
        request = {"plan": "plan.md", "allowed_writes": allowed if allowed is not None else ["src/logic.py", "tests/unit.py"],
                   "tasks": tasks if tasks is not None else [self.task()]}
        self.request.write_text(json.dumps(request))
        code, payload = self.cli("seal", "--root", self.repo, "--input", self.request,
                                 "--output", self.sealed)
        self.assertEqual(code, 0, payload)
        return json.loads(self.sealed.read_text())["fingerprint"]

    def verify(self, fingerprint):
        return self.cli("verify", "--root", self.repo, "--sealed", self.sealed,
                        "--fingerprint", fingerprint)

    def run_plan(self, fingerprint, *, phase="green"):
        return self.cli("run", "--root", self.repo, "--sealed", self.sealed,
                        "--fingerprint", fingerprint, "--output", self.output, "--phase", phase)

    def test_seal_and_verify_unchanged_inputs(self):
        fingerprint = self.seal()
        self.assertEqual(self.verify(fingerprint)[0], 0)

    def test_implementation_may_change_only_allowed_paths(self):
        fingerprint = self.seal()
        (self.repo / "src/logic.py").write_text("VALUE = 2\n")
        self.assertEqual(self.verify(fingerprint)[0], 0)

    def test_plan_change_is_rejected(self):
        fingerprint = self.seal()
        (self.repo / "plan.md").write_text("# Different behavior\n")
        self.assertEqual(self.verify(fingerprint)[0], 3)

    def test_plan_cannot_be_made_writable(self):
        self.request.write_text(json.dumps({"plan": "plan.md", "allowed_writes": ["plan.md"],
                                            "tasks": [self.task()]}))
        self.assertEqual(self.cli("seal", "--root", self.repo, "--input", self.request,
                                 "--output", self.sealed)[0], 3)

    def test_untracked_out_of_scope_file_is_rejected(self):
        fingerprint = self.seal()
        (self.repo / "unexpected.txt").write_text("outside write scope")
        self.assertEqual(self.verify(fingerprint)[0], 3)

    def test_ignored_input_change_is_not_invisible(self):
        (self.repo / "ignored-input.txt").write_text("before")
        fingerprint = self.seal()
        (self.repo / "ignored-input.txt").write_text("after")
        self.assertEqual(self.verify(fingerprint)[0], 3)

    def test_sealed_commands_cannot_be_tampered(self):
        fingerprint = self.seal()
        data = json.loads(self.sealed.read_text())
        data["request"]["tasks"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(0)"]
        self.sealed.write_text(json.dumps(data))
        self.assertNotEqual(self.verify(fingerprint)[0], 0)

    def test_path_escape_is_invalid(self):
        self.request.write_text(json.dumps({"plan": "plan.md", "allowed_writes": ["../escape"],
                                            "tasks": [self.task()]}))
        code, _ = self.cli("seal", "--root", self.repo, "--input", self.request,
                           "--output", self.sealed)
        self.assertEqual(code, 3)

    def test_symlink_input_is_rejected(self):
        outside = self.base / "outside.txt"
        outside.write_text("private")
        (self.repo / "linked").symlink_to(outside)
        self.request.write_text(json.dumps({"plan": "plan.md", "allowed_writes": [],
                                            "tasks": [self.task()]}))
        self.assertNotEqual(self.cli("seal", "--root", self.repo, "--input", self.request,
                                    "--output", self.sealed)[0], 0)

    def test_dependency_cycle_is_invalid(self):
        task = self.task(depends=["test"])
        self.request.write_text(json.dumps({"plan": "plan.md", "allowed_writes": [], "tasks": [task]}))
        self.assertEqual(self.cli("seal", "--root", self.repo, "--input", self.request,
                                  "--output", self.sealed)[0], 2)

    def test_passing_tap_keeps_coverage_pending_and_raw_output(self):
        code, payload = self.run_plan(self.seal())
        self.assertEqual(code, 0, payload)
        result = json.loads((self.output / "result.json").read_text())
        self.assertEqual(result["coverage_status"], "needs_review")
        logs = [p.read_text() for p in self.output.rglob("*") if p.is_file() and p.suffix != ".json"]
        self.assertTrue(any("ok 1 - one" in text for text in logs), logs)

    def test_red_requires_real_target_failure_not_just_exit_code(self):
        task = self.task(code="print('TAP version 13\\nnot ok 1 - one\\n1..1'); raise SystemExit(1)")
        code, payload = self.run_plan(self.seal(tasks=[task]), phase="red")
        self.assertEqual(code, 0, payload)
        result = json.loads((self.output / "result.json").read_text())
        self.assertEqual(result["phase"], "red")

    def test_red_cannot_accept_a_passing_target(self):
        self.assertNotEqual(self.run_plan(self.seal(), phase="red")[0], 0)

    def test_runner_failure_without_case_is_not_valid_red(self):
        task = self.task(code="print('environment missing'); raise SystemExit(1)")
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]), phase="red")[0], 0)

    def test_missing_target_is_not_a_pass(self):
        task = self.task(name="required", text="TAP version 13\nok 1 - different\n1..1")
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)

    def test_duplicate_case_names_are_ambiguous(self):
        task = self.task(text="TAP version 13\nok 1 - one\nok 2 - one\n1..2")
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)

    def test_skipped_target_is_not_a_pass(self):
        task = self.task(text="TAP version 13\nok 1 - one # SKIP unavailable\n1..1")
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)

    def test_incomplete_tap_is_not_a_pass(self):
        task = self.task(text="TAP version 13\nok 1 - one\n1..2")
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)

    def test_zero_test_report_is_not_a_pass(self):
        task = self.task(text="TAP version 13\n1..0")
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)

    def test_junit_stdout_maps_class_and_test(self):
        task = self.task(name="Suite::one", reporter="junit", text=(
            '<testsuite tests="1" failures="0"><testcase classname="Suite" name="one"/></testsuite>'))
        code, payload = self.run_plan(self.seal(tasks=[task]))
        self.assertEqual(code, 0, payload)

    def test_go_json_uses_package_and_test_identity(self):
        events = [{"Action": "run", "Package": "example", "Test": "TestOne"},
                  {"Action": "pass", "Package": "example", "Test": "TestOne"},
                  {"Action": "pass", "Package": "example"}]
        task = self.task(name="example/TestOne", reporter="go",
                         text="\n".join(json.dumps(x) for x in events))
        code, payload = self.run_plan(self.seal(tasks=[task]))
        self.assertEqual(code, 0, payload)

    def test_jest_json_maps_full_name(self):
        report = {"success": True, "numTotalTests": 1, "numPassedTests": 1,
                  "numFailedTests": 0, "numPendingTests": 0,
                  "testResults": [{"status": "passed", "assertionResults": [
                      {"fullName": "suite one", "status": "passed"}]}]}
        task = self.task(name="suite one", reporter="jest", text=json.dumps(report))
        code, payload = self.run_plan(self.seal(tasks=[task]))
        self.assertEqual(code, 0, payload)

    def test_stale_junit_file_is_rejected(self):
        task = self.task(reporter="junit", code="pass")
        task["report_path"] = "report.xml"
        fingerprint = self.seal(tasks=[task])
        (self.repo / "report.xml").write_text('<testsuite><testcase name="one"/></testsuite>')
        self.assertEqual(self.run_plan(fingerprint)[0], 3)

    def test_existing_untracked_input_cannot_be_hidden_as_a_report(self):
        (self.repo / "report.xml").write_text("user input, not disposable evidence")
        task = self.task(reporter="junit", code="pass")
        task["report_path"] = "report.xml"
        self.request.write_text(json.dumps({"plan": "plan.md", "allowed_writes": [], "tasks": [task]}))
        self.assertEqual(self.cli("seal", "--root", self.repo, "--input", self.request,
                                 "--output", self.sealed)[0], 3)

    def test_new_junit_file_is_accepted_only_after_its_producer(self):
        xml = '<testsuite tests="1"><testcase classname="Suite" name="one"/></testsuite>'
        task = self.task(name="Suite::one", reporter="junit",
                         code="from pathlib import Path; Path('report.xml').write_text(" + repr(xml) + ")")
        task["report_path"] = "report.xml"
        code, payload = self.run_plan(self.seal(tasks=[task]))
        self.assertEqual(code, 0, payload)

    def test_timeout_is_recorded_as_failure_with_raw_evidence(self):
        task = self.task(code="import time; time.sleep(2)")
        task["timeout_seconds"] = 0.03
        code, _ = self.run_plan(self.seal(tasks=[task]))
        self.assertEqual(code, 1)
        result = json.loads((self.output / "result.json").read_text())
        self.assertEqual(result["tasks"][0]["error_kind"], "command-timeout")

    def test_validation_cannot_change_even_allowed_source(self):
        code = "from pathlib import Path; Path('src/logic.py').write_text('changed'); print('TAP version 13\\nok 1 - one\\n1..1')"
        self.assertEqual(self.run_plan(self.seal(tasks=[self.task(code=code)]))[0], 3)

    def test_validation_head_drift_stops_later_independent_tasks(self):
        command = ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                   "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                   "commit", "--allow-empty", "-m", "unexpected validation commit"]
        code = "import subprocess; subprocess.run(" + repr(command) + ",capture_output=True,check=True); print('TAP version 13\\nok 1 - one\\n1..1')"
        first = self.task(code=code)
        later = self.task(task_id="later")
        exit_code, _ = self.run_plan(self.seal(tasks=[first, later]))
        self.assertEqual(exit_code, 3)
        result = json.loads((self.output / "result.json").read_text())
        self.assertEqual(result["execution_status"], "refused")
        self.assertEqual(result["tasks"][1]["status"], "not-run")

    def test_validation_cannot_change_request_outside_project_snapshot(self):
        code = "from pathlib import Path; Path(" + repr(str(self.request)) + ").write_text('{}'); print('TAP version 13\\nok 1 - one\\n1..1')"
        self.assertEqual(self.run_plan(self.seal(tasks=[self.task(code=code)]))[0], 3)

    def test_validation_cannot_change_the_sealed_carrier(self):
        code = "from pathlib import Path; Path(" + repr(str(self.sealed)) + ").write_text('{}'); print('TAP version 13\\nok 1 - one\\n1..1')"
        self.assertEqual(self.run_plan(self.seal(tasks=[self.task(code=code)]))[0], 3)

    def test_visible_prior_evidence_is_not_silently_excluded(self):
        fingerprint = self.seal()
        self.output = self.repo / "evidence/first"
        self.assertEqual(self.run_plan(fingerprint)[0], 0)
        self.output = self.repo / "evidence/second"
        self.assertEqual(self.run_plan(fingerprint)[0], 3)

    def test_failure_blocks_dependents_but_runs_independent_task(self):
        failing = self.task(task_id="bad", code="print('TAP version 13\\nnot ok 1 - one\\n1..1'); raise SystemExit(1)")
        dependent = self.task(task_id="dependent", depends=["bad"])
        independent = self.task(task_id="independent")
        code, _ = self.run_plan(self.seal(tasks=[failing, dependent, independent]))
        self.assertEqual(code, 1)
        result = json.loads((self.output / "result.json").read_text())
        states = {task["id"]: task["status"] for task in result["tasks"]}
        self.assertEqual(states, {"bad": "fail", "dependent": "blocked", "independent": "pass"})

    def test_evidence_directory_cannot_overwrite_prior_run(self):
        fingerprint = self.seal()
        self.assertEqual(self.run_plan(fingerprint)[0], 0)
        before = (self.output / "result.json").read_bytes()
        self.assertNotEqual(self.run_plan(fingerprint)[0], 0)
        self.assertEqual((self.output / "result.json").read_bytes(), before)

    def test_managed_block_preserves_outside_bytes(self):
        target = self.base / "AGENTS.md"
        target.write_bytes(b"user header\n<!-- begin -->\nold\n<!-- end -->\nuser tail\n")
        content = self.base / "content.md"
        content.write_text("new rule\n")
        preview = self.base / "preview.json"
        code, payload = self.cli("managed-preview", "--target", target, "--content", content,
                                 "--output", preview, "--begin-marker", "<!-- begin -->",
                                 "--end-marker", "<!-- end -->")
        self.assertEqual(code, 0, payload)
        fingerprint = json.loads(preview.read_text())["fingerprint"]
        code, payload = self.cli("managed-apply", "--preview", preview, "--fingerprint", fingerprint)
        self.assertEqual(code, 0, payload)
        self.assertEqual(target.read_bytes(), b"user header\n<!-- begin -->\nnew rule\n<!-- end -->\nuser tail\n")

    def test_managed_preview_cannot_overwrite_later_user_change(self):
        target = self.base / "AGENTS.md"
        target.write_text("before")
        content = self.base / "content.md"
        content.write_text("new rule")
        preview = self.base / "preview.json"
        self.assertEqual(self.cli("managed-preview", "--target", target, "--content", content,
                                  "--output", preview)[0], 0)
        target.write_text("user edit")
        fingerprint = json.loads(preview.read_text())["fingerprint"]
        self.assertEqual(self.cli("managed-apply", "--preview", preview, "--fingerprint", fingerprint)[0], 3)
        self.assertEqual(target.read_text(), "user edit")

    def test_managed_incomplete_marker_is_rejected(self):
        target = self.base / "AGENTS.md"
        target.write_text("<!-- begin -->\nuser text")
        content = self.base / "content.md"
        content.write_text("rule")
        self.assertNotEqual(self.cli("managed-preview", "--target", target, "--content", content,
                                    "--output", self.base / "preview.json", "--begin-marker", "<!-- begin -->",
                                    "--end-marker", "<!-- end -->")[0], 0)

    def test_managed_versioned_begin_marker_can_be_updated(self):
        target = self.base / "AGENTS.md"
        target.write_text("user\n<!-- begin old -->\nold rule\n<!-- end -->\ntail\n")
        content = self.base / "content.md"
        content.write_text("new rule\n")
        preview = self.base / "preview.json"
        code, payload = self.cli("managed-preview", "--target", target, "--content", content,
                                 "--output", preview, "--begin-marker", "<!-- begin old -->",
                                 "--end-marker", "<!-- end -->", "--new-begin-marker", "<!-- begin new -->")
        self.assertEqual(code, 0, payload)
        fingerprint = json.loads(preview.read_text())["fingerprint"]
        code, payload = self.cli("managed-apply", "--preview", preview, "--fingerprint", fingerprint)
        self.assertEqual(code, 0, payload)
        self.assertEqual(target.read_text(), "user\n<!-- begin new -->\nnew rule\n<!-- end -->\ntail\n")

    def test_inventory_requires_every_visible_file_to_be_classified(self):
        mapping = {"files": [], "features": [], "batches": []}
        path = self.base / "inventory.json"
        path.write_text(json.dumps(mapping))
        self.assertNotEqual(self.cli("inventory", "--root", self.repo, "--input", path)[0], 0)

    def test_inventory_valid_mapping_still_requires_coverage_review(self):
        mapping = {"files": [
            {"path": "src/logic.py", "kind": "production"},
            {"path": "tests/unit.py", "kind": "test"},
            {"path": "plan.md", "kind": "excluded", "reason": "confirmed plan"},
            {"path": ".gitignore", "kind": "excluded", "reason": "Git ignore configuration"}],
            "features": [{"id": "value", "entrypoint": "src/logic.py", "acceptance": "plan.md",
                          "source_files": ["src/logic.py"], "tests": [
                              {"id": "TC-VALUE", "name": "value", "path": "tests/unit.py", "layer": "unit", "planned": False}],
                          "not_applicable": {"integration": "pure calculation", "e2e": "no standalone journey"}}],
            "batches": [{"id": "batch", "features": ["value"], "depends_on": []}]}
        path = self.base / "inventory.json"
        path.write_text(json.dumps(mapping))
        code, payload = self.cli("inventory", "--root", self.repo, "--input", path)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["evidence"]["coverage_status"], "needs_review")

    def test_red_requires_all_selected_targets_to_fail(self):
        task = self.task(code="print('TAP version 13\\nnot ok 1 - one\\nok 2 - two\\n1..2'); raise SystemExit(1)")
        task["cases"].append({"id": "TC-TWO", "report_name": "two"})
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]), phase="red")[0], 0)

    def test_failed_go_package_cannot_hide_behind_passing_case(self):
        events = [{"Action": "run", "Package": "example", "Test": "TestOne"},
                  {"Action": "pass", "Package": "example", "Test": "TestOne"},
                  {"Action": "fail", "Package": "example"}]
        task = self.task(name="example/TestOne", reporter="go",
                         text="\n".join(json.dumps(x) for x in events))
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)

    def test_go_nested_packages_are_not_conflated(self):
        events = [
            {"Action": "run", "Package": "example/pkg", "Test": "TestParent"},
            {"Action": "pass", "Package": "example/pkg", "Test": "TestParent"},
            {"Action": "pass", "Package": "example/pkg"},
            {"Action": "run", "Package": "example/pkg/sub", "Test": "TestChild"},
            {"Action": "fail", "Package": "example/pkg/sub", "Test": "TestChild"},
            {"Action": "fail", "Package": "example/pkg/sub"},
        ]
        report = "\n".join(json.dumps(x) for x in events)
        task = self.task(name="example/pkg/sub/TestChild", reporter="go",
                         code="print(" + repr(report) + "); raise SystemExit(1)")
        code, payload = self.run_plan(self.seal(tasks=[task]), phase="red")
        self.assertEqual(code, 0, payload)

    def test_jest_failed_suite_cannot_hide_behind_passing_case(self):
        report = {"success": False, "numTotalTests": 1, "numPassedTests": 1,
                  "numFailedTests": 0, "numPendingTests": 0,
                  "testResults": [{"status": "failed", "assertionResults": [
                      {"fullName": "suite one", "status": "passed"}]}]}
        task = self.task(name="suite one", reporter="jest", text=json.dumps(report))
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)

    def test_nested_tap_skip_is_not_execution_evidence(self):
        task = self.task(name="suite", text=(
            "TAP version 13\n# Subtest: suite\n    ok 1 - child # SKIP absent\n    1..1\nok 1 - suite\n1..1"))
        self.assertNotEqual(self.run_plan(self.seal(tasks=[task]))[0], 0)


class LightweightDocumentTests(unittest.TestCase):
    CRITERIA = (
        "目标与行为已确认", "无跨层或公开契约变更", "无持久化或权限变更",
        "无共享时序或不可逆变更", "单一部署单元且回退明确", "验收可执行",
    )

    def document(self):
        rows = "".join(f"| {name} | 是 | 实际源码与已确认需求相符 |\n" for name in self.CRITERIA)
        return (
            "# Local change\n\n文档档位：轻量\n完整文档要求：否\n\n"
            "## 适用性\n\n| 判据 | 结论 | 依据 |\n| --- | --- | --- |\n" + rows +
            "\n## 需求与验收\n\n| 行为 | 预期结果 | 验证 |\n| --- | --- | --- |\n"
            "| 输入数值 | 返回确认值，不额外写数据 | `python test.py` |\n"
            "\n## 实施与证据\n\n| 任务 | 代码落点 | 状态 | 证据 |\n| --- | --- | --- | --- |\n"
            "| T01 修复返回值 | `src.py` | ☐ 未开始 | — |\n"
            "\n## 风险与恢复\n\n局部计算修改，保留原实现，恢复后运行同一目标测试。\n"
        )

    def lint(self, text, stage=False):
        with tempfile.TemporaryDirectory(prefix="agentflow-light-test-",
                                         dir="/tmp" if Path("/tmp").is_dir() else None) as name:
            root = Path(name)
            (root / "src.py").write_text("# actual code location\n")
            (root / "evidence.txt").write_text("verified output\n")
            feature = root / "feature"
            feature.mkdir()
            (feature / "README.md").write_text(text)
            if stage:
                (feature / "spec").mkdir()
                (feature / "spec" / "requirements.md").write_text("# Existing full-chain stage\n")
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/lab/doc_chain.py"), "--root", str(root), str(feature)],
                text=True, capture_output=True, timeout=30, check=False)
            return result.returncode, result.stdout + result.stderr

    def test_all_declared_criteria_and_real_material_pass(self):
        code, output = self.lint(self.document())
        self.assertEqual(code, 0, output)

    def test_unknown_risk_cannot_use_lightweight_profile(self):
        code, output = self.lint(self.document().replace("| 无持久化或权限变更 | 是 |", "| 无持久化或权限变更 | 未知 |"))
        self.assertEqual(code, 1, output)
        self.assertIn("C26", output)

    def test_requested_full_documents_cannot_be_downgraded(self):
        self.assertEqual(self.lint(self.document().replace("完整文档要求：否", "完整文档要求：是"))[0], 1)

    def test_conflicting_complete_document_declarations_are_rejected(self):
        code, output = self.lint(self.document() + "\n完整文档要求：是\n")
        self.assertEqual(code, 1, output)
        self.assertIn("C26", output)

    def test_conflicting_profile_declarations_are_rejected(self):
        code, output = self.lint(self.document() + "\n文档档位：完整\n")
        self.assertEqual(code, 1, output)
        self.assertIn("C26", output)

    def test_repeated_identical_declarations_are_not_a_unique_source(self):
        self.assertEqual(self.lint(self.document() + "\n完整文档要求：否\n")[0], 1)

    def test_missing_criterion_cannot_pass(self):
        text = self.document().replace("| 验收可执行 | 是 | 实际源码与已确认需求相符 |\n", "")
        self.assertEqual(self.lint(text)[0], 1)

    def test_completed_task_needs_existing_evidence(self):
        text = self.document().replace("☐ 未开始 | —", "☑ 已完成 | —")
        self.assertEqual(self.lint(text)[0], 1)
        self.assertEqual(self.lint(text.replace("☑ 已完成 | —", "☑ 已完成 | `evidence.txt`"))[0], 0)

    def test_existing_full_stage_cannot_be_hidden_by_profile_marker(self):
        self.assertEqual(self.lint(self.document(), stage=True)[0], 1)

    def test_profile_declaration_in_a_code_sample_is_not_metadata(self):
        text = self.document().replace("文档档位：轻量", "```text\n文档档位：轻量\n```")
        code, output = self.lint(text)
        self.assertEqual(code, 1, output)
        self.assertIn("C1", output)

    def test_eligibility_table_in_a_code_sample_is_not_actual_evidence(self):
        text = self.document().replace("| 判据 | 结论 | 依据 |", "```text\n| 判据 | 结论 | 依据 |")
        text = text.replace("\n## 需求与验收", "\n```\n\n## 需求与验收")
        self.assertEqual(self.lint(text)[0], 1)

    def test_duplicate_task_ids_are_rejected(self):
        row = "| T01 修复返回值 | `src.py` | ☐ 未开始 | — |"
        self.assertEqual(self.lint(self.document().replace(row, row + "\n" + row))[0], 1)


class EvidenceLayoutTests(unittest.TestCase):
    def check_layout(self, directory):
        lab = str(ROOT / "tools/lab")
        with tempfile.TemporaryDirectory(prefix="agentflow-evidence-layout-",
                                         dir="/tmp" if Path("/tmp").is_dir() else None) as name:
            root = Path(name)
            for zone in ("docs/issues", "docs/features", "episodes", "reviews"):
                target = root / zone
                target.mkdir(parents=True)
                (target / "README.md").write_text("# Record index\n")
            (root / "docs/releases").mkdir()
            (root / "docs/releases/todo.md").write_text("# Work\n")
            (root / "docs/releases/pending-test.md").write_text("# Pending\n")
            artifact = root / "docs/features/batch/testing/project-feature" / directory / "native/run/stdout.txt"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("actual output\n")
            with mock.patch.object(sys, "path", [lab, *sys.path]):
                from gate import workspace
            with mock.patch.object(workspace, "ROOT", root):
                return [str(error) for error in workspace.validate_workspace_artifacts()]

    def test_nested_raw_evidence_is_supported_by_the_record_contract(self):
        self.assertEqual(self.check_layout("evidence"), [])

    def test_nested_scratch_is_supported_but_arbitrary_record_folders_are_not(self):
        self.assertEqual(self.check_layout("scratch"), [])
        self.assertTrue(any("unexpected entry under testing" in error
                            for error in self.check_layout("not-evidence")))


if __name__ == "__main__":
    unittest.main()
