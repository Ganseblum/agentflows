---
bug_id: ISS-2026-09-14-无审查声明
title: verified 记录缺少独立审查
status: verified
severity: P3
error_kind: other
attribution: workflow_policy
provenance: agentflow
project: example-project
files:
  - examples/invalid/bug-record-verified-without-review.md
recorded_at: 2026-09-14T08:00:00Z
agentflow_version: 0.2.0
---

## 现象

该记录声称已修复并验证。

## 根因

用于演示 `verified` 状态必须有独立证据：本记录刻意省略了 schema 对
`status: verified` 强制要求的 `reviewer`、`review_decision` 与 `regression_status`。

## 修复

不适用——这是刻意的非法示例；校验器必须拒绝它。

## 审查

（本示例的非法点只在 frontmatter 缺 reviewer / review_decision / regression_status。）

## 变更记录

- 2026-09-14 09:00 +00:00 · verified · 刻意缺 schema 审查字段（示例）
