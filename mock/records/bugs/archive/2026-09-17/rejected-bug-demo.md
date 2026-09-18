---
bug_id: BUG-20260917-905
title: 【样板】rejected 状态——归档形态（只出现在 records/bugs/archive/ 下）
status: rejected
severity: P3
error_kind: other
attribution: unknown
provenance: session-artifact
project: agentflows
files:
  - skills/agentflow/SKILL.md
recorded_at: 2026-09-17T01:30:00Z
updated_at: 2026-09-17T02:10:00Z
rejection_reason: 澄清后确认是预期行为（非缺陷），按约定移入 archive/
---

## 现象

（演示）一次看起来异常的行为，建档后经澄清为设计内行为。

## 根因

误报：所述行为在规格中即为预期，不属于缺陷。

## 修复

不适用——本记录以 `rejected` 归档，保留判定依据供回溯；不得留在活动记录区
（校验器强制：rejected 必须在 `records/bugs/archive/` 下）。

## 变更记录

- 2026-09-17 01:30 · 建档（open）· 行为异常上报。
- 2026-09-17 02:10 · 转 rejected · 澄清为预期行为，移入 archive/。
