---
bug_id: BUG-20260919-001
title: 计划书无异常矩阵——超时/并发/状态迁移/孤儿 run 等失败模式全部未定义
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

评审档位 Design（异常矩阵格）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）中「风险与对策」表是风险登记册而非异常矩阵，以下失败模式全文无定义：

- (a) 超时：Go→Runtime `POST /v1/runs`、模型生成停摆、契约二 SSE 空闲、LiteLLM 上游超时，全文无一个超时值；
- (b) 重复/并发提交：同一会话并发 run 的策略未定义，`POST /v1/runs` 无幂等键，cancel 对已终态 run 的语义未定义；
- (c) 状态迁移主体：`queued → running` 由谁迁移未定义；
- (d) 孤儿 run 回收：Go 或 Runtime 崩溃后 running 态 run 谁在何时翻终态未定义——M1 验收「杀 Runtime 进程后重连不丢事件」恰好会在此漏洞下通过（事件重放正常而 run 永远卡 running）；
- (e) 契约二无重放：Go 重启后丢失 Runtime 事件流续接语义未定义；
- (f) 告警：全文无任何告警设计。

决定性片段（快照引用）：

> 状态机 `queued → running → succeeded | failed | cancelled`

「点数硬闸」「降级为截断」等表述按评审契约属无信息 fail-safe 措辞。

## 影响

文档自称硬要求的两项（防账单失控、事件不丢）在失败模式下不闭环；实现者无异常行为可依据，各写各的。

## 根因

模板仅有「风险与对策」登记册章节，未强制异常矩阵；作者将风险登记册当成异常处理设计的全部，未按「关键路径 × 失败模式」逐格推演。

## 备注

修复方向：以关键路径步骤表为行头补异常矩阵，每格写明检测、处理、重试主体/次数/退避、幂等前提、用户可见结果、告警；空格显式 N/A + 理由。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 第二方评审 finding F1，状态 open。
