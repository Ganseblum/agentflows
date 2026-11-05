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
并强制写出五个必填字段：review_scope / reviewed_revision / inline_objects / stop_rule / output_budget
（契约见 references/contracts.md）。缺任何一项的简报，reviewer 可以直接回 blocked。

用法：
  python3 gen_review_brief.py --out brief.md --objective "确认登录..."
      --files spec/qa/acceptance.md design/be/backend.md
      [--repo .] [--scope full|delta|spot] [--assertions asserts.txt]
      [--checks checks.txt] [--prev-findings prev.txt] [--budget 12]
      [--stop-rule "..."] [--self-test]

  --assertions 文件格式（一行一条）：
      断言 | 判据 | 核实点
      例：退出失败后刷新会恢复登录态 | 与 G3 冲突 | design/be/backend.md:181

  --checks 文件格式：每条一行，`命令 :: exit=N :: 逐字输出`（或 `命令 :: exit=N :: @路径`）；
      旧两段式 `命令 :: 逐字输出` / `命令 :: @路径` 仍接受，但渲染为「退出码未验证」
  --diff-base 目录：按仓库相对路径与该目录（评审快照）逐文件生成 unified diff，内联为 §1.1；
      delta 轮的变化面以 §1.1 为准，§1 全文用于核对上下文（reviewer 无 Bash，diff 必须内联）
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

DEFAULT_STOP_RULE = (
    "本轮 full 评审；阻塞项修复后最多 1 轮 delta，且不得超过本档上限"
    "（S/M = 2 轮、L = 3 轮）；非阻塞建议写入 residual_risks 后收口，"
    "同一原因两轮无进展即停并交代。收口口径：P0/P1 与证据有效性类 finding"
    "（如假绿断言）阻塞收口；文档措辞/计数类 P2/P3 默认写入 residual_risks 收口，"
    "不为其另开 delta 轮。"
)


def git_head(repo: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "no-git"
    except (OSError, subprocess.TimeoutExpired):
        return "no-git"


def parse_assertions(path: Path | None) -> list[tuple[str, str, str]]:
    if not path or not path.is_file():
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
    if not path or not path.is_file():
        return []
    out: list[tuple[str, str, int | None]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "::" not in raw:
            continue
        cmd, _, rest = raw.partition("::")
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
            body = p.read_text(encoding="utf-8") if p.is_file() else f"<文件不存在：{p}>"
        out.append((cmd.strip(), body, exit_code))
    return out


def build_brief(*, objective: str, files: list[Path], repo: Path, scope: str,
                assertions: list[tuple[str, str, str]], checks: list[tuple[str, str, int | None]],
                prev: str, budget: int, stop_rule: str,
                diff_base: Path | None = None, reuse_round: int | None = None,
                review_round: int | None = None, tier: str = "M") -> str:
    head = git_head(repo)
    L: list[str] = []
    L.append(f"# 评审简报（{date.today().isoformat()} 生成）\n")
    L.append("> 本简报由 `scripts/gen_review_brief.py` 生成，**手写简报不被接受**。")
    L.append("> reviewer 收到后先核五个必填字段（下方元信息块），缺一项即可回 `blocked: 简报不合格`。\n")

    L.append("## 元信息（五个必填字段）\n")
    L.append(f"- `review_scope`: {scope}")
    L.append(f"- `reviewed_revision`: {head}（工作区快照；未提交内容以本简报 §1 的内联正文为准）")
    L.append(f"- `inline_objects`: 下方 §1 逐文件内联（{len(files)} 个文件，逐字）")
    L.append(f"- `stop_rule`: {stop_rule}")
    if reuse_round is not None and prev.strip():
        L.append(
            f"- `reviewer_reuse`: 本轮为同一 reviewer 的第 {reuse_round} 轮（累计）；"
            "上轮结论锚点见 §4。报告须声明「本结论部分依赖上轮判断」。")
    elif reuse_round is not None:
        L.append(
            "- `reviewer_reuse`: 未附上轮锚点——简报不合格：--reuse-round 必须与 --prev-findings "
            "同时给出，复用声明没有上轮结论锚点不成立。")
    elif prev.strip():
        L.append(
            "- `reviewer_reuse`: 未声明累计轮次（--reuse-round 缺失）；复用同一 reviewer 时契约要求"
            "写明累计轮次与上轮锚点，报告须声明「本结论部分依赖上轮判断」。")
    L.append(f"- `output_budget`: findings ≤{budget} 条，报告正文 ≤6000 字符；超限按严重度截断并声明")
    if review_round is not None:
        max_rounds = {"S": 2, "M": 2, "L": 3}[tier]
        if review_round > max_rounds:
            L.append(
                f"- `review_budget`: 本轮为第 {review_round} 轮，超出 {tier} 档默认上限 {max_rounds} 轮"
                "（S/M = full 1 + delta ≤1；L = full 1 + delta 1 + 收口核对 1）——**偏离分档默认**，"
                "须在批次记录写明超出理由与停止条件，否则按流程缺陷记入评审记录。")
        else:
            L.append(f"- `review_budget`: 第 {review_round} 轮 / {tier} 档默认上限 {max_rounds} 轮，在档内。")
    L.append("")

    L.append("## 目标\n")
    L.append(objective.strip() + "\n")

    L.append(f"## §1 评审对象（逐字内联，共 {len(files)} 个文件）\n")
    for f in files:
        if not f.is_file():
            L.append(f"### `{f}` — **文件不存在，简报不合格**\n")
            continue
        body = f.read_text(encoding="utf-8", errors="replace")
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
        L.append(f"### `{f}`（sha256 前 12 位 `{digest}`，{len(body.splitlines())} 行）\n")
        L.append("```text")
        L.append(body.rstrip())
        L.append("```\n")

    if diff_base is not None:
        L.append(f"## §1.1 逐文件 diff（相对 `{diff_base}`；delta 轮的变化面以本节为准，§1 全文用于核对上下文）\n")
        files_rels: list[tuple[Path, Path]] = []
        for f in files:
            try:
                rel = f.resolve().relative_to(repo.resolve())
            except ValueError:
                rel = Path(f.name)
            files_rels.append((f, rel))
        listed: set[str] = set()
        rel_values = [rel for _, rel in files_rels]
        dup_rels = {r for r in rel_values if rel_values.count(r) > 1}
        if dup_rels:
            L.append(
                "> 警告：本轮清单含仓外同名文件（"
                + "、".join(sorted(r.as_posix() for r in dup_rels))
                + "），基线配对不可靠，以下文件的 diff 仅作参考。\n")
        for f, rel in files_rels:
            listed.add(rel.as_posix())
            if rel in dup_rels:
                L.append(f"### `{rel.as_posix()}` — **基线配对不可靠（仓外同名文件）**\n")
                continue
            base = diff_base / rel
            if not base.is_file():
                L.append(f"### `{rel.as_posix()}` — **新增（基线无此文件）**\n")
                continue
            base_lines = base.read_text(encoding="utf-8", errors="replace").splitlines()
            cur_lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            if base_lines == cur_lines:
                L.append(f"### `{rel.as_posix()}` — 与基线一致（无 diff）\n")
                continue
            patch = "\n".join(difflib.unified_diff(
                base_lines, cur_lines,
                fromfile=f"base/{rel.as_posix()}", tofile=f"current/{rel.as_posix()}",
                lineterm=""))
            L.append(f"### `{rel.as_posix()}`（{len(patch.splitlines())} 行 diff）\n")
            L.append("```text")
            L.append(patch)
            L.append("```\n")
        extras = sorted(
            p.relative_to(diff_base.resolve()).as_posix()
            for p in diff_base.resolve().rglob("*")
            if p.is_file()
            and p.name != "MANIFEST.txt"
            and p.relative_to(diff_base.resolve()).as_posix() not in listed
        )
        if extras:
            L.append(f"> 基线存在但本轮清单未列的文件（{len(extras)} 个）；若属删除/移出评审面，须显式处置：")
            for rel in extras:
                L.append(f"> - `{rel}`")
            L.append("")
        if not listed:
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
            L.append("```text")
            L.append(body.rstrip())
            L.append("```\n")
        L.append("> 这些检查已由 supervisor 跑过。你不必重跑，也不必采信摘要——正文就是逐字输出；")
        L.append("> 标注「退出码未验证」的检查不得引用为「已通过」，要么补退出码重跑，要么按未运行处理。\n")
    else:
        L.append("> 未附检查输出。涉及「跑过没跑过」的断言按 `unverified` 处理。\n")

    L.append("## §4 上轮未关闭项（delta 轮必填）\n")
    if prev.strip():
        L.append(prev.strip() + "\n")
    else:
        L.append("> 首轮评审，无上轮遗留。\n")

    L.append("## 交付形态\n")
    L.append("```yaml")
    L.append("decision: approved | changes_requested | blocked")
    L.append("status: complete | partial")
    L.append("findings: 每条 = 严重度 + 位置(path:line) / 原因 / 代价 / 建议修法")
    L.append("previous_findings: 每条 = id + severity + status(closed|unverified) + cost_replay（delta 轮必填）")
    L.append("passed: PASS A1, PASS A3 …（一行一条）")
    L.append("residual_risks: 未覆盖面与建议")
    L.append("```")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="生成评审简报（内联对象 + 五必填字段）")
    ap.add_argument("--out", help="输出文件路径")
    ap.add_argument("--objective", default="", help="本轮评审目标（一句话）")
    ap.add_argument("--files", nargs="*", default=[], help="被评审文件（相对 --repo）")
    ap.add_argument("--repo", default=".", help="仓库根（默认当前目录）")
    ap.add_argument("--scope", default="full", choices=["full", "delta", "spot"])
    ap.add_argument("--assertions", default=None, help="断言表文件（断言 | 判据 | 核实点）")
    ap.add_argument("--checks", default=None, help="已执行检查文件（命令 :: 输出 或 命令 :: @文件）")
    ap.add_argument("--prev-findings", default=None, help="上轮未关闭项文件")
    ap.add_argument("--budget", type=int, default=12, help="findings 上限（默认 12）")
    ap.add_argument("--stop-rule", default=DEFAULT_STOP_RULE)
    ap.add_argument("--diff-base", default=None,
                    help="基线目录（如评审快照）；给出时生成 §1.1 逐文件 diff")
    ap.add_argument("--reuse-round", type=int, default=None,
                    help="复用同一 reviewer 的累计轮次（--prev-findings 存在时渲染 reviewer_reuse 声明）")
    ap.add_argument("--review-round", type=int, default=None,
                    help="本轮在该阶段的评审轮次（≥1）；给出时渲染 review_budget 并检查分档上限")
    ap.add_argument("--tier", default="M", choices=["S", "M", "L"],
                    help="评审成本档位（默认 M）；S/M 默认上限 2 轮、L 3 轮")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not args.out or not args.files:
        ap.error("需要 --out 与 --files（或 --self-test）")

    repo = Path(args.repo).resolve()
    files = [(repo / f).resolve() if not Path(f).is_absolute() else Path(f) for f in args.files]
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print(f"[错误] 被评审文件不存在：{'、'.join(missing)}", file=sys.stderr)
        print("       内联对象缺失的简报会被 reviewer 判 blocked，故此处直接失败。", file=sys.stderr)
        return 1

    diff_base = Path(args.diff_base).resolve() if args.diff_base else None
    if diff_base is not None and not diff_base.is_dir():
        print(f"[错误] --diff-base 不是目录：{diff_base}", file=sys.stderr)
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

    brief = build_brief(
        objective=args.objective, files=files, repo=repo, scope=args.scope,
        assertions=parse_assertions(Path(args.assertions) if args.assertions else None),
        checks=parse_checks(Path(args.checks) if args.checks else None),
        prev=(Path(args.prev_findings).read_text(encoding="utf-8") if args.prev_findings
              and Path(args.prev_findings).is_file() else ""),
        budget=args.budget, stop_rule=args.stop_rule,
        diff_base=diff_base, reuse_round=args.reuse_round,
        review_round=args.review_round, tier=args.tier,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(brief, encoding="utf-8")
    print(f"[ok] 简报 -> {out}（{len(brief)} 字符，内联 {len(files)} 个文件）")
    print("     五必填字段已写入元信息块。")
    return 0


def _self_test() -> int:
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def case(name, fn):
        base = Path(tempfile.mkdtemp(prefix="af-brief-"))
        try:
            fn(base)
            results.append((name, True, ""))
        except AssertionError as exc:
            results.append((name, False, str(exc)))
        finally:
            import shutil
            shutil.rmtree(base, ignore_errors=True)

    def t_basic(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n内容行\n", encoding="utf-8")
        (base / "as.txt").write_text("退出失败恢复登录 | 与 G3 冲突 | a.md:2\n", encoding="utf-8")
        (base / "ck.txt").write_text("pytest -q :: 3 passed\n", encoding="utf-8")
        brief = build_brief(objective="确认登录", files=[base / "a.md"], repo=base, scope="full",
                            assertions=parse_assertions(base / "as.txt"),
                            checks=parse_checks(base / "ck.txt"), prev="", budget=12,
                            stop_rule="1 轮")
        for token in ["`review_scope`: full", "`stop_rule`: 1 轮", "`output_budget`: findings ≤12",
                      "内容行", "退出失败恢复登录", "3 passed", "sha256 前 12 位"]:
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
                            prev="", budget=3, stop_rule="1 轮", diff_base=base / "base")
        assert "## §1.1" in brief, "缺 §1.1 diff 节"
        assert "-旧行" in brief and "+新行" in brief, "缺 diff 正文"
        assert "**新增（基线无此文件）**" in brief, "缺新增标注"
        assert "gone.md" in brief, "缺基线未列文件提示"

    def t_reuse_round(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        kw = dict(objective="o", files=[base / "a.md"], repo=base, scope="delta",
                  assertions=[], checks=[], budget=3, stop_rule="1 轮")
        brief1 = build_brief(prev="上轮遗留", reuse_round=4, **kw)
        assert "第 4 轮（累计）" in brief1 and "部分依赖上轮判断" in brief1, "reuse_round=4 未渲染"
        brief2 = build_brief(prev="上轮遗留", **kw)
        assert "未声明累计轮次" in brief2, "缺未声明标记"
        brief3 = build_brief(prev="", **kw)
        assert "reviewer_reuse" not in brief3, "首轮不应渲染 reviewer_reuse"
        brief4 = build_brief(prev="", reuse_round=4, **kw)
        assert "未附上轮锚点——简报不合格" in brief4, "reuse_round 缺 prev 应判简报不合格"
        assert "第 4 轮（累计）" not in brief4, "无锚点时不得渲染累计声明"

    def t_diff_base_name_collision(base: Path) -> None:
        (base / "x").mkdir()
        (base / "y").mkdir()
        (base / "bd").mkdir()
        (base / "x" / "same.md").write_text("一\n", encoding="utf-8")
        (base / "y" / "same.md").write_text("二\n", encoding="utf-8")
        (base / "bd" / "same.md").write_text("基线\n", encoding="utf-8")
        brief = build_brief(objective="o", files=[base / "x" / "same.md", base / "y" / "same.md"],
                            repo=base / "x", scope="full", assertions=[], checks=[],
                            prev="", budget=3, stop_rule="1 轮", diff_base=base / "bd")
        assert "基线配对不可靠（仓外同名文件）" in brief, "缺同名告警"
        assert "-基线" not in brief.split("**基线配对不可靠（仓外同名文件）**")[-1], "不可靠文件不应生成 diff"

    def t_review_budget(base: Path) -> None:
        (base / "a.md").write_text("# 文档 A\n", encoding="utf-8")
        kw = dict(objective="o", files=[base / "a.md"], repo=base, scope="delta",
                  assertions=[], checks=[], prev="", budget=3, stop_rule="1 轮")
        brief_m2 = build_brief(review_round=2, tier="M", **kw)
        assert "第 2 轮 / M 档默认上限 2 轮，在档内" in brief_m2, "M 档第 2 轮应判在档内"
        brief_m3 = build_brief(review_round=3, tier="M", **kw)
        assert "超出 M 档默认上限 2 轮" in brief_m3 and "偏离分档默认" in brief_m3, "M 档第 3 轮应判偏离"
        brief_l3 = build_brief(review_round=3, tier="L", **kw)
        assert "在档内" in brief_l3, "L 档第 3 轮应判在档内"
        brief_s2 = build_brief(review_round=2, tier="S", **kw)
        assert "S 档默认上限 2 轮，在档内" in brief_s2, "S 档第 2 轮应判在档内"
        brief_s3 = build_brief(review_round=3, tier="S", **kw)
        assert "超出 S 档默认上限 2 轮" in brief_s3, "S 档第 3 轮应判偏离"
        brief_l4 = build_brief(review_round=4, tier="L", **kw)
        assert "超出 L 档默认上限 3 轮" in brief_l4, "L 档第 4 轮应判偏离"
        brief_none = build_brief(**kw)
        assert "review_budget" not in brief_none, "未给轮次不应渲染 review_budget"

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

    for name, fn in [("五个必填字段与内联正文齐备", t_basic),
                     ("断言表解析（注释/缺列容错）", t_assertion_parsing),
                     ("检查输出支持 @文件引用", t_check_file_ref),
                     ("检查输出退出码三段式与未验证标注", t_exit_code_checks),
                     ("diff-base 生成 §1.1 与新增/基线未列标注", t_diff_base),
                     ("reuse-round 渲染与首轮不渲染", t_reuse_round),
                     ("review_budget 分档上限与偏离标记", t_review_budget),
                     ("review-round 非法值拒绝且不写简报", t_invalid_round_cli)]:
        case(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
