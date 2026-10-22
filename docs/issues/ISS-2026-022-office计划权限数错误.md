---
bug_id: ISS-2026-022
title: 金标权限基数事实错误——计划写「30 → 32」，注册表现有 32 个应为 32 → 34
status: open
disposition: deferred
updated_at: 2026-10-23T00:18:22+08:00
severity: P3
error_kind: hallucination
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

必查维度（事实核对）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）写：

> 新增权限点：`office.read` / `office.write`（金标权限 30 → 32）

评审实测目标仓权限注册表（infinite-canvas@1343820:server/internal/authz/catalog.go，决定性片段）：

```go
var registry = []PermissionDef{
	{Key: PermStatsRead, Module: "stats", Name: "查看总览", ...},
```

注册表条目计数 `grep -c 'Key:'`（catalog.go L82–117）= **32**（stats3+users3+models2+channels2+moderation3+packages2+orders2+settings2+community2+roles2+audit1+membership2+sso2+feedback2+blog2）。「30」的基数来自会话早期提交信息、未读代码，已被工作树证伪。实现者按 30→32 写金标测试预期会直接撞 catalog_test.go。

## 影响

按错误基数落实现/测试，权限相关验收与既有断言冲突。

## 根因

基数取自会话记忆（早期提交信息「金标权限 28→30」），未读注册表现值即沿写为「30 → 32」。

## 备注

修复方向：计划改为 32 → 34（或注明「以实现时注册表实数为准」并声明核对方式）。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F13，状态 open。

- 2026-10-23 00:18 · 归属登记 · 补 `disposition: deferred`：该条属被评审项目（见 frontmatter `project`），本仓不承接；C18 归属检查要求显式声明，来源见 `docs/features/feature-2026-10-22-追溯闭环与证据在场/plan/PLAN-TRACE-001.md` T07。
