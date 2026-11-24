#!/usr/bin/env python3
"""Create a feature skeleton at an explicitly selected documentation tier.

  new_feature.py --hub <hub> --slug <name> --tier light
  new_feature.py --hub <hub> --slug <name> --tier full --tracks be[,fe,qa,ui]
                 [--prototype] [--date YYYY-MM-DD] [--template-dir <feature>]
                 [--dry-run]

light copies lightweight.md to README.md only. full copies the common
README/proposal/plan/spec-checklist and selected spec/design tracks; QA is always
included. --prototype explicitly opts into the prototype templates. Custom
--template-dir trees must use the same relative names; extra files are not copied.
No business decisions, applicability or approval are inferred from the tier.

All selected inputs and index registration are checked before writing. Creation
is exclusive, and index publication uses an optimistic state check plus a
same-directory atomic replacement. This is not a sandbox or a transaction against
hostile concurrent processes. Existing directories and registrations are refused.
Exit codes: 0 success, 1 conflict/environment/write failure, 2 invalid CLI/input.
"""
from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import tempfile
from datetime import date, datetime
from html import escape
from pathlib import Path

# Match the other portable script entry points: local imports never create files.
sys.dont_write_bytecode = True
from workflow_lib.snapshots import (
    WorkflowError,
    no_symlinks,
    project_path,
    relative_name,
)


TRACKS = ("be", "fe", "qa", "ui")
TRACK_FILES = {
    "be": ("spec/be/backend.md", "design/be/backend.md"),
    "fe": ("spec/fe/frontend.md", "design/fe/frontend.md"),
    "qa": ("spec/qa/acceptance.md", "design/qa/testing.md"),
    "ui": ("spec/ui/visual.md", "design/ui/visual.md"),
}
COMMON_FILES = (
    "README.md", "proposal/proposal.md", "plan/execution.md", "spec/checklist.md",
)
PROTOTYPE_FILES = ("prototype/README.md", "prototype/index.html")


class FeatureError(Exception):
    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def _cells(line: str) -> list[str] | None:
    line = line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        return None
    return [cell.strip() for cell in line[1:-1].split("|")]


def build_index_row(index_text: str, rel_dir: str) -> str | None:
    """Append within the unique 3/4-column feature table; never another table.

    None means the index has no unambiguous valid header and delimiter. Existing
    registrations raise instead of silently creating an unregistered directory.
    Preserve all bytes outside the inserted row, including CRLF and trailing text.
    """
    lines = index_text.splitlines(keepends=True)
    tables: list[tuple[int, list[str]]] = []
    for i, line in enumerate(lines):
        header = _cells(line)
        if header not in [
            ["批次", "一句话范围", "进度板"],
            ["批次", "一句话范围", "状态", "进度板"],
        ] or i + 1 >= len(lines):
            continue
        separator = _cells(lines[i + 1])
        if separator and len(separator) == len(header) and all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separator
        ):
            tables.append((i, header))
    if len(tables) != 1:
        return None
    start, header = tables[0]
    end = start + 2
    while end < len(lines):
        row = _cells(lines[end])
        if row is None:
            break
        if len(row) != len(header):
            return None
        end += 1
    registration = f"features/{rel_dir}"
    # Refuse a manually registered batch even if its directory is absent.
    for line in lines:
        row = _cells(line)
        if row and any(
            re.search(r"(?<![\w/-])" + re.escape(registration) + r"(?=$|[\s`/)#])", cell)
            for cell in row
        ):
            raise FeatureError(f"index.md 已有批次登记，不重复创建：{registration}")
    cells = {
        "批次": f"`{registration}`",
        "一句话范围": "<待填：做什么、不做什么>",
        "状态": "<待填>",
        "进度板": f"`{registration}/README.md`",
    }
    newline = "\r\n" if lines[start].endswith("\r\n") else "\n"
    row = "| " + " | ".join(cells[column] for column in header) + " |" + newline
    before = "".join(lines[:end])
    if before and not before.endswith("\n"):
        before += newline
    return before + row + "".join(lines[end:])


def _selection(args: argparse.Namespace, ap: argparse.ArgumentParser) -> tuple[str, ...]:
    if not args.tier:
        ap.error("需要显式 --tier light|full；脚本不自动判断风险")
    if args.tier == "light":
        if args.tracks is not None or args.prototype:
            ap.error("--tracks 与 --prototype 仅用于 --tier full")
        return ()
    if args.tracks is None:
        ap.error("--tier full 需要 --tracks 至少一轨；QA 始终纳入")
    selected = [part.strip() for part in args.tracks.split(",")]
    if any(part not in TRACKS for part in selected) or len(set(selected)) != len(selected):
        ap.error("--tracks 只能为 be,fe,qa,ui 的非空、不重复逗号列表")
    return tuple(track for track in TRACKS if track in selected or track == "qa")


def _batch_name(slug: str, day: str) -> str:
    # One whitelist-only component: no separators, dots, whitespace or escapes.
    edge = r"[A-Za-z0-9\u3400-\u4dbf\u4e00-\u9fff]"
    middle = r"[A-Za-z0-9_\-\u3400-\u4dbf\u4e00-\u9fff]"
    if not 1 <= len(slug) <= 80 or not re.fullmatch(edge + r"(?:" + middle + r"*" + edge + r")?", slug):
        raise FeatureError("--slug 为1到80字符的单段中文/字母/数字/_/-，首末须为中文、字母或数字", 2)
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", day):
        raise FeatureError("--date 必须严格为 YYYY-MM-DD", 2)
    try:
        parsed = date.fromisoformat(day)
    except ValueError as exc:
        raise FeatureError(f"--date 不是有效日期：{day}", 2) from exc
    if parsed.isoformat() != day:
        raise FeatureError("--date 必须严格为 YYYY-MM-DD", 2)
    return relative_name(f"feature-{day}-{slug}")


def _identity(path: Path) -> tuple[int, int]:
    info = path.lstat()
    return info.st_dev, info.st_ino


def _file_snapshot(path: Path) -> tuple[tuple[int, int, int, int, int], bytes]:
    """Read a regular file without following its leaf or any existing ancestor."""
    path = no_symlinks(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise FeatureError(f"需要普通文件：{path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != (
            before.st_dev, before.st_ino
        ):
            raise FeatureError(f"读取时文件已变化：{path}")
        data = stream.read()
        after = os.fstat(stream.fileno())
    state = lambda value: (
        value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns,
    )
    if state(info) != state(after) or _identity(no_symlinks(path)) != (
        info.st_dev, info.st_ino
    ):
        raise FeatureError(f"读取时文件已变化：{path}")
    return state(info), data


def _render_readme(text: str, tracks: tuple[str, ...], prototype: bool) -> str:
    """Render declared navigation slots while preserving authored text."""
    unselected = "、".join(track.upper() for track in TRACKS if track not in tracks)
    replacements = {
        "{{feature_spec_links}}": "、".join(
            f"[{track.upper()}]({TRACK_FILES[track][0]})" for track in tracks
        ),
        "{{feature_design_links}}": "、".join(
            f"[{track.upper()}]({TRACK_FILES[track][1]})" for track in tracks
        ),
        "{{feature_unselected_tracks}}": (
            f"{unselected}（补充理由，受影响的既有契约在对应规格中引用）。" if unselected else "各轨均已选择。"
        ),
        "{{feature_preview}}": (
            "已生成离线草稿：[预览说明](prototype/README.md) · [HTML 骨架](prototype/index.html)。按实际界面完善并记录确认依据。"
            if prototype else
            "未生成离线原型。需要界面确认时登记实际页面、版本与浏览器证据；无界面时登记不适用理由。"
        ),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _template_plan(
    template: Path, tier: str, tracks: tuple[str, ...], prototype: bool,
    slug: str, day: str, rel_dir: str,
) -> dict[str, bytes]:
    if tier == "light":
        names = [("lightweight.md", "README.md")]
    else:
        names = [(name, name) for name in COMMON_FILES]
        names += [(name, name) for track in tracks for name in TRACK_FILES[track]]
        if prototype:
            names += [(name, name) for name in PROTOTYPE_FILES]
    planned: dict[str, bytes] = {}
    for source_name, target_name in names:
        source = project_path(template, source_name, must_exist=True)
        _, data = _file_snapshot(source)
        try:
            text = data.decode("utf-8")
        except UnicodeError as exc:
            raise FeatureError(f"模板必须为 UTF-8：{source}") from exc
        # These tokens are mechanical identity/date placeholders, never approvals.
        for old, value in {
            "feature-<日期>-<主题>": rel_dir,
            "<feature 名>": slug,
            "<feature>": slug,
            "<功能或变更>": slug,
            "<日期>": day,
        }.items():
            text = text.replace(old, value)
        if tier == "full" and target_name == "README.md":
            text = _render_readme(text, tracks, prototype)
        elif target_name == "plan/execution.md":
            plan_id = f"PLAN-{day}-{slug}"
            recorded_at = datetime.now().astimezone().isoformat(timespec="seconds")
            text = text.replace("{{feature_plan_id}}", plan_id).replace(
                "{{feature_plan_recorded_at}}", recorded_at
            )
        elif target_name == "prototype/index.html":
            text = text.replace("&lt;feature 名&gt;", escape(slug))
        planned[relative_name(target_name)] = text.encode("utf-8")
    return planned


def _assert_owned(directories: dict[Path, tuple[int, int]]) -> None:
    for path, identity in directories.items():
        safe = no_symlinks(path)
        if not safe.is_dir() or _identity(safe) != identity:
            raise FeatureError(f"生成目录已被替换，拒绝继续：{path}")


def _write_new(path: Path, data: bytes) -> tuple[int, int]:
    path = no_symlinks(path)
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o644,
    )
    with os.fdopen(descriptor, "wb") as stream:
        info = os.fstat(stream.fileno())
        identity = info.st_dev, info.st_ino
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            # Remove only our failed file, never a concurrently substituted leaf.
            if _identity(no_symlinks(path)) == identity:
                path.unlink()
            raise
    return identity


def _cleanup_batch(
    target: Path, directories: dict[Path, tuple[int, int]],
    created_files: dict[Path, tuple[tuple[int, int], bytes]],
) -> None:
    """Delete only owned unchanged files/dirs; preserve any external additions."""
    try:
        _assert_owned(directories)
    except (OSError, FeatureError, WorkflowError) as exc:
        print(f"[警告] 批次目录所有权已变化，保留现场 {target}：{exc}", file=sys.stderr)
        return
    for path, (identity, data) in created_files.items():
        try:
            current, content = _file_snapshot(path)
            if current[:2] == identity and content == data:
                path.unlink()
            else:
                print(f"[警告] 文件已被外部修改，保留：{path}", file=sys.stderr)
        except (OSError, FeatureError, WorkflowError) as exc:
            print(f"[警告] 未清理文件 {path}：{exc}", file=sys.stderr)
    owned = [path for path in directories if path == target or target in path.parents]
    for path in sorted(owned, key=lambda item: len(item.parts), reverse=True):
        try:
            if _identity(no_symlinks(path)) == directories[path]:
                path.rmdir()  # A foreign addition prevents deletion.
        except OSError as exc:
            print(f"[警告] 未清理非空或变化目录 {path}：{exc}", file=sys.stderr)
        except WorkflowError as exc:
            print(f"[警告] 未清理链接目录 {path}：{exc}", file=sys.stderr)


def _replace_index(
    path: Path, desired: bytes,
    expected: tuple[tuple[int, int, int, int, int], bytes],
    directories: dict[Path, tuple[int, int]],
) -> None:
    """Publish to the existing index with the same optimistic guard as managed.py."""
    if _file_snapshot(path) != expected:
        raise FeatureError("index.md 在预检后变化；未登记，请基于新索引重跑")
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".agentflow-index-", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(desired)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, stat.S_IMODE(expected[0][2]))
        _assert_owned(directories)
        if _file_snapshot(path) != expected:
            raise FeatureError("index.md 在准备登记时变化；保留外部修改，请重跑")
        os.replace(temporary, no_symlinks(path))
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink()


def _generate(
    hub: Path, target: Path, index: Path,
    expected: tuple[tuple[int, int, int, int, int], bytes],
    new_index: bytes, files: dict[str, bytes],
) -> None:
    """Own only the exclusively created batch; never delete a foreign target."""
    features = project_path(hub, "features", directory=True)
    directories: dict[Path, tuple[int, int]] = {hub: _identity(hub)}
    owned_target: tuple[int, int] | None = None
    created_files: dict[Path, tuple[tuple[int, int], bytes]] = {}
    try:
        if not features.exists():
            try:
                features.mkdir()
            except FileExistsError:
                no_symlinks(features)
        directories[features] = _identity(no_symlinks(features))
        _assert_owned(directories)
        # Do not use exist_ok or copytree's merge mode for this ownership boundary.
        no_symlinks(target).mkdir()
        owned_target = _identity(target)
        directories[target] = owned_target
        for name, data in files.items():
            _assert_owned(directories)
            destination = project_path(target, name)
            for parent in reversed(destination.parents):
                if parent == target or target not in parent.parents:
                    continue
                if parent not in directories:
                    no_symlinks(parent).mkdir()
                    directories[parent] = _identity(parent)
            created_files[destination] = (_write_new(destination, data), data)
        _replace_index(index, new_index, expected, directories)
    except BaseException:
        if owned_target is not None:
            _cleanup_batch(target, directories, created_files)
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="按显式档位开批次并安全登记 index")
    ap.add_argument("--hub", help="文档枢纽根（必须含有效 index.md）")
    ap.add_argument("--slug", help="批次短名：单段中文/英文字母/数字/_/-")
    ap.add_argument("--date", default=date.today().isoformat(), help="严格 YYYY-MM-DD（默认今天）")
    ap.add_argument("--tier", choices=("light", "full"), help="必填；不自动判断风险")
    ap.add_argument("--tracks", help="full 必填；逗号分隔 be,fe,qa,ui；始终纳入 qa")
    ap.add_argument("--prototype", action="store_true", help="full：显式生成离线 prototype 模板")
    ap.add_argument("--template-dir", help="同名相对结构的 feature 模板根；只复制所选文件")
    ap.add_argument("--dry-run", action="store_true", help="完成所有输入预检并打印计划，零写入")
    ap.add_argument("--self-test", action="store_true", help="在临时目录跑生成与安全矩阵")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.hub or args.slug is None:
        ap.error("需要 --hub 与 --slug（或单独 --self-test）")
    tracks = _selection(args, ap)
    try:
        rel_dir = _batch_name(args.slug, args.date)
        # Reject user-controlled links before any resolution; /tmp and /var system
        # aliases are handled by the shared path contract.
        hub = no_symlinks(args.hub)
        if not hub.is_dir():
            raise FeatureError(f"枢纽不存在：{hub}", 2)
        features = project_path(hub, "features", directory=True)
        target = project_path(features, rel_dir, directory=True)
        if os.path.lexists(target):
            raise FeatureError(f"批次目录已存在，不覆盖：{target}")
        # Let the filesystem define its actual byte/name bound, including Unicode.
        if len(os.fsencode(rel_dir)) > os.pathconf(hub, "PC_NAME_MAX"):
            raise FeatureError("日期与 --slug 组合超过目标文件系统单段名称字节上限", 2)
        index = project_path(hub, "index.md", must_exist=True)
        expected = _file_snapshot(index)
        try:
            index_text = expected[1].decode("utf-8")
        except UnicodeError as exc:
            raise FeatureError("index.md 必须为 UTF-8；未创建任何批次文件") from exc
        new_index = build_index_row(index_text, rel_dir)
        if new_index is None:
            raise FeatureError(
                "index.md 需要唯一有效的批次表（批次/一句话范围/[状态/]进度板及分隔行）；"
                "请修复表头或手工立项，本次零写入"
            )
        template = no_symlinks(
            args.template_dir if args.template_dir else
            Path(__file__).absolute().parents[1] / "templates" / "feature"
        )
        if not template.is_dir():
            raise FeatureError(f"模板目录不存在：{template}", 2)
        if template == target or target in template.parents:
            raise FeatureError("模板目录不能位于本次目标内", 2)
        files = _template_plan(
            template, args.tier, tracks, args.prototype, args.slug, args.date, rel_dir,
        )
        print(
            f"[计划] tier={args.tier}；tracks={','.join(tracks) or '无'}；"
            f"prototype={'yes' if args.prototype else 'no'}"
        )
        print(f"[计划] 生成 {len(files)} 个模板文件 -> {target}")
        for name in sorted(files):
            print(f"  - {name}")
        print("[计划] index.md 批次表登记一行；不创建 testing 占位")
        if args.dry_run:
            print("[dry-run] 预检完成，未写入任何文件。")
            return 0
        _generate(hub, target, index, expected, new_index.encode("utf-8"), files)
        print(f"[ok] 已生成并登记：features/{rel_dir}")
        print("待填写：真实需求、适用性、验收与证据；模板生成不代表评审或阶段完成。")
        return 0
    except FeatureError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return exc.code
    except WorkflowError as exc:
        print(f"[错误] {exc.kind}：{exc}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as exc:
        print(f"[错误] 生成失败：{exc}", file=sys.stderr)
        return 1


def _self_test() -> int:
    import contextlib
    import io
    import shutil
    from unittest.mock import patch

    template = Path(__file__).absolute().parents[1] / "templates" / "feature"
    index_3 = ("# 索引\n\n## 批次清单\n\n| 批次 | 一句话范围 | 进度板 |\n"
               "| --- | --- | --- |\n")
    index_4 = ("# 索引\n\n## 批次清单\n\n| 批次 | 一句话范围 | 状态 | 进度板 |\n"
               "| --- | --- | --- | --- |\n")
    rel_dir = "feature-2026-11-05-demo"
    results: list[tuple[str, bool, str]] = []

    def hub_at(base: Path, content: str = index_3) -> Path:
        hub = base / "hub"
        hub.mkdir()
        (hub / "index.md").write_text(content, encoding="utf-8")
        return hub

    def tree(root: Path) -> dict[str, tuple[str, bytes | str]]:
        """Read authoritative paths, including empty dirs and link destinations."""
        entries: dict[str, tuple[str, bytes | str]] = {}
        for path in sorted(root.rglob("*")):
            name = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries[name] = ("link", os.readlink(path))
            elif path.is_dir():
                entries[name] = ("directory", "")
            elif path.is_file():
                entries[name] = ("file", path.read_bytes())
        return entries

    def run(hub: Path, extra: list[str] | None = None) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                code = main([
                    "--hub", str(hub), "--slug", "demo", "--date", "2026-11-05",
                    *(extra if extra is not None else ["--tier", "light"]),
                ])
            except SystemExit as exc:
                code = int(exc.code)
        return code, output.getvalue()

    def rejects_unchanged(hub: Path, extra: list[str], root: Path | None = None) -> None:
        root = root or hub
        before = tree(root)
        code, output = run(hub, extra)
        assert code != 0, output
        assert tree(root) == before, "拒绝后目录/文件/哨兵有变化：" + output
        print(f"  refused exit={code}: {output.strip().splitlines()[-1]}")

    def generated(hub: Path) -> set[str]:
        target = hub / "features" / rel_dir
        return {
            path.relative_to(target).as_posix()
            for path in target.rglob("*") if path.is_file()
        }

    def light(base: Path) -> None:
        hub = hub_at(base)
        code, output = run(hub)
        assert code == 0, output
        assert generated(hub) == {"README.md"}, generated(hub)
        assert "tier=light；tracks=无；prototype=no" in output, output
        readme = (hub / "features" / rel_dir / "README.md").read_text(encoding="utf-8")
        assert "# demo — 轻量交付" in readme
        assert "<是/否/未知>" in readme, "不能代替用户判定完整文档要求"
        assert not (hub / "features" / rel_dir / "testing").exists()
        print("  actual files=" + repr(sorted(generated(hub))))

    def full_be(base: Path) -> None:
        hub = hub_at(base)
        code, output = run(hub, ["--tier", "full", "--tracks", "be"])
        assert code == 0, output
        expected = set(COMMON_FILES + TRACK_FILES["be"] + TRACK_FILES["qa"])
        assert generated(hub) == expected, generated(hub)
        target = hub / "features" / rel_dir
        readme = (target / "README.md").read_text(encoding="utf-8")
        assert "tracks=be,qa" in output
        for unselected in ("fe", "ui", "prototype", "testing"):
            assert not (target / unselected).exists()
        for absent in ("spec/fe/", "spec/ui/", "design/fe/", "design/ui/", "prototype/index.html"):
            # Generic telemetry instructions may mention design/fe without a path.
            assert absent not in readme, readme
        assert "[BE](spec/be/backend.md)、[QA](spec/qa/acceptance.md)" in readme
        assert "[BE](design/be/backend.md)、[QA](design/qa/testing.md)" in readme
        assert "FE、UI（补充理由" in readme
        assert "未生成离线原型" in readme
        print("  actual files=" + repr(sorted(generated(hub))))

    def full_fe_prototype(base: Path) -> None:
        hub = hub_at(base)
        code, output = run(hub, ["--tier", "full", "--tracks", "fe,qa", "--prototype"])
        assert code == 0, output
        expected = set(COMMON_FILES + TRACK_FILES["fe"] + TRACK_FILES["qa"] + PROTOTYPE_FILES)
        assert generated(hub) == expected, generated(hub)
        readme = (hub / "features" / rel_dir / "README.md").read_text(encoding="utf-8")
        assert "tracks=fe,qa；prototype=yes" in output
        assert "已生成离线草稿" in readme and "prototype/index.html" in readme
        assert not (hub / "features" / rel_dir / "spec/be").exists()
        print("  actual files=" + repr(sorted(generated(hub))))

    def all_tracks(base: Path) -> None:
        hub = hub_at(base)
        code, output = run(hub, ["--tier", "full", "--tracks", "ui,qa,be,fe"])
        assert code == 0, output
        assert "tracks=be,fe,qa,ui" in output
        expected = set(COMMON_FILES)
        for track in TRACKS:
            expected.update(TRACK_FILES[track])
        assert generated(hub) == expected
        assert "各轨均已选择。" in (hub / "features" / rel_dir / "README.md").read_text(encoding="utf-8")

    def dry_run(base: Path) -> None:
        hub = hub_at(base)
        before = tree(hub)
        for options in [
            ["--tier", "light", "--dry-run"],
            ["--tier", "full", "--tracks", "fe", "--prototype", "--dry-run"],
        ]:
            code, output = run(hub, options)
            assert code == 0, output
            assert tree(hub) == before, output
            print("  " + output.strip().splitlines()[-1])

    def duplicate(base: Path) -> None:
        hub = hub_at(base)
        assert run(hub)[0] == 0
        rejects_unchanged(hub, ["--tier", "light"])
        # A directory without an index row is still not owned by this invocation.
        other = hub / "features/feature-2026-11-05-existing"
        other.mkdir()
        (other / "sentinel").write_bytes(b"foreign")
        rejects_unchanged(hub, ["--tier", "full", "--tracks", "be", "--slug", "existing"])

    def registered_without_directory(base: Path) -> None:
        hub = hub_at(base, index_3 + f"| `features/{rel_dir}` | manual | `features/{rel_dir}/README.md` |\n")
        rejects_unchanged(hub, ["--tier", "light"])

    def cli_validation(base: Path) -> None:
        hub = hub_at(base)
        for options in [
            [], ["--tier", "full"], ["--tier", "full", "--tracks", ""],
            ["--tier", "full", "--tracks", "be,"],
            ["--tier", "full", "--tracks", "be,be"],
            ["--tier", "full", "--tracks", "BE"],
            ["--tier", "full", "--tracks", "unknown"],
            ["--tier", "light", "--tracks", "be"],
            ["--tier", "light", "--prototype"], ["--tier", "auto"],
        ]:
            rejects_unchanged(hub, options)

    def bad_names(base: Path) -> None:
        hub = hub_at(base)
        (base / "sentinel").write_bytes(b"outside")
        for slug in [
            "x/../../../ESCAPED", "", ".", "..", "a.b", "/absolute", "a/b",
            "a\\b", "C:drive", "has space", "a\nb", "a\x00b", "emoji😀", "中" * 100,
        ]:
            rejects_unchanged(hub, ["--tier", "light", "--slug", slug], base)
        assert not (base / "ESCAPED").exists()
        assert (base / "sentinel").read_bytes() == b"outside"

    def bad_dates(base: Path) -> None:
        hub = hub_at(base)
        for day in [
            "2026-2-05", "20261105", "2026-02-29", "2026-13-01", "0000-01-01",
            "2026-11-05/../escape", "2026-11-05T00:00:00", "2026-11-05\n", "",
        ]:
            rejects_unchanged(hub, ["--tier", "light", "--date", day])
        code, output = run(hub, ["--tier", "light", "--slug", "中文_A-z9", "--date", "2024-02-29"])
        assert code == 0, output
        assert (hub / "features/feature-2024-02-29-中文_A-z9/README.md").is_file()

    def invalid_index(base: Path) -> None:
        hub = hub_at(base)
        cases = [
            b"\xff", b"# no table\n",
            b"| \xe6\x89\xb9\xe6\xac\xa1 | range | board |\n| --- | --- | --- |\n",
            "| 批次 | 一句话范围 | 进度板 |\n".encode(),
            "| 批次 | 一句话范围 | 进度板 |\n| nope | --- | --- |\n".encode(),
            (index_3 + index_4).encode(),
            (index_3 + "| broken | row |\n").encode(),
        ]
        for data in cases:
            (hub / "index.md").write_bytes(data)
            rejects_unchanged(hub, ["--tier", "light"])
            rejects_unchanged(hub, ["--tier", "light", "--dry-run"])
        (hub / "index.md").unlink()
        rejects_unchanged(hub, ["--tier", "light"])

    def index_layout(base: Path) -> None:
        # Existing rows, an empty table, a later unrelated table and CRLF survive.
        text = index_4.replace("\n", "\r\n") + (
            "| `features/older` | keep | draft | `features/older/README.md` |\r\n"
            "\r\n## Notes\r\n| Name | Value |\r\n| --- | --- |\r\n| x | y |\r\n"
        )
        hub = hub_at(base)
        (hub / "index.md").write_bytes(text.encode())
        os.chmod(hub / "index.md", 0o640)
        code, output = run(hub)
        assert code == 0, output
        actual = (hub / "index.md").read_bytes().decode()
        inserted = f"| `features/{rel_dir}` | <待填：做什么、不做什么> | <待填> | `features/{rel_dir}/README.md` |\r\n"
        assert actual == text.replace("\r\n\r\n## Notes", "\r\n" + inserted + "\r\n## Notes")
        assert stat.S_IMODE((hub / "index.md").stat().st_mode) == 0o640
        assert not list(hub.glob(".agentflow-index-*"))
        empty = build_index_row(index_3.rstrip("\n"), "feature-other")
        assert empty and "| --- | --- | --- |\n| `features/feature-other`" in empty
        assert empty.count("features/feature-other`") == 1

    def custom_templates(base: Path) -> None:
        hub = hub_at(base)
        custom = base / "templates"
        shutil.copytree(template, custom)
        (custom / "custom-extra.txt").write_text("do not copy", encoding="utf-8")
        code, output = run(hub, ["--tier", "light", "--template-dir", str(custom)])
        assert code == 0, output
        assert generated(hub) == {"README.md"}
        # A selected missing source, including nested sources, must fail pre-write.
        (custom / "lightweight.md").unlink()
        rejects_unchanged(hub, ["--tier", "light", "--slug", "second", "--template-dir", str(custom)], base)
        (custom / "design/be/backend.md").unlink()
        rejects_unchanged(hub, ["--tier", "full", "--tracks", "be", "--slug", "second", "--template-dir", str(custom)], base)
        rejects_unchanged(hub, ["--tier", "light", "--slug", "second", "--template-dir", str(base / "missing")], base)

    def symlinks(base: Path) -> None:
        # New isolated fixture per link surface so authoritative before/after includes
        # both the hub and every outside file that could otherwise be changed.
        for surface in ("hub", "hub-ancestor", "features", "target", "index", "template", "template-ancestor", "source", "source-ancestor"):
            area = base / surface
            area.mkdir()
            hub = hub_at(area)
            outside = area / "outside"
            outside.mkdir()
            (outside / "sentinel").write_bytes(b"outside-sentinel")
            custom = area / "templates"
            shutil.copytree(template, custom)
            invoked_hub = hub
            options = ["--tier", "light", "--template-dir", str(custom)]
            if surface == "hub":
                invoked_hub = area / "hub-link"
                invoked_hub.symlink_to(hub, target_is_directory=True)
            elif surface == "hub-ancestor":
                (area / "alias").symlink_to(area, target_is_directory=True)
                invoked_hub = area / "alias/hub"
            elif surface == "features":
                (hub / "features").symlink_to(outside, target_is_directory=True)
            elif surface == "target":
                (hub / "features").mkdir()
                (hub / "features" / rel_dir).symlink_to(outside, target_is_directory=True)
            elif surface == "index":
                (hub / "index.md").unlink()
                (outside / "index.md").write_text(index_3, encoding="utf-8")
                (hub / "index.md").symlink_to(outside / "index.md")
            elif surface == "template":
                (area / "template-link").symlink_to(custom, target_is_directory=True)
                options[-1] = str(area / "template-link")
            elif surface == "template-ancestor":
                (area / "alias").symlink_to(area, target_is_directory=True)
                options[-1] = str(area / "alias/templates")
            elif surface == "source":
                (custom / "lightweight.md").unlink()
                (custom / "lightweight.md").symlink_to(outside / "sentinel")
            else:
                shutil.rmtree(custom / "spec/be")
                (custom / "spec/be").symlink_to(outside, target_is_directory=True)
                options = ["--tier", "full", "--tracks", "be", "--template-dir", str(custom)]
            before = tree(area)
            code, output = run(invoked_hub, options)
            assert code != 0 and "symlink" in output, output
            assert tree(area) == before, surface + ": changed files"
            assert (outside / "sentinel").read_bytes() == b"outside-sentinel"
            print(f"  {surface}: refused exit={code}; outside sentinel unchanged")
        # Broken links are existing foreign targets too.
        broken_area = base / "broken"
        broken_area.mkdir()
        hub = hub_at(broken_area)
        (hub / "features").symlink_to(broken_area / "missing", target_is_directory=True)
        rejects_unchanged(hub, ["--tier", "light"], broken_area)

    def system_alias(base: Path) -> None:
        if sys.platform != "darwin":
            print("  /tmp system alias N/A outside macOS")
            return
        with tempfile.TemporaryDirectory(prefix="af-generator-alias-", dir="/tmp") as temp:
            hub = hub_at(Path(temp))
            code, output = run(hub)
            assert code == 0, output
            assert generated(hub) == {"README.md"}
            print("  macOS /tmp alias accepted")

    def write_failure(base: Path) -> None:
        hub = hub_at(base)
        (base / "sentinel").write_bytes(b"outside")
        before_index = (hub / "index.md").read_bytes()
        original = _write_new

        def fail_after_first(path: Path, data: bytes) -> tuple[int, int]:
            if path.name == "proposal.md":
                raise OSError("injected copy failure")
            return original(path, data)

        with patch(__name__ + "._write_new", side_effect=fail_after_first):
            code, output = run(hub, ["--tier", "full", "--tracks", "be"])
        assert code == 1 and "injected copy failure" in output, output
        assert not (hub / "features" / rel_dir).exists()
        assert (hub / "index.md").read_bytes() == before_index
        assert (base / "sentinel").read_bytes() == b"outside"
        assert run(hub)[0] == 0, "失败清理后应能重入"
        print("  partial batch removed; outside/index unchanged; rerun passed")

    def index_drift(base: Path) -> None:
        hub = hub_at(base)
        original = _write_new
        external = index_3 + "\nexternal writer\n"

        def modify_index(path: Path, data: bytes) -> tuple[int, int]:
            identity = original(path, data)
            (hub / "index.md").write_text(external, encoding="utf-8")
            return identity

        with patch(__name__ + "._write_new", side_effect=modify_index):
            code, output = run(hub)
        assert code == 1 and "预检后变化" in output, output
        assert (hub / "index.md").read_text(encoding="utf-8") == external
        assert not (hub / "features" / rel_dir).exists()
        assert not list(hub.glob(".agentflow-index-*"))
        print("  concurrent index edit kept; undelivered batch removed")

    def index_late_drift(base: Path) -> None:
        hub = hub_at(base)
        external = index_3 + "\nlate external writer\n"
        original = os.chmod

        def modify_index(path: Path, mode: int) -> None:
            original(path, mode)
            if Path(path).name.startswith(".agentflow-index-"):
                (hub / "index.md").write_text(external, encoding="utf-8")

        with patch("os.chmod", side_effect=modify_index):
            code, output = run(hub)
        assert code == 1 and "准备登记时变化" in output, output
        assert (hub / "index.md").read_text(encoding="utf-8") == external
        assert not (hub / "features" / rel_dir).exists()
        assert not list(hub.glob(".agentflow-index-*"))
        print("  final index recheck refused late edit; temp file removed")

    def publish_failure(base: Path) -> None:
        hub = hub_at(base)
        before = (hub / "index.md").read_bytes()
        with patch("os.replace", side_effect=OSError("injected index publication failure")):
            code, output = run(hub)
        assert code == 1 and "injected index publication failure" in output, output
        assert (hub / "index.md").read_bytes() == before
        assert not (hub / "features" / rel_dir).exists()
        assert not list(hub.glob(".agentflow-index-*"))
        assert run(hub)[0] == 0
        print("  atomic replacement failure kept index; cleaned batch/temp; rerun passed")

    def foreign_target_race(base: Path) -> None:
        hub = hub_at(base)
        target = no_symlinks(hub) / "features" / rel_dir
        original = Path.mkdir

        def create_foreign(path: Path, *args, **kwargs) -> None:
            if path == target:
                original(path)
                (path / "sentinel").write_bytes(b"foreign")
            original(path, *args, **kwargs)

        before_index = (hub / "index.md").read_bytes()
        with patch.object(Path, "mkdir", create_foreign):
            code, output = run(hub)
        assert code == 1, output
        assert (target / "sentinel").read_bytes() == b"foreign"
        assert (hub / "index.md").read_bytes() == before_index
        print("  raced-in foreign target retained and index untouched")

    def cleanup_foreign_content(base: Path) -> None:
        for change in ("added-file", "edited-readme", "replaced-directory"):
            area = base / change
            area.mkdir()
            hub = hub_at(area)
            target = no_symlinks(hub) / "features" / rel_dir
            outside = area / "outside"
            outside.mkdir()
            (outside / "sentinel").write_bytes(b"outside")
            before_index = (hub / "index.md").read_bytes()

            def fail_with_foreign_content(*args) -> None:
                if change == "added-file":
                    (target / "external").write_bytes(b"foreign")
                elif change == "edited-readme":
                    (target / "README.md").write_bytes(b"external edit")
                else:
                    target.rename(target.with_name(target.name + "-moved"))
                    target.symlink_to(outside, target_is_directory=True)
                raise OSError("injected failure after external change")

            with patch(__name__ + "._replace_index", side_effect=fail_with_foreign_content):
                code, output = run(hub)
            assert code == 1 and "injected failure" in output, output
            assert (hub / "index.md").read_bytes() == before_index
            if change == "added-file":
                assert (target / "external").read_bytes() == b"foreign"
                assert not (target / "README.md").exists()
            elif change == "edited-readme":
                assert (target / "README.md").read_bytes() == b"external edit"
            else:
                assert target.is_symlink()
                assert (target.with_name(target.name + "-moved") / "README.md").is_file()
            assert (outside / "sentinel").read_bytes() == b"outside"
            print(f"  {change}: external content preserved during cleanup")

    def custom_readme_facts(base: Path) -> None:
        hub = hub_at(base)
        custom = base / "templates"
        shutil.copytree(template, custom)
        readme = custom / "README.md"
        text = readme.read_text(encoding="utf-8")
        text = re.sub(r"^- 预览：.*$", "- 预览：真实页面 /reviewed-preview", text, flags=re.MULTILINE)
        text = text + "\n- 原型基线：existing@0123456\n"
        readme.write_text(text, encoding="utf-8")
        code, output = run(hub, ["--tier", "full", "--tracks", "qa", "--template-dir", str(custom)])
        assert code == 0, output
        actual = (hub / "features" / rel_dir / "README.md").read_text(encoding="utf-8")
        assert "- 预览：真实页面 /reviewed-preview" in actual
        assert "- 原型基线：existing@0123456" in actual
        print("  custom template facts retained; only known placeholders rendered")

    cases = [
        ("light 只生成 README 并保留未决业务占位", light),
        ("full be 自动纳入 qa，无 fe/ui/prototype/testing", full_be),
        ("full fe+qa 可显式生成 prototype", full_fe_prototype),
        ("显式全轨顺序与 UI 元信息", all_tracks),
        ("light/full dry-run 零写入", dry_run),
        ("重复目录与已有外部目录拒绝", duplicate),
        ("已登记但无目录也拒绝", registered_without_directory),
        ("档位/轨道/原型参数校验零写入", cli_validation),
        ("越界 slug 与非法字符拒绝，外哨兵不变", bad_names),
        ("严格日期及中文合法 slug", bad_dates),
        ("index 无效/缺失/非UTF8/歧义零写入", invalid_index),
        ("3/4列表、行尾、后续表与文件权限保留", index_layout),
        ("自有同结构模板选择与源缺失零写入", custom_templates),
        ("所有输入祖先与目标符号链接拒绝", symlinks),
        ("正常 macOS /tmp 系统别名可用", system_alias),
        ("复制部分失败只清本次目录且可重入", write_failure),
        ("index 预检后变化保留并发编辑", index_drift),
        ("index 替换前重检与临时文件清理", index_late_drift),
        ("index 发布失败保留原文且可重入", publish_failure),
        ("独占创建竞争不删除非本次目标", foreign_target_race),
        ("失败清理保留外部新增/编辑/替换的内容", cleanup_foreign_content),
        ("自有README业务事实不被机械渲染覆盖", custom_readme_facts),
    ]
    for name, test in cases:
        print(f"CASE {name}")
        try:
            with tempfile.TemporaryDirectory(prefix="af-newfeat-selftest-") as temp:
                test(Path(temp))
        except Exception as exc:
            results.append((name, False, f"{type(exc).__name__}: {exc}"))
        else:
            results.append((name, True, ""))
    failed = [result for result in results if not result[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
