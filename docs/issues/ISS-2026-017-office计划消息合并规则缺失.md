---
bug_id: ISS-2026-017
title: 消息/事件双轨设计未定义合并去重规则——与目标仓 AGENTS.md 消息归属硬规则冲突
status: open
disposition: deferred
updated_at: 2026-10-23T00:18:22+08:00
severity: P2
error_kind: ai-ignored-doc
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

必查维度（AGENTS.md 对齐）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）设计为：

> `office_messages` …（用户可见消息，与事件流分离）

> 断线恢复：EventSource 带 `Last-Event-ID`，重连后由 Go 按 seq 重放补齐，页面刷新后历史从 `office_messages` 拉取。

而目标仓 AGENTS.md 已有硬性规则（infinite-canvas@1343820:AGENTS.md 内嵌片段）：

> Agent 对话消息必须同时按 `threadId`、`turnId` 和 `itemId` 归属；实时事件只用于补充未物化的 turn，历史快照成为权威后不得重复合并同一条消息。

计划的消息/事件双轨（刷新拉 messages、断线按 seq 重放事件）恰好踩在这条规则上，却未定义二者合并规则、归属键映射与幂等键——重放事件与已物化消息重复合并的风险正是该规则防的事故。

## 影响

实现者按计划落地会违反仓内既有硬规则，重放路径出现消息重复/错序。

## 根因

写双轨恢复设计时未检索仓内既有硬规则（AGENTS.md 消息归属与快照权威条款），协议自行新造。

## 备注

修复方向：计划补「重放事件 × 快照消息」的合并去重规则（归属键沿用/映射到 threadId/turnId/itemId，快照权威语义）。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F8，状态 open。

- 2026-10-23 00:18 · 归属登记 · 补 `disposition: deferred`：该条属被评审项目（见 frontmatter `project`），本仓不承接；C18 归属检查要求显式声明，来源见 `docs/features/feature-2026-10-22-追溯闭环与证据在场/plan/PLAN-TRACE-001.md` T07。
