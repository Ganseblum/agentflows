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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 10):
    raise SystemExit("init_workspace.py 需要 Python 3.10 或以上版本，请检查 python3 --version")
sys.dont_write_bytecode = True

from workflow_lib.managed import file_state, locate_managed_block, write_managed_file
from workflow_lib.snapshots import WorkflowError, no_symlinks, project_path

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

# 工程基线骨架的落点。收尾提示一直让 AI「回填 engineering-baseline.md」，但脚本从不创建它，
# 照提示做的人会去找一个不存在的文件（2026-11-04 核对发现）。现在脚本建骨架，用户填事实，
# 脚本永不接管：这是目标仓的实测记录，不是托管资产。
BASELINE_REL = Path(".agentflow") / "engineering-baseline.md"
MANIFEST_EXCLUDED = {str(BASELINE_REL)}

CURSOR_FRONTMATTER = (
    "---\n"
    "description: Agentflow 项目规则（工程底线 / 主链路 / 质量校验）\n"
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


def owned_span(data: bytes) -> tuple[int, int] | None:
    return locate_managed_block(
        data, f"{BEGIN_PREFIX}v0 {OURS_TAG} -->".encode(), END_MARK.encode(),
        begin_prefix=BEGIN_PREFIX.encode(), owner=OURS_TAG.encode(),
    )


def split_managed_block(text: str):
    """Compatibility wrapper: text offsets, scanning every owner rather than only the first."""
    data = text.encode("utf-8")
    try:
        span = owned_span(data)
    except WorkflowError:
        return "malformed", -1, -1
    if span is not None:
        b, e = span
        return "ours", len(data[:b].decode("utf-8")), len(data[:e].decode("utf-8"))
    return ("foreign" if BEGIN_PREFIX in text else "none"), -1, -1


def legacy_pointer_span(data: bytes) -> tuple[int, int] | None:
    """Only claim one complete legacy comment and its immediately adjacent import."""
    lines = data.split(b"\n")
    offset = 0
    found = None
    for index, raw in enumerate(lines):
        line = raw.removesuffix(b"\r")
        if line.startswith(b"<!-- agentflow:claude-pointer ") and OURS_TAG.encode() in line:
            if (not line.endswith(b"-->") or found is not None
                    or index + 1 >= len(lines) or lines[index + 1].removesuffix(b"\r") != b"@AGENTS.md"):
                raise WorkflowError("invalid-markers", "Claude legacy pointer is incomplete or duplicated", 3)
            finish = offset + len(raw) + 1 + len(b"@AGENTS.md")
            found = offset, finish
        offset += len(raw) + 1
    return found


def replace_carrier(data: bytes, version: str, body: str, kind: str) -> bytes:
    span = owned_span(data)
    if kind == "pointer":
        legacy = legacy_pointer_span(data)
        if span is not None and legacy is not None:
            raise WorkflowError("invalid-markers", "Claude pointer ownership is duplicated", 3)
        span = span if span is not None else legacy
    block = managed_block(version, body).encode().removesuffix(b"\n")
    if span is not None:
        b, e = span
        return data[:b] + block + data[e:]
    if kind == "mdc":
        raise WorkflowError("unowned-carrier", "已存在非本脚本生成的 mdc，不覆盖", 3)
    if kind == "pointer":
        raise WorkflowError("unowned-carrier", "已存在用户 CLAUDE.md，无法确定指针归属", 3)
    separator = b"\n" if data and not data.endswith(b"\n") else b""
    return data + separator + block + b"\n"


def merged_hosts(hosts: list[str], manifest: dict | None) -> list[str]:
    result = list(dict.fromkeys([*(manifest or {}).get("hosts", []), *hosts]))
    if not result or any(host not in CARRIERS for host in result):
        raise WorkflowError("invalid-hosts", f"需要至少一个已支持宿主：{result}")
    return result


def carrier_targets(hosts: list[str]) -> dict[Path, str]:
    result = {CARRIERS[host][1]: CARRIERS[host][0] for host in hosts}
    if "claude" in hosts:
        result[Path("AGENTS.md")] = "agents"
    return result


def expected_files(hosts: list[str]) -> set[str]:
    return {str(rel) for rel in carrier_targets(hosts)} | {
        f".agentflow/standards/{name}.md" for name in ("data-model", "frontend", "server-side")
    }


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
        self.expected: dict[Path, dict] = {}
        self.applied: list[dict] = []

    def add(self, action: str, path: Path, detail: str = "") -> None:
        self.items.append({"action": action, "path": str(path), "detail": detail})

    def summary_line(self) -> str:
        counts: dict[str, int] = {}
        for it in self.items:
            counts[it["action"]] = counts.get(it["action"], 0) + 1
        return "，".join(f"{k}×{v}" for k, v in sorted(counts.items()))


def build_plan(target: Path, skill_root: Path, hosts: list[str], version: str,
               refresh_assets: bool, manifest: dict | None) -> tuple[Plan, dict]:
    """Read and validate the entire plan before allowing any filesystem writes."""
    target = no_symlinks(target)
    plan = Plan()
    writes: dict[Path, bytes] = {}
    hosts = merged_hosts(hosts, manifest)
    maker_src = skill_root / "templates" / "host" / "maker.md"
    standards_src = skill_root / "references" / "standards"
    sources = sorted(standards_src.glob("*.md"))
    baseline_src = skill_root / "templates" / "engineering" / "baseline.md"
    if (not maker_src.is_file() or not baseline_src.is_file()
            or not {"data-model.md", "frontend.md", "server-side.md"}.issubset({p.name for p in sources})):
        plan.add("error", skill_root, "找不到 maker / baseline 模板或完整 standards 来源")
        return plan, writes
    maker_body = maker_src.read_text(encoding="utf-8")
    old_files = (manifest or {}).get("files", {})
    old_scopes = (manifest or {}).get("scopes", {})
    assets = {f".agentflow/standards/{src.name}": src for src in sources}
    carriers = carrier_targets(hosts)
    desired_paths = set(assets) | {str(rel) for rel in carriers} | {str(BASELINE_REL)}
    # Include the manifest itself and old records in path/state preflight. A symlink,
    # directory collision or missing retired record must not fail after partial writes.
    for rel in sorted(desired_paths | set(old_files) | {".agentflow/manifest.json"}):
        dst = project_path(target, rel)
        plan.expected[dst] = file_state(dst)
        for parent in dst.parents:
            if parent == target:
                break
            if parent.exists() and not parent.is_dir():
                raise WorkflowError("invalid-path", f"输出祖先不是目录：{parent}", 3)

    def current(dst: Path) -> bytes | None:
        state = plan.expected[dst]
        data = dst.read_bytes() if state["exists"] else None
        if file_state(dst) != state:
            raise WorkflowError("target-drift", f"规划期间文件变化：{dst}", 3)
        return data

    for rel, src in assets.items():
        dst = project_path(target, rel)
        source_rel = f"skills/agentflow/references/standards/{src.name}"
        rendered = asset_rendered(src.read_text(encoding="utf-8"), version, source_rel).encode()
        data = current(dst)
        if data is None:
            plan.add("create", dst)
            writes[dst] = rendered
            continue
        if data == rendered:
            plan.add("noop", dst, "内容一致")
            continue
        recorded = old_files.get(rel)
        header = re.fullmatch(
            rb"<!-- agentflow-managed source:" + re.escape(source_rel.encode()) + rb" version:[^\r\n]+ -->",
            data.split(b"\n", 1)[0].removesuffix(b"\r"),
        )
        unchanged = recorded is not None and old_scopes.get(rel, "file") == "file" and recorded == sha256_bytes(data)
        if unchanged or (refresh_assets and (recorded is not None or header is not None)):
            plan.add("refresh-asset", dst, f"更新来源至 {version}" if unchanged else "按 --refresh-assets 接管已识别托管资产")
            writes[dst] = rendered
        else:
            reason = "用户改动过托管资产" if recorded is not None else "同名文件无可接管来源" if header is None else "托管资产不在 manifest 中"
            plan.add("conflict", dst, reason + "；需手工合并或显式接管已识别资产")

    baseline_dst = project_path(target, str(BASELINE_REL))
    if plan.expected[baseline_dst]["exists"]:
        plan.add("noop", baseline_dst, "已有工程基线，不覆盖")
    else:
        plan.add("create", baseline_dst, "工程基线骨架（待按目标仓实测回填）")
        writes[baseline_dst] = baseline_src.read_bytes()

    for rel, kind in carriers.items():
        dst = project_path(target, str(rel))
        data = current(dst)
        body = "@AGENTS.md" if kind == "pointer" else maker_body
        if data is None:
            rendered = render_mdc(version, body) if kind == "mdc" else managed_block(version, body)
            plan.add("create", dst, "新建含托管块的入口")
            writes[dst] = rendered.encode()
            continue
        try:
            replacement = replace_carrier(data, version, body, kind)
        except WorkflowError as exc:
            plan.add("conflict", dst, f"{exc.kind}: {exc}")
            continue
        if replacement == data:
            plan.add("noop", dst, "托管块已最新，块外字节保留")
        else:
            action = "refresh-block" if owned_span(data) is not None or kind == "pointer" else "append-block"
            plan.add(action, dst, "仅更新自有区段，块外字节不动")
            writes[dst] = replacement

    # Retain old manifest entries even when the selected hosts or source set shrinks.
    for rel in sorted(set(old_files) - desired_paths):
        dst = project_path(target, rel)
        data = current(dst)
        try:
            digest, _ = content_digest(data, old_scopes.get(rel, "file")) if data is not None else (None, None)
        except WorkflowError:
            digest = None
        if digest != old_files[rel]:
            plan.add("conflict", dst, "旧托管记录缺失或漂移，不能隐式丢弃")
        else:
            plan.add("noop", dst, "保留旧托管记录")
    return plan, writes


def apply_plan(target: Path, plan: Plan, writes: dict[Path, bytes], dry_run: bool) -> int:
    target = no_symlinks(target)
    problems = 0
    for it in plan.items:
        mark = {"create": "[create]", "refresh-block": "[refresh]", "refresh-asset": "[refresh]",
                "append-block": "[append]", "noop": "[noop]", "skip": "[skip]",
                "conflict": "[conflict]", "error": "[error]"}[it["action"]]
        detail = f" — {it['detail']}" if it["detail"] else ""
        print(f"{mark} {it['path']}{detail}")
        problems += it["action"] in {"conflict", "error"}
    if problems or dry_run:
        print(f"\n[{'dry-run' if dry_run else 'fail'}] 计划：{plan.summary_line()}；未写入任何文件。")
        return problems
    # Check ALL inputs again before the first mkdir, backup, or file write.
    for path, expected in plan.expected.items():
        if file_state(path) != expected:
            raise WorkflowError("target-drift", f"预检后目标变化：{path}", 3)
    for path, data in writes.items():
        path = project_path(target, str(path.relative_to(target)))
        path.parent.mkdir(parents=True, exist_ok=True)
        result = write_managed_file(path, data, plan.expected[path])
        plan.applied.append(result)
        print(f"[written] {result['target']} backup={result['backup']}")
    return 0


def content_digest(data: bytes, scope: str) -> tuple[str, str]:
    if scope == "block":
        span = owned_span(data)
        if span is None:
            raise WorkflowError("missing-block", "本项目托管块缺失", 3)
        data = data[span[0]:span[1]]
    return sha256_bytes(data), scope


def manifest_data(target: Path, version: str, hosts: list[str], plan: Plan,
                  writes: dict[Path, bytes], old: dict | None) -> bytes:
    target = no_symlinks(target)
    files = dict((old or {}).get("files", {}))
    scopes = dict((old or {}).get("scopes", {}))
    carriers = {str(rel) for rel in carrier_targets(hosts)}
    for it in plan.items:
        if it["action"] in {"conflict", "error", "skip"}:
            raise WorkflowError("invalid-plan", "不能为未完成计划生成 manifest", 3)
        path = Path(it["path"])
        rel = str(path.relative_to(target))
        if rel in MANIFEST_EXCLUDED:
            continue
        data = writes[path] if path in writes else path.read_bytes()
        scope = "block" if rel in carriers else scopes.get(rel, "file")
        files[rel], scopes[rel] = content_digest(data, scope)
    missing = expected_files(hosts) - set(files)
    if missing:
        raise WorkflowError("incomplete-manifest", f"安装清单缺少：{sorted(missing)}", 3)
    value = {
        "tool": "agentflow-init", "version": version,
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hosts": hosts, "files": files, "scopes": scopes,
    }
    # Preserve bytes (including installed_at) on a true noop reinstall.
    if old and all(value[key] == old.get(key) for key in ("tool", "version", "hosts", "files", "scopes")):
        return project_path(target, ".agentflow/manifest.json").read_bytes()
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def write_manifest(target: Path, version: str, hosts: list[str], plan: Plan,
                   data: bytes | None = None) -> Path:
    target = no_symlinks(target)
    mpath = project_path(target, ".agentflow/manifest.json")
    if data is None:  # Legacy callers can still serialize an already applied plan.
        data = manifest_data(target, version, hosts, plan, {}, load_manifest(target))
    expected = plan.expected.get(mpath, file_state(mpath))
    mpath.parent.mkdir(parents=True, exist_ok=True)
    result = write_managed_file(mpath, data, expected)
    if result["action"] != "same":
        plan.applied.append(result)
        print(f"[written] {result['target']} backup={result['backup']}")
    return mpath


def run_check(target: Path) -> int:
    try:
        target = no_symlinks(target)
        manifest = load_manifest(target)
        if manifest is None:
            print(f"[fail] {target / '.agentflow/manifest.json'} 不存在：本项目未安装或 manifest 被删")
            return 1
        scopes = manifest.get("scopes", {})
        drift = 0
        required = expected_files(manifest["hosts"])
        for rel in sorted(required - set(manifest["files"])):
            print(f"[drift] manifest 缺少期望文件 {rel}")
            drift += 1
        for rel, recorded in sorted(manifest["files"].items()):
            path = project_path(target, rel)
            if not path.is_file():
                print(f"[drift] 缺失 {rel}")
                drift += 1
                continue
            data = path.read_bytes()
            try:
                digest, _ = content_digest(data, scopes.get(rel, "file"))
                if rel in {str(p) for p in carrier_targets(manifest["hosts"])}:
                    if owned_span(data) is None and not (rel == "CLAUDE.md" and legacy_pointer_span(data) is not None):
                        raise WorkflowError("missing-block", "本项目入口缺失", 3)
                if rel == "CLAUDE.md" and "claude" in manifest["hosts"]:
                    span = owned_span(data)
                    if span is not None and b"@AGENTS.md" not in data[span[0]:span[1]].splitlines():
                        raise WorkflowError("missing-pointer", "Claude 缺少 @AGENTS.md 引用", 3)
            except WorkflowError as exc:
                print(f"[drift] {rel}: {exc}")
                drift += 1
                continue
            if digest != recorded:
                print(f"[drift] 内容变化 {rel}")
                drift += 1
        if drift:
            print(f"[fail] {drift} 项漂移（安装版本 {manifest['version']}）")
            return 1
        print(f"[ok] 无漂移（安装版本 {manifest['version']}，{len(manifest['files'])} 个文件）")
        return 0
    except (WorkflowError, OSError, UnicodeError) as exc:
        print(f"[error] {getattr(exc, 'kind', 'read-failed')}: {exc}", file=sys.stderr)
        return 1


def load_manifest(target: Path) -> dict | None:
    """Fail explicitly on malformed existing manifests; never reinterpret as uninstalled."""
    target = no_symlinks(target)
    mpath = project_path(target, ".agentflow/manifest.json")
    if not mpath.exists():
        return None
    try:
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"重复键：{key}")
                result[key] = value
            return result
        value = json.loads(mpath.read_bytes(), object_pairs_hook=unique_object)
        if not isinstance(value, dict) or value.get("tool") != "agentflow-init":
            raise ValueError("需要 agentflow-init manifest 对象")
        if not isinstance(value.get("version"), str) or not value["version"]:
            raise ValueError("version 必须是非空字符串")
        hosts = value.get("hosts")
        if (not isinstance(hosts, list) or not hosts or any(not isinstance(host, str) or host not in CARRIERS for host in hosts)
                or len(hosts) != len(set(hosts))):
            raise ValueError("hosts 必须为非空且不重复的受支持宿主列表")
        if not isinstance(value.get("installed_at"), str):
            raise ValueError("installed_at 必须是时间字符串")
        datetime.fromisoformat(value["installed_at"])
        files, scopes = value.get("files"), value.get("scopes", {})
        if not isinstance(files, dict) or not files or not isinstance(scopes, dict):
            raise ValueError("files 必须为非空对象，scopes 必须为对象")
        if set(scopes) - set(files):
            raise ValueError("scopes 不能含 files 以外的路径")
        for rel, digest in files.items():
            project_path(target, rel)
            if rel in MANIFEST_EXCLUDED or rel == ".agentflow/manifest.json":
                raise ValueError(f"不能追踪用户基线或 manifest 自身：{rel}")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError(f"非法 sha256：{rel}")
            if scopes.get(rel, "file") not in {"file", "block"}:
                raise ValueError(f"非法 scope：{rel}")
        return value
    except (ValueError, TypeError, OSError, UnicodeError) as exc:
        raise WorkflowError("invalid-manifest", f"manifest 损坏：{mpath}: {exc}", 2) from exc


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
            except Exception as exc:
                results.append((name, False, f"{type(exc).__name__}: {exc}"))
            finally:
                _sh.rmtree(base, ignore_errors=True)
            return fn
        return deco

    def install(work: Path, *extra: str) -> int:
        argv = [str(work), "--agentflow", str(skill_root), *extra]
        orig = sys.argv
        sys.argv = ["init_workspace.py", *argv]
        try:
            return main()
        finally:
            sys.argv = orig

    def snapshot(work: Path) -> dict:
        return {str(p.relative_to(work)): ("link", str(p.readlink())) if p.is_symlink()
                else ("file", p.read_bytes()) if p.is_file() else ("dir",)
                for p in work.rglob("*")}

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
        cl = (work / "CLAUDE.md").read_bytes()
        span = owned_span(cl)
        assert span is not None and b"@AGENTS.md" in cl[span[0]:span[1]].splitlines(), "CLAUDE.md 指针缺失"
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

    @scenario("普通 AGENTS：CRLF 与无换行尾空白逐字保留")
    def _(work: Path) -> None:
        original = b"# Team\r\nKEEP \t  "
        (work / "AGENTS.md").write_bytes(original)
        assert install(work, "--hosts", "zcode") == 0
        assert (work / "AGENTS.md").read_bytes().startswith(original)

    @scenario("各宿主块外前后哨兵/CRLF 保留，二次安装零变化")
    def _(work: Path) -> None:
        assert install(work) == 0
        for rel in carrier_targets(list(CARRIERS)):
            path = work / rel
            data = path.read_bytes().replace(b"\n", b"\r\n")
            if rel.suffix == ".mdc":
                data = data.replace(b"---\r\n\r\n", b"---\r\n\r\nPREFIX \t\r\n", 1)
            else:
                data = b"PREFIX \t\r\n" + data
            path.write_bytes(data + b"\r\nSUFFIX  \t\r\n \t")
        assert install(work) == 0
        for rel in carrier_targets(list(CARRIERS)):
            data = (work / rel).read_bytes()
            assert b"PREFIX \t\r\n" in data and data.endswith(b"\r\nSUFFIX  \t\r\n \t"), rel
        before = snapshot(work)
        assert install(work) == 0 and snapshot(work) == before
        assert run_check(work) == 0

    @scenario("多 foreign + 唯一自有块：重跑幂等，check 通过")
    def _(work: Path) -> None:
        foreign = b"<!-- agentflow:begin v0 global -->\r\nFOREIGN \t\r\n<!-- agentflow:end -->\r\n"
        original = foreign + foreign.replace(b"global", b"other") + b" \t"
        (work / "AGENTS.md").write_bytes(original)
        assert install(work, "--hosts", "zcode") == 0
        assert (work / "AGENTS.md").read_bytes().startswith(original)
        before = snapshot(work)
        assert install(work, "--hosts", "zcode") == 0
        assert snapshot(work) == before
        assert (work / "AGENTS.md").read_bytes().count(OURS_TAG.encode()) == 1
        assert run_check(work) == 0

    @scenario("重复/残缺/嵌套自有块：各宿主拒绝且零写入")
    def _(work: Path) -> None:
        block = managed_block("0", "BODY").encode()
        foreign = b"<!-- agentflow:begin v0 global -->\n"
        variants = [block + block, block.split(END_MARK.encode())[0], foreign + block + END_MARK.encode()]
        for host, (_, rel) in CARRIERS.items():
            for number, data in enumerate(variants):
                child = work / f"{host}-{number}"
                (child / rel).parent.mkdir(parents=True)
                (child / rel).write_bytes(data)
                before = snapshot(child)
                assert install(child, "--hosts", host) != 0, (host, number)
                assert snapshot(child) == before, (host, number)

    @scenario("Claude 旧指针只迁移归属行，重复/不相邻归属拒绝")
    def _(work: Path) -> None:
        comment = CLAUDE_POINTER_TPL.format(version="0", tag=OURS_TAG).encode()
        original = b"PREFIX  \r\n" + comment.replace(b"\n", b"\r\n") + b"SUFFIX\t  \r\n"
        (work / "CLAUDE.md").write_bytes(original)
        assert install(work, "--hosts", "claude") == 0
        data = (work / "CLAUDE.md").read_bytes()
        assert data.startswith(b"PREFIX  \r\n") and data.endswith(b"\r\nSUFFIX\t  \r\n")
        assert data.count(b"@AGENTS.md") == 1 and run_check(work) == 0
        for number, bad in enumerate([comment + comment, comment.replace(b"\n@", b"\nUSER\n@")]):
            child = work / f"bad-{number}"
            child.mkdir()
            (child / "CLAUDE.md").write_bytes(bad)
            before = snapshot(child)
            assert install(child, "--hosts", "claude") != 0 and snapshot(child) == before

    @scenario("Claude-only 必须生成正文依赖，删除依赖 check 报错")
    def _(work: Path) -> None:
        assert install(work, "--hosts", "claude") == 0
        assert owned_span((work / "AGENTS.md").read_bytes()) is not None
        assert run_check(work) == 0
        (work / "AGENTS.md").unlink()
        assert run_check(work) != 0

    @scenario("conflict 全计划零写/manifest 不变/check 持续非零，refresh 与 hosts 缩小")
    def _(work: Path) -> None:
        assert install(work) == 0
        manifest = load_manifest(work)
        asset = work / ".agentflow/standards/frontend.md"
        asset.write_bytes(asset.read_bytes() + b"\nUSER_EDIT\n")
        before = snapshot(work)
        for extra in [(), ("--dry-run",)]:
            assert install(work, "--hosts", "zcode", *extra) != 0
            assert snapshot(work) == before
            assert run_check(work) != 0
        assert install(work, "--hosts", "zcode", "--refresh-assets") == 0
        updated = load_manifest(work)
        assert set(updated["hosts"]) == set(manifest["hosts"])
        assert set(updated["files"]) >= set(manifest["files"])
        assert b"USER_EDIT" not in asset.read_bytes() and run_check(work) == 0
        (work / "CLAUDE.md").unlink()
        assert run_check(work) != 0

    @scenario("refresh 不能覆盖无来源普通文件")
    def _(work: Path) -> None:
        asset = work / ".agentflow/standards/frontend.md"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"TEAM_ASSET\r\n")
        before = snapshot(work)
        assert install(work, "--refresh-assets") != 0 and snapshot(work) == before

    @scenario("目标文件/祖先目录/目标根 symlink 拒绝且仓外不变")
    def _(work: Path) -> None:
        outside = work.parent / "outside"
        outside.mkdir()
        external_file = outside / "rules.md"
        external_file.write_bytes(b"OUTSIDE\r\n")
        for name, rel in [("file", Path("AGENTS.md")), ("ancestor", Path(".cursor")), ("manifest", Path(".agentflow/manifest.json"))]:
            child = work / name
            child.mkdir()
            link = child / rel
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(outside if name == "ancestor" else external_file)
            before, external = snapshot(child), snapshot(outside)
            assert install(child) != 0
            assert snapshot(child) == before and snapshot(outside) == external
        alias = work.parent / "repo-alias"
        alias.symlink_to(work, target_is_directory=True)
        before = snapshot(work)
        assert install(alias) != 0 and snapshot(work) == before

    @scenario("坏 manifest 明确错误且零写，check 不假绿")
    def _(work: Path) -> None:
        assert install(work, "--hosts", "zcode") == 0
        path = work / ".agentflow/manifest.json"
        valid = path.read_bytes()
        original = json.loads(valid)
        unsafe = dict(original, files={**original["files"], "../outside": "0" * 64})
        variants = [b"not json", b"[]", valid.replace(b'"files": {', b'"files": {"x":"bad",', 1),
                    json.dumps(unsafe).encode(), valid.replace(b'"tool":', b'"tool":"duplicate", "tool":', 1)]
        for data in variants:
            path.write_bytes(data)
            before = snapshot(work)
            assert install(work) != 0 and snapshot(work) == before
            assert run_check(work) != 0
        missing = json.loads(valid)
        missing["files"].pop(".agentflow/standards/frontend.md")
        missing["scopes"].pop(".agentflow/standards/frontend.md", None)
        path.write_text(json.dumps(missing), encoding="utf-8")
        assert run_check(work) != 0, "期望资产不能从清单中消失"

    @scenario("来源模板版本升级兼容旧 manifest，块外 bytes 不变")
    def _(work: Path) -> None:
        assert install(work) == 0
        old = load_manifest(work)
        # This is an ordinary source upgrade, not mutation of the real worktree.
        upgrade = work.parent / "upgrade-skill"
        _sh.copytree(skill_root, upgrade)
        maker = upgrade / "templates/host/maker.md"
        maker.write_bytes(maker.read_bytes() + b"\nUPGRADED_BODY\n")
        for rel in carrier_targets(old["hosts"]):
            path = work / rel
            path.write_bytes(path.read_bytes() + b"\r\nUSER_SUFFIX  \t")
        plan, writes = build_plan(work, upgrade, old["hosts"], "999", False, old)
        data = manifest_data(work, "999", old["hosts"], plan, writes, old)
        assert apply_plan(work, plan, writes, False) == 0
        write_manifest(work, "999", old["hosts"], plan, data)
        for rel, kind in carrier_targets(old["hosts"]).items():
            content = (work / rel).read_bytes()
            assert content.endswith(b"\r\nUSER_SUFFIX  \t")
            assert b"v999 " in content
            assert kind == "pointer" or b"UPGRADED_BODY" in content
        assert run_check(work) == 0
        assert list(work.rglob("*.agentflow-backup-*")), "升级应保留备份"

    @scenario("来源缺失/输出祖先是文件：整计划零写入")
    def _(work: Path) -> None:
        empty = work.parent / "empty-source"
        empty.mkdir()
        before = snapshot(work)
        assert install(work, "--agentflow", str(empty)) != 0 and snapshot(work) == before
        (work / ".cursor").write_bytes(b"NOT_A_DIRECTORY")
        before = snapshot(work)
        assert install(work) != 0 and snapshot(work) == before

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

    plan = None
    try:
        # Reject user-controlled links before any resolve; /tmp aliases are handled
        # by the shared snapshots helper. Init intentionally does not require Git.
        target = no_symlinks(args.target)
        if not target.is_dir():
            raise WorkflowError("missing-path", f"目标仓不存在：{target}")
        if args.check:
            return run_check(target)
        skill_root = no_symlinks(args.agentflow) if args.agentflow else Path(__file__).resolve().parents[1]
        version = find_plugin_version(skill_root)
        manifest = load_manifest(target)
        hosts = merged_hosts([h.strip() for h in args.hosts.split(",") if h.strip()], manifest)
        plan, writes = build_plan(target, skill_root, hosts, version, args.refresh_assets, manifest)
        problems = any(it["action"] in {"conflict", "error"} for it in plan.items)
        # Prepare all manifest bytes BEFORE the first write, including dry-run.
        data = None if problems else manifest_data(target, version, hosts, plan, writes, manifest)
        conflicts = apply_plan(target, plan, writes, args.dry_run)
        if conflicts:
            return 1
        if not args.dry_run:
            mpath = write_manifest(target, version, hosts, plan, data)
            print(f"\n[ok] manifest -> {mpath}")
        print(f"后续：让 AI 读目标仓现状，回填 AGENTS.md 的项目事实段与 {BASELINE_REL.as_posix()}"
              "（探测命令必须带超时）。")
        return 0
    except (WorkflowError, OSError, UnicodeError) as exc:
        print(f"[error] {getattr(exc, 'kind', 'io-error')}: {exc}", file=sys.stderr)
        if plan is not None:
            print("[partial] 实际已写文件与备份：" + json.dumps(plan.applied, ensure_ascii=False), file=sys.stderr)
        return getattr(exc, "code", 1)


if __name__ == "__main__":
    raise SystemExit(main())
