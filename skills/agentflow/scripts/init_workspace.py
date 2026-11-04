#!/usr/bin/env python3
"""init_workspace.py — agentflow 项目侧安全安装器：固定件 copy，AI 只填项目事实。

设计要点（2026-11-04 可用性批，替代旧版盲覆盖实现）：
- 先出计划再落盘：--dry-run 只打印 [create]/[refresh]/[append]/[noop]/[skip]/[conflict]，不写任何文件。
- 绝不覆盖宿主既有文件：AGENTS.md / .cursor/rules / CLAUDE.md / copilot 只写
  「托管块」（agentflow:begin/end 标记之间），标记外的字节一律不动；无标记的既有文件
  只追加块或跳过并报告，由人决定。
- 载体只用各宿主官方入口：zcode/codex 读 <repo>/AGENTS.md，cursor 读
  .cursor/rules/*.mdc（frontmatter 在最前，标记在正文内），claude 读 <repo>/CLAUDE.md
  （一行 @AGENTS.md 指针），copilot 读 .github/copilot-instructions.md。
  旧版的 .zcode/rules/ 与 .claude/rules/ 不在官方载体清单，已移除。
- 工程内容标准复制到 <target>/.agentflow/standards/，带来源头（源路径+版本）；
  用户改过的托管资产不覆盖，报 conflict 由人裁决（--refresh-assets 显式接管）。
- .agentflow/manifest.json 记录版本与逐文件 sha256；--check 校验漂移。
- --self-test 在临时目录跑完整矩阵（干净安装 / 幂等重跑 / 追加不覆盖 / 标记块刷新 /
  外来文件保护 / 用户改动保护 / dry-run 零写入 / check 漂移检出）。

用法：
  python3 init_workspace.py <目标仓根> [--hosts zcode,codex,cursor,claude,copilot]
                            [--dry-run] [--check] [--refresh-assets]
                            [--agentflow <skill目录>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

END_MARK = "<!-- agentflow:end -->"
BEGIN_PREFIX = "<!-- agentflow:begin "
OURS_TAG = "managed by init_workspace.py"  # 区分本脚本块与宿主全局块（global-rules）
ASSET_HEADER_TPL = (
    "<!-- agentflow-managed source:{source} version:{version} -->"
)

CARRIERS = {
    "zcode": ("agents", Path("AGENTS.md")),
    "codex": ("agents", Path("AGENTS.md")),  # 与 zcode 同一文件，去重后只处理一次
    "cursor": ("mdc", Path(".cursor/rules/agentflow.mdc")),
    "claude": ("pointer", Path("CLAUDE.md")),
    "copilot": ("agents", Path(".github/copilot-instructions.md")),
}

CURSOR_FRONTMATTER = (
    "---\n"
    "description: Agentflow 项目规则（工程底线 / 主链路 / 门禁派遣）\n"
    "alwaysApply: true\n"
    "---\n\n"
)

CLAUDE_POINTER_TPL = (
    "<!-- agentflow:claude-pointer v{version} {tag} -->\n"
    "@AGENTS.md\n"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_plugin_version(skill_root: Path) -> str:
    """从 skill 目录向上找 plugin.json 取版本号；找不到返回 unknown。"""
    probe = skill_root.resolve()
    for _ in range(5):
        candidate = probe / "plugin.json"
        if candidate.is_file():
            try:
                return str(json.loads(candidate.read_text(encoding="utf-8")).get("version", "unknown"))
            except (json.JSONDecodeError, OSError):
                return "unknown"
        if probe.parent == probe:
            break
        probe = probe.parent
    return "unknown"


def managed_block(version: str, body: str) -> str:
    begin = f"{BEGIN_PREFIX}v{version} {OURS_TAG} -->"
    return f"{begin}\n{body.rstrip()}\n{END_MARK}\n"


def split_managed_block(text: str):
    """返回 (status, begin_idx, end_idx)。status ∈ ours / foreign / none / malformed。"""
    begin_idx = text.find(BEGIN_PREFIX)
    if begin_idx == -1:
        return "none", -1, -1
    end_idx = text.find(END_MARK, begin_idx)
    if end_idx == -1:
        return "malformed", begin_idx, -1
    begin_line_end = text.find("-->", begin_idx)
    if begin_line_end == -1:
        return "malformed", begin_idx, -1
    if OURS_TAG in text[begin_idx:begin_line_end]:
        return "ours", begin_idx, end_idx + len(END_MARK)
    return "foreign", begin_idx, end_idx + len(END_MARK)


def render_mdc(version: str, body: str) -> str:
    # frontmatter 必须在文件最前；管理标记放正文内，不能插在 frontmatter 之前
    return CURSOR_FRONTMATTER + managed_block(version, body)


def render_agents(version: str, body: str) -> str:
    return managed_block(version, body)


def asset_rendered(source_text: str, version: str, source_rel: str) -> str:
    header = ASSET_HEADER_TPL.format(source=source_rel, version=version)
    return f"{header}\n{source_text.rstrip()}\n"


class Plan:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, action: str, path: Path, detail: str = "") -> None:
        self.items.append({"action": action, "path": str(path), "detail": detail})

    def summary_line(self) -> str:
        counts: dict[str, int] = {}
        for it in self.items:
            counts[it["action"]] = counts.get(it["action"], 0) + 1
        return "，".join(f"{k}×{v}" for k, v in sorted(counts.items()))


def build_plan(target: Path, skill_root: Path, hosts: list[str], version: str,
               refresh_assets: bool, manifest: dict | None) -> tuple[Plan, dict]:
    """扫描目标仓，产出计划与所需写内容（path -> bytes），不触碰文件系统（只读）。"""
    plan = Plan()
    writes: dict[Path, bytes] = {}

    maker_src = skill_root / "templates" / "host" / "maker.md"
    standards_src = skill_root / "references" / "standards"
    if not maker_src.is_file() or not standards_src.is_dir():
        plan.add("error", skill_root, "找不到 templates/host/maker.md 或 references/standards/")
        return plan, writes

    maker_body = maker_src.read_text(encoding="utf-8")

    old_files: dict[str, str] = {}
    if manifest:
        old_files = manifest.get("files", {})

    # 1) 资产：standards/*.md
    for src in sorted(standards_src.glob("*.md")):
        rel = f".agentflow/standards/{src.name}"
        dst = target / rel
        rendered = asset_rendered(src.read_text(encoding="utf-8"), version,
                                  f"skills/agentflow/references/standards/{src.name}")
        if not dst.exists():
            plan.add("create", dst)
            writes[dst] = rendered.encode("utf-8")
            continue
        current = dst.read_text(encoding="utf-8")
        if current == rendered:
            plan.add("noop", dst, "内容一致")
            continue
        recorded = old_files.get(rel)
        ours_header = current.startswith("<!-- agentflow-managed ")
        if (recorded is not None and recorded == sha256_bytes(dst.read_bytes())) or (recorded is None and ours_header and refresh_assets):
            plan.add("refresh-asset", dst, f"旧版本 {manifest.get('version') if manifest else '?'} -> {version}" if manifest else "按 --refresh-assets 接管")
            writes[dst] = rendered.encode("utf-8")
        else:
            if recorded is not None:
                reason = "用户改动过托管资产（sha 与 manifest 不符）"
            elif ours_header:
                reason = "托管资产不在 manifest 中（manifest 缺失或被重建）"
            else:
                reason = "存在无来源头的同名文件"
            plan.add("conflict", dst, f"{reason}；确认后用 --refresh-assets 接管或手工合并")

    # 2) 宿主载体（去重：zcode/codex 共用 AGENTS.md）
    seen_paths: set[Path] = set()
    for host in hosts:
        kind, rel = CARRIERS.get(host, (None, None))
        if kind is None:
            plan.add("skip", target / f"<未知宿主 {host}>", "不在支持列表")
            continue
        dst = target / rel
        if dst in seen_paths:
            continue
        seen_paths.add(dst)

        if kind == "agents":
            body = maker_body
            if not dst.exists():
                plan.add("create", dst, "新建含托管块的入口")
                writes[dst] = (managed_block(version, body)).encode("utf-8")
                continue
            text = dst.read_text(encoding="utf-8")
            status, b, e = split_managed_block(text)
            if status == "ours":
                new_text = text[:b] + managed_block(version, body).rstrip("\n") + text[e:]
                if new_text == text:
                    plan.add("noop", dst, "托管块已最新")
                else:
                    plan.add("refresh-block", dst, "替换标记内内容，标记外字节不动")
                    writes[dst] = new_text.encode("utf-8")
            elif status == "malformed":
                plan.add("conflict", dst, "发现残缺的 agentflow 标记块，需人工处理")
            elif status == "foreign":
                plan.add("append-block", dst, "既有文件含其他 agentflow 块（如全局规则），在文末追加本项目块")
                writes[dst] = (text.rstrip() + "\n\n" + managed_block(version, body)).encode("utf-8")
            else:
                plan.add("append-block", dst, "既有 AGENTS.md 无托管块，在文末追加（原字节不动）")
                writes[dst] = (text.rstrip() + "\n\n" + managed_block(version, body)).encode("utf-8")

        elif kind == "mdc":
            rendered = render_mdc(version, maker_body)
            if not dst.exists():
                plan.add("create", dst)
                writes[dst] = rendered.encode("utf-8")
                continue
            text = dst.read_text(encoding="utf-8")
            status, b, e = split_managed_block(text)
            if status == "ours" and text != rendered:
                plan.add("refresh-block", dst, "frontmatter + 标记块整体重渲染（该文件整体为生成物）")
                writes[dst] = rendered.encode("utf-8")
            elif status == "ours":
                plan.add("noop", dst, "内容一致")
            elif status == "malformed":
                plan.add("conflict", dst, "残缺标记块，需人工处理")
            else:
                plan.add("conflict", dst, "已存在非本脚本生成的 mdc，不覆盖")

        elif kind == "pointer":
            rendered = CLAUDE_POINTER_TPL.format(version=version, tag=OURS_TAG)
            if not dst.exists():
                plan.add("create", dst, "一行 @AGENTS.md 指针")
                writes[dst] = rendered.encode("utf-8")
                continue
            text = dst.read_text(encoding="utf-8")
            if text == rendered:
                plan.add("noop", dst, "内容一致")
            elif OURS_TAG in text:
                plan.add("refresh-block", dst, "更新指针版本注释")
                writes[dst] = rendered.encode("utf-8")
            else:
                plan.add("conflict", dst, "已存在用户 CLAUDE.md，不覆盖；可手工加一行 @AGENTS.md")

    return plan, writes


def apply_plan(target: Path, plan: Plan, writes: dict[Path, bytes], dry_run: bool) -> int:
    conflicts = 0
    for it in plan.items:
        mark = {"create": "[create]", "refresh-block": "[refresh]", "refresh-asset": "[refresh]",
                "append-block": "[append]", "noop": "[noop]", "skip": "[skip]",
                "conflict": "[conflict]", "error": "[error]"}[it["action"]]
        detail = f" — {it['detail']}" if it["detail"] else ""
        print(f"{mark} {it['path']}{detail}")
        if it["action"] == "conflict":
            conflicts += 1
    if dry_run:
        print(f"\n[dry-run] 计划：{plan.summary_line()}；未写入任何文件。")
        return 0
    for path, data in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return conflicts


def write_manifest(target: Path, version: str, hosts: list[str], plan: Plan) -> Path:
    files: dict[str, str] = {}
    scopes: dict[str, str] = {}
    for it in plan.items:
        p = Path(it["path"])
        if p.is_file() and (it["action"] in {"create", "refresh-block", "refresh-asset", "append-block", "noop"}):
            rel = str(p.relative_to(target))
            text = p.read_text(encoding="utf-8", errors="replace")
            status, b, e = split_managed_block(text)
            if status == "ours":
                # 只钉托管块区段：标记外的字节归用户，不应触发 --check 漂移
                files[rel] = sha256_bytes(text[b:e].encode("utf-8"))
                scopes[rel] = "block"
            else:
                files[rel] = sha256_bytes(p.read_bytes())
                scopes[rel] = "file"
    mpath = target / ".agentflow" / "manifest.json"
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps({
        "tool": "agentflow-init",
        "version": version,
        "installed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "hosts": hosts,
        "files": files,
        "scopes": scopes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return mpath


def run_check(target: Path) -> int:
    mpath = target / ".agentflow" / "manifest.json"
    if not mpath.is_file():
        print(f"[fail] {mpath} 不存在：本项目未安装或 manifest 被删")
        return 1
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    scopes = manifest.get("scopes", {})
    drift = 0
    for rel, recorded in sorted(manifest.get("files", {}).items()):
        p = target / rel
        if not p.is_file():
            print(f"[drift] 缺失 {rel}")
            drift += 1
            continue
        if scopes.get(rel) == "block":
            text = p.read_text(encoding="utf-8", errors="replace")
            status, b, e = split_managed_block(text)
            if status != "ours":
                print(f"[drift] 托管块缺失 {rel}")
                drift += 1
            elif sha256_bytes(text[b:e].encode("utf-8")) != recorded:
                print(f"[drift] 托管块内容变化 {rel}")
                drift += 1
        elif sha256_bytes(p.read_bytes()) != recorded:
            print(f"[drift] 内容变化 {rel}")
            drift += 1
    ag = target / "AGENTS.md"
    if ag.is_file() and split_managed_block(ag.read_text(encoding="utf-8"))[0] != "ours":
        print("[drift] AGENTS.md 缺少本项目托管块")
        drift += 1
    if drift:
        print(f"[fail] {drift} 项漂移（安装版本 {manifest.get('version')}）")
        return 1
    print(f"[ok] 无漂移（安装版本 {manifest.get('version')}，{len(manifest.get('files', {}))} 个文件）")
    return 0


def load_manifest(target: Path) -> dict | None:
    mpath = target / ".agentflow" / "manifest.json"
    if not mpath.is_file():
        return None
    try:
        return json.loads(mpath.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- self-test

def _self_test() -> int:
    import shutil as _sh
    import tempfile

    skill_root = Path(__file__).resolve().parents[1]
    results: list[tuple[str, bool, str]] = []

    def scenario(name: str):
        def deco(fn):
            base = Path(tempfile.mkdtemp(prefix="af-init-selftest-"))
            work = base / "repo"
            work.mkdir()
            try:
                fn(work)
                results.append((name, True, ""))
            except AssertionError as exc:
                results.append((name, False, str(exc)))
            finally:
                _sh.rmtree(base, ignore_errors=True)
            return fn
        return deco

    def install(work: Path, *extra: str) -> None:
        argv = [str(work), "--agentflow", str(skill_root), *extra]
        orig = sys.argv
        sys.argv = ["init_workspace.py", *argv]
        try:
            main()
        finally:
            sys.argv = orig

    @scenario("干净安装：入口/资产/manifest/cursor frontmatter 齐备")
    def _(work: Path) -> None:
        install(work)
        ag = (work / "AGENTS.md").read_text(encoding="utf-8")
        assert ag.startswith("<!-- agentflow:begin "), "AGENTS.md 未以托管块开头"
        assert ".agentflow/standards/server-side.md" in ag, "maker 未引用本地 standards 路径"
        assert (work / ".agentflow" / "standards" / "server-side.md").is_file()
        assert (work / ".agentflow" / "manifest.json").is_file()
        mdc = (work / ".cursor" / "rules" / "agentflow.mdc").read_text(encoding="utf-8")
        assert mdc.startswith("---\n"), "cursor frontmatter 不在文件最前"
        assert "alwaysApply: true" in mdc and OURS_TAG in mdc
        cl = (work / "CLAUDE.md").read_text(encoding="utf-8")
        assert cl.strip().splitlines()[-1] == "@AGENTS.md", "CLAUDE.md 指针缺失"
        assert ".zcode/rules" not in str(sorted(p.name for p in work.rglob('*'))), "不应再生成 .zcode/rules"

    @scenario("幂等重跑：二次安装全部 noop，字节不变")
    def _(work: Path) -> None:
        install(work)
        before = {p: p.read_bytes() for p in sorted(work.rglob("*")) if p.is_file()}
        install(work)
        after = {p: p.read_bytes() for p in sorted(work.rglob("*")) if p.is_file()}
        assert before == after, "重跑改变了文件字节"

    @scenario("既有 AGENTS.md（无标记）：追加块，原字节保留为前缀")
    def _(work: Path) -> None:
        original = "# 我的仓规则\n\n- 不要动 CI 配置\n"
        (work / "AGENTS.md").write_text(original, encoding="utf-8")
        install(work)
        text = (work / "AGENTS.md").read_text(encoding="utf-8")
        assert text.startswith(original), "原有内容被改动"
        assert OURS_TAG in text and END_MARK in text

    @scenario("标记块刷新：标记外字节不动，块内更新")
    def _(work: Path) -> None:
        install(work)
        ag = work / "AGENTS.md"
        text = ag.read_text(encoding="utf-8")
        status, b, e = split_managed_block(text)
        assert status == "ours"
        ag.write_text(text[:b] + "TAIL\n" + text[e:] + "\n尾部附录\n", encoding="utf-8")
        install(work)
        new = ag.read_text(encoding="utf-8")
        assert "尾部附录" in new, "标记外内容丢失"
        status, b, e = split_managed_block(new)
        assert status == "ours" and ".agentflow/standards/server-side.md" in new[b:e]

    @scenario("外来同名资产：不覆盖，报 conflict")
    def _(work: Path) -> None:
        std = work / ".agentflow" / "standards"
        std.mkdir(parents=True)
        (std / "server-side.md").write_text("# 团队自有规范，勿覆盖\n", encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            install(work)
        assert (std / "server-side.md").read_text(encoding="utf-8") == "# 团队自有规范，勿覆盖\n", "外来文件被覆盖"
        assert "conflict" in buf.getvalue()

    @scenario("用户改过托管资产：默认不覆盖；--refresh-assets 显式接管")
    def _(work: Path) -> None:
        install(work)
        p = work / ".agentflow" / "standards" / "server-side.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n<!-- 人工补充 -->\n", encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            install(work)
        assert "人工补充" in p.read_text(encoding="utf-8"), "默认模式下用户改动丢失"
        assert "conflict" in buf.getvalue()
        with contextlib.redirect_stdout(io.StringIO()):
            install(work, "--refresh-assets")
        assert "人工补充" not in p.read_text(encoding="utf-8"), "显式接管后应刷新"

    @scenario("dry-run：零写入")
    def _(work: Path) -> None:
        install(work, "--dry-run")
        assert not (work / "AGENTS.md").exists(), "dry-run 写入了文件"
        assert not (work / ".agentflow").exists()

    @scenario("--check：未装报错、装后通过、块外追加不算漂移、块内与资产篡改检出")
    def _(work: Path) -> None:
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            assert run_check(work) == 1, "未安装时 --check 应失败"
            install(work)
            assert run_check(work) == 0, "刚安装完 --check 应通过"
            ag = work / "AGENTS.md"
            ag.write_text(ag.read_text(encoding="utf-8") + "\n用户自己的附录行\n", encoding="utf-8")
            assert run_check(work) == 0, "托管块外追加用户内容不应报漂移"
            ag.write_text(ag.read_text(encoding="utf-8").replace("server-side.md", "server-side-X.md"),
                          encoding="utf-8")
            assert run_check(work) == 1, "托管块内篡改应报漂移"
            install(work, "--refresh-assets")  # 刷新块内内容，恢复基线
            assert run_check(work) == 0, "刷新后 --check 应恢复通过"
            p = work / ".agentflow" / "standards" / "data-model.md"
            p.write_text("# tampered\n", encoding="utf-8")
            assert run_check(work) == 1, "资产篡改后 --check 应报漂移"

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="agentflow 项目侧安全安装器（固定件 copy，AI 填项目事实）")
    ap.add_argument("target", nargs="?", help="目标仓根目录（--self-test 时可省略）")
    ap.add_argument("--agentflow", default=None, help="agentflow skill 目录（默认：脚本上两级）")
    ap.add_argument("--hosts", default="zcode,codex,cursor,claude,copilot",
                    help="逗号分隔宿主：zcode,codex,cursor,claude,copilot")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不写文件")
    ap.add_argument("--check", action="store_true", help="校验已安装内容与 manifest 是否漂移")
    ap.add_argument("--refresh-assets", action="store_true",
                    help="托管资产被用户改动时也刷新（默认报 conflict 不覆盖）")
    ap.add_argument("--self-test", action="store_true", help="在临时目录跑安装矩阵自测")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not args.target:
        ap.error("需要目标仓根目录（或 --self-test）")

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"[错误] 目标仓不存在：{target}", file=sys.stderr)
        return 2
    if args.check:
        return run_check(target)

    skill_root = Path(args.agentflow).resolve() if args.agentflow else Path(__file__).resolve().parents[1]
    version = find_plugin_version(skill_root)
    hosts = [h.strip() for h in args.hosts.split(",") if h.strip()]
    manifest = load_manifest(target)

    plan, writes = build_plan(target, skill_root, hosts, version, args.refresh_assets, manifest)
    conflicts = apply_plan(target, plan, writes, args.dry_run)
    if not args.dry_run:
        mpath = write_manifest(target, version, hosts, plan)
        print(f"\n[ok] manifest -> {mpath}")
    if conflicts:
        print(f"\n[注意] {conflicts} 项 conflict 待人工处理（其余已按计划落盘）")
    print("后续：让 AI 读目标仓现状，回填 AGENTS.md 的项目事实段与 engineering-baseline.md（探测命令必须带超时）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
