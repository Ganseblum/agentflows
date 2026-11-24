#!/usr/bin/env python3
"""gen_review_brief.py — 生成评审简报（把「定位」从 reviewer 的工作里删掉）。

问题：评审简报由 supervisor 现场手写，每次都写歪——2026-11-02 实测一份 3,471 字符的简报里
27% 是 sha256（reviewer 没有 Bash，物理上无法校验），6 份文档只给路径不给内容，导致 reviewer
把大量轮次花在「找这句话在哪」而不是「判断对不对」。首轮因此用了 30.5 分钟。

做法：**手写简报不接受**。用本脚本生成，它强制内联：
  §1 评审对象（被评审文件逐字内容，带 path 标注）
  §2 断言表（每条断言 → 判据 → 核实点 path:line）
  §3 已执行的检查与逐字输出（supervisor 先跑，reviewer 不重跑）
  §4 上轮未关闭项（delta 轮）
并写出评审类型、范围、冻结的对象、停止条件和交付预算（契约见 references/contracts.md）。

用法：
  python3 gen_review_brief.py --out brief.md --objective "确认登录..."
      --files spec/qa/acceptance.md design/be/backend.md
      [--repo .] [--scope full|delta|spot] [--review-type document|implementation]
      [--assertions asserts.txt]
      [--checks checks.txt] [--prev-findings prev.txt] [--budget 12]
      [--stop-rule "..."] [--self-test]
      [--task-status tasks.txt --task-ids T01 T02]

  --task-ids：沿用原计划 ID，从完整映射选受评任务；递归前置须终态，后继可待办。
      task-status 格式为 tasks: N 头，加 N 行 `T01 | deps: - | status: ☑`；
      有前置写 `T02 | deps: T01,T03 | status: ☑`，状态允许 ☑ / — 本期不做 / N/A / ☐ / ◐。
      每行 deps 必填。脚本校验唯一 ID、完整行数、引用与环；映射和原计划的一致性仍须人工核实。
      不加 --task-ids 时保留旧 tasks:N + 每行终态格式，所有行均纳入入口校验。
  --reviewed-revision：从严格验证的快照或固定 full SHA 的普通 Git blob 内联，
      工作树改动或删除不影响正文。提交中已删路径仅在 --diff-base 含原文件时接受并生成删除 diff；
      快照缺文件不视为删除。UTF-8 解码严格，非法字节失败，不替换后重算 hash。

  --assertions 文件格式（一行一条）：
      断言 | 判据 | 核实点
      例：退出失败后刷新会恢复登录态 | 与 G3 冲突 | design/be/backend.md:181

  --checks 文件格式：每条一行，`命令 :: exit=N :: 逐字输出`（或 `命令 :: exit=N :: @路径`）；
      旧两段式 `命令 :: 逐字输出` / `命令 :: @路径` 仍接受，但渲染为「退出码未验证」
  --review-type：document 评审冻结的阶段文档或外部文档；implementation 用原计划状态映射。
      未填类型的旧调用继续生成，缺少任务范围或冻结对象时仅供准备。
  --diff-base 目录：按仓库相对路径生成 unified diff。delta 须同时给出该目录与
      --prev-findings，或用 --no-previous-findings 写明上轮结论的可复核来源与零遗留。
  --reuse-round N：复用同一 reviewer 的累计轮次（N ≥ 2）；必须与 --prev-findings 同时给出，
      元信息块渲染 reviewer_reuse 声明（契约：contracts.md「跨阶段不复用」）
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

if sys.version_info < (3, 10):
    raise SystemExit("gen_review_brief.py 需要 Python 3.10 或以上版本，请检查 python3 --version")
sys.dont_write_bytecode = True

from workflow_lib.review_bundle import (
    freeze_diff_base, freeze_review, safe_path, source_path,
)
from workflow_lib.managed import write_managed_file
from workflow_lib.snapshots import WorkflowError

DEFAULT_STOP_RULE = (
    "按简报 `review_gate`：入口不满足不开始（reviewer 返回 blocked）；出口满足即收口；"
    "同一原因连续两次失败或一轮无进展（无新证据且无 finding 关闭）即停并升级。"
)

REVIEW_GATE_ENTRY = (
    "被评审对象已冻结（评审快照目录或提交；material 评审不得用 unverified-boundary）；"
    "{stage}已知必需检查有命令、原始输出和退出码，无适用命令时注明依据；"
    "简报必填字段与内联对象齐备。"
    "任一不满足 → reviewer 返回 blocked 并列缺失项，不开始评审。"
)
REVIEW_GATE_EXIT = (
    "本轮 finding 已进入 required_changes 或已立案；上轮 finding 为 closed 且 cost_replay 成立，"
    "或 residual_risks 写明无法关闭的理由；无未关闭 P0/P1；用户可见断言有「若为假会失败」的"
    "检查或标 unverified（此时结论 ≤ partial）；同一原因连续两次失败或一轮无进展"
    "（无新证据且无 finding 关闭）即停并升级。"
)
STATUS_MATRIX = (
    "入口不满足（简报不合格/对象未冻结/{task}必需检查未跑或无退出码）→ decision: blocked，"
    "不开始评审；已开始评审但某个具体断言缺原始证据 → status: partial（decision 只能是 "
    "changes_requested 或 blocked，绝不是 approved）。"
)
UNVERIFIED_BOUNDARY = (
    "unverified-boundary（未提供评审快照或提交；§1 内联正文为唯一绑定）"
)
_TASKS_HEADER_RE = re.compile(r"^tasks:\s*(\d+)\s*$")
_TASK_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
TERMINAL_TASK_STATES = {"☑", "☑ 已完成", "— 本期不做", "N/A"}
PENDING_TASK_STATES = {"☐", "☐ 未开始", "☐ 待开始", "◐", "◐ 进行中", "⚠", "⚠ 阻塞"}


def validate_reviewed_revision(value: str, repo: Path, files: list[Path]) -> None:
    """兼容旧校验入口；正文生成仍须自行固定同一份完整对象。"""
    freeze_review(repo, files, value)


def _terminal(line: str) -> bool:
    return (not any(mark in line for mark in ("◐", "☐", "⚠", "进行中", "未开始", "阻塞"))
            and any(mark in line for mark in ("☑", "—", "N/A")))


def validate_task_status(text: str, task_ids: list[str] | None = None) -> list[str]:
    """旧终态文本兼容；指定 IDs 时校验完整原计划映射与受评依赖闭包。"""
    lines = [line.strip() for line in text.splitlines()
             if line.strip() and not line.strip().startswith("#")]
    headers = [line for line in lines if line.startswith("tasks:")]
    if len(headers) != 1 or not (header := _TASKS_HEADER_RE.fullmatch(headers[0])):
        raise ValueError("--task-status 须有唯一 `tasks: N` 头")
    rows = [line for line in lines if not line.startswith("tasks:")]
    expected = int(header[1])
    if len(rows) != expected:
        raise ValueError(f"任务状态行数 {len(rows)} ≠ 声明 tasks: {expected}")
    if not task_ids:
        for line in rows:
            if not _terminal(line):
                raise ValueError(f"任务未终态或缺终态标记（☑ / — 本期不做 / N/A）：{line}")
        return []
    if len(task_ids) != len(set(task_ids)) or any(not _TASK_ID_RE.fullmatch(i) for i in task_ids):
        raise ValueError("--task-ids 必须是唯一原计划 ID 列表")
    tasks: dict[str, tuple[list[str], str]] = {}
    for line in rows:
        parts = [part.strip() for part in line.split("|")]
        if (len(parts) != 3 or not _TASK_ID_RE.fullmatch(parts[0])
                or not parts[1].startswith("deps:") or not parts[2].startswith("status:")):
            raise ValueError(f"范围映射须逐行声明 `ID | deps: -或ID,ID | status: 状态`：{line}")
        identifier = parts[0]
        raw_deps = parts[1][len("deps:"):].strip()
        deps = [] if raw_deps == "-" else [dep.strip() for dep in raw_deps.split(",")]
        state = parts[2][len("status:"):].strip()
        if identifier in tasks:
            raise ValueError(f"重复任务 ID：{identifier}")
        if (any(not _TASK_ID_RE.fullmatch(dep) for dep in deps)
                or len(deps) != len(set(deps))):
            raise ValueError(f"任务前置缺失或重复：{identifier}")
        if state not in TERMINAL_TASK_STATES | PENDING_TASK_STATES:
            raise ValueError(f"未知任务状态：{identifier} {state}")
        tasks[identifier] = (deps, state)
    for identifier, (deps, _) in tasks.items():
        unknown = set(deps) - tasks.keys()
        if unknown:
            raise ValueError(f"任务 {identifier} 引用未知/遗漏前置：{', '.join(sorted(unknown))}")
    unknown_ids = set(task_ids) - tasks.keys()
    if unknown_ids:
        raise ValueError(f"--task-ids 引用未知任务：{', '.join(sorted(unknown_ids))}")
    # Validate the whole mapping, including pending successors; no recursion depth limit.
    dependents: dict[str, list[str]] = {identifier: [] for identifier in tasks}
    counts = {identifier: len(deps) for identifier, (deps, _) in tasks.items()}
    for identifier, (deps, _) in tasks.items():
        for dep in deps:
            dependents[dep].append(identifier)
    ready = [identifier for identifier, count in counts.items() if count == 0]
    done: set[str] = set()
    while ready:
        identifier = ready.pop()
        done.add(identifier)
        for successor in dependents[identifier]:
            counts[successor] -= 1
            if counts[successor] == 0:
                ready.append(successor)
    if len(done) != len(tasks):
        raise ValueError(f"任务依赖成环：{', '.join(sorted(tasks.keys() - done))}")
    closure: set[str] = set()
    pending = list(task_ids)
    while pending:
        identifier = pending.pop()
        if identifier not in closure:
            closure.add(identifier)
            pending.extend(tasks[identifier][0])
    for identifier in sorted(closure):
        if tasks[identifier][1] not in TERMINAL_TASK_STATES:
            raise ValueError(f"受评任务或递归前置未终态：{identifier} {tasks[identifier][1]}")
    return sorted(closure)


def git_head(repo: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "no-git"
    except (OSError, subprocess.TimeoutExpired):
        return "no-git"


def parse_assertions(path: Path | None) -> list[tuple[str, str, str]]:
    if not path:
        return []
    rows: list[tuple[str, str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        while len(parts) < 3:
            parts.append("")
        rows.append((parts[0], parts[1], parts[2]))
    return rows


def parse_checks(path: Path | None) -> list[tuple[str, str, int | None]]:
    if not path:
        return []
    out: list[tuple[str, str, int | None]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cmd, delimiter, rest = raw.partition("::")
        if not cmd.strip() or not delimiter:
            raise ValueError(f"{path}:{number} 缺少检查命令或 :: 分隔符")
        exit_code: int | None = None
        body = rest.strip()
        # 三段式：`命令 :: exit=N :: 输出`；两段式旧格式仍接受（exit 记 None）。
        m = re.match(r"^exit=(-?\d+)\s*::\s*(.*)$", body, re.DOTALL)
        if m:
            exit_code = int(m.group(1))
            body = m.group(2)
        body = body.strip()
        if body.startswith("@"):
            p = Path(body[1:].strip())
            body = read_text_exact(p)
        out.append((cmd.strip(), body, exit_code))
    return out


def read_text_exact(path: Path) -> str:
    return safe_path(path).read_bytes().decode("utf-8")


def literal_block(body: str, language: str = "text") -> str:
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", body)), default=0))
    return f"{fence}{language}\n{body}" + ("" if body.endswith("\n") else "\n") + fence + "\n"


def build_brief(*, objective: str, files: list[Path], repo: Path, scope: str,
                assertions: list[tuple[str, str, str]], checks: list[tuple[str, str, int | None]],
                prev: str, budget: int, stop_rule: str,
                diff_base: Path | None = None, reuse_round: int | None = None,
                review_round: int | None = None, task_status: str = "",
                reviewed_revision: str | None = None,
                task_ids: list[str] | None = None,
                review_type: str | None = None,
                no_previous_findings: str = "",
                snapshot_source_repo: Path | None = None) -> str:
    if scope == "delta" and (diff_base is None or not (prev.strip() or no_previous_findings.strip())):
        raise ValueError("delta 评审须提供 --diff-base 及非空 --prev-findings 或 --no-previous-findings")
    if prev.strip() and no_previous_findings.strip():
        raise ValueError("--prev-findings 与 --no-previous-findings 不可同时给出")
    if reuse_round is not None and not prev.strip():
        raise ValueError("--reuse-round 需要 --prev-findings 的可核对上轮锚点")
    if review_type == "document" and (task_status.strip() or task_ids):
        raise ValueError("document 评审无需任务映射；请移除 --task-status 和 --task-ids")
    if review_type == "implementation" and not (task_status.strip() and task_ids):
        raise ValueError("implementation 评审须同时提供 --task-status 与 --task-ids")
    if review_type is not None and not reviewed_revision:
        raise ValueError(f"{review_type} 评审须提供 --reviewed-revision 的快照或提交")
    if review_type is not None and not objective.strip():
        raise ValueError(f"{review_type} 评审须用 --objective 说明评审对象或目标")
    kind = review_type or "implementation"
    closure = validate_task_status(task_status, task_ids) if task_status.strip() else []
    if task_ids and not task_status.strip():
        raise ValueError("--task-ids 必须与 --task-status 完整原计划映射同时给出")
    base_objects = freeze_diff_base(diff_base, safe_path(repo), snapshot_source_repo) if diff_base is not None else None
    bundle = freeze_review(repo, files, reviewed_revision,
                           set(base_objects) if base_objects is not None else None, snapshot_source_repo)
    # Decode strictly once; neither the body nor the diff can reread a mutable source.
    bodies = {name: data.decode("utf-8") if data is not None else None
              for name, data in bundle.objects.items()}
    base_bodies = ({name: data.decode("utf-8") for name, data in base_objects.items()}
                   if base_objects is not None else None)
    head = git_head(repo)
    revision = bundle.revision or UNVERIFIED_BOUNDARY
    L: list[str] = []
    L.append(f"# 评审简报（{date.today().isoformat()} 生成）\n")
    L.append("> 本简报由 `scripts/gen_review_brief.py` 生成，**手写简报不被接受**。")
    L.append("> reviewer 收到后先核下方元信息和对应类型的入口条件，缺项即返回 `blocked: 简报不合格`。\n")

    L.append("## 评审元信息\n")
    L.append(f"- `review_type`: {kind}")
    L.append(f"- `review_scope`: {scope}")
    L.append(f"- `reviewed_revision`: {revision}（生成时工作树 HEAD {head}）")
    if bundle.kind == "draft":
        L.append("> 草稿：对象未冻结。派发前须提供快照或提交重新生成。")
    L.append(f"- `inline_objects`: 下方 §1 逐文件内联（{len(files)} 个文件，逐字）")
    L.append(f"- `stop_rule`: {stop_rule}")
    if reuse_round is not None and prev.strip():
        L.append(
            f"- `reviewer_reuse`: 本轮为同一 reviewer 的第 {reuse_round} 轮（累计）；"
            "上轮结论锚点见 §4。报告须声明「本结论部分依赖上轮判断」。")
    L.append(f"- `output_budget`: findings ≤{budget} 条，报告正文 ≤6000 字符；超限按严重度截断并声明")
    stage_gate = (
        "被审文档及直接相关上游材料、来源固定，无需实现任务映射；" if kind == "document"
        else "提交者在简报 §0 给出任务状态快照，受评任务及递归前置全部终态；"
             "评审/收口后继可待办，范围映射须对照原计划；"
    )
    L.append(f"- `review_gate`: 入口 = {REVIEW_GATE_ENTRY.format(stage=stage_gate)}")
    L.append(f"  出口 = {REVIEW_GATE_EXIT}")
    L.append(f"  状态矩阵 = {STATUS_MATRIX.format(task='任务未完成/' if kind == 'implementation' else '')}")
    if review_round is not None:
        L.append(f"- `review_round`: 第 {review_round} 轮（仅记录，不设上限；轮次由入口/出口条件决定）")
    L.append("")

    L.append("## §0 评审输入\n")
    if kind == "document":
        L.append("> 文档评审。以冻结的阶段产物、直接相关上游材料和判据为输入，任务状态不适用。\n")
    if task_ids:
        L.append(f"- 受评原计划任务 IDs：{', '.join(task_ids)}")
        L.append(f"- 递归前置闭包（含受评任务）：{', '.join(closure)}")
        L.append("> 下方完整映射须从原计划派生并沿用原 ID；脚本只验证映射的完整声明、引用、环与闭包终态，"
                 "未自动验证它与原计划内容一致。独立评审须对照原计划，核实没有漏任务或漏前置；"
                 "闭包外评审/收口后继允许待办。\n")
    if task_status.strip():
        L.append(literal_block(task_status))
    if kind == "implementation" and not task_ids:
        L.append("> 未提供受评原计划任务映射——**实现评审入口不满足，派发前须提供 --task-status 和 --task-ids**。\n")

    L.append("## 目标\n")
    L.append(objective.strip() + "\n")

    L.append(f"## §1 评审对象（逐字内联，共 {len(files)} 个文件）\n")
    for path, name in zip(bundle.paths, bundle.names):
        data, body = bundle.objects[name], bodies[name]
        if data is None:
            L.append(f"### `{path}` — **已删除（固定提交 tree 不含此路径，基线含此文件）**\n")
            continue
        digest = hashlib.sha256(data).hexdigest()[:12]
        L.append(f"### `{path}`（sha256 前 12 位 `{digest}`，{len(body.splitlines())} 行）\n")
        L.append(literal_block(body))

    if base_bodies is not None:
        L.append(f"## §1.1 逐文件 diff（相对 `{diff_base}`；delta 轮的变化面以本节为准，§1 全文用于核对上下文）\n")
        for name in bundle.names:
            body = bodies[name]
            if name not in base_bodies:
                L.append(f"### `{name}` — **新增（基线无此文件）**\n")
            elif body is None:
                L.append(f"### `{name}` — **删除（提交 tree 已核实）**\n")
            before = base_bodies.get(name, "")
            after = body if body is not None else ""
            if before == after and body is not None:
                L.append(f"### `{name}` — 与基线一致（无 diff）\n")
                continue
            diff_lines = difflib.unified_diff(
                before.splitlines(keepends=True), after.splitlines(keepends=True),
                fromfile=f"base/{name}" if name in base_bodies else "/dev/null",
                tofile=f"current/{name}" if body is not None else "/dev/null")
            patch = "".join(line if line.endswith("\n")
                            else line + "\n\\ No newline at end of file\n" for line in diff_lines)
            L.append(f"### `{name}`（{len(patch.splitlines())} 行 diff）\n")
            L.append(literal_block(patch))
        extras = sorted(base_bodies.keys() - set(bundle.names))
        if extras:
            L.append(f"> 基线存在但本轮清单未列的文件（{len(extras)} 个）；若属删除/移出评审面，须显式处置：")
            for name in extras:
                L.append(f"> - `{name}`")
            L.append("")
        if not bundle.names:
            L.append("> 本轮清单为空。\n")

    L.append("## §2 断言表（逐条判断，不要通读全文找）\n")
    if assertions:
        L.append("| # | 断言 | 判据 | 核实点 |")
        L.append("| --- | --- | --- | --- |")
        for i, (claim, criterion, anchor) in enumerate(assertions, 1):
            L.append(f"| A{i} | {claim} | {criterion} | {anchor or '（未给锚点）'} |")
        L.append("")
        L.append("> 只回答这张表：每条给「成立 / 不成立 / 未验证」+ 一句依据。")
        L.append("> 通过的项报 `PASS A<n>` 一行即可；只有 finding 需要引用原文。\n")
    else:
        L.append("> 未提供断言表。请对 §1 内容做整体判断，并按 `output_budget` 截断。\n")

    L.append("## §3 已执行的检查（原始输出，不必重跑）\n")
    if checks:
        for cmd, body, exit_code in checks:
            stamp = f"（exit {exit_code}）" if exit_code is not None else "（退出码未验证）"
            L.append(f"**`{cmd}`**{stamp}\n")
            L.append(literal_block(body))
        L.append("> 这些检查已由 supervisor 跑过。你不必重跑，也不必采信摘要——正文就是逐字输出；")
        L.append("> 标注「退出码未验证」的检查不得引用为「已通过」，要么补退出码重跑，要么按未运行处理。\n")
    else:
        L.append("> 未附检查输出。涉及「跑过没跑过」的断言按 `unverified` 处理。\n")

    L.append("## §4 上轮未关闭项（delta 轮必填）\n")
    if prev.strip():
        L.append(prev.strip() + "\n")
    elif no_previous_findings.strip():
        L.append(no_previous_findings.strip() + "\n")
    else:
        L.append("> 本简报未附上轮结论。\n")

    L.append("## 交付形态\n")
    L.append("```yaml")
    L.append("decision: approved | changes_requested | blocked")
    L.append("status: complete | partial | blocked")
    L.append("findings: []  # 无发现时保留空数组")
    L.append("# 有发现时改成缩进列表，每条包含 id、severity、issue、location；")
    L.append("# 可附 cause、evidence、cost、fix。")
    L.append("previous_findings: 每条 = id + severity + status(closed|unverified) + cost_replay（delta 轮必填）")
    L.append("passed: PASS A1, PASS A3 …（一行一条）")
    L.append("residual_risks: 未覆盖面与建议")
    L.append("```")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="生成文档或实现评审简报，保留冻结对象和原始检查证据")
    ap.add_argument("--out", help="输出文件路径")
    ap.add_argument("--objective", default="", help="本轮评审目标（一句话）")
    ap.add_argument("--files", nargs="*", default=[], help="被评审文件（相对 --repo）")
    ap.add_argument("--repo", default=".", help="仓库根（默认当前目录）")
    ap.add_argument("--scope", default="full", choices=["full", "delta", "spot"])
    ap.add_argument("--review-type", choices=("document", "implementation"),
                    help="指定阶段文档或实现评审；未指定时兼容旧实现简报")
    ap.add_argument("--assertions", default=None, help="断言表文件（断言 | 判据 | 核实点）")
    ap.add_argument("--checks", default=None, help="已执行检查文件（命令 :: 输出 或 命令 :: @文件）")
    ap.add_argument("--prev-findings", default=None, help="上轮未关闭项文件")
    ap.add_argument("--no-previous-findings", default="", help="没有遗留项时，写明上轮结论和可复核来源")
    ap.add_argument("--budget", type=int, default=12, help="findings 上限（默认 12）")
    ap.add_argument("--stop-rule", default=DEFAULT_STOP_RULE)
    ap.add_argument("--diff-base", default=None,
                    help="基线目录（如评审快照）；给出时生成 §1.1 逐文件 diff")
    ap.add_argument("--reuse-round", type=int, default=None,
                    help="复用同一 reviewer 的累计轮次（--prev-findings 存在时渲染 reviewer_reuse 声明）")
    ap.add_argument("--review-round", type=int, default=None,
                    help="本轮在该阶段的评审轮次（≥1，仅记录不设上限）；给出时渲染 review_round")
    ap.add_argument("--task-status", default=None,
                    help="任务状态文件（旧 tasks:N 终态行；配合 --task-ids 使用完整原计划 ID/deps/status 映射）")
    ap.add_argument("--task-ids", nargs="+", default=None,
                    help="受评原计划 IDs；映射行格式 ID | deps: -或ID,ID | status: ☑/☐/◐/— 本期不做/N/A；递归前置须终态")
    ap.add_argument("--reviewed-revision", default=None,
                    help="评审快照目录或提交号；未给时渲染 unverified-boundary（material 评审不得据此 approved）")
    ap.add_argument("--snapshot-source-repo", help="迁移同一仓库后，显式指定快照 MANIFEST 记录的原仓根")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not args.out or not args.files:
        ap.error("需要 --out 与 --files（或 --self-test）")

    try:
        repo = safe_path(Path(args.repo))
        files = [source_path(repo, f) for f in args.files]
        diff_base = safe_path(Path(args.diff_base)) if args.diff_base else None
        source_repo = safe_path(Path(args.snapshot_source_repo)) if args.snapshot_source_repo else None
        out = safe_path(Path(args.out))
        if out.exists():
            raise ValueError(f"简报要求新输出文件，不覆盖：{out}")
        if diff_base and out.is_relative_to(diff_base):
            raise ValueError("简报输出不得位于 diff 基线目录内")
        if args.reviewed_revision:
            candidate = Path(args.reviewed_revision)
            if candidate.is_dir() and out.is_relative_to(safe_path(candidate)):
                raise ValueError("简报输出不得位于评审快照目录内")
    except (OSError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    if args.reuse_round is not None:
        if args.reuse_round < 2:
            print("[错误] --reuse-round 是复用轮次，首轮没有复用；最小值 2", file=sys.stderr)
            return 1
        if not args.prev_findings:
            print("[错误] --reuse-round 必须与 --prev-findings 同时给出（复用声明需要上轮结论锚点）",
                  file=sys.stderr)
            return 1
    if args.review_round is not None and args.review_round < 1:
        print("[错误] --review-round 从 1 开始计数，不能小于 1", file=sys.stderr)
        return 1
    task_status = ""
    if args.task_status:
        try:
            task_status = Path(args.task_status).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"[错误] --task-status 不可读：{exc}", file=sys.stderr)
            return 1
    try:
        brief = build_brief(
            objective=args.objective, files=files, repo=repo, scope=args.scope,
            assertions=parse_assertions(Path(args.assertions) if args.assertions else None),
            checks=parse_checks(Path(args.checks) if args.checks else None),
            prev=read_text_exact(Path(args.prev_findings)) if args.prev_findings else "",
            budget=args.budget, stop_rule=args.stop_rule,
            diff_base=diff_base, reuse_round=args.reuse_round,
            review_round=args.review_round,
            task_status=task_status, reviewed_revision=args.reviewed_revision,
            task_ids=args.task_ids, review_type=args.review_type,
            no_previous_findings=args.no_previous_findings, snapshot_source_repo=source_repo,
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        write_managed_file(out, brief.encode("utf-8"), {"exists": False})
    except (OSError, ValueError, WorkflowError, subprocess.TimeoutExpired) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    print(f"[ok] 简报 -> {out}（{len(brief)} 字符，内联 {len(files)} 个文件）")
    print("     已写入评审入口和元信息。")
    return 0


def _self_test() -> int:
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def case(name, fn):
        base = safe_path(Path(tempfile.mkdtemp(prefix="af-brief-")))
        original_argv = sys.argv[:]
        try:
            fn(base)
            results.append((name, True, ""))
        except Exception as exc:
            results.append((name, False, f"{type(exc).__name__}: {exc}"))
        finally:
            import shutil
            sys.argv = original_argv
            shutil.rmtree(base, ignore_errors=True)

    def make_snapshot(base: Path, repo: Path, files: list[str], round_no: int = 1) -> Path:
        from review_snapshot import make_snapshot as snapshot
        feature = base / "feature"
        feature.mkdir(exist_ok=True)
        return snapshot(repo, feature, round_no, files, None)[0]

    def git(repo: Path, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        assert result.returncode == 0, (args, result.stdout, result.stderr)
        return result.stdout.strip()

    def commit(repo: Path, message: str = "test object") -> str:
        if not (repo / ".git").is_dir():
            git(repo, "init", "--quiet")
        git(repo, "add", "--all")
        git(repo, "-c", "user.name=Review Test", "-c", "user.email=review@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
            "commit", "--quiet", "--allow-empty", "-m", message)
        return git(repo, "rev-parse", "HEAD")

    def render(repo: Path, files: list[str], **extra) -> str:
        delta = extra.get("diff_base") is not None
        return build_brief(objective="frozen regression", files=[repo / f for f in files], repo=repo,
                           scope="delta" if delta else "full", assertions=[], checks=[], prev="", budget=3,
                           no_previous_findings="REV-TEST 无遗留" if delta else "",
                           stop_rule="test", **extra)

    def t_basic(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n内容行\n", encoding="utf-8")
        (base / "as.txt").write_text("退出失败恢复登录 | 与 G3 冲突 | a.md:2\n", encoding="utf-8")
        (base / "ck.txt").write_text("pytest -q :: exit=0 :: 3 passed\n", encoding="utf-8")
        revision = commit(base)
        brief = build_brief(objective="确认登录", files=[base / "a.md"], repo=base, scope="full",
                            assertions=parse_assertions(base / "as.txt"),
                            checks=parse_checks(base / "ck.txt"), prev="", budget=12,
                            stop_rule="1 轮", task_status="tasks: 1\nT01 ☑", reviewed_revision=revision[:7])
        for token in ["`review_scope`: full", "`stop_rule`: 1 轮", "`output_budget`: findings ≤12",
                      "内容行", "退出失败恢复登录", "3 passed", "sha256 前 12 位",
                      "（exit 0）", "`reviewed_revision`: " + revision]:
            assert token in brief, f"简报缺 {token}"

    def t_assertion_parsing(base: Path) -> None:
        (base / "as.txt").write_text("# 注释\n断言一 | 判据一 | p.md:10\n\n断言二 | 判据二\n",
                                     encoding="utf-8")
        rows = parse_assertions(base / "as.txt")
        assert len(rows) == 2, f"应解析 2 条，实际 {len(rows)}"
        assert rows[0] == ("断言一", "判据一", "p.md:10"), rows[0]
        assert rows[1][2] == "", "缺核实点应补空字符串"

    def t_check_file_ref(base: Path) -> None:
        (base / "out.txt").write_text("逐字输出内容\n", encoding="utf-8")
        (base / "ck.txt").write_text(f"npm test :: @{base / 'out.txt'}\n", encoding="utf-8")
        rows = parse_checks(base / "ck.txt")
        assert rows and "逐字输出内容" in rows[0][1], rows

    def t_exit_code_checks(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n内容行\n", encoding="utf-8")
        (base / "out.txt").write_text("3 passed\n", encoding="utf-8")
        (base / "ck.txt").write_text(
            f"npm test :: exit=0 :: @{base / 'out.txt'}\nnpm run lint :: eslint .\n",
            encoding="utf-8")
        rows = parse_checks(base / "ck.txt")
        assert rows[0][0] == "npm test" and rows[0][1].rstrip() == "3 passed" and rows[0][2] == 0, rows[0]
        assert rows[1][0] == "npm run lint" and rows[1][1] == "eslint ." and rows[1][2] is None, rows[1]
        brief = build_brief(objective="确认退出码", files=[base / "a.md"], repo=base, scope="full",
                            assertions=[], checks=rows, prev="", budget=3, stop_rule="1 轮")
        assert "**`npm test`**（exit 0）" in brief, "缺 exit 0 标注"
        assert "**`npm run lint`**（退出码未验证）" in brief, "缺退出码未验证标注"
        assert "不得引用为「已通过」" in brief, "缺未验证处置说明"

    def t_diff_base(base: Path) -> None:
        (base / "cur").mkdir()
        (base / "base").mkdir()
        (base / "base" / "a.md").write_text("# 文档 A\n旧行\n", encoding="utf-8")
        (base / "cur" / "a.md").write_text("# 文档 A\n新行\n", encoding="utf-8")
        (base / "cur" / "b.md").write_text("# 新增\n", encoding="utf-8")
        (base / "base" / "gone.md").write_text("# 将删\n", encoding="utf-8")
        brief = build_brief(objective="delta 评审", files=[base / "cur" / "a.md", base / "cur" / "b.md"],
                            repo=base / "cur", scope="delta", assertions=[], checks=[],
                            prev="", budget=3, stop_rule="1 轮", diff_base=base / "base",
                            no_previous_findings="REV-TEST 判定无遗留")
        assert "## §1.1" in brief, "缺 §1.1 diff 节"
        assert "-旧行" in brief and "+新行" in brief, "缺 diff 正文"
        assert "**新增（基线无此文件）**" in brief, "缺新增标注"
        assert "gone.md" in brief, "缺基线未列文件提示"

    def t_reuse_round(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        kw = dict(objective="o", files=[base / "a.md"], repo=base, scope="full",
                  assertions=[], checks=[], budget=3, stop_rule="1 轮")
        brief1 = build_brief(prev="上轮遗留", reuse_round=4, **kw)
        assert "第 4 轮（累计）" in brief1 and "部分依赖上轮判断" in brief1, "reuse_round=4 未渲染"
        brief2 = build_brief(prev="上轮遗留", **kw)
        assert "reviewer_reuse" not in brief2, "仅附上轮遗留不等于复用同一评审者"
        brief3 = build_brief(prev="", **kw)
        assert "reviewer_reuse" not in brief3, "首轮不应渲染 reviewer_reuse"
        rejects(lambda: build_brief(prev="", reuse_round=4, **kw), "上轮锚点")

    def t_diff_base_name_collision(base: Path) -> None:
        for name in ("repo", "x", "y"):
            (base / name).mkdir()
        files = [str(base / side / "same.md") for side in ("x", "y")]
        Path(files[0]).write_text("FIRST_OLD\n", encoding="utf-8")
        Path(files[1]).write_text("SECOND_OLD\n", encoding="utf-8")
        before = make_snapshot(base, base / "repo", files)
        Path(files[0]).write_text("FIRST_NEW\n", encoding="utf-8")
        Path(files[1]).write_text("SECOND_NEW\n", encoding="utf-8")
        current = make_snapshot(base, base / "repo", files, 2)
        brief = render(base / "repo", files, reviewed_revision=str(current), diff_base=before)
        assert "-FIRST_OLD" in brief and "+FIRST_NEW" in brief
        assert "-SECOND_OLD" in brief and "+SECOND_NEW" in brief
        assert "基线配对不可靠" not in brief, "稳定来源映射不应再靠 basename 配对"

    def t_review_gate(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        kw = dict(objective="o", files=[base / "a.md"], repo=base, scope="full",
                  assertions=[], checks=[], prev="", budget=3, stop_rule="1 轮")
        brief = build_brief(review_round=999, **kw)
        for token in ("`review_gate`: 入口 =", "出口 =", "任务状态快照", "cost_replay",
                      "unverified", "≤ partial", "状态矩阵", "第 999 轮（仅记录，不设上限",
                      "material 评审不得用 unverified-boundary", "required_changes 或已立案",
                      "无进展（无新证据且无 finding 关闭）"):
            assert token in brief, f"缺 {token}"
        assert "review_budget" not in brief and "偏离分档" not in brief, "不应再有固定轮次上限"
        assert "超出" not in brief and "上限 2 轮" not in brief, "轮次不应有上限告警"
        brief_none = build_brief(**kw)
        assert "review_round" not in brief_none, "未给轮次不应渲染 review_round"
        assert "`review_gate`: 入口 =" in brief_none, "首轮也应渲染 review_gate"

    def t_task_and_revision(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        snap = make_snapshot(base, base, ["a.md"])
        kw = dict(objective="o", files=[base / "a.md"], repo=base, scope="full",
                  assertions=[], checks=[], prev="", budget=3, stop_rule="1 轮")
        brief = build_brief(task_status="tasks: 2\nT01 ☑\nT02 ☑", reviewed_revision=str(snap), **kw)
        assert "T01 ☑" in brief and "T02 ☑" in brief, "任务状态未内联"
        assert f"`reviewed_revision`: {snap}" in brief, "快照路径未渲染"
        assert "`reviewed_revision`: unverified-boundary" not in brief, "给了快照不应再写 unverified-boundary"
        brief2 = build_brief(**kw)
        assert "未提供受评原计划任务映射——**实现评审入口不满足" in brief2, "缺任务状态告警"
        assert "unverified-boundary（未提供评审快照或提交" in brief2, "缺 unverified-boundary"

    def t_invalid_tier_and_task(base: Path) -> None:
        import contextlib
        import io
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        out = base / "brief.md"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sys.argv = ["gen_review_brief.py", "--out", str(out), "--objective", "o",
                        "--files", str(base / "a.md"), "--repo", str(base), "--tier", "M"]
            try:
                main()
            except SystemExit as exc:
                assert int(exc.code or 0) == 2, f"--tier 应被 argparse 拒绝（2），实际 {exc.code}"
            else:
                raise AssertionError("--tier 未被拒绝")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sys.argv = ["gen_review_brief.py", "--out", str(out), "--objective", "o",
                        "--files", str(base / "a.md"), "--repo", str(base),
                        "--task-status", str(base / "ghost.txt")]
            code = main()
        assert code == 1, f"任务状态文件不存在应退出 1，实际 {code}"

    def t_invalid_snapshot_and_task(base: Path) -> None:
        import contextlib
        import io
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        out = base / "brief.md"
        digest = hashlib.sha256((base / "a.md").read_bytes()).hexdigest()

        def run_cli(extra: list[str]) -> int:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sys.argv = ["gen_review_brief.py", "--out", str(out), "--objective", "o",
                            "--files", str(base / "a.md"), "--repo", str(base), *extra]
                return main()

        # 不存在的快照目录
        assert run_cli(["--reviewed-revision", str(base / "ghost-snap")]) == 1
        # 目录缺 MANIFEST
        (base / "bad-snap").mkdir()
        assert run_cli(["--reviewed-revision", str(base / "bad-snap")]) == 1
        # 空 MANIFEST（无有效 sha256 条目）
        (base / "empty-snap").mkdir()
        (base / "empty-snap" / "MANIFEST.txt").write_text("files: 0\n", encoding="utf-8")
        assert run_cli(["--reviewed-revision", str(base / "empty-snap")]) == 1
        # 快照未覆盖 --files
        (base / "other-snap").mkdir()
        data = (base / "a.md").read_bytes()
        (base / "other-snap" / "other.md").write_bytes(data)
        (base / "other-snap" / "MANIFEST.txt").write_text(
            f"files: 1\n{digest}  {len(data)}  other.md\n", encoding="utf-8")
        assert run_cli(["--reviewed-revision", str(base / "other-snap")]) == 1
        # 不可解析的提交号（临时目录不是 git 仓库）
        assert run_cli(["--reviewed-revision", "deadbee"]) == 1
        # 非终态任务
        bad_task = base / "task.txt"
        bad_task.write_text("tasks: 1\nT01 ◐ 进行中\n", encoding="utf-8")
        assert run_cli(["--task-status", str(bad_task)]) == 1
        # 缺 tasks 头
        no_header = base / "task2.txt"
        no_header.write_text("T01 ☑\n", encoding="utf-8")
        assert run_cli(["--task-status", str(no_header)]) == 1
        # 行数与 tasks: N 不符
        mismatch = base / "task3.txt"
        mismatch.write_text("tasks: 2\nT01 ☑\n", encoding="utf-8")
        assert run_cli(["--task-status", str(mismatch)]) == 1
        # 正向：真正复制对象且大小/hash匹配的快照 + 终态任务
        good_snap = make_snapshot(base, base, ["a.md"])
        good_task = base / "task4.txt"
        good_task.write_text("tasks: 1\nT01 ☑\n", encoding="utf-8")
        code = run_cli(["--reviewed-revision", str(good_snap),
                        "--task-status", str(good_task)])
        assert code == 0 and out.exists(), f"有效快照应通过，实际 {code}"

    def t_stop_rule_default(base: Path) -> None:
        import subprocess as sp
        text = sp.run([sys.executable, __file__, "--help"], capture_output=True, text=True).stdout
        assert "--tier" not in text, "--tier 已移除"
        assert "--review-round" in text, "缺 --review-round"

    def t_invalid_round_cli(base: Path) -> None:
        import contextlib
        import io
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        out = base / "brief.md"
        for bad in ("0", "-1"):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                sys.argv = ["gen_review_brief.py", "--out", str(out), "--objective", "o",
                            "--files", str(base / "a.md"), "--repo", str(base),
                            "--review-round", bad]
                code = main()
            assert code == 1, f"--review-round {bad} 应退出 1，实际 {code}"
            assert not out.exists(), f"--review-round {bad} 不应写简报"

    def rejects(fn, contains: str = "") -> None:
        try:
            fn()
        except (OSError, ValueError) as exc:
            assert not contains or contains in str(exc), str(exc)
            return
        raise AssertionError("预期拒绝，实际成功")

    def cli(repo: Path, files: list[str], extra: list[str]) -> tuple[subprocess.CompletedProcess, Path]:
        out = repo.parent / "cli-brief.txt"
        out.unlink(missing_ok=True)
        command = [sys.executable, __file__, "--repo", str(repo), "--out", str(out),
                   "--objective", "frozen CLI regression", "--files", *files, *extra]
        result = subprocess.run(command, capture_output=True, text=True)
        return result, out

    def t_frozen_snapshot(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        source = repo / "a.md"
        source.write_bytes(b"BASELINE_BEFORE\n")
        before = make_snapshot(base, repo, ["a.md"])
        data = b"OLD_REVIEWED\r\n  trailing spaces  \r\n\r\n"
        source.write_bytes(data)
        current = make_snapshot(base, repo, ["a.md"], 2)
        source.write_bytes(b"NEW_UNREVIEWED\n")
        brief = render(repo, ["a.md"], reviewed_revision=str(current), diff_base=before)
        assert "OLD_REVIEWED" in brief and "NEW_UNREVIEWED" not in brief
        assert data.decode("utf-8") in brief, "内联时改变了CRLF/空白/末尾换行"
        assert hashlib.sha256(data).hexdigest()[:12] in brief, "不是按原始bytes计算hash"
        assert "+OLD_REVIEWED" in brief and "-BASELINE_BEFORE" in brief
        source.unlink()
        result, out = cli(repo, ["a.md"], ["--reviewed-revision", str(current)])
        assert result.returncode == 0 and "OLD_REVIEWED" in out.read_text(), result.stderr
        rejects(lambda: render(repo, ["missing.md"], reviewed_revision=str(current)))

    def t_frozen_commit(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        source = repo / "a.md"
        source.write_bytes(b"BASELINE\n")
        before = make_snapshot(base, repo, ["a.md"])
        frozen = b"COMMITTED_OLD\r\n"
        source.write_bytes(frozen)
        revision = commit(repo)
        source.write_bytes(b"WORKTREE_NEW\n")
        brief = render(repo, ["a.md"], reviewed_revision=revision[:8], diff_base=before)
        assert f"`reviewed_revision`: {revision}" in brief, "未固定完整commit SHA"
        assert "COMMITTED_OLD" in brief and "WORKTREE_NEW" not in brief
        assert "+COMMITTED_OLD" in brief and hashlib.sha256(frozen).hexdigest()[:12] in brief
        source.unlink()
        result, out = cli(repo, ["a.md"], ["--reviewed-revision", revision[:8]])
        assert result.returncode == 0 and "COMMITTED_OLD" in out.read_text(), result.stderr
        rejects(lambda: render(repo, ["not-committed.md"], reviewed_revision=revision))
        outside = base / "external.md"
        outside.write_text("external")
        rejects(lambda: render(repo, [str(outside)], reviewed_revision=revision), "仓外")
        source.symlink_to(outside)
        rejects(lambda: render(repo, ["a.md"], reviewed_revision=revision), "Symlink")

    def t_commit_delete(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        (repo / "gone.md").write_bytes(b"DELETED_FROZEN_LINE\n")
        before = make_snapshot(base, repo, ["gone.md"])
        commit(repo)
        (repo / "gone.md").unlink()
        revision = commit(repo, "delete object")
        (repo / "gone.md").write_bytes(b"UNREVIEWED_RECREATED\n")
        brief = render(repo, ["gone.md"], reviewed_revision=revision, diff_base=before)
        assert "已删除" in brief and "--- base/gone.md" in brief and "+++ /dev/null" in brief
        assert "-DELETED_FROZEN_LINE" in brief and "UNREVIEWED_RECREATED" not in brief
        rejects(lambda: render(repo, ["gone.md"], reviewed_revision=revision), "不含普通文件")
        rejects(lambda: render(repo, ["typo.md"], reviewed_revision=revision, diff_base=before))

    def t_git_special_objects(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        (repo / "plain.md").write_text("ordinary\n")
        (repo / "linked.md").symlink_to("plain.md")
        revision = commit(repo)
        (repo / "linked.md").unlink()
        rejects(lambda: render(repo, ["linked.md"], reviewed_revision=revision), "普通 blob")
        git(repo, "update-index", "--add", "--cacheinfo", f"160000,{revision},module")
        git(repo, "-c", "user.name=Review Test", "-c", "user.email=review@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
            "commit", "--quiet", "-m", "gitlink object")
        linked_revision = git(repo, "rev-parse", "HEAD")
        rejects(lambda: render(repo, ["module"], reviewed_revision=linked_revision), "普通 blob")
        rejects(lambda: render(repo, ["module/child.md"], reviewed_revision=linked_revision), "父项")

    def t_invalid_utf8(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        source = repo / "bad.md"
        source.write_bytes(b"INVALID_UTF8\xff\n")
        snap = make_snapshot(base, repo, ["bad.md"])
        revision = commit(repo)
        for frozen in (None, str(snap), revision):
            result, out = cli(repo, ["bad.md"], ["--reviewed-revision", frozen] if frozen else [])
            assert result.returncode == 1 and not out.exists(), (frozen, result.stdout, result.stderr)
            assert "utf-8" in result.stderr, result.stderr
        source.write_bytes(b"valid now\n")
        rejects(lambda: render(repo, ["bad.md"], diff_base=snap), "utf-8")

    def t_snapshot_rejections(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        (repo / "a.md").write_bytes(b"FROZEN\n")
        snap = make_snapshot(base, repo, ["a.md"])
        manifest = snap / "MANIFEST.txt"
        original = manifest.read_text()
        row = original.splitlines()[-1]
        for text in (original + "files: 1\n", original.replace("files: 1", "files: 2"),
                     original.replace("files: 1", "files: 2") + row + "\n",
                     original + "bad manifest\n", original.replace("a.md", "../escape"),
                     original.replace("a.md", "MANIFEST.txt")):
            manifest.write_text(text)
            result, out = cli(repo, ["a.md"], ["--reviewed-revision", str(snap)])
            assert result.returncode == 1 and not out.exists(), (text, result.stdout, result.stderr)
        manifest.write_text(original)
        target = snap / "a.md"
        for content in (b"DRIFT!\n", b"size drift is different\n", None):
            if content is None:
                target.unlink()
            else:
                target.write_bytes(content)
            result, out = cli(repo, ["a.md"], ["--reviewed-revision", str(snap)])
            assert result.returncode == 1 and not out.exists(), (result.stdout, result.stderr)
        target.symlink_to(repo / "a.md")
        rejects(lambda: render(repo, ["a.md"], reviewed_revision=str(snap)), "Symlink")

    def t_legacy_external_rebuild(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        outside = base / "same.md"
        outside.write_bytes(b"external\n")
        snap = base / "legacy"
        snap.mkdir()
        (snap / "same.md").write_bytes(outside.read_bytes())
        digest = hashlib.sha256(outside.read_bytes()).hexdigest()
        (snap / "MANIFEST.txt").write_text(f"files: 1\n{digest}  9  same.md\n")
        rejects(lambda: render(repo, [str(outside)], reviewed_revision=str(snap)), "重新生成快照")
        current = make_snapshot(base, repo, [str(outside)])
        outside.unlink()
        assert "external" in render(repo, [str(outside)], reviewed_revision=str(current))

    def t_read_once(base: Path) -> None:
        from unittest.mock import patch
        import workflow_lib.review_bundle as library
        repo = base / "repo"
        repo.mkdir()
        (repo / "a.md").write_bytes(b"BASELINE\n")
        before = make_snapshot(base, repo, ["a.md"])
        (repo / "a.md").write_bytes(b"FIXED_BYTES\n")
        current = make_snapshot(base, repo, ["a.md"], 2)
        real_read = library.read_regular
        counts: dict[Path, int] = {}
        def one_read(path: Path) -> bytes:
            counts[path] = counts.get(path, 0) + 1
            assert counts[path] == 1, f"对象被重复读取：{path}"
            data = real_read(path)
            if path == current / "a.md":
                path.write_bytes(b"LATER_SNAPSHOT_CHANGE\n")
            return data
        with patch.object(library, "read_regular", one_read):
            brief = render(repo, ["a.md"], reviewed_revision=str(current), diff_base=before)
        assert "FIXED_BYTES" in brief and "+FIXED_BYTES" in brief
        assert "LATER_SNAPSHOT_CHANGE" not in brief

    def t_task_closure(base: Path) -> None:
        text = ("tasks: 4\nT01 | deps: - | status: ☑\nT02 | deps: T01 | status: ☑\n"
                "T03 | deps: T02 | status: ☐\nT04 | deps: T03 | status: ⚠ 阻塞\n")
        assert validate_task_status(text, ["T02"]) == ["T01", "T02"]
        (base / "a.md").write_bytes(b"reviewed\n")
        snap = make_snapshot(base, base, ["a.md"])
        status = base / "tasks.txt"
        status.write_text(text)
        result, out = cli(base, ["a.md"], ["--reviewed-revision", str(snap),
                                          "--task-status", str(status), "--task-ids", "T02"])
        assert result.returncode == 0, result.stderr
        brief = out.read_text()
        for token in ("受评原计划任务 IDs：T02", "闭包（含受评任务）：T01, T02", "T03 | deps: T02 | status: ☐",
                      "未自动验证它与原计划内容一致", "没有漏任务或漏前置"):
            assert token in brief, token
        rejects(lambda: validate_task_status(text))  # Legacy input still requires every row terminal.
        rejects(lambda: validate_task_status(text.replace("T01 | deps: - | status: ☑",
                                                         "T01 | deps: - | status: ◐"), ["T02"]), "T01")
        rejects(lambda: validate_task_status(text, ["T03"]), "T03")
        rejects(lambda: validate_task_status(text, ["UNKNOWN"]), "未知")
        rejects(lambda: validate_task_status(text, ["T02", "T02"]), "唯一")
        rejects(lambda: validate_task_status(text.replace("deps: T01", "deps: MISSING"), ["T02"]), "遗漏")
        rejects(lambda: validate_task_status(text.replace("T04 | deps: T03", "T04 | deps: T04"), ["T02"]), "成环")
        rejects(lambda: validate_task_status(text.replace("tasks: 4", "tasks: 5"), ["T02"]), "行数")
        rejects(lambda: validate_task_status(text.replace("T04 | deps: T03", "T03 | deps: T03"), ["T02"]), "重复")
        rejects(lambda: validate_task_status(text.replace("T01 | deps: - |", "T01 |"), ["T02"]), "逐行声明")
        rejects(lambda: validate_task_status(text.replace("deps: T01", "deps: "), ["T02"]), "前置")
        rejects(lambda: validate_task_status(text + "tasks: 4\n", ["T02"]), "唯一")
        rejects(lambda: render(base, ["a.md"], task_ids=["T02"]), "同时给出")
        assert validate_task_status("tasks: 2\nT01 ☑\nT02 — 本期不做") == []

    def t_document_delta_and_outputs(base: Path) -> None:
        repo = base / "repo"
        repo.mkdir()
        source = repo / "proposal.md"
        source.write_text("# 原提案\n", encoding="utf-8")
        before = make_snapshot(base, repo, [source.name])
        body = "# 新提案\n```sh\nprintf example\n```\n## 正文续节\n"
        source.write_text(body, encoding="utf-8")
        current = make_snapshot(base, repo, [source.name], 2)
        evidence = ["--review-type", "document", "--reviewed-revision", str(current)]
        result, out = cli(repo, [source.name], evidence)
        assert result.returncode == 0, result.stderr
        brief = out.read_text()
        assert "`review_type`: document" in brief and "任务状态不适用" in brief
        assert "````text\n" + body + "````" in brief
        assert "任务未完成/" not in brief
        for incomplete in ([], ["--diff-base", str(before)], ["--no-previous-findings", "REV-1 无遗留"]):
            result, out = cli(repo, [source.name], [*evidence, "--scope", "delta", *incomplete])
            assert result.returncode != 0 and not out.exists()
        result, out = cli(repo, [source.name], [
            *evidence, "--scope", "delta", "--diff-base", str(before),
            "--no-previous-findings", "REV-1 无遗留",
        ])
        assert result.returncode == 0, result.stderr
        assert "## §1.1" in out.read_text() and "REV-1 无遗留" in out.read_text()
        result = subprocess.run([sys.executable, __file__, "--repo", str(repo), "--out", str(source),
                                 "--files", source.name, *evidence], capture_output=True)
        assert result.returncode != 0 and source.read_text() == body

    def t_wrong_snapshot_repo(base: Path) -> None:
        original = base / "original"
        other = base / "other"
        original.mkdir()
        other.mkdir()
        (original / "a.md").write_text("ORIGINAL")
        (other / "a.md").write_text("OTHER")
        snap = make_snapshot(base, original, ["a.md"])
        args = ["--review-type", "document", "--reviewed-revision", str(snap)]
        result, out = cli(other, ["a.md"], args)
        assert result.returncode != 0 and not out.exists() and "快照仓库不匹配" in result.stderr
        result, out = cli(other, ["a.md"], [*args, "--snapshot-source-repo", str(original)])
        assert result.returncode == 0 and "ORIGINAL" in out.read_text()

    for name, fn in [("五个必填字段与内联正文齐备", t_basic),
                     ("断言表解析（注释/缺列容错）", t_assertion_parsing),
                     ("检查输出支持 @文件引用", t_check_file_ref),
                     ("检查输出退出码三段式与未验证标注", t_exit_code_checks),
                     ("diff-base 生成 §1.1 与新增/基线未列标注", t_diff_base),
                     ("reuse-round 渲染与首轮不渲染", t_reuse_round),
                     ("review_gate 入口/出口与轮次仅记录", t_review_gate),
                     ("任务状态与 reviewed_revision 渲染", t_task_and_revision),
                     ("--tier 拒绝与任务状态文件缺失", t_invalid_tier_and_task),
                     ("快照不存在/缺 MANIFEST/非终态任务拒绝", t_invalid_snapshot_and_task),
                     ("--tier 已移除、--review-round 保留", t_stop_rule_default),
                     ("review-round 非法值拒绝且不写简报", t_invalid_round_cli),
                     ("仓外同名文件按稳定来源映射配对diff", t_diff_base_name_collision),
                     ("快照OLD/工作树NEW或已删只内联冻结bytes及同一diff新侧", t_frozen_snapshot),
                     ("固定fullSHA读取commit/工作树不同或已删", t_frozen_commit),
                     ("提交删除有基线时生成delete diff，缺对象不补工作树", t_commit_delete),
                     ("提交symlink/gitlink与非目录父项拒绝", t_git_special_objects),
                     ("草稿/快照/提交/基线严格UTF8不替换", t_invalid_utf8),
                     ("简报拒绝坏清单/重复/逃逸/缺快照文件/大小hash漂移", t_snapshot_rejections),
                     ("旧仓外basename无来源映射明确要求重建", t_legacy_external_rebuild),
                     ("§1与diff复用一次读取的冻结内容", t_read_once),
                     ("原计划映射闭包终态、后继待办及unknown/cycle/遗漏拒绝", t_task_closure),
                     ("冻结文档入口、delta 必需项、围栏与输出保护", t_document_delta_and_outputs),
                     ("跨仓快照拒绝，显式原仓迁移可回放", t_wrong_snapshot_repo)]:
        case(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
