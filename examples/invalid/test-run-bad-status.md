---
test_run_id: TR-2026-09-17-002
title: "登录用例回归执行（演示项目，非法状态负例）"
project: demo-webapp
test_plan_id: TP-2026-09-17-001
test_plan_version: "1"
target_revision: 9f2c1a7
environment: staging（base_url 见计划）；宿主浏览器由 supervisor 按步骤脚本执行；账号角色 tester-01
credentials: session-injected env；值永不落盘
summary_pass: "1"
summary_fail: "0"
summary_blocked: "0"
summary_not_run: "0"
decision: partial
recorded_at: "2026-09-17T16:30:00Z"
updated_at: "2026-09-17T16:30:00Z"
---

# 登录用例回归执行（演示项目，非法状态负例）

负例：结果表使用固定枚举之外的状态词，必须被校验拒绝。

## 结果

| 用例 ID | 状态 | 证据 | 说明 |
| --- | --- | --- | --- |
| TC-LOGIN-001 | maybe | — | 非法状态词，校验必须拒绝本记录 |

## 证据

无——本记录是负例，不承载真实执行证据。

## 结论

负例用于钉住结果枚举：pass / fail / blocked / not-run 之外的词必须被拒绝。
