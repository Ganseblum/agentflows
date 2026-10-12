---
bug_id: ISS-2026-013
title: 缺关键路径分步时序表——架构图与契约散文不可替代步骤表基线
status: open
severity: P1
error_kind: missing-constraint
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

评审档位 Design（关键路径时序格）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）有架构图与两层契约的散文描述、事件类型表，但没有一张「用户发消息 → Go 建 run → POST /v1/runs → 事件逐条落库转发 → done → 计费」的分步时序表。设计档要求用户真实请求链以步骤表为基线，图不可替代表；后续异常矩阵也需要这张表作行头。

## 影响

关键路径无基线，异常矩阵无处挂行；实现顺序与验证断言缺少可对照的分步契约。

## 根因

模板无关键路径时序表强制项；架构图加契约散文被当成了完整设计表达，「图示关系、步骤表承载过程」的分工未被遵守。

## 备注

修复方向：补关键路径分步时序表（含每步的责任方、输入输出、失败分支指针），作为异常矩阵行头。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F4，状态 open。
