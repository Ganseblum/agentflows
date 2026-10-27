"""pre-push hook 的回归测试。

旧实现校验的是当前工作区，于是「坏提交留在历史里、工作区事后改好」的推送会被
放行——与脚本注释宣称的检查对象不符。这里钉住修复后的行为：门在待推送提交的
临时检出上运行，且「无法验证」默认拦下而不是放行。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "skills" / "agentflow" / "scripts" / "pre-push.sh"
ZERO = "0" * 40

# 最小门：只实现 hook 依赖的 --list 契约、一个会受坏提交影响的 docs 目标，和一个 lint 目标。
FAKE_GATE = '''#!/usr/bin/env python3
import os
import sys

if "--list" in sys.argv:
    print("docs")
    print("lint")
    print("all runs 2 checks")
    raise SystemExit(0)

target = sys.argv[1]
if target == "docs":
    if os.path.exists("BROKEN"):
        print("FAIL docs (1 error(s))")
        print("  - BROKEN marker present")
        raise SystemExit(1)
    print("PASS docs")
    raise SystemExit(0)
if target == "lint":
    print("PASS lint")
    raise SystemExit(0)
print("unknown target " + target)
raise SystemExit(2)
'''


class PrePushHookTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.repo = self.root / "repo"
        (self.repo / "tools" / "lab").mkdir(parents=True)
        (self.repo / "tools" / "lab" / "validate.py").write_text(FAKE_GATE, encoding="utf-8")
        (self.repo / "README.md").write_text("hello\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("config", "user.email", "hook-test@example.invalid")
        self.git("config", "user.name", "hook test")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        # 解释器替身：-c 探测按需成功或失败，其余参数交给当前解释器执行假门。
        self.shim = self._write_shim("shim", lint_available=True)
        self.shim_no_deps = self._write_shim("shim-no-deps", lint_available=False)

    def tearDown(self):
        self._temp.cleanup()

    def git(self, *args, check=True):
        return subprocess.run(
            ["git", *args], cwd=self.repo, text=True, capture_output=True, check=check
        )

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def _write_shim(self, name, lint_available):
        path = self.root / name
        probe = "exit 0" if lint_available else "exit 1"
        path.write_text(
            "#!/bin/sh\n"
            f'if [ "$1" = "-c" ]; then {probe}; fi\n'
            f'exec "{sys.executable}" "$@"\n',
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def run_hook(self, stdin_text=None, env=None, cwd=None):
        full_env = {**os.environ, "AGENTFLOW_GATE_PYTHON": str(self.shim)}
        if env:
            full_env.update(env)
        kwargs = (
            {"input": stdin_text}
            if stdin_text is not None
            else {"stdin": subprocess.DEVNULL}
        )
        return subprocess.run(
            ["bash", str(HOOK)],
            cwd=str(cwd or self.repo),
            env=full_env,
            capture_output=True,
            text=True,
            **kwargs,
        )

    def make_repo(self, name, with_gate):
        repo = self.root / name
        repo.mkdir()
        if with_gate:
            (repo / "tools" / "lab").mkdir(parents=True)
            (repo / "tools" / "lab" / "validate.py").write_text(FAKE_GATE, encoding="utf-8")
        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        for args in (
            ["init", "-q"],
            ["config", "user.email", "hook-test@example.invalid"],
            ["config", "user.name", "hook test"],
            ["add", "-A"],
            ["commit", "-qm", "base"],
        ):
            subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()
        return repo, sha

    def ref_line(self, sha, remote_ref="refs/heads/main"):
        return f"refs/heads/main {sha} {remote_ref} {ZERO}\n"

    def commit_bad_marker(self):
        (self.repo / "BROKEN").write_text("broken\n", encoding="utf-8")
        self.git("add", "BROKEN")
        self.git("commit", "-qm", "add broken marker")
        return self.head()

    def test_clean_commit_passes(self):
        result = self.run_hook(self.ref_line(self.head()))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("全绿", result.stdout)

    def test_bad_commit_is_blocked_even_when_worktree_is_fixed(self):
        bad = self.commit_bad_marker()
        (self.repo / "BROKEN").unlink()
        result = self.run_hook(self.ref_line(bad))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("FAIL docs", result.stdout)
        self.assertFalse((self.repo / "BROKEN").exists(), "hook 不得改动工作区")

    def test_deletion_only_push_passes_without_running_gate(self):
        result = self.run_hook(f"refs/heads/gone {ZERO} refs/heads/gone {self.head()}\n")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("只包含删除操作", result.stdout)
        self.assertNotIn("校验待推送提交", result.stdout)

    def test_any_bad_ref_blocks_the_push(self):
        base = self.head()
        bad = self.commit_bad_marker()
        stdin = (
            f"refs/heads/a {base} refs/heads/a {ZERO}\n"
            f"refs/heads/b {bad} refs/heads/b {ZERO}\n"
        )
        result = self.run_hook(stdin)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(f"{bad[:7]}:docs", result.stderr)
        self.assertIn(base[:7], result.stdout)

    def test_missing_interpreter_blocks_by_default(self):
        result = self.run_hook(
            self.ref_line(self.head()),
            env={"AGENTFLOW_GATE_PYTHON": str(self.root / "missing-python")},
        )
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("未运行不等于通过", result.stderr)

    def test_missing_interpreter_can_be_allowed_explicitly(self):
        result = self.run_hook(
            self.ref_line(self.head()),
            env={
                "AGENTFLOW_GATE_PYTHON": str(self.root / "missing-python"),
                "AGENTFLOW_PREPUSH_ALLOW_UNRUN": "1",
            },
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("未经门禁验证", result.stderr)

    def test_missing_lint_dependencies_blocks_by_default(self):
        result = self.run_hook(
            self.ref_line(self.head()),
            env={"AGENTFLOW_GATE_PYTHON": str(self.shim_no_deps)},
        )
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("有检查未运行", result.stderr)

    def test_missing_lint_dependencies_can_be_allowed_explicitly(self):
        result = self.run_hook(
            self.ref_line(self.head()),
            env={
                "AGENTFLOW_GATE_PYTHON": str(self.shim_no_deps),
                "AGENTFLOW_PREPUSH_ALLOW_UNRUN": "1",
            },
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("未运行项未经验证", result.stderr)

    def test_removing_the_gate_is_blocked(self):
        self.git("rm", "-q", "tools/lab/validate.py")
        self.git("commit", "-qm", "remove gate")
        result = self.run_hook(self.ref_line(self.head()))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("删除了 tools/lab/validate.py", result.stderr)

    def test_unreadable_commit_object_is_blocked(self):
        result = self.run_hook(self.ref_line("1" * 40))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("不是本地可读的提交", result.stderr)

    def test_malformed_stdin_is_blocked(self):
        result = self.run_hook("garbage-without-fields\n")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("stdin 行格式无法识别", result.stderr)

    def test_manual_run_without_stdin_checks_head(self):
        result = self.run_hook()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("改校验 HEAD", result.stdout)

    def test_annotated_tag_push_is_not_falsely_blocked(self):
        # 这条钉的是「打标签的推送不被误拦」，不是「剥离不可或缺」：git 自己也会把
        # commit-ish 解析到 commit。剥离的判别力由下一条 tree 对象用例承担。
        self.git("tag", "-a", "v1", "-m", "tag for hook test")
        tag_sha = self.git("rev-parse", "v1").stdout.strip()
        self.assertNotEqual(tag_sha, self.head(), "annotated tag 应指向 tag 对象")
        result = self.run_hook(self.ref_line(tag_sha, "refs/tags/v1"))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("全绿", result.stdout)

    def test_non_commit_object_is_blocked(self):
        # 剥离开关真正区分的东西：tree 对象不是 commit，必须被拦下而不是拿去检出。
        tree_sha = self.git("rev-parse", "HEAD^{tree}").stdout.strip()
        result = self.run_hook(self.ref_line(tree_sha, "refs/tags/treetag"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("不是本地可读的提交", result.stderr)

    def test_tree_without_gate_is_unrun_and_blocked_by_default(self):
        repo, sha = self.make_repo("no-gate", with_gate=False)
        result = self.run_hook(self.ref_line(sha), cwd=repo)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("no-gate", result.stderr)
        self.assertIn("有检查未运行", result.stderr)
        self.assertIn("无门禁（no-gate）请补上 tools/lab/validate.py", result.stderr)

    def test_tree_without_gate_can_be_allowed_explicitly(self):
        repo, sha = self.make_repo("no-gate-allowed", with_gate=False)
        result = self.run_hook(
            self.ref_line(sha), env={"AGENTFLOW_PREPUSH_ALLOW_UNRUN": "1"}, cwd=repo
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("未运行项未经验证", result.stderr)

    def test_temporary_worktrees_are_cleaned_up(self):
        self.run_hook(self.ref_line(self.head()))
        listing = self.git("worktree", "list", "--porcelain").stdout
        self.assertEqual(1, listing.count("worktree "), listing)


if __name__ == "__main__":
    unittest.main()