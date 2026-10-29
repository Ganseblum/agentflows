# 执行证据落点

本目录存放 `feature-2026-10-29-全面修正与瘦身` 实施过程中的**原始输出**，不落结论摘录。
进度权威始终在计划看板 `../../../plan/PLAN-FIX-001.md`，本目录只做它的证据载体。

| 子目录 | 内容 | 产生任务 |
| --- | --- | --- |
| `evidence/gate-runs/` | `validate.py all`、`doc_chain.py <本批>`、`--self-test`、`unittest` 的逐字输出 | T04…T14 |
| `evidence/scan-before-after/` | 记录面引用扫描在「改写前 / 改写后 / 删除后」三次的命中原文与计数 | T10、T11 |
| `evidence/deletion-counts/` | 删除动作前后的文件数与体积对比，附 `dirty-guard` 的 snapshot / verify 输出 | T11 |
| `evidence/dispatch-probe/` | 两组委派探测的原始返回（成功返回或失败错误原文），用于确定评审档位 | T14 |

约定：只存在于本机 `/tmp` 的输出不算证据，须原样落进本目录后才可写进计划的证据列
（判据口径同 `skills/agentflow/references/document-chain.md` 的门 8）。
