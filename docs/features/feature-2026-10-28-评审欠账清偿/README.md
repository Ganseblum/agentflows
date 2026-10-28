# feature-2026-10-28-评审欠账清偿 — 让「补门」从承诺变成可清点的欠账

> agentflow 目标承接
> 文档档位：完整。UI 轨未启用；埋点 N/A（理由：本批只改记录 frontmatter、评审记录与文档索引，
> 不新增用户可见行为与埋点事件）。
> 落点基准：.

## 元信息

- 需求原文：2026-10-28 用户对本仓 2026-10-28 全面评测报告的后续指示「看看怎么修复，单独立项看看」。
  评测报告见 `docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md` §二 B2；两个前序批次各自的 L0 声明见
  `docs/features/feature-2026-10-28-评测整改批/README.md` 与
  `docs/features/feature-2026-10-28-表达面与角色治理/README.md` 的元信息节。
- 主实施仓：本仓（agentflows）。相关系统：无。UI 轨：未启用。埋点：N/A。
- 状态：**立项与范围冻结**。计划看板 `plan/PLAN-DEBT-001.md` 的全部任务当前为 `☐ 未开始`
  ——本批只定范围与判据，不改实现。
- 评审档位（如实）：**由 T01 的两组委派探测决定，立项时不预设**。2026-10-28 实测向 `reviewer`
  派发一次探测成功返回——这只证明「至少 1 个只读角色可派」，不足以区分 L1（只能派 1 个）与
  L2（能派 2 个）。按 `contracts.md:34-38`，档位由派发调用是否返回这一二值事实决定，
  不得按成本偏好选档。T01 的记录落批次 `testing/`。

## 段落映射

| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 欠账的三类来源、实测数量、范围与不做事项 |
| spec | `spec/be/backend.md`、`spec/qa/acceptance.md` | 欠账清单的字段级口径、清偿判据、验收点 |
| design | `design/be/backend.md`、`design/qa/testing.md` | 判据落点、异常矩阵、回滚点 |
| plan | `plan/PLAN-DEBT-001.md` | 执行计划（当前全部未开始） |
| testing | `testing/` | 清偿轮次的原始门输出 |
| reviews | `reviews/` | 独立评审记录落点 |

## 推进进度

> 规则：完成即将行首 ☐ 改 ☑；不适用改 ☑ 并写 (N/A: 原因)；评审类门禁只能由独立评审勾选。

### 1. Proposal [PM]
☑ 主稿已成文（`proposal/proposal.md`），含三类欠账的实测数量与不做事项

### 2. Spec [按角色]
☑ spec/be 已成文（`spec/be/backend.md`），含 Proposal 反审 checklist，阻塞项已关闭
☑ spec/qa 已成文（`spec/qa/acceptance.md`），验收点与判据预先写定

### 3. 需求评审 [门禁]
☐ 待独立评审（档位由 T01 两组探测决定；记录落 `reviews/`）

### 4. Design [按角色]
☑ design/be 已成文（`design/be/backend.md`）
☑ design/qa 已成文（`design/qa/testing.md`）

### 5. 技术方案评审 [门禁]
☐ 待独立评审（前置＝需求评审门）

### 6. Plan [执行契约]
☑ 已成文（`plan/PLAN-DEBT-001.md`），全部任务未开始——本批只定范围

### 7. 实施与验证
☐ 未开始（本批当前交付物是「范围 + 判据」，不是代码改动）

## 目标承接表

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 两个批次的 L0 欠账被清偿 | `proposal/proposal.md` §1.2 | M-A，G1-AC-01、G1-AC-02 | T01、T02、T03，T08 | ☐ 未开始 |
| G2 评审欠账可机器清点 | `proposal/proposal.md` §1.2 | M-B，G2-AC-01、G2-AC-02 | T04、T08 | ☐ 未开始 |
| G3 五条待评审缺陷逐条清偿 | `proposal/proposal.md` §1.2 | M-C，G3-AC-01、G3-AC-02 | T05、T06、T07、T08 | ☐ 未开始 |

## 当前步骤

本批的当前交付物是**范围冻结**：`spec/be/backend.md` §1 给出欠账清单的字段级口径（哪些算欠账、
每条欠账的清偿条件是什么），`design/be/backend.md` 给出为什么清点的真源必须是仓内派生事实
而不是手工清单（自指判据会 0 对 0 判绿），以及为什么 `review_tier` 校验必须同时覆盖
评审记录与批次文档两层。T01–T08 全部 `☐ 未开始`，实施需另一次授权。

两个入口门（需求评审、技术方案评审）当前为 `☐`。**本轮已按独立评审跑过一次需求评审门**，
结论 `changes_requested`（12 条 P0/P1/P2，全部已按证据修正本批文档），详见
`reviews/review-2026-10-28-001.md`；修正后的文档需**再评审一轮**才可关闭该门。
