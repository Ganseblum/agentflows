import datetime as _dt
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "tools" / "lab"
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import doc_chain
import validate


class GoalTraceabilityEvidenceTests(unittest.TestCase):
    """C22 goal traceability and C23 evidence presence (2026-10-23 gate change, user-authorized).

    Each test pins one defect the 2026-10-22 walkthrough found in real files: a proposal goal that
    disappeared from spec and the plan board while every gate stayed green, and ☑ task rows whose
    only evidence was a /tmp path that had already been cleaned away. C22 is marker-gated; C23 is
    not, because the evidence duty belongs to the plan contract rather than to an opt-in layer.
    """

    README_TMPL = (
        "# 批次\n\n## 需求评审门\n## 技术方案评审门\n\n"
        "本批启用 {marker} 标记。\n\n## 目标承接表\n\n"
        "| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n{rows}"
    )
    ROW_OK = "| G1 目标一 | `proposal/p.md` | M-A 与 G1-AC-01 | T01 | ☑ 已完成 |\n"
    PROPOSAL = "# proposal\n\n## 1.2 目标\n\n- **G1 目标一**：可判定。\n"
    SPEC = (
        "# spec\n\n## 3.0 不合规项（反审 checklist）\n\n"
        "| # | 缺口 | 阻塞 | 状态 |\n| --- | --- | --- | --- |\n| B-1 | x | 阻塞 | ☑ 已关闭 |\n\n"
        "### M-A 模块一\n\n| 验收点 | 来源 |\n| --- | --- |\n| G1-AC-01 | proposal G1 |\n"
    )
    GOOD_EVIDENCE = "`docs/issues/README.md` 在盘"

    def _plan(self, evidence: str, status: str = "☑ 已完成") -> str:
        return (
            "# plan\n\n## 0. 分支策略\n\n"
            "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| T01 | 做一件事 | `a.py` | — | {status} | {evidence} |\n"
        )

    def _batch(self, root: Path, *, marker: str = "agentflow 目标承接",
               rows: str | None = None, plan_text: str | None = None) -> Path:
        batch = root / "docs" / "features" / "b"
        for stage in ("proposal", "spec", "plan"):
            (batch / stage).mkdir(parents=True, exist_ok=True)
        (batch / "README.md").write_text(
            self.README_TMPL.format(marker=marker, rows=self.ROW_OK if rows is None else rows),
            encoding="utf-8")
        (batch / "proposal" / "p.md").write_text(self.PROPOSAL, encoding="utf-8")
        (batch / "spec" / "s.md").write_text(self.SPEC, encoding="utf-8")
        (batch / "plan" / "p.md").write_text(
            self._plan(self.GOOD_EVIDENCE) if plan_text is None else plan_text, encoding="utf-8")
        (root / "docs" / "issues").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "issues" / "README.md").write_text("# issues\n", encoding="utf-8")
        (root / "a.py").write_text("# a\n", encoding="utf-8")
        return batch

    def test_tmp_only_evidence_on_a_completed_row_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, plan_text=self._plan("`/tmp/baseline.txt`（已清理）"))
            errors = doc_chain.batch_traceability_findings(batch, root)
            self.assertEqual(
                [e for e in errors if e.startswith("C23")],
                [e for e in errors if "C23 证据在场" in e and "T01" in e],
            )

    def test_repo_qualified_and_na_cells_are_valid_carriers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._batch(root)
            for cell in (self.GOOD_EVIDENCE, "youc@1a2b3c4:docs/x.md", "N/A: 纯文本改动，门输出即证据"):
                self.assertTrue(
                    doc_chain.evidence_carriers(cell, root), f"carrier missed: {cell}")

    def test_commit_sha_counts_only_when_git_can_resolve_it(self) -> None:
        def git(cwd: Path, *args: str) -> str:
            completed = subprocess.run(
                ["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                cwd=cwd, capture_output=True, text=True, check=True)
            return completed.stdout.strip()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root)
            git(root, "init", "-q")
            git(root, "config", "user.email", "t@example.com")
            git(root, "config", "user.name", "t")
            git(root, "add", "-A")
            git(root, "commit", "-qm", "fixture")
            sha = git(root, "rev-parse", "--short", "HEAD")
            self.assertIn("提交号", doc_chain.evidence_carriers(f"{sha} 落盘", root))
            self.assertEqual(doc_chain.evidence_carriers("deadbe 落盘", batch), [])
            self._plan(f"`{sha}` 提交在历史里")
            self.assertEqual(
                [e for e in doc_chain.batch_traceability_findings(batch, root) if "C23" in e], [])

    def test_rows_that_are_not_done_carry_no_evidence_duty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, plan_text=self._plan("", status="☐ 未开始"))
            errors = doc_chain.batch_traceability_findings(batch, root)
            self.assertEqual([e for e in errors if "C23" in e], [])

    def test_goal_declared_upstream_but_missing_from_the_table_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, rows="")
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("G1" in e and "未进入承接表" in e for e in errors), errors)

    def test_phantom_task_id_and_status_overclaim_both_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, rows=self.ROW_OK.replace("T01", "T99"))
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("T99" in e and "不在计划任务表" in e for e in errors), errors)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            # 承接表声称已完成，看板行还在进行中：状态聚合不一致必须红
            batch = self._batch(root, plan_text=self._plan(self.GOOD_EVIDENCE, status="◐ 进行中"))
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("承接表标已完成" in e for e in errors), errors)

    def test_completed_task_that_nobody_claims_trips_as_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, rows=self.ROW_OK.replace("| T01 |", "| — |"))
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("孤儿任务" in e and "T01" in e for e in errors), errors)

    def test_marker_without_a_table_does_not_silently_skip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root)
            (batch / "README.md").write_text(
                "# 批次\n\n## 需求评审门\n\n本批启用 agentflow 目标承接 标记，表还没建。\n",
                encoding="utf-8")
            errors = doc_chain.goal_traceability_findings(batch, root)
            self.assertTrue(any("没有承接表" in e for e in errors), errors)

    def test_unmarked_batch_is_left_alone_by_c22(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = self._batch(root, marker="目标承接", rows="")
            self.assertEqual(doc_chain.goal_traceability_findings(batch, root), [])

    def test_repo_scan_applies_c23_to_every_batch_but_c22_only_to_opted_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._batch(root, marker="目标承接", rows="",
                        plan_text=self._plan("`/tmp/x.txt`"))
            errors = doc_chain.repo_policy_findings(root)
            self.assertTrue(any("C23 证据在场" in e for e in errors), errors)
            self.assertFalse(any("C22 目标承接" in e for e in errors), errors)

    def test_disposition_field_is_optional_and_enumerated(self) -> None:
        base = {
            "bug_id": "ISS-2026-10-22-归属示例",
            "title": "归属示例",
            "status": "open",
            "severity": "P2",
            "error_kind": "other",
            "attribution": "product_code",
            "provenance": "external",
            "project": "demo",
            "files": ["a.py"],
            "recorded_at": "2026-10-22T16:00:00Z",
        }
        validator = validate.SchemaValidator(validate.BUG_RECORD_SCHEMA)
        self.assertEqual(validator.validate(dict(base)), [])
        self.assertEqual(validator.validate({**base, "disposition": "deferred"}), [])
        bad = validator.validate({**base, "disposition": "wontfix"})
        self.assertTrue(bad, "an out-of-set disposition must be rejected")
        self.assertTrue(any("deferred" in error.message for error in bad), bad)





class ReviewRoundTwoFixTests(unittest.TestCase):
    """第二轮评审三项门语义修复：C17 日粒度、C18 表头归一化、无 git 的失败关闭文案。"""

    DEC_HEAD = ("| 来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- |\n")

    def _repo(self, directory: Path) -> None:
        def git(*args: str) -> None:
            subprocess.run(["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                           cwd=directory, check=True, capture_output=True)
        git("init", "-q")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")

    def _decision_text(self, verify_date: str) -> str:
        row = (f"| `a.md` | A 选一 B 选二 | {verify_date} `grep x` | 选 A | 批次 T01 | "
               f"P2 | 单模块(tools/lab/doc_chain.py) | N |\n")
        return "# 决策\n\n本文件由 agentflow 决策记录方法生成\n\n" + self.DEC_HEAD + row

    def test_c17_same_day_commit_is_not_stale(self) -> None:
        today = _dt.date.today().isoformat()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repo(root)
            (root / "a.md").write_text("# a\n", encoding="utf-8")
            when = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
            env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
            subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True, env=env)
            subprocess.run(["git", "commit", "-qm", "same day"], cwd=root, check=True,
                           capture_output=True, env=env)
            # 核验日期与提交同一天：不得判过期（秒比对时这里必然红）
            self.assertEqual(doc_chain.staleness_findings("d.md", self._decision_text(today), root), [])
            (root / "d.md").write_text(self._decision_text(today), encoding="utf-8")
            earlier = (_dt.date.today() - _dt.timedelta(days=3)).isoformat()
            errors = doc_chain.staleness_findings("d.md", self._decision_text(earlier), root)
            self.assertTrue(errors and "C17 staleness" in errors[0] and "之后的日期被修改" in errors[0], errors)

    def test_c18_accepts_decorated_ledger_header(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            issues = root / "docs" / "issues"
            issues.mkdir(parents=True)
            (issues / "ISS-2026-01-02-x.md").write_text("---\nstatus: open\n---\n", encoding="utf-8")
            readme = ("# 批次\n\n本批启用 agentflow 决策归属 标记。\n\n"
                      "| **记录编号** | `任务号` | 说明 |\n| --- | --- | --- |\n"
                      "| ISS-2026-01-02-x | T01 | 承接 |\n")
            (root / "docs" / "features" / "b").mkdir(parents=True)
            self.assertEqual(
                doc_chain.ownership_findings("b/README.md", readme, root), [],
                "装饰过的表头不得让 covered 集合静默变空（过红方向同样是判据失真）")

    def test_missing_git_is_reported_as_such(self) -> None:
        original = doc_chain.git_available
        doc_chain.git_available = lambda: False
        try:
            errors = doc_chain.evidence_presence_findings(
                "plan/p.md",
                "| ID | 任务 | 代码落点 | 依赖 | 状态 | 证据 |\n| --- | --- | --- | --- | --- | --- |\n"
                "| T01 | x | `a.py` | — | ☑ 已完成 | deadbee 提交在历史里 |\n",
                Path.cwd())
        finally:
            doc_chain.git_available = original
        self.assertTrue(errors and "环境无 git" in errors[0], errors)


if __name__ == "__main__":
    unittest.main()

