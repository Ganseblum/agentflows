# 评审落点

本目录是 `feature-2026-10-29-全面修正与瘦身` 两个入口门（需求评审门、技术方案评审门）的记录落点，
对应计划 `../plan/PLAN-FIX-001.md` 的 T14。

**当前状态：本目录除本说明外无评审记录，即两个门尚未关闭。** 批次 README 不预设评审档位——
档位由 T14 的两组委派探测结果决定，探测的原始返回落 `../testing/`。评审真实跑过之前，
本目录不得出现「已完成评审」的表述；跑完后每个文件带 `review_tier` 与 `dispatch_errors`
（若降级），由 `docs/PENDING-DECISIONS.md` 与本批目标承接表回写状态，状态权威在各记录 frontmatter。

`review_tier` 与 `dispatch_errors` 两字段是本批 T09 进入 `schemas/review.schema.json` 的契约字段；
在该判据落地前写的记录会走「未声明」分支，不红也不绿。
