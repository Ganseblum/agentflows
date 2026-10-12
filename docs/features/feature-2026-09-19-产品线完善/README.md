# `产品线完善` Feature 总览

这份 `README.md` 是当前 Feature 的唯一入口。本批次是「Agentflow 方法自身」的产品线工作——
不是某个目标仓的需求，而是这个插件的方法与产品演进。

推荐阅读顺序：`proposal -> spec -> design -> plan`

## 段落到落点映射

本批次的五段不重复造册——提案 / 规格 / 设计三段由 `docs/product/` 链承载，计划在本目录：

| 链阶段 | 落点 | 说明 |
| --- | --- | --- |
| proposal | [`docs/product/proposal/proposal.md`](../../product/proposal/proposal.md) | 产品提案（含 OQ 开放问题表） |
| spec | [`docs/product/spec/method-spec.md`](../../product/spec/method-spec.md) · [`acceptance-matrix.md`](../../product/spec/acceptance-matrix.md) | 方法规格与验收口径矩阵 |
| design | [`docs/product/design/product-design.md`](../../product/design/product-design.md) | 产品设计 |
| plan | [`plan/PLAN-PRODUCT-001.md`](plan/PLAN-PRODUCT-001.md) · [`plan/PLAN-LOOP-SMOKE-001.md`](plan/PLAN-LOOP-SMOKE-001.md) | 产品完善路线总账 + 第一次 improve 闭环 |
| 门禁勾选 | [`docs/product/README.md`](../../product/README.md) | 各段完成状态与勾选 |

## 元信息

- 批次性质：方法自身演进（无目标业务仓）；版本史见 [`CHANGELOG.md`](../../../CHANGELOG.md)
- 待拍板事项：跨批次单点清单 [`docs/PENDING-DECISIONS.md`](../../PENDING-DECISIONS.md)（产品链修复轮等）
- 最后更新：2026-10-12（本批次由顶层 `docs/plans/` 归位而来）

## 推进进度

> 规则：完成即行首 `☐` 改为 `☑`；不适用改为 `☑` 并写 `(N/A: 原因)`；勾选时附文档相对链接。
> 任务级看板在各计划自身的「任务清单」表内回写——本节只记批次级阶段。

- ☑ 产品提案（`docs/product/proposal/proposal.md`）
- ◐ 方法规格与验收矩阵（`docs/product/spec/`；需求评审门未跑，修复轮待排——见 `docs/PENDING-DECISIONS.md` 第 1 条）
- ◐ 产品设计（`docs/product/design/product-design.md` 成稿；技术方案评审门未跑）
- ◐ 执行计划（`plan/`：PLAN-PRODUCT-001 与 PLAN-LOOP-SMOKE-001 在册；PLAN-LOOP-SMOKE 5/9 任务完成，T10 已失对象）
