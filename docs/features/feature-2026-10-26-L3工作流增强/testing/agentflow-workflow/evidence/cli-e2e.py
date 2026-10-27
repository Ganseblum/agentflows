"""Reproduce the public CLI against disposable projects and an actual Node test runner."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def exercise(tool: Path, label: str, destination: Path, transcript: list[str]) -> dict:
    temp_root = "/tmp" if Path("/tmp").is_dir() else None
    with tempfile.TemporaryDirectory(prefix="agentflow-native-e2e-", dir=temp_root) as name:
        project = Path(name)
        (project / "src").mkdir()
        (project / "tests").mkdir()
        (project / "plan.md").write_text("# Confirmed behavior\nThe public value function returns 2.\n")
        (project / "src/value.cjs").write_text("module.exports = () => 1;\n")
        (project / "tests/value.test.cjs").write_text(
            "const test = require('node:test');\n"
            "const assert = require('node:assert/strict');\n"
            "const value = require('../src/value.cjs');\n"
            "test('returns confirmed value', () => assert.equal(value(), 2));\n"
        )
        for command in [
            ["git", "init"], ["git", "add", "."],
            ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "commit", "-m", "fixture"],
        ]:
            result = subprocess.run(command, cwd=project, text=True, capture_output=True, check=True)
            transcript.append(json.dumps(command) + "\n" + result.stdout + result.stderr)
        state = project / ".git/agentflow"
        state.mkdir()

        def call(args, expected=0):
            argv = [sys.executable, str(tool), *map(str, args)]
            result = subprocess.run(argv, cwd=project, text=True, capture_output=True, timeout=30)
            transcript.append("COMMAND " + json.dumps(argv, ensure_ascii=False) + "\n" +
                              result.stdout + result.stderr + f"\nEXIT_CODE={result.returncode}\n")
            if result.returncode != expected:
                raise AssertionError(transcript[-1])
            value = json.loads(result.stdout)
            print(label, args[0], "EXIT_CODE=" + str(result.returncode), value["status"], flush=True)
            return value

        node = shutil.which("node")
        if node is None:
            raise RuntimeError("This reproduction needs the actual Node test runner; do not fake its result")
        tasks = [
            {"id": "preflight", "depends_on": [], "argv": [node, "--version"], "cwd": ".",
             "timeout_seconds": 10, "kind": "preflight", "reporter": "exit", "cases": []},
            {"id": "target", "depends_on": ["preflight"],
             "argv": [node, "--test", "--test-reporter=tap", "tests/value.test.cjs"], "cwd": ".",
             "timeout_seconds": 10, "kind": "test", "reporter": "tap",
             "cases": [{"id": "TC-VALUE-001", "report_name": "returns confirmed value"}]},
        ]

        def seal(tag, declared_tasks):
            request = state / (tag + ".request.json")
            sealed = state / (tag + ".sealed.json")
            request.write_text(json.dumps({"plan": "plan.md", "allowed_writes": ["src/value.cjs"],
                                           "tasks": declared_tasks}))
            result = call(["seal", "--root", project, "--input", request, "--output", sealed])
            return sealed, result["evidence"]["fingerprint"]

        sealed, fingerprint = seal("native", tasks)
        common = ["--root", project, "--sealed", sealed, "--fingerprint", fingerprint]
        call(["verify", *common])
        call(["run", *common, "--output", state / "red", "--phase", "red"])
        red = json.loads((state / "red/result.json").read_text())
        assert red["tasks"][1]["cases"][0]["status"] == "fail"
        assert "AssertionError" in (state / "red/target.stdout").read_text()
        (project / "src/value.cjs").write_text("module.exports = () => 2;\n")
        call(["verify", *common])
        call(["run", *common, "--output", state / "green", "--phase", "green"])
        green = json.loads((state / "green/result.json").read_text())
        assert green["tasks"][1]["cases"][0]["status"] == "pass"
        assert green["coverage_status"] == "needs_review"

        plan = (project / "plan.md").read_bytes()
        (project / "plan.md").write_text("unconfirmed replacement")
        call(["verify", *common], expected=3)
        (project / "plan.md").write_bytes(plan)
        (project / "unexpected.txt").write_text("outside planned writes")
        call(["verify", *common], expected=3)
        (project / "unexpected.txt").unlink()

        bad = {"id": "bad", "depends_on": [], "argv": [sys.executable, "-c", "raise SystemExit(1)"],
               "cwd": ".", "timeout_seconds": 5, "kind": "preflight", "reporter": "exit", "cases": []}
        dependent = {**tasks[1], "id": "dependent", "depends_on": ["bad"],
                     "cases": [{"id": "TC-DEPENDENT", "report_name": "returns confirmed value"}]}
        independent = {**tasks[1], "id": "independent", "depends_on": [],
                       "cases": [{"id": "TC-INDEPENDENT", "report_name": "returns confirmed value"}]}
        split, split_fp = seal("dependencies", [bad, dependent, independent])
        call(["run", "--root", project, "--sealed", split, "--fingerprint", split_fp,
              "--output", state / "dependencies"], expected=1)
        split_results = json.loads((state / "dependencies/result.json").read_text())
        assert {x["id"]: x["status"] for x in split_results["tasks"]} == {
            "bad": "fail", "dependent": "blocked", "independent": "pass"}

        mapping = {"files": [
            {"path": "plan.md", "kind": "excluded", "reason": "confirmed plan"},
            {"path": "src/value.cjs", "kind": "production"},
            {"path": "tests/value.test.cjs", "kind": "test"}],
            "features": [{"id": "value", "entrypoint": "public value function", "acceptance": "plan.md",
                          "source_files": ["src/value.cjs"], "tests": [
                              {"id": "TC-VALUE-001", "name": "returns confirmed value",
                               "path": "tests/value.test.cjs", "layer": "unit", "planned": False}],
                          "not_applicable": {"integration": "pure calculation", "e2e": "no standalone user journey"}}],
            "batches": [{"id": "first", "features": ["value"], "depends_on": []}]}
        map_file = state / "map.json"
        map_file.write_text(json.dumps(mapping))
        assert call(["inventory", "--root", project, "--input", map_file])["evidence"]["coverage_status"] == "needs_review"

        target, content = state / "AGENTS.md", state / "rules.md"
        target.write_bytes(b"user header\n<!-- begin old -->\nold\n<!-- end -->\nuser tail\n")
        content.write_text("new rule\n")
        preview = state / "managed.json"
        result = call(["managed-preview", "--target", target, "--content", content, "--output", preview,
                       "--begin-marker", "<!-- begin old -->", "--end-marker", "<!-- end -->",
                       "--new-begin-marker", "<!-- begin new -->"])
        applied = call(["managed-apply", "--preview", preview, "--fingerprint", result["evidence"]["fingerprint"]])
        assert target.read_bytes() == b"user header\n<!-- begin new -->\nnew rule\n<!-- end -->\nuser tail\n"
        assert Path(applied["evidence"]["backup"]).is_file()
        stale = state / "stale.json"
        result = call(["managed-preview", "--target", target, "--content", content, "--output", stale])
        target.write_text("later user edit")
        call(["managed-apply", "--preview", stale, "--fingerprint", result["evidence"]["fingerprint"]], expected=3)
        assert target.read_text() == "later user edit"

        destination.mkdir(parents=True, exist_ok=False)
        for directory in ("red", "green", "dependencies"):
            shutil.copytree(state / directory, destination / directory)
        return {"tool": str(tool), "label": label, "native_red_observed": True,
                "native_green_observed": True, "coverage_status": "needs_review",
                "drift_rejected": True, "dependency_split_verified": True,
                "inventory_checked": True, "managed_preserved_user_content": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True, type=Path)
    parser.add_argument("--secondary-tool", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    transcript: list[str] = []
    results = []
    try:
        for label, tool in [("source", args.tool), ("runtime", args.secondary_tool)]:
            results.append(exercise(tool.resolve(), label, output / label, transcript))
    finally:
        (output / "commands.txt").write_text("\n\n".join(transcript))
    (output / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("NATIVE_E2E_PASS", output, flush=True)


if __name__ == "__main__":
    main()
