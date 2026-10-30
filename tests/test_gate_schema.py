import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "tools" / "lab"
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import isolation
import validate


class ValidatorRegressionTests(unittest.TestCase):
    def test_files_entry_rejects_absolute_and_outside_paths(self) -> None:
        absolute = validate.files_entry_errors("/etc/passwd", Path("ISS-x.md"))
        outside = validate.files_entry_errors("../outside.md", Path("ISS-x.md"))
        self.assertTrue(any("must be repository-relative" in error.message for error in absolute), absolute)
        self.assertTrue(any("resolves outside the repository" in error.message for error in outside), outside)

    def test_max_items_rejects_overflow(self) -> None:
        import gate.schema as schema_module

        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://example.test/max-items.json",
            "type": "array",
            "maxItems": 1,
            "items": {"type": "string"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "max-items.schema.json"
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = schema_module.SchemaValidator(path).validate(["a", "b"])
        self.assertTrue(any("must contain at most 1 items" in error.message for error in errors), [e.message for e in errors])

    def test_contains_allows_more_than_minimum_matches(self) -> None:
        # Kills the `matched_count < minimum` → `!=` mutation: more than the minimum must pass.
        import gate.schema as schema_module

        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://example.test/contains-min.json",
            "type": "array",
            "contains": {"type": "string", "pattern": "^a"},
            "minContains": 1,
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "contains.schema.json"
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = schema_module.SchemaValidator(path).validate(["a", "ab"])
        self.assertEqual([], [error.message for error in errors])

    def test_plan_schema_accepts_decision_deps_as_a_token_list(self) -> None:
        # P1-5: plan.schema.json had additionalProperties:false, so a plan could not carry the
        # dependency field the document-chain contract tells authors to write.
        import gate.schema as schema_module

        instance = {
            "plan_id": "PLAN-DECISION-DEPS",
            "plan_version": "0.1.0",
            "status": "proposed",
            "objective": "o",
            "recorded_at": "2026-10-30T00:00:00Z",
            "decision_deps": ["DEC-2026-001#r1"],
        }
        path = ROOT / "schemas" / "plan.schema.json"
        validator = schema_module.SchemaValidator(path)
        self.assertEqual([], [error.message for error in validator.validate(instance)])
        bad = dict(instance, decision_deps="DEC-2026-001#r1")
        self.assertTrue(any("must be of type 'array'" in error.message for error in validator.validate(bad)))

    def test_unknown_schema_type_fails_closed(self) -> None:
        # T08 / G2-AC-05: a misspelled type used to return True from is_type and silently
        # disable the field; both the schema walker and the instance validator must reject it.
        import gate.schema as schema_module

        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://example.test/unknown-type.json",
            "type": "object",
            "properties": {"value": {"type": "objct"}},
            "required": ["value"],
            "additionalProperties": False,
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "unknown.schema.json"
            path.write_text(json.dumps(schema), encoding="utf-8")
            loader_errors = schema_module.check_schema_keywords(schema, path)
            instance_errors = schema_module.SchemaValidator(path).validate({"value": "x"})
        self.assertTrue(
            any("unsupported type value 'objct'" in error.message for error in loader_errors),
            [error.message for error in loader_errors],
        )
        self.assertTrue(
            any("unsupported schema type 'objct'" in error.message for error in instance_errors),
            [error.message for error in instance_errors],
        )

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
            # The launcher delegates to the docchain package; copy it too so the copied
            # launcher can import and re-invoke itself in the temp tree.
            shutil.copytree(LAB / "docchain", root / "tools" / "lab" / "docchain")
            errors = validate.validate_doc_chain_live(root)
            self.assertTrue(any("docs/features" in error.path for error in errors))
            (root / "docs" / "features").mkdir(parents=True)
            (root / "docs" / "features" / "drifted.md").write_text(
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
            "bug_id": "ISS-2026-01-02-a",
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
            "bug_id": "ISS-2026-01-02-b",
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
            "first_record": "ISS-2026-01-02-a",
            "occurrences": ["ISS-2026-01-02-a"],
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
                "first_record: ISS-2026-01-02-a\n"
                "occurrences:\n"
                "  - ISS-2026-01-02-a\n"
                "recorded_at: 2026-01-01T00:00:00Z\n"
                "---\n",
                encoding="utf-8",
            )
            errors = validate.validate_recurrence_markdown(path)
        self.assertTrue(any("filename must equal class_id" in error.message for error in errors))

    def test_bug_record_verified_requires_closure_criteria(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "ISS-2026-01-02-c",
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

    def test_bug_record_verified_requires_review_evidence_fields(self) -> None:
        # 0.13.0 added these as schema conditions; pin each one so a future loosening is red.
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "ISS-2026-01-01-d",
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
            "closure_criteria": "validate.py artifacts exits 0",
        }
        self.assertFalse(validator.validate(dict(base)))
        for field in ("reviewer", "review_decision", "regression_status"):
            data = dict(base)
            data.pop(field)
            errors = validator.validate(data)
            self.assertTrue(
                any(field in f"{error.path} {error.message}" for error in errors),
                [error.message for error in errors],
            )

    def test_bug_record_verified_requires_approved_review_and_passing_regression(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "ISS-2026-01-01-e",
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
            "closure_criteria": "validate.py artifacts exits 0",
        }
        for label, override in (
            ("review_decision", {"review_decision": "changes_requested"}),
            ("regression_status", {"regression_status": "not-run"}),
        ):
            errors = validator.validate(dict(base, **override))
            self.assertTrue(
                any(label in f"{error.path} {error.message}" for error in errors),
                [error.message for error in errors],
            )

    def test_bug_record_rejected_requires_rejection_reason(self) -> None:
        validator = validate.SchemaValidator(ROOT / "schemas" / "bug-record.schema.json")
        base = {
            "bug_id": "ISS-2026-01-01-f",
            "title": "t",
            "status": "rejected",
            "severity": "P2",
            "error_kind": "other",
            "attribution": "unknown",
            "provenance": "agentflow",
            "project": "p",
            "files": ["a.py"],
            "recorded_at": "2026-01-01T00:00:00Z",
        }
        errors = validator.validate(dict(base))
        self.assertTrue(any("rejection_reason" in f"{e.path} {e.message}" for e in errors))
        self.assertFalse(validator.validate(dict(base, rejection_reason="not a defect")))

    def test_bug_record_closed_states_require_change_log_section(self) -> None:
        body = "## 现象\nx\n\n## 根因\ny\n\n## 修复\nz\n"
        frontmatter = (
            "---\n"
            "bug_id: ISS-2026-01-01-g\n"
            "title: t\n"
            "status: fixed-pending-review\n"
            "severity: P2\n"
            "error_kind: other\n"
            "attribution: unknown\n"
            "provenance: agentflow\n"
            "project: p\n"
            "files:\n"
            "  - a.py\n"
            "recorded_at: 2026-01-01T00:00:00Z\n"
            "regression_status: pass\n"
            "---\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ISS-2026-01-01-g.md"
            path.write_text(frontmatter + body, encoding="utf-8")
            errors = validate.validate_bug_markdown(path)
            self.assertTrue(
                any("变更记录" in error.message for error in errors),
                [error.message for error in errors],
            )
            path.write_text(
                frontmatter + body + "\n## 变更记录\n2026-01-01 00:00 +00:00 · 修复落地 · unit test\n",
                encoding="utf-8",
            )
            self.assertEqual([error.message for error in validate.validate_bug_markdown(path)], [])

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
                "review_id: REV-2026-01-01-001\n"
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
            path = Path(temporary) / "EP-2026-01-01-001.json"
            record = {
                "schema_version": 1,
                "episode_id": "EP-2026-01-01-001",
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
            path.write_text(json.dumps(dict(record, episode_id="EP-2026-01-01-002")), encoding="utf-8")
            errors = validate.validate_episode_document(path)
            self.assertTrue(any("must equal episode_id" in error.message for error in errors))

    def test_examples_contract_declares_the_invalid_plan_family(self) -> None:
        # Regression for a silent gap: a case-sensitive glob once excluded the uppercase-named
        # invalid plan example, so the negative example never exercised the plan gate. The
        # historical fix is now structural — INVALID_EXAMPLES declares every negative example
        # and validate_examples requires each declared entry to exist and be rejected — so this
        # pin asserts the *declaration* (the discriminating fact), not a full re-run of the
        # examples gate, which `validate.py all` already executes (one full-gate re-run inside
        # the suite made `all` pay for the same linter subprocesses twice).
        from gate.examples import INVALID_EXAMPLES

        self.assertIn("PLAN-INVALID-002.md", INVALID_EXAMPLES)
        plan_negatives = [n for n, (kind, _) in INVALID_EXAMPLES.items() if kind == "plan"]
        self.assertTrue(plan_negatives, "the invalid-plan family must stay declared")

    def test_role_files_name_every_schema_required_field_and_heading(self) -> None:
        # T12: the role files' declared field lists and fixed sections must match what the
        # schemas/gate actually require; following the role literally cannot be gate-red.
        import gate.docs as docs_module

        for role, (schema_name, headings) in docs_module.ROLE_SCHEMA_CONTRACTS.items():
            schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            text = (ROOT / "agents" / f"{role}.md").read_text(encoding="utf-8")
            errors = docs_module.role_contract_findings(
                ROOT / "agents" / f"{role}.md", text, schema["required"], headings
            )
            self.assertEqual([], [error.message for error in errors])

    def test_role_contract_cross_check_catches_missing_field_and_heading(self) -> None:
        import gate.docs as docs_module

        errors = docs_module.role_contract_findings(
            Path("agents/example.md"),
            "`test_plan_id` 与 `title`；## 用例",
            ["test_plan_id", "title", "recorded_at"],
            ("## 用例", "## 流程疑点"),
        )
        messages = [error.message for error in errors]
        self.assertTrue(any("recorded_at" in message for message in messages), messages)
        self.assertTrue(any("## 流程疑点" in message for message in messages), messages)

    def test_correction_propagation_flags_unannotated_references(self) -> None:
        # T16: once CHANGELOG/issues retract an identifier, every other reference must carry
        # an erratum marker; the correction source itself is exempt.
        import gate.docs as docs_module

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs" / "features").mkdir(parents=True)
            (root / "CHANGELOG.md").write_text(
                "## 0.1.0\n\n- `GhostTests` 从未进入门禁，勘误。\n", encoding="utf-8"
            )
            (root / "docs" / "features" / "a.md").write_text(
                "`GhostTests` 覆盖了全部路径。\n", encoding="utf-8"
            )
            (root / "docs" / "features" / "b.md").write_text(
                "`GhostTests`（已勘误）不再作为证据。\n", encoding="utf-8"
            )
            errors = docs_module.correction_propagation_findings(root)
        messages = [error.message for error in errors]
        self.assertEqual(1, len(messages), messages)
        self.assertIn("a.md", errors[0].path)
        self.assertIn("GhostTests", messages[0])

    def test_doc_consistency_passes_on_the_current_tree(self) -> None:
        errors = validate.validate_doc_consistency()
        self.assertEqual(errors, [])

    def test_init_section_template_ships_markers_and_the_three_gate_clauses(self) -> None:
        # Init used to be prose-only, so each target repo invented its own section shape.
        # The template is now the carrier; losing a marker or a gate clause silently turns a
        # re-run into a full rewrite or drops the gate obligations from the repo rules.
        self.assertEqual(validate.validate_init_section_template(), [])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = [error.message for error in validate.validate_init_section_template(root)]
            self.assertTrue(any("repo-rules template is missing" in message for message in missing), missing)
            template = root / "skills" / "agentflow" / "templates" / "hub" / "repo-rules.md"
            template.parent.mkdir(parents=True)
            template.write_text(
                "<!-- agentflow:repo-rules:begin v0 -->\n"
                "<!-- agentflow:repo-rules:end -->\n",
                encoding="utf-8",
            )
            (root / "skills" / "agentflow" / "SKILL.md").write_text(
                "Init 见 templates/hub/repo-rules.md\n", encoding="utf-8"
            )
            messages = [error.message for error in validate.validate_init_section_template(root)]
            self.assertEqual(len(messages), 3, messages)
            self.assertTrue(all("lacks gate clause" in message for message in messages), messages)

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

    def test_shipped_plan_template_can_be_used_as_hybrid(self) -> None:
        template = ROOT / "skills/agentflow/templates/feature/plan/execution.md"
        lines: list[str] = []
        filled_tasks = 0
        for line in template.read_text(encoding="utf-8").splitlines():
            for task_id, dependency in (("T01", "—"), ("T02", "T01")):
                if line.startswith(f"| {task_id} |"):
                    line = (
                        f"| {task_id} | 验证模板 | QA | `src.py` | {dependency} |"
                        " 设计说明 | 可观察结果 | ☐ 未开始 | — |"
                    )
                    filled_tasks += 1
                    break
            lines.append(line)
        self.assertEqual(2, filled_tasks, "The real template must supply the task rows")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "PLAN-TEMPLATE-001.md"
            path.write_text(
                "---\nplan_id: PLAN-TEMPLATE-001\nplan_version: 0.1.0\n"
                "status: proposed\nobjective: 使用随插件交付的计划模板\n"
                "recorded_at: 2026-10-26T00:00:00Z\n---\n\n"
                + "\n".join(lines)
                + "\n",
                encoding="utf-8",
            )
            errors = validate.validate_plan_markdown(path)
        self.assertEqual([], [error.message for error in errors])

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

    def test_task_table_without_trailing_pipes_is_still_read(self) -> None:
        # T05: the gate carried its own row parser that demanded a trailing `|`, so a table
        # written without outer pipes (legal CommonMark) was invisible — a row with a free-text
        # status sailed through. The parser is now shared with docchain, and 依赖 is read by
        # column name, so an extra column before it must not be mistaken for the dependency.
        body = (
            "## 进展概览\n\n概述\n\n## 任务清单\n\n"
            "ID | 任务 | 优先级 | 负责人 | 代码落点 | 依赖 | 状态 | 证据回写\n"
            "--- | --- | --- | --- | --- | --- | --- | ---\n"
            "`T01` | 甲 | P0 | BE | a.ts | — | 乱写 | \n"
            "`T02` | 乙 | P0 | QA | b.ts | `T01` | ☐ 未开始 | \n"
            "\n## 验证命令\n\n```sh\necho x\n```\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "PLAN-TEST-005.md"
            path.write_text(
                "---\nplan_id: PLAN-TEST-005\nplan_version: 0.1.0\n"
                "status: proposed\nobjective: o\nrecorded_at: 2026-09-17T00:00:00Z\n---\n\n"
                + body,
                encoding="utf-8",
            )
            errors = validate.validate_plan_markdown(path)
        messages = [error.message for error in errors]
        self.assertTrue(any("乱写" in m and "T01" in m for m in messages), messages)
        self.assertFalse(any("unknown dependency" in m for m in messages), messages)
        self.assertFalse(any("T02" in m for m in messages), messages)

    def test_blocking_decision_is_read_from_the_column_not_the_prose(self) -> None:
        # T07 G2-AC-01 / G2-AC-02: the blocking flag is read from 是否阻塞 by name and accepts
        # both "阻塞/不阻塞" and "是/否". Scanning every cell for the substring 阻塞 both missed a
        # row that said "是" and invented blockers from prose that merely mentioned 阻塞.
        def errors_for(table: str) -> list[str]:
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "PLAN-TEST-006.md"
                path.write_text(
                    "---\nplan_id: PLAN-TEST-006\nplan_version: 0.1.0\n"
                    "status: approved\nobjective: o\nrecorded_at: 2026-09-17T00:00:00Z\n---\n\n"
                    "## 进展概览\n\n概述\n\n## 任务清单\n\n"
                    "| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |\n"
                    "| --- | --- | --- | --- | --- | --- | --- |\n"
                    "| `T01` | 甲 | P0 | a.ts | — | ☐ 未开始 | |\n"
                    "\n### 未决项\n\n"
                    + table
                    + "\n## 验证命令\n\n```sh\necho x\n```\n",
                    encoding="utf-8",
                )
                return [error.message for error in validate.validate_plan_markdown(path)]

        yes_row = (
            "| 编号 | 问题 | 状态 | 是否阻塞 |\n| --- | --- | --- | --- |\n"
            "| U-01 | 权限模型待定 | 尚未关闭 | 是 |\n"
        )
        self.assertTrue(any("U-01" in m for m in errors_for(yes_row)), "「是」must block approval")

        prose_row = (
            "| 编号 | 问题 | 状态 | 是否阻塞 |\n| --- | --- | --- | --- |\n"
            "| U-02 | 阻塞风险已登记，但本项不阻塞实施 | 尚未关闭 | 否 |\n"
        )
        self.assertFalse(
            any("U-02" in m for m in errors_for(prose_row)),
            "prose mentioning 阻塞 with 是否阻塞=否 must not block",
        )

        three_column = (
            "| 前置 | 关联任务 | 说明 |\n| --- | --- | --- |\n"
            "| V-F1 | T01 | 落点未核实 |\n"
        )
        self.assertTrue(
            any("V-F1" in m for m in errors_for(three_column)),
            "the official three-column form must enter the check",
        )

        unknown_row = (
            "| 编号 | 问题 | 状态 | 是否阻塞 |\n| --- | --- | --- | --- |\n"
            "| U-03 | 权限模型待定 | 尚未关闭 | 待定 |\n"
        )
        self.assertTrue(
            any("U-03" in m for m in errors_for(unknown_row)),
            "an unrecognised blocking value must fail closed",
        )

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
        relative = Path("docs/issues/归档/2026-01-01/ISS-2026-01-02-archived.md")
        frontmatter = {"bug_id": "ISS-2026-01-02-archived", "recorded_at": "2026-01-02T00:00:00Z"}
        errors = validate.validate_bug_layout(frontmatter, ROOT / relative, relative, {})
        self.assertEqual(
            [error.message for error in errors],
            ["date directory '2026-01-01' does not match recorded_at date 2026-01-02"],
        )

    def test_bug_layout_requires_stem_equals_bug_id_and_date_matches_recorded_at(self) -> None:
        # The id IS the filename stem (2026-10-28 rename): a record whose bug_id or date drifts
        # from its own name points at an id no other record resolves, so both are gate failures.
        relative = Path("docs/issues/ISS-2026-09-14-重命名口径.md")
        consistent = {"bug_id": "ISS-2026-09-14-重命名口径", "recorded_at": "2026-09-14T12:00:00+08:00"}
        self.assertEqual(validate.validate_bug_layout(consistent, ROOT / relative, relative, {}), [])
        drifted = {"bug_id": "ISS-2026-09-14-别的名字", "recorded_at": "2026-09-15T12:00:00+08:00"}
        messages = [e.message for e in validate.validate_bug_layout(drifted, ROOT / relative, relative, {})]
        self.assertIn(
            "filename stem must equal bug_id 'ISS-2026-09-14-别的名字' (the stem is the record id)",
            messages,
        )
        self.assertIn("filename date must match recorded_at date 2026-09-15", messages)

    def test_credentials_field_rejects_obvious_secret_shapes(self) -> None:
        """2026-10-29 拍板 C：只给 credentials 加 pattern，只覆盖该字段。

        Positive values describe the injection method ("session-injected env");
        the negative values are the shapes no legitimate plan/run should carry.
        """
        plan = {
            "test_plan_id": "TP-2026-10-29-001",
            "title": "t",
            "project": "p",
            "feature": "f",
            "target_revision": "r1",
            "credentials": "session-injected env (AF_TEST_ACCOUNT / AF_TEST_PASSWORD)；值永不落盘",
            "case_count": "1",
            "test_version": "1",
            "status": "active",
            "recorded_at": "2026-10-29T00:00:00+08:00",
        }
        run = {
            "test_run_id": "TR-2026-10-29-001",
            "title": "t",
            "project": "p",
            "test_plan_id": "TP-2026-10-29-001",
            "test_plan_version": "1",
            "target_revision": "r1",
            "environment": "local",
            "credentials": "session-injected env；值永不落盘",
            "summary_pass": "1",
            "summary_fail": "0",
            "summary_blocked": "0",
            "summary_not_run": "0",
            "decision": "pass",
            "recorded_at": "2026-10-29T00:00:00+08:00",
        }
        plan_validator = validate.SchemaValidator(ROOT / "schemas" / "test-plan.schema.json")
        run_validator = validate.SchemaValidator(ROOT / "schemas" / "test-run.schema.json")
        self.assertEqual(plan_validator.validate(plan), [])
        self.assertEqual(run_validator.validate(run), [])
        for allowed in ("token: injected via env", "api_key: vault-managed", "password: rotated by ops"):
            with self.subTest(allowed=allowed):
                self.assertEqual(plan_validator.validate({**plan, "credentials": allowed}), [])
                self.assertEqual(run_validator.validate({**run, "credentials": allowed}), [])
        for secret in (
            "sk-abcdefgh12345678",
            "ghp_abcdefgh12345678",
            "AKIAABCDEFGHIJKLMNOP",
            "Bearer abcdefgh12345678",
            "token=abcdef123456",
            "PASSWORD=abcdef123456",
            "SECRET=abcdef123456",
        ):
            with self.subTest(secret=secret):
                self.assertTrue(plan_validator.validate({**plan, "credentials": secret}))
                self.assertTrue(run_validator.validate({**run, "credentials": secret}))

    @staticmethod
    def _git(repository: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )



