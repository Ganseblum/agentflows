#!/usr/bin/env python3
"""受跟踪文件在覆盖式写入前后的「他人未提交改动」保全校验。

问题：一个工作树里已有别人未提交的改动时，若用 `git show HEAD:<path> > <path>`、
`git checkout`、或脚本整文件重写，会把那些改动静默还原掉。这不是「撤销」，是数据丢失。

用法：

    python3 tools/dirty-guard.py snapshot <快照文件>
    ... 执行你认为安全的写操作 ...
    python3 tools/dirty-guard.py verify <快照文件>

verify 对被跟踪、且快照时处于 dirty 的每个文件，检查它当时的「新增行」是否仍然存在于
当前文件里；任一新增行消失即失败退出（退出码 1），并逐条打印消失的原行。

退出码：0 保全，1 有未提交改动消失，2 用法或环境问题。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

# 只看有内容变化的行；空白差异不构成保全证据
MIN_LINE_LEN = 1


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {proc.stderr.strip()}")
    return proc.stdout


def dirty_tracked(root: Path) -> list[str]:
    """受跟踪且工作树内容与索引不同的文件（不含未跟踪文件）。

    `-z` 输出以 NUL 分隔且不对非 ASCII 路径做八进制转义——本仓文件名多是中文，
    用默认的 `--name-only` 会拿到 `"episodes/\\345..."` 这种转义串，路径解析必然失败。
    """
    out = git(root, "diff", "--name-only", "-z", "--diff-filter=ACMRT")
    return [p for p in out.split("\0") if p.strip()]


def added_lines(root: Path, path: str) -> list[str]:
    """该文件相对索引的新增行（不含 `+++` 头）。"""
    out = git(root, "diff", "--unified=0", "--", path)
    lines: list[str] = []
    for line in out.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith("+") and len(line) - 1 >= MIN_LINE_LEN:
            lines.append(line[1:])
    return lines


def cmd_snapshot(root: Path, target: Path) -> int:
    data: dict[str, dict[str, object]] = {}
    for path in dirty_tracked(root):
        full = root / path
        content = full.read_bytes() if full.is_file() else b""
        data[path] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "added": added_lines(root, path),
        }
    target.write_text(
        json.dumps({"root": str(root), "files": data}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    skipped = len(git(root, "ls-files", "-m").splitlines()) - len(data)
    print(f"已记录 {len(data)} 个 dirty 受跟踪文件 → {target}")
    if skipped > 0:
        print(f"注意：{skipped} 个文件无法解析 diff（可能是二进制），未纳入保全校验")
    return 0


def cmd_verify(root: Path, target: Path) -> int:
    snap = json.loads(target.read_text(encoding="utf-8"))
    files: dict[str, dict[str, object]] = snap.get("files", {})
    if not files:
        print("快照为空，无需校验")
        return 0

    lost_total = 0
    for path, meta in sorted(files.items()):
        full = root / path
        if not full.is_file():
            print(f"FAIL {path}：快照后被删除")
            lost_total += 1
            continue
        current = full.read_text(encoding="utf-8", errors="replace")
        current_lines = set(current.splitlines())
        added_raw = meta.get("added") or []
        added = [str(x) for x in added_raw] if isinstance(added_raw, list) else []
        missing = [ln for ln in added if ln not in current_lines]
        if not missing:
            continue
        lost_total += len(missing)
        print(f"FAIL {path}：{len(missing)} 行未提交改动消失")
        for ln in missing[:10]:
            print(f"      - {ln}")
        if len(missing) > 10:
            print(f"      … 另有 {len(missing) - 10} 行")

    if lost_total:
        print()
        print(f"失败：合计 {lost_total} 行他人未提交改动被写入操作覆盖。")
        print("恢复方式：从 git 的不可达对象或编辑器历史里捞回原文；不要用 checkout 再覆盖一次。")
        return 1
    print(f"PASS：{len(files)} 个 dirty 文件的新增内容全部保全")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["snapshot", "verify"])
    ap.add_argument("target", help="快照文件路径")
    ap.add_argument("--root", default=".", help="git 工作树根，默认当前目录")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        git(root, "rev-parse", "--git-dir")
    except (RuntimeError, OSError) as exc:
        print(f"错误：{root} 不是 git 工作树（{exc}）", file=sys.stderr)
        return 2

    return (cmd_snapshot if args.action == "snapshot" else cmd_verify)(
        root, Path(args.target)
    )


if __name__ == "__main__":
    raise SystemExit(main())
