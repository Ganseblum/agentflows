---
bug_id: BUG-20260919-003
title: resume-per-turn 与「Runtime 可水平扩展」互相矛盾——同会话跨容器 transcript/工作区竞态未定义
status: open
severity: P1
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

必查维度（并发/状态机无定义态）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）同时声明：

> Runtime 保持近无状态，可水平扩展。

> 工作区：`/data/workspaces/{sessionId}/`，持久卷挂载

resume-per-turn 要求上一 run 的 transcript 先落定才能续接；同一会话两个 run 落到不同容器、共享持久卷时，transcript 与工作区文件存在竞态，resume 语义直接破坏。计划未定义：同会话 run 是否在 Go 层强制串行、扩展实例如何共享工作区卷（单机 compose 与横向扩展本身互相矛盾）、跨容器 resume 的会话文件寻址。

## 影响

状态机存在无定义状态；「近无状态可水平扩展」的声明与 resume 机制的前提冲突，按哪句实现都会坏掉另一句。

## 根因

两处声明各自在行业中常见，作者未将「无状态扩展」与「transcript/工作区落在本地卷」放进同一张图对撞；未定义同会话串行的归属方。

## 备注

修复方向：定义同会话串行规则（Go 层按 session 串行 run），并解释横向扩展与单机 compose/共享卷的关系，或收缩为单实例声明。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F3，状态 open。
