# 发布待办

> 在途批次索引、决策性记录与零散微项。已完成条目见 git 历史与 `../CHANGELOG.md`；
> 待用户拍板的事项见 `../plans/PENDING-DECISIONS.md`；待人工验收见 `pending-test.md`。

## 批次索引

> 已完成批次（全仓中文化 `4c767eb`、youc 吸收批 `6d10b14`、结构文档、端点复测与试水）见
> git 历史与 `../CHANGELOG.md`；本表只保留在途与新条目。

| # | 变更 | 状态 | 备注 |
| --- | --- | --- | --- |
| 1 | 清理与归档批（台账收敛 / 计划过期点同步 / 本地垃圾清扫） | 完成（随本批提交） | 记录见 episode `EP-20261010-003` |
| 2 | 产品链修复轮（REV-20261010-001 的 6 P1 + 6 P2） | 待排 | `../plans/PENDING-DECISIONS.md` |

## 决策性记录

- **吸收 youc 模式**（2026-10-10 用户指示）：实例化本文件与 `pending-test.md`；建立
  `plans/PENDING-DECISIONS.md` 单点拍板清单；`AGENTS.md` 增「表达与沉淀纪律」；`SKILL` 增
  「首次接入（Init）」；「单真源 + 生成视图」推迟为设计项（见待拍板第 8 条）。
- **中文化口径**（用户指示「能改的都改」）：含受保护面；受保护改动的授权依据与回溯评审
  登记见 `../plans/PENDING-DECISIONS.md` 第 2 条。

## 零散微项

- ~~计划看板回写：`plans/PLAN-PRODUCT-001.md` 自 2026-09-19 起未回写~~——已回写（2026-10-10，T02/T04/T05/T06 + 概览行）。
- ~~复核 `--case-ids` 门变更有无 `CHANGELOG` 条目~~——已复核：确认无条目，按书面豁免（不改写历史条目）。
- ~~`check-write-scope.sh` 的「. 全树范围」缺陷~~——已修复（ISS-2026-041 + 双回归用例）。
- ~~`schemas/*.schema.json` 内部 description 字段是否汉化~~——已拍板：不翻。
- `host_adapter` 隔离路径认证失败待处置——`../plans/PENDING-DECISIONS.md`（隔离路径条）。
- 完整公开切片闭环授权（约 18 次调用）——`../plans/PENDING-DECISIONS.md`（试水后授权条）。
- 产品链修复轮（REV-20261010-001）——`../plans/PENDING-DECISIONS.md`（修复轮条）。
