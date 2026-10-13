---
class_id: unverified-behavior-claims
title: 以推演代替最小实验的行为断言
status: unconsolidated
consolidated_in: 0.3.4
first_record: ISS-2026-006
occurrences:
  - ISS-2026-006
  - ISS-2026-039
recorded_at: 2026-09-16T11:57:15Z
updated_at: 2026-10-13T00:00:00+08:00
---

## 类模式

对工具、框架或宿主的行为以确定语气作出断言，但断言来自推演而非最小实验；断言被下一轮
复审的实验证伪，且错误的机制描述会掩盖真实缺陷——首现记录的第三例就掩盖了测试门的一个
完整绕过。

## 归纳内容（已吸收进 Agentflow 的哪一层）

- 0.3.4：硬边界 12（行为断言在最小实验复现前只是假设，含 supervisor 自身推断）+
  `AGENTS.md`「Experiments and recovery」规程（注入只在 /tmp 副本、恢复必须复跑检查观察到绿）。

## 再犯历史

| 次序 | 记录 | 发现版本 | 归纳后？ | 处置 |
| --- | --- | --- | --- | --- |
| 1 | [ISS-2026-006](../ISS-2026-006-未验证行为断言反复出现.md) | 0.3.3 | 否（归纳前） | 归纳进 0.3.4（边界 12）；同类再犯时升级为评测用例 |
| 2 | [ISS-2026-039](../ISS-2026-039-episode信号未验证零复发断言.md) | 0.8.3 | 是（0.3.4 归纳之后） | 再犯，档位 escalated；评测用例义务未履行（待办）；归纳状态回到 unconsolidated |

注：首现记录一个文件聚合了同一会话内的三例断言，`occurrences` 按记录计数，因此 006 计 1 次；
ISS-2026-039 计第 2 次。档位由 `validate.py recurrence` 推导（039 的 `agentflow_version` 0.8.3
高于 `consolidated_in` 0.3.4，故为 `escalated`）。

## 升级条件（再犯时怎么加重）

同一类断言在 0.3.4 之后的版本再次出现时（新记录带 `class_id: unverified-behavior-claims`
且 `agentflow_version` 高于 `consolidated_in`），`python3 tools/lab/validate.py recurrence`
会把该类标为 `escalated`，并按首现记录 Notes 写明的触发条件升级为评测用例；归纳状态回到
`unconsolidated`，直到新版本重新归纳。

## 升级记录（2026-09-21）

ISS-2026-039：episode method_effect_signal「零复发」缺证即断言（前提假：05~09 修复未安装；方法假：评审未报≠零复发）。按本类升级条件触发评测用例义务；吸收见候选 0.8.4（episode signal integrity 指引）。

2026-10-13 台账核对：ISS-2026-039 原先只在正文提及、frontmatter 无 `class_id`/`occurrence`，occurrences 仅含 006。
现已把 039 入册（`occurrence: "2"`），判定依据是 039 的「零复发」断言同样缺最小实验证据，属本类。
