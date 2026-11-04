#!/usr/bin/env python3
"""check_records.py — 目标仓批次跨文件一致性检查（门外工具，按需运行）。

解决痛点：doc_chain 的 C 编号判单文件结构；**跨文件事实漂移**（映射不回填、轮次断言与
评审记录数不符、计划状态与执行结论矛盾）没有机器管。本脚本是这些检查的快迭代载体
（不动受保护的 docchain 面）；跑稳后再按 DEC-2026-002/004/005 的拍板结论决定是否并门。

检查项（每项独立报告，error 影响退出码，warn 只提示）：
  R1  testing plan 已落盘时，spec/qa 的 AC×用例映射表不得残留「待覆盖」占位
  R2  批次 README 断言的评审轮次 == reviews/ 目录实际记录数（warn：散文断言按启发式识别）
  R3  plan 声明「全部完成」时，最新 run 的 decision 必须为 pass
  R4  releases/pending-test.md「未做与残余」条目应携带指向 plan R 表或 ISS 的引用（warn）
  R5  最新 run 结果表中 fail/blocked 行必须有非「—」证据，且引用的文件相对 run 目录存在
  R6  AC 覆盖闭合：plan 注册表「来源」列 ∪ testcases.yaml 的 ac ≡ spec/qa 定义表 AC 集合
      （「来源」列是唯一权威，由 gate/testing.py 强制非空；不读 frontmatter 的聚合副本）

用法：
  python3 check_records.py <feature-dir> [--hub <hub 根，用于定位 releases/>]
  python3 check_records.py --self-test

退出码：0 通过（warn 不影响）/ 1 有 error / 2 参数错误
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AC_RE = re.compile(r"\b(M\d{2}-AC-\d{2})\b")
AC_ROW_RE = re.compile(r"^\s*\|\s*(M\d{2}-AC-\d{2})\s*\|")
ROUND_RE = re.compile(r"评审[^。\n]{0,12}?(\d+)\s*轮|(\d+)\s*轮[^。\n]{0,8}评审")
RESULT_ROW_RE = re.compile(r"^\|\s*(TC-[\w-]+)\s*\|\s*(pass|fail|blocked|not-run)\s*\|")


def defined_acs(acceptance: Path) -> set[str]:
    """AC 定义 = acceptance.md 第一个含行首 AC 编号的连续表格块（与 check-testcases.py 同口径）。"""
    if not acceptance.is_file():
        return set()
    text = acceptance.read_text(encoding="utf-8", errors="replace")
    block: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            block.append(line)
        elif block:
            ids = {m.group(1) for ln in block if (m := AC_ROW_RE.match(ln))}
            if ids:
                return ids
            block = []
    ids = {m.group(1) for ln in block if (m := AC_ROW_RE.match(ln))}
    if ids:
        return ids
    return set(AC_RE.findall(text))


def frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict = {}
    for line in text[4:end].splitlines():
        key, sep, val = line.partition(":")
        if sep:
            data[key.strip()] = val.strip().strip('"')
    return data


def latest_run(feature_dir: Path) -> Path | None:
    runs = sorted(feature_dir.glob("testing/**/run-*.md"))
    return runs[-1] if runs else None


def latest_plan(feature_dir: Path) -> Path | None:
    plans = sorted(feature_dir.glob("plan/*.md"))
    return plans[-1] if plans else None


def latest_test_plan(feature_dir: Path) -> Path | None:
    """testing/ 下的用例库（test-planner 产出）；AC 覆盖只从这里取，不从 plan/execution.md 取。"""
    plans = sorted(feature_dir.glob("testing/**/plan-*.md"))
    return plans[-1] if plans else None


# ---------------------------------------------------------------- checks

def r1_mapping_placeholder(feature_dir: Path, hub: Path | None = None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    acceptance = feature_dir / "spec" / "qa" / "acceptance.md"
    plans = list(feature_dir.glob("testing/**/plan-*.md"))
    if not (acceptance.is_file() and plans):
        return out
    text = acceptance.read_text(encoding="utf-8", errors="replace")
    residue = [ln.strip() for ln in text.splitlines() if "待覆盖" in ln and ln.lstrip().startswith("|")]
    if residue:
        out.append(("error", f"R1 spec/qa 映射残留「待覆盖」×{len(residue)} 行，而 testing plan 已落盘（{plans[-1].name}）——AC↔用例映射须回填或指向 testcases.yaml"))
    return out


def r2_review_rounds(feature_dir: Path, hub: Path | None = None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    readme = feature_dir / "README.md"
    reviews_dir = feature_dir / "reviews"
    if not (readme.is_file() and reviews_dir.is_dir()):
        return out
    count = len(list(reviews_dir.glob("review-*.md")))
    if count == 0:
        return out
    text = readme.read_text(encoding="utf-8", errors="replace")
    claimed = set()
    for m in ROUND_RE.finditer(text):
        num = m.group(1) or m.group(2)
        if num:
            claimed.add(int(num))
    # 变更记录里引用历史轮数是合法的；只对「最高断言」判漂移
    if claimed and max(claimed) > count:
        out.append(("warn", f"R2 README 断言评审 {max(claimed)} 轮，reviews/ 实际记录 {count} 份（review-*.md）——散文断言为启发式识别，人工确认是否漂移"))
    return out


def r3_plan_vs_run(feature_dir: Path, hub: Path | None = None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    plan, run = latest_plan(feature_dir), latest_run(feature_dir)
    if not (plan and run):
        return out
    decision = frontmatter(run.read_text(encoding="utf-8", errors="replace")).get("decision", "")
    plan_text = plan.read_text(encoding="utf-8", errors="replace")
    claims_done = re.search(r"全部任务已完成|全部完成|已全部通过|整体完成", plan_text)
    if claims_done and decision and decision != "pass":
        out.append(("error", f"R3 plan 声明全部完成，但最新 run {run.name} 的 decision={decision or '缺失'}——状态矛盾"))
    return out


def r4_pending_test_links(feature_dir: Path, hub: Path | None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    base = hub if hub else feature_dir.parent.parent
    pending = base / "releases" / "pending-test.md"
    if not pending.is_file():
        return out
    text = pending.read_text(encoding="utf-8", errors="replace")
    section = re.split(r"^##\s+未做与残余\s*$", text, flags=re.MULTILINE)
    if len(section) < 2:
        return out
    for line in section[1].splitlines():
        s = line.strip()
        if not s or s.startswith(">") or s.startswith("#") or s.startswith("|--") or s == "|":
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            body = " ".join(cells)
        else:
            body = s
        if not body or set(body) <= {"-", " ", "/"}:
            continue
        if "plan/execution" not in body and not re.search(r"\bR0?\d\b|\bISS-", body):
            out.append(("warn", f"R4 pending-test「未做与残余」条目缺指向（plan R 表或 ISS-*）：{body[:48]}"))
    return out


def r5_run_evidence(feature_dir: Path, hub: Path | None = None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    run = latest_run(feature_dir)
    if not run:
        return out
    in_results = False
    for line in run.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            in_results = line.strip().startswith("## 结果")
            continue
        if not in_results:
            continue
        m = RESULT_ROW_RE.match(line)
        if not m:
            continue
        case, status = m.group(1), m.group(2)
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        evidence = cells[3] if len(cells) > 3 else ""
        if status in {"fail", "blocked"}:
            if not evidence or set(evidence) <= {"-", " ", "/"}:
                out.append(("error", f"R5 run {run.name}: {case} 状态 {status} 但证据列为空——fail/blocked 必须有原始输出引用"))
            elif not evidence.startswith("`") and "：" not in evidence and "http" not in evidence:
                ref = run.parent / evidence
                if not ref.is_file():
                    out.append(("error", f"R5 run {run.name}: {case} 证据文件不存在（相对 run 目录）：{evidence}"))
    return out


def plan_registry_sources(plan: Path) -> set[str]:
    """从 plan 的 `## 用例` 注册表「来源」列派生本计划覆盖的 AC 集合。

    这是 AC 覆盖的**唯一权威**：注册表每个用例一行，「来源」列指向 spec/qa 的 AC 编号
    （或被评 `gate/testing.py` 强制非空，T10）。不得在 frontmatter 另写一份聚合副本——
    副本一定会漂移（见 doc_chain 的「一条事实一个权威载体」）。
    """
    text = plan.read_text(encoding="utf-8", errors="replace")
    in_registry = False
    header_cols: list[str] = []
    source_idx = -1
    found: set[str] = set()
    for line in text.splitlines():
        if line.startswith("## "):
            in_registry = line.strip() == "## 用例"
            header_cols, source_idx = [], -1
            continue
        if not in_registry or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not header_cols:
            header_cols = cells
            source_idx = next((i for i, h in enumerate(cells) if h == "来源"), -1)
            continue
        if set("".join(cells)) <= set("-: "):
            continue  # 分隔行
        if source_idx == -1 or source_idx >= len(cells):
            continue
        if not re.match(r"^TC-", cells[0]):
            continue  # 只认用例行
        found.update(AC_RE.findall(cells[source_idx]))
    return found


def r6_ac_coverage(feature_dir: Path, hub: Path | None = None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    plan = latest_test_plan(feature_dir)
    acceptance = feature_dir / "spec" / "qa" / "acceptance.md"
    if not (plan and acceptance.is_file()):
        return out
    defined = defined_acs(acceptance)
    if not defined:
        return out  # 无 AC 体系，跳过
    # 覆盖集合是**派生值**：取 plan 注册表来源列，存在 testcases.yaml 时并集（yaml 权威）
    derived = plan_registry_sources(plan)
    yaml_refs: set[str] = set()
    for yf in feature_dir.rglob("testcases.yaml"):
        if "/reviews/snapshot-" in yf.as_posix():
            continue
        for line in yf.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.match(r"^\s*-?\s*ac:", line):
                yaml_refs.update(AC_RE.findall(line))
    refs = derived | yaml_refs
    if not refs:
        out.append(("error", "R6 plan 注册表「来源」列与 testcases.yaml 都未声明任何 AC——无法判定覆盖（无 AC 体系时 spec/qa 不应有 AC 定义表）"))
        return out
    if refs != defined:
        only_ref = sorted(refs - defined)
        only_def = sorted(defined - refs)
        detail = []
        if only_ref:
            detail.append(f"用例引用了定义表里没有的 AC：{'、'.join(only_ref)}")
        if only_def:
            detail.append(f"无任何用例覆盖：{'、'.join(only_def)}")
        out.append(("error", f"R6 AC 覆盖不闭合（权威＝plan 注册表来源列 ∪ testcases.yaml）——{'；'.join(detail)}"))
    return out


CHECKS = [r1_mapping_placeholder, r2_review_rounds, r3_plan_vs_run, r4_pending_test_links,
          r5_run_evidence, r6_ac_coverage]


def run_checks(feature_dir: Path, hub: Path | None) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for check in CHECKS:
        findings.extend(check(feature_dir, hub))
    return findings


# ---------------------------------------------------------------- self-test

def _self_test() -> int:
    import shutil
    import tempfile

    ACCEPTANCE = (
        "# 验收\n\n| 编号 | 场景 |\n| --- | --- |\n| M01-AC-01 | 登录成功 |\n| M01-AC-02 | 登录失败 |\n\n"
        "## 覆盖映射\n\n| AC | 用例 | 状态 |\n| --- | --- | --- |\n| M01-AC-01 | TC-01 | 已覆盖 |\n"
    )
    REGISTRY_BOTH = (
        "\n## 用例\n\n| 用例 ID | 级别 | 优先级 | 标题 | 入口 | 来源 |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| TC-01-01 | e2e | P0 | 登录成功 | 按钮 | M01-AC-01 |\n"
        "| TC-01-02 | e2e | P0 | 登录失败 | 按钮 | M01-AC-02 |\n"
    )
    REGISTRY_ONE = (
        "\n## 用例\n\n| 用例 ID | 级别 | 优先级 | 标题 | 入口 | 来源 |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| TC-01-01 | e2e | P0 | 登录成功 | 按钮 | M01-AC-01 |\n"
    )
    PLAN_DONE = "---\ntest_plan_id: TP-X\n---\n\n# 计划\n\n全部任务已完成（30/30）。\n"
    PLAN_PARTIAL = "---\ntest_plan_id: TP-X\n---\n\n# 计划\n\n进行中。\n"
    RUN_PASS = "---\ndecision: pass\n---\n\n## 结果\n\n| 用例 ID | 状态 | 层级 | 证据 | 实际结果 | 说明 |\n| --- | --- | --- | --- | --- | --- |\n| TC-01 | pass | browser | shot.png | 进入 | — |\n"
    RUN_FAIL = "---\ndecision: fail\n---\n\n## 结果\n\n| 用例 ID | 状态 | 层级 | 证据 | 实际结果 | 说明 |\n| --- | --- | --- | --- | --- | --- |\n| TC-01 | fail | browser | — | 超时 | — |\n"

    results: list[tuple[str, bool, str]] = []

    def case(name: str, build, expect_exit: int, expect_text: str) -> None:
        base = Path(tempfile.mkdtemp(prefix="af-records-selftest-"))
        try:
            feature = base / "hub" / "features" / "feature-x"
            build(base, feature)
            findings = run_checks(feature, base / "hub")
            errors = [f for kind, f in findings if kind == "error"]
            code = 1 if errors else 0
            text = "\n".join(f for _, f in findings)
            ok = code == expect_exit and expect_text in text
            results.append((name, ok, "" if ok else f"期望 exit={expect_exit} 含「{expect_text}」，实际 errors={errors}"))
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def mk(base, feature, acceptance=ACCEPTANCE, plan=PLAN_DONE, run=RUN_PASS, readme=None, pending=None,
           registry=REGISTRY_BOTH):
        (feature / "spec" / "qa").mkdir(parents=True)
        (feature / "plan").mkdir(parents=True)
        (feature / "testing" / "demo").mkdir(parents=True)
        (feature / "spec" / "qa" / "acceptance.md").write_text(acceptance, encoding="utf-8")
        (feature / "plan" / "execution.md").write_text(plan, encoding="utf-8")
        (feature / "testing" / "demo" / "plan-2026-11-04-001.md").write_text(
            "---\ntest_plan_id: TP-X\n---\n\n# 用例库\n" + registry, encoding="utf-8")
        (feature / "testing" / "demo" / "run-2026-11-04-001.md").write_text(run, encoding="utf-8")
        if readme is not None:
            rd = feature / "reviews"
            rd.mkdir(parents=True, exist_ok=True)
            (feature / "README.md").write_text(readme, encoding="utf-8")
            (rd / "review-2026-11-04-001.md").write_text("# review\n", encoding="utf-8")
        if pending is not None:
            rel = feature.parent.parent / "releases"
            rel.mkdir(parents=True, exist_ok=True)
            (rel / "pending-test.md").write_text(pending, encoding="utf-8")

    def shoot(base, feature):
        (feature / "testing" / "demo" / "shot.png").write_text("png", encoding="utf-8")

    acceptance_dirty = ACCEPTANCE.replace("已覆盖", "待覆盖")
    case("R1：plan 已落盘 + 待覆盖残留 → error", lambda b, f: (mk(b, f, acceptance=acceptance_dirty), shoot(b, f)), 1, "R1")
    case("R3：plan 称全部完成 + run fail → error", lambda b, f: (mk(b, f, run=RUN_FAIL), shoot(b, f)), 1, "R3")
    case("R5：fail 行证据为空 → error", lambda b, f: (mk(b, f, run=RUN_FAIL), shoot(b, f)), 1, "R5")
    case("R5：fail 行证据文件不存在 → error", lambda b, f: mk(b, f, run=RUN_FAIL.replace("| — | 超时 |", "| ghost.png | 超时 |")), 1, "R5")
    case("R6：注册表来源列未覆盖全部 AC → error", lambda b, f: (mk(b, f, plan=PLAN_PARTIAL, registry=REGISTRY_ONE), shoot(b, f)), 1, "R6")
    case("干净批次 → 0 error", lambda b, f: (mk(b, f, plan=PLAN_DONE.replace("全部任务已完成（30/30）。", "进行中。")), shoot(b, f)), 0, "")
    case("R2：README 断言轮数 > 记录数 → warn（不影响退出码）", lambda b, f: (mk(b, f, plan=PLAN_DONE.replace("全部任务已完成", "进行中"), readme="需求评审 3 轮通过。"), shoot(b, f)), 0, "R2")
    case("R4：pending-test 残余无指向 → warn", lambda b, f: (mk(b, f, plan=PLAN_DONE.replace("全部任务已完成", "进行中"), pending="# 待验证\n\n## 未做与残余\n\n- 跨浏览器不测\n"), shoot(b, f)), 0, "R4")

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        return _self_test()
    args = [a for a in sys.argv[1:] if a != "--hub"]
    if not args:
        print("用法：python3 check_records.py <feature-dir> [--hub <hub 根>]（或 --self-test）", file=sys.stderr)
        return 2
    feature_dir = Path(args[0]).resolve()
    if not feature_dir.is_dir():
        print(f"[错误] 批次目录不存在：{feature_dir}", file=sys.stderr)
        return 2
    hub = None
    if "--hub" in sys.argv:
        idx = sys.argv.index("--hub")
        if idx + 1 < len(sys.argv):
            hub = Path(sys.argv[idx + 1]).resolve()

    findings = run_checks(feature_dir, hub)
    errors = [f for kind, f in findings if kind == "error"]
    warns = [f for kind, f in findings if kind == "warn"]
    for f in errors:
        print(f"[error] {f}")
    for f in warns:
        print(f"[warn]  {f}")
    if errors:
        print(f"\n{len(errors)} 项 error、{len(warns)} 项 warn —— 跨文件漂移待修")
        return 1
    print(f"\n通过（0 error，{len(warns)} warn）——R1–R6 无跨文件事实漂移")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
