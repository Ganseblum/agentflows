---
class_id: unverified-behavior-claims
title: 以推演代替最小实验的行为断言
status: consolidated
consolidated_in: 0.13.0
first_record: ISS-2026-09-15-未验证行为断言反复出现
occurrences:
  - ISS-2026-09-15-未验证行为断言反复出现
  - ISS-2026-09-21-episode信号未验证零复发断言
  - ISS-2026-10-23-仓扫PASS被当作门有效的证据
recorded_at: 2026-09-16T11:57:15Z
updated_at: 2026-10-23T01:11:05+08:00
---

## 类模式

对工具、框架或宿主的行为以确定语气作出断言，但断言来自推演而非最小实验；断言被下一轮
复审的实验证伪，且错误的机制描述会掩盖真实缺陷——首现记录的第三例就掩盖了测试门的一个
完整绕过。

## 归纳内容（已吸收进 Agentflow 的哪一层）

- 0.3.4：硬边界 12（行为断言在最小实验复现前只是假设，含 supervisor 自身推断）+
  `AGENTS.md`「Experiments and recovery」规程（注入只在 /tmp 副本、恢复必须复跑检查观察到绿）。
- 0.8.4（再犯后重新归纳）：`skills/agentflow/references/document-chain.md` episode 捕获指引
  要求方法效果类信号区分「观察（未验证）」与「已验证（附检查命令与输出）」，且涉及「运行时
  装了什么」的信号以 `python3 tools/lab/validate.py installed` 输出为锚（该文本案在场，见
  该文件 installed 锚句）。
- 0.13.0（第 3 次再犯后重新归纳）：把「以 PASS 退出码代替实验」这条路在工具层堵掉——新增判据必须
  同时带正例、破坏例与不误伤例三类夹具（`tools/lab/doc_chain.py` 的 `--self-test` 用例 86–106 与本类
  现场一一对应），并要求以「门 PASS」为据的结论附扫描到的对象数或一次会失败的破坏实验；
  条款落 `docs/features/feature-2026-10-22-追溯闭环与证据在场/design/qa/testing.md` §4 的 V-05，
  现场记录落 `docs/issues/ISS-2026-10-23-仓扫PASS被当作门有效的证据.md`。

## 再犯历史

| 次序 | 记录 | 发现版本 | 归纳后？ | 处置 |
| --- | --- | --- | --- | --- |
| 1 | [ISS-2026-09-15-未验证行为断言反复出现](../ISS-2026-09-15-未验证行为断言反复出现.md) | 0.3.3 | 否（归纳前） | 归纳进 0.3.4（边界 12）；同类再犯时升级为评测用例 |
| 2 | [ISS-2026-09-21-episode信号未验证零复发断言](../ISS-2026-09-21-episode信号未验证零复发断言.md) | 0.8.3 | 是（0.3.4 之后） | 按升级条件触发评测用例义务；0.8.4 重新归纳（episode signal integrity 指引），`consolidated_in` 由 0.3.4 改 0.8.4 |
| 3 | [ISS-2026-10-23-仓扫PASS被当作门有效的证据](../ISS-2026-10-23-仓扫PASS被当作门有效的证据.md) | 0.12.0（修于 0.13.0） | 是（0.8.4 之后） | 以 `--repo` 的 PASS 推定「门在读」，被独立评审的字符级破坏实验证伪（该批次 15 行状态行从未被读到）；0.13.0 重新归纳（夹具三件套 + 「PASS 不是证据」条款），`consolidated_in` 由 0.8.4 改 0.13.0 |

注：`occurrences` 按记录计数（首现记录一个文件聚合了同一会话内的三例断言，计 1 条）。
2026-10-13 维护：ISS-2026-09-21-episode信号未验证零复发断言 此前只出现在「升级记录」正文与一处孤立列表项里，未进
`occurrences` 与本表，导致台账计数（1）与再犯事实（2 条）矛盾——已按再犯历史补齐，孤立
列表项移除。2026-10-23 维护：按同一教训，ISS-2026-10-23-仓扫PASS被当作门有效的证据 立录的**同时**就补齐 `occurrences`、
本表第 3 行与 `consolidated_in`，不留「正文提到而台账没记」的窗口。

## 升级条件（再犯时怎么加重）

同一类断言在 0.3.4 之后的版本再次出现时（新记录带 `class_id: unverified-behavior-claims`
且 `agentflow_version` 高于 `consolidated_in`），`python3 tools/lab/validate.py recurrence`
会把该类标为 `escalated`，并按首现记录 Notes 写明的触发条件升级为评测用例；归纳状态回到
`unconsolidated`，直到新版本重新归纳（本类已于 0.8.4 重新归纳）。

## 升级记录（2026-09-21）

ISS-2026-09-21-episode信号未验证零复发断言：episode method_effect_signal「零复发」缺证即断言（前提假：05~09 修复未安装；方法假：评审未报≠零复发）。按本类升级条件触发评测用例义务；吸收见候选 0.8.4（episode signal integrity 指引）。
