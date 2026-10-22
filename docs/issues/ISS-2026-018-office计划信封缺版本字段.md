---
bug_id: ISS-2026-018
title: 事件信封与消息存储均无版本字段——违反目标仓「协议版本与存储版本独立管理」硬规则
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

必查维度（AGENTS.md 对齐 / 契约兼容）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）事件信封：

> 所有事件统一信封：`{"seq":42,"type":"delta","runId":"r_…","ts":…,"payload":{…}}`

无版本字段；`office_messages` content JSON 亦无版本管理声明。目标仓 AGENTS.md 硬规则（infinite-canvas@1343820:AGENTS.md 内嵌片段）：

> Agent 通信协议版本与消息存储版本必须独立管理；消息存储格式升级时必须先备份再迁移

一套明确要长期演进、含大量预留事件的三层契约，版本位缺失与仓规则直接冲突。

## 影响

协议演进与存储迁移将无版本锚点，违反仓内硬规则；修复成本一行，但事后补代价大。

## 根因

信封字段按当前最小需要列出，未对照 AGENTS.md「协议版本与存储版本独立管理」条款预留版本位。

## 备注

修复方向：事件信封加版本字段；声明消息存储版本独立管理及迁移规则。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F9，状态 open。

- 2026-10-23 00:18 · 归属登记 · 补 `disposition: deferred`：该条属被评审项目（见 frontmatter `project`），本仓不承接；C18 归属检查要求显式声明，来源见 `docs/features/feature-2026-10-22-追溯闭环与证据在场/plan/PLAN-TRACE-001.md` T07。
