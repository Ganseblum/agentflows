---
class_id: demo-recurrence-class
title: 【样板】再犯类台账——已归纳后在更高版本再犯（档位 escalated）
status: consolidated
consolidated_in: 0.4.1
first_record: BUG-20260917-903
occurrences:
  - BUG-20260917-903
  - BUG-20260917-904
recorded_at: 2026-09-17T02:30:00Z
updated_at: 2026-09-17T02:30:00Z
---

## 类模式

（演示）同一约束缺口在认知/条款/旁路三层反复出现：归纳只修了原路径，同机制的旁路未被
覆盖，于是以"同一类、不同入口"的形态再犯。

## 归纳内容（已吸收进 Agentflow 的哪一层）

- 0.4.1：`skills/agentflow/references/contracts.md` 对应小节补条款（首现路径）；
- 待重归纳：0.4.2 的再犯表明归纳面不足，按升级条件升为评测用例覆盖旁路。

## 再犯历史

| 次序 | 记录 | 发现版本 | 归纳后？ | 处置 |
| --- | --- | --- | --- | --- |
| 1 | [BUG-20260917-903](../2026-09-17/recurrence-occ1-demo.md) | 0.4.0 | 否（归纳前） | 归纳进 0.4.1 |
| 2 | [BUG-20260917-904](../2026-09-17/recurrence-occ2-demo.md) | 0.4.2 | **是（0.4.2 > 0.4.1）** | 升级：重归纳 + 评测用例；归纳状态回 unconsolidated |

## 升级条件（本台账当前命中）

`python3 tools/lab/validate.py recurrence` 会把本类标为 `escalated`（存在发现版本高于
`consolidated_in` 的记录）。按首现记录既定触发条件升级为评测用例；重新归纳后更新
`consolidated_in` 并把 `status` 回到 `consolidated`。
