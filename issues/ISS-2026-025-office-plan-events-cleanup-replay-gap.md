---
bug_id: ISS-2026-025
title: 事件清理策略未定义，且清理与 Last-Event-ID 重放的空洞语义缺失
status: open
severity: P3
error_kind: other
attribution: product_code
provenance: external
project: infinite-canvas
files:
  - reviews/infinite-canvas-office-agent-plan/archive/2026-09-19-001/第六期-AI办公助理Agent产品线.md
recorded_at: 2026-09-19T14:21:06Z
source_revision: infinite-canvas@1343820
agentflow_version: 0.8.0
---

## 现象

必查维度（事件顺序与生命周期）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）：

> `office_events` | BIGINT 自增、run_id、seq、type、payload JSON；UNIQUE(run_id, seq)，按 session 清理

清理策略（触发时机、保留期）未定义，且与重放互相作用：客户端持旧 Last-Event-ID 重放已清理区间时的语义（空洞如何响应、是否返回终结指令）未定义。

## 影响

长会话事件表无限增长或清理后重放行为未定义，二选一都会在生产踩到。

## 根因

清理策略压缩成表字段内五个字（「按 session 清理」），未展开生命周期，也未推演清理与重放的交互。

## 备注

修复方向：定义保留期与触发时机；声明重放命中空洞时的响应契约（如返回 410/终结事件）。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F16，状态 open。
