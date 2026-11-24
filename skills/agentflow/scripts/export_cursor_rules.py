#!/usr/bin/env python3
"""export_cursor_rules.py — 将 agentflow 的核心纪律与工程标准导出为 Cursor 原生规则（.cursor/rules/*.mdc）。

支持的规则映射：
  - global-rules.mdc: 宿主跨仓铁律（分支、合并、授权、证据），alwaysApply: true
  - security-standards.mdc: 安全底线与审计规则 (SEC-01~SEC-10)，alwaysApply: true
  - server-side-standards.mdc: 服务端底线（幂等、防吞异常、资源有界），按后端文件 glob 触发
  - frontend-standards.mdc: 前端底线（单一真源、防连点、错误边界），按前端文件 glob 触发
  - data-model-standards.mdc: 数据模型与持久化底线，按 SQL/模型文件 glob 触发
  - api-standards.mdc: API 与契约规范，按路由/控制器/OpenAPI 文件 glob 触发
  - git-commit-standards.mdc: Git 提交规范，alwaysApply: true

先核对全部来源和目标，再写入。已有同名规则只有完整的对应托管块才能更新；
无标记的旧导出与用户规则一样需要手工处理。--dry-run 不创建目录或文件。

用法：
  python3 export_cursor_rules.py [--target-dir <目标仓根路径>] [--output-dir <rules目录>] [--dry-run] [--self-test]
退出码：0 成功 / 1 失败 / 2 参数错误
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from workflow_lib.managed import file_state, locate_managed_block, write_managed_file
from workflow_lib.snapshots import WorkflowError, no_symlinks

CURSOR_RULE_BEGIN = b"<!-- agentflow:cursor-rule "
CURSOR_RULE_END = b"<!-- agentflow:cursor-rule:end -->"
GLOBAL_RULE_BEGIN = b"<!-- agentflow:begin v{{version}} -->"
GLOBAL_RULE_END = b"<!-- agentflow:end -->"
FRONTMATTER = re.compile(rb"\A---\r?\n.*?^---(?:\r?\n|\Z)", re.MULTILINE | re.DOTALL)
FENCE = re.compile(rb" {0,3}(`{3,}|~{3,})([^\r\n]*)\r?\Z")

RULES_MAP = [
    {
        "name": "global-rules",
        "source": "skills/agentflow/templates/host/global-rules.md",
        "description": "Agentflow 跨仓核心纪律：写前查分支、合并与推送授权、证据纪律、合并收口、评审绑定 revision",
        "globs": "",
        "always_apply": True,
    },
    {
        "name": "security-standards",
        "source": "skills/agentflow/references/standards/security.md",
        "description": "Agentflow 安全工程与审计底线 (SEC-01~SEC-10)：认证鉴权、防越权、防注入、XSS、SSRF、密钥零硬编码",
        "globs": "",
        "always_apply": True,
    },
    {
        "name": "server-side-standards",
        "source": "skills/agentflow/references/standards/server-side.md",
        "description": "服务端工程底线 (BE-01~BE-15)：写接口幂等、防吞异常、下游超时、资源有界、优雅停机",
        "globs": "**/*.go,**/*.py,**/*.java,**/*.rs,**/*.ts,**/*.js,**/controllers/**,**/services/**,**/handlers/**",
        "always_apply": False,
    },
    {
        "name": "frontend-standards",
        "source": "skills/agentflow/references/standards/frontend.md",
        "description": "前端工程底线 (FE-01~FE-09)：状态单一真源、表单防重复提交、加载/空/错三态、可访问性",
        "globs": "**/*.tsx,**/*.jsx,**/*.vue,**/*.svelte,**/components/**,**/pages/**,**/views/**",
        "always_apply": False,
    },
    {
        "name": "data-model-standards",
        "source": "skills/agentflow/references/standards/data-model.md",
        "description": "数据模型与持久化底线 (DB-01~DB-06)：实体不变量、字段完整十属性、索引与查询对齐、迁移可回滚",
        "globs": "**/*.sql,**/models/**,**/entities/**,**/schemas/**,**/migrations/**",
        "always_apply": False,
    },
    {
        "name": "api-standards",
        "source": "skills/agentflow/references/standards/api-docs.md",
        "description": "API 契约标准 (API-01~API-08)：RESTful 语义、响应信封、统一错误码、分页排序、向下兼容",
        "globs": "**/api/**,**/routes/**,**/controllers/**,**/*openapi*,**/*swagger*,**/*.proto",
        "always_apply": False,
    },
    {
        "name": "git-commit-standards",
        "source": "skills/agentflow/references/standards/git-commits.md",
        "description": "Git 提交与变更规范 (GIT-01~GIT-06)：Conventional Commits、类型分类、破坏性变更、任务绑定",
        "globs": "",
        "always_apply": True,
    },
]


def render_frontmatter(rule: dict) -> bytes:
    """Keep activation metadata at the beginning of newly created rules."""
    description = rule["description"]
    globs = rule["globs"]
    always_apply = "true" if rule["always_apply"] else "false"

    frontmatter = [
        "---",
        f'description: "{description}"',
    ]
    if globs:
        frontmatter.append(f'globs: "{globs}"')
    frontmatter.append(f"alwaysApply: {always_apply}")
    frontmatter.append("---\n\n")
    return "\n".join(frontmatter).encode("utf-8")


def mask_fenced_code(contents: bytes) -> bytes:
    """Hide examples from marker lookup, keeping the original byte offsets."""
    masked = []
    opening = b""
    for line in contents.split(b"\n"):
        match = FENCE.fullmatch(line)
        if not opening:
            if match and not (match[1].startswith(b"`") and b"`" in match[2]):
                opening = match[1]
            masked.append(b" " * len(line) if opening else line)
        else:
            masked.append(b" " * len(line))
            if match and match[1].startswith(opening) and not match[2].strip(b" \t"):
                opening = b""
    return b"\n".join(masked)


def render_rule(rule: dict, source: bytes, original: bytes | None, target: Path) -> bytes:
    """Build a new rule or replace only its own managed block."""
    source_header = FRONTMATTER.match(source)
    if source_header is not None:
        source = source[source_header.end():]
    source = source.decode("utf-8").replace("\r\n", "\n").strip().encode("utf-8")
    if rule["name"] == "global-rules":
        source_span = locate_managed_block(source, GLOBAL_RULE_BEGIN, GLOBAL_RULE_END)
        if source_span is None:
            raise WorkflowError("invalid-source", f"全局规则来源缺少模板托管块：{rule['source']}")
        start, end = source_span
        source = source[start + len(GLOBAL_RULE_BEGIN):end - len(GLOBAL_RULE_END)].strip()
        # A repository .mdc applies to this workspace, unlike the original host template.
        source = source.replace("本宿主的所有工作区".encode(), "当前工作区".encode(), 1)
    begin = CURSOR_RULE_BEGIN + rule["name"].encode("ascii") + b" -->"
    if CURSOR_RULE_BEGIN in source or CURSOR_RULE_END in source:
        raise WorkflowError("invalid-source", f"来源含导出器托管标记：{rule['source']}")
    block = b"\n".join((begin, source, CURSOR_RULE_END))
    if original is None:
        return render_frontmatter(rule) + block + b"\n"

    header = FRONTMATTER.match(original)
    body_offset = header.end() if header else 0
    try:
        span = locate_managed_block(mask_fenced_code(original[body_offset:]), begin, CURSOR_RULE_END,
                                    begin_prefix=CURSOR_RULE_BEGIN)
    except WorkflowError as exc:
        raise WorkflowError(exc.kind, f"{target}：{exc}") from exc
    if header is None or span is None:
        raise WorkflowError("unowned-rule", f"已有同名规则未找到有效托管块，请先手工处理：{target}")
    start, end = body_offset + span[0], body_offset + span[1]
    if original[start:].startswith(begin + b"\r\n"):
        block = block.replace(b"\n", b"\r\n")
    return original[:start] + block + original[end:]


def export_rules(repo_root: Path, target_dir: Path, dry_run: bool = False) -> list[str]:
    """Preflight the whole batch and then apply the shared guarded file writer."""
    target_dir = no_symlinks(target_dir)
    for parent in (target_dir, *target_dir.parents):
        if parent.exists() and not parent.is_dir():
            raise WorkflowError("invalid-target", f"输出路径不是目录：{parent}")

    plan = {}
    expected = {}
    for rule in RULES_MAP:
        source_path = no_symlinks(repo_root / rule["source"])
        expected[source_path] = file_state(source_path)
        if not expected[source_path]["exists"]:
            raise WorkflowError("missing-source", f"缺少规则来源：{source_path}")
        target = target_dir / f"{rule['name']}.mdc"
        expected[target] = file_state(target)
        original = target.read_bytes() if expected[target]["exists"] else None
        desired = render_rule(rule, source_path.read_bytes(), original, target)
        action = "create" if original is None else "same" if desired == original else "refresh"
        plan[target] = (action, desired)

    for path, state in expected.items():
        if file_state(path) != state:
            raise WorkflowError("path-drift", f"预检期间文件发生变化：{path}")

    if not dry_run and any(action == "create" for action, _ in plan.values()):
        no_symlinks(target_dir).mkdir(parents=True, exist_ok=True)
    for target, (action, desired) in plan.items():
        if dry_run:
            print(f"[dry-run] [{action}] {target}")
            continue
        result = write_managed_file(target, desired, expected[target])
        backup = f"；备份 {result['backup']}" if result["backup"] else ""
        print(f"[{action}] {target}{backup}")
    return [str(path) for path in plan]


def self_test(repo_root: Path) -> int:
    """Exercise the CLI with rule sources and destinations in an isolated copy."""
    import shutil
    import subprocess
    from tempfile import TemporaryDirectory

    with TemporaryDirectory(prefix="agentflow-cursor-test-", dir="/tmp") as directory:
        fixture = Path(directory).resolve()
        source_root = fixture / "plugin"
        script = source_root / Path(__file__).resolve().relative_to(repo_root)
        script.parent.mkdir(parents=True)
        shutil.copy2(__file__, script)
        shutil.copytree(Path(__file__).parent / "workflow_lib", script.parent / "workflow_lib",
                        ignore=shutil.ignore_patterns("__pycache__"))
        for rule in RULES_MAP:
            source = source_root / rule["source"]
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo_root / rule["source"], source)

        def run(*args: str | Path, code: int = 0, expect: str) -> None:
            completed = subprocess.run([sys.executable, str(script), *map(str, args)],
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print(completed.stdout, end="")
            print(f"exit={completed.returncode}")
            assert (completed.returncode, expect in completed.stdout) == (code, True)

        project = fixture / "empty-project"
        rule_dir = project / ".cursor" / "rules"
        run("--target-dir", project, "--dry-run", expect="[dry-run] [create]")
        print(f"预览后项目路径存在：{project.exists()}；缓存目录：{list(source_root.rglob('__pycache__'))}")
        assert not project.exists() and not list(source_root.rglob("__pycache__"))

        run("--target-dir", project, expect="Total exported rules: 7")
        files = sorted(rule_dir.iterdir())
        print(f"输出规则：{[path.name for path in files]}")
        assert {path.name for path in files} == {f"{rule['name']}.mdc" for rule in RULES_MAP}
        global_rule = (rule_dir / "global-rules.mdc").read_bytes()
        print(f"全局规则应用范围：{next(line.decode() for line in global_rule.splitlines() if line.startswith('适用范围'.encode()))}")
        assert "适用范围：当前工作区。".encode() in global_rule and GLOBAL_RULE_BEGIN not in global_rule
        frontend = (rule_dir / "frontend-standards.mdc").read_bytes()
        header = FRONTMATTER.match(frontend)
        assert header and b'globs: "**/*.tsx,' in header.group() and b"alwaysApply: false" in header.group()
        before = [(path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns) for path in files]
        run("--target-dir", project, expect="[same]")
        assert sorted(rule_dir.iterdir()) == files
        assert before == [(path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns) for path in files]

        # Modify a source and put project-owned content on both sides of its generated block.
        rule = RULES_MAP[-1]
        target = rule_dir / f"{rule['name']}.mdc"
        begin = CURSOR_RULE_BEGIN + rule["name"].encode("ascii") + b" -->"
        prefix = b"---\r\ndescription: Team rule\r\nalwaysApply: false\r\n---\r\n# Team prefix  \r\n"
        example = b"~~~md\r\n" + begin + b"\r\n# Example only\r\n" + CURSOR_RULE_END + b"\r\n~~~~\r\n"
        suffix = b"\r\n# Team suffix\r\n" + example + b"\t "
        managed = begin + target.read_bytes().split(begin, 1)[1].rstrip(b"\n")
        original = prefix + managed.replace(b"\n", b"\r\n") + suffix
        target.write_bytes(original)
        source = source_root / rule["source"]
        source.write_bytes(source.read_bytes() + b"\nUPGRADED_BODY\n")
        run("--output-dir", rule_dir, expect="[refresh]")
        updated = target.read_bytes()
        print(f"升级后前缀：{updated[:len(prefix)]!r}；尾部：{updated[-len(suffix):]!r}")
        assert updated.startswith(prefix) and updated.endswith(suffix)
        assert b"UPGRADED_BODY\r\n" + CURSOR_RULE_END in updated
        backups = list(rule_dir.glob(f"{target.name}.agentflow-backup-*"))
        assert len(backups) == 1 and backups[0].read_bytes() == original

        protected = fixture / "protected"
        protected.mkdir()
        existing = protected / target.name
        sentinel = b"---\r\nnormal-rule: true\r\n---\r\nUser-owned rule  "
        existing.write_bytes(sentinel)
        run("--output-dir", protected, "--dry-run", code=1, expect="unowned-rule")
        run("--output-dir", protected, code=1, expect="unowned-rule")
        print(f"冲突后目录：{[path.name for path in protected.iterdir()]}；原文：{existing.read_bytes()!r}")
        assert list(protected.iterdir()) == [existing] and existing.read_bytes() == sentinel

        example_rule = prefix + example
        existing.write_bytes(example_rule)
        run("--output-dir", protected, code=1, expect="unowned-rule")
        print(f"示例规则目录：{[path.name for path in protected.iterdir()]}；原文：{existing.read_bytes()!r}")
        assert list(protected.iterdir()) == [existing] and existing.read_bytes() == example_rule

        linked = fixture / "linked"
        linked.symlink_to(protected, target_is_directory=True)
        run("--output-dir", linked, code=1, expect="symlink")
        existing.unlink()
        existing.symlink_to(target)
        run("--output-dir", protected, code=1, expect="symlink")
        assert list(protected.iterdir()) == [existing] and target.read_bytes() == updated

        existing.unlink()
        existing.mkdir()
        run("--output-dir", protected, code=1, expect="Regular target file required")
        assert list(protected.iterdir()) == [existing] and not list(existing.iterdir())

        source.unlink()
        missing_target = fixture / "missing-source-target"
        run("--output-dir", missing_target, code=1, expect="missing-source")
        print(f"缺源失败后输出路径存在：{missing_target.exists()}")
        assert not missing_target.exists()

    print("PASS export_cursor_rules self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Export agentflow rules to Cursor .mdc format.")
    parser.add_argument("--target-dir", type=str, default=".", help="Target repository root path.")
    parser.add_argument("--output-dir", type=str, default="", help="Direct output dir for .mdc files.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    parser.add_argument("--self-test", action="store_true", help="Run self-tests and exit.")

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[2]
    if args.self_test:
        return self_test(repo_root)

    out_dir = Path(args.output_dir) if args.output_dir else Path(args.target_dir) / ".cursor" / "rules"
    try:
        exported = export_rules(repo_root, out_dir, dry_run=args.dry_run)
    except WorkflowError as exc:
        print(f"[{exc.kind}] {exc}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as exc:
        print(f"[export-failed] {exc}", file=sys.stderr)
        return 1
    print(f"Total exported rules: {len(exported)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
