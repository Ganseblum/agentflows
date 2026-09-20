#!/usr/bin/env python3
"""Deterministic cross-closure linter for feature document chains.

Born from the 2026-09-20 quality failure: a full proposal -> spec -> design -> plan chain
was generated where every stage "existed" but design carried no API contracts, no failure
sequence diagrams, no state-machine diagrams, no wireframes, and plans carried no file
targets — and nothing failed, because no check existed. This tool is that check.

Scope and assumptions (honest): this linter checks the doc-chain conventions shared by this
repository's contract (skills/agentflow/references/document-chain.md) and the business
repositories that adopt it — the feature-directory layout (README + proposal/ + spec/ +
design/{be,fe}/ + plan/{be,fe}/). It is a FLOOR check, not a quality verdict: passing means
the structural density bar is met, not that the content is correct. Content correctness
still belongs to the review gates.

Checks:
  C1  structure        every stage directory holds at least one real document (no .gitkeep only)
  C2  entry gates      README carries the requirement-review and design-review gate entries
  C3  spec re-audit    a spec file contains the re-audit checklist; no blocking row left open (☐)
  C4  design/be figures  >=1 sequenceDiagram WITH an alt failure branch, >=1 flowchart,
                       >=1 erDiagram or stateDiagram
  C5  contract closure every interface id declared in design/be's contract table appears
                       in design/fe (its exception matrix or elsewhere)
  C6  fe exception matrix  design/fe has a table whose header covers success AND failure
  C7  fe wireframes    >=2 text wireframes (box-drawing frames) in design/fe
  C8  design/fe figures  >=1 flowchart, >=1 sequenceDiagram, >=1 stateDiagram
  C9  plan grounding   every task row carries a code-location token; branch strategy present;
                       design's V-n open items are referenced by some plan
  C10 mermaid fences   every ```mermaid block is closed

Usage:
    python3 tools/lab/doc_chain.py <feature-dir>
    python3 tools/lab/doc_chain.py --self-test

Exit code 0 = all checks pass; 1 = findings; 2 = usage error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MERMAID_KINDS = ("sequenceDiagram", "flowchart", "erDiagram", "stateDiagram")
BOX_CHARS = ("┌", "└", "├", "│")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def mermaid_blocks(text: str) -> list[str]:
    blocks, lines, inside, buf = [], text.splitlines(), False, []
    for line in lines:
        if line.strip() == "```mermaid":
            inside, buf = True, []
        elif inside and line.strip() == "```":
            inside = False
            blocks.append("\n".join(buf))
        elif inside:
            buf.append(line)
    return blocks  # unclosed fences simply never land here; C10 counts them separately


def mermaid_kinds(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for block in mermaid_blocks(text):
        for kind in MERMAID_KINDS:
            if kind in block:
                out.setdefault(kind, []).append(block)
                break
    return out


def find_stage(files: list[Path], *parts: str) -> list[Path]:
    """All non-gitkeep .md files under <feature>/<parts...> (recursively)."""
    base = Path(*parts)
    return [
        f
        for f in files
        if f.parent == base or base in f.parents
        if f.suffix == ".md" and f.name != ".gitkeep"
    ]


def lint(feature_dir: Path) -> list[str]:
    errors: list[str] = []
    if not feature_dir.is_dir():
        return [f"{feature_dir}: 目录不存在"]

    files = sorted(feature_dir.rglob("*"))
    md_files = [f for f in files if f.is_file() and f.suffix == ".md" and f.name != ".gitkeep"]
    readme = feature_dir / "README.md"

    # C1 structure
    for stage in ("proposal", "spec", "design", "plan"):
        stage_files = [f for f in md_files if stage in f.relative_to(feature_dir).parts]
        if not stage_files:
            errors.append(f"C1 结构: {stage}/ 下没有任何有效文档（仅 .gitkeep 占位）")
    if not readme.is_file():
        errors.append("C1 结构: 缺少 README.md 唯一入口")

    all_text = {f: read(f) for f in md_files}

    # C2 entry gates
    if readme.is_file():
        rtext = all_text.get(readme, "")
        for gate in ("需求评审", "技术方案评审"):
            if gate not in rtext:
                errors.append(f"C2 入口门禁: README 未声明「{gate}」门禁条目")

    # C3 spec re-audit + blocking closed
    spec_files = find_stage(md_files, feature_dir / "spec")
    audit_found = False
    for f in spec_files:
        text = all_text[f]
        if ("不合规项" in text) or ("反审" in text):
            audit_found = True
        for line in text.splitlines():
            # accepted tolerance (review note b): the whole-line 非阻塞 skip can also
            # suppress a 阻塞-status row whose text merely mentions 非阻塞 —
            # false-negative direction, acceptable for a floor linter
            if "非阻塞" in line:
                continue  # non-blocking rows may stay open pending review confirmation
            if line.lstrip().startswith("|") and "阻塞" in line and "☐" in line:
                errors.append(f"C3 反审门: {f.relative_to(feature_dir)} 存在未关闭的阻塞项: {line.strip()[:80]}")
    if spec_files and not audit_found:
        errors.append("C3 反审门: spec/ 下没有任何文件包含「不合规项/反审」checklist")

    # C4/C5/C6/C7/C8 per-side design requirements
    be_files = find_stage(md_files, feature_dir / "design" / "be")
    fe_files = find_stage(md_files, feature_dir / "design" / "fe")
    be_text = "\n".join(all_text[f] for f in be_files) if be_files else ""
    fe_text = "\n".join(all_text[f] for f in fe_files) if fe_files else ""

    if be_files:
        kinds = mermaid_kinds(be_text)
        seq_with_alt = [b for b in kinds.get("sequenceDiagram", []) if re.search(r"^\s*alt\b", b, re.M)]
        if not seq_with_alt:
            errors.append("C4 design/be: 缺少含失败分支（alt）的时序图")
        if "flowchart" not in kinds:
            errors.append("C4 design/be: 缺少架构/流程 flowchart")
        spec_kinds = mermaid_kinds("\n".join(all_text[f] for f in spec_files) if spec_files else "")
        if not (kinds.get("erDiagram") or kinds.get("stateDiagram")
                or spec_kinds.get("erDiagram") or spec_kinds.get("stateDiagram")):
            errors.append("C4 design/be: 缺少 ER 图或状态机图（design/be 或 spec）")
        if not re.search(r"\|\s*#?\s*接口.*\|.*请求字段.*响应字段|\|.*请求字段.*\|.*响应字段", be_text):
            errors.append("C4 design/be: 缺少字段级 API 契约表（请求字段/响应字段列表头）")
        # C5: ids declared in the CONTRACT TABLE's first column must appear in design/fe
        contract_ids: set[str] = set()
        # row pattern is strictly per-line: a `\s*$\n?` variant would bridge one blank
        # line and swallow the NEXT table (decision ids misread as contract ids).
        # accepted tolerance (review note): a table ending at EOF without a trailing
        # newline drops its last row's id here — false-negative direction, floor-safe
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", be_text, re.M):
            header = table.splitlines()[0]
            if "请求字段" in header and "响应字段" in header:
                for row in table.splitlines()[2:]:
                    first = row.strip("|").split("|")[0].strip()
                    m = re.match(r"^([A-Za-z]{1,3}\d{1,3})\b", first)
                    if m:
                        contract_ids.add(m.group(1).upper())
        fe_ids = set(re.findall(r"\b([A-Za-z]{1,3}\d{1,3})\b", fe_text))
        # accepted tolerance (review note a): \b fails on CJK-adjacent ids (e.g. `A1的`),
        # which over-reports C5 — the safe direction for a floor linter
        fe_ids = {i.upper() for i in fe_ids}
        missing = sorted(contract_ids - fe_ids)
        if contract_ids and missing:
            errors.append(f"C5 契约闭合: design/be 契约表声明的接口 {missing} 未在 design/fe 出现（缺异常矩阵行或调用）")
    if fe_files:
        kinds = mermaid_kinds(fe_text)
        for kind in ("flowchart", "sequenceDiagram", "stateDiagram"):
            if kind not in kinds:
                errors.append(f"C8 design/fe: 缺少 {kind}")
        wireframes = [
            b
            for b in re.findall(r"```text\n(.*?)```", fe_text, re.S)
            if any(c in b for c in BOX_CHARS)
        ]
        has_prototype = any(f.suffix == ".html" and "prototype" in str(f.relative_to(feature_dir)).lower()
                            for f in md_files + [x for x in files if x.is_file() and x.suffix == ".html"])
        if len(wireframes) < 2 and not has_prototype:
            errors.append(f"C7 design/fe: 工程线框不足 2 张（现 {len(wireframes)}）且无 prototype HTML 原型")
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", fe_text, re.M):
            header = table.splitlines()[0]
            if ("成功" in header or "正常" in header) and ("失败" in header or "异常" in header):
                break
        else:
            errors.append("C6 design/fe: 缺少接口异常边界矩阵（表头需同时覆盖 成功 与 失败/异常）")

    # C9 plan grounding
    plan_files = find_stage(md_files, feature_dir / "plan")
    plan_text = "\n".join(all_text[f] for f in plan_files) if plan_files else ""
    if plan_files:
        # task rows = table rows carrying a task id AND a write-back status cell; a row may
        # satisfy grounding via a code path OR an explicit to-verify reference (unknown
        # location must be pinned to a V-item, never left unexplained)
        task_rows = [
            line
            for line in plan_text.splitlines()
            if line.lstrip().startswith("|")
            and re.search(r"\b(?:FT?\d{2}|T\d{1,2})\b", line)
            and re.search(r"[☐☑◐⚠—]", line)
            and "待核实" not in line.split("|")[1]
        ]
        path_or_v = re.compile(r"[\w./-]+\.(?:go|ts|tsx|vue|sql|py|md)\b|`[\w/.-]+/`|/`|\bV-F?\d+\b|/tmp")
        for row in task_rows:
            if not path_or_v.search(row):
                errors.append(f"C9 plan 落点: 任务行缺少代码落点路径或待核实引用: {row.strip()[:80]}")
        if not re.search(r"分支|branch|feature[-_]", plan_text):
            errors.append("C9 plan: 未声明分支策略")
        v_ids = set(re.findall(r"\bV-F?\d+\b", be_text + fe_text))
        for vid in sorted(v_ids):
            # no heading-anchored exemption: any V-id declared anywhere in design must be
            # referenced by some plan, or C9 fails (F2 fix — the old `### 1.3` split
            # silently disabled this check for designs numbered differently)
            if vid not in plan_text:
                errors.append(f"C9 待核实闭合: design 声明的 {vid} 未被任何 plan 引用")
        for f in plan_files:
            for line in all_text[f].splitlines():
                if line.lstrip().startswith("|") and "⚠ 阻塞" in line and "☐" in line:
                    errors.append(f"C9 plan: {f.relative_to(feature_dir)} 存在未回写证据的阻塞任务行")

    # C11 template structure (marker-gated): chains declaring the agentflow doc-chain
    # marker in README must carry the fixed design headings (heading literals, like the
    # records contract) — prose skeletons alone allow generation drift.
    if readme.is_file() and "agentflow 文档链方法生成" in all_text.get(readme, ""):
        be_heads = "\n".join(all_text[f] for f in be_files) if be_files else ""
        fe_heads = "\n".join(all_text[f] for f in fe_files) if fe_files else ""
        import re as _re
        if not _re.search(r"^##+ .*(先说结论|关键决策速览|结论先行)", be_heads, _re.M):
            errors.append("C11 结构模板: design/be 缺固定标题（先说结论/关键决策速览）")
        if "影响面评估" not in be_heads:
            errors.append("C11 结构模板: design/be 缺「影响面评估」章")
        for fname, head in (("design/be", be_heads), ("design/fe", fe_heads)):
            if "评审前自检" not in head:
                errors.append(f"C11 结构模板: {fname} 缺「评审前自检」章")
        if fe_files and "data-testid" not in fe_heads:
            errors.append("C11 结构模板: design/fe 缺 data-testid 可测性清单")

    # C10 mermaid fence balance
    for f in md_files:
        text = all_text[f]
        opened = sum(1 for line in text.splitlines() if line.strip() == "```mermaid")
        blocks = len(mermaid_blocks(text))
        if opened != blocks:
            errors.append(f"C10 mermaid: {f.relative_to(feature_dir)} 有 {opened} 个 mermaid 围栏但仅 {blocks} 个闭合")

    return errors


def self_test() -> int:
    """Per-check discrimination fixtures (reviewer-authored matrix, 2026-09-20).

    One dense chain must pass; one mutation per check must fail with that check id; the
    AC3 non-regression classes (非阻塞 rows, decision-table ids, design ledger rows) must
    NOT trip. Fixes review finding F1 ("self-test vacuous for most checks").
    """
    import subprocess
    import tempfile

    linter = Path(__file__).resolve()
    base = {
        "README.md": "# feature\n\n## 需求评审门\n## 技术方案评审门\n",
        "proposal/p.md": "# proposal\n",
        "spec/s.md": (
            "# spec\n\n## 3.0 不合规项（反审 checklist）\n\n"
            "| # | 缺口 | 阻塞 | 状态 |\n| --- | --- | --- | --- |\n"
            "| B-1 | x | 阻塞 | ☑ 已关闭 |\n"
            "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n"
        ),
        "design/be/b.md": (
            "# be\n\n"
            "| 接口 | 请求字段 | 响应字段 |\n| --- | --- | --- |\n| A1 | d(string,Y) | uid |\n\n"
            "| # | 决策 | 结论 |\n| --- | --- | --- |\n| D6 | 决策六 | 方案二 |\n| D10 | 决策十 | 方案三 |\n\n"
            "### 1.3 待核实清单\n\n"
            "| # | 事项 | 影响 |\n| --- | --- | --- |\n| V-9 | 外部接口形态 | T02 |\n\n"
            "```mermaid\nsequenceDiagram\n    A->>B: go\n    alt 失败\n        B-->>A: err\n    end\n```\n"
            "```mermaid\nflowchart TB\n    A --> B\n```\n"
            "```mermaid\nerDiagram\n    t1 ||--o{ t2 : has\n```\n"
        ),
        "design/fe/f.md": (
            "# fe\n\nA1 调用见异常矩阵\n\n"
            "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n| A1 | ok | 412 |\n\n"
            "```mermaid\nflowchart LR\n    L --> D\n```\n"
            "```mermaid\nsequenceDiagram\n    U->>L: click\n```\n"
            "```mermaid\nstateDiagram-v2\n    [*] --> S1\n```\n"
            "```text\n┌─列表──┐\n│ 卡片  │\n└──────┘\n```\n"
            "```text\n┌─弹窗──┐\n│ 字段  │\n└──────┘\n```\n"
        ),
        "plan/be/p.md": (
            "# plan\n\n## 0. 分支策略 feature-x\n\n"
            "| ID | 任务 | 代码落点 | 依赖 | 状态 |\n| --- | --- | --- | --- | --- |\n"
            "| T01 | 迁移 | `migrations/x.sql` | — | ☐ |\n\n"
            "V-9 由 T02 承接\n"
        ),
    }

    def rep(files: dict, rel: str, old: str, new: str) -> dict:
        assert old in files[rel], "mutation anchor missing in " + rel
        files[rel] = files[rel].replace(old, new)
        return files

    def run_case(name: str, expect_rc: int, want: list[str], mutate=None, results=None) -> None:
        files = dict(base)
        if mutate:
            files = mutate(dict(base))
        d = Path(tempfile.mkdtemp()) / "feature"
        for rel, text in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        r = subprocess.run([sys.executable, str(linter), str(d)], capture_output=True, text=True)
        out = r.stdout + r.stderr
        ok = r.returncode == expect_rc and all(w in out for w in want)
        results.append((name, ok))
        if not ok:
            print(f"  wanted {want}, exit={r.returncode}, got:\n{out}")

    ALT = "    alt 失败\n        B-->>A: err\n    end\n"
    CONTRACT = "| 接口 | 请求字段 | 响应字段 |\n| --- | --- | --- |\n| A1 | d(string,Y) | uid |\n\n"
    WF2 = "```text\n┌─弹窗──┐\n│ 字段  │\n└──────┘\n```\n"
    results: list[tuple[str, bool]] = []

    run_case("01 good dense chain passes (D6/D10 never C5; design ledger never C9)", 0,
             ["PASS doc-chain"], results=results)

    def m_thin(f):
        rep(f, "design/be/b.md", CONTRACT, "")
        rep(f, "design/be/b.md", ALT, "")
        rep(f, "design/fe/f.md", WF2, "")
        rep(f, "plan/be/p.md", "`migrations/x.sql`", "迁移三张表")
        return f
    run_case("02 original-thin chain fails C4-contract/C4-alt/C7/C9", 1,
             ["缺少字段级 API 契约表", "缺少含失败分支（alt）的时序图",
              "C7 design/fe: 工程线框不足 2 张（现 1）", "C9 plan 落点"],
             m_thin, results)
    run_case("03 open 非阻塞 row does NOT trip C3", 0, ["PASS doc-chain"],
             lambda f: rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                           "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n| B-9 | z | 非阻塞 | ☐ 待评审确认 |\n"),
             results)
    run_case("04 open 阻塞 row trips C3", 1, ["C3 反审门"],
             lambda f: rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                           "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n| B-9 | z | 阻塞 | ☐ 待评审确认 |\n"),
             results)
    run_case("05 C5 contract-table id absent from fe trips C5", 1, ["C5 契约闭合"],
             lambda f: rep(f, "design/be/b.md", "| A1 | d(string,Y) | uid |\n",
                           "| A1 | d(string,Y) | uid |\n| B2 | e(string,Y) | x |\n"),
             results)
    run_case("06 C1 stage without a real doc trips C1", 1, ["C1 结构"],
             lambda f: (f.pop("plan/be/p.md"), f)[1], results)
    run_case("07 C2 README missing gate trips C2", 1, ["C2 入口门禁"],
             lambda f: f.update({"README.md": "# feature\n\n## 需求评审门\n"}) or f, results)
    run_case("08 C4 missing flowchart trips C4", 1, ["缺少架构/流程 flowchart"],
             lambda f: rep(f, "design/be/b.md", "```mermaid\nflowchart TB\n    A --> B\n```\n", ""),
             results)
    run_case("09 C4 missing ER/state trips C4", 1, ["缺少 ER 图或状态机图"],
             lambda f: rep(f, "design/be/b.md", "```mermaid\nerDiagram\n    t1 ||--o{ t2 : has\n```\n", ""),
             results)
    run_case("10 C7 single wireframe trips C7", 1, ["C7 design/fe: 工程线框不足 2 张（现 1）"],
             lambda f: rep(f, "design/fe/f.md", WF2, ""), results)
    run_case("11 C8 missing stateDiagram trips C8", 1, ["C8 design/fe: 缺少 stateDiagram"],
             lambda f: rep(f, "design/fe/f.md", "```mermaid\nstateDiagram-v2\n    [*] --> S1\n```\n", ""),
             results)
    run_case("12 C6 fe missing exception matrix trips C6", 1, ["C6 design/fe: 缺少接口异常边界矩阵"],
             lambda f: rep(f, "design/fe/f.md",
                           "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n| A1 | ok | 412 |\n\n", ""),
             results)
    run_case("13 C10 unclosed mermaid fence trips C10", 1, ["C10 mermaid"],
             lambda f: f.update({"design/be/b.md": f["design/be/b.md"] + "```mermaid\nflowchart X\n"}) or f,
             results)
    run_case("14 C9 missing branch strategy trips C9", 1, ["未声明分支策略"],
             lambda f: rep(f, "plan/be/p.md", "## 0. 分支策略 feature-x", "## 0. 执行顺序"), results)
    run_case("15 C9 design V-item unreferenced by plan trips C9", 1, ["C9 待核实闭合"],
             lambda f: rep(f, "plan/be/p.md", "V-9 由 T02 承接\n", ""), results)
    run_case("16 C9 open blocking plan row trips C9", 1, ["未回写证据的阻塞任务行"],
             lambda f: f.update({"plan/be/p.md": f["plan/be/p.md"] + "| T99 | 修复 | `fix/x.go` | — | ⚠ 阻塞 ☐ |\n"}) or f,
             results)
    def strip_wireframes(f):
        # remove all text-wireframe blocks (fence-to-fence), keep everything else
        f["design/fe/f.md"] = re.sub(r"```text\n.*?```", "", f["design/fe/f.md"], flags=re.S)
        f["design/fe/prototype.html"] = "<html>定时任务原型</html>"
        return f
    run_case("18 html prototype alone satisfies C7", 0, ["PASS doc-chain"], strip_wireframes, results)

    def add_marker(f):
        f["README.md"] = f["README.md"] + "\n本 feature 文档链由 agentflow 文档链方法生成（2026-09-20）\n"
        return f
    run_case("19 marker without fixed headings trips C11", 1, ["C11 结构模板"], add_marker, results)

    def add_marker_and_heads(f):
        f = add_marker(f)
        f["design/be/b.md"] += "\n## 0. 先说结论\n| 问题 | 结论 |\n\n## 1.6 兼容性思考 & 影响面评估\n\n## 4. Design 评审前自检\n"
        f["design/fe/f.md"] += "\n## 4. Design 评审前自检\n\n| data-testid | 节点 | 出现条件 |\n| --- | --- | --- |\n| x-card | 卡片 | 列表 |\n"
        return f
    run_case("20 marker with fixed headings passes C11", 0, ["PASS doc-chain"], add_marker_and_heads, results)
    run_case("17 task-like row inside a DESIGN table is never a C9 task row", 0, ["PASS doc-chain"],
             lambda f: rep(f, "design/be/b.md", "| V-9 | 外部接口形态 | T02 |\n",
                           "| V-9 | 外部接口形态 | T02 |\n| T99 | 待核实事项 | — |\n"),
             results)

    ok = all(passed for _, passed in results)
    for name, passed in results:
        print(("PASS " if passed else "FAIL ") + name)
    print(f"{sum(p for _, p in results)}/{len(results)} self-test cases pass")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if len(argv) == 1 and argv[0] == "--self-test":
        return self_test()
    if len(argv) != 1:
        print(__doc__)
        return 2
    errors = lint(Path(argv[0]))
    if errors:
        print(f"FAIL doc-chain ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS doc-chain {argv[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
