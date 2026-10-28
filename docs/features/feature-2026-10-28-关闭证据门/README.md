# feature-2026-10-28-关闭证据门 — 让「已关闭」必须带可复核证据

> agentflow 目标承接
> 文档档位：完整。UI 轨未启用；埋点 N/A。
> 落点基准：.

## 元信息

- 需求原文：2026-10-28 用户指令「回优化到 agentflow 里面完善一下缺失的这块，建立一个 feature 把问题、出现原因、怎么改写好，然后也修复他」。
- 主实施仓：本仓（agentflows）。相关系统：无。UI 轨：未启用。埋点：N/A。
- 门变更授权：本批修改 `tools/lab/gate/records.py` 与 `tests/test_gate_schema.py` 两个受保护面；用户在 2026-10-28 明确选择「允许改受保护门」。`schemas/bug-record.schema.json` **不改**——核实后确认它已在 0.13.0 强制 verified/rejected 条件。独立评审仍待跑，见 `reviews/README.md`。
- 状态：实施、负例回归、端到端实验、CHANGELOG 0.21.0 与 episode 均已完成；首轮独立评审为 changes_requested，4 项已修复并按 L0 档确定性复核通过，**独立复审待补**——两个评审门因此保持 ☐ 未勾选。唯一权威进度源是 `plan/PLAN-CLOSE-001.md` 的任务看板。

## 段落映射

| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 问题、根因、范围、不做事项与成功判据 |
| spec | `spec/be/backend.md`、`spec/qa/acceptance.md` | 契约现状与验收点 |
| design | `design/be/backend.md`、`design/qa/testing.md` | 校验落点、异常矩阵与验证命令 |
| plan | `plan/PLAN-CLOSE-001.md` | 执行契约与任务证据 |
| testing | `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md` | 三道门的原始输出 |
| reviews | `reviews/README.md` | 独立评审待跑声明 |

## 推进进度

### 1. Proposal [PM]
☑ 主稿已成文（`proposal/proposal.md`），问题、根因、目标 G1–G3 与不做事项齐备

### 2. Spec [按角色]
☑ spec/be 已成文（`spec/be/backend.md`），含 Proposal 反审 checklist 且无未关闭阻塞项
☑ spec/qa 已成文（`spec/qa/acceptance.md`），验收点与判据预先写定

### 3. 需求评审 [门禁]
☐ 首轮独立评审 changes_requested（F1–F4，见 `reviews/agentflow-关闭证据门/review-2026-10-28-001.md`）；4 项已修复并按 L0 复核通过，独立复审待补，门未勾选

### 4. Design [按角色]
☑ design/be 已成文（`design/be/backend.md`）
☑ design/qa 已成文（`design/qa/testing.md`）

### 5. 技术方案评审 [门禁]
☐ 同第 3 项：首轮 findings 已修复、L0 复核通过，独立复审待补；前置 = 需求评审门

### 6. Plan [执行契约]
☑ 已成文并执行（`plan/PLAN-CLOSE-001.md`，status: proposed，执行事实以任务表为准）

### 7. 实施与验证
☑ 代码、4 个回归用例、端到端实验、`validate.py all` 11 项与 `doc_chain.py` 全部通过；证据在 `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md`

### 8. 收口
◐ CHANGELOG 0.21.0、版本号、episode 已完成；独立复审未跑，正式收口待补

## 目标承接表

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 契约文档与门一致 | `proposal/proposal.md` §1.2 | M01，G1-AC-01、G1-AC-02 | T01 | ☑ 已完成 |
| G2 离开 open 必须留下流转记录 | `proposal/proposal.md` §1.2 | M02，G2-AC-01 | T02 | ☑ 已完成 |
| G3 现有状态条件与新增标题检查都有负例钉住 | `proposal/proposal.md` §1.2 | M03，G3-AC-01 至 G3-AC-03 | T03、T04 | ☑ 已完成 |

## 当前步骤

- 下一步：补一次独立复审（首轮 findings 已修复）；通过后把两个评审门勾选并正式收口。
- 阻塞项：独立复审未跑（用户中止第二轮子代理评审），按 L0 登记；不阻塞实施事实。

## 模块进度总览

| 模块 | 负责人 | 状态 | 做到哪（已完成） | 还差什么（待办） |
| --- | --- | --- | --- | --- |
| M01 契约文档同步 | BE | ☑ | `docs/issues/README.md` 与模板改为「已由门强制」，写明状态条件矩阵 | 无 |
| M02 流转记录门 | BE | ☑ | 非 open 记录必须有 `## 变更记录` | 无 |
| M03 回归与证据 | QA/BE | ☑ | 5 条负例 + 2 条正例钉住 schema 条件与流转记录；端到端实验、CHANGELOG/episode 完成 | 独立复审 |
