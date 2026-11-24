"""Strict review manifests and byte-frozen review objects shared by both CLIs."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess

from .snapshots import WorkflowError, no_symlinks, relative_name

MANIFEST_NAME = "MANIFEST.txt"
EXTERNAL_NAMESPACE = "__review_external__"
_ENTRY = re.compile(r"^([0-9a-f]{64})[ \t]+([0-9]+)[ \t]+(.+)$")
_COMMIT = re.compile(r"^[0-9a-fA-F]{7,40}$")
_HEADERS = {"created_at", "reviewed_revision", "repo", "files"}


def safe_path(path: Path) -> Path:
    try:
        return no_symlinks(path)
    except WorkflowError as exc:
        raise ValueError(str(exc)) from exc


def safe_name(value: str) -> str:
    try:
        name = relative_name(value)
    except WorkflowError as exc:
        raise ValueError(str(exc)) from exc
    if (any(ord(c) < 32 or ord(c) == 127 for c in name)
            or len(name.splitlines()) != 1):
        raise ValueError(f"控制字符不能用于评审路径：{value!r}")
    if any(part != part.strip() for part in name.split("/")):
        raise ValueError(f"评审路径分量不能以空白开头或结尾：{value!r}")
    if name == MANIFEST_NAME or name.startswith(MANIFEST_NAME + "/"):
        raise ValueError(f"评审路径与保留名 {MANIFEST_NAME} 碰撞：{name}")
    return name


def source_path(repo: Path, value: Path | str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        safe_name(path.as_posix())
        path = repo / path
    return safe_path(path)


def source_name(repo: Path, source: Path) -> tuple[str, bool]:
    try:
        relative = source.relative_to(repo)
    except ValueError:
        # The full canonical source path, not its basename, is the stable identity.
        digest = hashlib.sha256(str(source).encode("utf-8")).hexdigest()
        return safe_name(f"{EXTERNAL_NAMESPACE}/{digest}/{source.name}"), True
    return safe_name(relative.as_posix()), False


def read_regular(path: Path) -> bytes:
    path = safe_path(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"需要普通文件：{path}")
    return path.read_bytes()


def unique_paths(names: list[str]) -> None:
    seen: set[str] = set()
    for name in names:
        safe_name(name)
        if name in seen:
            raise ValueError(f"重复评审路径：{name}")
        seen.add(name)
    for name in seen:
        for parent in Path(name).parents:
            if parent.as_posix() in seen:
                raise ValueError(f"评审路径文件/目录碰撞：{parent} / {name}")


@dataclass(frozen=True)
class ManifestEntry:
    sha256: str
    size: int
    name: str


@dataclass(frozen=True)
class Manifest:
    entries: tuple[ManifestEntry, ...]
    headers: dict[str, str]
    sources: dict[str, Path]


def parse_manifest(path: Path) -> Manifest:
    text = read_regular(path).decode("utf-8")
    entries: list[ManifestEntry] = []
    headers: dict[str, str] = {}
    sources: dict[str, Path] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.startswith("#"):
            continue
        key, separator, value = raw.partition(":")
        if separator and key in _HEADERS:
            if key in headers or not value.strip():
                raise ValueError(f"MANIFEST 重复或空头部（第 {number} 行）：{key}")
            headers[key] = value.strip()
            continue
        if raw.startswith("source: "):
            try:
                mapping = json.loads(raw[len("source: "):])
            except json.JSONDecodeError as exc:
                raise ValueError(f"MANIFEST source 映射损坏：第 {number} 行") from exc
            if (not isinstance(mapping, list) or len(mapping) != 2
                    or any(not isinstance(v, str) for v in mapping)):
                raise ValueError("MANIFEST source 必须是 [快照路径, 仓外绝对来源]")
            name, source = mapping
            safe_name(name)
            if name in sources or not Path(source).is_absolute() or "\x00" in source:
                raise ValueError(f"MANIFEST 重复或非法 source 映射：{name}")
            sources[name] = Path(source)
            continue
        match = _ENTRY.fullmatch(raw)
        if not match:
            raise ValueError(f"MANIFEST 第 {number} 行无法解析：{raw!r}")
        name = safe_name(match[3])
        entries.append(ManifestEntry(match[1], int(match[2]), name))
    if "files" not in headers or not re.fullmatch(r"[0-9]+", headers["files"]):
        raise ValueError("MANIFEST 缺少有效 files: N 头")
    if not entries or int(headers["files"]) != len(entries):
        raise ValueError(f"MANIFEST files: {headers['files']} 与实际文件行 {len(entries)} 不一致或为空")
    unique_paths([entry.name for entry in entries])
    names = {entry.name for entry in entries}
    if not sources.keys() <= names:
        raise ValueError("MANIFEST source 映射未对应文件行")
    mapped_sources: set[str] = set()
    recorded_repo = Path(headers["repo"]) if "repo" in headers else None
    for name, source in sources.items():
        digest = hashlib.sha256(str(source).encode("utf-8")).hexdigest()
        expected = f"{EXTERNAL_NAMESPACE}/{digest}/{source.name}"
        if name != expected or str(source) in mapped_sources:
            raise ValueError(f"MANIFEST source 映射非一对一稳定仓外路径：{name}")
        if recorded_repo and (source == recorded_repo or recorded_repo in source.parents):
            raise ValueError(f"MANIFEST source 不是仓外来源：{source}")
        mapped_sources.add(str(source))
    return Manifest(tuple(entries), headers, sources)


@dataclass(frozen=True)
class Snapshot:
    root: Path
    manifest: Manifest
    objects: dict[str, bytes]

    def validate_repo(self, repo: Path, source_repo: Path | None = None) -> None:
        recorded = self.manifest.headers.get("repo")
        if not recorded or not Path(recorded).is_absolute():
            raise ValueError("快照缺少可核对的仓库身份（MANIFEST 的 repo）；请从原仓重新生成快照")
        allowed = {repo}
        if source_repo is not None:
            allowed.add(safe_path(source_repo))
        if Path(recorded) not in allowed:
            expected = " 或 ".join(str(path) for path in sorted(allowed))
            raise ValueError(
                f"快照仓库不匹配：MANIFEST 记录 {recorded}，本次要求 {expected}；"
                "迁移同一仓库时可显式用 --snapshot-source-repo 指定旧根路径"
            )

    def name_for(self, repo: Path, source: Path) -> str:
        name, external = source_name(repo, source)
        if external:
            if self.manifest.sources.get(name) != source:
                raise ValueError(f"仓外对象没有唯一来源映射（旧 basename 快照有歧义，请重建）：{source}")
        elif name in self.manifest.sources:
            raise ValueError(f"仓内路径与仓外来源映射冲突：{name}")
        if name not in self.objects:
            raise ValueError(f"--files 中的 {name} 不在快照 MANIFEST 中")
        return name


def load_snapshot(path: Path) -> Snapshot:
    root = safe_path(path)
    manifest = parse_manifest(root / MANIFEST_NAME)
    objects: dict[str, bytes] = {}
    for entry in manifest.entries:
        try:
            data = read_regular(root / entry.name)
        except OSError as exc:
            raise ValueError(f"快照文件不可读：{entry.name}：{exc}") from exc
        if len(data) != entry.size or hashlib.sha256(data).hexdigest() != entry.sha256:
            raise ValueError(f"快照文件大小/hash 漂移：{entry.name}")
        objects[entry.name] = data
    return Snapshot(root, manifest, objects)


@dataclass(frozen=True)
class ReviewBundle:
    revision: str | None
    paths: tuple[Path, ...]
    names: tuple[str, ...]
    objects: dict[str, bytes | None]
    kind: str


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(f"git {' '.join(args)} 失败：{result.stderr.decode('utf-8', errors='replace').strip()}")
    return result.stdout


def freeze_review(repo: Path, files: list[Path], revision: str | None,
                  deletion_names: set[str] | None = None,
                  source_repo: Path | None = None) -> ReviewBundle:
    repo = safe_path(repo)
    paths = tuple(source_path(repo, f) for f in files)
    if len(paths) != len(set(paths)):
        raise ValueError("--files 含重复来源路径")
    if revision and not _COMMIT.fullmatch(revision):
        snap = load_snapshot(Path(revision))
        snap.validate_repo(repo, source_repo)
        names = tuple(snap.name_for(repo, path) for path in paths)
        unique_paths(list(names))
        return ReviewBundle(str(snap.root), paths, names,
                            {name: snap.objects[name] for name in names}, "snapshot")
    names = tuple(source_name(repo, path)[0] for path in paths)
    unique_paths(list(names))
    if revision:
        if any(source_name(repo, path)[1] for path in paths):
            raise ValueError("提交模式不支持仓外对象")
        full_sha = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").decode("ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", full_sha):
            raise ValueError("提交模式需要完整 SHA-1 提交对象")
        tree: dict[str, tuple[str, str, str]] = {}
        for row in _git(repo, "ls-tree", "-r", "-z", full_sha).split(b"\0"):
            if not row:
                continue
            meta, name_bytes = row.split(b"\t", 1)
            mode, kind, oid = meta.decode("ascii").split()
            tree[name_bytes.decode("utf-8")] = (mode, kind, oid)
        objects: dict[str, bytes | None] = {}
        for name in names:
            if name not in tree:
                for parent in Path(name).parents:
                    if parent.as_posix() in tree:
                        raise ValueError(f"提交路径父项不是普通目录：{name}")
                if deletion_names and name in deletion_names:
                    objects[name] = None
                    continue
                raise ValueError(f"提交不含普通文件：{name}")
            mode, kind, oid = tree[name]
            if mode not in {"100644", "100755"} or kind != "blob":
                raise ValueError(f"提交对象不是普通 blob（拒 symlink/gitlink）：{name}")
            objects[name] = _git(repo, "cat-file", "blob", oid)
        return ReviewBundle(full_sha, paths, names, objects, "commit")
    return ReviewBundle(None, paths, names,
                        {name: read_regular(path) for name, path in zip(names, paths)}, "draft")


def freeze_diff_base(path: Path, repo: Path, source_repo: Path | None = None) -> dict[str, bytes]:
    root = safe_path(path)
    if (root / MANIFEST_NAME).exists() or (root / MANIFEST_NAME).is_symlink():
        snapshot = load_snapshot(root)
        snapshot.validate_repo(repo, source_repo)
        return snapshot.objects
    if not root.is_dir():
        raise ValueError(f"--diff-base 不是目录：{root}")
    objects = {}
    for entry in sorted(root.rglob("*")):
        checked = safe_path(entry)
        if checked.is_dir():
            continue
        name = safe_name(entry.relative_to(root).as_posix())
        objects[name] = read_regular(entry)
    return objects
