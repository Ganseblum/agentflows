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
            for name in validate.EXPECTED_TEST_FILES:
                (tests_dir / name).write_text("", encoding="utf-8")
            (tests_dir / "smuggled_test.py").write_text("", encoding="utf-8")
            undeclared_errors = validate.validate_unit_tests(root)
            for name in validate.EXPECTED_TEST_FILES:
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
                "tests/test_gate_schema.py" in error.path and "declared test file is missing" in error.message
                for error in missing_declared_errors
            ),
            [str(error) for error in missing_declared_errors],
        )

    def test_empty_and_trivial_suites_fail_the_count_floor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests_dir = root / "tests"
            tests_dir.mkdir()
            for name in validate.EXPECTED_TEST_FILES:
                (tests_dir / name).write_text("# no tests here\n", encoding="utf-8")
            module = tests_dir / "test_gate_schema.py"
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
            (repo / "issues" / "归档" / "2026-09-15" / "ISS-2026-09-15-record.md").write_text(
                "x", encoding="utf-8"
            )
            record = repo / "issues" / "recurrence" / "ledger.md"
            errors = self._contained_reference_errors(
                repo, "see ../归档/2026-09-15/ISS-2026-09-15-record.md for evidence", record
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
            record = repo / "issues" / "ISS-2026-01-02-record.md"
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
            "bug_id: ISS-2026-01-01-escape\n"
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
            (repo / "docs" / "issues" / "ISS-2026-01-01-escape.md").write_text(bug, encoding="utf-8")
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
            for name in validate.EXPECTED_TEST_FILES:
                (tests / name).write_text("", encoding="utf-8")
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



