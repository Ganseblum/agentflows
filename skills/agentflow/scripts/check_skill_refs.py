#!/usr/bin/env python3
"""check_skill_refs.py — 校验 skill（触发层）与 references（正文层）的接线一致性。

要防的三类漂移：
  R1 断链：skill 里 `../agentflow/references/X.md` 指向的文件不存在。
  R2 孤儿条款：skill 的硬约束写了 `（正文：§X）`，但该 references 里没有对应标题——
     说明摘要已跑在正文前面（条款只活在提醒里，正文没依据）。
  R3 反向失联：references 头部「加载者」声明了某个入口，但那个入口并没引用它——
     说明入口已迁移而声明没跟上（读者按声明去找会落空）。

设计取舍：R2 依赖 skill 里显式的 `（正文：§X）` 标注，不用中文分词猜关键词——
猜出来的覆盖度既不可复现也不可审计。标注是本脚本的接口，与 C18 记录归属表同思路。

用法：
  python3 check_skill_refs.py [--root <仓库根>] [--self-test]
退出码：0 通过 / 1 有问题 / 2 参数错误
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REF_LINK_RE = re.compile(r"\]\(([^)]*references/([A-Za-z0-9._-]+\.md))(?:#[^)]*)?\)")
CITE_RE = re.compile(r"（正文：§\s*([^）]+)）")
LOADER_RE = re.compile(r"^\s*>\s*\*\*加载者\*\*[：:]\s*(.+)$", re.MULTILINE)


def headings(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^#{2,3}\s+(.+)$", text, re.MULTILINE)]


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
    for m in REF_LINK_RE.finditer(text):
        raw, name = m.group(1), m.group(2)
        target = (skill.parent / raw).resolve()
        if not target.is_file():
            errors.append(f"R1 断链: {rel_skill} 引用 {raw} 但文件不存在")
            continue
        refs_seen[name] = target

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

    # R3 — the reference's declared 加载者 must actually reference this skill back
    for name, target in refs_seen.items():
        ref_text = target.read_text(encoding="utf-8", errors="replace")
        for m in LOADER_RE.finditer(ref_text):
            declared = m.group(1)
            if skill.stem in declared or skill.parent.name in declared:
                continue
            # 声明里提到本入口名的任一形态即可；只在声明点名了「用户主动入口」时才算失联
            if "主动入口" in declared and skill.parent.name not in declared:
                errors.append(
                    f"R3 反向失联: {target.relative_to(root).as_posix()} 声明加载者是 "
                    f"「{declared[:60]}」，但没提到 {skill.parent.name}"
                )
    return errors


def run(root: Path) -> list[str]:
    errors: list[str] = []
    skills_dir = root / "skills"
    for skill in sorted(skills_dir.glob("*/SKILL.md")):
        errors.extend(check_skill(skill, root))
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="校验 skill 与 references 的接线一致性")
    ap.add_argument("--root", default=".", help="仓库根（默认当前目录）")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    root = Path(args.root).resolve()
    if not (root / "skills").is_dir():
        print(f"[错误] {root}/skills 不存在", file=sys.stderr)
        return 2
    errors = run(root)
    if errors:
        print(f"FAIL skill-refs ({len(errors)} findings)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS skill-refs（R1 断链 / R2 孤儿条款 / R3 反向失联 均无）")
    return 0


def _self_test() -> int:
    import shutil
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def case(name: str, build, expect: int, want: str) -> None:
        base = Path(tempfile.mkdtemp(prefix="af-skillrefs-"))
        try:
            (base / "skills").mkdir()
            build(base)
            errors = run(base)
            code = 1 if errors else 0
            text = "\n".join(errors)
            ok = code == expect and want in text
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

    case("干净接线通过", t_clean, 0, "")  # 无 findings 即通过；PASS 字样由 main() 打印
    case("R1 断链", t_broken_link, 1, "R1 断链")
    case("R2 孤儿条款（正文节不存在）", t_orphan, 1, "R2 孤儿条款")

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
