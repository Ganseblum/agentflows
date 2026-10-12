---
bug_id: ISS-2026-035
title: 文档链时效性引用无收口装置——上游「待产出」在后置文档落盘后失实，链路无收口通读轮、linter 不查语义过时
status: fixed-pending-review
regression_status: not-run
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/references/document-chain.md
  - tools/lab/doc_chain.py
recorded_at: 2026-09-21T14:20:00+08:00
source_revision: agentflow@7a235b5 (0.8.3+方法整合候选)
agentflow_version: 0.8.3
---

## 现象

aiwork 定时任务文档链（aiwork-automation-doc-chain-002）交付后用户追问 design 质量，supervisor 亲读发现 `design/be/tech-design-backend.md` 尾部三处「待产出」失实：

> :981「测试设计见 `design/qa/`（待产出）」、:1001「QA 测试设计：`design/qa/test-design.md`（待产出）」、:1002「实施计划：……（待产出）」

而 design/qa 与三份 plan 在评审收口时全部已存在。同型错误在 spec 轮已被独立评审抓到过（spec/fe FE-1「尚未产出」），当时只做了点修复（改 spec/fe 两行），未升级为链路级检查——同一缺陷在链路另一份文档的尾部原样复发。

## 根因

1. **流水线生产无收口时点**：文档链按 spec→design→plan 顺序由不同 agent 产出，上游文档的「前向引用」（关联文档节）在落笔时如实、后置文档落盘后必然过时；没有任何一方被指派「最后一份文档落盘后回读全链清时效性引用」。
2. **点修复不升装置**：FE-1 的修复停留在一处两行，没有变成检查项。
3. **机器门盲区**：`doc_chain.py` 检查链接目标存在性（C 系列）与结构，不检查「文档声称 X 未产出而 X 已存在」的语义矛盾。

## 修复

1. `document-chain.md` 新增「链路收口检查」条款：链路在最后一份文档落盘后、宣告完成前，必须跑一遍固定收口检查——时效性引用（待产出/尚未产出/待补充 vs 实际文件）、流程角色词、会话材料落仓、关联文档解析；可机器化的部分由 linter 承接。
2. `doc_chain.py` 新增时效性引用检查：行内含「待产出/尚未产出/待补充/待生成」且同时含指向**已存在**目标的 markdown 链接 → finding；判别性自测加正反例。

regression_status=not-run：linter 新检查以自测 case 固定；真实链预防效果待下次文档链对照。
