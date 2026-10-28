---
plan_id: PLAN-DEBT-001
plan_version: 1.0.0
status: proposed
objective: 清偿两个 2026-10-28 批次的 L0 评审欠账与五条待评审缺陷，并让评审欠账可被一条命令清点、伪降级可被机器判红
recorded_at: 2026-10-28T14:30:00+08:00
---

# PLAN-DEBT-001 — 评审欠账清偿执行计划

## 进展概览

- 总任务 8 项：☐ 8 项未开始（T01–T08）。本批当前只交付范围与判据，不含实施。
- 阻塞：无。
- 权威状态：本表即唯一任务状态源。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 探测委派能力（向 `reviewer` 派一次最小任务），把原始返回与欠账清单初值写进批次证据与 `docs/releases/todo.md`；能力不可用则本批整体转 ⚠ | P0 | `docs/releases/todo.md`、`docs/features/feature-2026-10-28-评审欠账清偿/testing/` | — | ☐ 未开始 | — |
| T02 | 对评测整改批（0.20.0，被评审 revision `26988a4`）派独立评审，记录落批次 `reviews/`，含 `review_tier: L1` 与 `reviewed_revision` | P0 | `docs/features/feature-2026-10-28-评测整改批/reviews/` | T01 | ☐ 未开始 | — |
| T03 | 对表达面与角色治理批（范围冻结批，被评审 revision `26988a4`）派独立评审，记录落批次 `reviews/` | P0 | `docs/features/feature-2026-10-28-表达面与角色治理/reviews/` | T01 | ☐ 未开始 | — |
| T04 | 给 `review_tier` 加记录侧校验：schema 增两字段 + 一条 `allOf`，校验器判伪降级；**属受保护面门变更，须逐项授权后方可开工** | P0 | `schemas/review.schema.json`、`tools/lab/gate/records.py`、`tests/test_gate_records.py` | — | ☐ 未开始 | — |
| T05 | 清偿 ISS-2026-057 与 ISS-2026-058：独立复核修复是否成立，成立则补 `fix_revision` + `reviewer` + `review_decision` 转 `verified`，不成立则退回 `open` 并写复核结论 | P0 | `docs/issues/ISS-2026-057-元信息同行声明默认落点基准被误判.md`、`docs/issues/ISS-2026-058-变异语料锚点漂移致判据不可观察.md` | T01 | ☐ 未开始 | — |
| T06 | 清偿 ISS-2026-060 与 ISS-2026-061（后者原文本就写着「待独立评审第二轮复跑」，直接走第二轮） | P0 | `docs/issues/ISS-2026-060-仓扫PASS被当作门有效的证据.md`、`docs/issues/ISS-2026-061-新判据声明了却不被校验的六处.md` | T01 | ☐ 未开始 | — |
| T07 | 清偿 ISS-2026-066：复核四处不同步是否已消除，`fix_revision` 改写为已并入 `main` 的提交号 | P0 | `docs/issues/ISS-2026-066-整改批自述与实现面不同步.md` | T01 | ☐ 未开始 | — |
| T08 | 全量门实跑 + 把清偿结果回写 `docs/releases/pending-test.md` 与批次 README 目标承接表 | P0 | `docs/releases/pending-test.md`、`docs/features/feature-2026-10-28-评审欠账清偿/README.md` | T01、T02、T03、T04、T05、T06、T07 | ☐ 未开始 | — |

## 分支策略

| 仓库 | 用途 | 基线 | 基线提交 | 开发分支 | 确认状态 | 确认依据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentflows | 实施与测试 | main | c134d0b | feature-2026-10-28-评审欠账清偿 | 已确认 | 用户 2026-10-28「看看怎么修复，单独立项看看」 | 不推送、不合并、不重装 |

## 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-评审欠账清偿"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

## 门与回滚点

- **门 1（实施前）**：T01 的委派探测必须先跑。探测失败即 T02/T03/T05/T06/T07 全部置 ⚠，
  本批停在立项状态——**不得**改用主审自审冒充清偿，那正是本批要清的欠账形态。
- **门 2（受保护面）**：T04 触碰 `schemas/` 与 `tools/lab/`，属门变更。开工前须逐项列出拟改内容
  并单独授权；未获授权时 T04 置 ⚠，G2 结论上限 `partial`。
- **门 3（评审推翻）**：T02/T03 得出 `changes_requested` 时，findings 一律转成 `ISS-*` 记录，
  受影响的改动回到待修状态（`contracts.md` 不变式 3）；不得以「当时评估过」为由保留。
- **门 4（交付）**：T08 前四类验证命令全绿，且两批 `reviews/` 各有记录、五条 ISS 状态全部
  离开 `fixed-pending-review`。
- **回滚点**：本批基线为 `main` 的 `c134d0b`；文档面改动可整节回退，
  schema 与校验器回滚须同批回退两者。
- **评审档位**：L1（委派能力已于 2026-10-28 实测恢复）。两个入口门待独立 `reviewer` 承担；
  门未关闭前本批结论上限 `partial`。

## 未决事项（实施前需用户确认）

| # | 事项 | 推荐 | 说明 |
| --- | --- | --- | --- |
| 1 | T04 是否授权改 `schemas/review.schema.json` 与 `tools/lab/gate/` | 授权 | 伪降级判据没有不受保护面的落点；不授权则 G2 只能停在「清单可清点」，`review_tier` 仍无人校验 |
| 2 | 两批的独立评审是否按 L1（单角色）而非 L2 执行 | L1 | 本批只改文档与记录层，单角色足够；L2 需两个只读角色，成本更高且不增加结论可信度 |
| 3 | 五条 ISS 中若有复核不成立者，是否允许退回 `open` | 允许 | 不允许就只剩「推到 verified」一条路，那是伪造结论 |
