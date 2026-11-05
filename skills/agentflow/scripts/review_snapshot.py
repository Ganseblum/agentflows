#!/usr/bin/env python3
"""review_snapshot.py — 生成可回放的评审快照（评审简报钉修订的推荐形态）。

解决痛点：被评审对象是未提交工作区时，旧做法是给 reviewer 一串 sha256——无 Bash 的评审者
无法校验，修复后哈希全部失效，delta 轮只能全量重读。快照把「被评审那一刻」的文件复制下来：
复核可回放、修复后不失效、简报从「6 个 sha256 + 全量路径」变成「快照目录一行」。

用法：
  python3 review_snapshot.py --feature <批次目录> --round <n> --files <路径...>
                             [--repo <仓库根，默认当前目录>] [--out <快照父目录，默认 <feature>/reviews>]
  python3 review_snapshot.py --verify <快照目录> [--repo <仓库根，默认当前目录>]

行为：
  1. 校验文件清单（相对 --repo 解析；未提交 / 未跟踪内容照常读盘——这正是快照的意义）
  2. 复制到 <out>/snapshot-<round>/（保持相对路径结构；目录已存在即报错退出，不覆盖）
  3. 生成 MANIFEST.txt：时间戳、repo HEAD（无 git 时记 no-git）、reviewed_revision 行、
     每文件一行「sha256  字节数  相对路径」
  4. 打印可直接粘进评审简报的 reviewed_revision 与 read_scope 段

  --verify：按 MANIFEST 对当前仓库工作树逐文件重算 sha256，输出逐文件 一致/改动/缺失 与汇总。
  只核对 MANIFEST 清单内文件——清单外的工作树改动不在核对面，快照必须包含完整变化文件清单。
  存在漂移时退出码 1——用于「批准后冻结」核对（contracts.md 评审结果节）：approved 之后至提交
  之前被评审文件不得改动，批次收口（提交前）运行一次，把「绑定仍成立」变成可复核输出。
  退出码：0 = 全部一致；1 = 有漂移；2 = 用法或 MANIFEST 问题。
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

MANIFEST_NAME = "MANIFEST.txt"
_MANIFEST_LINE = re.compile(r"^([0-9a-f]{64})\s+(\d+)\s+(.+)$")


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
        "# review snapshot manifest",
        f"created_at: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"reviewed_revision: snapshot {snap.name} @ {git_head(repo)}",
        f"repo: {repo.resolve()}",
        f"files: {len(copied)}",
        "",
    ]
    for dst, rel in copied:
        lines.append(f"{sha256_file(dst)}  {dst.stat().st_size:>9}  {rel.as_posix()}")
    (snap / MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return snap, [rel.as_posix() for _, rel in copied]


_HEADER_KEYS = ("created_at:", "reviewed_revision:", "repo:", "files:")


def parse_manifest(manifest: Path) -> tuple[list[tuple[str, int, str]], int, int | None]:
    """解析 MANIFEST，返回 (文件行, 无法解析行数, 头部声明的 files: N 或 None)。"""
    entries: list[tuple[str, int, str]] = []
    skipped = 0
    declared_files: int | None = None
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        raw = raw.rstrip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith(_HEADER_KEYS):
            if raw.startswith("files:"):
                try:
                    declared_files = int(raw.split(":", 1)[1].strip())
                except ValueError:
                    skipped += 1
            continue
        m = _MANIFEST_LINE.match(raw)
        if m:
            entries.append((m.group(1), int(m.group(2)), m.group(3).strip()))
        else:
            skipped += 1
    return entries, skipped, declared_files


def verify_snapshot(repo: Path, snap: Path) -> list[tuple[str, str, str]]:
    """按 MANIFEST 对当前工作树逐文件核对。

    返回 [(状态, 相对路径, 细节)]，状态 ∈ 一致 | 改动 | 缺失。
    MANIFEST 缺失、无可解析文件行、有破损行或与头部 files: N 不一致时抛 ValueError——
    破损清单会把文件静默排除出核对面，给出假「绑定仍成立」，必须拒绝而不是带病核对。
    """
    manifest = snap / MANIFEST_NAME
    if not manifest.is_file():
        raise ValueError(f"快照目录缺 {MANIFEST_NAME}：{snap}")
    entries, skipped, declared = parse_manifest(manifest)
    if not entries:
        raise ValueError(f"MANIFEST 无可解析文件行：{manifest}")
    if skipped:
        raise ValueError(f"MANIFEST 有 {skipped} 行无法解析——破损清单拒绝核对：{manifest}")
    if declared is not None and declared != len(entries):
        raise ValueError(f"MANIFEST files: {declared} 与实际文件行 {len(entries)} 不一致：{manifest}")
    rows: list[tuple[str, str, str]] = []
    for sha, _size, rel in entries:
        target = repo / rel
        if not target.is_file():
            rows.append(("缺失", rel, ""))
            continue
        current = sha256_file(target)
        if current == sha:
            rows.append(("一致", rel, ""))
        else:
            rows.append(("改动", rel, f"快照 {sha[:12]} / 当前树 {current[:12]}"))
    return rows


def cmd_verify(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"[错误] 仓库根不存在：{repo}", file=sys.stderr)
        return 2
    snap = Path(args.verify).resolve()
    try:
        rows = verify_snapshot(repo, snap)
    except ValueError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 2
    print(f"核对快照：{snap}")
    print(f"仓库根：{repo}")
    for status, rel, detail in rows:
        suffix = f"    {detail}" if detail else ""
        print(f"  {status}    {rel}{suffix}")
    drift = sum(1 for status, _, _ in rows if status != "一致")
    total = len(rows)
    print(f"汇总：{total - drift}/{total} 一致，{drift} 漂移")
    print("注：仅核对 MANIFEST 清单内文件；清单外工作树改动未覆盖——快照必须包含完整变化文件清单。")
    if drift:
        print("结论：快照与当前树不一致——approved 绑定已失效；"
              "按 contracts.md「批准后冻结」重开 spot 评审或重新快照。")
        return 1
    print("结论：快照与当前树一致，绑定仍成立。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="生成评审快照（reviewed_revision 的可回放形态）")
    ap.add_argument("--feature", default=None, help="批次目录（快照默认落 <feature>/reviews/）")
    ap.add_argument("--round", default=None, type=int, help="评审轮次号（快照目录名 snapshot-<n>）")
    ap.add_argument("--files", nargs="+", default=None, help="被评审文件清单（相对 --repo）")
    ap.add_argument("--repo", default=".", help="仓库根（默认当前目录）")
    ap.add_argument("--out", default=None, help="快照父目录（默认 <feature>/reviews）")
    ap.add_argument("--verify", default=None, metavar="SNAPSHOT",
                    help="核对模式：按 MANIFEST 对当前工作树逐文件重算 sha256，报漂移")
    ap.add_argument("--self-test", action="store_true", help="在临时目录跑快照自测")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if args.verify:
        return cmd_verify(args)
    if not (args.feature and args.round and args.files):
        ap.error("需要 --feature、--round、--files（或 --verify <快照目录>，或 --self-test）")

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

    def t_verify_clean(base: Path) -> None:
        repo, feature, _ = setup(base)
        snap = make(repo, feature, 1, ["src/a.py", "src/b.py"])
        rows = verify_snapshot(repo, snap)
        assert len(rows) == 2 and all(r[0] == "一致" for r in rows), rows

    def t_verify_drift(base: Path) -> None:
        repo, feature, a = setup(base)
        snap = make(repo, feature, 1, ["src/a.py", "src/b.py"])
        a.write_text("print('changed')\n", encoding="utf-8")
        (repo / "src" / "b.py").unlink()
        rows = verify_snapshot(repo, snap)
        status = {rel: st for st, rel, _ in rows}
        assert status["src/a.py"] == "改动", status
        assert status["src/b.py"] == "缺失", status

    def t_verify_exit_codes(base: Path) -> None:
        import contextlib
        import io
        repo, feature, a = setup(base)
        snap = make(repo, feature, 1, ["src/a.py"])
        ns = argparse.Namespace(repo=str(repo), verify=str(snap))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code_clean = cmd_verify(ns)
        assert code_clean == 0, f"未漂移快照应退出 0，实际 {code_clean}"
        assert "绑定仍成立" in buf.getvalue()
        a.write_text("print('changed')\n", encoding="utf-8")
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            code_drift = cmd_verify(ns)
        assert code_drift == 1, f"漂移快照应退出 1，实际 {code_drift}"
        assert "改动" in buf2.getvalue() and "绑定已失效" in buf2.getvalue()

    def t_verify_rejects_broken_manifest(base: Path) -> None:
        import contextlib
        import io
        repo, feature, _ = setup(base)
        snap = make(repo, feature, 1, ["src/a.py", "src/b.py"])
        ns = argparse.Namespace(repo=str(repo), verify=str(snap))
        manifest = snap / MANIFEST_NAME
        original = manifest.read_text(encoding="utf-8")
        manifest.write_text(original + "deadbeef  10  src/a.py\n", encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cmd_verify(ns)
        assert code == 2, f"破损行应退出 2，实际 {code}"
        manifest.write_text(original + hashlib.sha256(b"x").hexdigest() + "        1  src/ghost.py\n",
                            encoding="utf-8")
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            code2 = cmd_verify(ns)
        assert code2 == 2, f"files: N 与文件行不一致应退出 2，实际 {code2}"

    for name, fn in [
        ("基本复制与 MANIFEST", t_basic),
        ("修复后快照不漂移（可回放）", t_replay_after_edit),
        ("轮次目录隔离", t_round_isolation),
        ("重复轮次报错不覆盖", t_duplicate_round),
        ("缺失文件报错且无半成品", t_missing_file),
        ("verify：未漂移全一致", t_verify_clean),
        ("verify：改动与缺失逐文件报出", t_verify_drift),
        ("verify：退出码 0/1 与结论行", t_verify_exit_codes),
    ]:
        check(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
