---
bug_id: ISS-<YYYY>-<NNN>
title: <一句话标题>
status: open
severity: P2
error_kind: <ai-ignored-doc | ai-ignored-code | missing-constraint | hallucination | logic-error | host-compat | environment | other>
attribution: <workflow_policy | role_prompt | context | tool_or_host | model_limit | product_code | evaluation | unknown>
provenance: <agentflow | session-artifact | user-input | external | undetermined>
project: <项目 slug>
files:
  - <在盘路径，或 仓库@revision:路径>
recorded_at: <ISO 8601 UTC，如 2026-01-01T00:00:00Z>
affected_slices:
  - <受影响切片；无则删整段>
fix_revision: <修复落地后回填 commit / PR / 版本；否则删行>
class_id: <再犯类 id；非再犯删行>
occurrence: "<再犯序号，如 1；非再犯删行>"
reviewer: <仅 verified：评审人>
review_decision: <仅 verified：approved | changes_requested | blocked>
regression_status: <fixed-pending-review 与 verified 需要：pass | fail | not-run>
closure_criteria: <仅 verified、必须可判定：命名指标 / 日志消失 / 命令输出>
rejection_reason: <仅 rejected：拒绝原因>
updated_at: <每次改动刷新；不填则删行>
source_revision: <发现时的源 revision；按需删行>
agentflow_version: <记录时的插件版本；按需删行>
---

<!-- 填写说明（复制本文件到 `issues/ISS-<YYYY>-<NNN>-<slug>.md` 后：文件名与 `bug_id` 一致；替换全部占位符；不适用或未满足条件的行整行删除；完成后删掉本注释，并运行 `python3 tools/lab/validate.py artifacts` 校验）：

- 正文章节标题是校验器按整行精确匹配的固定字面量：`## 现象` 与 `## 根因` 恒需；非 `open` 状态需 `## 修复`；`verified` 还需 `## 审查`；有决定性代码或片段时使用 `## 问题代码`。标题文字不得改名。
- frontmatter 条件字段一览：`fixed-pending-review` 与 `verified` 需要 `regression_status`；`verified` 另需 `reviewer`、`review_decision: approved` 与可判定的 `closure_criteria`；`rejected` 需要 `rejection_reason`；再犯类带 `class_id` 与 `occurrence`。
- `provenance: undetermined` 时正文必须写明缺的是什么证据；`files` 的外部引用要带仓限定地址，并在正文内嵌决定性片段或引用原句。
- 各状态的完整可运行样板（open / fixed-pending-review / verified / rejected / 再犯两类）见 `mock/` 目录的映射表；状态机为 `open → fixed-pending-review → verified`，或 `rejected` 移入 `归档/`。
-->

## 现象

<发生了什么、影响谁、如何观测到；复现步骤或原始输出>

## 根因

<根因；归因要有依据——引用覆盖它的条款（`path:line`），或写明无条款覆盖及理由>

## 修复

<修复内容与验证方式；未修复时写当前方案与残余风险>

## 问题代码

```text
<决定性代码或片段；其旁写明仓限定地址原文>
```

## 审查

<评审人、决定、回归检查与 `closure_criteria` 逐条闭合结果>

## 变更记录

- <YYYY-MM-DD HH:MM> · <动作> · <一句话证据>
