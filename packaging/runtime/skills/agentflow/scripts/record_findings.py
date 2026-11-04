#!/usr/bin/env python3
"""record_findings.py — 评审轮末把 reviewer findings 机械立案为 ISS 记录。

解决什么：问题闭环（issue-tracking.md §0）要求确认缺陷强制落账（ISS 或评审缺陷表二选一），
但落账靠 supervisor 手工——产品 findings 还会写进评审缺陷表，过程/规范类缺陷经常没人立，
「评审说了、没人记账、下批再犯」。本脚本把立案变成机械步骤：读 reviewer 返回的 findings
YAML，逐条生成 ISS 记录（按 issue-template.md 形态），追加台账行，输出 finding→ISS 映射
（回填评审记录），并把 reviewer 原始 YAML 归档进评审记录（contracts.md「编号唯一与记录可回放」）。

用法：
  python3 record_findings.py --findings <报告.yaml 或 -> --issues-dir <记录根>/issues
        --project <项目 slug>
        [--review-id <评审id>] [--round N] [--claimed-by <承接批次标识>]
        [--min-severity P1] [--all]
        [--attribution product_code] [--defect-class 代码] [--escape-stage 评审]
        [--error-kind other] [--agentflow-version <版本>]
        [--archive-yaml-to <评审记录.md>]
        [--dry-run] [--self-test]

  --findings      reviewer 报告全文或仅 findings 块（`findings:` 缩进块序列）；`-` 读 stdin；
                  顶格列表项（`- severity:` 不缩进）不是合法输入，报错不猜
  --issues-dir    记录根的 issues/ 目录（含台账 README.md 时自动追加台账行并替换模板占位行）
  --project       ISS frontmatter 的 project 字段（必填；记录归属哪个项目）
  --claimed-by    给出时该记录视为已被该批次承接（不写 disposition）；缺省写 disposition: deferred
  --min-severity  立案下限，默认 P1（P0/P1）；--all 时忽略下限全量立案
  --attribution / --defect-class / --escape-stage / --error-kind
                  ISS frontmatter 归因维度，默认按代码评审 findings：product_code / 代码 / 评审 / other；
                  过程/规范类发现改用 workflow_policy / 流程 等组合
  --agentflow-version  归因到 agentflow 或需判断复发版本时填写；缺省整行省略（模板「不适用时删行」）
  --archive-yaml-to  给出时把 reviewer 原始 YAML 追加进该评审记录（与是否立案无关；dry-run 下不写盘）

退出码：0 = 已立案（或 dry-run 计划）；1 = 无符合条件的 findings（不算错误）；2 = 输入或用法错误。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
_FINDING_KEYS = ("severity", "location", "issue", "evidence", "cost", "fix", "id")
_ENTRY_RE = re.compile(r"^(\s*)-\s+(\w+):\s*(.*)$")
_KEY_RE = re.compile(r"^(\s*)(\w+):\s*(.*)$")
LEDGER_HEADER = "| 编号 | 一句话 | 记录链接 | 归属 |"
LEDGER_SEPARATOR = "| --- | --- | --- | --- |"
# 台账占位行判据：模板示例行（hub/issues-README.md 的 `ISS-YYYY-MM-DD-<slug>`）或旧式占位文本
PLACEHOLDER_MARKS = ("ISS-YYYY-MM-DD-<slug>", "（当前无开放条目）")

OWNERSHIP = {
    "代码": "目标仓",
    "规范": "agentflow 方法侧",
    "模板": "agentflow 方法侧",
    "流程": "agentflow 方法侧",
}


def parse_findings(text: str) -> list[dict[str, str]]:
    """从 reviewer 报告中解析 findings 块（缩进的 `- key: value` 块序列）。

    支持全文（含 decision/status 等其它顶层键）或仅 findings 块；与字段同缩进的行是
    下一个字段，更深缩进的行（含形如 `key:` 的引用片段）并入前值。缺失 severity/issue
    或顶格列表项按非法输入报错，不猜。
    """
    lines = text.splitlines()
    start = None
    for i, raw in enumerate(lines):
        if re.match(r"^findings:\s*$", raw):
            start = i + 1
            break
        if re.match(r"^findings:\s*\[\s*\]\s*$", raw):
            return []
    if start is None:
        raise ValueError("输入中找不到 `findings:` 块（或空列表 `findings: []`）")

    findings: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    current_key: str | None = None
    field_indent: int | None = None  # 条目字段行的缩进；更深缩进 = 前值续行
    for raw in lines[start:]:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        entry = _ENTRY_RE.match(raw)
        if not raw.startswith((" ", "\t")):  # 顶层行 → findings 块结束
            if entry and current is None and not findings:
                raise ValueError(
                    "findings 为顶格列表项（`- severity:` 未缩进）——本脚本只接受缩进块形态，请修正输入")
            break
        if entry and entry.group(2) in _FINDING_KEYS:
            if current is not None:
                findings.append(current)
            current = {entry.group(2): entry.group(3).strip()}
            current_key = entry.group(2)
            field_indent = len(entry.group(1)) + 2  # `- ` 之后的字段缩进
            continue
        key = _KEY_RE.match(raw)
        if current is None:
            continue  # findings: 前导的其它缩进行，忽略
        if key and key.group(2) in _FINDING_KEYS and len(key.group(1)) == field_indent:
            current[key.group(2)] = key.group(3).strip()
            current_key = key.group(2)
        elif current_key:
            # 续行（含形如 `key:` 的更深缩进引用片段）并入前值，不覆盖
            current[current_key] = (current[current_key] + " " + raw.strip()).strip()
    if current is not None:
        findings.append(current)

    for i, f in enumerate(findings, 1):
        if not f.get("severity"):
            raise ValueError(f"第 {i} 条 finding 缺 severity（输入不合法，不猜测）")
        if f["severity"] not in SEVERITY_ORDER:
            raise ValueError(f"第 {i} 条 finding severity 非法：{f['severity']!r}")
        if not f.get("issue"):
            raise ValueError(f"第 {i} 条 finding 缺 issue 描述")
    return findings


def slugify(issue: str) -> str:
    cleaned = re.sub(r"[\s/:*?\"<>|`\\（）()【】\[\]{}，。；：、'\"—…·]+", "", issue)
    return cleaned[:12] or "finding"


def render_iss(finding: dict[str, str], *, bug_id: str, now: str, local_stamp: str,
               project: str, review_id: str | None, round_no: int | None,
               claimed_by: str | None, attribution: str, defect_class: str,
               escape_stage: str, error_kind: str, agentflow_version: str | None) -> str:
    severity = finding["severity"]
    location = finding.get("location", "（未给位置）")
    issue = finding["issue"]
    evidence = finding.get("evidence", "（未附证据）")
    cost = finding.get("cost", "（未写代价）")
    fix = finding.get("fix", "（未给修法）")
    # frontmatter 安全：半角「冒号+空格」会破坏 YAML mapping，替换为全角
    title = issue.replace(": ", "：")
    source = f"（来源：{review_id}" + (f" 第 {round_no} 轮）" if round_no else "）") if review_id else ""
    disposition_line = "" if claimed_by else "disposition: deferred"
    claimed_note = f"承接批次：{claimed_by}（承接后同轮修复）。" if claimed_by else "承接批次未定（disposition: deferred）。"
    version_line = f"agentflow_version: {agentflow_version}\n" if agentflow_version else ""
    verify_gap = ""
    if attribution == "product_code":
        verify_gap = """
## 验证缺口

待补——修复批次按五类失效模式逐条判定，命中哪类写哪类，一类都不命中写「不适用 — 理由」：
M1 入口未覆盖｜M2 断言与实现同源｜M3 跨边界不变量无 owner｜M4「测不了」被降级｜M5 环境掩盖。
每条写清「缺哪个入口/断言/不变量」与「应补的用例（入口 + 证据层级）或检查」。
"""
    return f"""---
bug_id: {bug_id}
title: {title}
status: open
{disposition_line}
severity: {severity}
error_kind: {error_kind}
attribution: {attribution}
provenance: session-artifact
defect_class: {defect_class}
escape_stage: {escape_stage}
project: {project}
files:
  - {location}
recorded_at: {now}
{version_line}updated_at: {now}
---

## 现象

{issue}（严重度 {severity}）{source}
位置：{location}
观察证据：{evidence}
影响面/代价：{cost}

## 根因

待补——立案时仅登记 finding 证据；根因与归因依据由修复批次（或 bug-investigator）补齐，引用覆盖它的条款（`path:line`）或写明无条款覆盖。
{verify_gap}
## 修复方案

{claimed_note}候选修法（评审给出）：{fix}
方案状态：待审核——实施前由承接批次确认；无法可靠建议时写明缺少的证据或待人决定。

## 回归检查

未运行——修复未落地（open）。

## 怎么避免

open 阶段候选措施待承接批次提出；`defect_class: {defect_class}` 非「代码」时，verified 后须按 issue-tracking §3 回填 agentflow 改进 commit。

## 变更记录

- {local_stamp} · 立案（record_findings.py） · {source or "来源评审见映射表"}
"""


def append_ledger(issues_dir: Path, rows: list[str]) -> bool:
    """向 issues/README.md 台账追加行；替换模板占位行（含占位标记的整行）。返回是否找到台账。"""
    readme = issues_dir / "README.md"
    if not readme.is_file():
        return False
    lines = readme.read_text(encoding="utf-8").splitlines()
    try:
        sep_idx = next(i for i, l in enumerate(lines) if l.strip() == LEDGER_SEPARATOR)
    except StopIteration:
        return False
    end = sep_idx + 1
    while end < len(lines) and (lines[end].startswith("|") or any(ph in lines[end] for ph in PLACEHOLDER_MARKS)):
        end += 1
    block = lines[sep_idx + 1:end]
    kept = [l for l in block if not any(ph in l for ph in PLACEHOLDER_MARKS)]
    lines[sep_idx + 1:end] = kept + rows
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def archive_yaml(review_record: Path, yaml_text: str, round_no: int | None, review_id: str | None) -> None:
    head = f"## 第 {round_no} 轮 reviewer 原始返回（归档）" if round_no else "## reviewer 原始返回（归档）"
    if review_id:
        head += f" — {review_id}"
    with review_record.open("a", encoding="utf-8") as fh:
        fh.write(f"\n{head}\n\n```yaml\n{yaml_text.rstrip()}\n```\n")


def do_archive(archive_to: str, yaml_text: str, round_no: int | None, review_id: str | None) -> None:
    """把 reviewer 原始 YAML 追加进评审记录；目标不存在时告警不中断。"""
    record = Path(archive_to)
    if record.is_file():
        archive_yaml(record, yaml_text, round_no, review_id)
        print(f"[ok] reviewer 原始 YAML 已归档 -> {record}")
    else:
        print(f"[警告] --archive-yaml-to 文件不存在，未归档：{record}", file=sys.stderr)


def check_record(path: Path, bug_id: str) -> list[str]:
    """模板合法性自检：bug_id 与文件名、recorded_at 日期一致，必填节与 frontmatter 关键字段。"""
    problems: list[str] = []
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 2 else ""
    m_date = re.search(r"^recorded_at: (\d{4}-\d{2}-\d{2})", frontmatter, re.MULTILINE)
    bug_date = "-".join(bug_id.split("-")[1:4])
    if not m_date:
        problems.append("frontmatter 缺 recorded_at")
    elif m_date.group(1) != bug_date:
        problems.append(f"bug_id 日期 {bug_date} ≠ recorded_at 日期 {m_date.group(1)}")
    for section in ("## 现象", "## 根因", "## 修复方案", "## 变更记录"):
        if section not in text:
            problems.append(f"缺必填节 {section}")
    for field in ("bug_id:", "status:", "severity:", "defect_class:", "escape_stage:", "project:"):
        if field not in frontmatter:
            problems.append(f"frontmatter 缺 {field}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="评审 findings 机械立案为 ISS 记录")
    ap.add_argument("--findings", default=None, help="reviewer 报告文件（或 `-` 读 stdin）")
    ap.add_argument("--issues-dir", default=None, help="记录根的 issues/ 目录")
    ap.add_argument("--project", default=None, help="ISS frontmatter 的 project 字段（必填）")
    ap.add_argument("--review-id", default=None, help="评审记录 id（写入来源与台账）")
    ap.add_argument("--round", type=int, default=None, help="评审轮次号")
    ap.add_argument("--claimed-by", default=None, help="承接批次标识；给出时不写 disposition")
    ap.add_argument("--min-severity", default="P1", choices=["P0", "P1", "P2", "P3"],
                    help="立案下限（默认 P1）")
    ap.add_argument("--all", action="store_true", help="忽略下限，全量立案")
    ap.add_argument("--attribution", default="product_code",
                    choices=["workflow_policy", "role_prompt", "context", "tool_or_host",
                             "model_limit", "product_code", "evaluation", "unknown"])
    ap.add_argument("--defect-class", default="代码", choices=["规范", "模板", "流程", "代码"])
    ap.add_argument("--escape-stage", default="评审", choices=["需求", "设计", "实现", "测试", "评审"])
    ap.add_argument("--error-kind", default="other",
                    choices=["ai-ignored-doc", "ai-ignored-code", "missing-constraint",
                             "hallucination", "logic-error", "host-compat", "environment", "other"])
    ap.add_argument("--agentflow-version", default=None,
                    help="归因到 agentflow 或需判断复发版本时填写；缺省整行省略")
    ap.add_argument("--archive-yaml-to", default=None, help="reviewer 原始 YAML 归档进该评审记录")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不写任何文件")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not args.findings or not args.issues_dir or not args.project:
        ap.error("需要 --findings、--issues-dir 与 --project（或 --self-test）")

    if args.findings == "-":
        yaml_text = sys.stdin.read()
    else:
        try:
            yaml_text = Path(args.findings).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[错误] --findings 不可读：{exc}", file=sys.stderr)
            return 2
    try:
        findings = parse_findings(yaml_text)
    except ValueError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 2

    threshold = SEVERITY_ORDER[args.min_severity]
    selected = findings if args.all else [f for f in findings if SEVERITY_ORDER[f["severity"]] <= threshold]

    issues_dir = Path(args.issues_dir)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    local_stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    ownership = OWNERSHIP.get(args.defect_class, "待归属")
    mapping: list[str] = []
    rows: list[str] = []
    planned: list[tuple[Path, str, str]] = []
    used: set[str] = set()

    for i, f in enumerate(selected, 1):
        slug = slugify(f["issue"])
        date_part = now[:10]
        bug_id = f"ISS-{date_part}-{slug}"
        target = issues_dir / f"{bug_id}.md"
        # 同名冲突（磁盘已有或本批次已用）：追加序号保证唯一，不覆盖
        n = 2
        while target.exists() or bug_id in used:
            bug_id = f"ISS-{date_part}-{slug}-{n}"
            target = issues_dir / f"{bug_id}.md"
            n += 1
        used.add(bug_id)
        content = render_iss(f, bug_id=bug_id, now=now, local_stamp=local_stamp,
                             project=args.project, review_id=args.review_id,
                             round_no=args.round, claimed_by=args.claimed_by,
                             attribution=args.attribution, defect_class=args.defect_class,
                             escape_stage=args.escape_stage, error_kind=args.error_kind,
                             agentflow_version=args.agentflow_version)
        planned.append((target, bug_id, content))
        label = f.get("id") or f"findings[{i}]"
        mapping.append(f"  {label}（{f['severity']}，{f['issue'][:24]}…） -> {bug_id}")
        cell = f["issue"][:40].replace("|", "／")
        rows.append(f"| {bug_id} | {cell} | [{bug_id}.md]({bug_id}.md) | {ownership} |")

    # reviewer 原始 YAML 归档与立案解耦：无论是否立案都归档，但 dry-run 承诺不写任何文件
    if args.archive_yaml_to and not args.dry_run:
        do_archive(args.archive_yaml_to, yaml_text, args.round, args.review_id)

    if not selected:
        print(f"[ok] findings 共 {len(findings)} 条，符合立案下限 {args.min_severity} 的 0 条——不立案（非错误）")
        return 1

    print(f"立案计划：{len(selected)}/{len(findings)} 条（下限 {args.min_severity}"
          + ("，--all" if args.all else "") + "）")
    for line in mapping:
        print(line)
    if args.dry_run:
        print("dry-run：未写任何文件。")
        return 0

    issues_dir.mkdir(parents=True, exist_ok=True)
    for target, bug_id, content in planned:
        target.write_text(content, encoding="utf-8")
        problems = check_record(target, bug_id)
        if problems:
            print(f"[错误] {target.name} 模板自检未过：{'；'.join(problems)}", file=sys.stderr)
            return 2
    ledger_ok = append_ledger(issues_dir, rows)
    print(f"[ok] 已立案 {len(planned)} 条 -> {issues_dir.resolve()}"
          + ("；台账已追加" if ledger_ok else "；未找到台账 README（跳过台账行）"))
    print("收口提醒：defect_class 非「代码」的记录 verified 后须按 issue-tracking §3 反哺 agentflow；"
          "映射表请回填评审记录 findings 表。")
    return 0


def _self_test() -> int:
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def case(name, fn):
        base = Path(tempfile.mkdtemp(prefix="af-record-"))
        try:
            fn(base)
            results.append((name, True, ""))
        except AssertionError as exc:
            results.append((name, False, str(exc)))
        finally:
            import shutil
            shutil.rmtree(base, ignore_errors=True)

    SAMPLE = """decision: changes_requested
status: complete
findings:
  - severity: P1
    location: src/api/client.js:26-49
    issue: csrf 获取无超时
    evidence: fetchCsrf 的 fetch 无 signal
    cost: 登录锁永不释放
    fix: 加 AbortController
  - severity: P2
    location: README.md:3
    issue: 覆盖声明夸大
    evidence: 声称有 Ego 证据
residual_risks: 略
"""
    HUB_README = (
        "# issues — 缺陷与事项流\n\n## 开放条目\n\n" + LEDGER_HEADER + "\n" + LEDGER_SEPARATOR + "\n"
        + "| ISS-YYYY-MM-DD-<slug> | <一句话现象> | `ISS-YYYY-MM-DD-<slug>.md` | <负责人 / 关联批次> |\n"
        + "\n> 台账不写状态结论。\n"
    )

    def t_parse(base: Path) -> None:
        rows = parse_findings(SAMPLE)
        assert len(rows) == 2 and rows[0]["severity"] == "P1" and rows[0]["cost"] == "登录锁永不释放", rows
        assert parse_findings("decision: approved\nfindings: []\nstatus: complete\n") == []
        multi = SAMPLE.replace("evidence: fetchCsrf 的 fetch 无 signal\n",
                               "evidence: fetchCsrf 的 fetch 无 signal\n      且无计时器，两层问题\n")
        assert "两层问题" in parse_findings(multi)[0]["evidence"]
        # 更深缩进、形如 `key:` 的引用片段并入前值，不覆盖字段
        quoted = SAMPLE.replace(
            "    evidence: fetchCsrf 的 fetch 无 signal\n",
            "    evidence: 引用上轮原文\n        issue: csrf timeout missing\n    （引文完）\n")
        parsed = parse_findings(quoted)
        assert parsed[0]["issue"] == "csrf 获取无超时", f"字段被续行窃改：{parsed[0]['issue']}"
        assert "issue: csrf timeout missing" in parsed[0]["evidence"], "续行未并入 evidence"
        assert "（引文完）" in parsed[0]["evidence"], "字段后的续行未并入"
        # 顶格列表项 → 报错
        try:
            parse_findings("findings:\n- severity: P1\n  issue: 顶格\n")
        except ValueError:
            pass
        else:
            raise AssertionError("顶格列表项应报错")

    def t_end_to_end(base: Path) -> None:
        issues = base / "issues"
        issues.mkdir()
        report = base / "report.yaml"
        report.write_text(SAMPLE, encoding="utf-8")
        (issues / "README.md").write_text(HUB_README, encoding="utf-8")
        rc = main_with(["--findings", str(report), "--issues-dir", str(issues),
                        "--project", "test-login", "--review-id", "review-x", "--round", "1"])
        assert rc == 0, f"exit {rc}"
        created = sorted(p.name for p in issues.glob("ISS-*.md"))
        assert len(created) == 1, created  # P2 被默认下限滤掉
        text = (issues / created[0]).read_text(encoding="utf-8")
        for token in ("status: open", "severity: P1", "attribution: product_code",
                      "defect_class: 代码", "project: test-login", "disposition: deferred",
                      "## 现象", "## 验证缺口", "## 变更记录"):
            assert token in text, f"缺 {token}"
        assert "agentflow_version" not in text, "缺省不应写 agentflow_version"
        readme = (issues / "README.md").read_text(encoding="utf-8")
        assert "ISS-YYYY-MM-DD-<slug>" not in readme.split("## 开放条目")[1].split("> 本表")[0], "占位行未替换"
        assert created[0] in readme, "台账缺新行"
        assert "| 目标仓 |" in readme, "归属列缺失"

    def t_all_dry_run_and_claimed(base: Path) -> None:
        issues = base / "issues"
        report = base / "report.yaml"
        record = base / "review.md"
        report.write_text(SAMPLE, encoding="utf-8")
        record.write_text("# 评审记录\n", encoding="utf-8")
        rc = main_with(["--findings", str(report), "--issues-dir", str(issues),
                        "--project", "p", "--all", "--dry-run",
                        "--archive-yaml-to", str(record)])
        assert rc == 0, f"exit {rc}"
        assert not list(issues.glob("ISS-*.md")), "dry-run 不应写文件"
        assert record.read_text(encoding="utf-8") == "# 评审记录\n", "dry-run 不应写归档"
        rc2 = main_with(["--findings", str(report), "--issues-dir", str(issues),
                         "--project", "p", "--all", "--claimed-by", "agentflows@fix-batch"])
        assert rc2 == 0, f"exit {rc2}"
        assert len(list(issues.glob("ISS-*.md"))) == 2, "全量立案应为 2 条"
        text = list(issues.glob("ISS-*.md"))[0].read_text(encoding="utf-8")
        assert "disposition" not in text, "承接后不应写 disposition"
        assert "承接批次：agentflows@fix-batch" in text, "缺承接标注"

    def t_slug_collision(base: Path) -> None:
        issues = base / "issues"
        report = base / "collide.yaml"
        report.write_text(
            "findings:\n"
            "  - severity: P1\n    issue: record_findings.py 的第一处缺陷\n  - severity: P1\n"
            "    issue: record_findings.py 的第二处缺陷\n", encoding="utf-8")
        rc = main_with(["--findings", str(report), "--issues-dir", str(issues),
                        "--project", "p", "--all"])
        assert rc == 0, f"exit {rc}"
        created = sorted(p.name for p in issues.glob("ISS-*.md"))
        assert len(created) == 2 and len(set(created)) == 2, f"同名冲突未去重：{created}"
        assert any(name.endswith("-2.md") for name in created), f"第二个应加 -2 序号：{created}"

    def t_invalid_input(base: Path) -> None:
        report = base / "bad.yaml"
        report.write_text("findings:\n  - location: a.md:1\n    issue: 缺 severity\n", encoding="utf-8")
        rc = main_with(["--findings", str(report), "--issues-dir", str(base / "issues"), "--project", "p"])
        assert rc == 2, f"非法输入应退出 2，实际 {rc}"
        no_block = base / "noblock.yaml"
        no_block.write_text("decision: approved\n", encoding="utf-8")
        rc2 = main_with(["--findings", str(no_block), "--issues-dir", str(base / "issues"), "--project", "p"])
        assert rc2 == 2, f"无 findings 块应退出 2，实际 {rc2}"
        rc3 = main_with(["--findings", str(base / "ghost.yaml"),
                         "--issues-dir", str(base / "issues"), "--project", "p"])
        assert rc3 == 2, f"文件不存在应退出 2，实际 {rc3}"
        colon = base / "colon.yaml"
        colon.write_text("findings:\n  - severity: P1\n    issue: 违反 FE-02: 防连点只用了 disabled\n",
                         encoding="utf-8")
        rc4 = main_with(["--findings", str(colon), "--issues-dir", str(base / "issues2"),
                         "--project", "p", "--all"])
        assert rc4 == 0, f"exit {rc4}"
        created = list((base / "issues2").glob("ISS-*.md"))
        assert created and "title: 违反 FE-02：防连点" in created[0].read_text(encoding="utf-8"), "title 冒号未替换"

    def t_archive_and_below_threshold(base: Path) -> None:
        issues = base / "issues"
        report = base / "report.yaml"
        record = base / "review.md"
        report.write_text(SAMPLE, encoding="utf-8")
        record.write_text("# 评审记录\n", encoding="utf-8")
        rc = main_with(["--findings", str(report), "--issues-dir", str(issues),
                        "--project", "p", "--min-severity", "P0", "--archive-yaml-to", str(record),
                        "--review-id", "review-y", "--round", "2"])
        assert rc == 1, f"低于下限应退出 1，实际 {rc}"
        text = record.read_text(encoding="utf-8")
        assert "reviewer 原始返回（归档）" in text, "归档失败"
        assert "第 2 轮" in text, "归档缺轮次"

    def main_with(argv: list[str]) -> int:
        import contextlib
        import io
        sys.argv = ["record_findings.py"] + argv
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            try:
                return main()
            except SystemExit as exc:  # argparse 错误
                return int(exc.code or 0)

    for name, fn in [
        ("findings 解析（多行值/引用片段不覆盖/顶格报错）", t_parse),
        ("端到端：hub 形态台账 + 模板自检", t_end_to_end),
        ("--all、dry-run 与 claimed-by", t_all_dry_run_and_claimed),
        ("同批次 slug 冲突加序号", t_slug_collision),
        ("非法输入/缺文件/title 冒号", t_invalid_input),
        ("低于下限退出 1 + YAML 归档", t_archive_and_below_threshold),
    ]:
        case(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
