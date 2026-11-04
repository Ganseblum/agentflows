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

  --checks 文件格式：每条一行，`命令 :: 逐字输出`（或 `命令 :: @路径`）
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import date
from pathlib import Path

DEFAULT_STOP_RULE = (
    "本轮 full 评审；阻塞项修复后最多 1 轮 delta；非阻塞建议写入 residual_risks 后收口，"
    "不自动开第 3 轮。同一原因两轮无进展即停并交代。"
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


def parse_checks(path: Path | None) -> list[tuple[str, str]]:
    if not path or not path.is_file():
        return []
    out: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "::" not in raw:
            continue
        cmd, _, body = raw.partition("::")
        body = body.strip()
        if body.startswith("@"):
            p = Path(body[1:].strip())
            body = p.read_text(encoding="utf-8") if p.is_file() else f"<文件不存在：{p}>"
        out.append((cmd.strip(), body))
    return out


def build_brief(*, objective: str, files: list[Path], repo: Path, scope: str,
                assertions: list[tuple[str, str, str]], checks: list[tuple[str, str]],
                prev: str, budget: int, stop_rule: str) -> str:
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
    L.append(f"- `output_budget`: findings ≤{budget} 条，报告正文 ≤6000 字符；超限按严重度截断并声明\n")

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
        for cmd, body in checks:
            L.append(f"**`{cmd}`**\n")
            L.append("```text")
            L.append(body.rstrip())
            L.append("```\n")
        L.append("> 这些检查已由 supervisor 跑过。你不必重跑，也不必采信摘要——正文就是逐字输出。\n")
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

    brief = build_brief(
        objective=args.objective, files=files, repo=repo, scope=args.scope,
        assertions=parse_assertions(Path(args.assertions) if args.assertions else None),
        checks=parse_checks(Path(args.checks) if args.checks else None),
        prev=(Path(args.prev_findings).read_text(encoding="utf-8") if args.prev_findings
              and Path(args.prev_findings).is_file() else ""),
        budget=args.budget, stop_rule=args.stop_rule,
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

    for name, fn in [("五个必填字段与内联正文齐备", t_basic),
                     ("断言表解析（注释/缺列容错）", t_assertion_parsing),
                     ("检查输出支持 @文件引用", t_check_file_ref)]:
        case(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
