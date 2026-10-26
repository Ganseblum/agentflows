"""Discrimination self-test for the doc-chain linter (reviewer-authored negative corpus)."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .checks import repo_policy_findings
from .constants import *


def self_test() -> int:
    """Per-check discrimination fixtures (reviewer-authored matrix, 2026-09-20).

    One dense chain must pass; one mutation per check must fail with that check id; the
    AC3 non-regression classes (非阻塞 rows, decision-table ids, design ledger rows) must
    NOT trip. Fixes review finding F1 ("self-test vacuous for most checks"). Cases 27–34
    pin C14's positive/negative surface (paired forms, definition rows, code spans, the
    real-corpus 「IP 桶」 near-miss); cases 35–38 pin the --file text-form mode and its
    mutual exclusion with the positional feature dir; cases 39–43 pin C13's per-file exemption
    and the planned-role exemption; cases 44–48 pin the C4/C8 applicability rule and C1's
    段落映射豁免; cases 49–54 pin C9's task-row and 分支策略 rules; cases 55–56 pin C5's
    prose-only id scan; case 34 documents why C15 stays clause-governed (see the note at
    CODE_SUBJECT_RE); cases 73–85 pin the 2026-10-21 gate change (bare-glyph status dialect,
    README 落点基准, C19 qa acceptance, C20 埋点贯通, C21 ui 轨, placeholder non-firing);
    cases 86–97 pin the 2026-10-23 gate change (C22 goal traceability — missing carrier row,
    phantom task id, status over-claim, orphan task, marker-without-table, opt-in respected;
    C23 evidence presence — /tmp-only, empty cell, repo-qualified and N/A carriers, and the
    repo scan applying C23 to every batch while C22 stays marker-gated); cases 99–102 pin C24
    single-ledger mode (HISTORY.md without README carries C2 gates and C22 承接表; both files
    present keeps README as the leader and treats HISTORY.md as an ordinary stage doc).
    """

    # The linter is the thin launcher (doc_chain.py), not this module: the self-test
    # relaunches it as a subprocess, and the launcher is what gate/checks.py and the
    # protected test invoke. This resolves to tools/lab/doc_chain.py in both the main
    # tree and the temp copy the gate exercises it in.
    linter = Path(__file__).resolve().parent.parent / "doc_chain.py"
    base = {
        "README.md": "# feature\n\n## 需求评审门\n## 技术方案评审门\n",
        "proposal/p.md": "# proposal\n",
        "spec/s.md": (
            "# spec\n\n## 3.0 不合规项（反审 checklist）\n\n"
            "| # | 缺口 | 阻塞 | 状态 |\n| --- | --- | --- | --- |\n"
            "| B-1 | x | 阻塞 | ☑ 已关闭 |\n"
            "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n"
        ),
        "spec/qa/acceptance.md": (
            "# qa\n\n## 1. 验收口径\n\n- AC-01 登录成功后跳转工作台\n"
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
            "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n| --- | --- | --- | --- | --- | --- |\n"
            "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 | `migrations/x.sql` |\n\n"
            "V-9 由 T02 承接\n"
        ),
        # "@root/" keys are written under the fixture repo root (the feature dir's parent), so C9
        # code-location paths resolve against a real file, not against this repository.
        "@root/migrations/x.sql": "-- x\n",
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
            p = d.parent / rel[len("@root/"):] if rel.startswith("@root/") else d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(linter), "--root", str(d.parent), str(d)],
            capture_output=True, text=True, check=False,
        )
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
    run_case("12b C6 header-only matrix does NOT satisfy C6 (matrix needs a data row)", 1,
             ["C6 design/fe: 缺少接口异常边界矩阵"],
             lambda f: rep(f, "design/fe/f.md",
                           "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n| A1 | ok | 412 |\n\n",
                           "| 接口 | 成功 | 失败/异常 |\n| --- | --- | --- |\n\n"),
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
        f["design/fe/f.md"] = re.sub(r"```text\n.*?```", "", f["design/fe/f.md"], flags=re.DOTALL)
        f["design/fe/prototype.html"] = (
            "<html>\n<body>\n<div data-testid=\"task-list\">定时任务列表原型</div>\n"
            "<div data-testid=\"task-retry\">重试</div>\n</body>\n</html>\n"
        )
        return f
    run_case("18 a real html prototype alone satisfies C7", 0, ["PASS doc-chain"],
             strip_wireframes, results)

    def empty_prototype(f):
        f = strip_wireframes(dict(base))
        f["design/fe/prototype.html"] = ""
        return f
    run_case("58 a zero-byte prototype.html no longer buys the C7 exemption (the name is not "
             "the artefact)", 1, ["C7 design/fe"], empty_prototype, results)
    run_case("59 a 阻塞-status row whose prose mentions 非阻塞 still trips C3 (the exemption is "
             "a status-cell claim, not a whole-line keyword)", 1, ["C3 反审门"],
             lambda f: rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                           "| B-2 | y | 阻塞（非阻塞项已另行列示） | ☐ 待评审确认 |\n"),
             results)

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

    def add_stale_existing_link(f):
        # claim word + link that resolves from spec/ -> design/be/b.md exists on disk
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n详设 [设计文档](../design/be/b.md) 尚未产出\n")
    run_case("21 C12 stale claim with an existing linked target trips C12", 1,
             ["C12 时效性引用: spec/s.md", "声称待产出但目标已存在: ../design/be/b.md"],
             add_stale_existing_link, results)

    def add_stale_absent_link(f):
        # same claim words, but the linked target does not exist — an honest pending claim
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n错误码表 [草案](./errata-draft.md) 待产出\n")
    run_case("22 C12 stale claim with an absent target does NOT trip", 0, ["PASS doc-chain"],
             add_stale_absent_link, results)

    def add_role_word(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n按 supervisor 的本轮评审意见执行\n")
    run_case("23 C13 session role word trips C13 (both the name and the session phrase)", 1,
             ["C13 会话角色词: proposal/p.md", "supervisor", "本轮评审"],
             add_role_word, results)

    def add_formal_role_name(f):
        # formal role names outside the closed word list never trip C13
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n由独立评审人与技术负责人收口\n")
    run_case("24 C13 formal role names do NOT trip", 0, ["PASS doc-chain"],
             add_formal_role_name, results)

    def add_stale_backtick_path(f):
        # claim word + backtick code path to a target that exists (the corpus's other form)
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n设计稿见 `../design/be/b.md`，待补充\n")
    run_case("25 C12 stale claim with an existing backtick path trips C12", 1,
             ["C12 时效性引用: spec/s.md", "声称待产出但目标已存在: ../design/be/b.md"],
             add_stale_backtick_path, results)

    def add_stale_backtick_absent(f):
        # same claim words, backtick form, but the path does not exist — honest pending claim
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n验收脚本 `./qa-check.md` 待补充\n")
    run_case("26 C12 stale backtick path with an absent target does NOT trip", 0, ["PASS doc-chain"],
             add_stale_backtick_absent, results)

    # --- C25 closure-claim (gate 6's machine half, 2026-10-26 audit G06). The batch README
    # declares `agentflow 链路收口`; the closure read was promised, so a stage doc must not
    # still carry a stale-time claim whose target exists. Three cases: a marked chain with a
    # rotted claim trips C25; a marked chain with an honest (absent-target) claim passes; an
    # unmarked chain with the same rotted claim is untouched by C25 (the prose gate 6 still
    # governs it, but C25 is opt-in so it must not fire uninvited). ---
    def add_closure_marker(f):
        return rep(f, "README.md", "## 技术方案评审门\n",
                   "## 技术方案评审门\n\nagentflow 链路收口\n")
    def add_closure_stale_existing(f):
        # stale claim pointing at a file that exists in the fixture (design/be/b.md)
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n接口契约 [A1](design/be/b.md) 待产出\n")
    run_case("103 C25 marked chain with a rotted stale claim trips C25", 1,
             ["C25 链路收口: spec/s.md", "标记了收口却仍声称待产出但目标已存在: design/be/b.md"],
             lambda f: add_closure_marker(add_closure_stale_existing(f)), results)
    def add_closure_stale_absent(f):
        # same claim words but the target genuinely does not exist — honest pending claim
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n验收脚本 [QA](./qa-check.md) 待补充\n")
    run_case("104 C25 marked chain with an absent-target claim does NOT trip C25", 0,
             ["PASS doc-chain"], lambda f: add_closure_marker(add_closure_stale_absent(f)), results)
    def add_unmarked_stale_absent(f):
        # same absent-target (honest) claim as 104, but NO closure marker — proves C25 is
        # opt-in: it must stay silent on an unmarked chain even though the claim words appear.
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n验收脚本 [QA](./qa-check.md) 待补充\n")
    run_case("105 C25 unmarked chain with a pending claim does NOT trip C25 (opt-in)", 0,
             ["PASS doc-chain"], add_unmarked_stale_absent, results)

    # --- C14 bare code subjects + --file mode. C15 (schema words in prose) is deliberately
    # NOT implemented — the closed-set heuristic flooded a real reviewed chain's legend rows;
    # case 34 pins that boundary. See the note at CODE_SUBJECT_RE for the full trade. ---

    def add_bare_bucket(f):
        return rep(f, "design/be/b.md", "### 1.3 待核实清单\n",
                   "### 1.3 待核实清单\n\nD 桶积分中断时对账回滚\n")
    run_case("27 C14 bare code subject in prose trips (D 桶)", 1,
             ["C14 代号裸用: design/be/b.md", "D 桶"], add_bare_bucket, results)

    def add_bare_bucket_heading(f):
        return rep(f, "proposal/p.md", "# proposal\n", "# proposal\n\n### A 桶：36 会话\n")
    run_case("28 C14 bare code subject as a heading trips (A 桶：36 会话)", 1,
             ["C14 代号裸用: proposal/p.md", "A 桶"], add_bare_bucket_heading, results)

    def add_bold_definition_row(f):
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n| **A** 交付 .pptx |\n")
    run_case("29 C14 bold-code definition row (口径表 form) never matches", 0,
             ["PASS doc-chain"], add_bold_definition_row, results)

    def add_paired_forms(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n交付桶（A 桶）承接演示物；A 桶（交付 .pptx）已就绪\n")
    run_case("30 C14 sanctioned paired forms 白话（代号）/代号（白话） do NOT trip", 0,
             ["PASS doc-chain"], add_paired_forms, results)

    def add_backtick_bucket(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n跑批脚本按 `A 桶` 过滤，日志另记\n")
    run_case("31 C14 inside an inline code span does NOT trip", 0,
             ["PASS doc-chain"], add_backtick_bucket, results)

    def add_glossary_row(f):
        return rep(f, "spec/s.md", "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n",
                   "| B-2 | y | 非阻塞 | ☐ 待评审确认 |\n\n| A 桶 | 交付 .pptx 的会话集合 |\n| --- | --- |\n")
    run_case("32 C14 glossary table rows are the sanctioned definition site", 0,
             ["PASS doc-chain"], add_glossary_row, results)

    def add_ip_bucket(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n限流口径：验证码与找回共用同一个 IP 桶\n")
    run_case("33 C14 real-corpus near-miss IP 桶 (letter run, not a lone code) does NOT trip", 0,
             ["PASS doc-chain"], add_ip_bucket, results)

    def add_schema_word(f):
        return rep(f, "proposal/p.md", "# proposal\n",
                   "# proposal\n\n单次执行积分按 prepared 会话口径统计\n")
    run_case("34 schema-word prose (prepared 会话) stays clause-governed — C15 deliberately "
             "not implemented (closed-set heuristic flooded a real chain's legend rows)", 0,
             ["PASS doc-chain"], add_schema_word, results)

    def run_file_case(name: str, expect_rc: int, want: list[str], text: str,
                      argv: list[str] | None = None, sub: str = "deliverable.md") -> None:
        d = Path(tempfile.mkdtemp()) / sub
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(text, encoding="utf-8")
        cmd = [sys.executable, str(linter)] + (argv if argv is not None else ["--file", str(d)])
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
        out = r.stdout + r.stderr
        ok = r.returncode == expect_rc and all(w in out for w in want)
        results.append((name, ok))
        if not ok:
            print(f"  wanted {want}, exit={r.returncode}, got:\n{out}")

    run_file_case("35 --file mode: session deliverable hitting C13+C14 exits 1", 1,
                  ["C14 代号裸用", "C13 会话角色词", "D 桶"],
                  "# 数据分析报告\n\n## 口径表\n\n| 代号 | 白话 |\n| --- | --- |\n| D | 中断桶 |\n\n"
                  "## 结论\n\nD 桶积分中断最多，本轮评审已确认。\n")
    run_file_case("36 --file mode: clean deliverable exits 0", 0, ["PASS doc-chain --file"],
                  "# 状态汇报\n\n全部检查通过，剩余两例行已排期。\n")
    run_file_case("37 --file together with a positional feature dir is a usage error", 2,
                  ["Usage"], "# 报告\n",
                  argv=[str(Path(tempfile.mkdtemp())), "--file", "deliverable.md"])
    run_file_case("38 --file without a path is a usage error", 2, ["Usage"], "# 报告\n",
                  argv=["--file"])

    # --- C13 scope + the planned-role exemption (cases 39–43). C13 is a defect in a deliverable;
    # it is skipped only on the files listed in C13_EXEMPT_FILES, one by one. The same sentence
    # must flip verdict on the file alone, and a planned role name (Execution Coordinator) is
    # neither a session word nor a reason to exempt.
    run_file_case("39 C13 role word passes in an exempt defining file (product-design.md)",
                  0, ["PASS doc-chain --file"],
                  "# product design\n\n| Supervisor（主会话） | 收口、委派 |\n",
                  sub="docs/product/design/product-design.md")
    run_file_case("40 C13 exempt file may quote the session words it defines as forbidden", 0,
                  ["PASS doc-chain --file"],
                  "# product design\n\n表达纪律禁止 supervisor、TD、本轮评审 一类会话词。\n",
                  sub="docs/product/design/product-design.md")
    run_file_case("41 Execution Coordinator is a planned role name, not a session word", 0,
                  ["PASS doc-chain --file"],
                  "# 计划\n\n未来的 Execution Coordinator 负责持久队列，本期不做。\n")
    run_file_case("42 C13 exemption is per file: an unlisted skills/ file with a role word trips",
                  1, ["C13 会话角色词"],
                  "# 说明\n\n按 supervisor 的指示执行。\n",
                  sub="skills/agentflow/references/unlisted.md")
    run_file_case("43 C13 exemption is per file: a non-exempt docs/product stage doc trips",
                  1, ["C13 会话角色词", "method-spec.md"],
                  "# method spec\n\nspec 由 supervisor 起草。\n",
                  sub="docs/product/spec/method-spec.md")

    # --- C4/C5/C8 applicability (cases 60–62): a role's checks apply when spec/<role>/ or
    # design/<role>/ holds a document, so an empty design/<role>/ cannot skip them.
    def m_spec_be_only(f):
        f.pop("design/be/b.md")
        f["spec/be/s.md"] = "# be spec\n"
        return f
    run_case("60 C4 applies when only spec/be holds a document and design/be is empty", 1,
             ["C4 design/be: 缺少含失败分支（alt）的时序图"], m_spec_be_only, results)

    def m_empty_be(f):
        f.pop("design/be/b.md")
        f["design/be/.gitkeep"] = ""
        return f
    run_case("61 C4 does NOT apply when design/be and spec/be are both empty", 0,
             ["PASS doc-chain"], m_empty_be, results)

    def m_spec_fe_only(f):
        f.pop("design/fe/f.md")
        f["spec/fe/s.md"] = "# fe spec\n"
        return f
    run_case("62 C8 applies when only spec/fe holds a document and design/fe is empty", 1,
             ["C8 design/fe: 缺少 flowchart"], m_spec_fe_only, results)

    # --- C1 段落映射豁免 (cases 47–48): an empty stage passes only with a named landing.
    def m_landing_design(f):
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        f["README.md"] += (
            "\n| 链阶段 | 落点 | 说明 |\n| --- | --- | --- |\n"
            "| design | `docs/product/design/product-design.md` | 产品设计 |\n"
        )
        return f
    run_case("47 C1 段落映射豁免: empty design/ passes when README names a landing", 0,
             ["PASS doc-chain"], m_landing_design, results)

    def m_landing_dash(f):
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        f["README.md"] += (
            "\n| 链阶段 | 落点 | 说明 |\n| --- | --- | --- |\n"
            "| design | — | 待定 |\n"
        )
        return f
    run_case("48 C1: empty design/ with a 「—」 landing still trips C1", 1,
             ["C1 结构: design/"], m_landing_dash, results)

    # --- C9 task rows and branch section (cases 49–54).
    run_case("49 C9 task row with 待核实 in the ID column is invalid", 1,
             ["ID 列非法"],
             lambda f: rep(f, "plan/be/p.md", "| T01 | 迁移 |", "| 待核实 | 迁移 |"), results)
    run_case("50 C9 status outside the fixed enum trips", 1,
             ["不在固定枚举内"],
             lambda f: rep(f, "plan/be/p.md", "☐ 未开始 |", "完成 |"), results)
    run_case("51 C9 code path that does not exist trips", 1,
             ["代码落点路径不存在: migrations/nope.sql"],
             lambda f: rep(f, "plan/be/p.md", "`migrations/x.sql`", "`migrations/nope.sql`"), results)
    run_case("52 C9 待核实 in the location cell passes without a real path", 0,
             ["PASS doc-chain"],
             lambda f: rep(f, "plan/be/p.md", "`migrations/x.sql` | — | ☐ 未开始 |",
                           "待核实 `db/schema.sql` | — | ☐ 未开始 |"), results)
    run_case("53 C9 待核实 outside the location cell does NOT rescue an empty location", 1,
             ["无仓库内路径且无「待核实」标记"],
             lambda f: rep(f, "plan/be/p.md", "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |",
                           "| T01 | 待核实迁移 | — | — | ☐ 未开始 |"), results)

    run_case("57 C9 本期不做 row needs no landing; its ID and status are still checked", 0,
             ["PASS doc-chain"],
             lambda f: rep(f, "plan/be/p.md", "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |",
                           "| T01 | 迁移 | — | — | — 本期不做 |"), results)

    def add_plan_without_branch(f):
        f["plan/be/q.md"] = "# plan q\n\n无任务表\n"
        return f
    run_case("54 C9 every plan file needs its own 分支策略 section", 1,
             ["plan/be/q.md 未声明分支策略"], add_plan_without_branch, results)

    # --- C5 ids counted from prose only (cases 55–56).
    def m_id_only_in_fence(f):
        rep(f, "design/fe/f.md", "A1 调用见异常矩阵\n", "")
        rep(f, "design/fe/f.md", "| A1 | ok | 412 |", "| X1 | ok | 412 |")
        f["design/fe/f.md"] += "```text\nA1 示例\n```\n"
        return f
    run_case("55 C5 contract id that appears only inside a code fence does NOT close", 1,
             ["C5 契约闭合", "A1"], m_id_only_in_fence, results)

    run_case("56 C5 contract id in fe prose closes (table row removed, prose mention kept)", 0,
             ["PASS doc-chain"],
             lambda f: rep(f, "design/fe/f.md", "| A1 | ok | 412 |", "| X1 | ok | 412 |"), results)

    def m_lightweight(f):
        f.pop("spec/s.md")
        f.pop("spec/qa/acceptance.md")
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        f["README.md"] = base["README.md"] + "\n轻量模式：无 spec/design 轨\n"
        return f
    run_case("42 declared lightweight chain (no spec/design track) passes C1", 0,
             ["PASS doc-chain"], m_lightweight, results)

    def m_lightweight_no_proposal(f):
        f = m_lightweight(dict(base))
        f.pop("proposal/p.md")
        return f
    run_case("43 declared lightweight chain still trips C1 when proposal is missing "
             "(the exemption narrows the stage set, it does not switch C1 off)", 1,
             ["C1 结构"], m_lightweight_no_proposal, results)

    def m_undeclared_thin(f):
        f.pop("design/be/b.md")
        f.pop("design/fe/f.md")
        return f
    run_case("63 an undeclared chain whose design track is empty still trips C1 (the exemption "
             "is declaration-gated, never inferred from emptiness)", 1,
             ["C1 结构"], m_undeclared_thin, results)

    # --- C15-C18 decision traceability (marker-gated, 2026-10-21). Each case builds a tiny
    # repo root with opt-in marker files and asserts repo_policy_findings discriminates. The
    # proposal's self-prove section requires the gate to bite its own examples: good passes,
    # mutations fail with the right check id.
    def run_repo_case(name: str, expect: int, want: list[str], files: dict,
                      with_issues: dict | None = None) -> None:
        d = Path(tempfile.mkdtemp()) / "repo"
        d.mkdir(parents=True, exist_ok=True)
        for rel, text in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        if with_issues:
            idir = d / "docs" / "issues"
            idir.mkdir(parents=True, exist_ok=True)
            for rel, text in with_issues.items():
                (idir / rel).write_text(text, encoding="utf-8")
        errs = repo_policy_findings(d)
        ok = (len(errs) == expect) and all(w in "\n".join(errs) for w in want)
        results.append((name, ok))
        if not ok:
            print(f"  wanted {expect} findings containing {want}, got {len(errs)}:\n"
                  + "\n".join(f"  - {e}" for e in errs))

    DEC_HEAD = ("| 来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    DEC_GOOD_ROW = ("| `docs/features/x/README.md:10` | A 改一 B 改二 | 2026-10-21 `grep x` | 选 A | 批次 T01 | "
                    "P2 | 多模块(youc-admin 订单筛选 + youc-canvas 支付) | N |\n")

    def dec_file(body: str) -> str:
        return ("# 决策\n\n本文件由 agentflow 决策记录方法生成（2026-10-21）\n\n" + body)

    run_repo_case("64 C16 compliant decision-record table passes", 0, [],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW)})
    run_repo_case("65 C16 missing 来源 trips C16", 1, ["C16 decision-record", "缺「来源」"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW.replace(
                      "`docs/features/x/README.md:10`", ""))})
    run_repo_case("66 C16 impact level word without module name trips C16", 1,
                  ["C16 decision-record", "只写级别词未列具体模块"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW.replace(
                      "多模块(youc-admin 订单筛选 + youc-canvas 支付)", "多模块"))})
    run_repo_case("67 C16 auto=Y on non-P3 trips C16", 1,
                  ["C16 decision-record", "自动决策=Y 仅允许 P3"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW
                      .replace("P2", "P2").replace(" | N |", " | Y |")
                      .replace("选 A", "选 A（自动规则 R1；触发条件 X；判定结论 Y）"))})
    run_repo_case("68 C16 missing verify date trips C16", 1,
                  ["C16 decision-record", "现状核验缺"],
                  {"examples/d.md": dec_file(DEC_HEAD + DEC_GOOD_ROW.replace(
                      "2026-10-21 `grep x`", "`grep x`"))})

    def ledger_file(body: str) -> str:
        return ("# 台账\n\n本文件由 agentflow 问题台账方法生成\n\n" + body)

    LED_HEAD = ("| 编号 | 一句话 | 记录链接 | 归属 |\n| --- | --- | --- | --- |\n")
    run_repo_case("69 C15 ledger row with status word and no ISS trips C15", 1,
                  ["C15 ledger-index", "台账行自带状态词"],
                  {"docs/issues/README.md": ledger_file(LED_HEAD + "| #1 | 渠道知识已修复 |  | 批次 T07 |\n")},
                  with_issues={"ISS-2026-001-x.md": "---\nstatus: fixed\n---\n"})
    run_repo_case("70 C15 compliant ledger row (ISS link resolves) passes", 0, [],
                  {"docs/issues/README.md": ledger_file(LED_HEAD + "| #1 | 渠道知识 | ISS-2026-001-x | 批次 T07 |\n")},
                  with_issues={"ISS-2026-001-x.md": "---\nstatus: fixed\n---\n"})

    OWN_HEAD = ("| 记录编号 | 任务号 | 说明 |\n| --- | --- | --- |\n")
    run_repo_case("71 C18 open issue not attached to a batch 承接表 trips C18", 1,
                  ["C18 ownership", "ISS-2026-001-x"],
                  {"docs/features/batch-a/README.md":
                   "# 批次\n\n本文件由 agentflow 决策归属方法生成\n\n" + OWN_HEAD + "| — | T01 | 收尾 |\n"},
                  with_issues={"ISS-2026-001-x.md": "---\nstatus: open\n---\n"})
    run_repo_case("72 C18 open issue covered by 承接表 passes", 0, [],
                  {"docs/features/batch-a/README.md":
                   "# 批次\n\n本文件由 agentflow 决策归属方法生成\n\n" + OWN_HEAD
                   + "| ISS-2026-001-x | T01 | 收尾 |\n"},
                   with_issues={"ISS-2026-001-x.md": "---\nstatus: open\n---\n"})

    # --- Unreadable marker file must not pass silently (2026-10-26 audit G02). The old
    # `except OSError: continue` turned a violating-but-unreadable decision record into a
    # PASS: chmod 000 flipped 8 C16 findings to zero.
    def _dec_violating() -> str:
        return dec_file(DEC_HEAD + DEC_GOOD_ROW.replace("| 批次 T01 |", "|  |"))

    def _unreadable_findings() -> list[str]:
        import tempfile

        d = Path(tempfile.mkdtemp()) / "repo"
        d.mkdir(parents=True, exist_ok=True)
        p = d / "examples" / "d.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_dec_violating(), encoding="utf-8")
        p.chmod(0o000)
        return repo_policy_findings(d)

    errs_unreadable = _unreadable_findings()
    results.append(("111 unreadable violating decision record is reported, not skipped",
                    len(errs_unreadable) >= 1
                    and any("无法读取" in e for e in errs_unreadable)))

    # --- C9 dialect / 落点基准 and C19-C21 (2026-10-21 gate change, user-authorized).
    # Cases 73-84 pin: the bare-glyph status dialect (aligned with gate/plan.py's first-char
    # read), the README 落点基准 declaration, the qa-acceptance presence check, and the two
    # opt-in README-row gates (埋点贯通 / ui 轨原型).
    def m_bare_status(f):
        return rep(f, "plan/be/p.md", "| ☐ 未开始 |", "| ☑ |")
    run_case("73 C9 bare-glyph status is legal (aligned with gate/plan.py first-char read)", 0,
             ["PASS doc-chain"], m_bare_status, results)

    def m_bare_dash(f):
        return rep(f, "plan/be/p.md", "| ☐ 未开始 |", "| — |")
    run_case("74 C9 bare dash counts as 本期不做 (no landing required)", 0,
             ["PASS doc-chain"], m_bare_dash, results)

    def m_free_text_status(f):
        return rep(f, "plan/be/p.md", "| ☐ 未开始 |", "| 已完成 |")
    run_case("75 C9 free-text status without a glyph still trips", 1,
             ["不在固定枚举内"], m_free_text_status, results)

    def m_base_ok(f):
        f["@root/lib/util.py"] = "-- util\n"
        f = rep(f, "plan/be/p.md", "`migrations/x.sql`", "`util.py`")
        f["README.md"] = f["README.md"] + "\n- 落点基准：lib\n"
        return f
    run_case("76 C9 落点基准 declaration redirects path resolution", 0,
             ["PASS doc-chain"], m_base_ok, results)

    def m_base_missing(f):
        f["@root/lib/util.py"] = "-- util\n"
        return rep(f, "plan/be/p.md", "`migrations/x.sql`", "`util.py`")
    run_case("77 C9 without a 落点基准 declaration the same cell trips", 1,
             ["代码落点路径不存在: util.py"], m_base_missing, results)

    def m_base_bad(f):
        f["README.md"] = f["README.md"] + "\n- 落点基准：no-such-dir/\n"
        return f
    run_case("78 C9 落点基准 pointing at a missing directory trips", 1,
             ["C9 落点基准"], m_base_bad, results)

    def m_no_qa(f):
        f.pop("spec/qa/acceptance.md")
        return f
    run_case("79 C19 spec with be/fe content but no qa acceptance trips", 1,
             ["C19 qa 验收"], m_no_qa, results)

    def m_no_qa_declared(f):
        f.pop("spec/qa/acceptance.md")
        f["README.md"] = f["README.md"] + "\n- 备注：qa 不适用（纯后端批）\n"
        return f
    run_case("80 C19 declared qa exemption passes", 0,
             ["PASS doc-chain"], m_no_qa_declared, results)

    def m_ui_track_bare(f):
        f = rep(f, "design/fe/f.md", WF2, "")
        f["README.md"] = f["README.md"] + "\n- UI 轨：已启用（spec/ui/visual.md + design/ui/visual.md）\n"
        return f
    run_case("81 C21 UI 轨 enabled without prototype or >=2 wireframes trips", 1,
             ["C21 ui 轨"], m_ui_track_bare, results)

    def m_ui_track_proto(f):
        f = rep(f, "design/fe/f.md", WF2, "")
        f["README.md"] = f["README.md"] + "\n- UI 轨：已启用（spec/ui/visual.md + design/ui/visual.md）\n"
        f["prototype/index.html"] = "<!doctype html>\n<html><body>" + "x" * 80 + "</body></html>\n"
        return f
    run_case("82 C21 UI 轨 enabled with a real prototype passes", 0,
             ["PASS doc-chain"], m_ui_track_proto, results)

    def m_track_bare(f):
        f["README.md"] = f["README.md"] + "\n- 埋点：本期新增 2 个事件（design/fe §1.7）\n"
        return f
    run_case("83 C20 埋点新增 declared without the three sections trips", 1,
             ["C20 埋点贯通"], m_track_bare, results)

    def m_track_ok(f):
        f["README.md"] = f["README.md"] + "\n- 埋点：本期新增 2 个事件（design/fe §1.7）\n"
        f["proposal/p.md"] = f["proposal/p.md"] + "\n## 6.2 埋点决策\n"
        f["spec/s.md"] = f["spec/s.md"] + "\n### 4. 埋点验收草案\n"
        f["design/fe/f.md"] = f["design/fe/f.md"] + "\n### 1.7 埋点事件契约\n"
        return f
    run_case("84 C20 埋点新增 with the three sections passes", 0,
             ["PASS doc-chain"], m_track_ok, results)

    # unfilled template placeholders never fire the opt-in gates
    def m_track_placeholder(f):
        f["README.md"] = f["README.md"] + "\n- 埋点：<本期新增 n 个事件（design/fe §1.7）｜复用既有事件 <事件名>｜N/A: 理由>\n- UI 轨：<已启用（spec/ui/visual.md + design/ui/visual.md）｜未启用>\n- 落点基准：<.（主实施仓根，默认）｜<相对目标仓根的路径>｜本批次目录>\n"
        return f
    run_case("85 unfilled README 落点基准/埋点/UI 轨 placeholders never fire", 0,
             ["PASS doc-chain"], m_track_placeholder, results)

    # --- C22 goal traceability and C23 evidence presence (2026-10-23 gate change,
    # user-authorized). Cases 86-95 pin the four C22 directions (missing carrier row, phantom
    # task id, status over-claim, orphan completed task), the marker-without-table case, the
    # four evidence carriers, the /tmp-only failure, and that an unmarked batch is untouched.
    TRACE_README = (
        "# feature\n\n## 需求评审门\n## 技术方案评审门\n\n"
        "本批次启用 agentflow 目标承接 标记，承接表如下。\n\n"
        "## 目标承接表\n\n"
        "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "{rows}"
    )
    TRACE_ROW_OK = ("| G1 目标一 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n")
    TRACE_SPEC = (
        "# spec\n\n## 3.0 不合规项（反审 checklist）\n\n"
        "| # | 缺口 | 阻塞 | 状态 |\n| --- | --- | --- | --- |\n| B-1 | x | 阻塞 | ☑ 已关闭 |\n\n"
        "### M-A 模块一\n\n| 验收点 | 来源 |\n| --- | --- |\n| G1-AC-01 | proposal §1.2 G1 |\n"
    )

    def trace_plan(evidence: str, status: str = "☑ 已完成") -> str:
        return (
            "# plan\n\n## 0. 分支策略 feature-x\n\n"
            "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| T01 | 迁移 | `migrations/x.sql` | — | {status} | {evidence} |\n\n"
            "V-9 由 T01 承接\n"
        )

    def trace_files(rows: str = TRACE_ROW_OK, evidence: str = "`migrations/x.sql` 在盘",
                    status: str = "☑ 已完成") -> dict:
        return {
            "README.md": TRACE_README.format(rows=rows),
            "proposal/p.md": "# proposal\n\n目标：G1 目标一（可判定）。\n",
            "spec/s.md": TRACE_SPEC,
            "plan/be/p.md": trace_plan(evidence, status),
            "@root/migrations/x.sql": "-- x\n",
        }

    def m_trace_ok(f):
        f.update(trace_files())
        return f
    run_case("86 C22 marked batch with a closed 承接表 passes", 0,
             ["PASS doc-chain"], m_trace_ok, results)

    def m_trace_missing_goal(f):
        f.update(trace_files(rows="| G2 目标二 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n"))
        return f
    run_case("87 C22 a goal declared upstream but absent from the table trips", 1,
             ["C22 目标承接", "未进入承接表"], m_trace_missing_goal, results)

    def m_trace_phantom_task(f):
        f.update(trace_files(rows=TRACE_ROW_OK.replace("T01", "T99")))
        return f
    run_case("88 C22 a task id cited by the table but missing from the plan trips", 1,
             ["C22 目标承接", "不在计划任务表"], m_trace_phantom_task, results)

    def m_trace_status_lie(f):
        f.update(trace_files(rows=TRACE_ROW_OK.replace("☑ 已完成", "☑ 已完成"),
                              status="☐ 未开始"))
        return f
    run_case("89 C22 table claims done while the board row is still 未开始 trips", 1,
             ["C22 目标承接", "承接表标已完成"], m_trace_status_lie, results)

    def m_trace_orphan_done(f):
        files = trace_files(rows=TRACE_ROW_OK.replace("T01", "—"))
        files["README.md"] = files["README.md"].replace("| T01 |", "| — |")
        f.update(files)
        return f
    run_case("90 C22 a completed task nobody claims trips as an orphan", 1,
             ["C22 目标承接", "孤儿任务"], m_trace_orphan_done, results)

    def m_trace_no_table(f):
        f["README.md"] = "# feature\n\n## 需求评审门\n## 技术方案评审门\n\n本批启用 agentflow 目标承接 标记。\n"
        return f
    run_case("91 C22 marker without a table trips instead of silently skipping", 1,
             ["C22 目标承接", "没有承接表"], m_trace_no_table, results)

    def m_trace_unmarked(f):
        f.update(trace_files())
        f["README.md"] = f["README.md"].replace("agentflow 目标承接", "目标承接")
        return f
    run_case("92 C22/C23 never fire on a batch that did not opt in (no false positives)", 0,
             ["PASS doc-chain"], m_trace_unmarked, results)

    def m_trace_tmp_evidence(f):
        f.update(trace_files(evidence="`/tmp/baseline.txt`（已随临时目录清理）"))
        return f
    run_case("93 C23 a ☑ row whose only evidence is a cleaned /tmp path trips", 1,
             ["C23 证据在场", "T01"], m_trace_tmp_evidence, results)

    def m_trace_repo_ref(f):
        f.update(trace_files(evidence="youc@1a2b3c4:docs/x.md 与 `N/A: 无额外产物`"))
        return f
    run_case("94 C23 repo-qualified refs and explicit N/A with reason are carriers", 0,
             ["PASS doc-chain"], m_trace_repo_ref, results)

    def m_trace_empty_evidence(f):
        f.update(trace_files(evidence=""))
        return f
    run_case("95 C23 an empty evidence cell on a ☑ row trips", 1,
             ["C23 证据在场", "证据列为空"], m_trace_empty_evidence, results)

    # Repo-scan side: C23 applies to every batch (the evidence duty belongs to the plan
    # contract, not to the opt-in marker), while C22 only bites opted-in batches.
    PLAN_TMP = (
        "# plan\n\n## 0. 分支策略 feature-x\n\n"
        "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n| --- | --- | --- | --- | --- | --- |\n"
        "| T01 | 迁移 | `a.py` | — | ☑ 已完成 | `/tmp/x.txt` 已清理 |\n"
    )
    UNMARKED_TRACE_README = (
        "# 批次\n\n## 需求评审门\n## 技术方案评审门\n\n目标承接如下（未打启用标记）。\n\n"
        "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| G1 目标一 | — | M-A | T01 | ☑ 已完成 |\n"
    )
    run_repo_case("96 C23 catches cleaned /tmp evidence in a batch that did not opt in", 1,
                  ["C23 证据在场", "T01"],
                  {"docs/features/b/README.md": "# 批次\n\n## 需求评审门\n",
                   "docs/features/b/plan/p.md": PLAN_TMP})
    run_repo_case("97 C22 skips an unmarked batch in the repo scan (opt-in preserved)", 0, [],
                  {"docs/features/b/README.md": UNMARKED_TRACE_README,
                   "docs/features/b/plan/p.md": trace_plan("N/A: 夹具，无额外产物")})

    # --- C24 single-ledger mode (2026-10-23 gate change, user-authorized). HISTORY.md present
    # while README.md is absent becomes the chain's single ledger: it carries C2 entry gates and,
    # when C22 is in scope, the 目标承接 mark + table. Purely additive — README present keeps the
    # README-path rules; HISTORY.md is then just another stage doc.
    TRACE_HISTORY = (
        "# HISTORY 任务记录\n\n## 当前状态\n\n| 字段 | 内容 |\n| --- | --- |\n"
        "| 当前节点 | 已交付人 |\n| 总体状态 | 已完成 |\n\n"
        "## 需求评审门\n## 技术方案评审门\n\n"
        "本批次启用 agentflow 目标承接 标记，承接表如下。\n\n"
        "## 目标承接表\n\n"
        "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "{rows}"
    )

    def m_history_ok(f):
        # README absent, HISTORY present, and the 承接表 closed — single-ledger mode, passes C1/C2,
        # and the traceability read comes from HISTORY.md.
        f.pop("README.md")
        f["HISTORY.md"] = TRACE_HISTORY.format(rows=TRACE_ROW_OK)
        f["proposal/p.md"] = "# proposal\n\n目标：G1 目标一（可判定）。\n"
        f["spec/s.md"] = TRACE_SPEC
        f["plan/be/p.md"] = trace_plan("`migrations/x.sql` 在盘")
        return f
    run_case("99 C24 single-ledger batch (HISTORY, no README) passes C1/C2/C22", 0,
             ["PASS doc-chain"], m_history_ok, results)

    def m_history_missing_gates(f):
        f = m_history_ok(dict(base))
        f["HISTORY.md"] = f["HISTORY.md"].replace("## 需求评审门\n## 技术方案评审门\n", "")
        return f
    run_case("100 C24 single-ledger batch missing entry gates in HISTORY trips C2", 1,
             ["C2 入口门禁", "HISTORY.md"], m_history_missing_gates, results)

    def m_history_orphan(f):
        f = m_history_ok(dict(base))
        f["HISTORY.md"] = f["HISTORY.md"].replace("| T01 |", "| — |")
        return f
    run_case("101 C24 single-ledger batch with an orphan completed task trips C22 in HISTORY", 1,
             ["C22 目标承接", "孤儿任务"], m_history_orphan, results)

    def m_history_with_readme(f):
        # Both files present: README mode wins, HISTORY.md is an ordinary stage doc (not a ledger).
        # The README already carries the gates and a closed 承接表, so it must pass unchanged.
        f.update(trace_files())
        f["HISTORY.md"] = "# HISTORY\n\n（仅作阶段事件账本，不接管门禁）\n"
        return f
    run_case("102 C24 both README and HISTORY present: README governs, HISTORY is a stage doc", 0,
             ["PASS doc-chain"], m_history_with_readme, results)

    def m_base_inline_default(f):
        # 元信息写在同一行、且声明的就是默认值：不得凭空造出一个不存在的目录
        f["README.md"] = (f["README.md"]
                          + "\n- UI 轨：未启用；落点基准：.（主实施仓根，默认）；最后更新时间：2026-10-23\n")
        return f
    run_case("98 C9 落点基准 declared inline as the default value never invents a missing dir", 0,
             ["PASS doc-chain"], m_base_inline_default, results)

    # --- 2026-10-23 独立评审 findings 的回归夹具（100-106）：每条都对应评审指出的一个
    # 「声明了但没校验」或「判据静默失明」的空洞。
    def m_evid_backticked_task_id(f):
        files = trace_files(evidence="`/tmp/x.txt`（已清理）")
        files["plan/be/p.md"] = files["plan/be/p.md"].replace("| T01 |", "| `T01` |")
        f.update(files)
        return f
    run_case("100 C23 reads backtick-quoted task ids (the dialect that once made it blind)", 1,
             ["C23 证据在场", "T01"], m_evid_backticked_task_id, results)

    def m_evid_bare_path(f):
        files = trace_files(evidence="docs/x.md 的原始输出已入库")
        files["@root/docs/x.md"] = "# x\n"
        f.update(files)
        return f
    run_case("101 C23 accepts a bare written repo path, as the contract states", 0,
             ["PASS doc-chain"], m_evid_bare_path, results)

    def m_trace_phantom_source(f):
        f.update(trace_files(rows="| G1 目标一 | `proposal/NOPE.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n"))
        return f
    run_case("102 C22 validates the 出处 column, not just the spec column", 1,
             ["C22 目标承接", "proposal/NOPE.md 不在盘"], m_trace_phantom_source, results)

    def m_trace_decoy_placement(f):
        files = trace_files()
        files["README.md"] = files["README.md"].replace("## 目标承接表", "## 随便一张同形表")
        files["@root/README-decoy.md"] = ""
        f.update(files)
        return f
    run_case("103 C22 reads only the table under the 目标承接 heading (decoy elsewhere trips)", 1,
             ["C22 目标承接", "标题下没有承接表"], m_trace_decoy_placement, results)

    def m_trace_decorated_header(f):
        files = trace_files()
        files["README.md"] = files["README.md"].replace(
            "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n",
            "| **目标** | `proposal 出处` | **spec 承接** | plan 任务 | 状态 |\n")
        f.update(files)
        return f
    run_case("104 C22 matches decorated column labels instead of reporting 缺表", 0,
             ["PASS doc-chain"], m_trace_decorated_header, results)

    def m_trace_status_stale(f):
        f.update(trace_files(rows="| G1 目标一 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ◐ 进行中 |\n",
                             status="☑ 已完成"))
        return f
    run_case("105 C22 catches a 进行中 row whose tasks are all done (both directions)", 1,
             ["C22 目标承接", "未回写"], m_trace_status_stale, results)

    def m_evid_self_repo_ref(f):
        f.update(trace_files(evidence="agentflow@0000000:zzz.md"))
        return f
    run_case("106 C23 verifies a ref qualified with this repo's own name instead of waving it through", 1,
             ["C23 证据在场", "T01"], m_evid_self_repo_ref, results)

    # C23 reverse judgment (2026-10-26 audit G05): a path token that resolves to a DIRECTORY is
    # a location, not a verifiable artifact, so it must not alone satisfy C23. The fixture's only
    # evidence names an existing directory (the batch root itself) — it must trip.
    def m_evid_dir_token(f):
        f.update(trace_files(evidence="见 `docs/features` 目录下的产物"))
        return f
    run_case("107 C23 a ☑ row whose only evidence is a directory path trips (location != proof)", 1,
             ["C23 证据在场", "T01"], m_evid_dir_token, results)
    def m_evid_file_token(f):
        # the same wording but pointing at a real FILE (the deliverable) passes
        f.update(trace_files(evidence="见 `migrations/x.sql` 落盘"))
        return f
    run_case("108 C23 a ☑ row pointing at a real deliverable file is a valid carrier", 0,
             ["PASS doc-chain"], m_evid_file_token, results)

    def m_ft_task_id(f):
        # C9 的任务号方言：FT 前缀与一两位数字都必须合法（曾被 C22 的同名常量遮蔽）
        return rep(f, "plan/be/p.md", "| T01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |",
                              "| FT01 | 迁移 | `migrations/x.sql` | — | ☐ 未开始 |")
    run_case("99 C9 still accepts the FT-prefixed task id dialect (constant shadowing guard)", 0,
             ["PASS doc-chain"], m_ft_task_id, results)

    ok = all(passed for _, passed in results)
    for name, passed in results:
        print(("PASS " if passed else "FAIL ") + name)
    print(f"{sum(p for _, p in results)}/{len(results)} self-test cases pass")
    return 0 if ok else 1


