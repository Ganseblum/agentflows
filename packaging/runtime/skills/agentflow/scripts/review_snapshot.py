#!/usr/bin/env python3
"""review_snapshot.py — 生成可回放的评审快照（评审简报钉修订的推荐形态）。

解决痛点：被评审对象是未提交工作区时，旧做法是给 reviewer 一串 sha256——无 Bash 的评审者
无法校验，修复后哈希全部失效，delta 轮只能全量重读。快照把「被评审那一刻」的文件复制下来：
复核可回放、修复后不失效、简报从「6 个 sha256 + 全量路径」变成「快照目录一行」。

用法：
  python3 review_snapshot.py --feature <批次目录> --round <n> --files <路径...>
                             [--repo <仓库根，默认当前目录>] [--out <快照父目录，默认 <feature>/reviews>]

行为：
  1. 校验文件清单（相对 --repo 解析；未提交 / 未跟踪内容照常读盘——这正是快照的意义）
  2. 复制到 <out>/snapshot-<round>/（保持相对路径结构；目录已存在即报错退出，不覆盖）
  3. 生成 MANIFEST.txt：时间戳、repo HEAD（无 git 时记 no-git）、reviewed_revision 行、
     每文件一行「sha256  字节数  相对路径」
  4. 打印可直接粘进评审简报的 reviewed_revision 与 read_scope 段
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = "MANIFEST.txt"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "no-git"


def make_snapshot(repo: Path, feature: Path, round_no: int, files: list[str],
                  out_parent: Path | None) -> tuple[Path, list[str]]:
    missing: list[str] = []
    resolved: list[tuple[Path, Path]] = []  # (abs_src, rel_from_repo)
    for f in files:
        src = (repo / f).resolve() if not Path(f).is_absolute() else Path(f).resolve()
        if not src.is_file():
            missing.append(f)
            continue
        try:
            rel = src.relative_to(repo.resolve())
        except ValueError:
            rel = Path(src.name)  # 仓外文件按 basename 收录
        resolved.append((src, rel))
    if missing:
        raise FileNotFoundError("以下文件不存在，未生成快照：" + "、".join(missing))
    if not resolved:
        raise ValueError("文件清单为空")

    snap = (out_parent or (feature / "reviews")) / f"snapshot-{round_no}"
    if snap.exists():
        raise FileExistsError(f"快照目录已存在，不覆盖：{snap}")
    copied: list[tuple[Path, Path]] = []
    try:
        for src, rel in resolved:
            dst = snap / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            copied.append((dst, rel))
    except Exception:
        shutil.rmtree(snap, ignore_errors=True)
        raise

    lines = [
        f"# review snapshot manifest",
        f"created_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"reviewed_revision: snapshot {snap.name} @ {git_head(repo)}",
        f"repo: {repo.resolve()}",
        f"files: {len(copied)}",
        "",
    ]
    for dst, rel in copied:
        lines.append(f"{sha256_file(dst)}  {dst.stat().st_size:>9}  {rel.as_posix()}")
    (snap / MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return snap, [rel.as_posix() for _, rel in copied]


def main() -> int:
    ap = argparse.ArgumentParser(description="生成评审快照（reviewed_revision 的可回放形态）")
    ap.add_argument("--feature", default=None, help="批次目录（快照默认落 <feature>/reviews/）")
    ap.add_argument("--round", default=None, type=int, help="评审轮次号（快照目录名 snapshot-<n>）")
    ap.add_argument("--files", nargs="+", default=None, help="被评审文件清单（相对 --repo）")
    ap.add_argument("--repo", default=".", help="仓库根（默认当前目录）")
    ap.add_argument("--out", default=None, help="快照父目录（默认 <feature>/reviews）")
    ap.add_argument("--self-test", action="store_true", help="在临时目录跑快照自测")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not (args.feature and args.round and args.files):
        ap.error("需要 --feature、--round、--files（或 --self-test）")

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"[错误] 仓库根不存在：{repo}", file=sys.stderr)
        return 2
    feature = Path(args.feature).resolve()
    if not feature.is_dir():
        print(f"[错误] 批次目录不存在：{feature}", file=sys.stderr)
        return 2
    out_parent = Path(args.out).resolve() if args.out else None

    try:
        snap, rels = make_snapshot(repo, feature, args.round, args.files, out_parent)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1

    print(f"[ok] 快照 -> {snap}")
    print("\n可直接粘进评审简报的两行：")
    print(f"reviewed_revision: snapshot {snap.name}（MANIFEST 含逐文件 sha256 与 HEAD）")
    print("read_scope（内联对象）：")
    for rel in rels:
        print(f"  - {snap / rel}")
    print(f"  - {snap / MANIFEST_NAME}")
    return 0


def _self_test() -> int:
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def check(name: str, fn) -> None:
        base = Path(tempfile.mkdtemp(prefix="af-snap-selftest-"))
        try:
            fn(base)
            results.append((name, True, ""))
        except AssertionError as exc:
            results.append((name, False, str(exc)))
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def setup(base: Path) -> tuple[Path, Path, Path]:
        repo = base / "repo"
        (repo / "src").mkdir(parents=True)
        (repo / "src" / "a.py").write_text("print('a')\n", encoding="utf-8")
        (repo / "src" / "b.py").write_text("print('b')\n", encoding="utf-8")
        feature = base / "feat"
        feature.mkdir()
        return repo, feature, repo / "src" / "a.py"

    def make(repo: Path, feature: Path, round_no: int, files: list[str]) -> Path:
        snap, _ = make_snapshot(repo, feature, round_no, files, None)
        return snap

    def snap_file(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    # 逐条注册显式测试函数
    results.clear()

    def t_basic(base: Path) -> None:
        repo, feature, _ = setup(base)
        snap = make(repo, feature, 1, ["src/a.py", "src/b.py"])
        assert snap.name == "snapshot-1"
        assert snap_file(snap / "src" / "a.py") == "print('a')\n"
        manifest = snap_file(snap / MANIFEST_NAME)
        assert "reviewed_revision: snapshot snapshot-1" in manifest
        assert hashlib.sha256(b"print('a')\n").hexdigest() in manifest

    def t_replay_after_edit(base: Path) -> None:
        repo, feature, a = setup(base)
        snap = make(repo, feature, 1, ["src/a.py"])
        a.write_text("print('changed')\n", encoding="utf-8")
        assert snap_file(snap / "src" / "a.py") == "print('a')\n", "快照随工作区漂移"
        assert snap_file(snap / MANIFEST_NAME).count("  src/a.py") == 1

    def t_round_isolation(base: Path) -> None:
        repo, feature, _ = setup(base)
        s1 = make(repo, feature, 1, ["src/a.py"])
        s2 = make(repo, feature, 2, ["src/b.py"])
        assert s1 != s2 and (feature / "reviews" / "snapshot-2").is_dir()

    def t_duplicate_round(base: Path) -> None:
        repo, feature, _ = setup(base)
        make(repo, feature, 1, ["src/a.py"])
        try:
            make(repo, feature, 1, ["src/a.py"])
        except FileExistsError:
            return
        raise AssertionError("重复轮次未报错")

    def t_missing_file(base: Path) -> None:
        repo, feature, _ = setup(base)
        try:
            make(repo, feature, 1, ["src/ghost.py"])
        except FileNotFoundError:
            assert not (feature / "reviews").exists(), "失败时不应留半成品"
            return
        raise AssertionError("缺失文件未报错")

    for name, fn in [
        ("基本复制与 MANIFEST", t_basic),
        ("修复后快照不漂移（可回放）", t_replay_after_edit),
        ("轮次目录隔离", t_round_isolation),
        ("重复轮次报错不覆盖", t_duplicate_round),
        ("缺失文件报错且无半成品", t_missing_file),
    ]:
        check(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
