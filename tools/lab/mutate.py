#!/usr/bin/env python3
"""Mutation testing for the validate.py gate (feature-2026-10-13-质量提升, T05 / M-B).

Each mutation rewrites one line or one statement of a gate module inside a throwaway copy of
the repository, runs the check that owns it, and classifies the outcome:

  已杀死  the check exits non-zero (a crash is labelled 崩溃 in the detail column)
  存活    the check still exits zero
  超时    the check exceeded MUTATE_TIMEOUT_S; counted as 存活 and labelled
  无效    the rewrite did not change the file, or the anchor was not unique; this is an error

The real working tree is only ever read. Every rewrite happens in a `cp -R` copy that is removed
afterwards. Usage: see `--help`.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = Path("/tmp/mutation-report")
MUTATE_TIMEOUT_S = 120

# Check name -> argv (after `python3 -B`) run from the root of the copy.
CHECKS: dict[str, list[str]] = {
    "schemas": ["tools/lab/validate.py", "schemas"],
    "examples": ["tools/lab/validate.py", "examples"],
    "artifacts": ["tools/lab/validate.py", "artifacts"],
    "protected": ["tools/lab/validate.py", "protected"],
    "manifests": ["tools/lab/validate.py", "manifests"],
    "docs": ["tools/lab/validate.py", "docs"],
    "tests": ["tools/lab/validate.py", "tests"],
    "doc_chain": ["tools/lab/validate.py", "doc_chain"],
    "doc_chain_live": ["tools/lab/validate.py", "doc_chain_live"],
    "doc_chain_selftest": ["tools/lab/doc_chain.py", "--self-test"],
}

# Operators. Line operators rewrite the single line that contains the anchor; statement
# operators rewrite the AST node the anchor identifies.
OPERATORS: dict[str, str] = {
    "invert_cmp": "反转首个比较符：!=↔==、<↔>=、>↔<=",
    "relax_strict": "放宽首个严格比较：< → <=，> → >=",
    "disable_if": "条件短路：`if …:` → `if False:`",
    "drop_enum_member": "枚举元组裁掉末个成员",
    "empty_iter": "循环空迭代：`for … in X:` → `for … in ():`",
    "drop_statement": "errors.append/extend 语句 → pass",
    "drop_continue": "continue → pass",
}

# Inventory of gate check items: name -> (file, what the item decides). Every item needs at least
# one mutation or an EXEMPT entry; coverage_gaps() enforces this.
ITEMS: dict[str, tuple[str, str]] = {
    "plan.approval-gate": ("tools/lab/gate/plan.py", "未决项审批门（approved 计划不得含未关闭阻塞决策）"),
    "plan.approved-scope": ("tools/lab/gate/plan.py", "审批门触发条件 status == approved"),
    "plan.status-enum": ("tools/lab/gate/plan.py", "任务状态枚举"),
    "plan.dep-cycle": ("tools/lab/gate/plan.py", "依赖环检测"),
    "plan.dep-resolve": ("tools/lab/gate/plan.py", "依赖引用须解析到已列任务"),
    "plan.task-id-unique": ("tools/lab/gate/plan.py", "任务 ID 唯一"),
    "plan.row-width": ("tools/lab/gate/plan.py", "任务表行识别（列数下限）"),
    "records.bug-verified-review": ("tools/lab/gate/records.py", "bug 记录 verified 须含审查节"),
    "records.bug-open-fix": ("tools/lab/gate/records.py", "bug 记录非 open 须含修复节"),
    "records.bug-layout": ("tools/lab/gate/records.py", "bug 记录布局（扁平 / 归档目录）"),
    "records.recurrence-name": ("tools/lab/gate/records.py", "recurrence 台账文件名 = class_id"),
    "workspace.issues-layout": ("tools/lab/gate/workspace.py", "issues/ 下未知条目拒绝"),
    "workspace.issues-depth": ("tools/lab/gate/workspace.py", "issues/ 子目录深度"),
    "workspace.files-walk": ("tools/lab/gate/workspace.py", "bug 记录 files 条目接入校验"),
    "workspace.occurrence-unique": ("tools/lab/gate/workspace.py", "class occurrence 唯一"),
    "common.files-containment": ("tools/lab/gate/common.py", "files 条目：绝对路径与越界拒绝"),
    "schema.if-then-else": ("tools/lab/gate/schema.py", "if/then/else 语义"),
    "schema.enum": ("tools/lab/gate/schema.py", "enum 约束"),
    "schema.pattern": ("tools/lab/gate/schema.py", "pattern 约束"),
    "schema.required": ("tools/lab/gate/schema.py", "required 约束"),
    "schema.min-length": ("tools/lab/gate/schema.py", "minLength 约束"),
    "schema.max-items": ("tools/lab/gate/schema.py", "maxItems 边界"),
    "schema.contains": ("tools/lab/gate/schema.py", "contains / minContains 计数"),
    "testing.case-count": ("tools/lab/gate/testing.py", "用例数 case_count 与注册表相等"),
    "testing.summary": ("tools/lab/gate/testing.py", "summary_* 与结果表相等"),
    "testing.fail-evidence": ("tools/lab/gate/testing.py", "fail/blocked 行须带证据"),
    "testing.decision-pass": ("tools/lab/gate/testing.py", "decision pass 须零 fail/blocked"),
    "testing.case-registry": ("tools/lab/gate/testing.py", "结果行须属于计划注册表"),
    "docs.version-prose": ("tools/lab/gate/docs.py", "版本散文守卫"),
    "docs.retired-path": ("tools/lab/gate/docs.py", "退役路径 token 扫描"),
    "docs.broken-link": ("tools/lab/gate/docs.py", "相对 Markdown 链接须可解析"),
    "manifests.version-agree": ("tools/lab/gate/manifests.py", "五份 manifest 版本一致"),
    "manifests.name-agree": ("tools/lab/gate/manifests.py", "五份 manifest 名称一致"),
    "manifests.protected-coverage": ("tools/lab/gate/manifests.py", "受保护清单覆盖必需条目"),
    "checks.unit-floor": ("tools/lab/gate/checks.py", "单元测试数量下限"),
    "checks.unit-empty": ("tools/lab/gate/checks.py", "空测试套件拒绝"),
    "checks.skip-guard": ("tools/lab/gate/checks.py", "跳过的测试拒绝"),
    "checks.doc-chain-pair": ("tools/lab/gate/checks.py", "doc_chain 自测 N/M 相等"),
    "checks.doc-chain-floor": ("tools/lab/gate/checks.py", "doc_chain 自测用例数下限"),
    "reports.bug_report": ("tools/lab/gate/reports.py", "bug 记录报告表（纯输出）"),
    "reports.recurrence_report": ("tools/lab/gate/reports.py", "recurrence 报告表（纯输出）"),
    "doc_chain.C1": ("tools/lab/doc_chain.py", "C1 结构：阶段目录须有真实文档"),
    "doc_chain.C2": ("tools/lab/doc_chain.py", "C2 入口门禁：README 含两个评审门"),
    "doc_chain.C3": ("tools/lab/doc_chain.py", "C3 反审门：阻塞行不得未关闭"),
    "doc_chain.C4": ("tools/lab/doc_chain.py", "C4 design/be 图形与契约表"),
    "doc_chain.C5": ("tools/lab/doc_chain.py", "C5 契约闭合：be 契约 id 须出现在 fe"),
    "doc_chain.C6": ("tools/lab/doc_chain.py", "C6 fe 异常边界矩阵"),
    "doc_chain.C7": ("tools/lab/doc_chain.py", "C7 fe 线框数量或原型"),
    "doc_chain.C9": ("tools/lab/doc_chain.py", "C9 plan 分支策略节"),
    "doc_chain.C10": ("tools/lab/doc_chain.py", "C10 mermaid 围栏闭合"),
}

# Items exempt from mutation, with the reason. Keep this list short.
EXEMPT: dict[str, str] = {
    "reports.bug_report": "纯输出：只向 stdout 打印表格，返回值恒为空列表，不产生门禁错误，变异后的通过/失败结论无从观察",
    "reports.recurrence_report": "纯输出：只打印台账表，返回空列表；validate.py recurrence 的退出码恒为 0，不是门禁检查项",
    "checks.skip-guard": "skip>0 本身就令真实门变红（跳过的测试被拒绝，仓库测试自禁跳过），=True 的单元测试输出又不带 skipped=N 记号——两个可观测状态在可用语料中都不存在",
}


@dataclass(frozen=True)
class Mutation:
    id: str
    item: str
    file: str
    anchor: str
    op: str
    check: str


# (item, anchor, operator, check). File comes from ITEMS. Ids are assigned in order.
SPECS: list[tuple[str, str, str, str]] = [
    ("plan.approval-gate", "if is_blocking and not closed:", "disable_if", "examples"),
    ("plan.approved-scope", 'if frontmatter.get("status") == "approved":', "invert_cmp", "examples"),
    ("plan.status-enum", 'PLAN_TASK_STATUSES = (', "drop_enum_member", "artifacts"),
    ("plan.status-enum", "if status_word not in PLAN_TASK_STATUSES:", "disable_if", "examples"),
    ("plan.dep-cycle", "if node in visiting:", "disable_if", "examples"),
    ("plan.dep-resolve", "if dep not in known:", "disable_if", "examples"),
    ("plan.task-id-unique", "if task_id in task_rows:", "disable_if", "examples"),
    ("plan.row-width", "if len(cells) < 5:", "relax_strict", "examples"),
    ("records.bug-verified-review", 'if frontmatter.get("status") == "verified" and not heading_present(body, "## 审查"):', "invert_cmp", "examples"),
    ("records.bug-open-fix", 'if frontmatter.get("status") != "open" and not heading_present(body, "## 修复"):', "invert_cmp", "artifacts"),
    ("records.recurrence-name", 'if path.stem != frontmatter.get("class_id"):', "disable_if", "tests"),
    ("records.bug-layout", "elif len(parts) != 3:", "invert_cmp", "artifacts"),
    ("workspace.issues-layout", "unexpected entry under issues/; live issue records", "drop_statement", "tests"),
    ("workspace.issues-depth", "if n > 1 and not archived:", "invert_cmp", "artifacts"),
    ("workspace.files-walk", "files_entry_errors(entry, path)", "drop_statement", "tests"),
    ("workspace.occurrence-unique", 'if occurrence in used_occurrences.setdefault(class_id, {}):', "disable_if", "artifacts"),
    ("common.files-containment", "if Path(entry).is_absolute():", "disable_if", "tests"),
    ("common.files-containment", "if path_inside_root(entry) is None:", "disable_if", "tests"),
    ("schema.if-then-else", 'if "if" in schema:', "disable_if", "tests"),
    ("schema.enum", 'if "enum" in schema and not any', "disable_if", "tests"),
    ("schema.pattern", 'if "pattern" in schema:', "disable_if", "tests"),
    ("schema.required", "if required not in instance:", "disable_if", "tests"),
    ("schema.min-length", 'if "minLength" in schema and len(instance) < schema["minLength"]:', "invert_cmp", "artifacts"),
    ("schema.max-items", 'if "maxItems" in schema and len(instance) > schema["maxItems"]:', "relax_strict", "tests"),
    ("schema.contains", "if matches < minimum:", "invert_cmp", "tests"),
    ("testing.case-count", "int(declared_count) != len(cases)", "invert_cmp", "examples"),
    ("testing.summary", "int(declared) != observed:", "invert_cmp", "examples"),
    ("testing.fail-evidence", 'if status_cell in ("fail", "blocked") and evidence in NO_EVIDENCE_CELLS:', "disable_if", "tests"),
    ("testing.decision-pass", 'if frontmatter.get("decision") == "pass" and', "invert_cmp", "examples"),
    ("testing.case-registry", 'if case_id not in plan["cases"]:', "disable_if", "tests"),
    ("docs.version-prose", "for match in VERSION_LITERAL_PATTERN.finditer(text):", "empty_iter", "tests"),
    ("docs.retired-path", "if not preceded_by_word:", "disable_if", "tests"),
    ("docs.broken-link", "if not (path.parent / target_path).exists():", "disable_if", "tests"),
    ("manifests.version-agree", "if version != reference:", "invert_cmp", "tests"),
    ("manifests.version-agree", "if len(set(versions.values())) > 1:", "invert_cmp", "tests"),
    ("manifests.name-agree", "if plugin_name != reference:", "invert_cmp", "tests"),
    ("manifests.protected-coverage", "if not covered:", "disable_if", "tests"),
    ("checks.unit-floor", "if count < MIN_UNIT_TEST_COUNT:", "invert_cmp", "tests"),
    ("checks.unit-empty", "if count == 0:", "invert_cmp", "tests"),
    ("checks.doc-chain-pair", "if passed != total or total == 0:", "invert_cmp", "doc_chain"),
    ("checks.doc-chain-floor", "if total < MIN_DOC_CHAIN_SELF_TEST_CASES:", "invert_cmp", "doc_chain"),
    ("doc_chain.C1", "下没有任何有效文档", "drop_statement", "doc_chain_selftest"),
    ("doc_chain.C2", 'if gate not in rtext:', "disable_if", "doc_chain_selftest"),
    ("doc_chain.C3", 'if not (line.lstrip().startswith("|") and "阻塞" in line and "☐" in line):', "disable_if", "doc_chain_selftest"),
    ("doc_chain.C4", "if not seq_with_alt:", "disable_if", "doc_chain_selftest"),
    ("doc_chain.C4", 'if "flowchart" not in kinds:', "disable_if", "doc_chain_selftest"),
    ("doc_chain.C5", "C5 契约闭合: design/be 契约表声明的接口", "drop_statement", "doc_chain_selftest"),
    ("doc_chain.C6", "for table in re.findall(r\"((?:^\\|[^\\n]*\\|[ \\t]*\\n){2,})\", fe_text, re.M):", "empty_iter", "doc_chain_selftest"),
    ("doc_chain.C7", "if len(wireframes) < 2 and not has_prototype:", "disable_if", "doc_chain_selftest"),
    ("doc_chain.C9", "if not BRANCH_HEADING_RE.search(all_text[f]):", "disable_if", "doc_chain_selftest"),
    ("doc_chain.C10", "if opened != blocks:", "invert_cmp", "doc_chain_selftest"),
]

MUTATIONS: list[Mutation] = [
    Mutation(f"M{index:02d}", item, ITEMS[item][0], anchor, op, check)
    for index, (item, anchor, op, check) in enumerate(SPECS, start=1)
]

CMP_INVERT = {"!=": "==", "==": "!=", "<=": ">", ">=": "<", "<": ">=", ">": "<="}
CMP_PATTERN = re.compile(r"!=|==|<=|>=|<|>")
STRICT_PATTERN = re.compile(r"(?<![<>=!\-])([<>])(?!=)")


class MutationError(Exception):
    """A mutation cannot be applied; the run reports it as 无效."""


class CopyError(Exception):
    """The working tree could not be copied; the run aborts without touching the real tree."""


def _split_eol(line: str) -> tuple[str, str]:
    body = line.rstrip("\r\n")
    return body, line[len(body):]


def _op_invert_cmp(body: str) -> str | None:
    match = CMP_PATTERN.search(body)
    if match is None:
        return None
    return body[: match.start()] + CMP_INVERT[match.group()] + body[match.end():]


def _op_relax_strict(body: str) -> str | None:
    match = STRICT_PATTERN.search(body)
    if match is None:
        return None
    return body[: match.start()] + match.group(1) + "=" + body[match.end():]


def _op_disable_if(body: str) -> str | None:
    match = re.match(r"^(\s*)if .+:\s*$", body)
    if match is None:
        return None
    return f"{match.group(1)}if False:"


def _op_drop_enum_member(body: str) -> str | None:
    match = re.search(r',\s*(["\'][^"\']*["\'])\s*\)\s*$', body)
    if match is None:
        return None
    return body[: match.start()] + ")"


def _op_empty_iter(body: str) -> str | None:
    match = re.match(r"^(\s*)for (.+) in (.+):\s*$", body)
    if match is None:
        return None
    return f"{match.group(1)}for {match.group(2)} in ():"


LINE_OPERATORS = {
    "invert_cmp": _op_invert_cmp,
    "relax_strict": _op_relax_strict,
    "disable_if": _op_disable_if,
    "drop_enum_member": _op_drop_enum_member,
    "empty_iter": _op_empty_iter,
}


def _is_collect_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    func = node.value.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in ("append", "extend")
        and isinstance(func.value, ast.Name)
        and func.value.id == "errors"
    )


def apply_mutation(source: str, mutation: Mutation) -> str:
    """Return the mutated source. Raises MutationError when the anchor or operator does not apply."""
    lines = source.splitlines(keepends=True)
    if mutation.op in LINE_OPERATORS:
        hits = [index for index, line in enumerate(lines) if mutation.anchor in line]
        if len(hits) != 1:
            raise MutationError(f"anchor {mutation.anchor!r} matches {len(hits)} lines, need exactly 1")
        body, eol = _split_eol(lines[hits[0]])
        new_body = LINE_OPERATORS[mutation.op](body)
        if new_body is None:
            raise MutationError(f"operator {mutation.op} does not apply to line {hits[0] + 1}: {body.strip()!r}")
        lines[hits[0]] = new_body + eol
    elif mutation.op == "drop_statement":
        tree = ast.parse(source)
        nodes = [
            node
            for node in ast.walk(tree)
            if _is_collect_call(node) and mutation.anchor in (ast.get_source_segment(source, node) or "")
        ]
        if len(nodes) != 1:
            raise MutationError(f"anchor {mutation.anchor!r} selects {len(nodes)} statements, need exactly 1")
        node = cast("ast.stmt", nodes[0])
        first = lines[node.lineno - 1]
        indent = first[: len(first) - len(first.lstrip())]
        if node.col_offset != len(indent):
            raise MutationError("statement shares its line with other code")
        end = node.end_lineno
        if end is None:
            raise MutationError("statement has no end line")
        _, eol = _split_eol(lines[end - 1])
        lines[node.lineno - 1 : end] = [indent + "pass" + eol]
    elif mutation.op == "drop_continue":
        tree = ast.parse(source)
        nodes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Continue) and node.lineno >= 2 and mutation.anchor in lines[node.lineno - 2]
        ]
        if len(nodes) != 1:
            raise MutationError(f"anchor {mutation.anchor!r} selects {len(nodes)} continue statements, need exactly 1")
        target = cast("ast.stmt", nodes[0])
        body, eol = _split_eol(lines[target.lineno - 1])
        if body.strip() != "continue":
            raise MutationError("selected line is not a bare continue")
        lines[target.lineno - 1] = body[: len(body) - len(body.lstrip())] + "pass" + eol
    else:
        raise MutationError(f"unknown operator {mutation.op!r}")
    result = "".join(lines)
    ast.parse(result)  # the rewrite must still be Python
    return result


def copy_tree(destination: Path) -> None:
    completed = subprocess.run(
        ["cp", "-R", f"{ROOT}/.", str(destination)], capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise CopyError(completed.stderr.strip() or f"cp exited {completed.returncode}")
    for cache in destination.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run_check(copy: Path, check: str) -> tuple[int | None, str]:
    """Run one check in `copy`. Returns (exit code, combined output); exit code None means timeout."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    argv = [sys.executable, "-B", *CHECKS[check]]
    try:
        completed = subprocess.run(
            argv, cwd=str(copy), capture_output=True, text=True, timeout=MUTATE_TIMEOUT_S, env=env, check=False
        )
    except subprocess.TimeoutExpired:
        return None, ""
    return completed.returncode, f"{completed.stdout}\n{completed.stderr}"


def run_mutation(mutation: Mutation) -> dict:
    original = (ROOT / mutation.file).read_text(encoding="utf-8")
    record = asdict(mutation) | {"status": "", "timeout": False, "detail": ""}
    try:
        mutated = apply_mutation(original, mutation)
    except MutationError as exc:
        record |= {"status": "无效", "detail": str(exc)}
        return record
    if mutated == original:
        record |= {"status": "无效", "detail": "rewrite produced identical text"}
        return record
    work = Path(tempfile.mkdtemp(prefix="mutate-"))
    try:
        copy = work / "repo"
        copy_tree(copy)
        target = copy / mutation.file
        target.write_text(mutated, encoding="utf-8")
        if target.read_text(encoding="utf-8") == original:
            record |= {"status": "无效", "detail": "file unchanged after write"}
            return record
        code, output = run_check(copy, mutation.check)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if code is None:
        record |= {"status": "存活", "timeout": True, "detail": f"超时 >{MUTATE_TIMEOUT_S}s，按存活计"}
    elif code != 0:
        crashed = "Traceback" in output
        record |= {"status": "已杀死", "detail": "崩溃（traceback）" if crashed else f"exit {code}"}
    else:
        record |= {"status": "存活", "detail": "exit 0"}
    return record


def coverage_gaps() -> list[str]:
    covered = {mutation.item for mutation in MUTATIONS}
    gaps = [item for item in ITEMS if item not in covered and item not in EXEMPT]
    unknown = sorted(covered - set(ITEMS))
    return gaps + [f"unknown item {name}" for name in unknown]


def control(check: str, base: Path) -> tuple[bool, str]:
    code, output = run_check(base, check)
    return code == 0, output[-400:]


def print_listing() -> None:
    print("算子:")
    for name, text in OPERATORS.items():
        print(f"  {name:<18} {text}")
    print("\n检查项覆盖:")
    for item, (file, text) in ITEMS.items():
        count = sum(1 for mutation in MUTATIONS if mutation.item == item)
        marker = f"豁免: {EXEMPT[item]}" if item in EXEMPT else f"{count} 个变异"
        print(f"  {item:<30} {file:<32} {marker}  — {text}")
    print("\n变异项:")
    for mutation in MUTATIONS:
        print(f"  {mutation.id} {mutation.item:<30} {mutation.op:<17} {mutation.check:<18} {mutation.anchor}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="列出算子、检查项覆盖与全部变异，不运行")
    parser.add_argument("--check", help="只运行该检查项的变异（validate 子命令名或 doc_chain_selftest）")
    parser.add_argument("--report", default=str(DEFAULT_REPORT_DIR), help="报告输出目录")
    args = parser.parse_args(argv)

    for mutation in MUTATIONS:
        if mutation.op not in OPERATORS or mutation.check not in CHECKS or mutation.item not in ITEMS:
            print(f"mutation table error: {mutation.id}", file=sys.stderr)
            return 1
    gaps = coverage_gaps()
    if gaps:
        print("覆盖缺口（既无变异也无豁免）: " + ", ".join(gaps), file=sys.stderr)
        return 1

    if args.list:
        print_listing()
        return 0

    selected = MUTATIONS
    if args.check is not None:
        if args.check not in CHECKS:
            print(f"unknown check {args.check!r}; known: {', '.join(CHECKS)}", file=sys.stderr)
            return 2
        selected = [mutation for mutation in MUTATIONS if mutation.check == args.check]

    base_dir = Path(tempfile.mkdtemp(prefix="mutate-control-"))
    try:
        base = base_dir / "repo"
        copy_tree(base)
        for check in sorted({mutation.check for mutation in selected}):
            ok, tail = control(check, base)
            if not ok:
                print(f"CONTROL FAILED: unmutated copy does not pass {check}; results would be unreliable")
                print(tail)
                return 1
            print(f"CONTROL PASS {check}")
        results = []
        for mutation in selected:
            record = run_mutation(mutation)
            results.append(record)
            print(f"{record['id']} {record['status']:<4} {record['item']:<30} {record['check']:<18} {record['detail']}")
    except CopyError as exc:
        print(f"copy failed, aborted; real tree untouched: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    counts = {status: sum(1 for r in results if r["status"] == status) for status in ("已杀死", "存活", "无效")}
    timeouts = sum(1 for r in results if r["timeout"])
    summary = (
        f"总变异数 {len(results)}  已杀死 {counts['已杀死']}  存活 {counts['存活']}"
        f"（其中超时 {timeouts}）  无效 {counts['无效']}"
    )
    print(summary)

    report_dir = Path(args.report)
    try:
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        (report_dir / "summary.txt").write_text(summary + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"cannot write report to {report_dir}: {exc}", file=sys.stderr)
        return 1
    # A surviving mutant means the corpus has no instance of the violation class that mutation
    # simulates — the gate could be silently broken with nothing going red. That is a finding the
    # caller must act on (add negative corpus or register an EXEMPT), so it exits nonzero; an
    # invalid mutation (anchor drift) is a broken mutation spec, distinct from both.
    if counts["无效"]:
        return 2
    return 1 if counts["存活"] else 0


if __name__ == "__main__":
    sys.exit(main())
