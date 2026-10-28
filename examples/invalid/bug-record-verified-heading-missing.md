---
bug_id: ISS-2026-09-14-缺审查标题
title: verified 记录缺少「## 审查」正文节
status: verified
severity: P3
error_kind: other
attribution: workflow_policy
provenance: agentflow
project: example-project
files:
  - examples/invalid/bug-record-verified-heading-missing.md
recorded_at: 2026-09-14T08:00:00Z
agentflow_version: 0.2.0
reviewer: agentflow:reviewer（演示）
review_decision: approved
regression_status: pass
closure_criteria: "python3 -c 'print(1)' 退出码 0（演示占位）"
updated_at: 2026-09-14T09:00:00Z
---

## 现象

该记录声称已修复并验证；frontmatter 的 verified 必填字段（reviewer / review_decision /
regression_status / closure_criteria）全部在场——它的非法点**只在正文**：缺少
「## 审查」独立审查节。

## 根因

用于演示 `verified` 状态的正文硬节：schema 只看得到字段，正文独立审查节由校验器的跨
字段规则强制。本记录刻意省略了它。

## 修复

不适用——这是刻意的非法示例；校验器必须拒绝它。
