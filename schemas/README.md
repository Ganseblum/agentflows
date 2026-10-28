# Agentflow 契约

本目录存放 Agentflow 工作流的跨宿主记录契约：每份 JSON Schema 描述一类 Markdown 记录
（或 JSON episode）的 frontmatter 字段与跨字段不变量。校验器（`tools/lab/validate.py schemas`
与 `validate.py artifacts`）按这些契约编译记录，非法记录本目录之外无处可落地。

改进环专用契约在 [`skills/improve/references/`](../skills/improve/references/) 下，因为 Improve
Skill 直接链接到它们；校验器加载两处位置，并检查单份 JSON Schema 无法表达的跨文档不变量。
本目录与那两处都在 [`protected-paths.txt`](../protected-paths.txt) 内——放宽一份记录被据以度量
的 schema，就是编辑自己的门，因此契约变更属人工评审的门变更。

## 本目录的契约

| 文件 | 描述什么记录 | 落点 |
| --- | --- | --- |
| [`bug-record.schema.json`](bug-record.schema.json) | 缺陷记录 frontmatter：`bug_id` / `status` / `severity` / `error_kind` / `attribution` / `provenance`（字符串枚举，判定该记录是否 Agentflow 证据）与状态相关的必填项（`verified` 需 `reviewer` + `review_decision=approved` + `regression_status=pass` + `closure_criteria`）。 | `docs/issues/ISS-<YYYY-MM-DD>-<slug>.md`（平铺）；被拒记录移入 `docs/issues/归档/<YYYY-MM-DD>/` |
| [`recurrence.schema.json`](recurrence.schema.json) | 再犯类台账 frontmatter：`class_id` / `status` / `first_record` / `occurrences`（只存 bug_id，版本随记录走，单一真源）；`consolidated` 时需 `consolidated_in`。 | `docs/issues/recurrence/<class_id>.md` |
| [`plan.schema.json`](plan.schema.json) | 执行计划 frontmatter 的机器校验信封（`plan_id` / `plan_version` / `status` / `objective`）；正文的人类叙述与任务表断言由校验器另行强制。 | `docs/features/<批次>/plan/<plan_id>.md` |
| [`review.schema.json`](review.schema.json) | 评审记录 frontmatter：`review_id` / 目标项目与 feature / `source_revision` / `reviewed_docs`（归档快照路径） / `decision` / `findings`（指向现存 `docs/issues/` 记录）。 | `reviews/<project>-<feature-slug>/review-<YYYY-MM-DD>-<NNN>.md` |
| [`test-plan.schema.json`](test-plan.schema.json) | 测试计划 frontmatter：用例目录（`case_count` 与用例注册表对账）、`test_version`（原地修订即递增）、凭据按注入方式声明而非取值。 | `docs/features/<批次>/testing/<project>-<feature-slug>/plan-<YYYY-MM-DD>-<NNN>.md` |
| [`test-run.schema.json`](test-run.schema.json) | 测试执行记录 frontmatter：一轮执行对某钉定的计划版本，`summary_*` 计数与结果表对账，`decision` 与计数一致，`findings` / `flow_findings` 指向现存记录。 | `docs/features/<批次>/testing/<project>-<feature-slug>/run-<YYYY-MM-DD>-<NNN>.md` |

## 已裁撤：不再有评测夹具契约

本目录曾另有评测装置契约（公开用例夹具、runner、宿主 adapter 与 policy 引擎），随 2026-10-12
评测装置整线裁撤删除：`evals/`、`eval_runner.py` / `host_adapter.py` / `policy.py`、
`adapter-protocol.md`，以及 `eval-case.schema.json` 等三个 schema。留存的可复用设计知识与恢复
清单见 `docs/design-decisions.md` §3——恢复仪器化时按该清单重建，
包括重新引入的用例/对照契约。在此之前的改进环方法级改动一律 `measurement: none` 口径。

这些契约描述证据与执行计划。计划本身不构成修改代码或发布插件的授权。
