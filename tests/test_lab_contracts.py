import argparse
import contextlib
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

    def test_live_doc_chain_gate_flags_drift_and_requires_surface(self) -> None:
        # The compile gate must run the checker on the documents, not only pin the checker:
        # a drifted live document fails, and a missing declared surface is a failure rather
        # than a silent loss of coverage.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tools" / "lab").mkdir(parents=True)
            shutil.copy(LAB / "doc_chain.py", root / "tools" / "lab" / "doc_chain.py")
            (root / "docs" / "features").mkdir(parents=True)
            errors = validate.validate_doc_chain_live(root)
            self.assertTrue(any("docs/product" in error.path for error in errors))
            (root / "docs" / "product").mkdir(parents=True)
            (root / "docs" / "product" / "drifted.md").write_text(
                "# 报告\n\nD 桶积分中断最多。\n", encoding="utf-8"
            )
            errors = validate.validate_doc_chain_live(root)
        self.assertTrue(
            any("drifted.md" in error.path and "C14" in error.message for error in errors)
        )

    def test_path_residue_flags_migrated_plans_but_spares_examples_fixture(self) -> None:
        # docs/plans has no live descendant (it moved into the singular plan/), so it is a
        # token; examples/plans/ is a live fixture directory and must not be punished by it.
        self.assertIn("docs/plans", validate.PATH_RESIDUE_TOKENS)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs" / "features").mkdir(parents=True)
            (root / "docs" / "features" / "README.md").write_text(
                "计划落在 docs/plans/ 下。\n", encoding="utf-8"
            )
            errors = validate.validate_live_doc_references(root)
            self.assertTrue(any("docs/plans" in error.message for error in errors))
            (root / "examples" / "plans").mkdir(parents=True)
            (root / "examples" / "plans" / "README.md").write_text(
                "plans/ 下有结构有效的示例。\n", encoding="utf-8"
            )
            errors = validate.validate_live_doc_references(root)
        self.assertEqual([error for error in errors if "examples/plans" in error.path], [])

    def test_bug_record_severity_uses_priority_grades(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "ISS-2026-901",
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
            "bug_id": "ISS-2026-902",
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
            "first_record": "ISS-2026-901",
            "occurrences": ["ISS-2026-901"],
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
                "first_record: ISS-2026-901\n"
                "occurrences:\n"
                "  - ISS-2026-901\n"
                "recorded_at: 2026-01-01T00:00:00Z\n"
                "---\n",
                encoding="utf-8",
            )
            errors = validate.validate_recurrence_markdown(path)
        self.assertTrue(any("filename must equal class_id" in error.message for error in errors))

    def test_bug_record_verified_requires_closure_criteria(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "ISS-2026-903",
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
        path = ROOT / "issues" / "fixture.md"
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
        path = ROOT / "issues" / "fixture.md"
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
        path = ROOT / "docs" / "issues" / "fixture.md"
        cjk_dangling = validate.validate_body_references(
            "关联设计见 other-repo/docs/缺失文档.md 的说明。", path
        )
        self.assertTrue(any("缺失文档.md" in error.message for error in cjk_dangling))
        cjk_resolved = validate.validate_body_references(
            "见 docs/issues/README.md 的约定。", path
        )
        self.assertEqual(cjk_resolved, [])
        versions = validate.validate_body_references(
            "该行为在 0.3.4/0.3.5 均适用。", path
        )
        self.assertEqual(versions, [])

    def test_review_record_id_matches_recorded_at_and_is_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            record_dir = base / "reviews" / "demo-feature"
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
            relative = Path("reviews/demo-feature/review-20260101-001.md")
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
                "review_roundtrips": [],
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

    def test_live_doc_scan_flags_broken_links_and_retired_paths(self) -> None:
        # Discrimination fixtures for the 2026-10 residue scans. The good file pins every
        # exemption (fenced/inline quotations, near-miss word hits, the current roots); the
        # bad file must trip both scan classes.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / "docs").mkdir()
            (base / "docs" / "target.md").write_text("ok\n", encoding="utf-8")
            (base / "docs" / "good.md").write_text(
                "见 [target](target.md)。\n"
                "引文 `records/bugs/` 与 `](target)` 示例不扫。\n"
                "```\nrecords/ in a fence is a quotation\n```\n"
                "地址非主张：历史引用 agentflows@0.8.2:docs/agent-roles.md 仍可被记录引用。\n"
                "现行目录 docs/issues/ 与 docs/releases/ 正常。\n"
                "```mermaid\nflowchart TB\n    A[\"issues/ 是现行路径\"]\n```\n"
                "词内命中不入罪：debugs/、subrecords/ 均非退役路径。\n",
                encoding="utf-8",
            )
            errors = validate.validate_live_doc_references(root=base)
            self.assertEqual([error.message for error in errors], [])

            (base / "docs" / "bad.md").write_text(
                "断链：[missing](gone.md)。\n"
                "```mermaid\nflowchart TB\n    X[\"bugs/<日期>/ 旧图节点\"]\n```\n",
                encoding="utf-8",
            )
            messages = [error.message for error in validate.validate_live_doc_references(root=base)]
            self.assertTrue(any("broken relative link" in message for message in messages), messages)
            # The retired-path hit lives only inside the mermaid block: the mermaid-scanned
            # branch is the sole source of this assertion, so skipping diagrams fails here.
            self.assertTrue(
                any(
                    "retired path in prose" in message and "(line 4)" in message
                    for message in messages
                ),
                messages,
            )

    def test_live_doc_scan_exempts_generated_runtime_and_changelog_only(self) -> None:
        # 2026-10-12 slimming batch: the frozen `_archive/`, the retired iteration log, and the
        # migration-record directory lost their exemptions with their trees. Only the generated
        # runtime tree and CHANGELOG.md stay outside the scan; recreating any retired carrier
        # (e.g. docs/iteration-log.md) must now trip the token scan instead of passing silently.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / "packaging" / "runtime").mkdir(parents=True)
            (base / "packaging" / "runtime" / "generated.md").write_text(
                "records/ residue\n", encoding="utf-8"
            )
            (base / "docs").mkdir()
            (base / "CHANGELOG.md").write_text("records/ history\n", encoding="utf-8")
            self.assertEqual(validate.validate_live_doc_references(root=base), [])
            (base / "docs" / "iteration-log.md").write_text(
                "docs/iteration-log reborn\n", encoding="utf-8"
            )
            errors = validate.validate_live_doc_references(root=base)
            self.assertTrue(
                any("retired path in prose" in error.message for error in errors), errors
            )

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
                "plans are Markdown hybrids named <plan_id>.md; see plans/README.md\n",
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
            errors = validate.validate_plan_markdown(path)
        messages = [error.message for error in errors]
        self.assertTrue(any("duplicate task id" in m for m in messages))
        self.assertTrue(any("dependency cycle" in m for m in messages))
        self.assertTrue(any("blocking unresolved decision" in m for m in messages))

    def test_approval_gate_is_not_bypassed_by_a_decision_titled_with_wei_jue(self) -> None:
        # Item A: a 未决项 row whose text merely contains the word 未决 used to be skipped as if it
        # were a header, so an approved plan with an open blocking decision passed the gate.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "PLAN-TEST-004.md"
            path.write_text(
                "---\n"
                "plan_id: PLAN-TEST-004\n"
                "plan_version: 0.1.0\n"
                "status: approved\n"
                "objective: o\n"
                "recorded_at: 2026-09-17T00:00:00Z\n"
                "---\n\n## 进展概览\n\n概述\n\n## 任务清单\n\n"
                "| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| `T01` | 甲 | P0 | a.ts | — | ☐ 未开始 | |\n"
                "\n### 未决项\n\n"
                "| 编号 | 问题 | 是否阻塞 | 状态 |\n"
                "| --- | --- | --- | --- |\n"
                "| U-01 | 未决的权限模型 | 阻塞 | 尚未关闭 |\n"
                "\n## 验证命令\n\n```sh\necho x\n```\n",
                encoding="utf-8",
            )
            errors = validate.validate_plan_markdown(path)
        messages = [error.message for error in errors]
        self.assertTrue(
            any("blocking unresolved decision" in m and "U-01" in m for m in messages), messages
        )
        # The real header row ("编号") must still be skipped, not reported as a decision.
        self.assertFalse(any("'编号'" in m for m in messages), messages)

    def test_schema_else_without_if_is_not_applied(self) -> None:
        # Item E: JSON Schema applies then/else only as branches of an if. An else without an if
        # used to run unconditionally, so a bare else could reject every instance.
        with tempfile.TemporaryDirectory() as temporary:
            bare = Path(temporary) / "bare-else.schema.json"
            bare.write_text(json.dumps({"else": {"required": ["never"]}}), encoding="utf-8")
            self.assertEqual(validate.SchemaValidator(bare).validate({}), [])
            guarded = Path(temporary) / "guarded.schema.json"
            guarded.write_text(
                json.dumps(
                    {
                        "if": {"required": ["a"]},
                        "then": {"required": ["b"]},
                        "else": {"required": ["c"]},
                    }
                ),
                encoding="utf-8",
            )
            failed_if = validate.SchemaValidator(guarded).validate({})
            self.assertTrue(any("'c'" in error.message for error in failed_if), failed_if)
            self.assertEqual(validate.SchemaValidator(guarded).validate({"a": 1, "b": 1}), [])

    def test_external_fragment_must_sit_next_to_its_citation(self) -> None:
        # Item G: the old check accepted a fragment anywhere in the body. The excerpt must follow
        # its citation directly (blank lines allowed), or the citation must sit inside the quote.
        path = ROOT / "issues" / "fixture.md"
        frontmatter = {"files": ["example-project@r1:services/api/orders.go"]}
        distant = (
            "问题代码见 `example-project@r1:services/api/orders.go`：\n\n"
            "这里是一段与引文无关的正文说明。\n\n"
            "```\ncode\n```\n"
        )
        errors = validate.validate_external_excerpts(frontmatter, distant, path)
        self.assertTrue(
            any("embedded fragment" in error.message for error in errors),
            [error.message for error in errors],
        )
        blockquote = (
            "问题代码见 `example-project@r1:services/api/orders.go`：\n\n"
            "> 引文原文\n"
        )
        self.assertEqual(validate.validate_external_excerpts(frontmatter, blockquote, path), [])

    def test_bug_layout_archive_date_message_is_pinned(self) -> None:
        # Item F (helper extraction): the archive date check must keep its exact behavior.
        relative = Path("docs/issues/归档/2026-01-01/ISS-2026-910-archived.md")
        frontmatter = {"bug_id": "ISS-2026-910", "recorded_at": "2026-01-02T00:00:00Z"}
        errors = validate.validate_bug_layout(frontmatter, ROOT / relative, relative, {})
        self.assertEqual(
            [error.message for error in errors],
            ["date directory '2026-01-01' does not match recorded_at date 2026-01-02"],
        )

    @staticmethod
    def _git(repository: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )


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

    def test_lab_readme_states_the_checker_root_is_caller_designated(self) -> None:
        # Item K: the README used to claim check-diff "always" reads the trusted checker, but
        # --checker-root is caller-chosen. The wording must say so plainly.
        readme = (LAB / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("始终从受信任的检查器仓库读取", readme)
        self.assertIn("由调用方（监督者）指定", readme)

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

    def test_build_runtime_is_a_declared_and_required_gate_path(self) -> None:
        # Item O: packaging/build_runtime.py decides which files the candidate snapshot copies and
        # verifies, so it must be protected and must stay required by validate.py.
        self.assertIn("packaging/build_runtime.py", validate.REQUIRED_PROTECTED_PATHS)
        entries = [
            line.strip()
            for line in validate.PROTECTED_PATHS_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertIn("packaging/build_runtime.py", entries)
        with tempfile.TemporaryDirectory() as temporary:
            shrunken = Path(temporary) / "shrunken.txt"
            shrunken.write_text(
                "\n".join(entry for entry in entries if entry != "packaging/build_runtime.py") + "\n",
                encoding="utf-8",
            )
            errors = validate.validate_protected_paths(shrunken)
        self.assertTrue(
            any("packaging/build_runtime.py" in error.message for error in errors),
            [str(error) for error in errors],
        )

    def test_validate_workflow_runs_tests_once_read_only_with_full_history(self) -> None:
        # Item M: `validate.py all` already runs the regression suite, so a separate
        # `validate.py tests` step duplicated it. The workflow must also declare read-only
        # permissions and fetch full history for the trusted checker's default-branch reference.
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertNotIn("validate.py tests", workflow)

    def test_packaging_readme_names_every_forbidden_top_level_entry(self) -> None:
        # Item N: the exclusion list in packaging/README.md must match what build_runtime.py
        # forbids at the top level of the generated tree.
        sys.path.insert(0, str(ROOT / "packaging"))
        try:
            import build_runtime  # noqa: E402  (packaging/ is not a package)
        finally:
            sys.path.pop(0)
        readme = (ROOT / "packaging" / "README.md").read_text(encoding="utf-8")
        missing = sorted(
            name
            for name in build_runtime.FORBIDDEN_TOP_LEVEL
            if f"`{name}`" not in readme and f"`{name}/`" not in readme
        )
        self.assertEqual(missing, [], "packaging/README.md does not name these excluded entries")


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


class ValidateResidualTests(unittest.TestCase):
    """B5/B6/B10 (audit report 2 §6): structured decode errors, path containment, and the
    tests/ declared-content assertion no longer exempting dot entries.
    """

    def test_load_record_markdown_surfaces_decoding_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "non-utf8.md"
            path.write_bytes(b"---\nid: broken\n---\n\xff\xfe\xfa body")
            frontmatter, body, errors = validate.load_record_markdown(path)
        self.assertIsNone(frontmatter)
        self.assertEqual(body, "")
        self.assertEqual(len(errors), 1)
        self.assertIn("unreadable file", errors[0].message)

    def _contained_reference_errors(self, repo: Path, body: str, record: Path) -> list[validate.ValidationError]:
        with mock.patch.object(validate, "ROOT", repo):
            return validate.validate_body_references(body, record)

    def test_body_references_may_climb_within_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo = base / "repo"
            (repo / "issues" / "recurrence").mkdir(parents=True)
            (repo / "issues" / "归档" / "2026-09-15").mkdir(parents=True)
            (repo / "issues" / "归档" / "2026-09-15" / "ISS-2026-905-record.md").write_text(
                "x", encoding="utf-8"
            )
            record = repo / "issues" / "recurrence" / "ledger.md"
            errors = self._contained_reference_errors(
                repo, "see ../归档/2026-09-15/ISS-2026-905-record.md for evidence", record
            )
        self.assertEqual(errors, [])

    def test_body_references_cannot_escape_the_repository(self) -> None:
        # The old check resolved (ROOT / "../secret.md") OUTSIDE the repository and passed
        # when that file existed. The file here deliberately exists outside the patched
        # ROOT: only the containment rule keeps the reference rejected.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo = base / "repo"
            (repo / "issues").mkdir(parents=True)
            (base / "secret.md").write_text("outside evidence", encoding="utf-8")
            record = repo / "issues" / "ISS-2026-001-record.md"
            errors = self._contained_reference_errors(repo, "evidence at ../secret.md here", record)
        self.assertEqual(len(errors), 1)
        self.assertIn("exists neither in this repository", errors[0].message)

    def test_tests_directory_dot_entries_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tests = Path(temporary) / "tests"
            tests.mkdir()
            (tests / ".hidden").mkdir()
            (tests / ".hidden" / "__init__.py").write_text("import-time hijack", encoding="utf-8")
            errors = validate.validate_unit_tests(Path(temporary))
        self.assertTrue(any("unexpected entry in the test directory" in error.message for error in errors))

    LIVE_FIXTURE_FILES = {
        "docs/issues/README.md": "# issues\n",
        "docs/releases/todo.md": "# todo\n",
        "docs/features/README.md": "# features\n",
        "episodes/README.md": "# episodes\n",
        "reviews/README.md": "# reviews\n",
    }

    @classmethod
    def _live_fixture(cls, root: Path) -> None:
        """Create the five live record roots, each with a root-level file the walk accepts."""
        for relative, text in cls.LIVE_FIXTURE_FILES.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

    @staticmethod
    def _artifact_errors(root: Path) -> list[str]:
        with mock.patch.object(validate, "ROOT", root):
            return [str(error) for error in validate.validate_workspace_artifacts()]

    def test_files_entries_cannot_be_absolute_or_escape_the_repository(self) -> None:
        # Item B: the files: check used a bare is_file() on (ROOT / entry). An absolute entry such
        # as /etc/hosts ignored ROOT, and ../ climbed out of it; both passed as if they were evidence.
        bug = (
            "---\n"
            "bug_id: ISS-2026-920\n"
            "title: 绝对路径与上溯\n"
            "status: open\n"
            "severity: P2\n"
            "error_kind: other\n"
            "attribution: unknown\n"
            "provenance: agentflow\n"
            "project: p\n"
            "files:\n"
            "  - /etc/hosts\n"
            "  - ../outside.md\n"
            "  - docs/kept.md\n"
            "recorded_at: 2026-01-01T00:00:00Z\n"
            "---\n\n## 现象\n\nx\n\n## 根因\n\ny\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            self._live_fixture(repo)
            (repo / "docs" / "kept.md").write_text("kept", encoding="utf-8")
            (Path(temporary) / "outside.md").write_text("outside", encoding="utf-8")
            (repo / "docs" / "issues" / "ISS-2026-920-escape.md").write_text(bug, encoding="utf-8")
            errors = self._artifact_errors(repo)
        self.assertTrue(any("'/etc/hosts'" in error for error in errors), errors)
        self.assertTrue(any("'../outside.md'" in error for error in errors), errors)
        self.assertFalse(any("'docs/kept.md'" in error for error in errors), errors)

    def test_unrecognised_review_entries_fail_and_archive_snapshots_pass(self) -> None:
        # Item C: a non-record file directly under a review directory was skipped silently.
        # Archived evidence snapshots under archive/ remain allowed.
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            self._live_fixture(repo)
            feature = repo / "reviews" / "demo-feature"
            (feature / "archive" / "2026-09-16-001").mkdir(parents=True)
            (feature / "archive" / "2026-09-16-001" / "doc.md").write_text("snapshot", encoding="utf-8")
            (feature / "notes.md").write_text("stray", encoding="utf-8")
            errors = self._artifact_errors(repo)
        self.assertTrue(any("/reviews/demo-feature/notes.md" in error for error in errors), errors)
        self.assertFalse(any("/reviews/demo-feature/archive/" in error for error in errors), errors)

    def test_unknown_feature_batch_entries_fail_and_known_segments_pass(self) -> None:
        # Item C: non-plan files in docs/features/ were skipped. Unknown entries must now fail;
        # the documented batch layout (README, proposal/, plan/) must still pass.
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            self._live_fixture(repo)
            batch = repo / "docs" / "features" / "feature-2026-09-17-demo"
            (batch / "plan").mkdir(parents=True)
            (batch / "proposal").mkdir()
            (batch / "README.md").write_text("# batch\n", encoding="utf-8")
            (batch / "proposal" / "p.md").write_text("# proposal\n", encoding="utf-8")
            (batch / "notes.txt").write_text("stray", encoding="utf-8")
            (batch / "plan" / "notes.txt").write_text("stray", encoding="utf-8")
            (repo / "docs" / "features" / "stray.md").write_text("stray", encoding="utf-8")
            errors = self._artifact_errors(repo)
        paths = [error.split(": ", 1)[0] for error in errors]
        self.assertTrue(any(p.endswith("feature-2026-09-17-demo/notes.txt") for p in paths), errors)
        self.assertTrue(any(p.endswith("feature-2026-09-17-demo/plan/notes.txt") for p in paths), errors)
        self.assertTrue(any(p.endswith("docs/features/stray.md") for p in paths), errors)
        self.assertFalse(any(p.endswith(("README.md", "proposal/p.md")) for p in paths), errors)

    def test_feature_testing_records_are_patrolled(self) -> None:
        # Item H: features/<batch>/testing/ was never walked. The shipped valid plan and run pair
        # must pass there, and a misnamed plan must now fail.
        plan_source = (ROOT / "examples" / "testing" / "plan-2026-09-17-001.md").read_text(encoding="utf-8")
        run_source = (ROOT / "examples" / "testing" / "run-2026-09-17-001.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            self._live_fixture(repo)
            testing = repo / "docs" / "features" / "feature-2026-09-17-demo" / "testing" / "demo-webapp-feature-login"
            testing.mkdir(parents=True)
            (testing / "plan-2026-09-17-001.md").write_text(plan_source, encoding="utf-8")
            (testing / "run-2026-09-17-001.md").write_text(run_source, encoding="utf-8")
            clean = [error for error in self._artifact_errors(repo) if "/testing/" in error]
            self.assertEqual(clean, [])
            (testing / "plan-2026-09-18-001.md").write_text(plan_source, encoding="utf-8")
            broken = [error for error in self._artifact_errors(repo) if "/testing/" in error]
        self.assertTrue(
            any("plan-2026-09-18-001.md" in error and "must be plan-2026-09-17-001.md" in error for error in broken),
            broken,
        )

    def test_missing_agent_and_skill_directories_fail_the_docs_check(self) -> None:
        # Item C: a missing agents/ or skills/ directory made the glob empty and the check passed.
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(validate, "ROOT", Path(temporary)):
                errors = [str(error) for error in validate.validate_doc_consistency()]
        self.assertTrue(any("agents/ directory is missing" in error for error in errors), errors)
        self.assertTrue(any("skills/ directory is missing" in error for error in errors), errors)

    def test_generated_test_cache_holds_only_bytecode(self) -> None:
        # Item D: tests/__pycache__ was exempted wholesale, so a source file or package hidden in it
        # reached unittest discovery unchecked. Only .pyc files may live in the generated cache.
        with tempfile.TemporaryDirectory() as temporary:
            tests = Path(temporary) / "tests"
            (tests / "__pycache__").mkdir(parents=True)
            (tests / "test_lab_contracts.py").write_text("", encoding="utf-8")
            (tests / "test_record_store.py").write_text("", encoding="utf-8")
            (tests / "__pycache__" / "test_lab_contracts.cpython-312.pyc").write_bytes(b"")
            (tests / "__pycache__" / "sneaky.py").write_text("import-time hijack", encoding="utf-8")
            errors = validate.validate_unit_tests(Path(temporary))
        self.assertTrue(
            any(error.path == "tests/__pycache__/sneaky.py" for error in errors),
            [str(error) for error in errors],
        )
        self.assertFalse(any(error.path.endswith(".pyc") for error in errors))


class WriteScopeScriptTests(unittest.TestCase):
    """check-write-scope.sh: "." must cover the whole tree (it used to silently match nothing)."""

    SCRIPT = ROOT / "skills" / "agentflow" / "scripts" / "check-write-scope.sh"

    def _repo_with_changes(self, directory: Path) -> None:
        def git(*args: str) -> None:
            subprocess.run(
                ["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                cwd=directory,
                check=True,
                capture_output=True,
            )

        git("init", "-q")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")
        (directory / "tracked.txt").write_text("v1\n", encoding="utf-8")
        git("add", "tracked.txt")
        git("commit", "-qm", "init")
        (directory / "tracked.txt").write_text("v2\n", encoding="utf-8")
        (directory / "new.txt").write_text("new\n", encoding="utf-8")

    def test_dot_scope_covers_the_whole_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._repo_with_changes(directory)
            completed = subprocess.run(
                ["bash", str(self.SCRIPT), "HEAD", "."],
                cwd=directory,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("OK", completed.stdout)

    def test_out_of_scope_changes_still_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._repo_with_changes(directory)
            completed = subprocess.run(
                ["bash", str(self.SCRIPT), "HEAD", "sub"],
                cwd=directory,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn("FAIL", completed.stdout)


class TrendReviewFindingsTests(unittest.TestCase):
    def setUp(self) -> None:
        import trend

        self.trend = trend
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "reviews" / "feat").mkdir(parents=True)
        self.patch = mock.patch.object(trend, "ROOT", self.root)
        self.patch.start()

    def tearDown(self) -> None:
        self.patch.stop()
        self.tmp.cleanup()

    def test_review_without_findings_section_is_an_error(self) -> None:
        (self.root / "reviews" / "feat" / "review-2026-10-13-001.md").write_text(
            "# review\n\n无摘要\n", encoding="utf-8")
        with self.assertRaises(ValueError) as caught:
            self.trend.open_review_findings()
        self.assertIn("## 发现摘要", str(caught.exception))

    def test_counts_bullets_under_findings_section(self) -> None:
        (self.root / "reviews" / "feat" / "review-2026-10-13-001.md").write_text(
            "# review\n\n## 发现摘要\n\n- F1 一条\n- F2 一条\n\n## 其它\n\n- 不计\n",
            encoding="utf-8")
        self.assertEqual(self.trend.open_review_findings(), 2)


class GoalTraceabilityEvidenceTests(unittest.TestCase):
    """C22 goal traceability and C23 evidence presence (2026-10-23 gate change, user-authorized).

    Each test pins one defect the 2026-10-22 walkthrough found in real files: a proposal goal that
    disappeared from spec and the plan board while every gate stayed green, and ☑ task rows whose
    only evidence was a /tmp path that had already been cleaned away. C22 is marker-gated; C23 is
    not, because the evidence duty belongs to the plan contract rather than to an opt-in layer.
    """

    README_TMPL = (
        "# 批次\n\n## 需求评审门\n## 技术方案评审门\n\n"
        "本批启用 {marker} 标记。\n\n## 目标承接表\n\n"
        "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n{rows}"
    )
    ROW_OK = "| G1 目标一 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n"
    PROPOSAL = "# proposal\n\n## 1.2 目标\n\n- **G1 目标一**：可判定。\n"
    SPEC = (
        "# spec\n\n## 3.0 不合规项（反审 checklist）\n\n"
        "| # | 缺口 | 阻塞 | 状态 |\n| --- | --- | --- | --- |\n| B-1 | x | 阻塞 | ☑ 已关闭 |\n\n"
        "### M-A 模块一\n\n| 验收点 | 来源 |\n| --- | --- |\n| G1-AC-01 | proposal G1 |\n"
    )
    GOOD_EVIDENCE = "`docs/issues/README.md` 在盘"

    def _plan(self, evidence: str, status: str = "☑ 已完成") -> str:
        return (
            "# plan\n\n## 0. 分支策略\n\n"
            "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| T01 | 做一件事 | `a.py` | — | {status} | {evidence} |\n"
        )

    def _batch(self, root: Path, *, marker: str = "agentflow 目标承接",
               rows: str | None = None, plan_text: str | None = None) -> Path:
        batch = root / "docs" / "features" / "b"
        for stage in ("proposal", "spec", "plan"):
            (batch / stage).mkdir(parents=True, exist_ok=True)
        (batch / "README.md").write_text(
            self.README_TMPL.format(marker=marker, rows=self.ROW_OK if rows is None else rows),
            encoding="utf-8")
        (batch / "proposal" / "p.md").write_text(self.PROPOSAL, encoding="utf-8")
        (batch / "spec" / "s.md").write_text(self.SPEC, encoding="utf-8")
        (batch / "plan" / "p.md").write_text(
            self._plan(self.GOOD_EVIDENCE) if plan_text is None else plan_text, encoding="utf-8")
        (root / "docs" / "issues").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "issues" / "README.md").write_text("# issues\n", encoding="utf-8")
        (root / "a.py").write_text("# a\n", encoding="utf-8")
        return batch

    def test_tmp_only_evidence_on_a_completed_row_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, plan_text=self._plan("`/tmp/baseline.txt`（已清理）"))
            errors = doc_chain.batch_traceability_findings(batch, root)
            self.assertEqual(
                [e for e in errors if e.startswith("C23")],
                [e for e in errors if "C23 证据在场" in e and "T01" in e],
            )

    def test_repo_qualified_and_na_cells_are_valid_carriers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._batch(root)
            for cell in (self.GOOD_EVIDENCE, "youc@1a2b3c4:docs/x.md", "N/A: 纯文本改动，门输出即证据"):
                self.assertTrue(
                    doc_chain.evidence_carriers(cell, root), f"carrier missed: {cell}")

    def test_commit_sha_counts_only_when_git_can_resolve_it(self) -> None:
        def git(cwd: Path, *args: str) -> str:
            completed = subprocess.run(
                ["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                cwd=cwd, capture_output=True, text=True, check=True)
            return completed.stdout.strip()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root)
            git(root, "init", "-q")
            git(root, "config", "user.email", "t@example.com")
            git(root, "config", "user.name", "t")
            git(root, "add", "-A")
            git(root, "commit", "-qm", "fixture")
            sha = git(root, "rev-parse", "--short", "HEAD")
            self.assertIn("提交号", doc_chain.evidence_carriers(f"{sha} 落盘", root))
            self.assertEqual(doc_chain.evidence_carriers("deadbe 落盘", batch), [])
            plan = self._plan(f"`{sha}` 提交在历史里")
            self.assertEqual(
                [e for e in doc_chain.batch_traceability_findings(batch, root) if "C23" in e], [])

    def test_rows_that_are_not_done_carry_no_evidence_duty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, plan_text=self._plan("", status="☐ 未开始"))
            errors = doc_chain.batch_traceability_findings(batch, root)
            self.assertEqual([e for e in errors if "C23" in e], [])

    def test_goal_declared_upstream_but_missing_from_the_table_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, rows="")
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("G1" in e and "未进入承接表" in e for e in errors), errors)

    def test_phantom_task_id_and_status_overclaim_both_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, rows=self.ROW_OK.replace("T01", "T99"))
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("T99" in e and "不在计划任务表" in e for e in errors), errors)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            # 承接表声称已完成，看板行还在进行中：状态聚合不一致必须红
            batch = self._batch(root, plan_text=self._plan(self.GOOD_EVIDENCE, status="◐ 进行中"))
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("承接表标已完成" in e for e in errors), errors)

    def test_completed_task_that_nobody_claims_trips_as_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, rows=self.ROW_OK.replace("| T01 |", "| — |"))
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("孤儿任务" in e and "T01" in e for e in errors), errors)

    def test_marker_without_a_table_does_not_silently_skip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root)
            (batch / "README.md").write_text(
                "# 批次\n\n## 需求评审门\n\n本批启用 agentflow 目标承接 标记，表还没建。\n",
                encoding="utf-8")
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("没有承接表" in e for e in errors), errors)

    def test_unmarked_batch_is_left_alone_by_c22(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, marker="目标承接", rows="")
            self.assertEqual(doc_chain.goal_traceability_findings(batch, root), [])

    def test_repo_scan_applies_c23_to_every_batch_but_c22_only_to_opted_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._batch(root, marker="目标承接", rows="",
                        plan_text=self._plan("`/tmp/x.txt`"))
            errors = doc_chain.repo_policy_findings(root)
            self.assertTrue(any("C23 证据在场" in e for e in errors), errors)
            self.assertFalse(any("C22 目标承接" in e for e in errors), errors)

    def test_disposition_field_is_optional_and_enumerated(self) -> None:
        base = {
            "bug_id": "ISS-2026-900",
            "title": "归属示例",
            "status": "open",
            "severity": "P2",
            "error_kind": "other",
            "attribution": "product_code",
            "provenance": "external",
            "project": "demo",
            "files": ["a.py"],
            "recorded_at": "2026-10-22T16:00:00Z",
        }
        validator = validate.SchemaValidator(validate.BUG_RECORD_SCHEMA)
        self.assertEqual(validator.validate(dict(base)), [])
        self.assertEqual(validator.validate({**base, "disposition": "deferred"}), [])
        bad = validator.validate({**base, "disposition": "wontfix"})
        self.assertTrue(bad, "an out-of-set disposition must be rejected")
        self.assertTrue(any("deferred" in error.message for error in bad), bad)


if __name__ == "__main__":
    unittest.main()
