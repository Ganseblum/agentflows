---
bug_id: BUG-20260915-003
title: 反复出现的一类——以推演代替最小实验的行为断言，在随后每轮复审中均被证伪
status: fixed-pending-review
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflows
class_id: unverified-behavior-claims
occurrence: 1
files:
  - skills/agentflow/references/contracts.md
  - AGENTS.md
  - docs/next-session-handoff.md
affected_slices:
  - delegation-contracts
  - supervisor-discipline
  - gate-maintenance
recorded_at: 2026-09-15T03:23:11Z
updated_at: 2026-09-16T12:03:24Z
source_revision: 33962ee
agentflow_version: 0.3.3
regression_status: pass
---

## 现象

连续三轮设计/评审，每轮都包含至少一条"关于工具行为"的断言，以推演代替实验、以确定语气
写出，随后被下一轮的最小实验证伪：

| 轮次 | 断言 | 实验证伪结果 |
| --- | --- | --- |
| 第四批（隐式行为设计） | "401 冲突不在调用链上，靠往下追找不到" | 拦截器就注册在 axios 封装里，追一层即可看见机制；看不见的是冲突（需要状态维度）——断言把"机制不可达"和"冲突不可见"混为一谈 |
| 第四批（隐式行为设计） | "清单缺行结构上就能查出来" | 行内必填字段查不出"缺行"；真正可查的是显式空声明（`shared_mechanisms: []`）——"没问"与"问了、答案是没有"不可区分 |
| 第五批（门加固） | "`tests/__init__.py` 会在测试运行前 patch 被钉住的测试" | `discover -s tests` 下该文件完全不执行（实验 exit=0）；真实向量是子目录包的导入副作用——错误断言恰好掩盖了实际存在且更糟的完整绕过（见 BUG-20260915-002 同轮修复） |

第三例后果最重：基于错误机制描述交付的门存在完整绕过（子目录替换测试方法 → 改坏的断言
通过 → `validate.py tests` 返回 PASS），直到下一轮以实验复审才被发现并关闭。

## 根因

纪律只覆盖了 worker：「摘要不是验证，只有复现的确定性检查才是」（硬边界 4）——但没有任何
条款约束 **supervisor/主会话自己关于工具行为的推断**。推演unittest 的导入顺序、git checkout
的语义、JSON Schema 校验器的可查性，看起来都足够可信，于是被当成事实写进了设计和文档。
共性不是知识错误而是流程缺口：断言工具行为时没有强制"先做最小实验"这道工序。

归因 `missing-constraint` 而非 `hallucination`：三条断言都是有依据的合理推断，错在以事实
语气输出未验证的推断，而这正是当时契约没有禁止的行为。

## 修复

`contracts.md` 硬边界新增第 12 条（单点来源，两个 SKILL 共同引用）：

> A claim about how a tool, framework, or host behaves is a hypothesis until a minimal
> experiment reproduces it — exit codes and verbatim output are the evidence; reasoning about
> the implementation is not. State unverified behavior as unverified.

它是硬边界 4 的推广：4 管的是 worker 摘要，12 管的是 supervisor 自己的推断。与
`docs/host-platform-facts.md` 的既有实践一致（`doc` 行标未验证、实测行带证据）。

## 回归检查

- 条款已写入 `contracts.md`；`python3 tools/lab/validate.py all` 七项 PASS。
- 本轮复审本身即该纪律的实证样例：三条断言全部以最小实验的 exit code / 输出原文证伪，
  修复（子目录拒绝）亦以同一攻击复验 FAIL。

## 备注

- 若边界 12 生效后同类断言再犯，按 improve 环升级为评测用例（把"supervisor 必须对行为
  断言索要实验证据"变成可回归断言）；本轮不加，理由：三次实例均发生在门维护的元工作里
  而非任务简报执行中，当前回归面是每轮的实验化审计本身。
- 状态 `fixed-pending-review`：条款修复尚无独立 Reviewer 判定。
