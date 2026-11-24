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

  --findings      reviewer JSON 对象或 YAML 报告中的 findings 缩进序列；`-` 读 stdin。
                  YAML 支持标量、引号与 |/> 多行；嵌套对象、锚点等请改用 JSON。
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
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

if sys.version_info < (3, 10):
    raise SystemExit("record_findings.py 需要 Python 3.10 或以上版本，请检查 python3 --version")

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
_FINDING_KEYS = {"id", "severity", "issue", "location", "cause", "evidence", "cost", "fix"}
_ENTRY_RE = re.compile(r"^( *)- +(\w+):(?: +|$)(.*)$")
_KEY_RE = re.compile(r"^( *)(\w+):(?: +|$)(.*)$")
_FINDINGS_HEADER = re.compile(r"^findings:\s*(\[\s*\])?\s*(?:#.*)?$")
_SINGLE_QUOTED = re.compile(r"^'((?:[^']|'')*)'\s*(?:#.*)?$")
_BLOCK_START = re.compile(r"^([|>])([-+]?)(?: +#.*)?$")
LEDGER_HEADER = ("编号", "一句话", "记录链接", "归属")
# 台账占位行判据：模板示例行（hub/issues-README.md 的 `ISS-YYYY-MM-DD-<slug>`）或旧式占位文本
PLACEHOLDER_MARKS = ("ISS-YYYY-MM-DD-<slug>", "（当前无开放条目）")

OWNERSHIP = {
    "代码": "目标仓",
    "规范": "agentflow 方法侧",
    "模板": "agentflow 方法侧",
    "流程": "agentflow 方法侧",
}


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"重复键：{key}")
        result[key] = value
    return result


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _block_scalar(marker: re.Match[str], lines: list[str]) -> str:
    indentation = min((_indent(line) for line in lines if line.strip()), default=0)
    content = [line[indentation:] if line.strip() else "" for line in lines]
    if marker[1] == ">":
        # Fold adjacent ordinary lines; retain paragraph gaps and indented text.
        parts = []
        last = max((index for index, line in enumerate(content) if line), default=-1)
        for index, line in enumerate(content):
            next_line = content[index + 1] if index + 1 < len(content) else ""
            if line and not line.startswith(" ") and next_line and not next_line.startswith(" "):
                separator = " "
            elif line and not line.startswith(" ") and not next_line and index < last:
                separator = ""
            else:
                separator = "\n"
            parts.append(line + separator)
        value = "".join(parts)
    else:
        value = "".join(line + "\n" for line in content)
    if not value or marker[2] == "+":
        return value
    return value.rstrip("\n") + ("\n" if marker[2] != "-" else "")


def _read_scalar(raw: str, continuation: list[str]) -> str:
    raw = raw.strip()
    if marker := _BLOCK_START.fullmatch(raw):
        return _block_scalar(marker, continuation)
    extra = " ".join(line.strip() for line in continuation if line.strip())
    if raw.startswith("'"):
        match = _SINGLE_QUOTED.fullmatch(raw)
        if not match or extra:
            raise ValueError("不支持该单引号标量，请改用 YAML 多行标量或 JSON 字符串")
        return match[1].replace("''", "'")
    if raw.startswith('"'):
        value, end = json.JSONDecoder().raw_decode(raw)
        trailing = raw[end:].strip()
        if extra or (trailing and not trailing.startswith("#")):
            raise ValueError("双引号标量后存在多余输入，请改用 JSON 字符串")
        return value
    # Markdown inline code is a historical input. Keep it as literal text.
    if raw.startswith(("[", "{", "&", "*", "!", ">", "|")) or raw.startswith(("- ", "? ")):
        raise ValueError("findings 仅接受文本标量；复杂 YAML 请改用 JSON 对象和字符串")
    value = re.split(r"\s+#", raw, maxsplit=1)[0].rstrip()
    if value.startswith("#"):
        value = ""
    return " ".join(part for part in (value, extra) if part)


def _parse_yaml_findings(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    headers = [(index, match) for index, line in enumerate(lines)
               if (match := _FINDINGS_HEADER.fullmatch(line))]
    if len(headers) != 1:
        raise ValueError("要求唯一的 `findings:` 缩进列表或 `findings: []`")
    start, header = headers[0]
    findings: list[dict[str, str]] = []
    item_indent = field_indent = None
    index = start + 1
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indentation = _indent(line)
        if not indentation:
            if line.startswith("- "):
                raise ValueError("findings 列表项须缩进，不能顶格")
            break
        if header[1]:
            raise ValueError("findings: [] 后不可追加缩进列表")
        entry = _ENTRY_RE.fullmatch(line)
        if entry and (item_indent is None or indentation == item_indent):
            item_indent = indentation
            field_indent = entry.start(2)
            findings.append({})
            _, key, raw = entry.groups()
        else:
            field = _KEY_RE.fullmatch(line)
            if not findings or not field or indentation != field_indent:
                raise ValueError(f"findings 第 {index} 行不是有效的缩进行：{line}")
            _, key, raw = field.groups()
        item = findings[-1]
        if key not in _FINDING_KEYS or key in item:
            raise ValueError(f"findings 未知或重复字段：{key}")
        continuation = []
        is_block = bool(_BLOCK_START.fullmatch(raw.strip()))
        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip():
                if is_block:
                    continuation.append(candidate)
            elif _indent(candidate) < field_indent or (
                _indent(candidate) == field_indent and (is_block or _KEY_RE.match(candidate))
            ):
                break
            elif is_block or not candidate.lstrip().startswith("#"):
                continuation.append(candidate)
            index += 1
        item[key] = _read_scalar(raw, continuation)
    if not header[1] and not findings:
        raise ValueError("findings 块为空。无发现时请写 findings: []")
    return findings


def parse_findings(text: str) -> list[dict[str, str]]:
    if text.lstrip().startswith("{"):
        report = json.loads(text, object_pairs_hook=_unique_object)
        findings = report.get("findings")
    else:
        findings = _parse_yaml_findings(text)
    if not isinstance(findings, list):
        raise ValueError("findings 必须是列表")
    identities: set[str] = set()
    for i, finding in enumerate(findings, 1):
        if not isinstance(finding, dict) or finding.keys() - _FINDING_KEYS or any(
            not isinstance(value, str) for value in finding.values()
        ):
            raise ValueError(f"第 {i} 条 finding 必须由规定的文本字段组成")
        if finding.get("severity") not in SEVERITY_ORDER:
            raise ValueError(f"第 {i} 条 finding severity 非法：{finding.get('severity')!r}")
        if not finding.get("issue", "").strip():
            raise ValueError(f"第 {i} 条 finding 缺 issue 描述")
        if "id" in finding:
            identifier = finding["id"]
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", identifier) or identifier in identities:
                raise ValueError(f"第 {i} 条 finding id 无效或重复：{identifier!r}")
            identities.add(identifier)
    return findings


def slugify(issue: str) -> str:
    cleaned = "".join(char for char in issue if char.isalnum() or char in "_-")
    return cleaned[:12].strip("_-") or "finding"


def yaml_string(value: str) -> str:
    # JSON strings are valid YAML strings. Keep simple established spellings
    # readable while quoting values that YAML could interpret as other types.
    if (re.fullmatch(r"[\w./-]+", value) and value[0].isalpha()
            and value.lower() not in {"y", "n", "yes", "no", "on", "off", "true", "false", "null"}):
        return value
    return json.dumps(value, ensure_ascii=False)


def content_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def render_iss(finding: dict[str, str], *, bug_id: str, now: str, local_stamp: str,
               project: str, review_id: str | None, round_no: int | None,
               claimed_by: str | None, attribution: str, defect_class: str,
               escape_stage: str, error_kind: str, agentflow_version: str | None,
               source_key: str | None = None, source_digest: str | None = None) -> str:
    severity = finding["severity"]
    location = finding.get("location", "（未给位置）")
    issue = finding["issue"]
    evidence = finding.get("evidence", "（未附证据）")
    cause = finding.get("cause", "").strip()
    cost = finding.get("cost", "（未写代价）")
    fix = finding.get("fix", "（未给修法）")
    title = yaml_string(issue.strip())
    source = f"（来源：{review_id}" + (f" 第 {round_no} 轮）" if round_no else "）") if review_id else ""
    disposition_line = "" if claimed_by else "disposition: deferred"
    claimed_note = f"承接批次：{claimed_by}（承接后同轮修复）。" if claimed_by else "承接批次未定（disposition: deferred）。"
    version_line = f"agentflow_version: {yaml_string(agentflow_version)}\n" if agentflow_version else ""
    source_meta = (
        f"source_finding_key: sha256:{source_key}\nsource_finding_digest: sha256:{source_digest}\n"
        if source_key and source_digest else ""
    )
    cause_line = f"评审提供的原因：{cause}\n\n" if cause else ""
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
project: {yaml_string(project)}
files:
  - {yaml_string(location)}
recorded_at: {now}
{version_line}{source_meta}updated_at: {now}
---

## 现象

{issue}（严重度 {severity}）{source}
位置：{location}
观察证据：{evidence}
影响面/代价：{cost}

## 根因

{cause_line}待补——根因与归因依据由修复批次（或 bug-investigator）核对，引用覆盖它的条款（`path:line`）或写明无条款覆盖。
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


def _cells(line: str) -> tuple[str, ...]:
    text = line.strip()
    if not text.startswith("|") or not text.endswith("|"):
        return ()
    return tuple(cell.strip() for cell in re.split(r"(?<!\\)\|", text[1:-1]))


def ledger_headers(lines: list[str]) -> list[int]:
    headers = []
    fence = ""
    for index, line in enumerate(lines):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            if marker and marker[1].startswith(fence) and not marker[2].strip():
                fence = ""
        elif marker:
            fence = marker[1]
        elif _cells(line) == LEDGER_HEADER:
            headers.append(index)
    return headers


def plan_ledger(readme: Path, rows: dict[str, str]) -> tuple[bytes, bytes] | None:
    """Locate the registered issue table; leave every other table byte-for-byte."""
    if readme.is_symlink():
        raise ValueError(f"台账不得是符号链接：{readme}")
    if not readme.is_file():
        return None
    original = readme.read_bytes()
    lines = original.decode("utf-8").splitlines(keepends=True)
    headers = ledger_headers(lines)
    if not headers:
        return None
    if len(headers) != 1:
        raise ValueError(f"台账有多个相同表头，无法定位：{readme}")
    header = headers[0]
    separator = _cells(lines[header + 1]) if header + 1 < len(lines) else ()
    if len(separator) != len(LEDGER_HEADER) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
        raise ValueError(f"台账表头没有有效分隔行：{readme}")
    start = header + 2
    end = start
    while end < len(lines) and (_cells(lines[end]) or any(mark in lines[end] for mark in PLACEHOLDER_MARKS)):
        end += 1
    kept = [line for line in lines[start:end] if not any(mark in line for mark in PLACEHOLDER_MARKS)]
    registered = {cells[0] for line in kept if (cells := _cells(line))}
    pending = [row for identifier, row in rows.items() if identifier not in registered]
    if not pending and kept == lines[start:end]:
        return original, original
    newline = "\r\n" if lines[header].endswith("\r\n") else "\n"
    before = "".join(lines[:start] + kept)
    if not before.endswith("\n"):
        before += newline
    desired = before + "".join(row + newline for row in pending) + "".join(lines[end:])
    return original, desired.encode("utf-8")


def write_atomically(path: Path, data: bytes, expected: bytes | None = None) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".agentflow-findings-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if expected is None:
            os.link(temporary, path)
        else:
            if path.is_symlink() or path.read_bytes() != expected:
                raise ValueError(f"写入前文件已变化，请基于新内容重跑：{path}")
            os.chmod(temporary, path.stat().st_mode & 0o777)
            os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked_issues(issues_dir: Path):
    if issues_dir.is_symlink():
        raise ValueError(f"issues 目录不得是符号链接：{issues_dir}")
    issues_dir.mkdir(parents=True, exist_ok=True)
    lock = issues_dir / ".agentflow-record-findings.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError(f"缺陷登记正被占用；如已确认上次异常中止，可移除空锁目录后重跑：{lock}") from exc
    try:
        yield
    finally:
        lock.rmdir()


def archive_yaml(review_record: Path, yaml_text: str, round_no: int | None, review_id: str | None) -> None:
    head = f"## 第 {round_no} 轮 reviewer 原始返回（归档）" if round_no else "## reviewer 原始返回（归档）"
    if review_id:
        head += f" — {review_id}"
    digest = content_hash([review_id, round_no, yaml_text])
    marker = f"<!-- agentflow:findings-archive sha256:{digest} -->"
    current = review_record.read_bytes()
    if marker.encode() in current:
        return
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", yaml_text)), default=0))
    extension = "" if yaml_text.endswith("\n") else "\n"
    addition = f"\n{head}\n\n{marker}\n\n{fence}yaml\n{yaml_text}{extension}{fence}\n"
    write_atomically(review_record, current + addition.encode("utf-8"), current)


def do_archive(archive_to: str, yaml_text: str, round_no: int | None, review_id: str | None) -> None:
    """把 reviewer 原始 YAML 追加进评审记录；目标不存在时告警不中断。"""
    record = Path(archive_to)
    if record.is_file():
        archive_yaml(record, yaml_text, round_no, review_id)
        print(f"[ok] reviewer 原始 YAML 已归档 -> {record}")
    else:
        print(f"[警告] --archive-yaml-to 文件不存在，未归档：{record}", file=sys.stderr)


def frontmatter_text(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return ""
    return "\n".join(lines[1:lines.index("---", 1)])


def check_record(text: str, bug_id: str) -> list[str]:
    """模板合法性自检：bug_id 与文件名、recorded_at 日期一致，必填节与 frontmatter 关键字段。"""
    problems: list[str] = []
    frontmatter = frontmatter_text(text)
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


def recorded_findings(issues_dir: Path) -> dict[str, tuple[str, str]]:
    records = {}
    for path in sorted(issues_dir.glob("ISS-*.md")):
        if path.is_symlink() or not path.is_file():
            continue
        frontmatter = frontmatter_text(path.read_text(encoding="utf-8"))
        key = re.search(r"^source_finding_key: sha256:([0-9a-f]{64})$", frontmatter, re.MULTILINE)
        if not key:
            continue
        digest = re.search(r"^source_finding_digest: sha256:([0-9a-f]{64})$", frontmatter, re.MULTILINE)
        if not digest or key[1] in records:
            raise ValueError(f"缺陷来源身份缺摘要或重复：{path}")
        records[key[1]] = (path.stem, digest[1])
    return records


def plan_findings(args, findings: list[dict[str, str]], selected: list[dict[str, str]]) -> int:
    issues_dir = Path(args.issues_dir)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    local_stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    ownership = OWNERSHIP[args.defect_class]
    recorded = recorded_findings(issues_dir)
    mapping = []
    rows: dict[str, str] = {}
    planned: list[tuple[Path, bytes]] = []
    used = set()

    for i, finding in enumerate(selected, 1):
        digest = content_hash(finding)
        identity = finding.get("id") or content_hash([finding["severity"], finding["issue"], finding.get("location")])
        key = content_hash([args.project, args.review_id, args.round, identity]) if args.review_id else None
        prior = recorded.get(key) if key else None
        if prior:
            bug_id, prior_digest = prior
            if prior_digest != digest:
                raise ValueError(f"评审、轮次与 finding ID 对应已有立案，但发现内容变化：{bug_id}；请另开评审轮次")
        else:
            stem = f"ISS-{now[:10]}-{slugify(finding['issue'])}"
            bug_id = stem
            target = issues_dir / f"{bug_id}.md"
            suffix = 1
            while target.exists() or target.is_symlink() or bug_id in used:
                suffix += 1
                bug_id = f"{stem}-{suffix}"
                target = issues_dir / f"{bug_id}.md"
            content = render_iss(
                finding, bug_id=bug_id, now=now, local_stamp=local_stamp, project=args.project,
                review_id=args.review_id, round_no=args.round, claimed_by=args.claimed_by,
                attribution=args.attribution, defect_class=args.defect_class, escape_stage=args.escape_stage,
                error_kind=args.error_kind, agentflow_version=args.agentflow_version,
                source_key=key, source_digest=digest,
            )
            problems = check_record(content, bug_id)
            if problems:
                raise ValueError(f"{target.name} 模板自检未过：{'；'.join(problems)}")
            planned.append((target, content.encode("utf-8")))
            if key:
                recorded[key] = (bug_id, digest)
        used.add(bug_id)
        label = finding.get("id") or f"findings[{i}]"
        issue = " ".join(finding["issue"].split())
        mapping.append(f"  {label}（{finding['severity']}，{issue[:24]}…） -> {bug_id}" + ("（复用）" if prior else ""))
        cell = issue[:40].replace("|", "／")
        filename = f"{bug_id}.md"
        rows[bug_id] = f"| {bug_id} | {cell} | [{filename}]({quote(filename)}) | {ownership} |"

    readme = issues_dir / "README.md"
    ledger = plan_ledger(readme, rows)
    print(f"立案计划：{len(selected)}/{len(findings)} 条（下限 {args.min_severity}"
          + ("，--all" if args.all else "") + "）")
    for line in mapping:
        print(line)
    if args.dry_run:
        print("dry-run：未写任何文件。")
        return 0
    for target, content in planned:
        write_atomically(target, content)
    if ledger and ledger[0] != ledger[1]:
        write_atomically(readme, ledger[1], ledger[0])
    print(f"[ok] 新立案 {len(planned)} 条，复用 {len(rows) - len(planned)} 条 -> {issues_dir.resolve()}"
          + ("；台账已核对" if ledger else "；未找到台账表（跳过台账行）"))
    print("收口提醒：defect_class 非「代码」的记录 verified 后须按 issue-tracking §3 反哺 agentflow；"
          "映射表请回填评审记录 findings 表。")
    return 0


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
    if not args.findings or not args.issues_dir or not args.project or not args.project.strip():
        ap.error("需要 --findings、--issues-dir 与 --project（或 --self-test）")
    if args.review_id is not None and not args.review_id.strip():
        ap.error("--review-id 不能为空")
    if args.round is not None and args.round < 1:
        ap.error("--round 必须是正整数")

    if args.findings == "-":
        yaml_text = sys.stdin.read()
    else:
        try:
            yaml_text = Path(args.findings).read_bytes().decode("utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"[错误] --findings 不可读：{exc}", file=sys.stderr)
            return 2
    try:
        findings = parse_findings(yaml_text)
    except ValueError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 2

    threshold = SEVERITY_ORDER[args.min_severity]
    selected = findings if args.all else [f for f in findings if SEVERITY_ORDER[f["severity"]] <= threshold]

    try:
        if not selected:
            if args.archive_yaml_to and not args.dry_run:
                do_archive(args.archive_yaml_to, yaml_text, args.round, args.review_id)
            print(f"[ok] findings 共 {len(findings)} 条，符合立案下限 {args.min_severity} 的 0 条——不立案（非错误）")
            return 1
        if args.dry_run:
            return plan_findings(args, findings, selected)
        with locked_issues(Path(args.issues_dir)):
            result = plan_findings(args, findings, selected)
            if args.archive_yaml_to:
                do_archive(args.archive_yaml_to, yaml_text, args.round, args.review_id)
            return result
    except (OSError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 2


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
        "# issues — 缺陷与事项流\n\n## 开放条目\n\n| " + " | ".join(LEDGER_HEADER) + " |\n"
        + "| --- | --- | --- | --- |\n"
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
        assert created and 'title: "违反 FE-02: 防连点只用了 disabled"' in created[0].read_text(encoding="utf-8")

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

    def t_standard_findings_repeat(base: Path) -> None:
        report = base / "review.yaml"
        report.write_text("findings:\n"
                          "  - id: F01\n"
                          "    severity: 'P1'\n"
                          "    issue: |\n"
                          "      # Login: blocked\n"
                          "      A second line\n"
                          "    location: 'ui.md:7'\n"
                          "    cause: >\n"
                          "      The cause spans\n"
                          "      multiple lines.\n", encoding="utf-8")
        findings = parse_findings(report.read_text())
        assert findings[0]["issue"] == "# Login: blocked\nA second line\n"
        assert findings[0]["cause"] == "The cause spans multiple lines.\n"
        assert parse_findings(json.dumps({"findings": findings})) == findings
        issues = base / "issues"
        issues.mkdir()
        prefix = ("~~~md\r\n| 编号 | 一句话 | 记录链接 | 归属 |\r\n~~~\r\n\r\n"
                  "| Other | Example | Text | Extra |\r\n| --- | --- | --- | --- |\r\n| X | X | X | X |\r\n\r\n")
        ledger = issues / "README.md"
        ledger.write_bytes((prefix + HUB_README.replace("\n", "\r\n")).encode())
        archive = base / "review.md"
        archive.write_text("# Review\n")
        argv = ["--findings", str(report), "--issues-dir", str(issues), "--project", "example",
                "--review-id", "REV-1", "--round", "1", "--archive-yaml-to", str(archive)]
        assert main_with(argv) == 0
        issue, = issues.glob("ISS-*.md")
        content = issue.read_text()
        assert 'title: "# Login: blocked\\nA second line"' in content
        assert "The cause spans multiple lines." in content
        registered = ledger.read_bytes()
        archived = archive.read_bytes()
        assert registered.startswith(prefix.encode())
        assert registered.index(issue.stem.encode()) > registered.rindex("编号".encode())
        assert main_with(argv) == 0
        assert list(issues.glob("ISS-*.md")) == [issue]
        assert ledger.read_bytes() == registered and archive.read_bytes() == archived
        report.write_text(report.read_text().replace("multiple lines.", "changed lines."))
        assert main_with(argv) == 2
        assert issue.read_text() == content and ledger.read_bytes() == registered and archive.read_bytes() == archived

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
        ("含引号、多行、# 和冒号的报告；台账定位与同轮幂等", t_standard_findings_repeat),
    ]:
        case(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
