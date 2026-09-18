---
bug_id: BUG-20260917-904
title: 【样板】再犯类第 2 次——归纳后再犯（台账会标 escalated）
status: fixed-pending-review
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflows
class_id: demo-recurrence-class
occurrence: 2
files:
  - skills/agentflow/SKILL.md
recorded_at: 2026-09-17T02:00:00Z
updated_at: 2026-09-17T02:20:00Z
agentflow_version: 0.4.2
regression_status: not-run
---

## 现象

（演示）同类约束缺口在 0.4.1 归纳之后、0.4.2 再次出现——执行者在另一条路径上重复了
同一遗漏。

## 根因

0.4.1 的归纳只覆盖了原路径，未覆盖同机制的旁路。归因 `workflow_policy`。

## 修复

待落地：按台账升级条件，本类触发 improve 环升级（重归纳，通常升为评测用例），
归纳状态回到 unconsolidated 直到新版本重新归纳。

## 变更记录

- 2026-09-17 02:00 · 建档（open）· 判定为已归纳类的再犯（agentflow_version 0.4.2 >
  consolidated_in 0.4.1）。
- 2026-09-17 02:20 · 转 fixed-pending-review · 升级动作待执行。
