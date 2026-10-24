---
bug_id: ISS-<YYYY>-<NNN>
title: <一句话标题>
status: open
disposition: <仅 open 且未被批次承接表承接时填写：deferred | not-doing；否则删行>
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
fix_revision: <修复已落地时必填：commit / PR / 版本；否则删行>
class_id: <再犯类 id；非再犯删行>
occurrence: "<再犯序号，如 1；非再犯删行>"
reviewer: <仅 verified：评审人>
review_decision: <仅 verified：approved | changes_requested | blocked>
regression_status: <fixed-pending-review 与 verified 需要：pass | fail | not-run>
closure_criteria: <仅 verified、必须可判定：命名指标 / 日志消失 / 命令输出>
rejection_reason: <仅 rejected：拒绝原因>
updated_at: <每次改动刷新；不填则删行>
source_revision: <外部产物或代码发现的源 revision；不适用时删行>
agentflow_version: <归因到 Agentflow 或需判断复发版本时填写；不适用时删行>
---

<!-- 填写说明（复制本文件到 `issues/ISS-<YYYY>-<NNN>-<slug>.md` 后：文件名与 `bug_id` 一致（slug 用中文短语，无中文译法的技术词保留原文，如 `ISS-2026-001-claude-json-schema-被拒.md`）；替换全部占位符；不适用或未满足条件的行整行删除；完成后删掉本注释，并运行 `python3 tools/lab/validate.py artifacts` 校验）：

- 固定标题不得改名。`## 现象`、`## 根因`、`## 修复方案` 与 `## 变更记录` 都要填写；open 阶段先记录待审核建议，并标明审核状态，证据不足时写清缺什么。`## 修复` 只记实际改动；open 可省略。当前校验器对所有非 open 状态都要求 `## 修复`，因此 rejected 记录在该节写明“未实施”并指向拒绝原因。`verified` 还需 `## 审查`。
- `## 回归检查` 在修复已落地时填写命令、结果和原始证据；未运行时说明原因。`## 问题代码` 仅在有决定性代码片段时保留；`## 前后对比` 在修复前后有可复核证据时保留；其余情况删除整节，不留空标题。
- `## 怎么避免` 要区分候选建议与已落实措施：open 写建议状态；修复后写实际增加的规则、检查或其它控制及证据。若没有可行措施，说明原因，不把愿望写成已落实机制。
- 「为什么出现」要在 `## 根因` 里人话点破属于哪一类：`error_kind: ai-ignored-doc` = 文档写明了但没照做；`ai-ignored-code` = 代码写明了但没照做；`missing-constraint` = 文档/契约压根没说清（缺约束）；`hallucination` = 无中生有；`logic-error` = 推理/逻辑错。归因要有依据，不能只贴一个标签。
- frontmatter 条件字段一览：`fixed-pending-review` 与 `verified` 需要 `regression_status`；`verified` 另需 `reviewer`、`review_decision: approved` 与可判定的 `closure_criteria`；`rejected` 需要 `rejection_reason`；修复已落地需 `fix_revision`；再犯类带 `class_id` 与 `occurrence`。open 记录要么被带 `agentflow 目标承接` 标记的批次承接表引用，要么填写 `disposition: deferred` / `not-doing`；`disposition` 只说明归属，不是状态，也不代表已修复。
- `provenance: undetermined` 时正文必须写明缺的是什么证据；`files` 的外部引用要带仓限定地址，并在正文内嵌决定性片段或引用原句。
- 状态机为 `open → fixed-pending-review → verified`，或 `rejected` 移入 `归档/`；各状态的字段要求见上方条件字段一览，可运行的填写范例见 `examples/issues/`（正例）与 `examples/invalid/`（反例）。
-->

## 现象

<预期行为：……；实际行为：……；影响对象与范围：……；复现步骤：……；观察证据或原始输出：……>

## 根因

<根因；归因要有依据——引用覆盖它的条款（`path:line`），或写明无条款覆盖及理由>

## 修复方案

<发现阶段提出的候选做法、依据、主要风险/依赖、备选取舍，以及防止再犯的候选措施；写明方案状态（待审核 / 已采纳 / 已调整 / 暂缓 / 不做）与审核依据。方案应在发现时提出，审核后再实施；无法可靠建议时写明缺少的证据或待人决定>

## 修复

<只记录已实际实施的改动及其 revision。若 status 为 rejected，写“未实施”并指向 rejection_reason。不要把候选方案写成已完成的修复>

## 回归检查

<修复落地后写精确命令、观察结果与可复核证据；未运行时明确写未运行及原因>

## 前后对比

<修复前后的对照，证明 bug 真的解决了：改前行为/输出 vs 改后行为/输出，或 `git diff` 关键片段，
或最小实验的前后退出码/输出原文。没有可复现前后对照的，如实写「未做前后对照」并说明缺什么，
不得用「已修复」字样代替证据>

## 问题代码

```text
<决定性代码或片段；其旁写明仓限定地址原文>
```

## 怎么避免

<open 阶段写防复发候选措施及状态；修复后写实际落地的规则、检查、模板或其它控制及证据。若没有可行机制，如实写原因>

## 审查

<verified 时填写独立评审证据，以及 `closure_criteria` 逐条闭合结果；评审人、决定、回归状态与关闭条件以 frontmatter 为准>

## 变更记录

- <YYYY-MM-DD HH:MM ±HH:MM> · <动作> · <一句话证据>
