import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "tools" / "lab"
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import isolation  # noqa: E402
import validate  # noqa: E402


class ValidatorRegressionTests(unittest.TestCase):
    def test_json_schema_boolean_is_not_integer_const(self) -> None:
        self.assertFalse(validate.json_values_equal(True, 1))
        self.assertTrue(validate.json_values_equal(1, 1.0))

    def test_rfc3339_requires_timezone_and_accepts_lowercase_separators(self) -> None:
        with self.assertRaises(ValueError):
            validate.parse_rfc3339_date_time("2026-09-14")
        parsed = validate.parse_rfc3339_date_time("2026-09-14t12:00:00z")
        self.assertIsNotNone(parsed.tzinfo)

    def test_timestamp_order_returns_validation_error_for_date_only(self) -> None:
        errors = validate.validate_timestamp_order(
            {"recorded_at": "2026-09-14"}, ROOT / "fixture.json"
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("RFC 3339 date-time", errors[0].message)

    def test_enum_uses_json_schema_number_and_boolean_equality(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            schema = Path(temporary) / "enum.schema.json"
            schema.write_text(json.dumps({"enum": [1]}), encoding="utf-8")
            validator = validate.SchemaValidator(schema)
            self.assertTrue(validator.validate(True))
            self.assertFalse(validator.validate(1.0))

    def test_changed_paths_includes_tracked_and_ignored_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            self._git(repository, "init", "-q")
            self._git(repository, "config", "user.email", "test@example.com")
            self._git(repository, "config", "user.name", "Agentflow Tests")
            (repository / ".gitignore").write_text("*.ignored\n", encoding="utf-8")
            (repository / "tracked.txt").write_text("base\n", encoding="utf-8")
            self._git(repository, "add", ".")
            self._git(repository, "commit", "-q", "-m", "base")
            base = subprocess.run(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")
            (repository / "ordinary.txt").write_text("ordinary\n", encoding="utf-8")
            (repository / "ignored.ignored").write_text("ignored\n", encoding="utf-8")

            changed = isolation.changed_paths(repository, base)

        self.assertEqual(set(changed), {"tracked.txt", "ordinary.txt", "ignored.ignored"})

    def test_bug_record_severity_uses_priority_grades(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "BUG-20260101-001",
            "title": "t",
            "status": "open",
            "severity": "high",
            "error_kind": "other",
            "attribution": "unknown",
            "provenance": "agentflow",
            "project": "p",
            "files": ["a.py"],
            "recorded_at": "2026-01-01T00:00:00Z",
        }
        errors = validator.validate(dict(base))
        self.assertTrue(any("severity" in error.path for error in errors))
        self.assertFalse(validator.validate(dict(base, severity="P1")))

    def test_bug_record_provenance_is_required_and_guards_agentflow_attribution(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "BUG-20260101-002",
            "title": "t",
            "status": "open",
            "severity": "P2",
            "error_kind": "other",
            "attribution": "unknown",
            "provenance": "agentflow",
            "project": "p",
            "files": ["a.py"],
            "recorded_at": "2026-01-01T00:00:00Z",
        }
        without = dict(base)
        without.pop("provenance")
        self.assertTrue(
            any("provenance" in f"{error.path} {error.message}" for error in validator.validate(without))
        )
        contradiction = dict(base, attribution="workflow_policy", provenance="external")
        self.assertTrue(
            any("provenance" in f"{error.path} {error.message}" for error in validator.validate(contradiction))
        )
        self.assertFalse(validator.validate(dict(base, attribution="workflow_policy", provenance="agentflow")))
        self.assertFalse(validator.validate(dict(base, provenance="session-artifact")))

    def test_recurrence_ledger_requires_consolidation_version(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "recurrence.schema.json")
        base = {
            "class_id": "some-class",
            "title": "t",
            "status": "consolidated",
            "first_record": "BUG-20260101-001",
            "occurrences": ["BUG-20260101-001"],
            "recorded_at": "2026-01-01T00:00:00Z",
        }
        self.assertTrue(validator.validate(dict(base)))
        self.assertFalse(validator.validate(dict(base, consolidated_in="0.3.4")))

    def test_recurrence_ledger_filename_must_equal_class_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wrong-name.md"
            path.write_text(
                "---\n"
                "class_id: right-name\n"
                "title: t\n"
                "status: unconsolidated\n"
                "first_record: BUG-20260101-001\n"
                "occurrences:\n"
                "  - BUG-20260101-001\n"
                "recorded_at: 2026-01-01T00:00:00Z\n"
                "---\n",
                encoding="utf-8",
            )
            errors = validate.validate_recurrence_markdown(path)
        self.assertTrue(any("filename must equal class_id" in error.message for error in errors))

    def test_bug_record_verified_requires_closure_criteria(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "BUG-20260101-003",
            "title": "t",
            "status": "verified",
            "severity": "P2",
            "error_kind": "other",
            "attribution": "unknown",
            "provenance": "agentflow",
            "project": "p",
            "files": ["a.py"],
            "recorded_at": "2026-01-01T00:00:00Z",
            "reviewer": "r",
            "review_decision": "approved",
            "regression_status": "pass",
        }
        errors = validator.validate(dict(base))
        self.assertTrue(any("closure_criteria" in f"{e.path} {e.message}" for e in errors))
        self.assertFalse(
            validator.validate(dict(base, closure_criteria="validate.py tests no longer reports the bypass"))
        )

    def test_external_references_require_embedded_fragment_and_inline_citation(self) -> None:
        path = ROOT / "records" / "fixture.md"
        frontmatter = {
            "files": ["example-project@r1:services/api/orders.go"],
        }
        no_fragment = validate.validate_external_excerpts(frontmatter, "正文没有片段。", path)
        self.assertTrue(any("embedded fragment" in error.message for error in no_fragment))
        fragment_but_uncited = validate.validate_external_excerpts(
            frontmatter, "```\ncode\n```\n", path
        )
        self.assertTrue(any("must be cited in the body" in error.message for error in fragment_but_uncited))
        complete = validate.validate_external_excerpts(
            frontmatter,
            "问题代码见 `example-project@r1:services/api/orders.go`：\n```\ncode\n```\n",
            path,
        )
        self.assertEqual(complete, [])
        self.assertEqual(validate.validate_external_excerpts({"files": ["agents/reviewer.md"]}, "", path), [])

    def test_body_references_prose_must_resolve_and_quotations_are_exempt(self) -> None:
        path = ROOT / "records" / "fixture.md"
        dangling = validate.validate_body_references(
            "改动见 other/place/missing.md 的实现。", path
        )
        self.assertTrue(any("exists neither" in error.message for error in dangling))
        personal = validate.validate_body_references(
            "证据在 /Users/someone/project/file.md 里。", path
        )
        self.assertTrue(any("personal absolute path" in error.message for error in personal))
        quoted = validate.validate_body_references(
            "报错原文：\n```\nWrite tool result: plans/legacy-file.json not created\n```\n"
            "当时的命令是 `python3 tools/lab/host_adapter.py`。\n",
            path,
        )
        self.assertEqual(quoted, [])
        resolved = validate.validate_body_references(
            "依据 agents/reviewer.md 的检查协议。", path
        )
        self.assertEqual(resolved, [])
        url_only = validate.validate_body_references(
            "详见 https://example.com/spec.md。", path
        )
        self.assertEqual(url_only, [])

    def test_body_references_cover_cjk_paths_and_skip_version_slashes(self) -> None:
        path = ROOT / "records" / "fixture.md"
        cjk_dangling = validate.validate_body_references(
            "关联设计见 other-repo/docs/缺失文档.md 的说明。", path
        )
        self.assertTrue(any("缺失文档.md" in error.message for error in cjk_dangling))
        cjk_resolved = validate.validate_body_references(
            "见 records/bugs/README.md 的约定。", path
        )
        self.assertEqual(cjk_resolved, [])
        versions = validate.validate_body_references(
            "该行为在 0.3.4/0.3.5 均适用。", path
        )
        self.assertEqual(versions, [])

    def test_review_record_id_matches_recorded_at_and_is_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            record_dir = base / "records" / "reviews" / "demo-feature"
            (record_dir / "archive").mkdir(parents=True)
            (record_dir / "archive" / "doc.md").write_text("x", encoding="utf-8")
            path = record_dir / "review-20260101-001.md"
            path.write_text(
                "---\n"
                "review_id: REV-20260101-001\n"
                "title: t\n"
                "target_project: p\n"
                "target_feature: f\n"
                "source_revision: abc1234\n"
                "reviewed_docs:\n"
                "  - archive/doc.md\n"
                "decision: approved\n"
                "recorded_at: 2026-01-02T00:00:00Z\n"
                "---\n\n## 评审结论\n\nx\n",
                encoding="utf-8",
            )
            relative = Path("records/reviews/demo-feature/review-20260101-001.md")
            seen: dict[str, Path] = {}
            errors = validate.validate_review_markdown(path, relative, seen)
            self.assertTrue(
                any("review_id date must match recorded_at" in error.message for error in errors)
            )
            errors = validate.validate_review_markdown(path, relative, seen)
            self.assertTrue(
                any("duplicate review_id" in error.message for error in errors)
            )

    def test_episode_record_validates_and_pins_filename_to_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "EP-20260101-001.json"
            record = {
                "schema_version": 1,
                "episode_id": "EP-20260101-001",
                "source_type": "acceptance",
                "objective": "o",
                "outcome": "partial",
                "signals": [{"kind": "tests", "value": "ok"}],
                "feedback_summary": "f",
                "agentflow_version": "0.4.0",
                "host": "other",
                "provenance": {"carrier": "session"},
                "redactions": [],
            }
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = validate.validate_episode_document(path)
            self.assertEqual(errors, [])
            path.write_text(json.dumps(dict(record, episode_id="EP-20260101-002")), encoding="utf-8")
            errors = validate.validate_episode_document(path)
            self.assertTrue(any("must equal episode_id" in error.message for error in errors))

    def test_doc_consistency_passes_on_the_current_tree(self) -> None:
        errors = validate.validate_doc_consistency()
        self.assertEqual(errors, [])

    def test_plan_schema_rejects_unknown_status_and_requires_superseded_by(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "plan.schema.json")
        base = {
            "plan_id": "PLAN-TEST-001",
            "plan_version": "0.1.0",
            "status": "approved",
            "objective": "o",
            "recorded_at": "2026-09-17T00:00:00Z",
        }
        self.assertEqual(validator.validate(dict(base)), [])
        errors = validator.validate(dict(base, status="unknown"))
        self.assertTrue(any("status" in error.path for error in errors))
        errors = validator.validate(dict(base, status="superseded"))
        self.assertTrue(any("superseded_by" in f"{e.path} {e.message}" for e in errors))
        self.assertFalse(validator.validate(dict(base, status="superseded", superseded_by="PLAN-TEST-002")))

    def test_plan_markdown_rejects_cycle_duplicate_and_open_blocking_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "PLAN-TEST-002.md"
            path.write_text(
                "---\n"
                "plan_id: PLAN-TEST-002\n"
                "plan_version: 0.1.0\n"
                "status: approved\n"
                "objective: o\n"
                "recorded_at: 2026-09-17T00:00:00Z\n"
                "---\n\n## 进展概览\n\n概述\n\n## 任务清单\n\n"
                "| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| `T01` | 甲 | P0 | a.ts | `T02` | ☑ 已完成 | x |\n"
                "| `T02` | 乙 | P0 | b.ts | `T01` | ☐ 未开始 | |\n"
                "| `T02` | 重复 | P0 | c.ts | — | ☐ 未开始 | |\n"
                "\n### 未决项\n\n"
                "| 编号 | 问题 | 是否阻塞 | 状态 |\n"
                "| --- | --- | --- | --- |\n"
                "| U-01 | 某问题 | 阻塞 | 尚未关闭 |\n"
                "\n## 验证命令\n\n```sh\necho x\n```\n",
                encoding="utf-8",
            )
            errors = validate.validate_plan_markdown(path, Path("records/plans/PLAN-TEST-002.md"))
        messages = [error.message for error in errors]
        self.assertTrue(any("duplicate task id" in m for m in messages))
        self.assertTrue(any("dependency cycle" in m for m in messages))
        self.assertTrue(any("blocking unresolved decision" in m for m in messages))

    @staticmethod
    def _git(repository: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
