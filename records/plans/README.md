# Plans

`plan-architect` writes versioned execution plans here only when the supervisor supplies an
explicit output path. A plan is a **Markdown hybrid** — the frontmatter is the machine-checked
envelope, the body is the human narrative and the progress board. It is an execution contract,
not an authorization to change code.

File: `records/plans/<plan_id>.md` (filename equals `plan_id`), validated against
[`schemas/plan.schema.json`](../../schemas/plan.schema.json) plus the plan checker in
`tools/lab/validate.py`.

## Structure

```text
---
plan_id / plan_version / status (draft|proposed|approved|superseded)
objective / recorded_at / updated_at   (+ superseded_by when superseded)
---

## 进展概览            # 一行进度 + 三视角概览表（业务侧/技术侧/交付效果）+ 我们在哪/下一步/阻塞
## 任务清单            # T01… 任务表：优先级/代码落点/依赖/状态/证据回写 + ### 未决项
## 接口与共享机制       # 契约表 + 异常矩阵 + 发布顺序×回滚点 + 评审门（谁审什么、在哪个任务前）
## 验证命令            # 验收命令与预期
```

## Machine assertions (validated)

- filename = `plan_id`; `status` is the fixed enum; `superseded` requires `superseded_by`;
- task IDs unique; `依赖` references resolve to listed tasks and the graph is acyclic;
- task statuses are the fixed enum `☐ 未开始 / ◐ 进行中 / ☑ 已完成 / ⚠ 阻塞 / — 本期不做`
  (free-text statuses are rejected);
- `### 未决项` rows marked 阻塞 that are not closed **block `status: approved`**;
- the three required sections exist.

## Progress write-back discipline

Progress lives in the plan itself (the board): after a task completes, edit **only** its
状态 and 证据回写 columns — minimal diff; never rewrite completed task rows, never replace
the table with free-text status prose. The session-death resume protocol reads this table to
re-derive each task's state from the workspace.
