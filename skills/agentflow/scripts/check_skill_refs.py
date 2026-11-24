#!/usr/bin/env python3
"""check_skill_refs.py — 校验 skill（触发层）与 references（正文层）的接线一致性。

要防的六类漂移：
  R1 断链：skill 里 `../agentflow/references/X.md` 指向的文件不存在。
  R2 孤儿条款：skill 的硬约束写了 `（正文：§X）`，但该 references 里没有对应标题——
     说明摘要已跑在正文前面（条款只活在提醒里，正文没依据）。
  R3 反向失联：references 头部「加载者」声明了某个入口，但那个入口并没引用它——
     说明入口已迁移而声明没跟上（读者按声明去找会落空）。
  R4 主干超预算：SKILL.md 的「主干」表超过 5 行——默认阅读面会重新膨胀回「全量预读」。
  R5 版本漂移：根 manifest 与各宿主 manifest（含已生成的 runtime）版本不一致。
  R6 相对链接不可达：skills/ 下 Markdown 链接指向不存在的文件或逃出可分发树——
     源仓能解析、安装快照里却断链的路径，必须在这里暴露。

设计取舍：R2 依赖 skill 里显式的 `（正文：§X）` 标注，不用中文分词猜关键词——
猜出来的覆盖度既不可复现也不可审计。标注是本脚本的接口，与 C18 记录归属表同思路。

用法：
  python3 check_skill_refs.py [--root <仓库或安装根>] [--source-only] [--self-test]
退出码：0 通过 / 1 有问题 / 2 参数错误
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote
from workflow_lib.installation import RUNTIME_DIRECTORIES, RUNTIME_FILES, read_object

LINK_RE = re.compile(r"\]\(\s*(<[^>]+>|[^)\s]+)(?:\s+[\"'][^)]*[\"'])?\s*\)")
REFERENCE_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", re.MULTILINE)
HEADING_RE = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INLINE_CODE_RE = re.compile(r"(`+) .*? \1", re.VERBOSE)
LOADER_SKILL_RE = re.compile(r"skills/([\w-]+)/SKILL\.md|用户主动入口是\s*`([\w-]+)`")
CITE_RE = re.compile(r"（正文：§\s*([^）]+)）")
LOADER_RE = re.compile(r"^\s*>\s*\*\*加载者\*\*[：:]\s*(.+)$", re.MULTILINE)
MAIN_TRUNK_MAX = 5
MANIFEST_FILES = (*RUNTIME_FILES, *(f"{name}/plugin.json" for name in RUNTIME_DIRECTORIES if name.startswith(".")))
PAYLOAD_ROOTS = frozenset((*RUNTIME_DIRECTORIES, *RUNTIME_FILES))
VERSION_RE = re.compile(r"(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)){2}(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")


def main_trunk_rows(text: str) -> int:
    """Count data rows in the **主干** table; 0 when the marker is absent."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("**主干**"):
            rows: list[str] = []
            for row in lines[index + 1:]:
                if row.startswith("|"):
                    rows.append(row)
                elif rows:
                    break
            return max(0, len(rows) - 2)
    return 0


def headings(text: str) -> list[str]:
    return [m.group(1).strip() for m in HEADING_RE.finditer(without_examples(text))]


def heading_matches(section: str, heads: list[str]) -> bool:
    """标注的节名能对上某个标题（允许标注比标题短，如「§输出」对「输出：任务简报」）。"""
    want = section.strip().strip("§").strip()
    # 去掉标注里常见的限定后缀：「§六要素」「§依据缺失时」「§输出」
    for h in heads:
        if h == want or h.startswith(want) or want.startswith(h.split("：")[0].split(":")[0]):
            return True
        if want in h:
            return True
    return False


def check_skill(skill: Path, root: Path) -> list[str]:
    errors: list[str] = []
    text = skill.read_text(encoding="utf-8", errors="replace")
    rel_skill = skill.relative_to(root).as_posix()

    # R1 — every references link resolves
    refs_seen: dict[str, Path] = {}
    for raw in link_targets(text):
        target = resolve_target(skill, raw)
        if target is None or target.suffix != ".md" or "references" not in target.parts:
            continue
        if not target.is_file():
            errors.append(f"R1 断链: {rel_skill} 引用 {raw} 但文件不存在")
            continue
        refs_seen[raw] = target

    # R2 — every `（正文：§X）` citation has a matching heading in the cited file
    #      The citation applies to the reference named earlier in the same document; when a
    #      skill cites several, we accept a match in ANY referenced file (the author writes it
    #      next to the bullet, and bullets are grouped under one "读什么" list).
    for m in CITE_RE.finditer(text):
        section = m.group(1).strip()
        hit = False
        for target in refs_seen.values():
            if heading_matches(section, headings(target.read_text(encoding="utf-8", errors="replace"))):
                hit = True
                break
        if not hit:
            names = "、".join(sorted(refs_seen)) or "（本文件未引用任何 references）"
            errors.append(
                f"R2 孤儿条款: {rel_skill} 声明「正文：§{section}」，但 {names} 里没有对应标题"
                f"——摘要跑在正文前面了"
            )

    # R4 — the default reading surface stays bounded.
    if "**主干**" in text:
        rows = main_trunk_rows(text)
        if rows > MAIN_TRUNK_MAX:
            errors.append(
                f"R4 主干超预算: {rel_skill} 主干表 {rows} 行 > {MAIN_TRUNK_MAX}；"
                "把低频条目移到「按产物触发」，不要恢复全量预读"
            )
    return errors


def without_examples(text: str) -> str:
    """保留行位置，忽略围栏示例和 HTML 注释。"""
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m[0].count("\n"), text, flags=re.DOTALL)
    output: list[str] = []
    fence = ""
    for line in text.splitlines():
        marker = FENCE_RE.match(line)
        if fence:
            if marker and marker[1].startswith(fence) and not marker[2].strip():
                fence = ""
            output.append("")
        elif marker:
            fence = marker[1]
            output.append("")
        else:
            output.append(line)
    return "\n".join(output)


def link_targets(text: str) -> list[str]:
    prose = INLINE_CODE_RE.sub("", without_examples(text))
    return [m[1].removeprefix("<").removesuffix(">") for pattern in (LINK_RE, REFERENCE_RE)
            for m in pattern.finditer(prose)]


def resolve_target(doc: Path, raw: str) -> Path | None:
    file_part = unquote(raw.split("#", 1)[0].split("?", 1)[0])
    if re.match(r"^[a-z][a-z\d+.-]*:", file_part, re.IGNORECASE) or file_part.startswith("//"):
        return None
    return (doc.parent / file_part).resolve() if file_part else doc.resolve()


def loader_errors(root: Path, skills: list[Path]) -> list[str]:
    outgoing = {
        path.parent.name: {resolve_target(path, link) for link in link_targets(path.read_text(encoding="utf-8"))}
        for path in skills
    }
    errors: list[str] = []
    for reference in sorted((root / "skills").glob("*/references/**/*.md")):
        text = reference.read_text(encoding="utf-8")
        for row in LOADER_RE.finditer(text):
            for first, second in LOADER_SKILL_RE.findall(row[1]):
                name = first or second
                if reference.resolve() not in outgoing.get(name, set()):
                    errors.append(f"R3 反向失联: {reference.relative_to(root)} → {name}/SKILL.md；{row[0].strip()}")
    return errors


def manifest_version(path: Path, plugin_name: str) -> str:
    data = read_object(path)
    if path.name == "marketplace.json":
        plugins = data.get("plugins")
        if not isinstance(plugins, list):
            raise ValueError("缺少 plugins 列表")
        entries = [entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == plugin_name]
        if len(entries) != 1:
            raise ValueError(f"需要唯一的 {plugin_name} 插件条目")
        data = entries[0]
    if data.get("name") != plugin_name:
        raise ValueError(f"name 应为 {plugin_name}")
    version = data.get("version")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise ValueError("version 必须为版本字符串（如 1.2.3）")
    return version


def manifest_version_errors(root: Path, *, source_only: bool = False) -> list[str]:
    """检查所在树的全部必需清单；仓库另与生成包做同版本核对。"""
    found: list[tuple[str, str]] = []
    errors: list[str] = []
    try:
        plugin_name = read_object(root / "plugin.json").get("name")
        if not isinstance(plugin_name, str) or not plugin_name:
            raise ValueError("缺少插件名称")
    except (OSError, ValueError) as exc:
        return [f"R5 manifest 不可解析: plugin.json（{exc}）"]
    paths = list(MANIFEST_FILES)
    if not source_only and (root / "packaging/build_runtime.py").is_file():
        paths.extend(f"packaging/runtime/{rel}" for rel in MANIFEST_FILES)
    for rel in paths:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            errors.append(f"R5 manifest 缺失或不是常规文件: {rel}")
            continue
        try:
            found.append((rel, manifest_version(path, plugin_name)))
        except (OSError, ValueError) as exc:
            errors.append(f"R5 manifest 不可解析: {rel}（{exc}）")
    if len({version for _, version in found}) > 1:
        detail = ", ".join(f"{rel}={version}" for rel, version in found)
        errors.append(f"R5 版本不一致: {detail}")
    return errors


def anchors(doc: Path) -> set[str]:
    text = without_examples(doc.read_text(encoding="utf-8"))
    result = set(re.findall(r"""<(?:a|span)\s+(?:name|id)=["']([^"']+)["']""", text))
    used: set[str] = set()
    for title in headings(text):
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title.lower())
        slug = "".join("-" if ch == " " else ch for ch in clean
                       if ch in "-_ " or unicodedata.category(ch)[0] not in "PSC")
        anchor = slug
        suffix = 0
        while anchor in used:
            suffix += 1
            anchor = f"{slug}-{suffix}"
        used.add(anchor)
    return result | used


def relative_link_errors(root: Path) -> list[str]:
    """检查分发正文的行内链接、引用定义与 Markdown 标题锚点。"""
    root = root.resolve()
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    documents = sorted(path for name in ("skills", "agents") for path in (root / name).rglob("*.md"))
    for doc in documents:
        rel_doc = doc.relative_to(root).as_posix()
        for raw in link_targets(doc.read_text(encoding="utf-8")):
            if raw.startswith(("//", "http://", "https://")):
                continue
            file_part, _, fragment = raw.partition("#")
            if unquote(file_part).startswith("/") or re.match(r"(?i)(?:file:|[a-z]:[\\/])", file_part):
                errors.append(f"R6 绝对路径: {rel_doc} → {raw}（安装快照里不可移植）")
                continue
            target = resolve_target(doc, raw)
            if target is None:
                continue
            if not target.is_relative_to(root) or not target.relative_to(root).parts or target.relative_to(root).parts[0] not in PAYLOAD_ROOTS:
                errors.append(f"R6 链接逃出分发根: {rel_doc} → {raw}")
            elif not target.exists():
                errors.append(f"R6 相对链接不可达: {rel_doc} → {raw}")
            elif fragment and target.suffix == ".md" and target.is_file():
                if target not in anchor_cache:
                    anchor_cache[target] = anchors(target)
                if unquote(fragment) not in anchor_cache[target]:
                    errors.append(f"R6 标题锚点不可达: {rel_doc} → {raw}")
    return errors


def run(root: Path, *, source_only: bool = False) -> list[str]:
    errors: list[str] = []
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    for skill in skills:
        errors.extend(check_skill(skill, root))
    errors.extend(loader_errors(root, skills))
    errors.extend(manifest_version_errors(root, source_only=source_only))
    errors.extend(relative_link_errors(root))
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="校验 skill 与 references 的接线一致性")
    ap.add_argument("--root", default=".", help="仓库根（默认当前目录）")
    ap.add_argument("--source-only", action="store_true", help="仅检查当前源码清单，可在重建前运行")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    root = Path(args.root).resolve()
    if not (root / "skills").is_dir():
        print(f"[错误] {root}/skills 不存在", file=sys.stderr)
        return 2
    errors = run(root, source_only=args.source_only)
    if errors:
        print(f"FAIL skill-refs ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS skill-refs（R1 断链 / R2 孤儿条款 / R3 反向失联 / R4 主干预算 / R5 版本一致 / R6 链接可达 均无）")
    return 0


def _self_test() -> int:
    import shutil
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def write_manifests(base: Path) -> None:
        for rel in MANIFEST_FILES:
            path = base / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            entry = '{"name":"agentflow","version":"1.0.0"}'
            path.write_text('{"plugins":[' + entry + ']}' if path.name == "marketplace.json" else entry,
                            encoding="utf-8")

    def case(name: str, build, expect: int, want: str) -> None:
        base = Path(tempfile.mkdtemp(prefix="af-skillrefs-"))
        try:
            (base / "skills").mkdir()
            write_manifests(base)
            build(base)
            errors = run(base)
            code = 1 if errors else 0
            text = "\n".join(errors)
            ok = code == expect and want in text
            if text:
                print(text)
            results.append((name, ok, "" if ok else f"期望 exit={expect} 含「{want}」，实际：{text or '无 findings'}"))
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def mk_skill(base: Path, name: str, body: str) -> Path:
        d = base / "skills" / name
        d.mkdir(parents=True, exist_ok=True)
        p = d / "SKILL.md"
        p.write_text(body, encoding="utf-8")
        return p

    def mk_ref(base: Path, name: str, body: str) -> None:
        d = base / "skills" / "agentflow" / "references"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(body, encoding="utf-8")

    def t_clean(base: Path) -> None:
        mk_ref(base, "intake.md", "# Intake\n\n> **加载者**：`SKILL.md` 路由；用户主动入口是 `agentflow-intake`。\n\n## 六要素\n\n内容\n")
        mk_skill(base, "agentflow-intake",
                 "---\nname: agentflow-intake\n---\n\n"
                 "读 [`../agentflow/references/intake.md`](../agentflow/references/intake.md)\n\n"
                 "- **红线原样保留**（正文：§六要素）\n")

    def t_broken_link(base: Path) -> None:
        mk_skill(base, "agentflow-intake",
                 "---\nname: agentflow-intake\n---\n\n读 [`../agentflow/references/ghost.md`](../agentflow/references/ghost.md)\n")

    def t_orphan(base: Path) -> None:
        mk_ref(base, "intake.md", "# Intake\n\n## 六要素\n\n内容\n")
        mk_skill(base, "agentflow-intake",
                 "---\nname: agentflow-intake\n---\n\n"
                 "读 [`../agentflow/references/intake.md`](../agentflow/references/intake.md)\n\n"
                 "- **缺依据先问**（正文：§依据缺失时）\n")

    def t_main_trunk(base: Path) -> None:
        mk_ref(base, "execution.md", "# Execution\n\n## 测试\n\n内容\n")
        rows = "\n".join(
            f"| 工作{i} | [执行](../agentflow/references/execution.md) |" for i in range(6)
        )
        mk_skill(base, "agentflow",
                 "**主干**（每次委派）：\n\n| 工作 | 入口 |\n| --- | --- |\n" + rows + "\n\n"
                 "**按产物触发**：其余内容。\n")

    def t_manifest_clean(base: Path) -> None:
        (base / "packaging").mkdir()
        (base / "packaging/build_runtime.py").touch()
        write_manifests(base / "packaging/runtime")

    def t_manifest_mismatch(base: Path) -> None:
        t_manifest_clean(base)
        (base / "packaging/runtime/.qoder-plugin/plugin.json").write_text(
            '{"name":"agentflow","version":"0.9.0"}', encoding="utf-8")

    def t_dead_relative_link(base: Path) -> None:
        mk_skill(base, "agentflow-intake",
                 "---\nname: agentflow-intake\n---\n\n"
                 "读 [缺失的发布内容](../asset.md)\n")

    def t_reverse(base: Path) -> None:
        mk_skill(base, "agentflow-intake", "# Intake\n")
        mk_ref(base, "intake.md", "# Intake\n\n> **加载者**：用户主动入口是 `agentflow-intake`。\n")

    def t_fragment(base: Path) -> None:
        mk_ref(base, "intake.md", "# Intake\n\n## 依据缺失时\n")
        mk_skill(base, "agentflow-intake", "[正确](../agentflow/references/intake.md#依据缺失时)\n"
                 "[错误](../agentflow/references/intake.md#不存在)\n")

    def t_reference(base: Path) -> None:
        mk_skill(base, "agentflow-intake", "[参考][entry]\n\n[entry]: ../dead.md\n")

    def t_outside(base: Path) -> None:
        (base / "README.md").touch()
        mk_skill(base, "agentflow-intake", "[维护说明](../../README.md)\n")

    def t_examples(base: Path) -> None:
        mk_skill(base, "agentflow-intake", "~~~md\n[示例](../dead.md)\n~~~\n"
                 "<!-- [例子](../dead.md) -->\n")

    case("干净接线通过", t_clean, 0, "")  # 无 findings 即通过；PASS 字样由 main() 打印
    case("R1 断链", t_broken_link, 1, "R1 断链")
    case("R2 孤儿条款（正文节不存在）", t_orphan, 1, "R2 孤儿条款")
    case("R3 引用者反向失联", t_reverse, 1, "R3 反向失联")
    case("R4 主干超预算", t_main_trunk, 1, "R4 主干超预算")
    case("R5 版本一致通过", t_manifest_clean, 0, "")
    case("R5 生成树宿主版本不一致", t_manifest_mismatch, 1, "R5 版本不一致")
    case("R5 必需清单缺失", lambda base: (base / ".qoder-plugin/plugin.json").unlink(),
         1, "R5 manifest 缺失")
    case("R5 拒绝 JSON 数组", lambda base: (base / ".codex-plugin/plugin.json").write_text("[]"),
         1, "R5 manifest 不可解析")
    case("R6 相对链接不可达", t_dead_relative_link, 1, "R6 相对链接不可达")
    case("R6 标题锚点不可达", t_fragment, 1, "R6 标题锚点不可达")
    case("R6 引用式链接不可达", t_reference, 1, "R6 相对链接不可达")
    case("R6 拒绝维护面文件", t_outside, 1, "R6 链接逃出分发根")
    case("R6 跳过例子", t_examples, 0, "")

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
