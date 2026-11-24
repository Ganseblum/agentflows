#!/usr/bin/env python3
"""把可安装的插件面复制到 packaging/runtime。

真源保持在仓库根（agents/、skills/、各 manifest）。本脚本把该面复制到一个生成目录，使
local-directory marketplace 可以在不包含仓库维护面（docs/、packaging/）的情况下对其进行快照。

复制只涉及常规文件。符号链接一律拒绝，确保生成树不能指向声明的面之外。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "agentflow" / "scripts"))
from check_skill_refs import manifest_version_errors, run as check_skill_refs
from workflow_lib.installation import RUNTIME_DIRECTORIES, RUNTIME_FILES, inventory, read_object, verify_inventory
from workflow_lib.snapshots import WorkflowError, no_symlinks

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_DEST = SCRIPT_DIR / "runtime"

def fail(message: str) -> int:
    print(f"packaging: {message}", file=sys.stderr)
    return 1


def assert_safe_destination(destination: Path) -> None:
    if ROOT.is_relative_to(destination):
        raise ValueError("拒绝覆盖仓库根或其任意祖先目录")
    if destination == SCRIPT_DIR:
        raise ValueError("拒绝覆盖 packaging/")
    for name in (*RUNTIME_DIRECTORIES, ".git", "docs"):
        if destination.is_relative_to(ROOT / name):
            raise ValueError(f"拒绝覆盖源树 {name}")
    for name in RUNTIME_FILES:
        if destination == ROOT / name:
            raise ValueError(f"拒绝覆盖源文件 {name}")
    if destination.exists():
        try:
            inventory(destination)
            if read_object(destination / "plugin.json").get("name") != read_object(ROOT / "plugin.json").get("name"):
                raise ValueError("插件名称不同")
        except (ValueError, OSError, WorkflowError) as exc:
            raise ValueError(f"目标并非本插件的生成树，拒绝覆盖：{destination}（{exc}）") from exc


def copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"不允许符号链接：{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"不允许符号链接：{source}")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if "__pycache__" in relative.parts or path.name == ".DS_Store" or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink():
            raise ValueError(f"不允许符号链接：{path}")
        if not path.is_file():
            continue
        copy_file(path, destination / relative)


def build(destination: Path) -> list[str]:
    destination.mkdir()
    copied: list[str] = []
    for name in RUNTIME_DIRECTORIES:
        source = ROOT / name
        if not source.is_dir():
            raise ValueError(f"缺少必需目录：{name}")
        copy_tree(source, destination / name)
        copied.append(name)
    for name in RUNTIME_FILES:
        source = ROOT / name
        if not source.is_file():
            raise ValueError(f"缺少必需文件：{name}")
        copy_file(source, destination / name)
        copied.append(name)
    return copied


def rebuild(destination: Path) -> list[str]:
    assert_safe_destination(destination)
    errors = manifest_version_errors(ROOT, source_only=True)
    if errors:
        raise ValueError("源码清单检查失败：\n" + "\n".join(errors))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{destination.name}.build-", dir=destination.parent) as staged:
        payload = Path(staged) / "payload"
        copied = build(payload)
        errors = check_skill_refs(payload)
        if errors:
            raise ValueError("生成包检查失败：\n" + "\n".join(errors))
        inventory(payload)
        lock = destination.with_name(f".{destination.name}.agentflow-build.lock")
        try:
            lock.mkdir()
        except FileExistsError as exc:
            raise ValueError(f"另一构建正在替换目标，或有待恢复的上一份产物：{lock}") from exc
        previous = lock / "previous"
        try:
            assert_safe_destination(destination)
            if destination.exists():
                destination.rename(previous)
            try:
                payload.rename(destination)
            except BaseException:
                if previous.exists():
                    previous.rename(destination)
                raise
        finally:
            # 留下无法恢复的上一份产物，便于人工恢复。
            if previous.exists() and destination.exists() and not payload.exists():
                shutil.rmtree(previous)
            if not previous.exists():
                lock.rmdir()
        return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        default=str(DEFAULT_DEST),
        help="输出目录；只可替换同名插件生成树，默认 packaging/runtime",
    )
    parser.add_argument("--verify-installed", help="只读核验安装载荷，不重建生成树")
    parser.add_argument("--expected-tree", default=str(DEFAULT_DEST))
    parser.add_argument("--codex-source", action="store_true", help="允许声明的 Codex 源码快照顶层维护文件")
    args = parser.parse_args(argv)
    if args.verify_installed:
        try:
            verify_inventory(inventory(Path(args.expected_tree)), Path(args.verify_installed),
                             codex_source=args.codex_source)
        except (OSError, ValueError, WorkflowError) as exc:
            return fail(str(exc))
        return 0
    try:
        destination = no_symlinks(Path(args.destination).expanduser())
        copied = rebuild(destination)
    except (OSError, ValueError, WorkflowError) as exc:
        return fail(str(exc))
    print(f"已写入 {destination}")
    print("已复制 " + ", ".join(copied))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
