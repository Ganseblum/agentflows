---
bug_id: ISS-2026-042
title: issue 模板教出记录契约之外的形态——无 frontmatter 的元信息表骨架，照抄产出被 artifacts 拒；templates 清单同时漏列 issue/releases
status: fixed-pending-review
regression_status: pass
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/templates/issue/issue-template.md
  - skills/agentflow/templates/README.md
recorded_at: 2026-10-10T16:05:00+08:00
source_revision: agentflows@af1ba3d + uncommitted 修复工作树（2026-10-10）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-10）
---

## 现象

`skills/agentflow/templates/issue/issue-template.md`（0.9.0 结构改造批新增）的内容是
"元信息表 + 现象与影响 / 证据与复现 / 结论与修复" 形态（youc 风格），与记录契约不一致：

- 没有 YAML frontmatter——校验器第一步即拒（`frontmatter block is missing`）；
- 章节字面量对不上——契约要求 `## 现象` 与 `## 根因` 恒需（`BUG_REQUIRED_HEADINGS`），
  非 `open` 状态需 `## 修复`，`verified` 需 `## 审查`。

而 `issues/README.md`（"编号与看板"节）明文写"起稿用 `skills/agentflow/templates/issue/issue-template.md`"——
照该模板起稿的记录会被 `validate.py artifacts` 拒绝，指路指到了错模板上。

## 根因

两条约束缺口叠加：① 0.9.0 增补模板时引入了 youc 风格的 issue 约定（元信息表），未对照本仓
记录契约（`schemas/bug-record.schema.json` 与固定章节字面量）确认形态——与 ISS-2026-031
（模板教出缺陷形态）同类；② 模板形态没有任何检查覆盖：`validate.py` 的 mock/examples/artifacts
都不巡检 `templates/`，`templates/README.md` 的清单又只列 feature/* 十三件，issue 与 releases
两个真文件既不在清单、也无形态校验（同批意图写明"真文件 + 清单（含 issue 模板、releases
双文件）"，清单完整性也未落地）。

## 修复

1. `skills/agentflow/templates/issue/issue-template.md` 整体重写为契约形态：frontmatter 全字段
   占位（必填十项 + 条件字段按状态自述）+ 固定章节 + 填写说明（说明 frontmatter 不允许注释行、
   条件字段一览、章节字面量规则、关闭条件必须可判定——保留 0.9.0 增补意图）。
2. `skills/agentflow/templates/README.md`：补 `issue/` 与 `releases/` 两个真文件的清单行，并加
   一行指向 `mock/` 的完整样板映射表（骨架抄 templates、填好的完整样板复制 mock——三面分工：
   骨架 / 正反例（`examples/`）/ 完整样板与门夹具（`mock/`））。

## 回归检查

- 填充模拟（一次性整树副本 `/tmp/agentflow-template-check`，只排除 `.git`/缓存/一次性索引）：
  把修复后的骨架按填写说明填充为两条记录——`ISS-2099-991`（open，保留填写说明注释）与
  `ISS-2099-992`（verified，条件字段齐备、删除填写说明）——运行 `python3 tools/lab/validate.py
  artifacts` → `rc=0`、`PASS artifacts`。
- `python3 tools/lab/validate.py all` → 全绿（随本批提交前复跑）。

## 备注

- 同类先例 ISS-2026-031 同为模板文本修复；本例的回归定义为"填充样例在副本上编译通过"（观察级）。
  模板形态无常设自动化检查覆盖——如需门级覆盖（如按骨架生成本例并断言）属门变更，另批申报。
- `mock/` 是 `validate.py mock` 的判别夹具（0.10.0 批已登记"删即砍门"），本次未动；模板清单
  与完整样板的分工以 `templates/README.md` 新增行为准。

## 变更记录

- 2026-10-10 16:05 · recorded + fixed · 模板重写 + 清单补全 + 填充模拟 `PASS artifacts`（副本留档 `/tmp/agentflow-template-check`）
