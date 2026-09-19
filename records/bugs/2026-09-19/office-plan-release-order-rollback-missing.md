---
bug_id: BUG-20260919-011
title: 发布顺序×回滚点缺失，且「默认授予普通用户」与「限内测范围」两个声明互相矛盾
status: open
severity: P2
error_kind: missing-constraint
attribution: product_code
provenance: external
project: infinite-canvas
files:
  - records/reviews/infinite-canvas-office-agent-plan/archive/2026-09-19-001/第六期-AI办公助理Agent产品线.md
recorded_at: 2026-09-19T14:21:06Z
source_revision: infinite-canvas@1343820
agentflow_version: 0.8.0
---

## 现象

评审档位 Design（发布顺序×回滚点格）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）M1–M3 是构建顺序而非发布计划：无各阶段回滚点（office 权限/路由/表按什么顺序下线、nginx location 摘除、feature flag）。且两处声明打架：

> 新增权限点：`office.read` / `office.write`（金标权限 30 → 32），默认授予普通用户

> 容器即沙箱的隔离强度 | 限内测范围；公众开放前必须完成阶段二

默认授予普通用户即全量放开，与「限内测」矛盾。

## 影响

阶段一隔离边界未经验收即可能全量暴露；出问题无成体系的回退路径。

## 根因

里程碑按构建顺序书写，未转换为「对外可发布状态 × 回退路径」视角；权限默认授予（安全节）与限内测（风险表）分处两节未对撞。

## 备注

修复方向：各里程碑配回滚点；权限改为默认仅授予内测角色，灰度路径明确。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F11，状态 open。
