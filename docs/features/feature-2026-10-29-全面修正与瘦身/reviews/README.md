# 评审落点

本目录是 `feature-2026-10-29-全面修正与瘦身` 两个入口门（需求评审门、技术方案评审门）的记录落点，
对应计划 `../plan/PLAN-FIX-001.md` 的 T14。

## 在册记录

| 记录 | 轮次与对象 | 决定 | 档位 |
| --- | --- | --- | --- |
| `review-2026-10-29-001.md` | 第一轮 · 门判据四条（技术侧） | `changes_requested`（P1×4、P2×8，已在 T19 处置） | L2 |
| `review-2026-10-29-002.md` | 第一轮 · 需求与文档链（需求侧） | `changes_requested`（P0×4、P1×5、P2×1，已在 T19 处置） | L2 |
| `review-2026-10-29-003.md` | 第二轮 · 需求与验收面 | `changes_requested`（6 条 findings，已逐条修复） | L2 |
| `review-2026-10-29-004.md` | 第二轮 · 技术方案与实施面 | `changes_requested`（5 条 findings，已逐条修复） | L2 |
| `review-2026-10-29-005.md` | 第三轮 · 修复后的 delta 复审 | `blocked`（两次派发均失败，未产出评审正文） | **L0** |

**两个入口门当前仍为 `☐`**：只有独立评审 `approved` 才勾选；L0 的主审自审与确定性门实跑
是降级义务，不是评审结论。补门条件与承诺见 `review-2026-10-29-005.md` 与
`../testing/agentflow-全面修正与瘦身/evidence/dispatch-probe/tier-2026-10-29-r2.md`。

`review_tier` 与 `dispatch_errors` 两字段是本批 T09 进入 `schemas/review.schema.json` 的契约字段；
在该判据落地前写的记录走「未声明」分支，不红也不绿。声明 `L0` 而 `dispatch_errors` 为空会被
记录侧判据判为伪降级，本目录不存在该形态。
