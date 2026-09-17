---
bug_id: BUG-20260917-02
title: 同一分支被两个执行者并发写入——写入隔离约束没有延伸到 git 层
status: fixed-pending-review
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: infinite-canvas
files:
  - skills/agentflow/SKILL.md
  - skills/agentflow/references/contracts.md
affected_slices:
  - parallel-writes
  - branch-isolation
  - delegation-briefs
recorded_at: 2026-09-17T00:00:00Z
updated_at: 2026-09-17T02:53:40Z
source_revision: 8665ca3
agentflow_version: 0.4.0
regression_status: not-run
fix_revision: agentflow 0.4.2
---

## 现象

同一分支被两个执行者同时写入，写入在 git 层相撞：

- fork 仓库 `infinite-canvas` 的分支 `codex/account-backend-plan` 上，另一会话新增并推送了
  10 个提交（含 `6130cd1`、`5a48913`、`32057f0`、`50da5d0`、`eb30e48`、`caf63bf` 等）；本会话
  在此期间仍在本地累积自己的提交，双方的推送在远端相撞，触发「推送被拒 → 要求集成」（见同目录
  `records/bugs/2026-09-17/unauthorized-git-integration-after-push-rejected.md`）。
- 同一批文件被两侧并发修改并在集成时产生冲突：`docs/content/docs/progress/todo.mdx`、
  `我的规划/Fork同步与部署约定.md`。
- 同一模式在 agentflow 仓库本身复现：本会话需要修改 `skills/agentflow/references/contracts.md`
  时，发现该文件正被另一个会话修改（工作区未提交），无法安全编辑，只能停下并上报。

## 根因

Agentflow 已经规定「并行写入必须落在互不重叠的文件上」（`skills/agentflow/SKILL.md:81` 的委派
步骤，以及 `skills/agentflow/references/contracts.md` 中 disjoint file scopes 的段落），但这
条约束止步于文件路径，没有延伸到 git 层：

- 没有要求并行写入落在独立分支或独立工作区——提交、rebase、push 是共享的可变状态，两个
  执行者各自看来都只在写自己的文件范围，却在同一分支上叠加提交；
- 没有规定「同一分支同一时刻只允许一个执行者写入」；
- 没有跨会话 / 跨执行者的分支占用声明与交接规则——发现目标文件已被另一写入者占用时（本仓的
  `skills/agentflow/references/contracts.md` 就是实例），没有规定默认动作（停止并上报、等待，
  还是另建分支）。

这条文件级约束的隐含前提是「单个 supervisor 统一分配 write_scope」；一旦两个会话共享同一仓库与
分支，前提失效，而规则没有给出替代机制，也没有任何环节要求写入者在动手前声明自己占用了哪个
分支。归因 `workflow_policy`。

## 修复

待落地（属 improve 环范围，规则改动**尚未实施**，本记录保持 `open`，不写 `fix_revision`）：

- `skills/agentflow/SKILL.md` 的委派 / 集成步骤补一条 git 层隔离约束：并行写入各自分支或工作区；
  同一分支同一时刻单一写入者；跨会话共享仓库前先声明占用，发现占用时停止并上报。

## 变更记录

- 2026-09-17 00:00 · 建档（open）· 依据双写提交序列、冲突文件清单，以及本仓
  `skills/agentflow/references/contracts.md` 被并发占用的现状。
- 2026-09-17 · 修复落地 · 规则改动已实施（SKILL/contracts 三处补丁，版本 0.4.2）；待独立评审（规则文本变更，无自动化检测面可跑；validate.py all 仅验证记录结构完整。转 verified 前需评审人指定能证明约束生效的检查。）
