#!/usr/bin/env python3
"""check-testcases.py — 校验 testcases.yaml 与 spec/qa 验收点（AC）的覆盖一致性。

解决痛点 12：把 markdown 散文 AC 表固化为结构化 yaml 后，机械校验：
  - 每条 AC（spec/qa/acceptance.md 的 M##-AC-##）至少 1 条用例
  - 无孤儿用例（用例的 ac 不在 AC 表中）
  - 每条用例必须有 steps 与 expect（design 必须表述操作过程 + 预期结果）

AC 定义的识别口径：取 acceptance.md 中**第一个含行首 AC 编号（`| M01-AC-01 |`）的连续表格块**
作为定义表——后续的覆盖映射表 / 引用不再计入定义，避免把引用当定义；识别不到定义表时退回
全文匹配并显式告警（此时引用也会计入定义）。本脚本是目标仓侧的按需工具（门外检查），
不声称已接入 validate.py 或 CI——接入与否以各仓自己的门配置为准。

用法：
  python3 scripts/check-testcases.py <feature-dir>
    <feature-dir>/spec/qa/acceptance.md   —— AC 来源
    <feature-dir>/testing/<*> /testcases.yaml —— 用例来源（可多处）
  python3 scripts/check-testcases.py --self-test   —— 临时目录跑覆盖矩阵自测

退出码：0 通过 / 1 发现问题 / 2 参数或解析错误
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

AC_RE = re.compile(r"\b(M\d{2}-AC-\d{2})\b")
AC_ROW_RE = re.compile(r"^\s*\|\s*(M\d{2}-AC-\d{2})\s*\|")


def _table_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            cur.append(line)
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks


def collect_acs(acceptance: Path) -> tuple[set[str], str]:
    """返回 (定义的 AC 集合, 识别口径说明)。定义表 = 第一个含行首 AC 的表格块。"""
    if not acceptance.is_file():
        return set(), "文件不存在"
    text = acceptance.read_text(encoding="utf-8", errors="replace")
    for block in _table_blocks(text):
        ids = {m.group(1) for line in block if (m := AC_ROW_RE.match(line))}
        if ids:
            return ids, f"定义表=首个含行首 AC 的表格块（{len(ids)} 条）"
    print("[warn] acceptance.md 未识别到行首 AC 定义行（| M01-AC-01 |）；退回全文匹配，"
          "引用也会计入定义——建议 AC 定义表把编号放行首列", file=sys.stderr)
    return set(AC_RE.findall(text)), "全文匹配（未识别到定义表）"


def _parse_simple_cases(text: str) -> list[dict]:
    """无 PyYAML 时的降级解析：只支持本脚本文档化的扁平用例格式
    （每条以 `- ac:` 开头；键取标量，`steps: [a, b]` 取内联列表）。"""
    cases: list[dict] = []
    cur: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.lstrip().startswith("- "):
            if cur:
                cases.append(cur)
            cur = {}
            line = line.lstrip()[2:]
        if cur is None or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if not val:
            continue  # 逐行列表形态本格式未使用，跳过
        if val.startswith("[") and val.endswith("]"):
            cur[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            cur[key] = val.strip("'\"")
    if cur:
        cases.append(cur)
    return cases


def collect_yaml_ac_cases(feature_dir: Path):
    cases = []
    for yf in feature_dir.rglob("testcases.yaml"):
        if "/reviews/snapshot-" in yf.as_posix():
            # 评审快照里的历史副本不参与覆盖判定，否则旧用例会掩盖当前缺口（假绿）
            print(f"[warn] 跳过评审快照内的 testcases.yaml：{yf}")
            continue
        text = yf.read_text(encoding="utf-8")
        try:
            import yaml  # 延迟导入；缺失时降级到内置扁平解析器
        except ImportError:
            data = _parse_simple_cases(text)
        else:
            data = yaml.safe_load(text) or []
        for c in data:
            if isinstance(c, dict) and "ac" in c:
                cases.append((c.get("ac"), c, yf))
    return cases


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        return _self_test()
    if len(sys.argv) < 2:
        print("用法：python3 scripts/check-testcases.py <feature-dir>（或 --self-test）", file=sys.stderr)
        return 2
    feature_dir = Path(sys.argv[1]).resolve()
    if not feature_dir.is_dir():
        print(f"[错误] 目录不存在：{feature_dir}", file=sys.stderr)
        return 2

    acs, _ = collect_acs(feature_dir / "spec" / "qa" / "acceptance.md")
    if not acs:
        print(f"[warn] 在 {feature_dir/'spec/qa/acceptance.md'} 未找到 AC 编号（M##-AC-##）")
    cases = collect_yaml_ac_cases(feature_dir)
    if not cases:
        print("[warn] 未找到任何 testcases.yaml；若已有 AC 请先生成用例文件")
        return 1

    covered = set()
    problems = []
    for ac, case, yf in cases:
        if ac not in acs:
            problems.append(f"孤儿用例：{yf} 中 ac={ac} 不在 AC 表中")
            continue
        covered.add(ac)
        if not case.get("steps"):
            problems.append(f"缺 steps：{yf} 中 ac={ac}（design 必须表述操作过程）")
        if not case.get("expect"):
            problems.append(f"缺 expect：{yf} 中 ac={ac}（design 必须表述预期结果）")

    uncovered = acs - covered
    for u in sorted(uncovered):
        problems.append(f"未覆盖 AC：{u} 没有任何用例")

    if problems:
        print("发现问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"通过：{len(acs)} 条 AC 全部覆盖，{len(cases)} 条用例均含 steps/expect")
    return 0


def _self_test() -> int:
    """临时目录自测：定义表识别（引用不计入定义）、全覆盖通过、缺用例报未覆盖、孤儿报错。"""
    import tempfile

    ok = True

    def run_case(name: str, files: dict[str, str], expect_exit: int, expect_text: str) -> None:
        nonlocal ok
        base = Path(tempfile.mkdtemp(prefix="af-tc-selftest-"))
        try:
            (base / "spec" / "qa").mkdir(parents=True)
            (base / "testing" / "demo").mkdir(parents=True)
            for rel, content in files.items():
                p = base / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
            import io, contextlib
            buf_out, buf_err = io.StringIO(), io.StringIO()
            argv = sys.argv
            sys.argv = ["check-testcases.py", str(base)]
            try:
                with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                    code = main()
            finally:
                sys.argv = argv
            output = buf_out.getvalue() + buf_err.getvalue()
            passed = code == expect_exit and expect_text in output
            print(f"{'PASS' if passed else 'FAIL'}  {name}（exit={code}）"
                  + ("" if passed else f" — 期望 exit={expect_exit} 且含「{expect_text}」，实际输出：\n{output}"))
            ok = ok and passed
        finally:
            import shutil
            shutil.rmtree(base, ignore_errors=True)

    acceptance = (
        "# 验收\n\n| 编号 | 场景 | 可观察结果 |\n| --- | --- | --- |\n"
        "| M01-AC-01 | 正确凭据登录 | 进入工作台 |\n"
        "| M01-AC-02 | 错误凭据 | 提示错误 |\n\n"
        "## 覆盖映射\n\n| AC | 用例 | 状态 |\n| --- | --- | --- |\n"
        "| M01-AC-01 | TC-01 | 待覆盖 |\n| M01-AC-02 | TC-02 | 待覆盖 |\n"
    )
    yaml_ok = (
        "- ac: M01-AC-01\n  title: 登录成功\n  steps: [打开页面, 输入凭据, 提交]\n"
        "  expect: 进入工作台\n- ac: M01-AC-02\n  title: 登录失败\n  steps: [打开页面, 输入错误凭据]\n"
        "  expect: 提示错误\n"
    )
    run_case("全覆盖通过（映射表引用不计为额外定义）", {
        "spec/qa/acceptance.md": acceptance, "testing/demo/testcases.yaml": yaml_ok,
    }, 0, "通过：2 条 AC 全部覆盖")

    run_case("缺用例 → 未覆盖 AC", {
        "spec/qa/acceptance.md": acceptance,
        "testing/demo/testcases.yaml": yaml_ok.split("- ac: M01-AC-02")[0],
    }, 1, "未覆盖 AC：M01-AC-02")

    run_case("引用编号不在定义表 → 孤儿用例", {
        "spec/qa/acceptance.md": acceptance,
        "testing/demo/testcases.yaml": yaml_ok + "- ac: M99-AC-99\n  title: 幻影\n  steps: [x]\n  expect: y\n",
    }, 1, "孤儿用例")

    run_case("缺 steps/expect → 报缺口", {
        "spec/qa/acceptance.md": acceptance,
        "testing/demo/testcases.yaml": "- ac: M01-AC-01\n  title: 空壳\n  expect: 有\n",
    }, 1, "缺 steps")

    run_case("评审快照内的 testcases.yaml 被跳过（快照孤儿不计）", {
        "spec/qa/acceptance.md": acceptance,
        "testing/demo/testcases.yaml": yaml_ok,
        "reviews/snapshot-1/testing/demo/testcases.yaml": "- ac: M99-AC-99\n  title: 快照旧用例\n  steps: [x]\n  expect: y\n",
    }, 0, "通过：2 条 AC 全部覆盖")

    print(f"\n{'全部通过' if ok else '存在失败'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
