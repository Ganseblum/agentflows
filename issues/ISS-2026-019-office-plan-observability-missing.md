---
bug_id: ISS-2026-019
title: 可观测性缺失——四跳链路无日志/指标/trace 设计，配合无告警无法线上排障
status: open
severity: P2
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

评审档位 Design（可观测性格）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）部署节与上线前检查清单均为功能性检查（迁移验证、curl 冒烟、重连演练、对账），全文未点名可观测性：跨 web→Go→Runtime→LiteLLM 四跳，故障定位靠什么（run_id/session_id 贯穿的日志、事件延迟/失败指标、trace）没有任何交代；配合 ISS-2026-010（无告警设计），线上排障无抓手。

## 影响

分钟级长任务 + 多跳转发 + 外部网关的链路，故障时无法定位是哪一跳的问题；计费纠纷与孤儿 run 无审计线索。

## 根因

上线检查清单按功能验收组织，可观测性不在作者默认清单内；模板未强制可观测性小节。

## 备注

修复方向：补可观测性小节（run_id/session_id 贯穿日志、关键指标、孤儿 run 与计费失败的告警）。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F10，状态 open。
