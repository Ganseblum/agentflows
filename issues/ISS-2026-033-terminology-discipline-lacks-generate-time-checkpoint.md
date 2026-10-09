---
bug_id: ISS-2026-033
title: 表达纪律只有条款没有写前装置——「缺省/挂点/软删/fail-open」等 8 处黑话由用户逐个抓出
status: fixed-pending-review
regression_status: not-run
severity: P3
error_kind: missing-constraint
attribution: role_prompt
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/references/document-chain.md
recorded_at: 2026-09-20T21:00:00+08:00
source_revision: agentflow@0.8.3
agentflow_version: 0.8.3
---

## 现象

表达纪律条款自 0.8.2 已存在（document-chain.md："no invented jargon…Fix priority is 换 > 释 > 删"），但本轮生成时未对照执行，用户逐个抓出 8 处：缺省（=默认值）、挂点（=接入点）、软删（=软删除）、fail-open（=宁可放行不阻塞）、以及 single-flight 无白话注释。全部按「换」修复，验证了条款的正确性；问题在**执行时机**——纪律靠"写完被人抓"而非"写时对照"。

## 根因

条款存在但缺少三个落地点之一即可提前拦截的装置：

1. 模板占位符旁无一行黑话自查提醒（写前对照）；
2. reviewer 文档模式的检查项不含表达纪律（评审兜底缺失——独立评审跑了两遍都没抓「缺省」，用户一眼抓到）；
3. doc_chain.py 无术语词典告警（机器兜底缺失；词典类检查是 C 级下限检查的合理扩展，但需防止词典膨胀，候选实现需评估）。

## 修复

已按上述方向整合入库（同仓提交：agents/reviewer.md、skills/agentflow/references/document-chain.md、skills/agentflow/references/document-chain-templates.md），regression_status=not-run（规则文本变更，无自动化回归面）；生效仍待 improve 治理环收口（evaluator/governor/版本发布）与插件重装。

最小改动：reviewer 文档模式 general pass 加表达纪律检查项（引用即报）；模板 proposal/spec/design 三处占位说明区各加一行「术语：换>释>删，作者能解读者要猜的词即缺陷」。doc_chain.py 词典告警作为候选单独评估（防词典膨胀）。
