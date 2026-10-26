---
bug_id: ISS-2026-038
title: 机器门存在性检查≠形态标准——为过 linter C4 补的契约总表为 cram 形态（ISS-2026-032 升级）；fe §1.2 宽表反模式跨模板漂移
status: verified
regression_status: pass
severity: P2
error_kind: other
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/references/document-chain.md
  - tools/lab/doc_chain.py
recorded_at: 2026-09-21T14:26:00+08:00
source_revision: agentflow@7a235b5 (0.8.3+方法整合候选)
agentflow_version: 0.8.3
class_id: crammed-contract-table-form
occurrence: "2"
updated_at: 2026-10-19T21:45:00+08:00
reviewer: agentflow:reviewer（2026-10-19 独立批量复审）
review_decision: approved
closure_criteria: document-chain.md「存在性检查≠形态标准」条款 + skills/agentflow/templates/feature/design/be/backend.md「字段级契约」节 与 skills/agentflow/templates/feature/design/fe/frontend.md「字段级契约」节（宽表格塞列不合格形态）grep 在场；doc_chain.py --self-test 63/63 退出 0；unittest OK；validate.py all 9 项 PASS 退出 0。
---

## 现象

aiwork 定时任务文档链两处形态缺陷：

1. design/be §1.4.2 字段级契约**总表** cram：IF-A02 响应一格塞 13 个字段带内联注释、IF-A01 请求一格塞 10 个——用户上轮明确要求「字段/类型/必填/说明拆列或代码块+注释」（ISS-2026-032 已把该形态教进模板），但该总表是 supervisor 在 design 阶段为通过 linter C4（检查「存在含『请求字段/响应字段』表头的契约表」）而补写的：**满足存在性检查、违反形态标准**。C4 无法检测 cram。
2. design/fe §1.2 用七列宽表写 L1-L8 核心逻辑——be 模板附录 C 明文「宽表格塞满五列」为不合格形态、规范写法是「#### 小节+加粗标签」，但该形态约束只存在于 **be** 模板，fe/qa 模板无同等条款，fe 产物随之漂移（be 同节是规范形态，两份同链文档风格还不一致）。

## 根因

Goodhart：时间压力下机器检查项（存在性）变成目标本身；linter 的检查粒度（表头 token 匹配）与质量标准（拆列形态）之间有缝，缝隙处产出的产物门全绿但形态不合格。跨模板漂移则是形态规范只挂在单侧模板、无跨文档一致性归属。

## 修复

1. `document-chain.md` 质量判据新增：**通过存在性检查不等于满足形态标准**；索引性总表（契约总表/清单表）只作导航，字段级契约的形态基准=逐字段拆列或代码块+注释；总表 cram 同样计缺陷（linter C4 保持存在性检查，形态归评审与自查条款）。
2. `document-chain-templates.md` design/fe（及 qa，如涉及核心逻辑节）补与 be 同等的形态约束：核心算法与关键逻辑用「#### 小节+加粗标签分段」，宽表格塞列列为不合格形态。
3. ~~`doc_chain.py`：C4 语义注释明确其存在性定位，防后续把形态期望错挂到 C4（不新增形态解析——形态判断归评审人，避免不可靠的机器猜形态）~~——2026-10-19 独立复审核对：git 全历史零命中，该项未落地，回写删除；功能修复由第 1、2 项承载（存在性≠形态条款 + 模板形态约束）。

regression_status=not-run：条款与模板文本变更；形态对照面=下次文档链 design 阶段评审。

## 审查

2026-10-19 独立复审（agentflow:reviewer 子代理，只读）。修复声称核对：第 1、2 项成立（document-chain.md:291-293 存在性≠形态条款、skills/agentflow/templates/feature/design/be/backend.md:60 与 skills/agentflow/templates/feature/design/fe/frontend.md:95 宽表格塞列不合格形态均在盘）；第 3 项（doc_chain.py C4 语义注释）经 git 全历史检索从未落地，回写删除该项声称——功能修复由第 1、2 项承载。回归证据：self-test 63/63、unittest 96 OK、validate all 9×PASS。review_decision：approved。

## 变更记录

- 2026-10-19 21:45 · 独立复审通过 · agentflow:reviewer 批量复审（只读）核对修复声称与回归证据成立，转 verified。
