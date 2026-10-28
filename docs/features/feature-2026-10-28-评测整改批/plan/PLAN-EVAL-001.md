---
plan_id: PLAN-EVAL-001
plan_version: 1.0.0
status: approved
objective: 落地 2026-10-28 评测报告的五批整改（整改追踪载体、评审能力分级、表达面收敛、本地门基线、改进环首次闭环）
recorded_at: 2026-10-28T11:27:15+08:00
---

# PLAN-EVAL-001 — 评测整改批执行计划

## 进展概览

- 总任务 10 项：☑ 10 项已完成（T01–T10）。
- 阻塞：无。
- 权威状态：本表即唯一任务状态源；批次 README 只作索引。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 审计发现表加 `整改状态`/`fix_revision` 两列并逐行回写 35 项 | P0 | `docs/evaluations/AGENTFLOW-AUDIT-2026-10-26.md` | — | ☑ 已完成 | `docs/features/feature-2026-10-28-评测整改批/testing/agentflow-eval/evidence/T01-audit-columns.txt`（7 列 × 35 行，PASS） |
| T02 | 审核契约写入「发现总表必须带整改状态列」+ G34 成本对照登记 | P1 | `skills/agentflow/references/repo-audit.md`、`docs/PENDING-DECISIONS.md` | T01 | ☑ 已完成 | `skills/agentflow/references/repo-audit.md` 的「发现总表必须带整改状态列」节 + `docs/PENDING-DECISIONS.md` 第 15/16 条 |
| T03 | 评审能力分级协议 L0/L1/L2 写入委派契约 | P0 | `skills/agentflow/references/contracts.md` | — | ☑ 已完成 | `skills/agentflow/references/contracts.md` 的「评审能力分级」节（三档表 + 三条不变式） |
| T04 | SKILL 第 8 步引用分级协议 | P0 | `skills/agentflow/SKILL.md` | T03 | ☑ 已完成 | `skills/agentflow/SKILL.md` 第 8 步（含 `review_tier` 与分级指针） |
| T05 | SKILL 合并 execution-coordinator 重复声明；链契约加判据速查；roles 写 FE/BE 裁决规则 | P1 | `skills/agentflow/SKILL.md`、`skills/agentflow/references/document-chain.md`、`skills/agentflow/references/roles.md` | — | ☑ 已完成 | `skills/agentflow/SKILL.md`（`grep -c 当前不存在` = 1）、`skills/agentflow/references/document-chain.md`（降档速查）、`skills/agentflow/references/roles.md`（FE/BE 裁决规则） |
| T06 | 批次文档链五段成文并通过 linter | P0 | `docs/features/feature-2026-10-28-评测整改批/` | T01 | ☑ 已完成 | `docs/features/feature-2026-10-28-评测整改批/testing/agentflow-eval/evidence/T06-doc-chain.txt` |
| T07 | `validate.py lint` 与 `pre-push.sh` 自动探测 `.venv` | P0 | `tools/lab/validate.py`、`skills/agentflow/scripts/pre-push.sh` | — | ☑ 已完成 | `docs/features/feature-2026-10-28-评测整改批/testing/agentflow-eval/evidence/T07-venv-probe.txt`（正例 PASS / 两反例 EXIT=1） |
| T08 | README/AGENTS 给出 `.venv` 一行约定；刷新 trends | P1 | `README.md`、`docs/trend.jsonl` | T07 | ☑ 已完成 | `README.md` 的「本机一行就绪」注记 + `docs/trend.jsonl` 末行 |
| T09 | 改进环首份真实候选与发布记录 | P1 | `docs/features/feature-2026-10-28-评测整改批/testing/agentflow-eval/evidence/improvement/` | T03 | ☑ 已完成 | `docs/features/feature-2026-10-28-评测整改批/testing/agentflow-eval/evidence/improvement/candidate-EVAL-001.json`、`docs/features/feature-2026-10-28-评测整改批/testing/agentflow-eval/evidence/improvement/release-record-EVAL-001.json` |
| T10 | 全量门实跑 + 重建 runtime + 升版 | P0 | 五份 manifest、`packaging/runtime/`、`CHANGELOG.md` | T01、T02、T03、T04、T05、T06、T07、T08、T09 | ☑ 已完成 | `docs/features/feature-2026-10-28-评测整改批/testing/agentflow-eval/evidence/T10-validate-all.txt` |

## 分支策略

| 仓库 | 用途 | 基线 | 基线提交 | 开发分支 | 确认状态 | 确认依据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentflows | 实施与测试 | main | de806947d22665d347007b690d22136a1a442dca | feature-2026-10-28-评测整改批 | 已确认 | 用户 2026-10-28 批准五批方案后建分支 | 不推送、不合并、不重装 |

## 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-评测整改批"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

## 门与回滚点

- **门 1**：T01–T06 完成后跑一次批次 linter + `validate.py all`，红则退回本批修复。
- **门 2**：T07/T08 触及 `tools/lab/validate.py` 与 `pre-push.sh`（受保护面），改完必须重跑全量门，
  并确认无 `.venv` 时行为与之前逐字一致。
- **门 3**：T10 之前跑一次 `python3.12 -m unittest discover -s tests` 与
  `doc_chain.py --self-test`，两者都必须 OK。
- **回滚点**：单一分支单一提交序列；回滚目标是 `de80694`（0.19.3）。
- **评审档位**：本批执行期间委派不可用，按 `design/be/backend.md` §2 记 `review_tier: L0`；
  能力恢复后须补一次独立复核（T03 的协议正是为此而写）。