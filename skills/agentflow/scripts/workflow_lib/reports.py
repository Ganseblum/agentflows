"""Strict native report readers; process success alone is not case evidence."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from typing import Any

from .snapshots import WorkflowError


def _bad(message: str) -> WorkflowError:
    return WorkflowError("invalid-report", message, 1)


def _tap(text: str) -> list[dict[str, str]]:
    plans = []
    cases = []
    numbers = []
    for line in text.splitlines():
        if re.match(r"^\s*(?:not ok|ok)\s+\d+.*#\s*(?:SKIP|TODO)\b", line, re.IGNORECASE):
            raise _bad("TAP skip/todo, including nested cases, is not execution evidence")
        if line.startswith("Bail out!"):
            raise _bad("TAP bailed out")
        plan = re.fullmatch(r"1\.\.(\d+)(?:\s*#.*)?", line.strip())
        if plan and not line.startswith((" ", "\t")):
            plans.append(int(plan[1]))
            if re.search(r"#\s*(?:SKIP|TODO)\b", line, re.IGNORECASE):
                raise _bad("Skipped TAP plan is not execution evidence")
            continue
        result = re.fullmatch(r"(not ok|ok)\s+(\d+)(?:\s+-)?\s+(.+)", line)
        if result:
            name = result[3].strip()
            if re.search(r"#\s*(?:SKIP|TODO)\b", name, re.IGNORECASE):
                raise _bad("TAP skip/todo is not a passing behavior test")
            numbers.append(int(result[2]))
            cases.append(
                {"name": name, "status": "fail" if result[1] == "not ok" else "pass"}
            )
        elif re.match(r"^(?:not ok|ok)\b", line):
            raise _bad("Malformed or unnamed TAP result")
        elif line.strip() and not line.startswith((" ", "\t", "#", "TAP version ")):
            raise _bad("Non-TAP text outside diagnostics")
    if len(plans) != 1 or plans[0] < 1 or numbers != list(range(1, plans[0] + 1)):
        raise _bad(
            "TAP requires one nonempty plan and exactly its ordered result lines"
        )
    return cases


def _junit(text: str) -> list[dict[str, str]]:
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise _bad("JUnit declarations/entities are not accepted")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise _bad(f"Malformed JUnit XML: {exc}") from exc
    if root.tag.split("}")[-1] not in {"testsuite", "testsuites"}:
        raise _bad("JUnit root must be testsuite/testsuites")
    cases = []
    for node in root.iter():
        if node.tag.split("}")[-1] != "testcase":
            continue
        name = node.get("name", "").strip()
        classname = node.get("classname", "").strip()
        if not name:
            raise _bad("JUnit testcase has no name")
        tags = {child.tag.split("}")[-1] for child in node}
        if "skipped" in tags:
            raise _bad("Skipped JUnit testcase is not execution evidence")
        cases.append(
            {
                "name": f"{classname}::{name}" if classname else name,
                "status": "fail" if tags & {"failure", "error"} else "pass",
            }
        )
    # The optional suite counters must agree with actual direct/nested case nodes.
    for node in root.iter():
        if node.tag.split("}")[-1] not in {"testsuite", "testsuites"}:
            continue
        nested = [x for x in node.iter() if x.tag.split("}")[-1] == "testcase"]
        if "tests" in node.attrib:
            try:
                declared = int(node.attrib["tests"])
            except ValueError as exc:
                raise _bad("JUnit test count is not an integer") from exc
            if declared != len(nested):
                raise _bad("JUnit test count does not match testcase nodes")
        for field in ("failures", "errors"):
            if field in node.attrib:
                tag = "failure" if field == "failures" else "error"
                observed = sum(
                    any(child.tag.split("}")[-1] == tag for child in case)
                    for case in nested
                )
                try:
                    declared = int(node.attrib[field])
                except ValueError as exc:
                    raise _bad(f"JUnit {field} count is not an integer") from exc
                if declared != observed:
                    raise _bad(f"JUnit {field} count does not match testcase nodes")
        for field in ("skipped", "disabled"):
            if node.attrib.get(field, "0") not in {"0", "0.0"}:
                raise _bad("JUnit skipped/disabled cases are not accepted")
    return cases


def _go(text: str) -> list[dict[str, str]]:
    started: set[str] = set()
    packages: set[str] = set()
    ended_packages: set[str] = set()
    package_results: dict[str, str] = {}
    results: dict[str, str] = {}
    result_packages: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise _bad("Go report contains a non-JSON line") from exc
        if not isinstance(event, dict) or not isinstance(event.get("Action"), str):
            raise _bad("Malformed Go test event")
        package, test, action = event.get("Package"), event.get("Test"), event["Action"]
        if not isinstance(package, str) or not package:
            raise _bad("Go test event has no package")
        packages.add(package)
        if not test:
            if action in {"pass", "fail", "skip"}:
                if package in ended_packages or action == "skip":
                    raise _bad("Duplicate/skipped Go package completion")
                ended_packages.add(package)
                package_results[package] = action
            continue
        if not isinstance(test, str):
            raise _bad("Go test name must be a string")
        name = package + "/" + test
        if action == "run":
            if name in started:
                raise _bad("Duplicate Go test execution")
            started.add(name)
        elif action in {"pass", "fail", "skip"}:
            if action == "skip" or name in results or name not in started:
                raise _bad("Skipped, duplicate or unstarted Go test result")
            results[name] = action
            result_packages[name] = package
    if not started or set(results) != started or packages != ended_packages:
        raise _bad("Go report is empty or lacks terminal test/package events")
    for package, status in package_results.items():
        test_failures = any(result_packages[name] == package and result == "fail"
                            for name, result in results.items())
        if (status == "fail") != test_failures:
            raise _bad("Go package status does not match its named test results")
    return [{"name": name, "status": status} for name, status in results.items()]


def _jest(text: str) -> list[dict[str, str]]:
    try:
        report = json.loads(text)
    except json.JSONDecodeError as exc:
        raise _bad(f"Malformed Jest JSON: {exc}") from exc
    if not isinstance(report, dict) or not isinstance(report.get("testResults"), list):
        raise _bad("Jest report must contain testResults")
    cases: list[dict[str, str]] = []
    for suite in report["testResults"]:
        if not isinstance(suite, dict) or not isinstance(
            suite.get("assertionResults"), list
        ):
            raise _bad("Jest suite lacks assertionResults")
        assertions = suite["assertionResults"]
        if suite.get("testExecError") or not assertions:
            raise _bad("Jest suite failed to execute named assertions")
        suite_status = "failed" if any(case.get("status") == "failed" for case in assertions
                                       if isinstance(case, dict)) else "passed"
        if suite.get("status") != suite_status:
            raise _bad("Jest suite status does not match assertion results")
        for case in suite["assertionResults"]:
            if not isinstance(case, dict) or not isinstance(case.get("fullName"), str):
                raise _bad("Jest assertion lacks exact fullName")
            status = case.get("status")
            if status not in {"passed", "failed"}:
                raise _bad("Jest pending/todo/unknown assertions are not accepted")
            cases.append(
                {
                    "name": case["fullName"],
                    "status": "pass" if status == "passed" else "fail",
                }
            )
    counts = {
        "numTotalTests": len(cases),
        "numPassedTests": sum(case["status"] == "pass" for case in cases),
        "numFailedTests": sum(case["status"] == "fail" for case in cases),
    }
    for key, count in counts.items():
        if type(report.get(key)) is not int or report[key] != count:
            raise _bad(f"Jest {key} does not match actual assertion results")
    if report.get("numPendingTests", 0) != 0 or report.get("numTodoTests", 0) != 0:
        raise _bad("Jest pending/todo count is nonzero")
    if type(report.get("success")) is not bool or report["success"] != all(
        case["status"] == "pass" for case in cases
    ):
        raise _bad("Jest success does not match assertion results")
    return cases


def parse_report(reporter: str, text: str) -> list[dict[str, str]]:
    """Read complete native case records, rejecting empty/duplicate/skipped evidence."""
    parsers: dict[str, Any] = {"tap": _tap, "junit": _junit, "go": _go, "jest": _jest}
    if reporter not in parsers:
        raise WorkflowError(
            "unsupported-reporter", f"Unsupported native reporter: {reporter}"
        )
    cases = parsers[reporter](text)
    names = [case["name"] for case in cases]
    if not names or any(not name.strip() for name in names):
        raise _bad("Report has no named test cases")
    if len(set(names)) != len(names):
        raise _bad("Report case names are not unique")
    return cases
