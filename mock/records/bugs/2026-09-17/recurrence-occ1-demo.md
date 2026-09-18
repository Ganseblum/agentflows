---
bug_id: BUG-20260917-903
title: 【样板】再犯类第 1 次——类台账 occurrence 1（归纳前）
status: fixed-pending-review
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflows
class_id: demo-recurrence-class
occurrence: 1
files:
  - skills/agentflow/references/contracts.md
recorded_at: 2026-09-17T01:20:00Z
updated_at: 2026-09-17T01:50:00Z
agentflow_version: 0.4.0
regression_status: pass
---

## 现象

（演示）某类约束缺口第一次出现：执行者交付的产物缺少必需的边界声明。

## 根因

该类问题在 0.4.0 尚无条款覆盖。归因 `workflow_policy`。

## 修复

0.4.1 归纳：新增对应约束条款（见类台账 `demo-recurrence-class` 的归纳内容）。

## 变更记录

- 2026-09-17 01:20 · 建档（open）· 类首现，按类登记。
- 2026-09-17 01:50 · 归纳落地 · 0.4.1 补条款；本记录转 fixed-pending-review。
