#!/usr/bin/env python3
"""工作树在不可逆操作前后的「未提交内容」保全、核验与清理。

两类事故同源：内容只存在于工作树或索引里，git 没有副本。

- 覆盖式写入（`git show HEAD:<path> > <path>`、`git checkout`、脚本整文件重写）会把
  别人的未提交改动静默还原掉。
- 合并、删分支、`git worktree remove`、`git stash drop` 会把从未进入对象库的改动直接销毁。

**基线是 HEAD，不是索引。** 工作树与索引一致、风险全在「索引 vs HEAD」时（暂存了大量改动或
改名），只比索引的写法会拍出一份空快照——看着拍了，等于没拍。

用法：

    python3 tools/dirty-guard.py snapshot <快照文件> [--tar <仓库外目录>]
    ... 执行不可逆操作 ...
    python3 tools/dirty-guard.py verify <快照文件> [--accept <理由>]
    python3 tools/dirty-guard.py cleanup <快照文件>

`snapshot` 记录三类风险内容：相对 HEAD 有新增行的受跟踪文件（含改名后的新路径）、未跟踪文件、
未解决索引项（含各 stage 的 blob）。`--tar` 额外把前两类文件的当时内容归档到**仓库外**目录——
逐行比对只能证明「有没有丢」，不能恢复从未进过对象库的东西。

`verify` 逐文件检查快照时的新增行是否仍在当前文件里，消失即红。报红时先分辨那些行是不是自己
刚刚有意改写的：确实是有意的，用 `--accept "<理由>"` 记一句，理由与核验时间一起写回快照。

`cleanup` 只有在快照带 `verify` 通过标记时才删除快照文件与归档——核验跑完，原件就该退场，
不留「以防万一」的散落备份。

快照与归档都是**本地临时件，不得提交**：两者都必须落在仓库外，工具对落在仓库内的目标直接
报错退出。未提交内容的副本一旦进版本库，临时现场就被固化成历史，还会被下次操作连带。

退出码：0 成功，1 有内容消失或删除前置未满足，2 用法或环境问题。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

# 只看有内容变化的行；空白差异不构成保全证据
MIN_LINE_LEN = 1

# 单文件最多记录多少新增行；超过则截断并标注，避免大改名把快照撑爆
MAX_ADDED_LINES = 4000

SNAPSHOT_VERSION = 2

# 归档里带上这些文件即可覆盖恢复所需；缓存与对象库不属于「未提交内容」
TAR_EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache", "node_modules"}


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {proc.stderr.strip()}")
    return proc.stdout


def now() -> str:
    # 本工具要在「出事前一刻」就能跑，所以兼容系统 python3（本机 3.9.6）；
    # `datetime.UTC` 别名需 3.11+，故保留 timezone.utc 形态。
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def unmerged_paths(root: Path) -> dict[str, dict[str, str]]:
    """未解决索引项：路径 → {stage1/2/3: blob}。

    `-z` 的每条记录是 `<mode> <sha> <stage>\\t<path>`，NUL 分帧；本仓多是中文路径，
    不带 `-z` 会拿到八进制转义串，后续按路径读文件必然失败。
    """
    out = git(root, "ls-files", "-u", "-z")
    result: dict[str, dict[str, str]] = {}
    for record in out.split("\0"):
        if not record.strip():
            continue
        meta, _, path = record.partition("\t")
        parts = meta.split()
        if len(parts) != 3 or not path:
            continue
        result.setdefault(path, {})[f"stage{parts[2]}"] = parts[1]
    return result


def tracked_at_risk(root: Path) -> list[str]:
    """相对 HEAD 有新增内容的受跟踪文件（改名按新路径计），排除未解决项。

    改名后的文件在全新路径上会以 A 出现，其每一行都算新增——这正是需要的：
    改名把内容同时挪进了「索引 vs HEAD」，只比索引看不见它。
    """
    out = git(root, "diff", "HEAD", "--name-only", "-z", "--diff-filter=ACMRT")
    skip = unmerged_paths(root)
    return [p for p in out.split("\0") if p.strip() and p not in skip]


def untracked_files(root: Path) -> list[str]:
    out = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    return [p for p in out.split("\0") if p.strip()]


def added_lines(root: Path, path: str) -> tuple[list[str], int]:
    """该文件相对 HEAD 的新增行，返回（保留的行, 总新增行数）。"""
    out = git(root, "diff", "HEAD", "--unified=0", "--", path)
    lines: list[str] = []
    total = 0
    for line in out.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith("+") and len(line) - 1 >= MIN_LINE_LEN:
            total += 1
            if len(lines) < MAX_ADDED_LINES:
                lines.append(line[1:])
    return lines, total


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cmd_snapshot(root: Path, target: Path, tar_dir: Path | None) -> int:
    if str(target.resolve()).startswith(f"{root}{os.sep}"):
        print(
            f"错误：快照目标 {target} 在仓库内（{root}）。快照是本地临时件，"
            "不得进入版本库——它记录的是尚未提交的内容，提交它等于把临时现场固化，"
            "还会被下次操作连带。请放到仓库外（如 /tmp 或 ~ 下的临时目录）。",
            file=sys.stderr,
        )
        return 2
    files: dict[str, dict[str, object]] = {}
    added_totals: dict[str, int] = {}
    unreadable: list[str] = []
    for path in tracked_at_risk(root):
        full = root / path
        added, total = added_lines(root, path)
        if full.is_file():
            digest = sha256_of(full)
        else:
            digest = ""
            added = []
            unreadable.append(path)
        files[path] = {
            "sha256": digest,
            "added": added,
            "added_total": total,
            "truncated": total > len(added),
        }
        added_totals[path] = total

    untracked: dict[str, dict[str, object]] = {}
    for path in untracked_files(root):
        full = root / path
        if not full.is_file():
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        untracked[path] = {
            "sha256": sha256_of(full),
            "lines": sum(1 for line in text.splitlines() if line.strip()),
        }

    unmerged = unmerged_paths(root)
    for path in list(unmerged):
        full = root / path
        unmerged[path]["on_disk_sha256"] = sha256_of(full) if full.is_file() else ""
    archive: dict[str, str] = {}
    if tar_dir is not None:
        if str(tar_dir.resolve()).startswith(f"{root}{os.sep}"):
            print(
                f"错误：归档目录 {tar_dir} 在仓库内（{root}）。"
                "快照与归档必须落在仓库外——留在树里既会被下次操作连带，又会污染状态。",
                file=sys.stderr,
            )
            return 2
        tar_dir.mkdir(parents=True, exist_ok=True)
        archive_path = tar_dir / "at-risk.tar"
        with tarfile.open(archive_path, "w") as handle:
            for path in list(files) + list(untracked) + list(unmerged):
                parts = Path(path).parts
                if any(part in TAR_EXCLUDE_DIRS for part in parts):
                    continue
                full = root / path
                if full.is_file():
                    handle.add(full, arcname=path, recursive=False)
        archive = {
            "path": str(archive_path.resolve()),
            "sha256": sha256_of(archive_path),
        }

    head_sha = git(root, "rev-parse", "HEAD").strip()
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    payload = {
        "version": SNAPSHOT_VERSION,
        "root": str(root),
        "taken_at": now(),
        "head": head_sha,
        "branch": branch,
        "files": files,
        "untracked": untracked,
        "unmerged": unmerged,
        "archive": archive,
        "verified": None,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已记录 → {target}")
    print(f"  HEAD={head_sha[:7]} 分支={branch}")
    print(f"  受跟踪有新增内容: {len(files)} 个（新增行合计 {sum(added_totals.values())}）")
    print(f"  未跟踪文件: {len(untracked)} 个")
    print(f"  未解决索引项: {len(unmerged)} 个")
    if archive:
        print(f"  当时内容归档: {archive['path']}")
    truncated = [p for p, m in files.items() if m["truncated"]]
    if truncated:
        print(f"  注意：{len(truncated)} 个文件的新增行超过 {MAX_ADDED_LINES} 行已截断"
              f"（如 {'、'.join(truncated[:2])}）；逐行核验只覆盖前 {MAX_ADDED_LINES} 行，"
              "其余靠 --tar 归档保全")
    if unreadable:
        print(f"  注意：{len(unreadable)} 个文件在盘上读不到（已删除/未落地），未纳入逐行核验")
    if not files and not untracked and not unmerged:
        print("  警告：工作树相对 HEAD 无任何未提交内容——这份快照是空的，"
              "若你正要做的操作会销毁内容，说明该内容不在本工作树里，另找载体")
    return 0


def cmd_verify(root: Path, target: Path, accept: str | None) -> int:
    snap = json.loads(target.read_text(encoding="utf-8"))
    files: dict[str, dict[str, object]] = snap.get("files") or {}
    untracked: dict[str, dict[str, object]] = snap.get("untracked") or {}

    lost: list[tuple[str, list[str]]] = []
    gone: list[str] = []

    for path, meta in sorted(files.items()):
        full = root / path
        if not full.is_file():
            gone.append(path)
            continue
        current_lines = set(full.read_text(encoding="utf-8", errors="replace").splitlines())
        raw = meta.get("added")
        added = [str(x) for x in raw] if isinstance(raw, list) else []
        missing = [line for line in added if line not in current_lines]
        if missing:
            lost.append((path, missing))

    vanished_untracked = [
        path for path in sorted(untracked) if not (root / path).is_file()
    ]

    # 未解决项不能按 diff 逐行核（git 对冲突文件给的是 combined diff），改核 stage 内容：
    # ours(stage2)/theirs(stage3) 的每一行都必须在当前文件里找得到，否则就是被静默丢弃。
    unmerged_reported: list[str] = []
    for path, stages in sorted((snap.get("unmerged") or {}).items()):
        full = root / path
        if not full.is_file():
            lost.append((path, [f"<整个未解决文件在盘上消失，stage 内容仅存对象库：{stages}>"]))
            continue
        current_lines = set(full.read_text(encoding="utf-8", errors="replace").splitlines())
        for stage in ("stage2", "stage3"):
            sha = str(stages.get(stage) or "")
            if not sha:
                continue
            try:
                blob = git(root, "cat-file", "blob", sha)
            except RuntimeError:
                print(f"  注意 {path}：{stage} 的 blob {sha[:8]} 已不可达，无法逐行核验")
                continue
            missing = [ln for ln in blob.splitlines() if ln.strip() and ln not in current_lines]
            if missing:
                lost.append((f"{path}（{stage}）", missing))
        unmerged_reported.append(path)

    checked = len(files) + len(untracked) + len(unmerged_reported)
    if gone:
        print(f"FAIL：{len(gone)} 个受跟踪文件在快照后被删除")
        for path in gone[:10]:
            print(f"      - {path}")
    for path, missing in lost:
        print(f"FAIL {path}：{len(missing)} 行内容消失")
        for line in missing[:10]:
            print(f"      - {line}")
        if len(missing) > 10:
            print(f"      … 另有 {len(missing) - 10} 行")
    if vanished_untracked:
        print(f"FAIL：{len(vanished_untracked)} 个未跟踪文件消失（从未进对象库，git 里没有副本）")
        for path in vanished_untracked[:10]:
            print(f"      - {path}")

    failed = bool(gone or lost or vanished_untracked)
    if failed and not accept:
        print()
        print("失败：存在未提交内容消失。先分辨是不是你自己刚刚有意改写的——"
              "自己改写同一行也会报红，这是已知局限。")
        archive = (snap.get("archive") or {}).get("path")
        print("确属有意改写时：verify <快照> --accept \"<理由>\"；"
              + (f"需要取回原文时：tar -tf {archive}" if archive else "本次未建归档，无原件可取"))
        return 1

    reason = accept or "逐行保全通过，无消失内容"
    snap["verified"] = {
        "at": now(),
        "checked_files": checked,
        "lost_reported": len(lost) + len(gone) + len(vanished_untracked),
        "accept_reason": reason,
    }
    target.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    if failed:
        print(f"已按 --accept 记录理由并放行清理：{reason}")
    else:
        print(f"PASS：{checked} 个文件的未提交内容全部保全"
              f"（其中未解决项 {len(unmerged_reported)} 个按 stage 内容核；{reason}）")
    print("核验标记已写入快照，cleanup 可以放行。")
    return 0


def cmd_cleanup(root: Path, target: Path) -> int:
    snap = json.loads(target.read_text(encoding="utf-8"))
    verified = snap.get("verified")
    if not isinstance(verified, dict) or not verified.get("at"):
        print(
            "拒绝删除：该快照还没有通过的 verify 标记。\n"
            "  先跑 verify <快照>（有内容消失且确属有意改写时加 --accept \"<理由>\"），"
            "核验完成后 cleanup 才会放行。",
            file=sys.stderr,
        )
        return 1

    removed: list[str] = []
    archive = snap.get("archive") or {}
    archive_path = archive.get("path")
    if archive_path:
        path = Path(str(archive_path))
        if path.is_file():
            actual = sha256_of(path)
            if actual != archive.get("sha256"):
                print(f"错误：归档 {path} 的 sha256 与快照记录不一致，拒绝删除", file=sys.stderr)
                return 2
            path.unlink()
            removed.append(str(path))
            side = path.with_suffix(path.suffix + ".sha256")
            if side.is_file():
                side.unlink()
                removed.append(str(side))
    target.unlink()
    removed.append(str(target))

    print(f"已清理快照（核验时间 {verified['at']}，理由：{verified['accept_reason']}）")
    for item in removed:
        print(f"  - {item}")
    print(f"  剩余保全原件：0（工作树 {root} 之外不再留有副本）")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["snapshot", "verify", "cleanup"])
    ap.add_argument("target", help="快照文件路径")
    ap.add_argument("--root", default=".", help="git 工作树根，默认当前目录")
    ap.add_argument("--tar", help="把未提交内容的当时副本归档到该目录（必须在仓库外）")
    ap.add_argument("--accept", help="报红但确属自己有意改写时，写明理由并放行清理")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        git(root, "rev-parse", "--git-dir")
    except (RuntimeError, OSError) as exc:
        print(f"错误：{root} 不是 git 工作树（{exc}）", file=sys.stderr)
        return 2

    target = Path(args.target)
    if args.action == "snapshot":
        return cmd_snapshot(root, target, Path(args.tar) if args.tar else None)
    if args.action == "verify":
        return cmd_verify(root, target, args.accept)
    return cmd_cleanup(root, target)


if __name__ == "__main__":
    raise SystemExit(main())
