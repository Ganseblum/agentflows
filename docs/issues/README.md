# issues — 缺陷与事项

给人读的缺陷与事项归档：每个缺陷或事项一个 Markdown 文件，命名为
`ISS-<YYYY>-<NNN>-<slug>.md`（slug 用中文短语，无中文译法的技术词保留原文）；复发的失败类另在 `recurrence/` 下配一本台账：

```text
issues/
  ISS-2026-001-claude-json-schema-被拒.md      # 编号逐项递增（缺陷与事项同一编号家族）
  recurrence/                 # 每个复发或已归纳的类一本台账
    unverified-behavior-claims.md
  归档/                        # rejected 记录，保留其日期目录
    2026-08-01/
      ISS-2026-041-陈旧-flaky-测试.md
```

## 编号与看板

- **编号**：`ISS-<YYYY>-<NNN>-<slug>.md`（逐项递增；缺陷与事项同一编号家族；slug 用中文短语）。起稿用
  `skills/agentflow/templates/issue/issue-template.md`。
- **看板**：开放条目平铺于本目录；仅 `rejected` 记录移入 `归档/<日期>/`，其余状态（含
  `verified`）原地保留（见下文归档规则）。
- **升级通道**：小修在本目录内解决；中/大问题经用户确认后升格为 `docs/features/` 批次，
  并在原条目登记去向。
- **状态**：历史缺陷记录已随 2026-10 结构改造迁移执行批次迁入本目录并统一编号
  （编号连续递增；旧编号对照随迁移批次留存在 git 历史）。

每个文件是 YAML frontmatter（机器校验的契约，
[`schemas/bug-record.schema.json`](../../schemas/bug-record.schema.json)）加一段给人读的
Markdown 正文。正文使用固定的中文小节标题——校验器匹配这些精确字面量：`## 现象`、
`## 根因` 和 `## 修复`（`open` 的缺陷除外）；只要有代码片段就建议使用 `## 问题代码`，
记录一旦 `verified` 就必须有 `## 审查`。常见附加小节：`## 前后对比`（修复前后对照，证明
bug 真的解决了）、`## 怎么避免`（防再犯机制）、`## 回归检查`、`## 备注`、
`## 变更记录`（每次状态流转 追加一行：`YYYY-MM-DD HH:MM · 动作 · 一句话证据`，流转历史
不随 `updated_at` 单一时间戳丢失）。

「为什么出现」要在 `## 根因` 里人话点破类别，而不是只贴 frontmatter 标签：`error_kind` 为
`ai-ignored-doc`（文档写明了但没照做）、`ai-ignored-code`（代码写明了但没照做）、
`missing-constraint`（文档/契约压根没说清）、`hallucination`（无中生有）、`logic-error`
（推理错）时，正文都要写出具体是哪条文档没照做、或哪处契约缺失。

Frontmatter 字段：`bug_id`、`title`、`status`（open / fixed-pending-review / verified /
rejected）、`severity`（优先级别：P0 critical / P1 high / P2 medium / P3 low）、
`error_kind`（ai-ignored-doc / ai-ignored-code / missing-constraint / hallucination /
logic-error / host-compat / environment / other）、`attribution`、`provenance`、`project`、
`files`、`recorded_at`、`updated_at`；verified 时还要有 `reviewer` + `review_decision` +
`regression_status` + `closure_criteria`（可度量的关闭条件：指标、日志缺席或检查输出）；
rejected 时要有 `rejection_reason`；记录属于某个再犯类时要带 `class_id` + `occurrence`；
修复已落地则要带 `fix_revision`（修复落地的 commit/PR/版本，跨仓时带仓限定）。

**引用自包含**：`files` 条目要么是本仓路径（校验器查在盘），要么是仓限定引用
`<repo>@<revision>:<path>`（如 `aiwork-workflow-ai@3930ebb:templates/.../tech-design-backend.md`）；
既不在本仓又没仓限定的裸路径直接 FAIL——它对拿到记录但没有那个仓库的人是悬空引用。

**外部引用必须带片段（校验器强制）**：含仓限定引用的记录，正文必须内嵌决定性片段——
代码用围栏代码块（`## 问题代码`，注释行标注仓限定地址），文档用引用块（`>`，引关键
原文一两句）——且片段旁必须出现该仓限定地址原文（校验器检查）。仓限定是**地址**，内嵌
片段才是**证据**。评审桥的发现优先把 `files` 指向本仓快照
（`reviews/<feature>/archive/<轮次>/<doc>.md`，本仓路径直接过在盘检查），原始
仓限定地址写进正文——整份 copy 由评审桥的 `archive/` 承担，记录自身只嵌片段。

**正文引用规则（校验器强制，bug 记录 / 评审记录 / 类台账同适用）**：正文**散文**里出现
的文档/代码路径是记录自己的主张，必须在盘（本仓或记录旁的相对路径）或为仓限定引用；
围栏代码块与内联代码（`` ` `` 包裹）是**引文**——逐字引用的证据，含历史路径——不扫；
个人绝对路径（`/Users/...`、`~/...`）一律禁止，记录是可移植证据；URL 无法校验，至多作
补充信息，**不得作为证据**（要证据就引快照/内嵌片段）。

## Provenance — 是不是 Agentflow 产生的问题

`provenance`（必填）回答一个必须先答的问题：**出问题的那份产物/行为归谁**——它决定这条记录
能不能作为 Agentflow 的改进证据。

| 取值 | 含义 |
| --- | --- |
| `agentflow` | Agentflow 自身表面：条款、角色提示词、门、评测、简报纪律、`tools/lab/` 工具 |
| `session-artifact` | 会话内即兴产出、无 Agentflow 条款覆盖（agent 自己写的计划、分析、决策、代码） |
| `user-input` | 用户提供的指令、计划、分析 |
| `external` | 业务仓库既有代码、宿主、工具、环境 |
| `undetermined` | 尚未查清——必须在正文写明缺的是什么证据 |

两条硬规则：

1. **归因铁律（schema 强制）**：`attribution` 为 `workflow_policy` 或 `role_prompt` 时，
   `provenance` 必须是 `agentflow`——不能把责任归给 Agentflow 的规则，同时又承认问题产物
   不来自 Agentflow。
2. **改进环只看 `agentflow`**（`skills/improve/SKILL.md`）：`session-artifact` / `user-input` /
   `external` 是上下文而非证据；`undetermined` 必须先解决归属才能进入聚类。

判定要有依据（`agents/bug-investigator.md`）：归 `agentflow` 时引用覆盖它的条款
`path:line`；归 `session-artifact` 时写明"无条款覆盖"以及为什么这不属于方法应管的范围。
`python3 tools/lab/validate.py report` 第 7 列输出该字段，可直接
`awk -F'\t' '$7=="agentflow"'` 过滤。

归档规则：`rejected` 记录必须移入 `issues/归档/<same-date-dir>/`；`verified` 记录原地保留
作为参考。

## 再犯台账

`recurrence/<class_id>.md`（契约
[`schemas/recurrence.schema.json`](../../schemas/recurrence.schema.json)）：每个复发或已归纳的
失败类一个文件；单次发生的普通 bug 不建台账。`status` 为 `unconsolidated`（未归纳升级）
或 `consolidated`（已归纳升级，`consolidated_in` 写明吸收该类的 Agentflow 版本）。
`occurrences` 按时间列出记录 id——版本从各记录自己的 `agentflow_version` 读取，台账不复制。
约束（校验器强制）：台账中的每条记录带 `class_id` 与唯一 `occurrence`；带 `class_id` 的记录
必须有对应台账；已归纳类的记录必须带 `agentflow_version`，否则无法判定它在归纳前还是归纳后。

档位**由事实推导，不靠人工标记**：`python3 tools/lab/validate.py recurrence` 输出
`single`（只有一次）/ `recurred`（改了又出现）/ `escalated`（归纳后再犯——最高档加重标记，
触发 improve 环升级）。
