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
| T01 | 两组委派探测：先派 1 个只读角色，再派 2 个；按结果定档（1 成功 + 第 2 个失败 ⇒ L1；2 个都成功 ⇒ L2），原始返回落批次证据；同时把欠账清单的人读镜像写进 `docs/releases/todo.md` | P0 | `docs/releases/todo.md`、`docs/features/feature-2026-10-28-评审欠账清偿/testing/` | — | ☐ 未开始 | — |
| T02 | 对评测整改批（0.20.0，被评审 revision `26988a4`）派独立评审，记录落批次 `reviews/`，含按 T01 结果确定的 `review_tier` 与 `source_revision` | P0 | `docs/features/feature-2026-10-28-评测整改批/reviews/` | T01 | ☐ 未开始 | — |
| T03 | 对表达面与角色治理批（范围冻结批，被评审 revision `26988a4`）派独立评审，记录落批次 `reviews/` | P0 | `docs/features/feature-2026-10-28-表达面与角色治理/reviews/` | T01 | ☐ 未开始 | — |
| T04 | 给 `review_tier` 加校验：schema 增两字段 + 一条 `allOf`，校验器判伪降级（L0 而 `dispatch_errors` 空），并跑 `packaging/build_runtime.py` 重建生成树；**属受保护面门变更，须逐项授权后方可开工** | P0 | `schemas/review.schema.json`、`tools/lab/gate/records.py`、`tests/test_gate_records.py`、`packaging/runtime/schemas/review.schema.json` | — | ☐ 未开始 | — |
| T05 | 清偿 ISS-2026-057 与 ISS-2026-058：独立复核修复是否成立，成立则补 `fix_revision`（提交号）+ `reviewer` + `review_decision` + `closure_criteria` + 正文 `## 审查`，转 `verified`；不成立则退回 `open` 并写复核结论 | P0 | `docs/issues/ISS-2026-057-元信息同行声明默认落点基准被误判.md`、`docs/issues/ISS-2026-058-变异语料锚点漂移致判据不可观察.md` | T01 | ☐ 未开始 | — |
| T06 | 清偿 ISS-2026-060 与 ISS-2026-061（后者原文本就写着「待独立评审第二轮复跑」，直接走第二轮） | P0 | `docs/issues/ISS-2026-060-仓扫PASS被当作门有效的证据.md`、`docs/issues/ISS-2026-061-新判据声明了却不被校验的六处.md` | T01 | ☐ 未开始 | — |
| T07 | 清偿 ISS-2026-066：复核四处不同步是否已消除，`fix_revision` 改写为可解析提交号（如 `26988a4`） | P0 | `docs/issues/ISS-2026-066-整改批自述与实现面不同步.md` | T01 | ☐ 未开始 | — |
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

- **门 1（实施前）**：T01 的两组委派探测必须先跑，原始返回落批次证据。两组都失败即
  T02/T03/T05/T06/T07 全部置 ⚠，本批停在立项状态——**不得**改用主审自审冒充清偿，那正是本批要清的
  欠账形态。档位按实测定（1 成功 + 第 2 个失败 ⇒ L1；2 个都成功 ⇒ L2），不按成本偏好选。
- **门 2（受保护面）**：T04 触碰 `schemas/`、`tools/lab/` 与 `packaging/runtime/schemas/`（生成树），
  属门变更。开工前须逐项列出拟改内容并单独授权；未获授权时 T04 置 ⚠，G2 结论上限 `partial`。
  授权范围必须含「跑 `python3 packaging/build_runtime.py` 重建快照」——只改源不重建会让
  `validate.py manifests` 红（实测原文：`packaging/runtime/schemas/review.schema.json: content differs from source`）。
- **门 3（评审推翻）**：T02/T03 得出 `changes_requested` 时，findings 一律转成 `ISS-*` 记录
  （不设「正文写已就地修复」旁路），受影响的改动回到待修状态（`contracts.md` 不变式 3）；
  不得以「当时评估过」为由保留。
- **门 4（交付）**：T08 前四类验证命令全绿，且两批 `reviews/` 各有记录、五条 ISS 状态全部
  离开 `fixed-pending-review`。
- **回滚点**：本批基线为 `main` 的 `c134d0b`；文档面改动可整节回退，
  schema 与校验器回滚须同批回退两者，并重跑 `build_runtime.py` 使快照跟随。
- **评审档位**：由 T01 的两组探测决定（不预设）。门未关闭前本批结论上限 `partial`。

## 未决事项（实施前需用户确认）

| # | 事项 | 推荐 | 说明 |
| --- | --- | --- | --- |
| 1 | T04 是否授权改 `schemas/review.schema.json`、`tools/lab/gate/` 并重建生成树 | 授权 | 伪降级判据没有不受保护面的落点；不授权则 G2 只能停在「清单可清点」，`review_tier` 仍无人校验。已登记 `docs/PENDING-DECISIONS.md` 第 17 条 |
| 2 | 是否把 `review_tier` 补进 episode 与决策记录两处契约指名的载体 | 本批不做，另立 | 契约 `contracts.md:42-43` 点名的是「决策记录或 episode」，那两处当前都无该字段且同属受保护面；本批的真实欠账在批次 README/计划层，由派生清单覆盖。已登记第 18 条 |
| 3 | 五条 ISS 中若有复核不成立者，是否允许退回 `open` | 允许（已定为 spec M-C-01） | 不设为待决项——不允许就只剩「推到 verified」一条路，那是伪造结论。此项已由 spec 冻结，不再作为并行台账存在 |

> 档位（L1/L2）**不是**待拍板事项：它由 T01 的两组派发结果决定，属能力事实而非偏好选择。
