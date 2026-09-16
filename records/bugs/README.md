# Bug records

Human-readable bug archive, one Markdown file per bug, grouped by the UTC date the bug was
recorded; recurring failure classes additionally get a ledger under `recurrence/`:

```text
records/bugs/
  2026-09-14/
    claude-json-schema-rejected.md
  recurrence/                 # one ledger per class that recurred or was consolidated
    unverified-behavior-claims.md
  archive/                    # closed and retired records keep their date directory
    2026-08-01/
      stale-flaky-test.md
```

Each file is YAML frontmatter (the machine-checked contract,
[`schemas/bug-record.schema.json`](../../schemas/bug-record.schema.json)) plus a Markdown body
for humans. The body uses fixed Chinese section headings — the validator matches these exact
literals: `## 现象`, `## 根因`, and `## 修复` (except for `open` bugs); `## 问题代码` is
recommended whenever a code snippet exists, and `## 审查` is required once a record is
`verified`. Common extra sections: `## 回归检查`, `## 备注`, `## 变更记录`（每次状态流转
append 一行：`YYYY-MM-DD HH:MM · 动作 · 一句话证据`，流转历史不随 `updated_at` 单一时间戳
丢失）.

Frontmatter fields: `bug_id`, `title`, `status` (open / fixed-pending-review / verified /
rejected), `severity` (priority grade: P0 critical / P1 high / P2 medium / P3 low),
`error_kind` (ai-ignored-doc / ai-ignored-code / missing-constraint / hallucination /
logic-error / host-compat / environment / other), `attribution`, `provenance`, `project`,
`files`, `recorded_at`, `updated_at`; `reviewer` + `review_decision` + `regression_status` +
`closure_criteria`（可度量的关闭条件：指标、日志缺席或检查输出） when verified;
`rejection_reason` when rejected; `class_id` + `occurrence` when the record belongs to a
recurrence class; `fix_revision`（修复落地的 commit/PR/版本，跨仓时带仓限定） whenever the
fix has landed.

**引用自包含**：`files` 条目要么是本仓路径（校验器查在盘），要么是仓限定引用
`<repo>@<revision>:<path>`（如 `aiwork-workflow-ai@3930ebb:templates/.../tech-design-backend.md`）；
既不在本仓又没仓限定的裸路径直接 FAIL——它对拿到记录但没有那个仓库的人是悬空引用。

**外部引用必须带片段（校验器强制）**：含仓限定引用的记录，正文必须内嵌决定性片段——
代码用围栏代码块（`## 问题代码`，注释行标注仓限定地址），文档用引用块（`>`，引关键
原文一两句）——且片段旁必须出现该仓限定地址原文（校验器检查）。仓限定是**地址**，内嵌
片段才是**证据**。评审桥的发现优先把 `files` 指向本仓快照
（`records/reviews/<feature>/archive/<轮次>/<doc>.md`，本仓路径直接过在盘检查），原始
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

Archive rule: a `rejected` record must be moved into `records/bugs/archive/<same-date-dir>/`;
`verified` records stay in place as reference.

## Recurrence ledger

`recurrence/<class_id>.md` (contract
[`schemas/recurrence.schema.json`](../../schemas/recurrence.schema.json)): one file per failure
class that recurred or was consolidated; plain single-occurrence bugs get no ledger. `status`
is `unconsolidated`（未归纳升级）or `consolidated`（已归纳升级，`consolidated_in` 写明吸收该类的
Agentflow 版本）。`occurrences` 按时间列出记录 id——版本从各记录自己的 `agentflow_version`
读取，台账不复制。约束（校验器强制）：台账中的每条记录带 `class_id` 与唯一 `occurrence`；
带 `class_id` 的记录必须有对应台账；已归纳类的记录必须带 `agentflow_version`，否则无法判定
它在归纳前还是归纳后。

档位**由事实推导，不靠人工标记**：`python3 tools/lab/validate.py recurrence` 输出
`single`（只有一次）/ `recurred`（改了又出现）/ `escalated`（归纳后再犯——最高档加重标记，
触发 improve 环升级）。

The parent [records index](../README.md) documents conventions and retrospective queries.
