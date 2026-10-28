#!/usr/bin/env python3
"""工程基线吸收批的验收复跑脚本。

只读仓库文件并重写 `evidence/` 下的验收证据；不修改任何产品面。
用法：python3.12 docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/scratch/verify.py
退出码：0 全部通过；1 存在失败检查。
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
EVID = HERE.parent / "evidence"


def cells(line: str) -> int:
    return len([c for c in line.strip().strip("|").split("|")])


def emit(name: str, title: str, hits: list[str], ok: bool) -> None:
    lines = [
        "$ python3.12 docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/scratch/verify.py",
        f"# {title}",
        *hits,
        "",
        f"RESULT: {'PASS' if ok else 'FAIL'}",
        f"exit={0 if ok else 1}",
    ]
    (EVID / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{'PASS' if ok else 'FAIL'} {name}")


def check_t01() -> bool:
    tpl = ROOT / "skills/agentflow/templates/engineering/baseline.md"
    text = tpl.read_text(encoding="utf-8")
    heads = [ln for ln in text.splitlines() if ln.startswith("## ")]
    expected = [f"## {i}." for i in range(10)]
    missing = [e for e in expected if not any(h.startswith(e) for h in heads)]
    fillable = {}
    for i in range(1, 10):
        start = next((j for j, ln in enumerate(text.splitlines()) if ln.startswith(f"## {i}.")), None)
        end = next((j for j in range(start + 1, len(text.splitlines())) if text.splitlines()[j].startswith("## ")), len(text.splitlines()))
        block = "\n".join(text.splitlines()[start:end])
        fillable[i] = ("<" in block) or ("| ---" in block)
    index = (ROOT / "skills/agentflow/templates/README.md").read_text(encoding="utf-8")
    root_index = (ROOT / "index.md").read_text(encoding="utf-8")
    runtime = ROOT / "packaging/runtime/skills/agentflow/templates/engineering/baseline.md"
    same = runtime.is_file() and runtime.read_bytes() == tpl.read_bytes()
    hits = [
        *[f"  {h}" for h in heads],
        f"固定小节：{10 - len(missing)}/10；缺失：{missing or '无'}",
        f"1–9 节可填（含占位或表格）：{all(fillable.values())}；缺：{[k for k, v in fillable.items() if not v]}",
        f"templates/README.md 指针：{'engineering/baseline.md' in index}",
        f"index.md 指针：{'工程基线' in root_index}",
        f"生成树同名且逐字节一致：{same}",
    ]
    ok = not missing and all(fillable.values()) and "engineering/baseline.md" in index and "工程基线" in root_index and same
    emit("T01-baseline-template.txt", "工程基线模板：小节、可填性、指针、生成树", hits, ok)
    return ok


def check_t02() -> bool:
    skill = (ROOT / "skills/agentflow/SKILL.md").read_text(encoding="utf-8").splitlines()
    hits = [(i, ln) for i, ln in enumerate(skill, 1) if 33 <= i <= 52 and ("六项" in ln or "工程基线" in ln)]
    text = "\n".join(ln for _, ln in hits)
    ok = "与用户确认六项" in text and "工程基线入口" in text and "templates/engineering/baseline.md" in text
    emit(
        "T02-init.txt",
        "Init：六项确认、工程基线入口、模板指针",
        [f"  {i}: {ln}" for i, ln in hits],
        ok,
    )
    return ok


def check_t03() -> bool:
    be = (ROOT / "skills/agentflow/templates/feature/design/be/backend.md").read_text(encoding="utf-8").splitlines()
    config_header = next((ln for ln in be if ln.startswith("| 键与代码字段 |")), "")
    boundary_header = next((ln for ln in be if ln.startswith("| 限制项 |")), "")
    config_rows = [ln for ln in be if ln.startswith("| <ENV") or ln.startswith("| <键")]
    boundary_rows = [ln for ln in be if ln.startswith("| <超时")]
    start = next(i for i, ln in enumerate(be) if "1.3.5 数据设计核对" in ln)
    end = next(i for i in range(start + 1, len(be)) if be[i].startswith("### 1.4"))
    rows = [ln for ln in be[start:end] if ln.startswith("| ") and not ln.startswith("| ---") and "核对项" not in ln]
    rows_filled = [ln for ln in rows if "<填写>" in ln]
    selfcheck = [ln for ln in be if "字段与数据核对表逐项" in ln]
    agent = (ROOT / "agents/backend-engineer.md").read_text(encoding="utf-8").splitlines()
    agent_hits = [(i, ln) for i, ln in enumerate(agent, 1) if "新增或修改持久化字段" in ln]
    hits = [
        f"配置表头：{config_header}",
        f"配置表列数：{cells(config_header)}（期望 12）",
        f"配置占位数据行：{len(config_rows)}（期望 ≥1）",
        f"边界表列数：{cells(boundary_header)}（期望 7）",
        f"边界占位数据行：{len(boundary_rows)}（期望 ≥1）",
        f"数据核对行：{len(rows)}；其中含 <填写>：{len(rows_filled)}（期望 8/8）",
        *[f"  {ln.strip()}" for ln in rows],
        f"自检命中：{selfcheck[0].strip() if selfcheck else '无'}",
        *[f"  backend-engineer {i}: {ln[:120]}..." for i, ln in agent_hits],
    ]
    ok = (
        cells(config_header) == 12
        and len(config_rows) >= 1
        and cells(boundary_header) == 7
        and len(boundary_rows) >= 1
        and len(rows) == 8
        and len(rows_filled) == 8
        and len(selfcheck) == 1
        and len(agent_hits) == 1
    )
    emit("T03-design-be.txt", "design/be：配置/边界表可填、8 项核对、角色纪律", hits, ok)
    return ok


def check_t04() -> bool:
    proto_text = (ROOT / "skills/agentflow/templates/feature/prototype/README.md").read_text(encoding="utf-8")
    proto = proto_text.splitlines()
    proto_hits = [(i, ln) for i, ln in enumerate(proto, 1) if ln.strip().startswith("- [ ] P")]
    chain_text = (ROOT / "skills/agentflow/references/document-chain.md").read_text(encoding="utf-8")
    chain = chain_text.splitlines()
    chain_hits = [(i, ln) for i, ln in enumerate(chain, 1) if "原型要能点" in ln or "脚本扫描只能当线索" in ln]
    hits = [
        *[f"  prototype {i}: {ln.strip()}" for i, ln in proto_hits],
        *[f"  document-chain {i}: {ln.strip()}" for i, ln in chain_hits],
        f"原型模板仍含『99.4%』：{'99.4%' in proto_text}（期望 False）",
        f"链契约仍含『99%』：{'99%' in chain_text}（期望 False）",
    ]
    ok = len(proto_hits) == 5 and len(chain_hits) == 2 and "99.4%" not in proto_text and "99%" not in chain_text
    emit("T04-prototype.txt", "原型：P1–P5 与链契约判据；禁止未经换算的误报率", hits, ok)
    return ok


def check_t05() -> bool:
    plan_text = (ROOT / "skills/agentflow/templates/testing/plan.md").read_text(encoding="utf-8")
    plan = plan_text.splitlines()
    need = ("并发与竞态", "生命周期与清理", "契约与兼容")
    plan_hits = [(i, ln) for i, ln in enumerate(plan, 1) if any(k in ln for k in need) or "最小必测集" in ln or "十一个方向" in ln]
    tp_text = (ROOT / "agents/test-planner.md").read_text(encoding="utf-8")
    tp_hits = [(i, ln) for i, ln in enumerate(tp_text.splitlines(), 1) if "三类易漏维度" in ln]
    chain_text = (ROOT / "skills/agentflow/references/document-chain.md").read_text(encoding="utf-8")
    hits = [
        *[f"  plan {i}: {ln.strip()[:160]}" for i, ln in plan_hits],
        *[f"  test-planner {i}: {ln.strip()[:160]}" for i, ln in tp_hits],
        f"链契约写『十一个方向』：{'十一个方向' in chain_text}",
        f"链契约仍写『八个方向』：{'八个方向' in chain_text}（期望 False）",
    ]
    ok = (
        all(any(k in ln for _, ln in plan_hits) for k in need)
        and "最小必测集" in plan_text
        and "十一个方向" in plan_text
        and len(tp_hits) == 1
        and "十一个方向" in chain_text
        and "八个方向" not in chain_text
    )
    emit("T05-testing-plan.txt", "测试计划：三行方向、最小必测集、契约同步", hits, ok)
    return ok


def check_fe() -> bool:
    fe_text = (ROOT / "agents/frontend-engineer.md").read_text(encoding="utf-8")
    fe_need = [
        "请求、缓存与生命周期", "取消", "晚到响应", "缓存键", "失效", "登出", "401",
        "零值", "必需回调", "unknown", "纯计算", "可访问名称", "Blob URL", "公开配置",
    ]
    fe_hits = [k for k in fe_need if k in fe_text]

    design_text = (ROOT / "skills/agentflow/templates/feature/design/fe/frontend.md").read_text(encoding="utf-8")
    design_need = [
        "缓存键与失效", "身份与生命周期", "省略 / null / 空串 / 零值 / 空数组",
        "金额 / 点数 / 大整数", "取消与资源释放", "登录态与权限变化", "写后缓存失效",
    ]
    design_hits = [k for k in design_need if k in design_text]
    selfcheck = [
        ln for ln in design_text.splitlines()
        if ln.startswith("- ☐") and any(k in ln for k in ("请求取消", "字段省略", "可访问性", "媒体资源"))
    ]

    spec_text = (ROOT / "skills/agentflow/templates/feature/spec/fe/frontend.md").read_text(encoding="utf-8")
    spec_need = ["### 2.1 前端行为口径", "数据刷新与去重", "并发与晚到响应", "身份与权限", "字段空值语义", "键盘与可访问性", "媒体与下载"]
    spec_hits = [k for k in spec_need if k in spec_text]

    base_text = (ROOT / "skills/agentflow/templates/engineering/baseline.md").read_text(encoding="utf-8")
    base_need = ["请求层与客户端边界", "### UI、文案与可访问性基线", "多站点 / 多应用", "文案与国际化", "可访问性：", "格式与命名："]
    base_hits = [k for k in base_need if k in base_text]

    hits = [
        f"frontend-engineer 命中：{len(fe_hits)}/{len(fe_need)}；缺：{[k for k in fe_need if k not in fe_hits]}",
        *[f"  fe: {k}" for k in fe_hits],
        f"design/fe 命中：{len(design_hits)}/{len(design_need)}；缺：{[k for k in design_need if k not in design_hits]}",
        f"design/fe 自检：{len(selfcheck)}/4",
        *[f"  design: {k}" for k in design_hits],
        f"spec/fe 命中：{len(spec_hits)}/{len(spec_need)}；缺：{[k for k in spec_need if k not in spec_hits]}",
        f"工程基线命中：{len(base_hits)}/{len(base_need)}；缺：{[k for k in base_need if k not in base_hits]}",
    ]
    ok = (
        len(fe_hits) == len(fe_need)
        and len(design_hits) == len(design_need)
        and len(selfcheck) == 4
        and len(spec_hits) == len(spec_need)
        and len(base_hits) == len(base_need)
    )
    emit("T10-frontend-discipline.txt", "FE 五组纪律、两层模板与工程基线", hits, ok)
    return ok


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    results = [check_t01(), check_t02(), check_t03(), check_t04(), check_t05(), check_fe()]
    print(f"summary: {sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
