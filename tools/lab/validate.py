#!/usr/bin/env python3
"""Validate Agentflow contracts, examples, and record artifacts.

This intentionally uses only the Python standard library. It implements the small
Draft 2020-12 vocabulary used by the repository's contracts and adds explicit
cross-document checks that JSON Schema cannot express conveniently.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate.checks
import gate.common
import gate.docs
import gate.examples
import gate.installed
import gate.manifests
import gate.plan
import gate.records
import gate.reports
import gate.schema
import gate.testing
import gate.workspace

from gate.common import (
    BUG_RECORD_SCHEMA,
    EPISODE_SCHEMA,
    EXPECTED_TEST_FILES,
    INSTALLED_COMPONENTS,
    INSTALLED_FILES,
    LIVE_RECORD_ROOTS,
    MANIFEST_POINTERS,
    MIN_DOC_CHAIN_SELF_TEST_CASES,
    MIN_UNIT_TEST_COUNT,
    PROTECTED_PATHS_FILE,
    QUALIFIED_REF_PATTERN,
    RECURRENCE_SCHEMA,
    REQUIRED_PROTECTED_PATHS,
    REVIEW_SCHEMA,
    RFC3339_DATE_TIME,
    ROOT,
    TEST_PLAN_SCHEMA,
    TEST_RUN_SCHEMA,
    ValidationError,
    dated_id_errors,
    files_entry_errors,
    heading_present,
    is_separator_row,
    is_type,
    json_equal_key,
    json_values_equal,
    load_json,
    load_record_markdown,
    parse_frontmatter,
    parse_plan_task_row,
    parse_rfc3339_date_time,
    path_inside_root,
    read_document_text,
    record_date_of,
    validate_timestamp_order,
    version_tuple,

)
from gate.schema import (
    IMPROVEMENT_SCHEMA_NAMES,
    SCHEMA_PATHS,
    SchemaValidator,
    check_schema_refs,
    iter_schema_paths,
    validate_schemas,

)
from gate.plan import (
    PLAN_REQUIRED_HEADINGS,
    PLAN_TASK_ID_PATTERN,
    PLAN_TASK_STATUSES,
    PLAN_TASK_STATUS_MARKS,
    validate_plan_markdown,

)
from gate.records import (
    BODY_PATH_PATTERN,
    BUG_ARCHIVE_DIR,
    BUG_FILENAME_PATTERN,
    BUG_REQUIRED_HEADINGS,
    RECURRENCE_DIR,
    URL_PATTERN,
    excerpt_follows_citation,
    prose_without_quotations,
    validate_body_references,
    validate_bug_layout,
    validate_bug_markdown,
    validate_episode_document,
    validate_external_excerpts,
    validate_recurrence_markdown,
    validate_review_markdown,

)
from gate.testing import (
    NO_EVIDENCE_CELLS,
    TEST_CASE_ID_PATTERN,
    TEST_CASE_LEVELS,
    TEST_CASE_PRIORITIES,
    TEST_PLAN_REQUIRED_HEADINGS,
    TEST_RESULT_STATUSES,
    TEST_RUN_REQUIRED_HEADINGS,
    parse_test_case_registry,
    validate_test_plan_markdown,
    validate_test_run_markdown,

)
from gate.workspace import (
    FEATURE_SEGMENTS,
    is_project_feature_slug,
    validate_workspace_artifacts,

)
from gate.docs import (
    FENCED_BLOCK_PATTERN,
    HISTORICAL_DOC_CARRIERS,
    INLINE_CODE_PATTERN,
    LINK_TARGET_PATTERN,
    MIGRATED_PATH_TOKENS,
    PATH_RESIDUE_TOKENS,
    PRE_050_PLAN_CONTRACT_MARKERS,
    RETIRED_PATH_TOKENS,
    ROLE_NAME_PATTERN,
    SKILL_ROLE_PATTERN,
    VERSION_LITERAL_PATTERN,
    VERSION_PROSE_FILES,
    live_doc_paths,
    strip_quotation_fences,
    validate_agents_md_plan_contract,
    validate_doc_consistency,
    validate_live_doc_references,

)
from gate.manifests import (
    load_protected_paths,
    manifest_value,
    validate_manifests,
    validate_protected_paths,

)
from gate.installed import (
    component_manifest,
    installed_plugin_roots,
    plugin_identity,
    validate_installed,

)
from gate.examples import (
    INVALID_EXAMPLES,
    example_test_plans,
    validate_examples,
    validate_invalid_plan_example,
    validate_invalid_test_run_example,

)
from gate.checks import (
    DOC_CHAIN_FEATURE_SURFACE,
    DOC_CHAIN_LIVE_ROOTS,
    validate_doc_chain,
    validate_doc_chain_live,
    validate_unit_tests,

)
from gate.reports import (
    bug_report,
    recurrence_report,

)

ROOT = Path(__file__).resolve().parents[2]


# The regression tests rebind `validate.ROOT` to a fixture tree and expect the check
# functions to follow. The check bodies live in the gate submodules and read their own
# module-global ROOT at call time, so a rebind here is propagated to each of them.
_GATE_MODULES = (
    gate.common,
    gate.schema,
    gate.plan,
    gate.records,
    gate.testing,
    gate.workspace,
    gate.docs,
    gate.manifests,
    gate.installed,
    gate.examples,
    gate.checks,
    gate.reports,
)


class _RootAwareModule(types.ModuleType):
    """Propagate a `validate.ROOT` rebind to the gate submodules."""

    def __setattr__(self, name: str, value: object) -> None:
        super().__setattr__(name, value)
        if name == "ROOT":
            for module in _GATE_MODULES:
                setattr(module, "ROOT", value)


sys.modules[__name__].__class__ = _RootAwareModule


def report(label: str, errors: list[ValidationError]) -> bool:
    if errors:
        print(f"FAIL {label} ({len(errors)} error(s))")
        for error in errors:
            print(f"  - {error}")
        return False
    print(f"PASS {label}")
    return True


def main(argv: list[str] | None = None) -> int:
    # Hard floor: tests/ use PEP 604 syntax without a future import, so an
    # interpreter below 3.10 cannot run the suite — refuse loudly instead of
    # reporting 8 PASS plus a misleading tests failure.
    if sys.version_info < (3, 10):
        found = ".".join(str(part) for part in sys.version_info[:3])
        sys.stderr.write(
            f"validate.py: interpreter too old: found Python {found}, require >= 3.10. "
            "The default `python3` may be the Xcode CLT 3.9; use `python3.12` explicitly. "
            "No check was run.\n"
        )
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        choices=[
            "schemas",
            "examples",
            "artifacts",
            "protected",
            "manifests",
            "docs",
            "tests",
            "doc_chain",
            "doc_chain_live",
            "installed",
            "all",
            "report",
            "recurrence",
        ],
        help="contract set to validate, or 'report'/'recurrence' for retrospective tables",
    )
    parser.add_argument(
        "--path",
        dest="installed_path",
        help="for 'installed', compare against this plugin copy instead of the ZCode cache",
    )
    parser.add_argument("--project", dest="report_project", help="for 'report', only records of this project")
    parser.add_argument("--status", dest="report_status", help="for 'report', only records with this status")
    parser.add_argument(
        "--provenance", dest="report_provenance", help="for 'report', only records with this provenance"
    )
    args = parser.parse_args(argv)

    if args.target == "report":
        errors = bug_report(
            project=args.report_project, status=args.report_status, provenance=args.report_provenance
        )
        return 1 if errors else 0

    if args.target == "recurrence":
        errors = recurrence_report()
        return 1 if errors else 0

    if args.target == "installed":
        status, errors = validate_installed(args.installed_path)
        if status == "skip":
            print("SKIP installed (no local plugin install found; nothing to compare)")
            return 0
        return 0 if report("installed", errors) else 1

    checks = {
        "schemas": [("schemas", validate_schemas)],
        "examples": [("examples", validate_examples)],
        "artifacts": [("artifacts", validate_workspace_artifacts)],
        "protected": [("protected", validate_protected_paths)],
        "manifests": [("manifests", validate_manifests)],
        "docs": [("docs", validate_doc_consistency)],
        "tests": [("tests", validate_unit_tests)],
        "doc_chain": [("doc_chain", validate_doc_chain)],
        "doc_chain_live": [("doc_chain_live", validate_doc_chain_live)],
        "all": [
            ("schemas", validate_schemas),
            ("examples", validate_examples),
            ("artifacts", validate_workspace_artifacts),
            ("protected", validate_protected_paths),
            ("manifests", validate_manifests),
            ("docs", validate_doc_consistency),
            ("tests", validate_unit_tests),
            ("doc_chain", validate_doc_chain),
            ("doc_chain_live", validate_doc_chain_live),
        ],
    }[args.target]

    success = True
    for label, check in checks:
        success = report(label, check()) and success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
