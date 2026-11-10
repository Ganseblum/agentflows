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
  2. 复制到 <out>/snapshot-<round>/（仓内保持相对路径；仓外按绝对来源hash命名并记录source映射）
     复制前校验来源与目标一对一、路径安全且无用户symlink，拒保留名 MANIFEST.txt 碰撞；目录存在不覆盖
  3. 生成 MANIFEST.txt：时间戳、repo HEAD（无 git 时记 no-git）、reviewed_revision 行、
     每文件一行「sha256  字节数  相对路径」
  4. 打印可直接粘进评审简报的 reviewed_revision 与 read_scope 段

  --verify：先校验清单与快照自身file/大小/hash，再核当前来源（仓内相对路径或仓外source映射），
  输出逐文件 一致/改动/缺失 与汇总。旧无映射外部basename身份不可恢复，须重建；普通旧仓内快照兼容。
  只核对 MANIFEST 清单内文件——清单外的工作树改动不在核对面，快照必须包含完整变化文件清单。
  存在漂移时退出码 1——用于「批准后冻结」核对（contracts.md 评审结果节）：approved 之后至提交
  之前被评审文件不得改动，批次收口（提交前）运行一次，把「绑定仍成立」变成可复核输出。
  退出码：0 = 全部一致；1 = 有漂移；2 = 用法或 MANIFEST 问题。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from workflow_lib.review_bundle import (
    MANIFEST_NAME, load_snapshot, parse_manifest as strict_manifest,
    read_regular, safe_path, source_name, source_path, unique_paths,
)


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
    repo = safe_path(repo)
    feature = safe_path(feature)
    if round_no < 1 or not files:
        raise ValueError("轮次须 ≥1，文件清单不能为空")
    sources = [source_path(repo, f) for f in files]
    if len(sources) != len(set(sources)):
        raise ValueError("重复来源路径，未生成快照")
    resolved = [(src, *source_name(repo, src)) for src in sources]
    unique_paths([name for _, name, _ in resolved])
    # Read every source before creating output, so preflight cannot leave a partial snapshot.
    frozen = [(src, name, external, read_regular(src)) for src, name, external in resolved]
    snap = safe_path((out_parent or (feature / "reviews")) / f"snapshot-{round_no}")
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.mkdir()  # Exclusive ownership: never remove an existing or concurrently created directory.
    try:
        lines = [
            "# review snapshot manifest",
            f"created_at: {datetime.now(UTC).isoformat(timespec='seconds')}",
            f"reviewed_revision: snapshot {snap.name} @ {git_head(repo)}",
            f"repo: {repo}",
            f"files: {len(frozen)}",
            "",
        ]
        for src, name, external, data in frozen:
            dst = safe_path(snap / name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("xb") as stream:
                stream.write(data)
            lines.append(f"{hashlib.sha256(data).hexdigest()}  {len(data):>9}  {name}")
            if external:
                lines.append("source: " + json.dumps([name, str(src)], ensure_ascii=False))
        with (snap / MANIFEST_NAME).open("x", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
        load_snapshot(snap)
    except Exception:
        shutil.rmtree(snap)
        raise
    return snap, [name for _, name, _, _ in frozen]


def parse_manifest(manifest: Path) -> tuple[list[tuple[str, int, str]], int, int | None]:
    """兼容旧返回形状；破损、重复和不安全清单由共享解析器拒绝。"""
    parsed = strict_manifest(manifest)
    return ([(e.sha256, e.size, e.name) for e in parsed.entries],
            0, int(parsed.headers["files"]))


def verify_snapshot(repo: Path, snap: Path) -> list[tuple[str, str, str]]:
    """按 MANIFEST 对当前工作树逐文件核对。

    返回 [(状态, 相对路径, 细节)]，状态 ∈ 一致 | 改动 | 缺失。
    MANIFEST 缺失、无可解析文件行、有破损行或与头部 files: N 不一致时抛 ValueError——
    破损清单会把文件静默排除出核对面，给出假「绑定仍成立」，必须拒绝而不是带病核对。
    """
    repo = safe_path(repo)
    snapshot = load_snapshot(snap)  # Validate the frozen objects before comparing current sources.
    rows: list[tuple[str, str, str]] = []
    for entry in snapshot.manifest.entries:
        target = safe_path(snapshot.manifest.sources.get(entry.name, repo / entry.name))
        if not target.exists():
            rows.append(("缺失", entry.name, ""))
            continue
        data = read_regular(target)
        current = hashlib.sha256(data).hexdigest()
        if current == entry.sha256 and len(data) == entry.size:
            rows.append(("一致", entry.name, ""))
        else:
            rows.append(("改动", entry.name, f"快照 {entry.sha256[:12]} / 当前来源 {current[:12]}"))
    return rows


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        repo = safe_path(Path(args.repo))
        if not repo.is_dir():
            raise ValueError(f"仓库根不存在：{repo}")
        snap = safe_path(Path(args.verify))
        rows = verify_snapshot(repo, snap)
    except (OSError, ValueError) as exc:
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
    print("来源解释：有 source 映射的条目核对映射来源，其余条目只作为仓内相对路径核对。"
          "旧仓外 basename 没有可恢复的来源身份，不能据此核实仓外绑定，必须重建快照。")
    if drift:
        print("结论：快照与当前树不一致——approved 绑定已失效；"
              "按 contracts.md「批准后冻结」重开 spot 评审或重新快照。")
        return 1
    print("结论：快照与按上述来源解释的当前文件一致，绑定仍成立（不含旧仓外 basename 身份）。")
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

    try:
        repo = safe_path(Path(args.repo))
        feature = safe_path(Path(args.feature))
        if not repo.is_dir() or not feature.is_dir():
            raise ValueError("仓库根与批次目录必须存在")
        out_parent = safe_path(Path(args.out)) if args.out else None
        snap, rels = make_snapshot(repo, feature, args.round, args.files, out_parent)
    except (OSError, ValueError) as exc:
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
        except Exception as exc:
            results.append((name, False, f"{type(exc).__name__}: {exc}"))
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

    def rejects(fn, exceptions=(ValueError,)) -> None:
        try:
            fn()
        except exceptions:
            return
        raise AssertionError("预期拒绝，实际成功")

    def t_external_sources(base: Path) -> None:
        repo, feature, _ = setup(base)
        sources = []
        for side, content in (("x", b"FIRST\n"), ("y", b"SECOND\n")):
            source = base / side / "same.txt"
            source.parent.mkdir()
            source.write_bytes(content)
            sources.append(source)
        snap = make(repo, feature, 1, [str(p) for p in sources])
        frozen = load_snapshot(snap)
        assert len(frozen.objects) == 2 and set(frozen.objects.values()) == {b"FIRST\n", b"SECOND\n"}
        assert len(frozen.manifest.sources) == 2
        assert all(row[0] == "一致" for row in verify_snapshot(repo, snap))
        sources[0].write_bytes(b"CHANGED\n")
        sources[1].unlink()
        rows = verify_snapshot(repo, snap)
        assert {row[0] for row in rows} == {"改动", "缺失"}, rows
        second = make(repo, feature, 2, [str(sources[0])])
        assert set(load_snapshot(second).objects) <= set(frozen.objects), "仓外 namespace 随内容变化"

    def t_preflight_collisions(base: Path) -> None:
        repo, feature, _ = setup(base)
        rejects(lambda: make(repo, feature, 1, ["src/a.py", "src/a.py"]))
        assert not (feature / "reviews").exists()
        (repo / MANIFEST_NAME).write_text("source object", encoding="utf-8")
        rejects(lambda: make(repo, feature, 1, [MANIFEST_NAME]))
        assert not (feature / "reviews").exists(), "碰撞预检后不应产生输出"
        rejects(lambda: make(repo, feature, 1, ["../repo/src/a.py"]))

    def t_strict_manifest(base: Path) -> None:
        repo, feature, _ = setup(base)
        snap = make(repo, feature, 1, ["src/a.py"])
        manifest = snap / MANIFEST_NAME
        original = manifest.read_text(encoding="utf-8")
        entry = original.splitlines()[-1]
        variants = [original + "files: 1\n", original + "repo: /duplicate\n",
                    original.replace("files: 1", "files: 2"),
                    original.replace("files: 1\n", ""), original + "junk line\n",
                    original.replace("files: 1", "files: 2") + entry + "\n"]
        for name in ("../escape", "/absolute", "src/../a.py", "a\\b", MANIFEST_NAME,
                     MANIFEST_NAME + "/child"):
            variants.append(original.replace("src/a.py", name))
        for text in variants:
            manifest.write_text(text, encoding="utf-8")
            rejects(lambda: load_snapshot(snap))
            rejects(lambda: verify_snapshot(repo, snap))
        manifest.write_text(original, encoding="utf-8")
        target = snap / "src/a.py"
        target.write_bytes(b"x" * target.stat().st_size)  # Same size, different hash.
        rejects(lambda: load_snapshot(snap))
        target.write_bytes(b"size drift")
        rejects(lambda: verify_snapshot(repo, snap))
        target.unlink()
        rejects(lambda: load_snapshot(snap))
        target.write_bytes((repo / "src/a.py").read_bytes())
        assert verify_snapshot(repo, snap)[0][0] == "一致"

    def t_legacy_snapshot(base: Path) -> None:
        repo, feature, _ = setup(base)
        snap = make(repo, feature, 1, ["src/a.py"])
        manifest = snap / MANIFEST_NAME
        entry = manifest.read_text(encoding="utf-8").splitlines()[-1]
        manifest.write_text("files: 1\n" + entry + "\n", encoding="utf-8")
        assert verify_snapshot(repo, snap)[0][0] == "一致", "普通旧仓内快照应继续读取"

    def t_symlinks(base: Path) -> None:
        repo, feature, a = setup(base)
        (repo / "link.py").symlink_to(a)
        rejects(lambda: make(repo, feature, 1, ["link.py"]))
        (base / "repo-link").symlink_to(repo, target_is_directory=True)
        rejects(lambda: make(base / "repo-link", feature, 1, ["src/a.py"]))
        (feature / "reviews").symlink_to(repo, target_is_directory=True)
        rejects(lambda: make(repo, feature, 1, ["src/a.py"]))
        (feature / "reviews").unlink()
        snap = make(repo, feature, 1, ["src/a.py"])
        target = snap / "src/a.py"
        target.unlink()
        target.symlink_to(a)
        rejects(lambda: verify_snapshot(repo, snap))
        target.unlink()
        target.write_bytes(a.read_bytes())
        manifest = snap / MANIFEST_NAME
        saved = base / "saved-manifest"
        manifest.rename(saved)
        manifest.symlink_to(saved)
        rejects(lambda: load_snapshot(snap))

    def t_failure_cleanup(base: Path) -> None:
        from unittest.mock import patch
        repo, feature, _ = setup(base)
        existing = make(repo, feature, 1, ["src/a.py"])
        before = (existing / MANIFEST_NAME).read_bytes()
        real_open = Path.open
        for failed_name in ("b.py", MANIFEST_NAME):
            def failing_open(path, mode="r", *args, **kwargs):
                if mode in {"x", "xb"} and path.name == failed_name:
                    raise OSError("injected copy/manifest failure")
                return real_open(path, mode, *args, **kwargs)
            with patch.object(Path, "open", failing_open):
                rejects(lambda: make(repo, feature, 2, ["src/a.py", "src/b.py"]), (OSError,))
            assert not (feature / "reviews/snapshot-2").exists(), "失败留下本轮半成品"
            assert (existing / MANIFEST_NAME).read_bytes() == before, "清理误删旧轮次"
        rejects(lambda: make(repo, feature, 1, ["src/b.py"]), (FileExistsError,))
        assert (existing / MANIFEST_NAME).read_bytes() == before

    for name, fn in [
        ("基本复制与 MANIFEST", t_basic),
        ("修复后快照不漂移（可回放）", t_replay_after_edit),
        ("轮次目录隔离", t_round_isolation),
        ("重复轮次报错不覆盖", t_duplicate_round),
        ("缺失文件报错且无半成品", t_missing_file),
        ("verify：未漂移全一致", t_verify_clean),
        ("verify：改动与缺失逐文件报出", t_verify_drift),
        ("verify：退出码 0/1 与结论行", t_verify_exit_codes),
        ("verify：破损清单与声明数量不符拒绝", t_verify_rejects_broken_manifest),
        ("仓外同名文件分离、稳定来源映射与漂移核对", t_external_sources),
        ("预检重复来源、保留名与路径逃逸无半成品", t_preflight_collisions),
        ("严格清单头/数量/路径/重复与快照缺失/大小/hash漂移", t_strict_manifest),
        ("普通旧仓内快照兼容", t_legacy_snapshot),
        ("源/父目录/输出/冻结对象/MANIFEST拒绝symlink", t_symlinks),
        ("复制与MANIFEST写入失败只清本轮目录", t_failure_cleanup),
    ]:
        check(name, fn)

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
