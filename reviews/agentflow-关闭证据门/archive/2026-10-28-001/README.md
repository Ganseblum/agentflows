# feature-2026-10-28-关闭证据门 — 让「已关闭」必须带可复核证据

> agentflow 目标承接
> 文档档位：完整。UI 轨未启用；埋点 N/A。
> 落点基准：.

## 元信息

- 需求原文：2026-10-28 用户指令「回优化到 agentflow 里面完善一下缺失的这块，建立一个 feature 把问题、出现原因、怎么改写好，然后也修复他」。
- 主实施仓：本仓（agentflows）。相关系统：无。UI 轨：未启用。埋点：N/A。
- 门变更授权：本批修改 `tools/lab/gate/records.py` 与 `tests/test_gate_schema.py` 两个受保护面；用户在 2026-10-28 明确选择「允许改受保护门」。`schemas/bug-record.schema.json` **不改**——核实后确认它已在 0.13.0 强制 verified/rejected 条件。独立评审仍待跑，见 `reviews/README.md`。
- 状态：实施与确定性门已完成；需求评审门与技术方案评审门均未跑（☐ 待独立评审）。唯一权威进度源是 `plan/PLAN-CLOSE-001.md` 的任务看板。

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
☐ 待独立评审（不得由实施者自勾）

### 4. Design [按角色]
☑ design/be 已成文（`design/be/backend.md`）
☑ design/qa 已成文（`design/qa/testing.md`）

### 5. 技术方案评审 [门禁]
☐ 待独立评审；前置 = 需求评审门

### 6. Plan [执行契约]
☑ 已成文并执行（`plan/PLAN-CLOSE-001.md`，status: proposed，执行事实以任务表为准）

### 7. 实施与验证
◐ 代码、负例回归与三道门已完成（证据在 `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md`）；独立复核与宿主重装未做

### 8. 收口
☐ 未收口：两个评审门未跑，版本号与 CHANGELOG 留给集成会话统一处理

## 目标承接表

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 契约文档与门一致 | `proposal/proposal.md` §1.2 | M01，G1-AC-01、G1-AC-02 | T01 | ☑ 已完成 |
| G2 离开 open 必须留下流转记录 | `proposal/proposal.md` §1.2 | M02，G2-AC-01 | T02 | ☑ 已完成 |
| G3 现有状态条件与新增标题检查都有负例钉住 | `proposal/proposal.md` §1.2 | M03，G3-AC-01 至 G3-AC-03 | T03、T04 | ☑ 已完成 |

## 当前步骤

- 下一步：派独立 reviewer 跑需求评审门与技术方案评审门；通过后由集成会话决定版本号与 CHANGELOG。
- 阻塞项：无（评审门未跑不等于阻塞实施，实施事实已按计划看板回写）。

## 模块进度总览

| 模块 | 负责人 | 状态 | 做到哪（已完成） | 还差什么（待办） |
| --- | --- | --- | --- | --- |
| M01 契约文档同步 | BE | ☑ | `docs/issues/README.md` 与模板改为「已由门强制」，写明状态条件矩阵 | 无 |
| M02 流转记录门 | BE | ☑ | 非 open 记录必须有 `## 变更记录` | 无 |
| M03 回归与证据 | QA/BE | ☑ | 5 条负例 + 2 条正例钉住 schema 条件与流转记录；三道门原始输出 | 独立评审 |
