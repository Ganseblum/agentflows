---
test_plan_id: TP-<YYYYMMDD>-<NNN>
title: "<用例库名称>"
project: <项目名>
feature: <feature-slug>
target_revision: <被测基线 revision>
credentials: <凭据运行时注入；值永不落盘>
base_url: <环境 URL>
case_count: "<与 ## 用例 注册表行数相等>"
test_version: "1"
status: active
recorded_at: "<RFC 3339 含时区>"
updated_at: "<RFC 3339 含时区，≥ recorded_at>"
---

# <用例库名称> — 自动化测试计划（testing/plan-<YYYY-MM-DD>-<NNN>.md）

> 用例步骤写给从未读过实现代码的操作者：每一步的预期都是可观察结果（页面元素、提示文案、
> 网络请求是否发出），不写实现细节。就地修订：只补用例并刷新 `case_count`、递增
> `test_version` 与 `updated_at`；单轮执行结果由 run-* 承载，本文件不写执行结果。

## 用例

<填：每个用例先在注册表加一行，再补同名的 ### 详情小节；级别枚举 smoke/e2e/api/boundary>
| 用例 ID | 级别 | 优先级 | 标题 |
| --- | --- | --- | --- |
| TC-<域>-<序号> | smoke | P0 | <一句话，含可观察预期> |

### TC-<域>-<序号> <同一标题>

前置：<状态与账号角色>。

| # | 操作 | 输入 | 预期可观察结果 |
| --- | --- | --- | --- |
| 1 | <操作> | <输入> | <可观察预期> |

## 边界覆盖

<填：未覆盖的边界写「未覆盖 — <原因>」，不许留空>
| 边界类 | 覆盖用例 | 说明 |
| --- | --- | --- |
| <空输入 / 非法格式 / 超长输入 / 已存在数据 / 未覆盖> | TC-<域>-<序号> | <说明> |

## 流程疑点

- Q1：<行为未在可见文档声明处写明——先声明再补用例；每条注明去向>
