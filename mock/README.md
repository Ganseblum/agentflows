# mock/ —— 各记录类型的完整样板（仅供预审，非证据）

这些文件演示**每种记录类型和关键状态**的最终形态。它们不是证据，不进仓库；预审通过后
按下方映射复制进 `records/` 对应位置即可作为真实记录使用（复制后跑
`python3 tools/lab/validate.py all` 验证）。

## 映射表（mock 文件 → 将来写入 records/ 的位置 → 演示的情况）

| mock 文件 | 目标位置 | 演示的情况 |
| --- | --- | --- |
| [records/bugs/2026-09-17/full-record-demo.md](records/bugs/2026-09-17/full-record-demo.md) | `records/bugs/<日期>/<slug>.md` | **verified** 全字段形态：条件四件套（reviewer/decision/regression/closure_criteria）、fix_revision、外部引用+内嵌片段 |
| [records/bugs/2026-09-17/open-bug-demo.md](records/bugs/2026-09-17/open-bug-demo.md) | 同上 | **open** 最小字段集；`provenance: undetermined` 必须写明缺的证据 |
| [records/bugs/2026-09-17/fixed-pending-review-demo.md](records/bugs/2026-09-17/fixed-pending-review-demo.md) | 同上 | **fixed-pending-review**：修复已落地、等待独立评审；`regression_status: not-run` 的诚实标注 |
| [records/bugs/2026-09-17/recurrence-occ1-demo.md](records/bugs/2026-09-17/recurrence-occ1-demo.md) | 同上 | 再犯类**第 1 次**记录：`class_id` + `occurrence: 1` |
| [records/bugs/2026-09-17/recurrence-occ2-demo.md](records/bugs/2026-09-17/recurrence-occ2-demo.md) | 同上 | 再犯类**第 2 次**（归纳后再犯）：`occurrence: 2`、版本高于 `consolidated_in` |
| [records/bugs/recurrence/demo-recurrence-class.md](records/bugs/recurrence/demo-recurrence-class.md) | `records/bugs/recurrence/<class_id>.md` | **类台账**：已归纳 + 归纳后再犯 → `recurrence` 查询输出 `escalated`（最高档加重标记） |
| [records/bugs/archive/2026-09-17/rejected-bug-demo.md](records/bugs/archive/2026-09-17/rejected-bug-demo.md) | `records/bugs/archive/<日期>/<slug>.md` | **rejected**：只在 archive/ 下合法，含 rejection_reason |
| [records/reviews/demo-project-feature-demo/review-2026-09-17-001.md](records/reviews/demo-project-feature-demo/review-2026-09-17-001.md) | `records/reviews/<project>-<feature-slug>/review-<日期>-<NNN>.md` | **评审记录**：feature 锚目录、决策 changes_requested、findings 关联 bug |
| [records/reviews/…/archive/2026-09-17-001/design-be.md](records/reviews/demo-project-feature-demo/archive/2026-09-17-001/design-be.md) | 评审记录旁的 `archive/<轮次>/` | **评审快照**：被评审文档逐字副本（证据，非记录） |
| [records/episodes/2026-09-17/EP-20260917-901.json](records/episodes/2026-09-17/EP-20260917-901.json) | `records/episodes/<日期>/<EP-id>.json` | **episode**：任务级决策记录（JSON），improve 环燃料 |
| [records/plans/PLAN-DEMO-SHARE-001.md](records/plans/PLAN-DEMO-SHARE-001.md) | `records/plans/<plan_id>.md` | **执行计划（0.5.0 融合形态）**：frontmatter 信封 + 进展概览/任务清单（状态+证据回写）/验证命令；机器断言=依赖无环、ID 唯一、状态枚举、阻塞未决不得 approved |

## 预审要点

1. **字段是否够用**：每条记录的信息是否覆盖你想留档的内容；缺什么字段说一声。
2. **状态机是否符合直觉**：open → fixed-pending-review → verified，rejected 归档。
3. **再犯类档位**：台账 + 两条 occurrence 的组合是否把"改了又出现"讲清楚。
4. **评审桥**：feature 锚目录 + 轮次文件 + 快照是否是你预期的双仓用法。

## 验证方式（已实测）

把 `mock/records/*` 合并进真实 `records/`（在 /tmp 副本上做过全量验证）：

```sh
python3 tools/lab/validate.py all        # 八项全绿
python3 tools/lab/validate.py report     # 样板记录出现在回溯表
python3 tools/lab/validate.py recurrence # demo-recurrence-class 输出 escalated
```
