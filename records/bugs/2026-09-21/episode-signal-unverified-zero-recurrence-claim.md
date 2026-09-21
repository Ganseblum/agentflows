---
bug_id: BUG-20260921-05
title: episode 信号缺证即断言——「方法条款目标缺陷零复发」前提假（修复未安装）且方法假（评审未报≠零复发），毒化改进环自身输入
status: fixed-pending-review
regression_status: not-run
severity: P1
error_kind: ai-ignored-doc
attribution: role_prompt
provenance: agentflow
project: agentflow
files:
  - records/episodes/2026-09-21/EP-20260921-001.json
  - skills/agentflow/references/document-chain.md
recorded_at: 2026-09-21T14:40:00+08:00
source_revision: agentflow@7a235b5 (0.8.3+方法整合候选)
agentflow_version: 0.8.3
---

## 现象

EP-20260921-001 记录 method_effect_signal：「0.8.3 方法条款（05~09）首次真实运行……目标缺陷类零复发」。两层失实（feedback-analyst 独立复核确认）：

1. **前提假**：运行时（aiwork-automation-doc-chain-002）装的是 0.8.3 已安装快照，05/07 条款与 reviewer 表达纪律检查项**均不在场**（独立核实：`~/.zcode/cli/plugins/cache/agentflow-local/agentflow/0.8.3/skills/agentflow/references/document-chain.md` 无「契约真源/stated once」条款、`agents/reviewer.md` 无表达纪律检查项——05~09 修复只入 source，待治理环发布+重装）。且会话未按 AGENTS.md 要求在 dogfood 前跑 `validate.py installed` 留存输出。
2. **方法假**：以「评审未报 finding」推断「零复发」——缺证即断言。实际亲读发现三类复发（BUG-20260921-02/03/04）。

已修订：episode 该信号已就地标注证伪（2026-09-21 修订前缀），本记录为其立账。

## 根因

1. episode schema 的 signals 无 verification-status 字段，正面信号与已验证信号同形存放，写作时无从强制区分「观察」与「已验证」。
2. supervisor 未跑 `validate.py installed` 即对方法效果下断言——违反本仓 AGENTS.md「Before any dogfood run 跑 installed 检查」的既有规则，属既有台账类 unverified-behavior-claims（consolidated 0.3.4）的复发面。

## 修复

1. `document-chain.md`（episode 捕获指引段）加一句：signals 中的方法效果类信号必须区分「观察（未验证）」与「已验证（附检查命令与输出）」；涉及「运行时装了什么」的信号以 `validate.py installed` 输出为准。
2. 本 episode 已就地修订；台账类 unverified-behavior-claims 按其升级条件处理（再犯应触发评测用例——本记录即再犯凭证）。

regression_status=not-run：指引文本变更；对照面=下次 episode 的 signals 是否带验证状态。
