#!/usr/bin/env python3
"""check_ac_clarity.py — AC 文案可定性软检（模糊词 + 无量纲）。

解决什么：spec/qa 的 AC 出现「无明显差异」「轻量占位」这类无法判定的措辞，评审时才发现
（F8 类），返工一轮。本脚本按验收表逐行扫描「可观察结果」列：命中模糊词且同行没有任何
可测量/可观察锚点（数字+单位、比较符、role/data-testid/HTTP 状态码、具体引号文案）时报警。

默认是软层：报警只打印 WARN，退出码 0；`--strict` 才把 WARN 升为失败（退出 1）。
不替代独立评审，只把「明显不可判定」的那一类提前暴露。

用法：
  python3 check_ac_clarity.py <spec/qa/acceptance.md ...>
  python3 check_ac_clarity.py <feature 目录>          # 递归找 spec/qa/acceptance.md 与 acceptance.md
  python3 check_ac_clarity.py <文件> --strict          # WARN 也退出 1

退出码：0 = 无问题（或软层仅 WARN）；1 = --strict 下有 WARN；2 = 输入/格式错误
（路径不存在、没找到验收表、识别到表但没有 AC 行）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 不可判定措辞：出现即要求同行有可测量/可观察锚点
VAGUE_TERMS = (
    "无明显差异", "无明显", "轻量", "正常", "合理", "友好", "流畅", "较快", "快速",
    "适当", "尽量", "良好", "合适", "及时", "稳定", "易用", "简洁", "美观",
    "足够", "较多", "较少", "差不多", "基本", "大概", "尽可能",
)
# 可测量/可观察锚点：数量+单位、比较符、具体可观察载体。引号内容不直接算锚点——
# 「显示「正常」」里的引号只是把模糊词圈出来，仍需按模糊词判定（见 has_anchor）。
ANCHOR_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*(?:ms|毫秒|s|秒|min|分钟|次|px|%|条|个|元|KB|MB|行|字|步|轮))"
    r"|([<>≤≥=]\s*\d)"
    r"|(role\s*=)|(data-testid)|(aria-)|(HTTP\s*\d{3})",
)
# 引号/否定语境里的词是「要求出现/禁止出现」的具体文案，不按模糊词处理
QUOTED_RE = re.compile(r"「[^」]*」|\"[^\"]*\"")
NEGATION_PREFIX = ("不得", "禁止", "不要", "不出现")
AC_ID_RE = re.compile(r"([A-Za-z0-9]+-AC-\d+|\bAC-\d+)")
SEPARATOR_RE = re.compile(r"^\|?[\s:\-|]+\|?$")


def find_acceptance_files(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for p in paths:
        if p.is_file():
            found.append(p)
        elif p.is_dir():
            # 两种布局取并集：spec/qa/acceptance.md 与任意 acceptance.md
            found.extend(sorted(p.rglob("spec/qa/acceptance.md")))
            found.extend(sorted(p.rglob("acceptance.md")))
        else:
            raise FileNotFoundError(f"路径不存在：{p}")
    seen: set[Path] = set()
    out: list[Path] = []
    for f in found:
        r = f.resolve()
        if r not in seen:
            seen.add(r)
            out.append(f)
    return out


def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")]


def normalize_cell(cell: str) -> str:
    return cell.replace("**", "").replace("`", "").strip()


def has_anchor(cell: str) -> bool:
    """数字/比较符/具体载体，或引号内不含模糊词的具体文案，才算可观察锚点。"""
    if ANCHOR_RE.search(cell):
        return True
    for quoted in QUOTED_RE.findall(cell):
        inner = quoted[1:-1]
        if inner and not any(term in inner for term in VAGUE_TERMS):
            return True
    return False


def is_vague(cell: str) -> list[str]:
    """返回该单元格命中的模糊词；只豁免否定语境中的引号文案（如「不得出现『正常』」）。"""
    masked = cell
    for quoted in QUOTED_RE.findall(cell):
        idx = cell.find(quoted)
        prefix = cell[max(0, idx - 4):idx]
        if any(neg in prefix for neg in NEGATION_PREFIX):
            masked = masked.replace(quoted, "")
    hits: list[str] = []
    for term in VAGUE_TERMS:
        if term in masked:
            hits.append(term)
    return hits


def scan_file(path: Path) -> tuple[list[tuple[str, str, str, str]], int, int, int]:
    """返回 ([(AC id, 模糊词们, 单元格原文, 文件)], 验收表数, AC 行数, 缺列行数)。"""
    rows: list[tuple[str, str, str, str]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_table = False
    result_col: int | None = None
    tables = 0
    ac_rows = 0
    malformed = 0
    for raw in lines:
        stripped = raw.strip()
        if "|" not in stripped:
            in_table = False
            result_col = None
            continue
        cells = split_row(raw)
        norm = [normalize_cell(c) for c in cells]
        header_result = next((i for i, c in enumerate(norm) if c.startswith("可观察结果")), None)
        has_ac_header = any("验收点" in c for c in norm)
        if header_result is not None and has_ac_header:
            in_table = True
            result_col = header_result
            tables += 1
            continue
        if not in_table or result_col is None:
            continue
        if SEPARATOR_RE.match(stripped):
            continue
        ac_id = None
        for candidate in cells:
            m = AC_ID_RE.search(candidate)
            if m:
                ac_id = m.group(1)
                break
        if not ac_id:
            continue
        if result_col >= len(cells):
            malformed += 1
            continue
        cell = cells[result_col].strip()
        if not cell or cell in ("—", "-", "（填写）"):
            continue
        ac_rows += 1
        if has_anchor(cell):
            continue
        hits = is_vague(cell)
        if hits:
            rows.append((ac_id, " / ".join(hits), cell, str(path)))
    return rows, tables, ac_rows, malformed


def main() -> int:
    ap = argparse.ArgumentParser(description="AC 文案可定性软检（模糊词 + 无量纲）")
    ap.add_argument("paths", nargs="*", help="acceptance.md 或 feature 目录")
    ap.add_argument("--strict", action="store_true", help="WARN 也退出 1")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not args.paths:
        ap.error("需要至少一个文件或目录（或 --self-test）")

    try:
        files = find_acceptance_files([Path(p) for p in args.paths])
    except FileNotFoundError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 2
    if not files:
        print("[错误] 未找到 acceptance.md", file=sys.stderr)
        return 2

    total_warn = 0
    for f in files:
        try:
            rows, tables, ac_rows, malformed = scan_file(f)
        except OSError as exc:
            print(f"[错误] 读取失败：{exc}", file=sys.stderr)
            return 2
        if tables == 0:
            print(f"[错误] {f} 未识别到验收表（表头需含「验收点」与「可观察结果」）", file=sys.stderr)
            return 2
        if malformed:
            print(f"[错误] {f} 有 {malformed} 行 AC 缺「可观察结果」列——格式不完整，拒绝核对", file=sys.stderr)
            return 2
        if ac_rows == 0:
            print(f"[错误] {f} 识别到验收表但没有 AC 行（验收点列需含 M01-AC-01 形态）", file=sys.stderr)
            return 2
        print(f"扫描 {f}：{ac_rows} 条 AC 行，{len(rows)} 条 WARN")
        for ac_id, terms, cell, _ in rows:
            total_warn += 1
            print(f"  WARN  {ac_id}  模糊词「{terms}」且无可测量锚点：{cell[:80]}")

    if total_warn == 0:
        print("PASS  未发现「模糊词 + 无量纲」的 AC 行")
        return 0
    if args.strict:
        print(f"汇总：{total_warn} 条 WARN（--strict：WARN 视为失败）")
        return 1
    print(f"汇总：{total_warn} 条 WARN（软层，不阻塞；--strict 可判失败）")
    return 0


def _self_test() -> int:
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def case(name, fn):
        base = Path(tempfile.mkdtemp(prefix="af-ac-"))
        try:
            fn(base)
            results.append((name, True, ""))
        except AssertionError as exc:
            results.append((name, False, str(exc)))
        finally:
            import shutil
            shutil.rmtree(base, ignore_errors=True)

    def write(base: Path, body: str, name: str = "acceptance.md") -> Path:
        f = base / name
        f.write_text(body, encoding="utf-8")
        return f

    def t_vague_and_anchor(base: Path) -> None:
        f = write(base, (
            "# 验收\n\n"
            "| 验收点 | 验收目标 | 可观察结果 | 优先级 |\n"
            "| --- | --- | --- | --- |\n"
            "| M01-AC-01 | 布局正确 | 与原型无明显差异 | P1 |\n"
            "| M01-AC-02 | 加载态 | 轻量占位 | P1 |\n"
            "| M01-AC-03 | 响应时间 | 5 次采样 P50 差 < 50ms | P1 |\n"
            "| M01-AC-04 | 提示 | 显示「正在恢复登录状态」文案 | P1 |\n"
            "| M01-AC-05 | 错误提示 | 不得出现「正常」字样 | P1 |\n"
        ))
        rows, tables, ac_rows, malformed = scan_file(f)
        ids = {ac for ac, _, _, _ in rows}
        assert tables == 1 and ac_rows == 5 and malformed == 0, (tables, ac_rows, malformed)
        assert "M01-AC-01" in ids and "M01-AC-02" in ids, ids
        assert "M01-AC-03" not in ids, "有数字阈值不应报警"
        assert "M01-AC-04" not in ids, "有具体引号文案不应报警"
        assert "M01-AC-05" not in ids, "否定语境/引号文案不应报警"

    def t_quoted_vague(base: Path) -> None:
        # 引号里是模糊词时，引号不构成锚点；引号里是具体文案时才是锚点
        f = write(base, (
            "| 验收点 | 可观察结果 |\n| --- | --- |\n"
            "| M01-AC-01 | 显示「正常」提示 |\n"
            "| M01-AC-02 | 显示「正在恢复登录状态」文案 |\n"
        ))
        rows, tables, ac_rows, malformed = scan_file(f)
        ids = {ac for ac, _, _, _ in rows}
        assert "M01-AC-01" in ids, "引号内模糊词应仍报警"
        assert "M01-AC-02" not in ids, "引号内具体文案应作为锚点"

    def t_malformed_rows(base: Path) -> None:
        f = write(base, (
            "| 验收点 | 可观察结果 |\n| --- | --- |\n| M01-AC-01 | 正常 |\n"
            "| M01-AC-02 |\n"  # 缺结果列
        ))
        rows, tables, ac_rows, malformed = scan_file(f)
        assert malformed == 1, f"缺列行应计入 malformed，实际 {malformed}"
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sys.argv = ["check_ac_clarity.py", str(f)]
            code = main()
        assert code == 2, f"缺列行应退出 2，实际 {code}"

    def t_template_header(base: Path) -> None:
        # 模板真实表头带括号说明；粗体/反引号也应归一化
        f = write(base, (
            "| 验收点 | 验收目标 | 可观察结果（断言什么） | 优先级 |\n"
            "| --- | --- | --- | --- |\n"
            "| M02-AC-01 | 布局 | **正常**显示 | P1 |\n"
            "| M02-AC-02 | 状态 | `响应`正常 | P1 |\n"
        ))
        rows, tables, ac_rows, malformed = scan_file(f)
        assert tables == 1 and ac_rows == 2 and malformed == 0, (tables, ac_rows, malformed)
        ids = {ac for ac, _, _, _ in rows}
        assert "M02-AC-01" in ids, "带括号表头应被识别"
        assert "M02-AC-02" in ids, "裸名词「响应」不应豁免模糊词"

    def t_no_table_is_error(base: Path) -> None:
        f = write(base, "# 没有表格\n\n普通段落。\n")
        rows, tables, ac_rows, malformed = scan_file(f)
        assert tables == 0 and not rows
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sys.argv = ["check_ac_clarity.py", str(f)]
            code = main()
        assert code == 2, f"无验收表应退出 2，实际 {code}"

    def t_cli(base: Path) -> None:
        f = write(base, (
            "| 验收点 | 可观察结果 |\n| --- | --- |\n| M02-AC-09 | 正常显示 |\n"
        ))
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sys.argv = ["check_ac_clarity.py", str(f)]
            code_soft = main()
        assert code_soft == 0, f"软层应退出 0，实际 {code_soft}"
        assert "WARN" in buf.getvalue() and "不阻塞" in buf.getvalue()
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            sys.argv = ["check_ac_clarity.py", str(f), "--strict"]
            code_strict = main()
        assert code_strict == 1, f"--strict 应退出 1，实际 {code_strict}"
        assert "WARN 视为失败" in buf2.getvalue(), "严格模式提示文案不对"

    def t_directory_union(base: Path) -> None:
        (base / "a" / "spec" / "qa").mkdir(parents=True)
        (base / "b").mkdir()
        write(base / "a" / "spec" / "qa", "| 验收点 | 可观察结果 |\n| --- | --- |\n| M01-AC-01 | 正常 |\n")
        write(base / "b", "| 验收点 | 可观察结果 |\n| --- | --- |\n| M02-AC-01 | 正常 |\n")
        files = find_acceptance_files([base])
        assert len(files) == 2, f"两个布局应取并集，实际 {files}"

    def t_missing(base: Path) -> None:
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sys.argv = ["check_ac_clarity.py", str(base / "ghost.md")]
            code = main()
        assert code == 2, f"路径不存在应退出 2，实际 {code}"

    for name, fn in [
        ("模糊词识别 / 锚点 / 引号与否定豁免", t_vague_and_anchor),
        ("引号内模糊词仍报警、具体文案作锚点", t_quoted_vague),
        ("缺列行拒绝核对退出 2", t_malformed_rows),
        ("模板表头（括号说明/粗体/反引号）与裸名词不漏报", t_template_header),
        ("无验收表退出 2（不报假 PASS）", t_no_table_is_error),
        ("软层退出 0 / --strict 退出 1", t_cli),
        ("目录两种布局取并集", t_directory_union),
        ("路径不存在退出 2", t_missing),
    ]:
        case(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
