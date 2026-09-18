import argparse
import contextlib
import io
import json
import os
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

import eval_runner  # noqa: E402
import host_adapter  # noqa: E402
import isolation  # noqa: E402
import policy  # noqa: E402
import seed_grader  # noqa: E402
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

    def test_changed_paths_is_nul_safe_for_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            self._git(repository, "init", "-q")
            self._git(repository, "config", "user.email", "test@example.com")
            self._git(repository, "config", "user.name", "Agentflow Tests")
            (repository / "base").write_text("x", encoding="utf-8")
            self._git(repository, "add", ".")
            self._git(repository, "commit", "-q", "-m", "base")
            base = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            (repository / "name with space").write_text("x", encoding="utf-8")
            self.assertIn("name with space", isolation.changed_paths(repository, base))

    def test_layout_rejects_equal_or_nested_checker_roots(self) -> None:
        root = Path("/tmp/root").resolve()
        self.assertTrue(isolation.layout_errors(root, root, root))

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
                "provenance": {"carrier": "session", "sanitized": True},
                "redactions": [],
            }
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = validate.validate_episode_document(path)
            self.assertEqual(errors, [])
            missing_sanitized = dict(record, provenance={"carrier": "session"})
            path.write_text(json.dumps(missing_sanitized), encoding="utf-8")
            errors = validate.validate_episode_document(path)
            self.assertTrue(
                any("sanitized" in error.message for error in errors),
                [error.message for error in errors],
            )
            path.write_text(json.dumps(dict(record, episode_id="EP-20260101-002")), encoding="utf-8")
            errors = validate.validate_episode_document(path)
            self.assertTrue(any("must equal episode_id" in error.message for error in errors))

    def test_examples_contract_includes_the_invalid_plan(self) -> None:
        # Regression for a silent gap: a case-sensitive glob once excluded the uppercase-named
        # invalid plan example, so the negative example never exercised the plan gate.
        errors = validate.validate_examples()
        self.assertEqual([error.message for error in errors], [])

    def test_doc_consistency_passes_on_the_current_tree(self) -> None:
        errors = validate.validate_doc_consistency()
        self.assertEqual(errors, [])

    def test_agents_md_plan_contract_tripwire_rejects_pre_050_wording(self) -> None:
        # The tripwire must fire on either stale marker of the pre-0.5.0 JSON plan
        # contract. The helper is pure, so it is pointed at a temporary file instead of
        # the real AGENTS.md, which stays untouched. The current-tree test above proves
        # the happy path only; the wiring into validate_doc_consistency is evidenced by
        # a runtime throwaway-copy flip, not by that test.
        for marker in ("plans are JSON", "<plan_id>.json"):
            with self.subTest(marker=marker):
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "AGENTS.md"
                    path.write_text(f"stale contract residue: {marker}\n", encoding="utf-8")
                    errors = validate.validate_agents_md_plan_contract(path)
                self.assertTrue(
                    any("pre-0.5.0 JSON plan contract" in error.message for error in errors),
                    [error.message for error in errors],
                )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "AGENTS.md"
            path.write_text(
                "plans are Markdown hybrids named <plan_id>.md; see records/plans/README.md\n",
                encoding="utf-8",
            )
            self.assertEqual(validate.validate_agents_md_plan_contract(path), [])

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


# PLAN-BUSINESS-EVAL-001 T09: pin the business evaluation slice (seed_grader golden fixtures,
# the frozen metric/result contracts, validate_business_evals, the isolation fourth position,
# and the adapter's business request/dry-run contract). Every fixture lives in a temporary
# directory or in the function arguments; no test calls a host, the network, or a model.
class SeedGraderGoldenTests(unittest.TestCase):
    """seed_grader golden fixtures: not too tight (real hits count) and not too loose."""

    CASE_ID = "BT-TEST"
    SEED = {
        "seed_id": "TEST-S1",
        "doc_ref": "docs/spec.md",
        "strategy": {"type": "path_and_anchor", "anchors": ["静默重投"], "mode": "any"},
    }

    def _seed_list(self, directory: Path, seeds: list[dict[str, Any]] | None = None) -> Path:
        path = Path(directory) / "seeds.json"
        path.write_text(
            json.dumps(
                {"schema_version": 1, "case_id": self.CASE_ID, "seeds": seeds or [self.SEED]}
            ),
            encoding="utf-8",
        )
        return path

    def _findings(self, directory: Path, rep: int, findings: list[dict[str, str]]) -> Path:
        rep_dir = Path(directory) / f"rep-{rep}"
        rep_dir.mkdir(parents=True, exist_ok=True)
        path = rep_dir / "findings.json"
        path.write_text(
            json.dumps({"schema_version": 1, "case_id": self.CASE_ID, "findings": findings}),
            encoding="utf-8",
        )
        return path

    def test_golden_findings_hit_their_seeds(self) -> None:
        # Too-tight detector: a correct finding (right path, anchor present) is a hit and the
        # repetition counts as accepted, never as a miss.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seeds = self._seed_list(base)
            findings_dir = base / "findings"
            self._findings(
                findings_dir,
                1,
                [{"path": "docs/spec.md", "issue": "行话未就地说明", "evidence": "原文含 静默重投 一词"}],
            )
            document = seed_grader.grade_case(seed_grader.load_seeds(seeds), findings_dir, 0.5)
        repetition = document["repetitions"][0]
        self.assertEqual(repetition["status"], "graded")
        self.assertEqual(repetition["hits"], ["TEST-S1"])
        self.assertEqual(repetition["missed"], [])
        self.assertEqual(repetition["unmatched_by_doc"], {})
        self.assertEqual(repetition["recall"], 1.0)
        self.assertTrue(repetition["accepted"])
        self.assertEqual(repetition["escaped_defects"], 0)
        self.assertEqual(seed_grader.exit_code(document), 0)

    def test_near_miss_findings_are_not_hits_and_land_in_unmatched_by_doc(self) -> None:
        # Too-loose detector: the right path without an anchor, and the right anchor on a
        # different document, must both stay misses; neither finding is penalized, but both
        # are reported as unmatched.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seeds = self._seed_list(base)
            findings_dir = base / "findings"
            self._findings(
                findings_dir,
                1,
                [
                    {"path": "docs/spec.md", "issue": "anchor missing", "evidence": "unrelated quote"},
                    {"path": "docs/other.md", "issue": "path wrong", "evidence": "原文含 静默重投"},
                ],
            )
            document = seed_grader.grade_case(seed_grader.load_seeds(seeds), findings_dir, 0.5)
        repetition = document["repetitions"][0]
        self.assertEqual(repetition["hits"], [])
        self.assertEqual(repetition["missed"], ["TEST-S1"])
        self.assertEqual(repetition["recall"], 0.0)
        self.assertFalse(repetition["accepted"])
        self.assertEqual(repetition["escaped_defects"], 1)
        self.assertEqual(
            repetition["unmatched_by_doc"],
            {
                "docs/spec.md": 1,
                "docs/other.md": 1,
            },
        )
        self.assertEqual(seed_grader.exit_code(document), 0)

    def test_unknown_strategy_fails_closed(self) -> None:
        # An answer key that declares a strategy the grader does not implement must abort:
        # no guessed matching rule, no score document, exit code 2.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            unknown_type = dict(self.SEED, strategy={"type": "semantic-similarity", "anchors": ["x"]})
            seeds = self._seed_list(base, [unknown_type])
            findings_dir = base / "findings"
            self._findings(findings_dir, 1, [])
            with self.assertRaises(seed_grader.SeedGraderError) as caught:
                seed_grader.load_seeds(seeds)
            self.assertIn("unknown strategy.type", str(caught.exception))
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = seed_grader.main(
                    ["--seeds", str(seeds), "--findings-dir", str(findings_dir), "--min-recall", "0.5"]
                )
        self.assertEqual(code, 2)
        self.assertEqual(standard_out.getvalue(), "")
        self.assertIn("unknown strategy.type", standard_error.getvalue())
        self.assertIn("fail-closed, no guessing", standard_error.getvalue())
        with self.assertRaises(seed_grader.SeedGraderError) as caught_mode:
            seed_grader.validate_seed_document(
                {
                    "case_id": self.CASE_ID,
                    "seeds": [dict(self.SEED, strategy={"type": "path_and_anchor", "mode": "all", "anchors": ["x"]})],
                },
                "seed document",
            )
        self.assertIn("unknown strategy.mode", str(caught_mode.exception))

    def test_missing_findings_fail_that_repetition_and_exit_two(self) -> None:
        # A missing artifact is a failed repetition with its error recorded — never a zero
        # score — and the process exits 2 while still printing the document.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seeds = self._seed_list(base)
            findings_dir = base / "findings"
            hit = [{"path": "docs/spec.md", "issue": "i", "evidence": "静默重投"}]
            self._findings(findings_dir, 1, hit)
            (findings_dir / "rep-2").mkdir()  # the repetition directory exists, the artifact does not
            self._findings(findings_dir, 3, hit)
            document = seed_grader.grade_case(seed_grader.load_seeds(seeds), findings_dir, 0.5)
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = seed_grader.main(
                    ["--seeds", str(seeds), "--findings-dir", str(findings_dir), "--min-recall", "0.5"]
                )
        repetitions = {item["rep"]: item for item in document["repetitions"]}
        self.assertEqual(repetitions[1]["status"], "graded")
        self.assertEqual(repetitions[2]["status"], "failed")
        self.assertIn("cannot read", repetitions[2]["error"])
        self.assertNotIn("recall", repetitions[2])
        self.assertEqual(repetitions[3]["status"], "graded")
        self.assertEqual(document["summary"], {"reps_graded": 2, "reps_failed": 1, "total_seeds": 1})
        self.assertEqual(seed_grader.exit_code(document), 2)
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(standard_out.getvalue())["repetitions"][1]["status"], "failed")
        self.assertIn("repetition 2 failed", standard_error.getvalue())

        # A gap in the repetition numbering is a failed repetition too (the run must not
        # silently shrink), because a higher repetition directory exists.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seeds = self._seed_list(base)
            findings_dir = base / "findings"
            hit = [{"path": "docs/spec.md", "issue": "i", "evidence": "静默重投"}]
            self._findings(findings_dir, 1, hit)
            self._findings(findings_dir, 3, hit)
            gap_document = seed_grader.grade_case(seed_grader.load_seeds(seeds), findings_dir, 0.5)
        self.assertEqual([item["status"] for item in gap_document["repetitions"]], ["graded", "failed", "graded"])
        self.assertIn("repetition directory rep-2 is missing", gap_document["repetitions"][1]["error"])
        self.assertEqual(seed_grader.exit_code(gap_document), 2)

    def test_path_spellings_of_the_same_document_are_equivalent(self) -> None:
        # The seed's doc_ref is snapshot-relative; an absolute path prefix, a `./` prefix,
        # and the bare relative path all name the same document and all count as hits.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seeds = self._seed_list(base)
            findings_dir = base / "findings"
            spellings = ("/opt/snapshot/docs/spec.md", "./docs/spec.md", "docs/spec.md")
            for rep, path in enumerate(spellings, start=1):
                self._findings(findings_dir, rep, [{"path": path, "issue": "i", "evidence": "静默重投"}])
            document = seed_grader.grade_case(seed_grader.load_seeds(seeds), findings_dir, 0.5)
        for item, path in zip(document["repetitions"], spellings):
            self.assertEqual(item["status"], "graded", path)
            self.assertEqual(item["hits"], ["TEST-S1"], path)
            self.assertEqual(item["missed"], [], path)
        self.assertEqual(document["summary"], {"reps_graded": 3, "reps_failed": 0, "total_seeds": 1})

    def test_off_target_findings_do_not_count_toward_recall(self) -> None:
        # With target_docs set, a finding whose path is outside the allowed documents is recorded
        # as off_target and must neither rescue a missed seed nor fail the repetition. Only the
        # in-scope hit counts toward recall.
        target_docs = ["docs/spec.md"]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seeds = self._seed_list(base)
            findings_dir = base / "findings"
            self._findings(
                findings_dir,
                1,
                [
                    {"path": "docs/spec.md", "issue": "hit", "evidence": "静默重投"},
                    {"path": "docs/other.md", "issue": "off target", "evidence": "静默重投"},
                ],
            )
            document = seed_grader.grade_case(
                seed_grader.load_seeds(seeds), findings_dir, 0.5, target_docs=target_docs
            )
        repetition = document["repetitions"][0]
        self.assertEqual(repetition["status"], "graded")
        self.assertEqual(repetition["hits"], ["TEST-S1"])
        self.assertEqual(repetition["missed"], [])
        self.assertEqual(repetition["recall"], 1.0)
        self.assertEqual(repetition["off_target"], [{"path": "docs/other.md", "issue": "off target"}])

    def test_unmatched_findings_above_the_per_doc_cap_fail_the_repetition(self) -> None:
        # Spamming off-topic findings on an allowed document does not game recall: once a target
        # document accumulates more unmatched findings than the per-doc cap, the repetition fails.
        target_docs = ["docs/spec.md"]
        spam = [
            {"path": "docs/spec.md", "issue": f"noise {index}", "evidence": "unrelated"}
            for index in range(seed_grader.MAX_UNMATCHED_PER_DOC + 1)
        ]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seeds = self._seed_list(base)
            findings_dir = base / "findings"
            self._findings(findings_dir, 1, spam)
            document = seed_grader.grade_case(
                seed_grader.load_seeds(seeds), findings_dir, 0.5, target_docs=target_docs
            )
        repetition = document["repetitions"][0]
        self.assertEqual(repetition["status"], "failed")
        self.assertIn("unmatched-finding cap exceeded", repetition["error"])
        self.assertEqual(document["summary"]["reps_failed"], 1)
        self.assertEqual(seed_grader.exit_code(document), 2)


class ContractPinTests(unittest.TestCase):
    """The frozen metric/result contracts the business slice must not drift (C6)."""

    EXPECTED_METRICS = (
        "acceptance_rate",
        "first_pass_review_rate",
        "correction_count",
        "escaped_defects",
        "permission_violations",
        "unnecessary_delegation_count",
        "tool_failures",
        "latency_ms",
    )
    EXPECTED_REPETITION_FIELDS = (
        "accepted",
        "first_pass_review",
        "correction_count",
        "escaped_defects",
        "permission_violations",
        "unnecessary_delegation",
        "tool_failures",
        "latency_ms",
        "evidence_refs",
    )

    def test_metric_names_are_exactly_the_eight_contract_metrics(self) -> None:
        self.assertEqual(eval_runner.METRIC_NAMES, self.EXPECTED_METRICS)
        self.assertEqual(len(eval_runner.METRIC_NAMES), 8)
        schema = json.loads(
            (ROOT / "schemas" / "evaluation-result.schema.json").read_text(encoding="utf-8")
        )
        summary = schema["properties"]["summary"]
        self.assertEqual(tuple(summary["required"]), self.EXPECTED_METRICS)
        self.assertEqual(set(summary["properties"]), set(self.EXPECTED_METRICS))
        self.assertIs(summary["additionalProperties"], False)

    def test_adapter_result_requires_exactly_the_nine_repetition_fields(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "adapter-case-result.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(tuple(schema["required"]), self.EXPECTED_REPETITION_FIELDS)
        self.assertEqual(set(schema["properties"]), set(self.EXPECTED_REPETITION_FIELDS))
        self.assertIs(schema["additionalProperties"], False)

        # The runner's conformance check enforces the same nine names, one by one.
        cases = [{"case_id": "BT-TEST", "slice": "business-doc-review", "holdout": False, "protected_guardrails": ["g"]}]
        args = argparse.Namespace(
            host="claude",
            model="test-model",
            permissions_profile="workspace-write",
            fixture_revision="fixture-test",
            repeat_count=1,
        )
        repetition = {
            "accepted": True,
            "first_pass_review": True,
            "correction_count": 0,
            "escaped_defects": 0,
            "permission_violations": 0,
            "unnecessary_delegation": False,
            "tool_failures": 0,
            "latency_ms": 1.5,
            "evidence_refs": ["result://test/BT-TEST/1"],
        }
        response = {
            "observed_context": {
                "host": "claude",
                "model": "test-model",
                "permissions_profile": "workspace-write",
                "fixture_revision": "fixture-test",
                "evidence_refs": ["context://test"],
            },
            "case_results": [
                {
                    "case_id": "BT-TEST",
                    "slice": "business-doc-review",
                    "holdout": False,
                    "protected_guardrails": ["g"],
                    "repetitions": [repetition],
                }
            ],
        }
        ordered, errors = eval_runner.validate_adapter_response(response, cases, args)
        self.assertEqual(errors, [])
        self.assertIsNotNone(ordered)
        for field in self.EXPECTED_REPETITION_FIELDS:
            with self.subTest(field=field):
                broken = json.loads(json.dumps(response))
                del broken["case_results"][0]["repetitions"][0][field]
                _, broken_errors = eval_runner.validate_adapter_response(broken, cases, args)
                self.assertTrue(
                    any(field in error.message for error in broken_errors), [str(e) for e in broken_errors]
                )

    def test_compare_requires_the_matching_seven_field_context(self) -> None:
        baseline = json.loads(
            (ROOT / "examples" / "evaluation-results" / "baseline.json").read_text(encoding="utf-8")
        )
        candidate = json.loads(
            (ROOT / "examples" / "evaluation-results" / "candidate.json").read_text(encoding="utf-8")
        )
        fields = (
            "suite_revision",
            "host",
            "model",
            "permissions_profile",
            "fixture_revision",
            "repeat_count",
            "suite_case_count",
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            code, output = self._compare(directory, baseline, candidate)
            self.assertEqual(code, 0, output)
            comparison = json.loads(output)
            self.assertEqual(tuple(comparison["context"]), fields)
            self.assertEqual(set(comparison["deltas"]), set(eval_runner.METRIC_NAMES))

            for field in fields:
                with self.subTest(field=field):
                    variant = json.loads(json.dumps(candidate))
                    if field in ("host", "model", "permissions_profile", "fixture_revision"):
                        variant[field] = "other-value"
                        variant["observed_context"][field] = "other-value"
                    elif field == "repeat_count":
                        variant[field] = 1
                        for case in variant["case_results"]:
                            case["repetitions"] = case["repetitions"][:1]
                    elif field == "suite_case_count":
                        extra = json.loads(json.dumps(variant["case_results"][0]))
                        extra["case_id"] = "AF-002"
                        variant["case_results"].append(extra)
                        variant["suite_case_count"] = 2
                    else:
                        variant[field] = "other-value"
                    code, output = self._compare(directory, baseline, variant)
                    self.assertEqual(code, 1, output)
                    self.assertIn(
                        f"{field}: baseline and candidate execution context must match", output
                    )

    @staticmethod
    def _compare(directory: Path, baseline: dict[str, Any], candidate: dict[str, Any]) -> tuple[int, str]:
        baseline_path = directory / "baseline.json"
        candidate_path = directory / "candidate.json"
        baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        standard_out, standard_error = io.StringIO(), io.StringIO()
        args = argparse.Namespace(
            baseline=str(baseline_path), candidate=str(candidate_path), output=None
        )
        with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
            code = eval_runner.compare_command(args)
        return code, standard_out.getvalue() + standard_error.getvalue()


class BusinessValidationTests(unittest.TestCase):
    """validate_business_evals: the shipped slice passes, every mutated fixture is caught."""

    def test_shipped_suite_and_an_unmodified_copy_validate_clean(self) -> None:
        self.assertEqual(validate.validate_business_evals(), [])
        shipped = self._shipped_cases()
        self.assertEqual(len(shipped), 3)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._write_fixture(directory, shipped)
            # The copies live outside the repository, so this also exercises the fallback
            # schema path in validate_business_evals.
            self.assertEqual(validate.validate_business_evals(directory), [])

    def test_mutated_business_fixtures_are_rejected_one_by_one(self) -> None:
        shipped = self._shipped_cases()
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory(
            dir=ROOT, prefix=".contract-seeds-"
        ) as seed_temporary:
            # validate_business_seeds resolves seeds_ref inside the repository, so the mutated
            # seed lists live in a temporary directory inside the checkout; the context manager
            # removes it again, and the case copies stay outside the repository. The public
            # case files themselves are never written to.
            directory = Path(temporary)
            seed_directory = Path(seed_temporary)

            with self.subTest(case="missing target_docs"):
                self._write_fixture(directory, shipped, mutate=lambda case: case.pop("target_docs"))
                self._assert_messages(directory, "required property 'target_docs'")

            with self.subTest(case="seed doc_ref outside target_docs"):
                self._write_fixture(directory, shipped, mutate=lambda case: case.update(target_docs=["docs/other.md"]))
                self._assert_messages(directory, "is not one of the case target_docs")

            with self.subTest(case="case count out of range"):
                self._write_fixture(directory, shipped, count=2)
                self._assert_messages(directory, "expected 3-10 business cases, found 2")

            with self.subTest(case="input_ref outside the repository"):
                self._write_fixture(directory, shipped, mutate=lambda case: case.update(input_ref="../outside-the-repository.md"))
                self._assert_messages(directory, "input_ref does not resolve to a file")

            with self.subTest(case="duplicate seed_id"):
                seed_path = seed_directory / "duplicate.seeds.json"
                seed_path.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "case_id": "BT-001",
                            "seeds": [
                                self._seed(shipped["BT-001"]["target_docs"][0], "S1", "path_and_anchor"),
                                self._seed(shipped["BT-001"]["target_docs"][0], "S1", "path_and_anchor"),
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                self._write_fixture(directory, shipped, seeds_ref=seed_path.relative_to(ROOT).as_posix())
                self._assert_messages(directory, "duplicate seed_id 'S1'")

            with self.subTest(case="unknown seed strategy.type"):
                seed_path.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "case_id": "BT-001",
                            "seeds": [
                                self._seed(shipped["BT-001"]["target_docs"][0], "S1", "path_and_anchor"),
                                self._seed(shipped["BT-001"]["target_docs"][0], "S2", "semantic-similarity"),
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                self._write_fixture(directory, shipped, seeds_ref=seed_path.relative_to(ROOT).as_posix())
                self._assert_messages(directory, "unknown strategy.type 'semantic-similarity'")

    @staticmethod
    def _seed(doc_ref: str, seed_id: str, strategy_type: str) -> dict[str, Any]:
        return {
            "seed_id": seed_id,
            "doc_ref": doc_ref,
            "strategy": {"type": strategy_type, "anchors": ["anchor"]},
        }

    @staticmethod
    def _shipped_cases() -> dict[str, dict[str, Any]]:
        cases: dict[str, dict[str, Any]] = {}
        for path in sorted((ROOT / "evals" / "business").glob("BT-*.json")):
            cases[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        return cases

    @staticmethod
    def _write_fixture(
        directory: Path,
        shipped: dict[str, dict[str, Any]],
        count: int = 3,
        mutate=None,
        seeds_ref: str | None = None,
    ) -> None:
        for existing in directory.glob("BT-*.json"):  # each fixture call is self-contained
            existing.unlink()
        for name in ("BT-001", "BT-002", "BT-003")[:count]:
            document = dict(shipped[name])
            if name == "BT-001":
                if mutate is not None:
                    mutate(document)
                if seeds_ref is not None:
                    document["seeds_ref"] = seeds_ref
            (directory / f"{name}.json").write_text(json.dumps(document), encoding="utf-8")

    @staticmethod
    def _assert_messages(directory: Path, expected: str) -> None:
        messages = [
            f"{error.path} {error.message}" for error in validate.validate_business_evals(directory)
        ]
        if not any(expected in message for message in messages):
            raise AssertionError(f"expected {expected!r} in {messages!r}")


class BusinessSuiteLoadingTests(unittest.TestCase):
    """eval_runner's business suite path: the loader and the --business-root gate."""

    def test_business_suite_loads_all_three_cases_with_their_business_fields(self) -> None:
        cases = eval_runner.load_suite(ROOT / "evals" / "business")
        self.assertEqual([case["case_id"] for case in cases], ["BT-001", "BT-002", "BT-003"])
        for case in cases:
            with self.subTest(case=case["case_id"]):
                shipped = json.loads(
                    (ROOT / "evals" / "business" / f"{case['case_id']}.json").read_text(encoding="utf-8")
                )
                self.assertEqual(case, shipped)
                for field in eval_runner.BUSINESS_CASE_FIELDS:
                    self.assertIn(field, case)
                    self.assertEqual(case[field], shipped[field])

    def test_business_suite_run_without_business_root_is_refused(self) -> None:
        # run_adapter refuses a business suite before it touches the adapter command, so
        # calling it directly is the shortest reachable path to the guard: no host, no
        # subprocess, and the placeholder adapter is never looked up.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for directory in (base / "repo", base / "workspace", base / "holdout"):
                directory.mkdir()
            args = argparse.Namespace(
                suite="evals/business",
                repository=str(base / "repo"),
                workspace=str(base / "workspace"),
                holdout_root=str(base / "holdout"),
                adapter="definitely-not-an-adapter-command",
            )
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = eval_runner.run_adapter(args)
        self.assertEqual(code, 1)
        self.assertEqual(standard_out.getvalue(), "")
        self.assertIn("--business-root is required for the suite", standard_error.getvalue())


class BuildRequestRepeatCountTests(unittest.TestCase):
    """build_request refuses to overwrite a case's frozen repeat_count with --repeat-count.

    Regression: build_request used to write args.repeat_count into every case entry and
    never read the case's own frozen value, so a caller could pass a different
    --repeat-count and produce baseline/candidate runs that are not comparable. The
    request structure and the --repeat-count CLI argument are unchanged; the check only
    applies to cases that carry the key (suite files always do).
    """

    def _case(self, case_id: str = "AF-TEST", repeat_count: int | None = None) -> dict[str, Any]:
        case: dict[str, Any] = {
            "case_id": case_id,
            "slice": "public-slice",
            "objective": "o",
            "input_ref": "evals/public/inputs/AF-001.md",
            "acceptance_criteria": ["c"],
            "protected_guardrails": ["g"],
            "holdout": False,
        }
        if repeat_count is not None:
            case["repeat_count"] = repeat_count
        return case

    def _args(self, repeat_count: int, base: Path) -> argparse.Namespace:
        for directory in ("repo", "workspace", "holdout"):
            (base / directory).mkdir(exist_ok=True)
        return argparse.Namespace(
            source_kind="baseline",
            source_revision="rev-test",
            artifact_digest="sha256:" + "a" * 64,
            result_id="TEST-RUN",
            agentflow_version="0.5.2",
            suite_revision="suite-test",
            host="claude",
            model="test-model",
            permissions_profile="workspace-write",
            fixture_revision="fixture-test",
            repeat_count=repeat_count,
            repository=str(base / "repo"),
            workspace=str(base / "workspace"),
            holdout_root=str(base / "holdout"),
        )

    def test_mismatched_frozen_repeat_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            with self.assertRaisesRegex(
                ValueError, r"case 'AF-TEST' declares repeat_count 5 but --repeat-count is 1"
            ):
                eval_runner.build_request(self._args(1, base), [self._case(repeat_count=5)])

    def test_all_mismatched_cases_are_named_in_one_message(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            with self.assertRaises(ValueError) as caught:
                eval_runner.build_request(
                    self._args(1, base),
                    [
                        self._case("AF-TEST", repeat_count=5),
                        self._case("AF-TEST-2", repeat_count=3),
                    ],
                )
        message = str(caught.exception)
        self.assertIn("case 'AF-TEST' declares repeat_count 5", message)
        self.assertIn("case 'AF-TEST-2' declares repeat_count 3", message)
        self.assertIn("a run must use the frozen case value", message)

    def test_matching_repeat_count_builds_the_request_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            request = eval_runner.build_request(self._args(5, base), [self._case(repeat_count=5)])
        self.assertEqual(request["repeat_count"], 5)
        self.assertEqual(request["cases"][0]["repeat_count"], 5)

    def test_case_without_repeat_count_key_still_builds(self) -> None:
        # Synthetic cases may omit the frozen key; the check only applies when it exists.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            request = eval_runner.build_request(self._args(1, base), [self._case()])
        self.assertEqual(request["cases"][0]["repeat_count"], 1)


class IsolationBusinessRootTests(unittest.TestCase):
    """layout_errors keeps its three-argument behavior and adds an optional fourth position."""

    def test_three_argument_layout_matches_the_default_fourth_position(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repository, candidate, holdout = base / "repo", base / "candidate", base / "holdout"
            for directory in (repository, candidate, holdout):
                directory.mkdir()
            three = isolation.layout_errors(repository, candidate, holdout)
            self.assertEqual(three, [])
            self.assertEqual(three, isolation.layout_errors(repository, candidate, holdout, None))
            self.assertFalse(any("business" in error for error in three), three)
            nested = isolation.layout_errors(repository, repository / "nested", holdout)
            self.assertEqual(nested, isolation.layout_errors(repository, repository / "nested", holdout, None))
            self.assertTrue(nested)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(LAB / "isolation.py"),
                    "validate-layout",
                    "--repository",
                    str(repository),
                    "--candidate",
                    str(candidate),
                    "--holdout",
                    str(holdout),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            layout = json.loads(completed.stdout)
            self.assertEqual(set(layout), {"repository", "candidate", "holdout"})
            self.assertNotIn("business_root", layout)

    def test_four_argument_layout_accepts_a_separate_root_and_flags_overlaps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repository, candidate, holdout, business = (
                base / name for name in ("repo", "candidate", "holdout", "business")
            )
            self.assertEqual(isolation.layout_errors(repository, candidate, holdout, business), [])
            inside_repository = isolation.layout_errors(repository, candidate, holdout, repository / "snapshot")
            self.assertTrue(
                any("must not be nested in or contain the repository" in error for error in inside_repository),
                inside_repository,
            )
            same_as_holdout = isolation.layout_errors(repository, candidate, holdout, holdout)
            self.assertTrue(
                any("must differ from the private holdout" in error for error in same_as_holdout),
                same_as_holdout,
            )
            contains_candidate = isolation.layout_errors(repository, candidate, holdout, candidate / "inside")
            self.assertTrue(
                any("must not be nested in or contain the candidate worktree" in error for error in contains_candidate),
                contains_candidate,
            )

            for directory in (repository, candidate, holdout, business):
                directory.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(LAB / "isolation.py"),
                    "validate-layout",
                    "--repository",
                    str(repository),
                    "--candidate",
                    str(candidate),
                    "--holdout",
                    str(holdout),
                    "--business-root",
                    str(business),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["business_root"], str(business.resolve()))

            nested = repository / "nested-snapshot"
            nested.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(LAB / "isolation.py"),
                    "validate-layout",
                    "--repository",
                    str(repository),
                    "--candidate",
                    str(candidate),
                    "--holdout",
                    str(holdout),
                    "--business-root",
                    str(nested),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("business snapshot root must not be nested in or contain the repository", completed.stderr)


class AdapterBusinessRequestTests(unittest.TestCase):
    """host_adapter's business branch: request validation, dry run, and grading overwrite."""

    def test_valid_business_request_passes_and_contract_deviations_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            workspace, _, snapshot = self._layout(base)
            request = self._request(base, business_root=snapshot.resolve())
            self.assertTrue(host_adapter.is_business_request(request))
            resolved_workspace, cases = host_adapter.validate_request(request, "claude", dry_run=True)
            self.assertEqual(resolved_workspace, workspace.resolve())
            self.assertEqual([case["case_id"] for case in cases], ["BT-TEST"])

            # The business branch is keyed on the request-level business_root, and a case
            # that carries business fields without it is rejected instead of being waved
            # through as a public case; a genuine public case stays acceptable under a
            # read-only profile.
            public_case = json.loads(
                (ROOT / "evals" / "public" / "AF-001.json").read_text(encoding="utf-8")
            )
            public = self._request(base, profile="read-only", cases=[public_case])
            self.assertFalse(host_adapter.is_business_request(public))
            host_adapter.validate_request(public, "claude", dry_run=True)
            with self.assertRaisesRegex(ValueError, "business cases require business_root"):
                host_adapter.validate_request(
                    self._request(base, profile="read-only"), "claude", dry_run=True
                )

            permutations = (
                (
                    "read-only profile cannot write findings",
                    self._request(base, business_root=snapshot.resolve(), profile="read-only"),
                    True,
                    "read-only profile cannot write the findings artifact",
                ),
                (
                    "a real run requires the seed patch",
                    self._request(base, business_root=snapshot.resolve()),
                    False,
                    "requires --seed-patch",
                ),
                (
                    "uppercase target_pin",
                    self._request(
                        base, business_root=snapshot.resolve(), cases=[self._business_case(target_pin="A" * 40)]
                    ),
                    True,
                    "40-character lowercase hex",
                ),
                (
                    "short target_pin",
                    self._request(
                        base, business_root=snapshot.resolve(), cases=[self._business_case(target_pin="a" * 39)]
                    ),
                    True,
                    "40-character lowercase hex",
                ),
            )
            for label, invalid, dry_run, message in permutations:
                with self.subTest(label=label):
                    with self.assertRaisesRegex(ValueError, message):
                        host_adapter.validate_request(invalid, "claude", dry_run=dry_run)

    def test_business_cases_must_share_a_single_target_pin(self) -> None:
        # M3 regression: the shared-pin guard had no test coverage. Two business cases
        # whose target_pins differ must be rejected, never silently scored against one pin.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            _, _, snapshot = self._layout(base)
            cases = [
                self._business_case(),
                self._business_case(case_id="BT-TEST-2", target_pin="b" * 40),
            ]
            with self.assertRaisesRegex(ValueError, "must share the same target_pin"):
                host_adapter.validate_request(
                    self._request(base, business_root=snapshot.resolve(), cases=cases),
                    "claude",
                    dry_run=True,
                )

    def test_target_docs_must_be_snapshot_relative_posix_paths(self) -> None:
        # Path-safety regression: an absolute target_docs entry ("/etc/passwd") and a
        # ".." segment entry ("../../outside.md") used to pass the business branch
        # untouched. The check is lexical, so a dry run rejects both without any snapshot
        # access, and a plain snapshot-relative path still passes.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            _, _, snapshot = self._layout(base)
            for label, target_docs, message in (
                ("absolute path", ["/etc/passwd"], "not an absolute path"),
                (".. segment", ["../../outside.md"], "without '..' segments"),
            ):
                with self.subTest(label=label):
                    with self.assertRaisesRegex(ValueError, message):
                        host_adapter.validate_request(
                            self._request(
                                base,
                                business_root=snapshot.resolve(),
                                cases=[self._business_case(target_docs=target_docs)],
                            ),
                            "claude",
                            dry_run=True,
                        )
            valid = self._request(
                base,
                business_root=snapshot.resolve(),
                cases=[
                    self._business_case(
                        target_docs=["docs/features/feature-A/spec/be/spec-backend.md"]
                    )
                ],
            )
            host_adapter.validate_request(valid, "claude", dry_run=True)

    def test_real_business_run_pins_the_snapshot_head_and_replays_the_seed_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            _, _, snapshot = self._layout(base)
            self._run_git(snapshot, "init", "-q")
            self._run_git(snapshot, "config", "user.email", "test@example.com")
            self._run_git(snapshot, "config", "user.name", "Agentflow Tests")
            document = snapshot / "docs/features/feature-A/spec/be/spec-backend.md"
            document.parent.mkdir(parents=True)
            document.write_text("batch limit: <=50 files\n", encoding="utf-8")
            self._run_git(snapshot, "add", ".")
            self._run_git(snapshot, "commit", "-q", "-m", "base")
            head = self._run_git(snapshot, "rev-parse", "HEAD").stdout.strip()
            # Dirty-tree seeding: the seed stays uncommitted, so HEAD remains the pin.
            document.write_text("batch limit: <=30 files\n", encoding="utf-8")
            patch = base / "seeds.patch"
            patch.write_text(self._run_git(snapshot, "diff").stdout, encoding="utf-8")

            request = self._request(
                base, business_root=snapshot.resolve(), cases=[self._business_case(target_pin=head)]
            )
            host_adapter.validate_request(request, "claude", seed_patch=patch, dry_run=False)

            seeded = host_adapter.seed_patch_paths(snapshot, patch)
            self.assertEqual(seeded, ["docs/features/feature-A/spec/be/spec-backend.md"])
            self.assertEqual(host_adapter.snapshot_status_paths(snapshot), seeded)
            self.assertEqual(
                host_adapter.snapshot_mismatch_errors(seeded, host_adapter.snapshot_status_paths(snapshot)), []
            )
            extra_document = snapshot / "docs/extra.md"
            extra_document.write_text("extra\n", encoding="utf-8")
            self.assertIn(
                "beyond the seed patch",
                " ".join(host_adapter.snapshot_mismatch_errors(seeded, host_adapter.snapshot_status_paths(snapshot))),
            )
            extra_document.unlink()

            stale = self._request(
                base, business_root=snapshot.resolve(), cases=[self._business_case(target_pin="b" * 40)]
            )
            with self.assertRaisesRegex(ValueError, "does not match target_pin"):
                host_adapter.validate_request(stale, "claude", seed_patch=patch, dry_run=False)

            document.write_text("batch limit: <=50 files\n", encoding="utf-8")  # patch no longer applied
            with self.assertRaisesRegex(ValueError, "not cleanly applied"):
                host_adapter.validate_request(request, "claude", seed_patch=patch, dry_run=False)

    def test_snapshot_mismatch_and_status_path_parsing_contracts(self) -> None:
        self.assertEqual(host_adapter.snapshot_mismatch_errors(["a.md"], ["a.md"]), [])
        missing = host_adapter.snapshot_mismatch_errors(["a.md"], [])
        self.assertEqual(len(missing), 1)
        self.assertIn("no longer show as changed", missing[0])
        self.assertIn("a.md", missing[0])
        extra = host_adapter.snapshot_mismatch_errors([], ["b.md"])
        self.assertEqual(len(extra), 1)
        self.assertIn("beyond the seed patch", extra[0])
        self.assertEqual(len(host_adapter.snapshot_mismatch_errors(["a.md"], ["b.md"])), 2)

        # `git status --porcelain -z` emits a rename's source path as one extra NUL-separated
        # field; the parser consumes it, so the source never surfaces as a changed path.
        document = "R  docs/renamed.md\0docs/original.md\0 M docs/changed.md\0?? docs/new.md\0"
        self.assertEqual(
            host_adapter.parse_status_paths(document),
            ["docs/changed.md", "docs/new.md", "docs/renamed.md"],
        )
        worktree_rename = " R docs/worktree-renamed.md\0docs/worktree-original.md\0"
        self.assertEqual(
            host_adapter.parse_status_paths(worktree_rename), ["docs/worktree-renamed.md"]
        )

    def test_dry_run_document_shows_business_inputs_and_public_document_stays_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            workspace, _, snapshot = self._layout(base)
            business_root = snapshot.resolve()
            request = self._request(base, business_root=business_root)
            resolved_workspace, cases = host_adapter.validate_request(request, "claude", dry_run=True)
            patch = base / "seeds.patch"
            document = host_adapter.dry_run_document(
                request, cases, resolved_workspace, "claude", business_root, patch
            )
            self.assertEqual(document["business_root"], str(business_root))
            self.assertEqual(document["seed_patch"], str(patch))
            self.assertEqual(
                document["skipped_checks"],
                [
                    "snapshot HEAD equals target_pin",
                    "seed patch applies cleanly in reverse (git apply --check --reverse)",
                    "snapshot file set equals the seed patch file set after each host call",
                    "snapshot git diff digest equals the seeded state after each host call",
                ],
            )
            self.assertEqual(document["invocation_count"], 3)
            entry = document["cases"][0]
            self.assertEqual(entry["target_docs"], ["docs/features/feature-A/spec/be/spec-backend.md"])
            self.assertEqual(entry["findings_pattern"], "findings/{case_id}/rep-{rep}/findings.json")
            self.assertEqual(
                entry["findings_directory"],
                str(host_adapter.findings_directory(resolved_workspace, "BT-TEST")),
            )
            self.assertIn(str(business_root), entry["prompt"])
            self.assertIn("Business review task:", entry["prompt"])

            public_case = json.loads((ROOT / "evals" / "public" / "AF-001.json").read_text(encoding="utf-8"))
            public_request = self._request(base, cases=[public_case])
            public_workspace, public_cases = host_adapter.validate_request(public_request, "claude", dry_run=True)
            public_document = host_adapter.dry_run_document(public_request, public_cases, public_workspace, "claude")
            self.assertNotIn("business_root", public_document)
            self.assertNotIn("seed_patch", public_document)
            self.assertNotIn("skipped_checks", public_document)
            self.assertEqual(set(public_document["cases"][0]), {"case_id", "repeat_count", "input_ref"})

    def test_grading_overwrites_host_self_reports_and_records_evidence(self) -> None:
        case = json.loads((ROOT / "evals" / "business" / "BT-001.json").read_text(encoding="utf-8"))
        seeds = json.loads(
            (ROOT / "evals" / "business" / "seeds" / "BT-001.seeds.json").read_text(encoding="utf-8")
        )
        hits = [
            {
                "path": seed["doc_ref"],
                "issue": "seeded defect",
                "evidence": f"quote containing {seed['strategy']['anchors'][0]}",
            }
            for seed in seeds["seeds"]
        ]
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            directory = host_adapter.findings_directory(workspace, case["case_id"])
            for rep, findings in ((1, hits), (2, [])):
                rep_dir = directory / f"rep-{rep}"
                rep_dir.mkdir(parents=True)
                (rep_dir / "findings.json").write_text(
                    json.dumps({"schema_version": 1, "case_id": case["case_id"], "findings": findings}),
                    encoding="utf-8",
                )
            repetitions = [
                {"accepted": False, "first_pass_review": False, "escaped_defects": 99, "evidence_refs": ["host://rep-1"]},
                {"accepted": True, "first_pass_review": True, "escaped_defects": 0, "evidence_refs": ["host://rep-2"]},
            ]
            document = host_adapter.grade_case_findings(ROOT, workspace, case, repetitions)
            self.assertTrue((directory / "grading.json").is_file())
        self.assertEqual(document["summary"], {"reps_graded": 2, "reps_failed": 0, "total_seeds": 3})
        self.assertTrue(repetitions[0]["accepted"])
        self.assertEqual(repetitions[0]["escaped_defects"], 0)
        self.assertIn("grading://BT-001/rep-1", repetitions[0]["evidence_refs"])
        self.assertFalse(repetitions[1]["accepted"])
        self.assertEqual(repetitions[1]["escaped_defects"], 3)
        self.assertIn("grading://BT-001/rep-2", repetitions[1]["evidence_refs"])

    def test_grade_case_findings_rejects_unrequested_repetitions(self) -> None:
        # F2 regression: the grader's covered repetition set must equal the run's repetition
        # set exactly. When an extra rep-<n> directory makes it a strict superset, the call
        # must fail closed instead of returning the document, because a returned document
        # would let the caller report the host's self-reported accepted/escaped_defects as a
        # scored success.
        case = json.loads((ROOT / "evals" / "business" / "BT-001.json").read_text(encoding="utf-8"))
        seeds = json.loads(
            (ROOT / "evals" / "business" / "seeds" / "BT-001.seeds.json").read_text(encoding="utf-8")
        )
        hits = [
            {
                "path": seed["doc_ref"],
                "issue": "seeded defect",
                "evidence": f"quote containing {seed['strategy']['anchors'][0]}",
            }
            for seed in seeds["seeds"]
        ]
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            directory = host_adapter.findings_directory(workspace, case["case_id"])
            for rep in (1, 2, 3):
                rep_dir = directory / f"rep-{rep}"
                rep_dir.mkdir(parents=True)
                (rep_dir / "findings.json").write_text(
                    json.dumps({"schema_version": 1, "case_id": case["case_id"], "findings": hits}),
                    encoding="utf-8",
                )
            repetitions = [
                {
                    "accepted": False,
                    "first_pass_review": False,
                    "escaped_defects": 99,
                    "evidence_refs": [f"host://rep-{rep}"],
                }
                for rep in (1, 2)
            ]
            with self.assertRaisesRegex(ValueError, r"unrequested repetitions \[3\]"):
                host_adapter.grade_case_findings(ROOT, workspace, case, repetitions)
            self.assertTrue((directory / "grading.json").is_file())
        # The fail-closed path leaves the host's raw values untouched: no repetition may
        # look graded when the grader did not cover it.
        self.assertFalse(repetitions[0]["accepted"])
        self.assertEqual(repetitions[0]["escaped_defects"], 99)
        self.assertEqual(repetitions[0]["evidence_refs"], ["host://rep-1"])
        self.assertFalse(repetitions[1]["accepted"])
        self.assertEqual(repetitions[1]["escaped_defects"], 99)

    @staticmethod
    def _business_case(**overrides: Any) -> dict[str, Any]:
        case: dict[str, Any] = {
            "case_id": "BT-TEST",
            "slice": "business-doc-review",
            "objective": "review the pinned snapshot documents",
            "input_ref": "evals/business/inputs/BT-001.md",
            "holdout": False,
            "repeat_count": 3,
            "target_id": "aiwork-workflow-ai",
            "target_pin": "a" * 40,
            "target_docs": ["docs/features/feature-A/spec/be/spec-backend.md"],
            "seeds_ref": "evals/business/seeds/BT-001.seeds.json",
            "findings_contract": {
                "path_pattern": "findings/{case_id}/rep-{rep}/findings.json",
                "format": "json",
                "required_fields": ["path", "issue", "evidence"],
            },
            "grading": {"min_seed_recall": 0.5},
        }
        case.update(overrides)
        return case

    def _request(
        self,
        base: Path,
        *,
        business_root: Path | None = None,
        profile: str = "workspace-write",
        cases: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "protocol_version": 1,
            "host": "claude",
            "source_kind": "baseline",
            "source_revision": "installed-revision",
            "artifact_digest": "sha256:" + "a" * 64,
            "result_id": "DRY-BUSINESS-TEST",
            "agentflow_version": "0.5.2",
            "suite_revision": "business-suite-test",
            "model": "test-model",
            "permissions_profile": profile,
            "fixture_revision": "business/aiwork-workflow-ai@" + "a" * 40,
            "repository_root": str(ROOT),
            "workspace_root": str(base / "workspace"),
            "holdout_root": str(base / "holdout"),
            "repeat_count": 3,
            "cases": [self._business_case()] if cases is None else cases,
        }
        if business_root is not None:
            request["business_root"] = str(business_root)
        return request

    @staticmethod
    def _layout(base: Path) -> tuple[Path, Path, Path]:
        workspace, holdout, snapshot = base / "workspace", base / "holdout", base / "snapshot"
        for directory in (workspace, holdout, snapshot):
            directory.mkdir()
        return workspace, holdout, snapshot

    @staticmethod
    def _run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )


# U-07 regression: `run_codex` must read the host result file by path. The previous
# implementation called `read_text` on the file object returned by `NamedTemporaryFile`,
# which has no such method, so every real codex run raised AttributeError before the
# structured result was ever parsed.
class HostAdapterCodexResultTests(unittest.TestCase):
    """run_codex reads the `--output-last-message` file by path and fails closed as ValueError."""

    CODEX_STUB = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

arguments = sys.argv[1:]
output_path = Path(arguments[arguments.index("--output-last-message") + 1])
output_path.write_text(
    json.dumps(
        {
            "accepted": True,
            "first_pass_review": True,
            "correction_count": 0,
            "escaped_defects": 0,
            "permission_violations": 0,
            "unnecessary_delegation": False,
            "tool_failures": 0,
            "evidence_refs": ["stub://codex/result"],
        }
    ),
    encoding="utf-8",
)
raise SystemExit(0)
"""

    CODEX_STUB_WITHOUT_RESULT = """#!/usr/bin/env python3
import sys
from pathlib import Path

arguments = sys.argv[1:]
Path(arguments[arguments.index("--output-last-message") + 1]).unlink()
raise SystemExit(0)
"""

    def _stub_codex(self, directory: Path, script: str) -> Path:
        """Write an executable `codex` stub taking `--output-last-message <path>`."""
        stub_directory = directory / "codex-bin"
        stub_directory.mkdir()
        stub = stub_directory / "codex"
        stub.write_text(script, encoding="utf-8")
        stub.chmod(0o755)
        return stub_directory

    def _stub_on_path(self, stub_directory: Path) -> Any:
        return mock.patch.dict(
            os.environ, {"PATH": str(stub_directory) + os.pathsep + os.environ["PATH"]}
        )

    def test_run_codex_reads_the_result_file_by_path(self) -> None:
        # The stub writes the structured result to the path it was handed, like the real
        # CLI, and prints nothing on stdout: a run_codex that reads the NamedTemporaryFile
        # object instead of the path cannot pass this test.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stub_directory = self._stub_codex(base, self.CODEX_STUB)
            workspace = base / "workspace"
            workspace.mkdir()
            request = {"model": "stub-model", "permissions_profile": "read-only"}
            with self._stub_on_path(stub_directory):
                payload = host_adapter.run_codex(
                    request,
                    "stub prompt",
                    workspace,
                    ROOT / "schemas" / "adapter-case-result.schema.json",
                    60,
                )
        self.assertIs(payload["accepted"], True)
        self.assertIs(payload["first_pass_review"], True)
        self.assertEqual(payload["correction_count"], 0)
        self.assertEqual(payload["escaped_defects"], 0)
        self.assertEqual(payload["permission_violations"], 0)
        self.assertIs(payload["unnecessary_delegation"], False)
        self.assertEqual(payload["tool_failures"], 0)
        self.assertEqual(payload["evidence_refs"], ["stub://codex/result"])
        self.assertGreaterEqual(payload["latency_ms"], 0)

    def test_run_codex_missing_result_file_raises_value_error(self) -> None:
        # A host that exits 0 without leaving a result file is a failed invocation; the read
        # failure must surface as ValueError (caught by main), not as an uncaught
        # AttributeError from the temporary file object.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stub_directory = self._stub_codex(base, self.CODEX_STUB_WITHOUT_RESULT)
            workspace = base / "workspace"
            workspace.mkdir()
            request = {"model": "stub-model", "permissions_profile": "read-only"}
            with self._stub_on_path(stub_directory):
                with self.assertRaisesRegex(ValueError, "cannot read the codex result file"):
                    host_adapter.run_codex(
                        request,
                        "stub prompt",
                        workspace,
                        ROOT / "schemas" / "adapter-case-result.schema.json",
                        60,
                    )


# Real incident: claude writes harmless warnings to stderr even on a successful run
# (`[claude-code:unrecognized_model] ... generate_session_title`). run_claude used to take
# stderr first on a non-zero exit, so a failed run reported that warning and dropped the
# error JSON claude writes to stdout — three consecutive diagnoses saw only the warning.
class HostAdapterClaudeFailureDetailTests(unittest.TestCase):
    """run_claude reports the stdout JSON error, not the stderr warning, on a failed run."""

    CLAUDE_STUB = """#!/usr/bin/env python3
import json
import sys

print("[claude-code:unrecognized_model] skipped generate_session_title", file=sys.stderr)
print(json.dumps({"is_error": True, "result": "real failure detail"}))
raise SystemExit(1)
"""

    def test_run_claude_reports_the_stdout_json_error_not_the_stderr_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stub_directory = base / "claude-bin"
            stub_directory.mkdir()
            stub = stub_directory / "claude"
            stub.write_text(self.CLAUDE_STUB, encoding="utf-8")
            stub.chmod(0o755)
            workspace = base / "workspace"
            workspace.mkdir()
            request = {"model": "stub-model", "permissions_profile": "read-only"}
            with mock.patch.dict(
                os.environ, {"PATH": str(stub_directory) + os.pathsep + os.environ["PATH"]}
            ):
                with self.assertRaises(RuntimeError) as raised:
                    host_adapter.run_claude(
                        request,
                        "stub prompt",
                        workspace,
                        ROOT / "schemas" / "adapter-case-result.schema.json",
                        60,
                    )
        message = str(raised.exception)
        self.assertIn("real failure detail", message)
        self.assertNotIn("unrecognized_model", message)


# Real incident: the business smoke invocation could read zero target-document bytes.
# `claude --print --permission-mode acceptEdits` scopes tool file access to the working
# directory (the adapter runs it with cwd=workspace), so every Read of the snapshot was
# answered "permission not granted" and Bash with "only files under <cwd> are permitted",
# while `permission_denials` stayed empty — the block happens in the tool layer, not the
# approval layer. The snapshot root must be named with `--add-dir`.
class HostAdapterClaudeAddDirTests(unittest.TestCase):
    """run_claude passes `--add-dir <business_root>` for a business request, and only there."""

    CLAUDE_STUB = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

Path(__file__).with_name("claude-argv.json").write_text(
    json.dumps(sys.argv[1:]), encoding="utf-8"
)
print(
    json.dumps(
        {
            "accepted": True,
            "first_pass_review": True,
            "correction_count": 0,
            "escaped_defects": 0,
            "permission_violations": 0,
            "unnecessary_delegation": False,
            "tool_failures": 0,
            "latency_ms": 1,
            "evidence_refs": ["stub://claude/add-dir"],
        }
    )
)
raise SystemExit(0)
"""

    def _run_with_stub(
        self, base: Path, name: str, request: dict[str, Any], prompt: str
    ) -> list[str]:
        """Run run_claude against a stub `claude` and return the argv the stub received."""
        stub_directory = base / name / "claude-bin"
        stub_directory.mkdir(parents=True)
        stub = stub_directory / "claude"
        stub.write_text(self.CLAUDE_STUB, encoding="utf-8")
        stub.chmod(0o755)
        workspace = base / name / "workspace"
        workspace.mkdir()
        with mock.patch.dict(
            os.environ, {"PATH": str(stub_directory) + os.pathsep + os.environ["PATH"]}
        ):
            payload = host_adapter.run_claude(
                request,
                prompt,
                workspace,
                ROOT / "schemas" / "adapter-case-result.schema.json",
                60,
            )
        self.assertIs(payload["accepted"], True)
        return json.loads((stub_directory / "claude-argv.json").read_text(encoding="utf-8"))

    def test_business_request_carries_add_dir_before_the_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            snapshot = base / "snapshot"
            snapshot.mkdir()
            business_root = str(snapshot.resolve())
            prompt = "stub prompt"
            request = {
                "model": "stub-model",
                "permissions_profile": "workspace-write",
                "business_root": business_root,
            }
            arguments = self._run_with_stub(base, "business", request, prompt)
        self.assertIn("--add-dir", arguments)
        self.assertEqual(arguments[arguments.index("--add-dir") + 1], business_root)
        self.assertLess(arguments.index("--add-dir"), arguments.index(prompt))

    def test_public_request_carries_no_add_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            request = {"model": "stub-model", "permissions_profile": "read-only"}
            arguments = self._run_with_stub(base, "public", request, "stub prompt")
        self.assertNotIn("--add-dir", arguments)


class ClaudeFailureDetailMatrixTests(unittest.TestCase):
    """claude_failure_detail takes stdout text only from a payload declaring an error.

    Regression for the inverse mistake: the guard used to accept every dict that was not
    ``is_error: false`` without an ``error`` field, so a valid success payload whose
    ``result`` held the model's answer (``is_error: false``, or no ``is_error`` key at all)
    had that answer quoted as the failure detail. The function is tested directly because
    it is pure: no host process or stub is involved, and every branch is reachable with a
    pair of strings.
    """

    def test_explicit_is_error_true_reports_the_result_text(self) -> None:
        stdout = json.dumps({"type": "result", "is_error": True, "result": "model refused the task"})
        self.assertEqual(
            host_adapter.claude_failure_detail(stdout, "[claude-code:unrecognized_model] warning", 1),
            "model refused the task",
        )

    def test_error_object_message_is_reported(self) -> None:
        stdout = json.dumps({"error": {"message": "invalid api key", "type": "authentication_error"}})
        self.assertEqual(
            host_adapter.claude_failure_detail(stdout, "[claude-code:unrecognized_model] warning", 1),
            "invalid api key",
        )

    def test_is_error_false_with_error_field_is_still_an_error(self) -> None:
        # The marker is the OR of the two signals: a payload that carries an error field is
        # an error report even when its is_error flag says otherwise.
        stdout = json.dumps({"is_error": False, "error": {"message": "stream disconnected"}})
        self.assertEqual(
            host_adapter.claude_failure_detail(stdout, "warning noise", 1),
            "stream disconnected",
        )

    def test_is_error_true_with_empty_result_falls_through_to_the_error_field(self) -> None:
        stdout = json.dumps({"is_error": True, "result": "", "error": "quota exhausted"})
        self.assertEqual(
            host_adapter.claude_failure_detail(stdout, "warning noise", 1),
            "quota exhausted",
        )

    def test_is_error_false_with_result_is_not_reported(self) -> None:
        # The false-positive case: a successful payload must not have its result text used,
        # even though the process exited non-zero for some other reason.
        stdout = json.dumps({"is_error": False, "result": "a perfectly good model answer"})
        detail = host_adapter.claude_failure_detail(stdout, "process killed by signal 9", 137)
        self.assertEqual(detail, "process killed by signal 9")
        self.assertNotIn("perfectly good", detail)

    def test_valid_payload_without_is_error_key_is_not_reported(self) -> None:
        # Same false positive with no is_error key at all: absence of the flag is not an
        # error declaration, so the result text must stay out of the diagnostic.
        stdout = json.dumps({"type": "result", "subtype": "success", "result": "the model answer"})
        detail = host_adapter.claude_failure_detail(stdout, "exit hook failed", 1)
        self.assertEqual(detail, "exit hook failed")
        self.assertNotIn("the model answer", detail)

    def test_non_dict_json_is_not_reported(self) -> None:
        stdout = json.dumps(["not", "an", "object"])
        self.assertEqual(
            host_adapter.claude_failure_detail(stdout, "stderr diagnostic", 1),
            "stderr diagnostic",
        )

    def test_non_json_stdout_falls_back_to_stderr(self) -> None:
        self.assertEqual(
            host_adapter.claude_failure_detail("not json at all", "diagnostic on stderr", 1),
            "diagnostic on stderr",
        )

    def test_non_json_stdout_with_empty_stderr_keeps_the_raw_stdout(self) -> None:
        self.assertEqual(
            host_adapter.claude_failure_detail("raw failure text", "", 1),
            "raw failure text",
        )

    def test_empty_streams_fall_back_to_the_exit_code(self) -> None:
        self.assertEqual(
            host_adapter.claude_failure_detail("", "   \n", 137),
            "claude exited with 137",
        )

    def test_json_payload_without_usable_text_falls_back_to_the_raw_stdout(self) -> None:
        # An error payload whose only text field is blank yields no detail; the fallback
        # then keeps the raw stdout text, as it did before the guard was tightened.
        stdout = json.dumps({"is_error": True, "result": "   "})
        self.assertEqual(host_adapter.claude_failure_detail(stdout, "", 1), stdout)

    def test_long_stdout_detail_is_truncated_to_2000_characters(self) -> None:
        stdout = json.dumps({"is_error": True, "result": "x" * 2500})
        detail = host_adapter.claude_failure_detail(stdout, "", 1)
        self.assertEqual(len(detail), 2000)
        self.assertEqual(detail, "x" * 2000)

    def test_long_stderr_fallback_is_truncated_to_2000_characters(self) -> None:
        detail = host_adapter.claude_failure_detail("", "e" * 2500, 1)
        self.assertEqual(len(detail), 2000)
        self.assertEqual(detail, "e" * 2000)


class StructuredReadFailureTests(unittest.TestCase):
    """load_json / read_document_text map OS and encoding failures to ValidationError.

    UnicodeDecodeError is a ValueError, not an OSError: before this was covered, a non-UTF-8
    JSON file (or a missing AGENTS.md) escaped the gate as a bare traceback instead of a
    structured ValidationError naming the path.
    """

    def test_load_json_reports_unreadable_files_as_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            _, missing_errors = validate.load_json(base / "missing.json")
            bad_encoding = base / "bad-encoding.json"
            bad_encoding.write_bytes(b'{ "case_id": "\xff\xfe" }')
            document, bad_errors = validate.load_json(bad_encoding)
        self.assertIsNone(document)
        self.assertTrue(missing_errors, "a missing file must produce a structured error")
        self.assertIn("invalid JSON", missing_errors[0].message)
        self.assertTrue(bad_errors, "a bad-encoding file must produce a structured error")
        self.assertIn("invalid JSON", bad_errors[0].message)
        self.assertIn("utf-8", bad_errors[0].message)

    def test_read_document_text_reports_missing_and_bad_encoding_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            _, missing_errors = validate.read_document_text(base / "AGENTS.md")
            bad = base / "latin1.md"
            bad.write_bytes(b"caf\xe9 latin-1 text")  # a lone \xe9 byte is invalid UTF-8
            _, bad_errors = validate.read_document_text(bad)
        self.assertEqual(len(missing_errors), 1)
        self.assertIn("cannot read document", missing_errors[0].message)
        self.assertIn("AGENTS.md", missing_errors[0].path)
        self.assertEqual(len(bad_errors), 1)
        self.assertIn("cannot read document", bad_errors[0].message)

    def test_missing_agents_md_is_a_structured_error_not_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            errors = validate.validate_agents_md_plan_contract(Path(temporary) / "AGENTS.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("cannot read document", errors[0].message)


class NegativeExampleDeclarationTests(unittest.TestCase):
    """examples/invalid is declarative now: every file must be a declared INVALID_EXAMPLES key.

    The directory used to be classified by filename prefix (case-sensitive for bug records,
    case-insensitive for plans), so a misspelled negative example was silently skipped and never
    exercised its gate. The consistency assertion fires when a file appears in the directory
    without being declared (or a declared entry goes missing), and validate_examples() reports
    the undeclared path and runs each declared negative through its validator.
    """

    def test_the_declared_list_matches_the_directory_exactly(self) -> None:
        present = {
            path.name
            for path in (ROOT / "examples" / "invalid").iterdir()
            if not path.name.startswith(".")
        }
        self.assertEqual(set(validate.INVALID_EXAMPLES), present)

    def test_every_declared_negative_is_rejected_by_its_validator(self) -> None:
        for name, (kind, check) in validate.INVALID_EXAMPLES.items():
            with self.subTest(example=name):
                errors = check(ROOT / "examples" / "invalid" / name)
                self.assertTrue(errors, f"{name} ({kind}) must be rejected by its validator")


class PolicyDecisionTests(unittest.TestCase):
    """policy.decide's full matrix: every decision path, both metric directions, tolerances,
    guardrail and slice regressions, the invalid class, bad candidate records, and exit codes.

    The fixtures are plain dicts built in-process; the end-to-end main() cases use the shipped
    example documents (schema-valid by construction). policy.py itself is unchanged.
    """

    DIGEST_BASE = "sha256:" + "a" * 64
    DIGEST_CANDIDATE = "sha256:" + "b" * 64
    DIGEST_OTHER = "sha256:" + "c" * 64

    def _rep(
        self,
        accepted: bool = True,
        first_pass: bool = True,
        corrections: int = 0,
        escaped: int = 0,
    ) -> dict[str, Any]:
        return {
            "accepted": accepted,
            "first_pass_review": first_pass,
            "correction_count": corrections,
            "escaped_defects": escaped,
            "permission_violations": 0,
            "unnecessary_delegation": False,
            "tool_failures": 0,
            "latency_ms": 90.0,
            "evidence_refs": ["result://test/rep"],
        }

    def _summary(self, **overrides: Any) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "acceptance_rate": 1.0,
            "first_pass_review_rate": 1.0,
            "correction_count": 0,
            "escaped_defects": 0,
            "permission_violations": 0,
            "unnecessary_delegation_count": 0,
            "tool_failures": 0,
            "latency_ms": 90.0,
        }
        summary.update(overrides)
        return summary

    def _case(
        self,
        case_id: str = "AF-001",
        slice_name: str = "role-selection",
        reps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "case_id": case_id,
            "slice": slice_name,
            "holdout": False,
            "protected_guardrails": ["permission_violations", "escaped_defects"],
            "repetitions": reps if reps is not None else [self._rep(), self._rep()],
        }

    def _result(self, source_kind: str, digest: str, version: str, source_revision: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "result_id": f"{source_kind}-test",
            "source_kind": source_kind,
            "source_revision": source_revision,
            "artifact_digest": digest,
            "agentflow_version": version,
            "suite_revision": "suite-1",
            "host": "codex",
            "model": "test-model",
            "permissions_profile": "read-write-workspace",
            "fixture_revision": "fixture-1",
            "repeat_count": 2,
            "suite_case_count": 1,
            "observed_context": {
                "host": "codex",
                "model": "test-model",
                "permissions_profile": "read-write-workspace",
                "fixture_revision": "fixture-1",
                "evidence_refs": ["context://test"],
            },
            "case_results": [self._case()],
            "summary": self._summary(),
            "generated_at": "2026-01-01T00:00:00Z",
        }

    def _baseline(self, **overrides: Any) -> dict[str, Any]:
        result = self._result("baseline", self.DIGEST_BASE, "0.3.1", "baseline-rev")
        result["case_results"] = [
            self._case(reps=[self._rep(), self._rep(accepted=False, first_pass=False, corrections=2)])
        ]
        result["summary"] = self._summary(acceptance_rate=0.5, first_pass_review_rate=0.5, correction_count=2)
        result.update(overrides)
        return result

    def _candidate(self, **overrides: Any) -> dict[str, Any]:
        result = self._result("candidate", self.DIGEST_CANDIDATE, "0.3.2-rc.1", "candidate-rev")
        result.update(overrides)
        return result

    def _record(self, **overrides: Any) -> dict[str, Any]:
        record: dict[str, Any] = {
            "schema_version": 1,
            "candidate_version": "0.3.2-rc.1",
            "parent_version": "0.3.1",
            "source_revision": "candidate-rev",
            "artifact_digest": self.DIGEST_CANDIDATE,
            "hypothesis": "test hypothesis",
            "evidence_ids": ["E-TEST-001"],
            "changed_components": ["skills/agentflow/SKILL.md"],
            "risk_class": "low",
            "evaluation_suite_revision": "suite-1",
            "primary_metrics": ["acceptance_rate"],
            "guardrails": ["escaped_defects"],
            "rejection_criteria": ["any guardrail regression"],
            "protected_slices": ["role-selection"],
        }
        record.update(overrides)
        return record

    @staticmethod
    def _policy(**tolerances: float) -> dict[str, Any]:
        return {"guardrail_tolerances": dict(tolerances)}

    def test_promote_when_a_primary_metric_improves_and_guardrails_hold(self) -> None:
        decision = policy.decide(self._record(), self._baseline(), self._candidate(), self._policy())
        self.assertEqual(decision["decision"], "promote")
        self.assertEqual(decision["evaluation_result"], "better")
        self.assertTrue(decision["required_human_approval"])
        self.assertEqual(decision["rollback_target"], "0.3.1")
        self.assertIn(
            "all declared primary metrics are non-regressing and at least one improved",
            decision["reasons"],
        )
        self.assertEqual(decision["metrics"]["acceptance_rate"]["direction"], "improved")
        self.assertEqual(decision["metrics"]["escaped_defects"]["direction"], "unchanged")
        self.assertEqual(
            decision["protected_slice_metrics"]["role-selection"]["acceptance_rate"]["direction"],
            "improved",
        )

    def test_revise_when_no_primary_metric_improves(self) -> None:
        flat_reps = [self._rep(), self._rep(accepted=False, first_pass=False, corrections=2)]
        candidate = self._candidate(
            summary=self._summary(acceptance_rate=0.5, first_pass_review_rate=0.5, correction_count=2),
            case_results=[self._case(reps=flat_reps)],
        )
        decision = policy.decide(self._record(), self._baseline(), candidate, self._policy())
        self.assertEqual(decision["decision"], "revise")
        self.assertEqual(decision["evaluation_result"], "neutral")
        self.assertIn("no declared primary metric improved", decision["reasons"])

    def test_reject_when_a_primary_metric_regresses(self) -> None:
        candidate = self._candidate(
            summary=self._summary(acceptance_rate=0.0, first_pass_review_rate=0.0),
            case_results=[
                self._case(
                    reps=[
                        self._rep(accepted=False, first_pass=False),
                        self._rep(accepted=False, first_pass=False),
                    ]
                )
            ],
        )
        decision = policy.decide(self._record(), self._baseline(), candidate, self._policy())
        self.assertEqual(decision["decision"], "reject")
        self.assertEqual(decision["evaluation_result"], "worse")

    def test_compare_direction_covers_both_metric_directions(self) -> None:
        self.assertEqual(policy.compare_direction("acceptance_rate", 0.5, 0.75), "improved")
        self.assertEqual(policy.compare_direction("acceptance_rate", 0.5, 0.25), "regressed")
        self.assertEqual(policy.compare_direction("acceptance_rate", 0.5, 0.5), "unchanged")
        self.assertEqual(policy.compare_direction("escaped_defects", 2, 1), "improved")
        self.assertEqual(policy.compare_direction("escaped_defects", 2, 3), "regressed")
        self.assertEqual(policy.compare_direction("escaped_defects", 2, 2), "unchanged")

    def test_invalid_identity_mismatches_reject_with_named_reasons(self) -> None:
        cases = (
            ("baseline source_kind", lambda b, c, r: b.update(source_kind="candidate"), "baseline result must have source_kind=baseline"),
            ("candidate source_kind", lambda b, c, r: c.update(source_kind="baseline"), "candidate result must have source_kind=candidate"),
            ("candidate source_revision", lambda b, c, r: c.update(source_revision="other-rev"), "candidate result source_revision does not match candidate record"),
            ("candidate artifact_digest", lambda b, c, r: c.update(artifact_digest=self.DIGEST_OTHER), "candidate result artifact_digest does not match candidate record"),
            ("identical artifact digests", lambda b, c, r: b.update(artifact_digest=self.DIGEST_CANDIDATE), "candidate artifact_digest must differ from the baseline artifact"),
            ("candidate version", lambda b, c, r: c.update(agentflow_version="9.9.9"), "candidate result agentflow_version does not match candidate version"),
            ("baseline parent version", lambda b, c, r: b.update(agentflow_version="9.9.9"), "baseline result agentflow_version does not match candidate parent version"),
            ("suite revision", lambda b, c, r: c.update(suite_revision="suite-2"), "candidate result suite_revision does not match candidate record"),
            ("host mismatch", lambda b, c, r: b.update(host="claude"), "baseline and candidate host must match"),
            ("observed_context model mismatch", lambda b, c, r: b["observed_context"].update(model="other-model"), "baseline and candidate observed_context.model must match"),
            ("case coverage mismatch", lambda b, c, r: c["case_results"][0].update(case_id="AF-009"), "baseline and candidate case/slice coverage must match"),
        )
        for label, mutate, reason in cases:
            with self.subTest(case=label):
                baseline, candidate, record = self._baseline(), self._candidate(), self._record()
                mutate(baseline, candidate, record)
                decision = policy.decide(record, baseline, candidate, self._policy())
                self.assertEqual(decision["decision"], "reject", decision["reasons"])
                self.assertEqual(decision["evaluation_result"], "invalid")
                self.assertIn(reason, decision["reasons"])

    def test_unknown_declared_metric_fails_closed(self) -> None:
        # Current fail-closed behavior, pinned as-is (policy.py is not modified in this batch):
        # the top-level metric loop records the unknown metric as invalid, but the protected
        # slice loop then indexes the summarize() metric table with the unknown name and
        # decide() raises KeyError; main() catches it and exits 1 with "FAIL policy evaluation".
        with self.assertRaises(KeyError):
            policy.decide(
                self._record(primary_metrics=["made_up_rate"]),
                self._baseline(),
                self._candidate(),
                self._policy(),
            )
        # The same wrong record through the CLI is a structured, non-zero rejection.
        with tempfile.TemporaryDirectory() as temporary:
            record = self._record(primary_metrics=["made_up_rate"])
            record_path = Path(temporary) / "record.json"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = policy.main(
                    [
                        "--candidate-record",
                        str(record_path),
                        "--baseline-result",
                        str(ROOT / "examples" / "evaluation-results" / "baseline.json"),
                        "--candidate-result",
                        str(ROOT / "examples" / "evaluation-results" / "candidate.json"),
                    ]
                )
        self.assertEqual(code, 1)
        self.assertIn("FAIL policy evaluation", standard_error.getvalue())
        self.assertIn("made_up_rate", standard_error.getvalue())

    def test_missing_or_non_numeric_metric_is_rejected(self) -> None:
        summary = self._summary()
        del summary["acceptance_rate"]
        decision = policy.decide(
            self._record(), self._baseline(), self._candidate(summary=summary), self._policy()
        )
        self.assertEqual(decision["decision"], "reject")
        self.assertEqual(decision["evaluation_result"], "invalid")
        self.assertIn("metric 'acceptance_rate' is missing or non-numeric", decision["reasons"])

    def test_lower_is_better_guardrail_tolerance_boundary(self) -> None:
        record = self._record(guardrails=["escaped_defects"])
        # Exactly at the tolerance (candidate > baseline + tolerance must be false): no failure.
        at_tolerance = self._candidate(
            summary=self._summary(escaped_defects=1),
            case_results=[self._case(reps=[self._rep(escaped=1), self._rep()])],
        )
        decision = policy.decide(record, self._baseline(), at_tolerance, self._policy(escaped_defects=1))
        self.assertEqual(decision["decision"], "promote")
        # Beyond the tolerance: guardrail failure rejects with the metric named.
        beyond = self._candidate(
            summary=self._summary(escaped_defects=2),
            case_results=[self._case(reps=[self._rep(escaped=2), self._rep()])],
        )
        decision = policy.decide(record, self._baseline(), beyond, self._policy(escaped_defects=1))
        self.assertEqual(decision["decision"], "reject")
        self.assertEqual(decision["evaluation_result"], "worse")
        self.assertIn("guardrails regressed: escaped_defects", decision["reasons"])
        # Default zero tolerance fails closed on any regression.
        decision = policy.decide(record, self._baseline(), at_tolerance, self._policy())
        self.assertEqual(decision["decision"], "reject")
        self.assertIn("guardrails regressed: escaped_defects", decision["reasons"])

    def test_higher_is_better_guardrail_tolerance_boundary(self) -> None:
        record = self._record(primary_metrics=["correction_count"], guardrails=["first_pass_review_rate"])
        baseline = self._baseline(
            repeat_count=4,
            case_results=[
                self._case(
                    reps=[
                        self._rep(corrections=4),
                        self._rep(),
                        self._rep(accepted=False, first_pass=False),
                        self._rep(accepted=False, first_pass=False),
                    ]
                )
            ],
            summary=self._summary(acceptance_rate=0.5, first_pass_review_rate=0.5, correction_count=4),
        )
        # 0.25 < 0.5 - 0.25 must be false: the boundary itself does not regress.
        at_tolerance = self._candidate(
            repeat_count=4,
            case_results=[
                self._case(
                    reps=[
                        self._rep(),
                        self._rep(accepted=False, first_pass=False),
                        self._rep(accepted=False, first_pass=False),
                        self._rep(accepted=False, first_pass=False),
                    ]
                )
            ],
            summary=self._summary(acceptance_rate=0.25, first_pass_review_rate=0.25, correction_count=0),
        )
        decision = policy.decide(record, baseline, at_tolerance, self._policy(first_pass_review_rate=0.25))
        self.assertEqual(decision["decision"], "promote")
        decision = policy.decide(record, baseline, at_tolerance, self._policy())
        self.assertEqual(decision["decision"], "reject")
        self.assertEqual(decision["evaluation_result"], "worse")
        self.assertIn("guardrails regressed: first_pass_review_rate", decision["reasons"])

    def test_protected_slice_regression_is_named_per_slice(self) -> None:
        candidate = self._candidate(
            summary=self._summary(escaped_defects=1),
            case_results=[self._case(reps=[self._rep(escaped=1), self._rep()])],
        )
        decision = policy.decide(self._record(), self._baseline(), candidate, self._policy())
        self.assertEqual(decision["decision"], "reject")
        self.assertEqual(decision["evaluation_result"], "worse")
        self.assertIn("guardrails regressed: escaped_defects", decision["reasons"])
        self.assertIn("protected slice regressions: role-selection:escaped_defects", decision["reasons"])

    def test_protected_slices_default_to_every_declared_slice(self) -> None:
        decision = policy.decide(
            self._record(protected_slices=[]), self._baseline(), self._candidate(), self._policy()
        )
        self.assertEqual(decision["decision"], "promote")
        self.assertIn("role-selection", decision["protected_slice_metrics"])

    def test_missing_protected_slice_is_invalid(self) -> None:
        decision = policy.decide(
            self._record(protected_slices=["ghost-slice"]), self._baseline(), self._candidate(), self._policy()
        )
        self.assertEqual(decision["decision"], "reject")
        self.assertEqual(decision["evaluation_result"], "invalid")
        self.assertIn(
            "protected slice 'ghost-slice' is missing from baseline or candidate", decision["reasons"]
        )

    def test_load_policy_defaults_to_zero_tolerances_for_every_known_metric(self) -> None:
        loaded = policy.load_policy(None)
        self.assertEqual(set(loaded["guardrail_tolerances"]), set(policy.KNOWN_METRICS))
        self.assertTrue(all(value == 0 for value in loaded["guardrail_tolerances"].values()))

    def test_load_policy_reads_tolerances_and_validates_the_document(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.json"
            path.write_text(json.dumps({"guardrail_tolerances": {"escaped_defects": 2}}), encoding="utf-8")
            loaded = policy.load_policy(str(path))
            self.assertEqual(loaded["guardrail_tolerances"]["escaped_defects"], 2)
            self.assertEqual(loaded["guardrail_tolerances"]["tool_failures"], 0)

            path.write_text(json.dumps({"guardrail_tolerances": {"made_up_metric": 1}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid guardrail tolerance"):
                policy.load_policy(str(path))
            path.write_text(json.dumps({"guardrail_tolerances": {"escaped_defects": -1}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid guardrail tolerance"):
                policy.load_policy(str(path))
            path.write_text(json.dumps([]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "policy must be a JSON object"):
                policy.load_policy(str(path))
            path.write_text(json.dumps({"guardrail_tolerances": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "guardrail_tolerances must be an object"):
                policy.load_policy(str(path))
            broken = Path(temporary) / "broken.json"
            broken.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                policy.load_policy(str(broken))

    def test_load_candidate_rejects_missing_malformed_and_schema_invalid_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            document, errors = policy.load_candidate(str(base / "missing.json"))
            self.assertIsNone(document)
            self.assertTrue(errors and "invalid JSON" in errors[0].message)

            array_path = base / "array.json"
            array_path.write_text("[]", encoding="utf-8")
            document, errors = policy.load_candidate(str(array_path))
            self.assertIsNone(document)
            self.assertIn("candidate must be a JSON object", errors[0].message)

            record = json.loads(
                (ROOT / "examples" / "policy" / "candidate-record.json").read_text(encoding="utf-8")
            )
            record.pop("candidate_version")
            invalid_path = base / "schema-invalid.json"
            invalid_path.write_text(json.dumps(record), encoding="utf-8")
            document, errors = policy.load_candidate(str(invalid_path))
            # load_candidate returns the parsed document alongside the schema errors; the
            # errors themselves are what make main() fail.
            self.assertIsNotNone(document)
            self.assertTrue(
                any("candidate_version" in f"{error.path} {error.message}" for error in errors),
                [str(error) for error in errors],
            )

        document, errors = policy.load_candidate(str(ROOT / "examples" / "policy" / "candidate-record.json"))
        self.assertIsNotNone(document)
        self.assertEqual(errors, [])

    def _main_arguments(self, **overrides: str) -> list[str]:
        arguments = {
            "candidate_record": str(ROOT / "examples" / "policy" / "candidate-record.json"),
            "baseline_result": str(ROOT / "examples" / "evaluation-results" / "baseline.json"),
            "candidate_result": str(ROOT / "examples" / "evaluation-results" / "candidate.json"),
        }
        arguments.update(overrides)
        flat: list[str] = []
        for flag, value in arguments.items():
            flat += [f"--{flag.replace('_', '-')}", value]
        return flat

    def test_main_promotes_the_shipped_example_trio_and_writes_the_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "decision.json"
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = policy.main([*self._main_arguments(output=str(output))])
            self.assertEqual(code, 0, standard_error.getvalue())
            self.assertTrue(output.is_file())
            decision = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(decision["decision"], "promote")
        self.assertTrue(decision["required_human_approval"])
        self.assertIn("WROTE", standard_out.getvalue())

    def test_main_prints_the_decision_and_exits_zero_without_output_path(self) -> None:
        standard_out, standard_error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
            code = policy.main(self._main_arguments())
        self.assertEqual(code, 0, standard_error.getvalue())
        self.assertEqual(json.loads(standard_out.getvalue())["decision"], "promote")

    def test_main_reports_broken_inputs_with_exit_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            broken = Path(temporary) / "candidate.json"
            broken.write_text("{not json", encoding="utf-8")
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = policy.main(self._main_arguments(candidate_record=str(broken)))
        self.assertEqual(code, 1)
        self.assertEqual(standard_out.getvalue(), "")
        self.assertIn("FAIL policy inputs", standard_error.getvalue())

    def test_main_reports_a_bad_policy_with_exit_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bad_policy = Path(temporary) / "policy.json"
            bad_policy.write_text(json.dumps({"guardrail_tolerances": {"made_up_metric": 1}}), encoding="utf-8")
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = policy.main(self._main_arguments(policy=str(bad_policy)))
        self.assertEqual(code, 1)
        self.assertIn("FAIL policy evaluation", standard_error.getvalue())


class CheckDiffGateTests(unittest.TestCase):
    """check_diff's protected-prefix block: the enforcement end of the candidate gate.

    check_diff reads protected-paths.txt from the real repository root (isolation.py hardwires
    that path), so the fixture candidate touches a path under a declared prefix
    (`tools/lab/validate.py`) inside a throwaway git repository. The real tree is never written to.
    """

    def _candidate_repo(self, base: Path) -> tuple[Path, str]:
        candidate = base / "candidate"
        candidate.mkdir()
        self._git(candidate, "init", "-q")
        self._git(candidate, "config", "user.email", "test@example.com")
        self._git(candidate, "config", "user.name", "Agentflow Tests")
        (candidate / "tools" / "lab").mkdir(parents=True)
        (candidate / "tools" / "lab" / "validate.py").write_text("base\n", encoding="utf-8")
        (candidate / "docs").mkdir()
        (candidate / "docs" / "notes.txt").write_text("base\n", encoding="utf-8")
        self._git(candidate, "add", ".")
        self._git(candidate, "commit", "-q", "-m", "base")
        head = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return candidate, head

    def test_touching_a_protected_path_is_blocked_and_named(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate, head = self._candidate_repo(Path(temporary))
            (candidate / "tools" / "lab" / "validate.py").write_text("candidate edit\n", encoding="utf-8")
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = isolation.check_diff(argparse.Namespace(candidate=str(candidate), base=head))
            result = json.loads(standard_out.getvalue())
        self.assertEqual(code, 1)
        self.assertIn("tools/lab/validate.py", result["blocked"])
        self.assertIn("candidate changed a forbidden path", standard_error.getvalue())

    def test_untracked_new_file_under_a_protected_prefix_is_blocked_too(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate, head = self._candidate_repo(Path(temporary))
            # `schemas/` is a protected directory prefix; a brand-new untracked file under it
            # must be blocked exactly like a modification of an enumerated protected file.
            (candidate / "schemas").mkdir()
            (candidate / "schemas" / "evil.json").write_text("{}\n", encoding="utf-8")
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = isolation.check_diff(argparse.Namespace(candidate=str(candidate), base=head))
            result = json.loads(standard_out.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["blocked"], ["schemas/evil.json"])
        self.assertIn("candidate changed a forbidden path", standard_error.getvalue())

    def test_only_unprotected_changes_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate, head = self._candidate_repo(Path(temporary))
            (candidate / "docs" / "notes.txt").write_text("changed\n", encoding="utf-8")
            (candidate / "docs" / "extra.txt").write_text("new\n", encoding="utf-8")
            standard_out, standard_error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(standard_out), contextlib.redirect_stderr(standard_error):
                code = isolation.check_diff(argparse.Namespace(candidate=str(candidate), base=head))
            result = json.loads(standard_out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["blocked"], [])
        self.assertEqual(result["changed_paths"], ["docs/extra.txt", "docs/notes.txt"])

    @staticmethod
    def _git(repository: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )


class GateIntegrityNegativeTests(unittest.TestCase):
    """The gate-integrity checks must fail on mutated fixtures, not only pass on this tree.

    validate_manifests, validate_protected_paths, and validate_unit_tests take an optional
    root/list-path (default = the previous hardwired behavior, so callers are unaffected), so
    the negative paths run in-process against throwaway trees. Nothing here mutates the real
    checkout; the two-parameter functions stay pinned by the full `validate all` run.
    """

    def _write_manifests(self, root: Path, name: str = "agentflow", version: str = "9.9.9") -> None:
        for relative, pointer in validate.MANIFEST_POINTERS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            document = (
                {"plugins": [{"name": name, "version": version}]}
                if pointer
                else {"name": name, "version": version}
            )
            path.write_text(json.dumps(document), encoding="utf-8")

    def test_manifest_version_divergence_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_manifests(root)
            self.assertEqual(validate.validate_manifests(root), [])
            (root / ".codex-plugin" / "plugin.json").write_text(
                json.dumps({"name": "agentflow", "version": "9.9.8"}), encoding="utf-8"
            )
            errors = validate.validate_manifests(root)
        self.assertEqual(len(errors), 1, [str(error) for error in errors])
        self.assertEqual(errors[0].path, ".codex-plugin/plugin.json")
        self.assertIn("disagrees with plugin.json", errors[0].message)

    def test_protected_list_shrinkage_and_missing_list_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            entries = [
                line
                for line in validate.PROTECTED_PATHS_FILE.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            self.assertIn("tools/lab/validate.py", entries)
            complete = base / "complete.txt"
            complete.write_text("\n".join(entries) + "\n", encoding="utf-8")
            self.assertEqual(validate.validate_protected_paths(complete), [])
            shrunken = base / "shrunken.txt"
            shrunken.write_text(
                "\n".join(entry for entry in entries if entry != "tools/lab/validate.py") + "\n",
                encoding="utf-8",
            )
            errors = validate.validate_protected_paths(shrunken)
            missing = validate.validate_protected_paths(base / "absent.txt")
        self.assertTrue(
            any(
                "tools/lab/validate.py" in error.message and "no longer covered" in error.message
                for error in errors
            ),
            [str(error) for error in errors],
        )
        self.assertTrue(any("missing" in error.message for error in missing))

    def test_undeclared_and_missing_test_entries_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors_without_tests = validate.validate_unit_tests(root)
            tests_dir = root / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_lab_contracts.py").write_text("", encoding="utf-8")
            (tests_dir / "test_record_store.py").write_text("", encoding="utf-8")
            (tests_dir / "smuggled_test.py").write_text("", encoding="utf-8")
            undeclared_errors = validate.validate_unit_tests(root)
            for name in ("smuggled_test.py", "test_lab_contracts.py", "test_record_store.py"):
                (tests_dir / name).unlink()
            missing_declared_errors = validate.validate_unit_tests(root)
        self.assertTrue(
            any("the test directory is missing" in error.message for error in errors_without_tests)
        )
        self.assertEqual(
            [f"{error.path} {error.message}" for error in undeclared_errors],
            [
                "tests/smuggled_test.py unexpected entry in the test directory; "
                "declare it here and in protected-paths.txt"
            ],
        )
        self.assertTrue(
            any(
                "tests/test_lab_contracts.py" in error.path and "declared test file is missing" in error.message
                for error in missing_declared_errors
            ),
            [str(error) for error in missing_declared_errors],
        )

    def test_empty_and_trivial_suites_fail_the_count_floor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests_dir = root / "tests"
            tests_dir.mkdir()
            module = tests_dir / "test_lab_contracts.py"
            module.write_text("# no tests here\n", encoding="utf-8")
            (tests_dir / "test_record_store.py").write_text("# no tests here\n", encoding="utf-8")
            empty_errors = validate.validate_unit_tests(root)
            module.write_text(
                "import unittest\n\n\nclass T(unittest.TestCase):\n"
                "    def test_placeholder(self) -> None:\n        pass\n",
                encoding="utf-8",
            )
            trivial_errors = validate.validate_unit_tests(root)
        self.assertEqual(
            [error.message for error in empty_errors],
            ["unit tests ran 0 tests; the regression suite is empty"],
        )
        self.assertEqual(len(trivial_errors), 1, [str(error) for error in trivial_errors])
        self.assertIn(
            f"ran 1 tests, below the required floor of {validate.MIN_UNIT_TEST_COUNT}",
            trivial_errors[0].message,
        )
        self.assertIn("gate change that requires explicit review", trivial_errors[0].message)


class ImprovementArtifactContractTests(unittest.TestCase):
    """records/improvement/: a legal four-artifact set compiles clean and every
    cross-document rule rejects its negative (the improvement loop's handoff plane)."""

    BASELINE_ID = "imp-eval-baseline-001"
    CANDIDATE_ID = "imp-eval-candidate-001"
    CANDIDATE_VERSION = "0.3.2-rc.1"
    METRICS = (
        "acceptance_rate",
        "first_pass_review_rate",
        "correction_count",
        "escaped_defects",
        "permission_violations",
        "unnecessary_delegation_count",
        "tool_failures",
        "latency_ms",
    )

    # ------------------------------------------------------------------ fixtures

    @staticmethod
    def _example_result(source_kind: str, result_id: str) -> dict[str, Any]:
        """A shipped, invariant-clean example result re-keyed for the improvement tree."""
        document = json.loads(
            (ROOT / "examples" / "evaluation-results" / f"{source_kind}.json").read_text(
                encoding="utf-8"
            )
        )
        document["result_id"] = result_id
        return document

    def _candidate_record(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "candidate_version": self.CANDIDATE_VERSION,
            "parent_version": "0.3.1",
            "source_revision": "candidate-revision-001",
            "artifact_digest": "sha256:" + "b" * 64,
            "hypothesis": "one falsifiable improvement claim",
            "evidence_ids": ["EP-20260917-001"],
            "changed_components": ["skills/agentflow/SKILL.md"],
            "risk_class": "low",
            "evaluation_suite_revision": "public-suite-001",
            "primary_metrics": ["acceptance_rate"],
            "guardrails": ["permission_violations"],
            "rejection_criteria": ["acceptance_rate decreases"],
            "protected_slices": ["evals/public"],
        }

    def _episode_record(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "episode_id": "EP-20260917-001",
            "source_type": "review",
            "objective": "capture the improvement task decision",
            "outcome": "accepted",
            "signals": [
                {"kind": "review", "value": "approved", "evidence_ref": "result://imp/x"}
            ],
            "feedback_summary": "sanitized factual summary",
            "agentflow_version": "0.3.1",
            "host": "codex",
            "provenance": {"carrier": "zcode-session", "sanitized": True},
            "redactions": [],
            "occurred_at": "2026-09-17T10:00:00Z",
        }

    def _comparison(self, baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "baseline_result_id": baseline["result_id"],
            "candidate_result_id": candidate["result_id"],
            "context": {field: baseline[field] for field in validate.COMPARISON_CONTEXT_FIELDS},
            "deltas": {
                metric: candidate["summary"][metric] - baseline["summary"][metric]
                for metric in self.METRICS
            },
            "baseline_summary": baseline["summary"],
            "candidate_summary": candidate["summary"],
        }

    def _release_record(
        self,
        candidate_record: dict[str, Any],
        baseline: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        def result_set(document: dict[str, Any]) -> dict[str, Any]:
            fields = (
                "result_id",
                "source_kind",
                "source_revision",
                "artifact_digest",
                "suite_revision",
                "host",
                "model",
                "permissions_profile",
                "fixture_revision",
                "repeat_count",
                "suite_case_count",
                "summary",
            )
            entry = {field: document[field] for field in fields}
            entry["uncertainty"] = "single example run"
            entry["evidence_refs"] = ["result://imp/" + document["result_id"]]
            return entry

        return {
            "schema_version": 1,
            "candidate": candidate_record,
            "baseline_results": result_set(baseline),
            "candidate_results": result_set(candidate),
            "evaluation_result": "better",
            "decision": "promote",
            "approvals": [{"actor": "release-governor", "decision": "approved"}],
            "rollout": {"mode": "human-gated"},
            "rollback_to": "0.3.1",
        }

    def _write_improvement_tree(self, root: Path) -> dict[str, Any]:
        """Write one legal four-artifact set (plus its evidence episode) under root/records."""
        improvement = root / "records" / "improvement"
        for subtree in ("candidates", "evaluations", "comparisons", "releases"):
            (improvement / subtree).mkdir(parents=True)
        (root / "records" / "episodes" / "2026-09-17").mkdir(parents=True)

        baseline = self._example_result("baseline", self.BASELINE_ID)
        candidate = self._example_result("candidate", self.CANDIDATE_ID)
        candidate_record = self._candidate_record()
        comparison = self._comparison(baseline, candidate)
        release = self._release_record(candidate_record, baseline, candidate)

        self._write_json(
            root / "records" / "episodes" / "2026-09-17" / "EP-20260917-001.json",
            self._episode_record(),
        )
        self._write_json(improvement / "evaluations" / f"{self.BASELINE_ID}.json", baseline)
        self._write_json(improvement / "evaluations" / f"{self.CANDIDATE_ID}.json", candidate)
        self._write_json(
            improvement / "candidates" / f"{self.CANDIDATE_VERSION}.json", candidate_record
        )
        self._write_json(improvement / "comparisons" / "imp-cmp-001.json", comparison)
        self._write_json(improvement / "releases" / "imp-release-001.json", release)
        return {
            "baseline": baseline,
            "candidate": candidate,
            "candidate_record": candidate_record,
            "comparison": comparison,
            "release": release,
        }

    @staticmethod
    def _write_json(path: Path, document: dict[str, Any]) -> None:
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------- helpers

    @staticmethod
    def _run_artifacts(root: Path) -> list[validate.ValidationError]:
        with mock.patch.object(validate, "ROOT", root):
            return validate.validate_workspace_artifacts()

    def _errors_with(
        self, mutate: Any, fixture: dict[str, Any] | None = None
    ) -> list[validate.ValidationError]:
        """Build the legal tree, apply mutate(root, fixture), run the artifacts check."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            written = self._write_improvement_tree(root)
            mutate(root, fixture if fixture is not None else written)
            return self._run_artifacts(root)

    @staticmethod
    def _messages(errors: list[validate.ValidationError]) -> str:
        return " | ".join(f"{error.path}: {error.message}" for error in errors)

    # -------------------------------------------------------------------- tests

    def test_legal_four_artifact_set_compiles_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_improvement_tree(root)
            self.assertEqual(self._run_artifacts(root), [])

    def test_comparison_with_a_missing_result_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            (root / "records" / "improvement" / "evaluations" / f"{self.CANDIDATE_ID}.json").unlink()

        errors = self._errors_with(mutate)
        self.assertTrue(
            any("candidate_result_id" in message and "does not resolve" in message for message in self._messages(errors).split(" | ")),
            self._messages(errors),
        )

    def test_evaluation_stem_not_equal_to_result_id_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            evaluations = root / "records" / "improvement" / "evaluations"
            (evaluations / f"{self.CANDIDATE_ID}.json").rename(evaluations / "wrong-stem.json")

        errors = self._errors_with(mutate)
        self.assertIn("filename stem must equal result_id", self._messages(errors))

    def test_candidate_stem_not_equal_to_candidate_version_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            candidates = root / "records" / "improvement" / "candidates"
            (
                candidates / f"{self.CANDIDATE_VERSION}.json"
            ).rename(candidates / "9.9.9.json")

        errors = self._errors_with(mutate)
        self.assertIn("filename stem must equal candidate_version", self._messages(errors))

    def test_comparison_referencing_swapped_source_kind_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            path = root / "records" / "improvement" / "evaluations" / f"{self.BASELINE_ID}.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["source_kind"] = "candidate"
            self._write_json(path, document)

        errors = self._errors_with(mutate)
        self.assertIn("source_kind is 'candidate', not 'baseline'", self._messages(errors))

    def test_comparison_context_diverging_from_result_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            path = root / "records" / "improvement" / "comparisons" / "imp-cmp-001.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["context"]["model"] = "other-model"
            self._write_json(path, document)

        errors = self._errors_with(mutate)
        self.assertIn("context.model does not match", self._messages(errors))

    def test_release_embedding_a_candidate_that_differs_from_the_record_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            path = root / "records" / "improvement" / "releases" / "imp-release-001.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["candidate"]["hypothesis"] = "quietly changed claim"
            self._write_json(path, document)

        errors = self._errors_with(mutate)
        self.assertIn("not JSON-equal to candidate record", self._messages(errors))

    def test_duplicate_comparison_result_pair_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            comparisons = root / "records" / "improvement" / "comparisons"
            self._write_json(comparisons / "imp-cmp-002.json", fixture["comparison"])

        errors = self._errors_with(mutate)
        self.assertIn("duplicate comparison result pair", self._messages(errors))

    def test_release_result_pair_without_a_matching_comparison_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            other = self._example_result("baseline", "imp-eval-baseline-002")
            evaluations = root / "records" / "improvement" / "evaluations"
            self._write_json(evaluations / "imp-eval-baseline-002.json", other)
            path = root / "records" / "improvement" / "releases" / "imp-release-001.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["baseline_results"]["result_id"] = "imp-eval-baseline-002"
            self._write_json(path, document)

        errors = self._errors_with(mutate)
        self.assertIn("no comparison under records/improvement/comparisons/ matches", self._messages(errors))

    def test_release_referencing_a_missing_result_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            path = root / "records" / "improvement" / "releases" / "imp-release-001.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["candidate_results"]["result_id"] = "imp-eval-missing-999"
            self._write_json(path, document)

        errors = self._errors_with(mutate)
        self.assertIn("imp-eval-missing-999", self._messages(errors))
        self.assertIn("does not resolve to an evaluation result", self._messages(errors))

    def test_release_embedding_an_unknown_candidate_version_is_rejected(self) -> None:
        def mutate(root: Path, fixture: dict[str, Any]) -> None:
            path = root / "records" / "improvement" / "releases" / "imp-release-001.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["candidate"]["candidate_version"] = "9.9.9"
            self._write_json(path, document)

        errors = self._errors_with(mutate)
        self.assertIn("embedded candidate_version '9.9.9' does not resolve", self._messages(errors))

    def test_candidate_evidence_ids_resolve_against_existing_records(self) -> None:
        def episode_negative(root: Path, fixture: dict[str, Any]) -> None:
            path = (
                root / "records" / "improvement" / "candidates" / f"{self.CANDIDATE_VERSION}.json"
            )
            document = json.loads(path.read_text(encoding="utf-8"))
            document["evidence_ids"] = ["EP-99999999-999"]
            self._write_json(path, document)

        errors = self._errors_with(episode_negative)
        self.assertIn("does not resolve to an existing record under records/episodes/", self._messages(errors))

        def bug_negative(root: Path, fixture: dict[str, Any]) -> None:
            path = (
                root / "records" / "improvement" / "candidates" / f"{self.CANDIDATE_VERSION}.json"
            )
            document = json.loads(path.read_text(encoding="utf-8"))
            document["evidence_ids"] = ["BUG-20260917-001"]
            self._write_json(path, document)

        errors = self._errors_with(bug_negative)
        self.assertIn("does not resolve to an existing record under records/bugs/", self._messages(errors))

    def test_unknown_entries_in_the_improvement_subtree_are_rejected(self) -> None:
        def stray_file(root: Path, fixture: dict[str, Any]) -> None:
            (root / "records" / "improvement" / "notes.txt").write_text("stray\n", encoding="utf-8")

        errors = self._errors_with(stray_file)
        self.assertIn("unexpected entry under records/improvement/", self._messages(errors))

        def nested_file(root: Path, fixture: dict[str, Any]) -> None:
            nested = root / "records" / "improvement" / "candidates" / "nested"
            nested.mkdir()
            self._write_json(nested / f"{self.CANDIDATE_VERSION}.json", fixture["candidate_record"])

        errors = self._errors_with(nested_file)
        self.assertIn("unexpected entry under records/improvement/", self._messages(errors))

        def wrong_suffix(root: Path, fixture: dict[str, Any]) -> None:
            (root / "records" / "improvement" / "evaluations" / "imp-eval-001.md").write_text(
                "{}\n", encoding="utf-8"
            )

        errors = self._errors_with(wrong_suffix)
        self.assertIn("evaluations artifacts are JSON files; unexpected non-json file", self._messages(errors))


class TestRecordContractTests(unittest.TestCase):
    """Test records under records/tests/ (0.7.0): plan registry contract and run invariants."""

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
            Path(root) / "records/tests/demo-webapp-feature-login/plan-2026-09-17-001.md",
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
            Path(root) / "records/tests/demo-webapp-feature-login/run-2026-09-17-001.md",
            self.RUN_MD.format(**fields),
        )
        errors, _, _ = validate.validate_test_run_markdown(path, path.relative_to(root), {}, plans)
        return errors

    def test_valid_plan_and_run_examples_pass(self) -> None:
        plan_path = ROOT / "examples" / "test-records" / "plan-2026-09-17-001.md"
        errors, entry = validate.validate_test_plan_markdown(plan_path, plan_path.relative_to(ROOT), {})
        self.assertEqual([], errors)
        self.assertIsNotNone(entry)
        run_path = ROOT / "examples" / "test-records" / "run-2026-09-17-001.md"
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
                Path(temporary) / "records/tests/demo-webapp-feature-login/plan-2026-09-17-001.md",
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

    def test_tests_is_a_known_record_class(self) -> None:
        self.assertIn("tests", validate.KNOWN_RECORD_CLASSES)


if __name__ == "__main__":
    unittest.main()
