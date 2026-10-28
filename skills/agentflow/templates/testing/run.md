---
test_run_id: TR-<YYYY-MM-DD>-<NNN>
title: "<本轮执行名称>"
project: <项目名>
test_plan_id: TP-<YYYY-MM-DD>-<NNN>
test_plan_version: "<钉住的计划 test_version>"
target_revision: <被测 revision>
environment: <环境：origin / 浏览器 / 账号角色>
credentials: <凭据运行时注入；值永不落盘>
summary_pass: "<数量>"
summary_fail: "<数量>"
summary_blocked: "<数量>"
summary_not_run: "<数量>"
decision: pass
recorded_at: "<RFC 3339 含时区>"
updated_at: "<RFC 3339 含时区>"
---

# <本轮执行名称> — 测试执行记录（testing/run-<YYYY-MM-DD>-<NNN>.md）

> 一轮一个新文件；更正已发生的结果时在**同一记录**刷新 `updated_at`（已发生的证据不改写）。
> 实际结果列写观察到的真实行为；fail 行的实际结果须与计划预期形成可对照差异。
> `decision: pass` 要求零 fail 且零 blocked；fail / blocked 行必须在 ## 证据 有原始输出；
> 钉住计划当前 `test_version` 时，注册表中的每个用例都要在结果表有交代。

执行范围：计划 test_version <N> 的哪些用例；判定只依据原始输出，不依据转述。

## 执行阶段与输入

| 项 | 实际内容 |
| --- | --- |
| 阶段 | <预检 / 目标失败 / 实现通过 / 重构回归> |
| 实际输入 | <提交、工作树内容或最终执行快照；使用工具时引用封存指纹和结果> |
| 精确用例与报告 | <测试路径、原生完整用例名及本次报告位置> |
| 目标失败依据 | <预期与实际失败原因；未发现用例、坏夹具、缺依赖不算有效失败> |
| 选测/复用依据 | <本次范围与未覆盖项；引用仍有效证据及核验条件> |

工具结果只是本记录的证据，不能取代计划版本、目标版本或状态权威。字段形态不因使用工具新增前置信封键。

## 结果

<填：状态枚举 pass / fail / blocked / not-run——之外的状态词一律被校验拒绝>
| 用例 ID | 状态 | 证据 | 实际结果 | 说明 |
| --- | --- | --- | --- | --- |
| TC-<域>-<序号> | pass | — | <观察到的真实行为> | <补充> |

## 证据

<填：原始输出块（截图 / 网络面板 / trace）；fail 与 blocked 行必须有可复现的证据引用>

## 覆盖复核

| 判断 | 结果与依据 |
| --- | --- |
| 记录合法 | <字段、引用与版本关系的检查> |
| 执行满足预期 | <本次快照实际执行的精确用例、命令与原始输出> |
| 覆盖经过复核 | <独立评审从真实入口、需求、失败路径和断言反查的结论；未完成如实写明> |

三种结论不能互代；必需用例未执行或关键场景未覆盖，不能因部分用例通过报功能完成。

## 结论

- 冒烟集与主流程：<通过 / 有失败逐条说明>
- 失败项：<可直接照跑的 Ego 操作序列（步骤、期望与实际、证据）、bug 记录去向（`ISS-<YYYY-MM-DD>-<slug>` id）>
- 状态联动：<本轮为已立 bug 的回归轮时，逐条点名结果支撑的 bug 状态变化——用例 pass 即支撑
  该 `ISS-*` 的 `regression_status: pass`（供 supervisor 评审后转 fixed-pending-review）；
  fail/blocked 则写明对应 bug 不前进或退回。executor 只报证据，bug 状态由 supervisor/recorder 回写>
- 流程疑点：<与计划声明的对照，下一轮决策>
