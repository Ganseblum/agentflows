---
bug_id: BUG-20260920-09
title: 文档链只有密度下限没有主线与克制要求——编号体系过载、元话语多、接口平铺、数据无生命周期叙事（用户评：混乱没重点废话多）
status: fixed-pending-review
regression_status: not-run
severity: P2
error_kind: missing-constraint
attribution: role_prompt
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/references/document-chain-templates.md
  - skills/agentflow/references/document-chain.md
recorded_at: 2026-09-20T21:00:00+08:00
source_revision: agentflow@0.8.3
agentflow_version: 0.8.3
---

## 现象

本轮 design/be 单文档同时运行六套编号体系（D1–D16 决策、S1–S12 步骤、V-1~V-12 待核实、AL-1~6 告警、GAP-x/OQ-x、605xx），大量句子是关于文档的元话语（门禁/承接/以谁为准/避免双源）而非关于系统的内容；16 条接口平铺成字典（未按用户做什么组织）；4 张表只有字段注释没有「一行数据的一生」。用户评："感觉很混乱 没重点，废话太多，接口、数据这点还不是不好理解逻辑"。

## 本轮已验证有效的修正（语料来源 ts-workflow-ai + aiwork 成熟样本）

1. 接口按**用户旅程分组**（看任务/管任务/驱动执行/辅助），每组一句场景话——阅读顺序=使用顺序；
2. DDL 前先写**数据生命周期叙事**（一行任务的一生：创建/到点声明/终态/删除四时点 + "task 记录现在、run 记录当时"的理解钥匙）；
3. **速查表降级**（errno+幂等+索引合并为一个"QA 提测速查"子节）、**元话语压成一句话**（标注约定表 7 行→1 行）；
4. ts 语料的「变更摘要版本表」「本期改动边界（权威）做/不做表」被 fe 采纳后结构感明显提升。

## 根因

document-chain.md 质量标准全部是"必须有"的下限（DDL、异常矩阵、testid…），治理反模式清单有「决策编号断档」「单文件巨石」，但**没有主线叙事与噪声上限**的反向要求；模板不含数据生命周期小节与接口旅程分组的骨架。

## 修复

已按上述方向整合入库（同仓提交：agents/reviewer.md、skills/agentflow/references/document-chain.md、skills/agentflow/references/document-chain-templates.md），regression_status=not-run（规则文本变更，无自动化回归面）；生效仍待 improve 治理环收口（evaluator/governor/版本发布）与插件重装。

1. 模板 design/be 加「数据怎么流转」小节（放 DDL 前）与「接口按用户旅程分组」的骨架提示；
2. document-chain.md 质量标准加一条：每个 design 文档必须能说出"读者按什么顺序读、每一章回答什么问题"；编号体系在同一文档内超过三套时必须在文档头给一张编号图例；
3. 治理反模式补两条：同一文档编号体系过载无图例；元话语（关于文档的话）成段出现。
