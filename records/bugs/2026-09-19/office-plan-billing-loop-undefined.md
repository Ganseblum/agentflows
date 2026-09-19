---
bug_id: BUG-20260919-002
title: 计费闭环四问无答案——run 中点数检测、扣减事务边界、失败补偿、cost 计量口径均未定义
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

评审档位 Design（异常矩阵计费格）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）计费设计仅一句：

> 计费：按 run 结束回填 token 用量，经 LiteLLM cost 追踪映射为点数扣减，复用 billing 域；点数不足发 `quota_exhausted` 事件并终止 run（防账单失控是硬要求）。

四问全无答案：(1) run 发起前有无预检/预估扣减；(2) run 中途点数耗尽由谁、以什么频率、按什么口径检测——done 事件才回填则硬闸拦不住单次长 run 的失控消耗；(3) run 终态与扣减落库之间 Go 崩溃的窗口如何补偿（失败 run 已耗 token 计不计费、退不退）；(4) LiteLLM cost 追踪对翻译路径与直通路径的计量口径（评审证据基线明确标注 LiteLLM cost 精度未验证）。

## 影响

「防账单失控」被文档自称硬要求，但没有任何一格写清检测与处理；长 run 失控消耗在当前设计下不可拦截。

## 根因

计费只写了正常路径（run 结束回填），模板未逼问中途耗尽、扣减窗口崩溃与计量口径；「防账单失控」被写成目标而非机制。

## 备注

修复方向：补预检、run 中检测机制（谁/多久/什么口径）、终态与扣减的事务边界、失败补偿规则；「LiteLLM cost 精度对账」从上线检查项升格为 M3 门禁。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F2，状态 open。
