# feature-2026-10-28-表达面与角色治理 — 让每条规则只有一个权威载体

> agentflow 目标承接
> 文档档位：完整。UI 轨未启用；埋点 N/A。
> 落点基准：.

## 元信息

- 需求原文：2026-10-28 用户在读完 2026-10-28 评测报告后，就其中两条未修问题（B4 表达面膨胀、
  B5 角色深度倒挂）指示「可以，先成立独立批次吧」。评测原文见
  `docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md` §二 B4/B5。
- 主实施仓：本仓（agentflows）。相关系统：无。UI 轨：未启用。埋点：N/A。
- 状态：**立项与范围冻结**。计划看板 `plan/PLAN-GOV-001.md` 的全部任务当前为 `☐ 未开始`
  ——本批只定范围与判据，不改实现。
- 评审档位（如实）：立项期间宿主子代理并发额度不可用，需求评审门与技术方案评审门按
  `contracts.md`「评审能力分级」记 **L0**（主审自审 + 全套确定性门）。能力恢复后须补独立复核。

## 段落映射

| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 两条问题的实测现状、范围、不做事项 |
| spec | `spec/be/backend.md`、`spec/qa/acceptance.md` | 载体归属表、收敛判据、验收点 |
| design | `design/be/backend.md`、`design/qa/testing.md` | 收敛方案、异常矩阵、回滚点 |
| plan | `plan/PLAN-GOV-001.md` | 执行计划（当前全部未开始） |
| testing | `testing/` | 28 例边界测试复跑证据（T05） |
| reviews | `reviews/` | 独立评审落点（当前为空，见评审档位） |

## 推进进度

> 规则：完成即将行首 ☐ 改 ☑；不适用改 ☑ 并写 (N/A: 原因)；评审类门禁只能由独立评审勾选。

### 1. Proposal [PM]
☑ 主稿已成文（`proposal/proposal.md`），含实测现状与不做事项

### 2. Spec [按角色]
☑ spec/be 已成文（`spec/be/backend.md`），含 Proposal 反审 checklist，阻塞项已关闭
☑ spec/qa 已成文（`spec/qa/acceptance.md`），验收点与判据预先写定

### 3. 需求评审 [门禁]
☑ (N/A: 宿主委派不可用，按 L0 档主审自审；补复核条件见元信息)

### 4. Design [按角色]
☑ design/be 已成文（`design/be/backend.md`）
☑ design/qa 已成文（`design/qa/testing.md`）

### 5. 技术方案评审 [门禁]
☑ (N/A: 同第 3 项，L0 档；补复核条件见元信息)

### 6. Plan [执行契约]
☑ 已成文（`plan/PLAN-GOV-001.md`），全部任务未开始——本批只定范围

### 7. 实施与验证
☐ 未开始（本批当前交付物是「范围 + 判据 + 裁决规则」，不是代码改动）

## 目标承接表

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 规则单一权威 | `proposal/proposal.md` §1.2 | M01，G1-AC-01、G1-AC-02 | T01、T02 | ☐ 未开始 |
| G2 同步义务退场 | `proposal/proposal.md` §1.2 | M01，G2-AC-01 | T03 | ☐ 未开始 |
| G3 大文档可导航 | `proposal/proposal.md` §1.2 | M02，G3-AC-01、G3-AC-02 | T04 | ☐ 未开始 |
| G4 FE/BE 悬案裁决 | `proposal/proposal.md` §1.2 | M03，G4-AC-01、G4-AC-02 | T05、T06 | ☐ 未开始 |
| G5 实现角色深度对齐 | `proposal/proposal.md` §1.2 | M04，G5-AC-01、G5-AC-02 | T07、T08 | ☐ 未开始 |

## 当前步骤

本批的当前交付物是**范围冻结**：`spec/be/backend.md` 的载体归属表决定了每条规则留在哪、
收成指针还是删掉；`design/be/backend.md` 给出了为什么不能一刀切的理由（宿主级载体必须自带全文）。
T01–T08 全部 `☐ 未开始`，实施需另一次授权。
