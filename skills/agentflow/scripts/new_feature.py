#!/usr/bin/env python3
"""new_feature.py — 一键开批次：复制 feature 模板全树 + 登记 index，AI 只填内容。

解决痛点：每开一个批次，AI 要手工复制十几份模板、建目录、登记索引——批次开箱从
「十几次手写」变一条命令；确定性动作交给脚本，AI 的力气花在 proposal 内容上
（蓝图 3.2 / 改动实施方案落地顺序 #4）。

用法：
  python3 new_feature.py --hub <枢纽路径> --slug <短名> [--date YYYY-MM-DD] [--dry-run]
                         [--template-dir <templates/feature>]

动作（纯机械，零 AI）：
  1. 目标 = <hub>/features/<date>-<slug>/；已存在即报错退出，绝不覆盖
  2. 复制 templates/feature 全树（保持 proposal/ spec/ design/ plan/ prototype/ 相对结构）
  3. 建 testing/ 目录（.gitkeep 占位）
  4. 在 <hub>/index.md 的「批次清单」表追加一行（自动适配 3 列 / 4 列表头；找不到表则
     打印手工登记行，不盲插）
  5. 打印「待 AI 填写清单」

退出码：0 成功 / 1 冲突或环境问题 / 2 用法错误
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path


def build_index_row(index_text: str, rel_dir: str) -> str | None:
    """按批次清单表头列数生成登记行；找不到表头返回 None。"""
    m = re.search(r"^\| 批次 \|.*$", index_text, flags=re.MULTILINE)
    if not m:
        return None
    header_cols = [c.strip() for c in m.group(0).strip().strip("|").split("|")]
    cells = {"批次": f"`features/{rel_dir}`",
             "一句话范围": "<待填：做什么、不做什么>",
             "状态": "<待填>",
             "进度板": f"`features/{rel_dir}/README.md`"}
    row = "| " + " | ".join(cells.get(h, "<待填>") for h in header_cols) + " |"
    lines = index_text.splitlines()
    insert_at = None
    for i, line in enumerate(lines):
        if re.match(r"^\|\s*`?features/", line) or (line.strip().startswith("|") and insert_at is not None
                                                    and i == insert_at + 1 and not line.lstrip().startswith("| --")):
            insert_at = i
    if insert_at is None:
        insert_at = m.group(0) and next(
            i for i, line in enumerate(lines)
            if line == m.group(0) or line.strip() == m.group(0).strip()
        ) + 1  # 表头下一行是分隔行，行插在分隔行之后
        insert_at += 1
    lines.insert(insert_at + 1, row)
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="一键开批次（复制模板全树 + 登记 index）")
    ap.add_argument("--hub", default=None, help="文档枢纽根（含 index.md 与 features/）")
    ap.add_argument("--slug", default=None, help="批次短名（feature-<date>-<slug>）")
    ap.add_argument("--date", default=date.today().isoformat(), help="批次日期（默认今天，YYYY-MM-DD）")
    ap.add_argument("--template-dir", default=None,
                    help="feature 模板目录（默认：脚本上两级 /templates/feature）")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不写文件")
    ap.add_argument("--self-test", action="store_true", help="临时目录跑立项矩阵自测")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not (args.hub and args.slug):
        ap.error("需要 --hub 与 --slug（或 --self-test）")

    hub = Path(args.hub).resolve()
    if not hub.is_dir():
        print(f"[错误] 枢纽不存在：{hub}", file=sys.stderr)
        return 2
    index_md = hub / "index.md"
    if not index_md.is_file():
        print(f"[错误] 枢纽缺 index.md：{index_md}", file=sys.stderr)
        return 1

    template_dir = (Path(args.template_dir).resolve() if args.template_dir
                    else Path(__file__).resolve().parents[1] / "templates" / "feature")
    if not template_dir.is_dir():
        print(f"[错误] 模板目录不存在：{template_dir}", file=sys.stderr)
        return 2

    rel_dir = f"feature-{args.date}-{args.slug}"
    target = hub / "features" / rel_dir
    if target.exists():
        print(f"[错误] 批次目录已存在，不覆盖：{target}", file=sys.stderr)
        return 1

    files = sorted(p for p in template_dir.rglob("*") if p.is_file())
    print(f"[计划] 复制 {len(files)} 个模板文件 -> {target}")
    for p in files:
        print(f"  - {p.relative_to(template_dir).as_posix()}")
    print("[计划] 建 testing/ 占位；登记 index.md 批次清单一行")
    if args.dry_run:
        print("\n[dry-run] 未写入任何文件。")
        return 0

    shutil.copytree(template_dir, target)
    (target / "testing").mkdir(parents=True, exist_ok=True)
    (target / "testing" / ".gitkeep").write_text("", encoding="utf-8")

    index_text = index_md.read_text(encoding="utf-8")
    new_text = build_index_row(index_text, rel_dir)
    if new_text is None:
        print("[warn] index.md 未找到「批次清单」表，请手工登记一行：")
        print(f"  | `features/{rel_dir}` | <待填：一句话范围> | `features/{rel_dir}/README.md` |")
    else:
        index_md.write_text(new_text, encoding="utf-8")
        print(f"[ok] index.md 已登记一行（features/{rel_dir}）")

    print("\n待 AI 填写清单：")
    print("  □ 各模板 <feature 名> 与占位符按本批事实填写；frontmatter 的日期与基线 HEAD 由会话供给")
    print("  □ proposal §1.4 范围穷举表按领域维度逐行决策；存量面处置表逐项标注")
    print("  □ index.md 一句话范围回填；plan 起稿后回填段落映射")
    return 0


def _self_test() -> int:
    import tempfile

    TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "feature"
    if not TEMPLATE.is_dir():
        print(f"[错误] 自测需要模板目录：{TEMPLATE}", file=sys.stderr)
        return 2

    INDEX_3COL = ("# 索引\n\n## 批次清单\n\n| 批次 | 一句话范围 | 进度板 |\n| --- | --- | --- |\n")
    INDEX_4COL = ("# 索引\n\n## 批次清单\n\n| 批次 | 一句话范围 | 状态 | 进度板 |\n| --- | --- | --- | --- |\n")
    results: list[tuple[str, bool, str]] = []

    def run(hub: Path, slug: str = "demo", extra: list[str] | None = None) -> int:
        argv = ["new_feature.py", "--hub", str(hub), "--slug", slug, "--date", "2026-11-04", *(extra or [])]
        orig = sys.argv
        sys.argv = argv
        try:
            return main()
        finally:
            sys.argv = orig

    import contextlib
    import io

    def case(name: str, fn) -> None:
        base = Path(tempfile.mkdtemp(prefix="af-newfeat-selftest-"))
        try:
            fn(base)
            results.append((name, True, ""))
        except AssertionError as exc:
            results.append((name, False, str(exc)))
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def t_clean_3col(base: Path) -> None:
        hub = base / "hub"
        hub.mkdir()
        (hub / "index.md").write_text(INDEX_3COL, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            assert run(hub) == 0
        target = hub / "features" / "feature-2026-11-04-demo"
        for rel in ["README.md", "proposal/proposal.md", "spec/be/backend.md", "spec/qa/acceptance.md",
                    "design/be/backend.md", "plan/execution.md", "testing/.gitkeep"]:
            assert (target / rel).is_file(), f"缺 {rel}"
        text = (hub / "index.md").read_text(encoding="utf-8")
        assert "| `features/feature-2026-11-04-demo` |" in text, "index 未登记"
        row_count = sum(1 for ln in text.splitlines() if ln.lstrip().startswith("| `features/"))
        assert row_count == 1, f"批次清单应恰有一行登记，实际 {row_count}"

    def t_duplicate(base: Path) -> None:
        hub = base / "hub"
        hub.mkdir()
        (hub / "index.md").write_text(INDEX_3COL, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            assert run(hub) == 0
            before = (hub / "index.md").read_text(encoding="utf-8")
            assert run(hub) == 1, "重复立项应报错退出"
        assert (hub / "index.md").read_text(encoding="utf-8") == before, "重复运行改了 index"

    def t_dry_run(base: Path) -> None:
        hub = base / "hub"
        hub.mkdir()
        (hub / "index.md").write_text(INDEX_3COL, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            assert run(hub, extra=["--dry-run"]) == 0
        assert not (hub / "features").exists(), "dry-run 写入了文件"

    def t_4col_compat(base: Path) -> None:
        hub = base / "hub"
        hub.mkdir()
        (hub / "index.md").write_text(INDEX_4COL, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            assert run(hub) == 0
        text = (hub / "index.md").read_text(encoding="utf-8")
        row = [ln for ln in text.splitlines() if "| `features/feature-2026-11-04-demo`" in ln][0]
        assert len([c for c in row.strip().strip("|").split("|")]) == 4, "4 列表头应生成 4 列行"

    for name, fn in [
        ("干净立项：模板全树 + testing 占位 + index 登记", t_clean_3col),
        ("重复立项拒绝且零改动", t_duplicate),
        ("dry-run 零写入", t_dry_run),
        ("4 列旧表头兼容", t_4col_compat),
    ]:
        case(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
