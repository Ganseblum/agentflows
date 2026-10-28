# Q-04 外部记录迁出分析

> 状态：待用户拍板。关联：`docs/PENDING-DECISIONS.md` 第 8 条①；`proposal/prd.md` Q-04。

## 一、现状

- `docs/issues/` 下有 16 条外部来源记录：ISS-2026-09-19-office计划缺异常矩阵 至 ISS-2026-09-19-office计划事件清理回放缺口。
- 这些记录来自另一个项目（office 计划相关），不是 agentflows 自身的缺陷。
- 当前在 `docs/issues/` 下，标注了来源。

**定位更正（2026-10-19 核查）**：这 16 条不是"误放在本仓的外部记录"，而是本仓**对外评审桥**的
正常产出。以 ISS-2026-09-19-office计划缺异常矩阵 为例：`provenance: external`、`attribution: product_code`、
`project: infinite-canvas`、`files` 指向 `reviews/infinite-canvas-office-agent-plan/archive/2026-09-19-001/`
下的评审快照——它们是 `reviews/infinite-canvas-office-agent-plan/review-2026-09-19-001.md` 的
findings。`reviews/README.md` 的工作流第 3 步写明「发现的问题一条一条写进 issues/」，第 4 步要求
`validate.py artifacts` 全绿才算收口。也就是说：**留在本仓是契约规定的默认，不是没收拾干净。**

## 二、问题

这些外部记录放在 agentflows 仓内，但内容属于另一个项目。是否迁出到外部项目？

## 三、选项

### 选项 A：迁出到外部项目

把 ISS-2026-09-19-office计划缺异常矩阵 至 025 迁移到外部项目的记录系统。

**收益**：agentflows 仓只留自己的记录；记录归位到正确的项目。
**风险**：不只是"更新引用"这么轻。迁出会同时打断三处在跑的机制——① 每条记录的 `files` 必须在盘
（`records.py` 的路径校验），迁走后要么变悬空、要么改成仓限定引用并内嵌片段；② 评审记录的
`findings` → `bug_id` 交叉核对（`workspace.py` 在扫完记录后校验），迁走后 review 指向的编号全部失效；
③ `validate.py report` 按 `project` 聚合的再犯类统计会丢掉这一整个项目。此外外部项目未必有对应的
记录系统与校验器，迁过去就失去了现在这套机器契约。

### 选项 B：留在 agentflows

不迁移，在 `docs/issues/` 下保留，标注来源。

**收益**：无需操作；记录可追溯。
**风险**：agentflows 仓内有外部记录；可能引起混淆。

### 选项 C：删除

删除这些外部记录。

**收益**：agentflows 仓只留自己的记录。
**风险**：丢失历史记录；无法追溯。

## 四、建议

- **推荐 B（留在本仓）**：这是契约规定的默认落点，不是权宜。要做的是把「来源」写得更好——
  每条记录已经有 `provenance: external` 与 `project`，无需额外标注。
- A 只在同时满足三个条件时才值得做：外部项目有自己的记录系统、愿意承接这批编号、且本仓这边
  把 review 的 `findings` 改成仓限定引用并内嵌片段。代价是把一套机器契约换成口头约定。
- 不建议 C（删除）：`reviews/README.md` 的定位就是"记录是证据"，删掉会连评审桥的可追溯性一起删掉。
- 本批 spec §3 已收口「本批不迁移，只在台账中标注来源」，所以任何迁出动作都属于下一批，且要先
  改契约——不要在本批顺手做。

## 五、决策点

| 决策点 | 选项 | 影响 |
| --- | --- | --- |
| 是否迁出 | 迁出 / 留下 / 删除 | 记录归属、仓内整洁度 |
| 如果迁出 | 目标位置 | 迁移方式、引用更新 |
