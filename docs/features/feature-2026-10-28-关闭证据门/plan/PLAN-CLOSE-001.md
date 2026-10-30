---
plan_id: PLAN-CLOSE-001
plan_version: 1.0.0
status: proposed
objective: 把关闭证据的三处载体对齐——文档不再声称门缺失、非 open 记录强制流转记录、schema 条件补齐负例回归。
recorded_at: 2026-10-28T15:55:00+08:00
updated_at: 2026-10-28T15:58:00+08:00
---

# 关闭证据门 — 执行契约

> 文档状态：proposed（两个评审门未跑）。执行事实以任务表为准，不以 approval 状态代替进度。

## 0. 分支策略

| 仓库 | 用途 | 基线 | 基线提交 | 开发分支 | 确认状态 | 确认依据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentflows | 实施 | main | c134d0b | feature-2026-10-28-关闭证据门 | 已确认 | 用户 2026-10-28 指令；独立 worktree 从 main 拉出，避开在途分支 | 开发分支无提交；2026-10-28 由该 worktree 的工作树改动直接并入 `main`（未推送） |

## 1. 落点与真源

本文件是执行契约真源；行为规格见 `spec/be/backend.md`，设计见 `design/be/backend.md`，验收见 `spec/qa/acceptance.md`，验证方案见 `design/qa/testing.md`。

## 2. 阶段划分

| 阶段 | 内容 | 完成判据 |
| --- | --- | --- |
| S1 契约文档 | README 与模板与门一致 | 旧表述零命中；状态矩阵在场 |
| S2 流转记录门 | 非 open 强制 `## 变更记录` | 负例必红、存量零误伤 |
| S3 回归 | schema 条件与标题检查的负例/正例 | `unittest` 全绿 |
| S4 全门 | `doc_chain.py` 与 `validate.py all` | 与基线一致，原始输出落盘 |

## 进展概览

**总任务数**：4 · **已完成**：4 · **进行中**：0 · **阻塞**：0 · **本期不做**：1（Q-01 fix_revision 强制）

当前停在：实施、端到端实验、CHANGELOG 0.21.0 与 episode 完成；首轮独立评审 changes_requested 的 4 项（F1–F4）已修复并按 L0 复核通过；独立复审已于 2026-10-29 经独立委派 L2 `approved` 闭环（复审初判 `changes_requested` 的唯一阻塞为无关批次 `09-19` 复审文件的退役路径引用，该红门已于同次修正消除，`validate.py all` 复跑 11/11 PASS）。下一步：无。阻塞：无。

## 任务清单

| ID | 任务 | 角色 | 代码落点 | 依赖 | 关联 design | 交付效果（可验证） | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | 修正文档旧表述并补状态条件矩阵 | BE | `docs/issues/README.md`、`skills/agentflow/templates/issue/issue-template.md` | — | design/be §1.2 | 「schema 尚不按状态强制」零命中；README 含 verified/rejected/变更记录三项要求 | ☑ 已完成 | `docs/issues/README.md`；`skills/agentflow/templates/issue/issue-template.md` |
| T02 | 非 open 记录要求 `## 变更记录` | BE | `tools/lab/gate/records.py` | — | design/be §1.2 | 缺该节的非 open 记录报固定文案错误 | ☑ 已完成 | `tools/lab/gate/records.py`；用例 T03-05 |
| T03 | 补齐 schema 条件与流转记录回归 | QA | `tests/test_gate_schema.py` | T02 | design/qa §3 | 五条负例、两条正例全绿 | ☑ 已完成 | `tests/test_gate_schema.py`；`testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md` |
| T04 | 跑文档链与全量门并落原始输出 | QA | `docs/features/feature-2026-10-28-关闭证据门/testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md` | T01、T03 | design/qa §7 | `doc_chain.py`、`unittest`、`validate.py all` 输出可复核 | ☑ 已完成 | `docs/features/feature-2026-10-28-关闭证据门/testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md` |

执行优先级：T02 →（T01 ∥ T03）→ T04。

### 3.1 未决项 / 前置与待核实闭合

| 前置 | 关联任务 | 说明 |
| --- | --- | --- |
| 独立复审（需求/技术方案） | T01–T04 | 首轮独立评审 changes_requested；F1–F4 已修复并按 L0 复核通过；独立复审已于 2026-10-29 经独立委派 L2 `approved` 闭环，记录见 `reviews/agentflow-关闭证据门/review-2026-10-28-002.md`（含「决议修正附注」说明初判 `changes_requested` 的外部红门已消除） |
| Q-01 `fix_revision` 强制 | — | 本期不做；存量 10 条 verified 缺该字段，先补载体再另开批次 |

## 4. 接口与共享机制

| 注册点/共享机制 | 位置 | 说明 |
| --- | --- | --- |
| bug 记录 schema | `schemas/bug-record.schema.json` | 状态条件的单点真源（本批不改） |
| 记录门 | `tools/lab/gate/records.py` | 正文标题与布局检查 |
| 全量记录面入口 | `tools/lab/validate.py` 的 `artifacts` | 所有记录编译的唯一入口 |
| 回归钉住 | `tests/test_gate_schema.py` | 负例与正例 |

## 5. 联调目标与发布顺序与回滚点

| 目标 | 地址/端口 | 用途 | 确认状态 | 确认依据 |
| --- | --- | --- | --- | --- |
| 本地仓 | 本 worktree | 仅本地校验 | 已确认 | 用户指令 |

| 顺序 | 动作 | 回滚点 | 不可回退点 |
| --- | --- | --- | --- |
| 1 | 记录门追加标题检查 | 回退该文件即可 | 无（已并入 `main`，回退即 revert） |
| 2 | 负例回归 | 回退测试文件 | 无 |
| 3 | 文档同步 | 回退文档 | 无 |

## 验证命令

| 命令 | 覆盖什么 | 命令依据 |
| --- | --- | --- |
| `.venv/bin/python -m unittest tests.test_gate_schema` | 负例与正例 | `tests/test_gate_schema.py` |
| `.venv/bin/python tools/lab/doc_chain.py docs/features/feature-2026-10-28-关闭证据门` | 本批次文档链 | `AGENTS.md` 文档链节 |
| `.venv/bin/python tools/lab/validate.py artifacts` | 存量记录零误伤 | `tools/lab/validate.py` |
| `.venv/bin/python tools/lab/validate.py all` | 全量门 | `AGENTS.md` 接受产物前 |
