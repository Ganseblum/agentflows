"""Doc-chain linter checks: parsing helpers, per-C findings, and the feature-dir pass."""

from __future__ import annotations

import datetime as _dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .constants import *


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def fenced_lines(text: str) -> set[int]:
    """Line numbers inside or on a ``` fence (the toggle lines themselves included)."""
    inside, out = False, set()
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            inside = not inside
            out.add(i)
        elif inside:
            out.add(i)
    return out


def strip_inline_code(line: str) -> str:
    """Drop `...` spans (even segments after a backtick split); unbalanced tail reads as code."""
    return "".join(line.split("`")[0::2])


def inside_parens(s: str, idx: int) -> bool:
    """True when s[idx] sits inside a （…）/ (…) span of its own line (depth counting, no nesting)."""
    depth = 0
    for ch in s[:idx]:
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            depth = max(0, depth - 1)
    return depth > 0


def c13_checked(label: str) -> bool:
    """False only for the files listed in C13_EXEMPT_FILES, matched on the path's tail.

    Tail matching lets --file (the path as given, possibly absolute) and the feature-chain pass
    (labels relative to the feature dir) resolve the same listing.
    """
    posix = label.replace("\\", "/")
    return not any(posix == name or posix.endswith("/" + name) for name in C13_EXEMPT_FILES)


def text_form_findings(label: str, text: str, resolve_roots: list[Path]) -> list[str]:
    """C12/C13/C14 — the text-form checks that need no feature-directory shape.

    Shared by the feature-chain pass (label = repo-relative path; link targets resolve against
    the document's directory and the feature root) and --file mode (label = the path as given;
    targets resolve against the file's own directory).
    """
    errors: list[str] = []
    fences = fenced_lines(text)
    check_c13 = c13_checked(label)
    for i, line in enumerate(text.splitlines(), 1):
        # C12 stale-time reference: the line claims a target is still pending while the
        # markdown link OR backtick code path on the same line already resolves on disk —
        # delete the claim or re-point it. Both pointee forms share one resolution pass,
        # deduped per line.
        if any(w in line for w in STALE_WORDS):
            seen: set[str] = set()
            for target in MD_LINK_RE.findall(line) + BT_PATH_RE.findall(line):
                t = target.split("#", 1)[0].split("?", 1)[0].strip()
                if not t or t in seen or t.startswith(("/", "http:", "https:", "mailto:")):
                    continue
                seen.add(t)
                if any((root / t).is_file() for root in resolve_roots):
                    errors.append(
                        f"C12 时效性引用: {label}:{i} 声称待产出但目标已存在: {t}"
                    )
        # C13 session role words: replace with the concrete role name, or delete the clause so
        # the body stands on its own. Skipped whole on the method-self-description surfaces —
        # there the words are defined terms or quoted examples (reviewer.md lists 「supervisor、
        # TD、本轮、本次会话一类」 as the very thing the clause forbids), and no line-local rule
        # can tell a mention from a use.
        if check_c13:
            role_line = line
            for phrase in ROLE_WORD_EXEMPT_PHRASES:
                role_line = re.sub(re.escape(phrase), " ", role_line, flags=re.IGNORECASE)
            hits = [w for w in ROLE_PHRASES if w in line] + ROLE_WORD_RE.findall(role_line)
            for w in sorted(set(hits)):
                errors.append(f"C13 会话角色词: {label}:{i} {w}")
        # C14 bare code subjects: codes pair with the plain word in prose; the definition
        # site, code spans/fences, and the two paired forms are exempt (see CODE_SUBJECT_RE).
        if i not in fences and not line.lstrip().startswith("|"):
            prose = strip_inline_code(line)
            for m in CODE_SUBJECT_RE.finditer(prose):
                glossed = prose[m.end():].lstrip(" \u3000").startswith(("（", "("))
                if glossed or inside_parens(prose, m.start()):
                    continue
                errors.append(f"C14 代号裸用: {label}:{i} {m.group(0)}")
    return errors


def mermaid_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    lines = text.splitlines()
    inside = False
    buf: list[str] = []
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


# A prototype HTML file must carry at least this many bytes to exempt the C7 wireframe floor.
# A name is not a prototype; a placeholder file must not be able to buy an exemption.
PROTOTYPE_MIN_BYTES = 64


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Pipe tables as (header cells, body rows): a pipe line followed by a separator line."""
    lines = text.splitlines()
    out: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and "-" in lines[i + 1] and SEP_RE.match(lines[i + 1]):
            header = split_row(lines[i])
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            out.append((header, rows))
            i = j
        else:
            i += 1
    return out


def stage_landing(readme_text: str) -> dict[str, str]:
    """Batch README 段落映射: stage -> 落点 cell, read from any table with a 落点 column."""
    out: dict[str, str] = {}
    for header, rows in md_tables(readme_text):
        if "落点" not in header:
            continue
        col = header.index("落点")
        for row in rows:
            if not row:
                continue
            stage = row[0].strip("`* ").lower()
            if stage in STAGE_DIRS and col < len(row):
                out[stage] = row[col].strip()
    return out


def path_candidates(cell: str) -> set[str]:
    """Repository-path tokens in a cell: path-like code spans plus bare paths with a known suffix."""
    found: set[str] = set()
    for span in re.findall(r"`([^`\n]+)`", cell):
        s = span.strip()
        if re.fullmatch(r"[\w.\-]+(?:/[\w.\-]+)*/?", s) and ("/" in s or re.search(r"\.[A-Za-z]{1,5}$", s)):
            found.add(s)
    found.update(BARE_PATH_RE.findall(cell))
    return found


def body_text(text: str) -> str:
    """The text with fenced code blocks removed: an id inside a code sample is not prose."""
    fences = fenced_lines(text)
    return "\n".join(line for i, line in enumerate(text.splitlines(), 1) if i not in fences)


def _declared_base(value: str, repo_root: Path, feature_dir: Path) -> Path | None:
    """Resolve a README 落点基准 value to a directory, or None when undeclared/placeholder."""
    v = value.split("｜")[0].split("|")[0].strip()
    # 元信息常把多个字段写在同一行（`- UI 轨：未启用；落点基准：.（默认）；最后更新时间：…`）；
    # 捕获到行尾会把后半句当成目录名，把合法声明判成假红，所以先按分号截断。
    v = v.split("；")[0].split(";")[0].strip()
    if not v or v.startswith("<"):
        return None  # unfilled template placeholder is not a declaration
    v = re.sub(r"[（(][^）)]*[）)]\s*$", "", v).strip().rstrip("/")
    if v in ("本批次目录",):
        return feature_dir
    if v in (".", "主实施仓根", "仓根", "目标仓根"):
        return repo_root
    return repo_root / v


def location_base(readme_text: str, repo_root: Path, feature_dir: Path) -> tuple[Path, list[str]]:
    """C9 落点基准: the directory code-location paths resolve against, plus declaration errors."""
    errors: list[str] = []
    base = repo_root
    m = LOCATION_BASE_RE.search(readme_text)
    if m:
        declared = _declared_base(m.group(1), repo_root, feature_dir)
        if declared is not None and not declared.is_dir():
            errors.append(f"C9 落点基准: README 声明的落点基准 {m.group(1).strip()} "
                          f"在目标仓根下不存在（路径按声明的基准解析，基准目录必须真实在盘）")
        elif declared is not None:
            base = declared
    return base, errors


def plan_findings(label: str, text: str, repo_root: Path, loc_base: Path | None = None) -> list[str]:
    """C9 task-row grounding for one plan file: ID shape, status enum, code location."""
    errors: list[str] = []
    base = loc_base if loc_base is not None else repo_root

    def at(row: list[str], i: int) -> str:
        return row[i] if i < len(row) else ""

    for header, rows in md_tables(text):
        if not header or header[0] != "ID":
            continue
        if "代码落点" not in header or "状态" not in header:
            errors.append(f"C9 plan: {label} 任务表缺少「代码落点」或「状态」列")
            continue
        loc_i, status_i = header.index("代码落点"), header.index("状态")
        for row in rows:
            task_id = at(row, 0).strip("`* ")
            if not TASK_ID_RE.match(task_id):
                errors.append(
                    f"C9 plan 任务表: {label} ID 列非法「{task_id}」（须为 T/FT 编号，「待核实」不得占 ID 列）"
                )
                continue
            status = at(row, status_i)
            if not (any(status.startswith(s) for s in TASK_STATUS_ENUM) or status in TASK_STATUS_BARE):
                errors.append(f"C9 plan 状态: {label} {task_id} 状态「{status}」不在固定枚举内")
            if status.startswith("— 本期不做") or status == "—":
                continue
            loc = at(row, loc_i)
            if PLACEHOLDER in loc:
                continue
            cands = path_candidates(loc)
            if not cands:
                errors.append(f"C9 plan 落点: {label} {task_id} 代码落点无仓库内路径且无「待核实」标记")
                continue
            for cand in sorted(cands):
                if not (base / cand.rstrip("/")).exists():
                    errors.append(f"C9 plan 落点: {label} {task_id} 代码落点路径不存在: {cand}")
    return errors


def find_stage(files: list[Path], *parts: str | Path) -> list[Path]:
    """All non-gitkeep .md files under <feature>/<parts...> (recursively)."""
    base = Path(*parts)
    return [
        f
        for f in files
        if f.parent == base or base in f.parents
        if f.suffix == ".md" and f.name != ".gitkeep"
    ]


def lint(feature_dir: Path, repo_root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    if not feature_dir.is_dir():
        return [f"{feature_dir}: 目录不存在"]

    files = sorted(feature_dir.rglob("*"))
    md_files = [f for f in files if f.is_file() and f.suffix == ".md" and f.name != ".gitkeep"]
    readme = feature_dir / "README.md"
    history = feature_dir / "HISTORY.md"
    all_text = {f: read(f) for f in md_files}

    # C24 single-ledger mode (2026-10-23 gate change, user-authorized): when README.md is absent
    # but HISTORY.md is present, HISTORY.md is the chain's single ledger — it carries the entry
    # gates and (when C22 is in scope) the 目标承接 mark/table. README-path rules do not apply.
    # This is additive: README present ⇒ README mode (unchanged); both present ⇒ README wins and
    # HISTORY.md is treated as an ordinary stage document (its markers are simply not consulted).
    single_ledger = (not readme.is_file()) and history.is_file()
    leader_text = all_text.get(readme, "") if readme.is_file() else (
        all_text.get(history, "") if single_ledger else ""
    )

    # C1 structure — three exemptions the chain contract allows, all declaration-gated:
    #   * 轻量模式：无 spec/design 轨 in the README meta line narrows the stage set to
    #     proposal + plan. Until 2026-10-13 C1 demanded all four stage directories
    #     unconditionally, so every such batch failed the very linter the contract told it to
    #     run before declaring the chain done: the降级 path existed on paper only. The exemption
    #     is declaration-gated (the README must say so), never inferred from emptiness — and it
    #     narrows the stage requirement, it does not switch C1 off.
    #   * a stage directory may be empty when the README's 段落映射 table names a landing for it
    #     (non-empty and not 「—」); otherwise it must hold a real document.
    #   * C24 single-ledger mode: README absent, HISTORY present — the whole chain is led by
    #     HISTORY.md, so C1 does not require README.md as the entry file.
    readme_text = all_text.get(readme, "")
    lightweight = bool(re.search(r"轻量模式[：:][^\n]*无\s*spec/design\s*轨", readme_text))
    required_stages = ("proposal", "plan") if lightweight else STAGE_DIRS
    landing = stage_landing(readme_text) if readme.is_file() else {}
    for stage in required_stages:
        stage_files = [f for f in md_files if stage in f.relative_to(feature_dir).parts]
        if stage_files:
            continue
        if landing.get(stage, "") not in ("", "—"):
            continue  # 段落映射豁免
        suffix = "（已声明轻量模式）" if lightweight else "，且 README 段落映射未写明落点"
        errors.append(f"C1 结构: {stage}/ 下没有任何有效文档（仅 .gitkeep 占位）{suffix}")
    if not readme.is_file() and not single_ledger:
        errors.append("C1 结构: 缺少 README.md 唯一入口（HISTORY.md 单账本模式需存在 HISTORY.md）")

    # C2 entry gates — read from the leader file (README, or HISTORY.md in single-ledger mode).
    if readme.is_file() or single_ledger:
        rtext = leader_text
        for gate in ("需求评审", "技术方案评审"):
            if gate not in rtext:
                src = "HISTORY.md" if single_ledger else "README.md"
                errors.append(f"C2 入口门禁: {src} 未声明「{gate}」门禁条目")

    # C3 spec re-audit + blocking closed
    spec_files = find_stage(md_files, feature_dir / "spec")
    audit_found = False
    for f in spec_files:
        text = all_text[f]
        if ("不合规项" in text) or ("反审" in text):
            audit_found = True
        for line in text.splitlines():
            if not (line.lstrip().startswith("|") and "阻塞" in line and "☐" in line):
                continue
            # The exemption is a status-cell claim, not a whole-line keyword. Until 2026-10-13
            # the check dropped any line containing 非阻塞 anywhere, so a row whose status cell
            # read 阻塞 but whose prose merely mentioned 非阻塞 was silently exempt — a false
            # negative the checker's own comment admitted and its self-test then pinned as
            # correct behaviour. Only a cell that starts with 非阻塞 exempts the row.
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if any(cell.startswith("非阻塞") for cell in cells):
                continue  # non-blocking rows may stay open pending review confirmation
            errors.append(f"C3 反审门: {f.relative_to(feature_dir)} 存在未关闭的阻塞项: {line.strip()[:80]}")
    if spec_files and not audit_found:
        errors.append("C3 反审门: spec/ 下没有任何文件包含「不合规项/反审」checklist")

    # C4/C5/C6/C7/C8 per-side design requirements
    be_files = find_stage(md_files, feature_dir / "design" / "be")
    fe_files = find_stage(md_files, feature_dir / "design" / "fe")
    # C4/C5/C8 apply to a role when spec/<role>/ or design/<role>/ holds any document. An empty
    # design/<role>/ therefore no longer skips the role's checks when the spec side has content.
    be_applies = bool(be_files or find_stage(md_files, feature_dir / "spec" / "be"))
    fe_applies = bool(fe_files or find_stage(md_files, feature_dir / "spec" / "fe"))
    be_text = "\n".join(all_text[f] for f in be_files) if be_files else ""
    fe_text = "\n".join(all_text[f] for f in fe_files) if fe_files else ""

    # Wireframe/prototype state is shared by C7 (fe track) and C21 (UI-track gate), so it is
    # computed once here regardless of whether the fe track applies.
    wireframes = [
        b
        for b in re.findall(r"```text\n(.*?)```", fe_text, re.DOTALL)
        if any(c in b for c in BOX_CHARS)
    ]
    has_prototype = any(
        x.is_file()
        and x.suffix == ".html"
        and "prototype" in str(x.relative_to(feature_dir)).lower()
        and x.stat().st_size >= PROTOTYPE_MIN_BYTES
        for x in files
    )

    if be_applies:
        kinds = mermaid_kinds(be_text)
        seq_with_alt = [b for b in kinds.get("sequenceDiagram", []) if re.search(r"^\s*alt\b", b, re.MULTILINE)]
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
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", be_text, re.MULTILINE):
            header = table.splitlines()[0]
            if "请求字段" in header and "响应字段" in header:
                for row in table.splitlines()[2:]:
                    first = row.strip("|").split("|")[0].strip()
                    m = re.match(r"^([A-Za-z]{1,3}\d{1,3})\b", first)
                    if m:
                        contract_ids.add(m.group(1).upper())
        fe_body = "\n".join(body_text(all_text[f]) for f in fe_files)
        fe_ids = set(re.findall(r"\b([A-Za-z]{1,3}\d{1,3})\b", fe_body))
        # accepted tolerance (review note a): \b fails on CJK-adjacent ids (e.g. `A1的`),
        # which over-reports C5 — the safe direction for a floor linter
        fe_ids = {i.upper() for i in fe_ids}
        missing = sorted(contract_ids - fe_ids)
        if contract_ids and missing:
            errors.append(f"C5 契约闭合: design/be 契约表声明的接口 {missing} 未在 design/fe 出现（缺异常矩阵行或调用）")
    if fe_applies:
        kinds = mermaid_kinds(fe_text)
        for kind in ("flowchart", "sequenceDiagram", "stateDiagram"):
            if kind not in kinds:
                errors.append(f"C8 design/fe: 缺少 {kind}")
        # A prototype exempts the wireframe floor only if it is a prototype: until 2026-10-13 any
        # zero-byte file named *prototype*.html satisfied it, because the check tested the path
        # name and never looked at the bytes.
        if len(wireframes) < 2 and not has_prototype:
            errors.append(f"C7 design/fe: 工程线框不足 2 张（现 {len(wireframes)}）且无 prototype HTML 原型")
        matrix = False
        for table in re.findall(r"((?:^\|[^\n]*\|[ \t]*\n){2,})", fe_text, re.MULTILINE):
            rows = table.splitlines()
            header = rows[0]
            if (
                ("成功" in header or "正常" in header)
                and ("失败" in header or "异常" in header)
                and any(SEP_RE.match(row.strip()) is None for row in rows[1:])
            ):
                matrix = True  # a data row below the header separator: the matrix has content
                break
        if not matrix:
            errors.append("C6 design/fe: 缺少接口异常边界矩阵（表头需同时覆盖 成功 与 失败/异常，且至少一行数据）")

    # C19 qa acceptance (2026-10-21 gate change, user-authorized): a spec that carries any
    # content but no qa acceptance document is a chain that cannot be accepted. C1 only catches
    # an EMPTY stage directory — it is silent when spec/ holds be/fe or unstructured docs while
    # spec/qa is empty, which is exactly the half-gap the cross-repo review corpus fell into
    # (one batch: spec holds one unstructured doc, qa empty). Exemption is declaration-gated
    # (README says 「qa 不适用」/「无 qa 轨」), never inferred.
    if not lightweight and spec_files:
        qa_files = find_stage(md_files, feature_dir / "spec" / "qa")
        if not qa_files and not (readme.is_file() and QA_EXEMPT_RE.search(readme_text)):
            errors.append(
                "C19 qa 验收: spec/ 有内容而 spec/qa/ 下没有任何验收文档"
                "（README 声明「qa 不适用」或「无 qa 轨」可豁免）"
            )

    # C20 埋点贯通 / C21 ui 轨 (2026-10-21 gate change, user-authorized): opt-in via the README
    # 元信息 rows the feature template ships. An unfilled placeholder (leading 「<」) is not a
    # declaration and never fires, so legacy chains without those rows are unaffected.
    if readme.is_file():
        m_track = TRACKING_RE.search(readme_text)
        if m_track and m_track.group(1).strip().startswith("本期新增"):
            spec_text_all = "\n".join(all_text[f] for f in spec_files) if spec_files else ""
            proposal_files = find_stage(md_files, feature_dir / "proposal")
            proposal_text = "\n".join(all_text[f] for f in proposal_files) if proposal_files else ""
            if not re.search(r"^#{2,6} .*埋点决策", proposal_text, re.MULTILINE):
                errors.append("C20 埋点贯通: proposal 缺「埋点决策」节（提案不问要不要埋，落地自然跳过）")
            if not re.search(r"^#{2,6} .*埋点", spec_text_all, re.MULTILINE):
                errors.append("C20 埋点贯通: spec 缺埋点验收草案节（spec/fe §4）")
            if not re.search(r"^#{2,6} .*埋点", fe_text, re.MULTILINE):
                errors.append("C20 埋点贯通: design/fe 缺埋点事件契约节（§1.7）")
        m_ui = UI_TRACK_RE.search(readme_text)
        if (
            m_ui
            and m_ui.group(1).strip().startswith("已启用")
            and len(wireframes) < 2
            and not has_prototype
        ):
            errors.append(
                "C21 ui 轨: README 声明 UI 轨已启用，但既无可直开原型"
                "（prototype/*.html 且 ≥64 字节）也无 ≥2 张 design/fe 工程线框"
            )

    # C9 plan grounding
    plan_files = find_stage(md_files, feature_dir / "plan")
    plan_text = "\n".join(all_text[f] for f in plan_files) if plan_files else ""
    if plan_files:
        loc_base, base_errors = location_base(readme_text, repo_root, feature_dir)
        errors.extend(base_errors)
        for f in plan_files:
            rel = str(f.relative_to(feature_dir))
            errors.extend(plan_findings(rel, all_text[f], repo_root, loc_base))
            if not BRANCH_HEADING_RE.search(all_text[f]):
                errors.append(f"C9 plan: {rel} 未声明分支策略（需以「分支策略」为标题的节）")
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
        if not _re.search(r"^##+ .*(先说结论|关键决策速览|结论先行)", be_heads, _re.MULTILINE):
            errors.append("C11 结构模板: design/be 缺固定标题（先说结论/关键决策速览）")
        if "影响面评估" not in be_heads:
            errors.append("C11 结构模板: design/be 缺「影响面评估」章")
        for fname, head in (("design/be", be_heads), ("design/fe", fe_heads)):
            if "评审前自检" not in head:
                errors.append(f"C11 结构模板: {fname} 缺「评审前自检」章")
        if fe_files and "data-testid" not in fe_heads:
            errors.append("C11 结构模板: design/fe 缺 data-testid 可测性清单")

    # C12/C13/C14 chain-closure pass (machine-checkable part of closure gate 6): a stage document
    # must stay true over time, readable without the session that wrote it, and free of bare code
    # subjects away from their definition site.
    stage_files = sorted(
        {f for stage in STAGE_DIRS for f in find_stage(md_files, feature_dir / stage)}
    )
    for f in stage_files:
        rel = str(f.relative_to(feature_dir))
        errors.extend(text_form_findings(rel, all_text[f], [f.parent, feature_dir]))

    # C10 mermaid fence balance
    for f in md_files:
        text = all_text[f]
        opened = sum(1 for line in text.splitlines() if line.strip() == "```mermaid")
        blocks = len(mermaid_blocks(text))
        if opened != blocks:
            errors.append(f"C10 mermaid: {f.relative_to(feature_dir)} 有 {opened} 个 mermaid 围栏但仅 {blocks} 个闭合")

    # C22/C23 (2026-10-23 gate change, user-authorized): goal traceability and evidence presence.
    # Both entry points call the same implementation, so a batch cannot pass the directory run and
    # then fail the repo run — two readings of one contract is exactly the defect this batch fixes.
    errors.extend(batch_traceability_findings(feature_dir, repo_root))

    return errors


# --- Decision-traceability checks (C15-C18). Marker-gated and opt-in, mirroring how C11
# gates the design-heading checks: a file only enters these checks when it carries the
# matching marker. This keeps the linter safe to run over the whole repo — a decision ledger
# that has not adopted the eight-column shape is not force-rewritten, and an open issue
# without a batch attachment does not flood the gate. The mechanism is pinned by --self-test
# and demonstrated on the opt-in example files (examples/decisions/).

DECISION_MARKER = "agentflow 决策记录"
LEDGER_MARKER = "agentflow 问题台账"
OWNERSHIP_MARKER = "agentflow 决策归属"
ISS_RE = re.compile(r"ISS-\d{4}-\d{3}(?:-[^\s|]+)?")

DECISION_COLUMNS = ["来源", "待决问题", "现状核验", "推荐", "关闭条件", "优先级", "影响范围", "自动决策"]
LEDGER_STATUS_WORDS = ("仍存在", "已修复", "已关闭", "已失效", "已修", "待修")
PRIORITY_RE = re.compile(r"\bP[0-3]\b")
LEVEL_RE = re.compile(r"(单功能|单模块|多模块|跨项目)")
# 影响范围 must be 级别(具体模块/项目) — a level word alone (no parenthesised name) is a finding.
IMPACT_RE = re.compile(r"(单功能|单模块|多模块|跨项目)\s*\(([^)]+)\)")
OPTION_RE = re.compile(r"[A-C][\u3000\s]")
AUTO_Y_RE = re.compile(r"自动规则|触发条件|判定结论")
DATE_CMD_RE = re.compile(r"\d{4}-\d{2}-\d{2}.*`[^`]+`")


def _ref_is_in_repo(repo_root: Path, path: str) -> bool | None:
    """True if path's first segment is a real entry of this repo (so a missing file is a real
    rot, not an external reference); False if it names a directory this repo does not have
    (treat as a foreign-repo source and accept it without resolution); None if no first segment.
    """
    seg = path.split("/")[0].split(":")[0].split("#")[0].split("?")[0].strip()
    if not seg:
        return None
    return (repo_root / seg).exists()


def _source_refs(cell: str, repo_root: Path) -> tuple[list[str], list[str]]:
    """Return (in_repo_missing, external) reference tokens from a 来源 cell.

    A backtick path or an ``ISS-`` link is an "external" reference when its first segment is
    not a real entry of this repo (e.g. ``planning/...`` belongs to another repo) and is
    accepted without resolution. An in-repo path that does not exist on disk is "missing" and
    must be reported. Cross-repo sources are legitimate — the decision's origin can live in a
    different repository.
    """
    missing: list[str] = []
    external: list[str] = []
    for span in re.findall(r"`([^`\n]+)`", cell):
        tok = span.strip()
        if ISS_RE.search(tok):
            target = repo_root / "docs" / "issues" / tok
            if not target.is_file():
                external.append(tok)
            continue
        p = tok.split("#")[0].split("?")[0].split(":")[0].strip()
        if not p or p.startswith(("/", "http:", "https:", "mailto:")):
            continue
        in_repo = _ref_is_in_repo(repo_root, p)
        if in_repo is None:
            continue
        if in_repo:
            if not (repo_root / p).exists():
                missing.append(tok)
        else:
            external.append(tok)
    for m in ISS_RE.findall(cell):
        full = m + ".md"
        if not (repo_root / "docs" / "issues" / full).is_file() and full not in external:
            external.append(full)
    return missing, external


def decision_record_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C16 — every decision-record table (header ⊇ DECISION_COLUMNS) must be machine-judgable."""
    errors: list[str] = []
    for header, rows in md_tables(text):
        if not all(col in header for col in DECISION_COLUMNS):
            continue  # not a decision-record table; leave 选项对比 / before-after tables alone
        for row in rows:
            cells = {header[i]: (row[i] if i < len(row) else "") for i in range(len(header))}
            src = cells.get("来源", "")
            pend = cells.get("待决问题", "")
            verify = cells.get("现状核验", "")
            rec = cells.get("推荐", "")
            close = cells.get("关闭条件", "")
            prio = cells.get("优先级", "")
            impact = cells.get("影响范围", "")
            auto = cells.get("自动决策", "")
            if not (re.search(r"`[^`]+`", src) or ISS_RE.search(src)):
                errors.append(f"C16 decision-record {label} 决策行缺「来源」（须有 path:line 或 ISS 编号）")
            else:
                missing, _ext = _source_refs(src, repo_root)
                for m in missing:
                    errors.append(f"C16 decision-record {label} 来源引用在盘上不存在: {m}")
            if len(OPTION_RE.findall(pend)) < 2:
                errors.append(f"C16 decision-record {label} 待决问题少于 2 个选项（须 A/B/C… 且各带代价）")
            if not DATE_CMD_RE.search(verify):
                errors.append(f"C16 decision-record {label} 现状核验缺「日期 + 反引号命令」")
            if not close.strip() or close.strip() in ("—", "无", "-"):
                errors.append(f"C16 decision-record {label} 关闭条件为空或为「无」")
            if not PRIORITY_RE.search(prio):
                errors.append(f"C16 decision-record {label} 优先级非 P0–P3")
            if not IMPACT_RE.search(impact):
                if LEVEL_RE.search(impact):
                    errors.append(
                        f"C16 decision-record {label} 影响范围只写级别词未列具体模块/项目"
                        f"（须 级别(具体模块/项目)，如 多模块(youc-admin 订单筛选页 + youc-canvas 支付组件)）"
                    )
                else:
                    errors.append(f"C16 decision-record {label} 影响范围格式非法（须 级别(具体模块/项目)）")
            am = auto.strip().upper()
            if am not in ("Y", "N"):
                errors.append(f"C16 decision-record {label} 自动决策须为 Y/N")
            elif am == "Y":
                if prio.strip() != "P3":
                    errors.append(f"C16 decision-record {label} 自动决策=Y 仅允许 P3（现 {prio.strip() or '空'}）")
                if not AUTO_Y_RE.search(rec):
                    errors.append(
                        f"C16 decision-record {label} 自动决策=Y 但推荐列缺「自动规则/触发条件/判定结论」"
                    )
    return errors


def _last_commit(repo_root: Path, rel_path: str) -> tuple[int, str] | None:
    """(commit epoch, short sha) of the last commit touching rel_path, or None if git/absent."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ct %h", "--", rel_path],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    parts = r.stdout.strip().splitlines()[0].split(None, 1)
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), parts[1]
    except ValueError:
        return None


def _decision_ref_commits(repo_root: Path, source_cell: str) -> list[tuple[str, tuple[int, str]]]:
    """Resolve every in-repo path referenced in a 来源 cell to its last commit (epoch, sha).

    External refs (URLs, absolute paths) and paths that are absent or never committed are
    skipped, matching the time-scope declared by this repository's decision-gate rules.
    """
    found: list[tuple[str, tuple[int, str]]] = []
    for span in re.findall(r"`([^`\n]+)`", source_cell):
        p = span.strip().split("#")[0].split("?")[0].split(":")[0].strip()
        if not p or p.startswith(("/", "http:", "https:", "mailto:")):
            continue
        if _ref_is_in_repo(repo_root, p) is not True:
            continue  # external refs are not time-checked (declared per repo scope)
        if not (repo_root / p).exists():
            continue
        commit = _last_commit(repo_root, p)
        if not commit:
            continue
        found.append((p, commit))
    return found


def staleness_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C17 — a decision's referenced in-repo path modified after its 核验 date is stale.

    Two modes, both git-backed:
      * Explicit 核验 date present: the row is compared against that date as before — a
        referenced path committed after it is stale and must be re-verified.
      * No explicit 核验 date: the baseline is auto-collected as the most recent commit
        touching any referenced in-repo path. By construction no referenced path can be
        newer than its own baseline, so such rows can never be flagged stale — the verifier
        opts into "trust git history" instead of hand-maintaining a date string. This removes
        the recurring friction of a human-typed date going stale on every edit to the row's
        referenced files (seen repeatedly, e.g. 2026-10-24 文档链吸收批).
    """
    errors: list[str] = []
    for header, rows in md_tables(text):
        if not all(col in header for col in DECISION_COLUMNS):
            continue
        for row in rows:
            cells = {header[i]: (row[i] if i < len(row) else "") for i in range(len(header))}
            verify = cells.get("现状核验", "")
            m = re.search(r"(\d{4}-\d{2}-\d{2})", verify)
            ref_commits = _decision_ref_commits(repo_root, cells.get("来源", ""))
            if m:
                try:
                    v_date = _dt.datetime.strptime(m.group(1), "%Y-%m-%d").date()
                except ValueError:
                    continue
                for p, commit in ref_commits:
                    # 日粒度比较。用秒比对会把「当天写核验、当天又改到被引用文件」永远判过期，
                    # 于是 2026-10-23 的门在数学上不可能同日转绿（独立评审第二轮 P1-1 实证）；
                    # 条款要防的是「拿几天前的清单来问人拍板」，不是同批次内的正常推进。
                    c_date = _dt.datetime.fromtimestamp(commit[0]).date()
                    if c_date > v_date:
                        errors.append(
                            f"C17 staleness {label} 引用 {p} 在核验（{m.group(1)}）之后的日期被修改: "
                            f"{commit[1]} {c_date.isoformat()} —— 须重跑核验命令并刷新日期"
                        )
                continue
            # No explicit 核验 date: baseline = latest commit among referenced in-repo paths.
            # Non-stale by construction; emit nothing. (Opt-in "trust git" mode.)
    return errors


def ledger_index_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C15 — a ledger row may not carry a status word unless it links an ISS; ISS links resolve."""
    errors: list[str] = []
    for _header, rows in md_tables(text):
        for row in rows:
            joined = " | ".join(row)
            if any(w in joined for w in LEDGER_STATUS_WORDS) and not ISS_RE.search(joined):
                errors.append(
                    f"C15 ledger-index {label} 台账行自带状态词且无 ISS 链接"
                    f"（状态只能写在记录 frontmatter）"
                )
            for iss in ISS_RE.findall(joined):
                if not (repo_root / "docs" / "issues" / (iss + ".md")).is_file():
                    errors.append(f"C15 ledger-index {label} 台账行引用 {iss} 但记录文件不存在")
    return errors


def _record_status(rec_text: str) -> tuple[str, str]:
    """(status, disposition) from a record's YAML-ish frontmatter (no yaml dep)."""
    if not rec_text.startswith("---"):
        return "", ""
    end = rec_text.find("\n---", 3)
    if end == -1:
        return "", ""
    fm = rec_text[3:end]
    st = re.search(r"^status:\s*(\S+)", fm, re.MULTILINE)
    disp = re.search(r"^disposition:\s*(\S+)", fm, re.MULTILINE)
    return (st.group(1) if st else ""), (disp.group(1) if disp else "")


def ownership_findings(label: str, text: str, repo_root: Path) -> list[str]:
    """C18 — every open issue must be attached to a batch 承接表 or carry deferred/not-doing."""
    errors: list[str] = []
    covered: set[str] = set()
    for header, rows in md_tables(text):
        cell = None
        if _has_columns(header, ["记录编号", "任务号"]):
            for row in rows:
                cell = _cells(header, row)
                covered.update(ISS_RE.findall(_col(cell, "记录编号")))
    issues_dir = repo_root / "docs" / "issues"
    if not issues_dir.is_dir():
        return errors
    for rec in sorted(issues_dir.glob("ISS-*.md")):
        body = rec.read_text(encoding="utf-8", errors="ignore")
        status, disp = _record_status(body)
        if status != "open":
            continue
        iss_id = rec.stem  # e.g. ISS-2026-010-office计划缺异常矩阵
        if iss_id in covered:
            continue
        if disp in ("deferred", "not-doing"):
            continue
        errors.append(
            f"C18 ownership {label} {iss_id} 状态 open，但未出现在任何批次承接表，"
            f"也无 deferred/not-doing 声明（须归属，否则登记当天即红）"
        )
    return errors


# --- Traceability and evidence-presence checks (C22-C23). Marker-gated like C15-C18: a batch
# opts in by carrying 「agentflow 目标承接」 in its README. What differs from the 2026-10-21
# batch is adoption: this repo's live batches opt in on the day the check ships, so the gate
# bites real files instead of only the fixtures under examples/ — the 2026-10-22 walkthrough
# found a proposal goal (CI on a real runner) that vanished from spec, acceptance points and
# the plan task table with nothing turning red, and two ☑ rows whose only evidence was a
# /tmp path that had already been cleaned away.

TRACE_MARKER = "agentflow 目标承接"
TRACE_COLUMNS = ["目标", "spec 承接", "plan 任务", "状态"]
GOAL_RE = re.compile(r"\bG\d+\b")
def trace_task_ids(cell: str) -> set[str]:
    """任务号引用列里的编号集合，方言与 C9 的 `TASK_ID_RE` 同一条（T / FT 前缀都认）。

    独立一份正则会造出「承接表能写、看板认不出」的空洞，所以这里只做切分与全匹配筛选。
    """
    return {tok for tok in re.split(r"[^0-9A-Za-z_-]+", cell) if TASK_ID_RE.fullmatch(tok)}
MODULE_RE = re.compile(r"\bM-[A-Z]\b")
AC_ID_RE = re.compile(r"\bG\d+-AC-\d+\b")
DONE_GLYPH = "☑"
TODO_GLYPH = "☐"
BLOCKED_GLYPH = "⚠"
SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{7,40}(?![0-9a-fA-F])")
REPO_REV_RE = re.compile(r"[\w.-]+@[0-9a-f]{7,40}:[^\s|`]+")
NA_RE = re.compile(r"N/A[:：]\s*\S")


def git_available() -> bool:
    return shutil.which("git") is not None


def _git_available() -> bool:
    """Resolve ``git_available`` so it can be monkeypatched via the public ``doc_chain``
    launcher module (the historical home of this function and what the regression tests
    patch). Falls back to the local definition when the launcher module is not imported."""
    launcher = sys.modules.get("doc_chain")
    if launcher is not None and hasattr(launcher, "git_available"):
        return bool(launcher.git_available())
    return git_available()


def _git_commit_present(repo_root: Path, sha: str) -> bool:
    """True only when git resolves sha as a commit object. No git means not verifiable: the
    check fails closed rather than letting an unverifiable claim pass on a machine without git."""
    try:
        r = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        )
    except OSError:
        return False
    return r.returncode == 0


def _tables_with_columns(text: str, cols: list[str]) -> list[tuple[list[str], list[list[str]]]]:
    """Every table whose (markup-normalised) header covers cols."""
    return [hd for hd in md_tables(text) if _has_columns(hd[0], cols)]


def _norm_col(name: str) -> str:
    """Column label without markup, so `**目标**`, `` `ID` `` and 「目标 」name the same column."""
    return name.strip().strip("`* ").replace(" ", "").replace("　", "")


def _col(cell: dict[str, str], name: str) -> str:
    """Read a column by label through the same normalisation the header match uses."""
    return cell.get(_norm_col(name), "")


def _has_columns(header: list[str], cols: list[str]) -> bool:
    wanted = {_norm_col(c) for c in cols}
    return wanted.issubset({_norm_col(h) for h in header})


def _cells(header: list[str], row: list[str]) -> dict[str, str]:
    return {_norm_col(h): (row[i] if i < len(row) else "") for i, h in enumerate(header)}


def plan_task_rows(text: str) -> dict[str, tuple[str, str]]:
    """task id -> (status cell, evidence cell) for every table with an ID and a 状态 column.

    The evidence column may be named 证据 or 证据回写; when absent the pair's second element is
    empty, which C23 reads as "no evidence" for a completed row rather than as a parse failure.
    """
    out: dict[str, tuple[str, str]] = {}
    for header, rows in md_tables(text):
        labels = {_norm_col(h) for h in header}
        if "ID" not in labels or "状态" not in labels:
            continue  # 列名按同一归一化匹配：装饰过的表头不得让整张表静默不可见
        ev_col = next((c for c in ("证据", "证据回写") if _norm_col(c) in labels), None)
        for row in rows:
            cell = _cells(header, row)
            tid = _col(cell, "ID").strip().strip("`* ")
            if not TASK_ID_RE.match(tid):  # 任务号方言单点取自 C9，不在这里另立一套
                continue
            out[tid] = (_col(cell, "状态"), _col(cell, ev_col) if ev_col else "")
    return out


def evidence_carriers(cell: str, repo_root: Path, batch_dir: Path | None = None) -> list[str]:
    """Which verifiable carriers this evidence cell holds: repo path, repo-qualified ref,
    resolvable commit sha, or an explicit N/A with a reason. /tmp and absolute paths never count.

    Paths resolve against the repo root *and* the batch directory, because evidence cells are
    written both ways in practice (`reviews/review-…md` relative to the batch, `docs/issues/…`
    relative to the repo). Reading only the repo root called correctly-written evidence missing —
    the over-wide judgement this batch's own exception matrix predicted and required narrowing.
    """
    roots = [repo_root] + ([batch_dir] if batch_dir is not None else [])
    kinds: list[str] = []
    own = {repo_root.name, "agentflow", "agentflows"}
    for m in REPO_REV_RE.finditer(cell):
        repo = m.group(0).split("@", 1)[0]
        if repo not in own:
            kinds.append("仓限定引用")
            continue
        # 本仓名也可以用仓限定写法，但那就得按本仓核：rev 可解析且路径在盘，否则是自己写的假地址
        rev, _, tail = m.group(0).split("@", 1)[1].partition(":")
        if tail and _git_commit_present(repo_root, rev) and (repo_root / tail).exists():
            kinds.append("本仓限定引用（已核）")
    # 路径 token 复用 C9 的 path_candidates：反引号内与裸写的带后缀路径都算，
    # 否则按契约（spec/be §6.2「反引号内或裸写」）正确写下的证据会被判成无载体。
    tokens = sorted(path_candidates(cell)) + [g for g in re.findall(r"\]\(([^)\s]+)\)", cell)]
    for tok in tokens:
        p = tok.strip().strip("（）()「」\"'[]").split("#")[0].split("§")[0]
        if not p or p.startswith(("/", "~", "http:", "https:", "mailto:")):
            continue
        if "@" in p or ":" in p:
            continue  # repo-qualified refs are handled above
        if any(_ref_is_in_repo(r, p) is True and (r / p).exists() for r in roots):
            kinds.append("仓内路径")
            break
    for sha in SHA_RE.findall(cell):
        if _git_commit_present(repo_root, sha):
            kinds.append("提交号")
            break
    if NA_RE.search(cell):
        kinds.append("显式不适用")
    return sorted(set(kinds))


def evidence_presence_findings(
    label: str, plan_text: str, repo_root: Path, batch_dir: Path | None = None
) -> list[str]:
    """C23 — a row marked 已完成 must carry something a third party can re-check on disk."""
    errors: list[str] = []
    rows = plan_task_rows(plan_text)
    for task_id, (status, evidence) in sorted(rows.items()):
        if not status.strip().startswith(DONE_GLYPH):
            continue  # 进行中 / 未开始 / 阻塞 / 本期不做 carry no evidence duty yet
        if evidence_carriers(evidence, repo_root, batch_dir):
            continue
        if not evidence.strip():
            detail = "证据列为空"
        elif SHA_RE.search(evidence) and not _git_available():
            detail = "环境无 git，提交号不可核（失败关闭：无 git 时提交号不算可复核载体）"
        elif "/tmp/" in evidence or re.search(r"(^|[\s`])/(Users|home|var)/", evidence):
            detail = "证据只指向临时目录或机器绝对路径，已不在盘"
        else:
            detail = "证据列无可复核载体（路径不存在、提交号不可解析、也不是仓限定引用）"
        errors.append(
            f"C23 证据在场: {label} {task_id} 标为已完成但{detail}"
            f"（四类载体之一即可：仓内存在的路径 / 仓库@修订:路径 / 可解析提交号 / N/A: 理由）"
        )
    return errors


def _heading_sections(text: str) -> list[str]:
    """Markdown chunks of (heading line + body up to the next heading)."""
    chunks: list[str] = []
    cur: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line):
            if cur:
                chunks.append("\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def trace_tables(source_text: str) -> list[tuple[list[str], list[list[str]]]]:
    """The 承接 tables sitting under a heading that names 目标承接.

    Heading scoping is not decoration: a table with the same four columns placed anywhere else in
    the source would otherwise satisfy the check while the real 承接表 stayed unread. The source is
    the README in normal mode, or HISTORY.md in C24 single-ledger mode.
    """
    out: list[tuple[list[str], list[list[str]]]] = []
    for section in _heading_sections(source_text):
        if "目标承接" in section.splitlines()[0]:
            out.extend(_tables_with_columns(section, TRACE_COLUMNS))
    return out


def goal_traceability_findings(feature_dir: Path, repo_root: Path) -> list[str]:
    """C22 — every proposal goal must land in spec and plan, and nothing may cite a phantom.

    Bidirectional on purpose: a one-way check (targets must appear downstream) is satisfied by
    writing anything downstream, while the reverse direction catches citations that no upstream
    goal ever declared. Status is compared with the plan board's glyphs, so a README claiming a
    goal is done while its tasks are still ☐ fails the same day it is written.
    """
    readme = feature_dir / "README.md"
    history = feature_dir / "HISTORY.md"
    single_ledger = (not readme.is_file()) and history.is_file()
    # Single-ledger mode (C24): README absent, HISTORY present — the 目标承接 mark and table live in
    # HISTORY.md. README present wins otherwise; HISTORY.md is then an ordinary stage doc, not a ledger.
    if single_ledger:
        readme_text = read(history)
    elif readme.is_file():
        readme_text = read(readme)
    else:
        return []
    if TRACE_MARKER not in readme_text:
        return []
    batch = feature_dir.name
    tables = trace_tables(readme_text)
    if not tables:
        return [
            (
                f"C22 目标承接: {batch} 打了 {TRACE_MARKER} 标记，但「目标承接」标题下没有承接表"
                f"（必需列：{' / '.join(TRACE_COLUMNS)}）；补表，不许摘标记"
            )
        ]
    md_files = [f for f in sorted(feature_dir.rglob("*.md")) if f.name != ".gitkeep"]
    stage_text = {
        "proposal": "\n".join(read(f) for f in find_stage(md_files, feature_dir / "proposal")),
        "spec": "\n".join(read(f) for f in find_stage(md_files, feature_dir / "spec")),
    }
    plan_rows: dict[str, tuple[str, str]] = {}
    for f in find_stage(md_files, feature_dir / "plan"):
        plan_rows.update(plan_task_rows(read(f)))

    def _resolves(token: str) -> bool:
        p = token.strip().split("#")[0].split("§")[0].strip()
        if not p or p.startswith(("/", "http:", "https:", "mailto:")) or "@" in p:
            return True  # 非仓内路径写法不在本判据射程内（外链与跨仓引用另有口径）
        return (feature_dir / p).exists() or (repo_root / p).exists()

    errors: list[str] = []
    table_goals: set[str] = set()
    referenced: set[str] = set()
    for header, rows in tables:
        for row in rows:
            cell = _cells(header, row)
            goals = set(GOAL_RE.findall(_col(cell, "目标")))
            if not goals:
                errors.append(f"C22 目标承接: {batch} 承接行「{_col(cell, '目标')[:24] or '空'}」没有目标编号 G n")
            table_goals |= goals
            tag = "/".join(sorted(goals)) or _col(cell, "目标")[:24]

            for mid in sorted(set(MODULE_RE.findall(_col(cell, "spec 承接")))):
                if mid not in stage_text["spec"]:
                    errors.append(f"C22 目标承接: {tag} 声明由 {mid} 承接，但 spec/ 文本里找不到 {mid}")
            for ac in sorted(set(AC_ID_RE.findall(_col(cell, "spec 承接")))):
                if ac not in stage_text["spec"]:
                    errors.append(f"C22 目标承接: {tag} 引用的验收点 {ac} 不在 spec/ 文本中")
            # 出处列同样要能在盘上解析——声明了「路径须可解析」却从不校验，就是第二条空转判据
            cited = _col(cell, "proposal 出处") + _col(cell, "spec 承接")
            for p in sorted(path_candidates(cited)):
                if not _resolves(p):
                    errors.append(f"C22 目标承接: {tag} 的出处 {p} 不在盘（批次目录与仓根各试一次）")

            tids = trace_task_ids(_col(cell, "plan 任务"))
            if not tids:
                errors.append(f"C22 目标承接: {tag} 未给出任何 plan 任务号")
            for t in sorted(tids):
                if t not in plan_rows:
                    errors.append(f"C22 目标承接: {tag} 引用的任务号 {t} 不在计划任务表（幻影引用）")
            referenced |= tids

            glyph = _col(cell, "状态").strip()[:1]
            real = {plan_rows[t][0].strip()[:1] for t in tids if t in plan_rows}
            if glyph == DONE_GLYPH and real and real != {DONE_GLYPH}:
                errors.append(
                    f"C22 目标承接: {tag} 承接表标已完成，所引任务行的字形是 {'/'.join(sorted(real))}"
                )
            if glyph in (TODO_GLYPH, "◐", BLOCKED_GLYPH) and real == {DONE_GLYPH}:
                errors.append(
                    f"C22 目标承接: {tag} 承接表状态是「{glyph}」，但所引任务行已全部完成（未回写）"
                )

    declared = set(GOAL_RE.findall(stage_text["proposal"]))
    for g in sorted(declared - table_goals):
        errors.append(f"C22 目标承接: 提案声明的目标 {g} 未进入承接表（缺承接）")
    for g in sorted(table_goals - declared):
        errors.append(f"C22 目标承接: 承接表引用了提案中不存在的目标 {g}（幻影目标）")
    for task_id, (status, _ev) in sorted(plan_rows.items()):
        if status.strip()[:1] in (DONE_GLYPH, BLOCKED_GLYPH) and task_id not in referenced:
            errors.append(
                f"C22 目标承接: {batch} 计划任务 {task_id} 已是完成或阻塞状态，"
                f"却没有被任何承接行引用（孤儿任务，须说明它服务哪个目标）"
            )
    return errors


def batch_traceability_findings(batch_dir: Path, repo_root: Path) -> list[str]:
    """C22 + C23 for one batch directory; the single entry both modes call.

    The plan glob is recursive on purpose: batches put plans under `plan/` and sometimes one level
    deeper (`plan/be/`), and a non-recursive read silently reports "no evidence problems" for every
    nested plan — the vacuous-check failure mode this whole batch exists to close.
    """
    errors = goal_traceability_findings(batch_dir, repo_root)
    plan_dir = batch_dir / "plan"
    if not plan_dir.is_dir():
        return errors
    for f in sorted(plan_dir.rglob("*.md")):
        if f.name == ".gitkeep":
            continue
        rel = f.relative_to(repo_root).as_posix() if f.is_relative_to(repo_root) else f.name
        errors.extend(evidence_presence_findings(rel, read(f), repo_root, batch_dir))
    return errors


def repo_policy_findings(repo_root: Path) -> list[str]:
    """Run C15-C18 over opt-in files. Marker-gated so the whole repo can be scanned safely."""
    errors: list[str] = []
    skip_dirs = (repo_root / ".git", repo_root / "packaging" / "runtime")
    md_files: list[Path] = []
    for p in repo_root.rglob("*.md"):
        if p.parent == skip_dirs[1] or any(s in p.parents for s in skip_dirs):
            continue
        md_files.append(p)
    for p in md_files:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = p.relative_to(repo_root).as_posix()
        if DECISION_MARKER in t:
            errors.extend(decision_record_findings(rel, t, repo_root))
            errors.extend(staleness_findings(rel, t, repo_root))
        if LEDGER_MARKER in t:
            errors.extend(ledger_index_findings(rel, t, repo_root))
    for batch in sorted(p for p in repo_root.glob("docs/features/*") if p.is_dir()):
        readme = batch / "README.md"
        t = read(readme) if readme.is_file() else ""
        if OWNERSHIP_MARKER in t:
            errors.extend(ownership_findings(readme.relative_to(repo_root).as_posix(), t, repo_root))
        # The batch set is every directory, not only those that already have a README: two modes
        # sharing one implementation is worthless if they disagree about which batches exist.
        errors.extend(batch_traceability_findings(batch, repo_root))
    return errors


