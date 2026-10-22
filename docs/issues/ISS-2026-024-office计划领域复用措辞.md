---
bug_id: ISS-2026-024
title: 「复用 billing 域 / 经现有 moderation 域」措辞误导跨产品域 import——仓规要求走 platform/service 层
status: open
disposition: deferred
updated_at: 2026-10-23T00:18:22+08:00
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

必查维度（AGENTS.md 对齐）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）写：

> 复用 billing 域

> 用户输入经现有 moderation 域审查

而目标仓 AGENTS.md 规定（infinite-canvas@1343820:AGENTS.md 内嵌片段）：

> 产品域之间不互相 import；确需共享的契约下沉到 `model`（如 `StorageKeyRe`、统计时区）或 `platform`，通用 HTTP 辅助进 `httpx`

仓内现成正确路径是 platform/billing 与 service 层。评审实测证据（infinite-canvas@1343820:server/internal/platform/billing/service.go）：

```go
// Package billing 平台点数域：credit_accounts 与 credit_transactions 的唯一业务入口。
```

（infinite-canvas@1343820:server/internal/service/moderation.go 存在，包声明 `package service`。）计划措辞会误导实现者跨产品域 import。

## 影响

实现者照字面落地会违反 server 结构规范，review 阶段返工。

## 根因

措辞沿用了架构图分层名（billing 域/moderation 域），未对齐仓内依赖方向规则的合法复用路径命名。

## 备注

修复方向：改写为「经 platform/billing 与 service 层复用」。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F15，状态 open。

- 2026-10-23 00:18 · 归属登记 · 补 `disposition: deferred`：该条属被评审项目（见 frontmatter `project`），本仓不承接；C18 归属检查要求显式声明，来源见 `docs/features/feature-2026-10-22-追溯闭环与证据在场/plan/PLAN-TRACE-001.md` T07。
