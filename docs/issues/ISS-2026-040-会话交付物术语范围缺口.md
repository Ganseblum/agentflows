---
bug_id: ISS-2026-040
title: 会话交付分析报告在表达纪律作用域外——三件套全锚文档链，代号裸用与模式词直搬散文两个新形态无条款/装置/评审覆盖
status: fixed-pending-review
regression_status: not-run
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/references/document-chain.md
  - skills/agentflow/references/roles.md
  - agents/reviewer.md
  - tools/lab/doc_chain.py
recorded_at: 2026-09-22T13:55:00+08:00
source_revision: agentflows@e32ef14 (0.8.4) + uncommitted 0.8.5/0.8.6 candidate working tree
agentflow_version: 0.8.4
fix_revision: agentflows 0.8.6（原 `releases/0.8.6.json`，2026-09-22 用户批准发布，该文件随 2026-10-12 版本记录停用删除；同批已按用户对照表就地修复两份存量报告并 --file exit 0）
class_id: session-deliverable-jargon-scope
occurrence: "1"
---

## 现象

用户反馈（2026-09-22）：「agentflow 写的东西还是有黑话」，并给出一张自制黑话→白话对照表（九组词）：撞墙/积分墙→积分不足被中断；免费档/付费档→免费用户/付费用户；A 桶/D 桶/G 桶→A 已交付/D 积分耗尽/G 停在确认或异常；零交付/零制品→没拿到成品；白烧→完全浪费；跑飞→消耗异常；草稿泄漏→把模型内部思考当成回复发出；prepared 会话→前端一建就留下的空记录；Run→执行（正文用「执行」，代码和 SQL 里保留 Run）。

语料核实：九组词中七组逐字命中 aiwork 仓 `temp/` 下两份会话内交付的数据分析报告（独立分析产物，非文档链）。决定性片段（行号为报告自身行号）：

> AIPPT 专家交付漏斗分析（自署 2026-09-16 16:00）：663 「全网 58.7% 的积分被"最终撞墙"的会话消耗，其中 36.2% 是彻底白烧——用户没拿到任何文件」

> 同报告 :30 「**C** 空会话（前端预建占位行） | `status='prepared'`，无任何 Run」；§2 标题 :99 「真实交付明细（A 桶：36 会话 / 44 个 .pptx）」；:83 「"白烧"的会话烧得更多」；:81/:288/:466 等十处「零交付」

> 会话聚合分析近 7 天全专家（0910-0916）：137 「跑得很深才撞墙」；148/263 「全部零交付」

报告没有黑话对照表——用户那张表是用户自己被迫做的解码器。其余两词（免费档/付费档、草稿泄漏）盘上无落盘命中，按无落盘证据记录（推测出自会话叙述）。时间线：两份报告（09-16/09-17）早于全部表达纪律条款（0.8.2 初版 09-20、0.8.3 完整吸收、0.8.4 角色词扩展 09-21）——报告级 provenance 判 session-artifact（无条款可违）；本记录的对象是方法面作用域缺口本身。

## 根因

1. **作用域缺口（本记录的缺陷对象）**：表达纪律三件套——document-chain.md 条款、document-chain-templates.md 写前提醒、doc_chain.py C12/C13——与 reviewer 文档模式检查全部锚定文档链；会话交付给用户的独立分析报告不在任何书面条款作用域内，也不被任何装置可达。
2. **条款文本缺两个形态规则**：(b) 代号一次定义后裸用作正文持续主语——报告 §1 口径表用白话判定标准定义过 A–X 全部桶，正文仍全程裸用「A 桶/D 桶/G 桶」，读者须回翻定义表或记忆映射；(c) 模式词直搬散文——`status='prepared'` 的 prepared、agent_run 的 Run 是可解析标识符而非发明行话，字面不受「发明行话」条款约束，缺陷是它们充当散文主语而白话词缺席。
3. **无可达装置**：这类产物没有模板、linter 无单文件入口、reviewer 默认不进场——与 ISS-2026-033 证明的「只有条款没有装置会失效」同构。

## 修复

随 candidate 0.8.6（同批入库，发布后回锚 fix_revision）：

1. `document-chain.md` 表达纪律条款增两条形态规则：**代号裸用**（代号只在定义处出现；正文白话主词，以「白话（代号）」或「代号+白话」成对伴随；判据=不回翻定义表能读懂任意一段正文）与**模式词分域**（标识符留代码/SQL/日志语境，散文用业务白话；判据采用户规则原文「正文用『执行』，代码和 SQL 里保留 Run」）；同条款增作用域声明——纪律同等适用于会话交付物，交付前写前自查 + `--file` 机器自查，材料性交付物可指派 reviewer。
2. `roles.md` supervisor 职责增会话交付物写前自查与机器自查一句；`reviewer.md` 文档模式增两个可逐条引用检查项（代号裸用/模式词分域）+ 会话交付物指派评审路径。
3. `doc_chain.py` 新增 **C14 代号裸用**（单大写字母+「桶」，排除定义表行/代码 span/成对括注；「组/档」因普通用语误报面不收，注释留档）与 **--file 单文件模式**（只跑 C12/C13/C14 文本形态检查，跳过 C1-C11 结构检查）；自测 26→38 case。C15 模式词分域机器检查经真语料评估误报面不可控（状态→视觉映射图例类与真缺陷行级不可分），按 brief 但书降级为条款文本+reviewer 管辖，证据留档自测 case 34。

regression_status=not-run：真实链预防效果待下次会话交付物对照。

## 回归检查

- `python3 tools/lab/doc_chain.py --self-test` 38/38 PASS；`python3 -m unittest discover -s tests` 155 OK；`python3 tools/lab/validate.py all` 9 项 PASS；`isolation.py check-diff --base HEAD` blocked=[]
- 真实缺陷语料（supervisor 本机执行，原文输出留存会话）：`--file` 对 AIPPT 报告 C14 命中 4 处（:40/:274/:280/:648）；姊妹报告与 Youc「IP 桶」文件零误报

## 备注

归因铁律一致性：attribution=workflow_policy ⇒ provenance=agentflow——缺陷对象是作用域声明（条款文本与装置布局），不是那两份报告；报告是动机证据（session-artifact 不得单独支撑源码改动，叠加可复核的作用域声明文本与用户拒绝信号后成立）。复发台账立新类 `session-deliverable-jargon-scope` 而非升级 `expression-discipline-jargon`：0.8.4 的吸收在其声明作用域（文档链）内未被本例证伪；产物早于 consolidated_in，记为该类 occurrence 会污染档位推导。用户反馈同时是策略裁决输入：会话交付物应受表达纪律管辖（0.8.6 的作用域声明即该裁决的方法面落点）。

## 变更记录

- 2026-09-22 13:55 · recorded · 用户九组词反馈 + 双报告语料核实 + candidate 0.8.6 修复轮落地，检查全绿
- 2026-09-22 15:15 · fix_revision 回锚 · 0.8.6 发布（用户批准），fix_revision=0.8.6；regression_status 维持 not-run 待首个真实交付物对照
