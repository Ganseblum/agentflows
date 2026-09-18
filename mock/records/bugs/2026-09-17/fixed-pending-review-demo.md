---
bug_id: BUG-20260917-902
title: 【样板】fixed-pending-review 状态——修复已落地，等待独立评审
status: fixed-pending-review
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflows
files:
  - skills/agentflow/references/contracts.md
recorded_at: 2026-09-17T01:10:00Z
updated_at: 2026-09-17T01:40:00Z
source_revision: 779f9d4
agentflow_version: 0.4.2
regression_status: not-run
fix_revision: agentflows@779f9d4
---

## 现象

（演示）某条委派约束在简报中缺失，实施者按不完整简报开工，产出被退回重做。

## 根因

简报纪律没有强制该约束。归因 `workflow_policy`：流程缺口，非执行者知识不足。

## 修复

已在 `skills/agentflow/references/contracts.md` 对应小节补齐约束条款。

## 变更记录

- 2026-09-17 01:10 · 建档（open）· 展示诊断入库。
- 2026-09-17 01:40 · 修复落地 · 转 fixed-pending-review；`regression_status: not-run`（规则
  文本变更无自动化检测面，待评审人指定能证明约束生效的检查）。
