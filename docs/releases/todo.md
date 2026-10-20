# 发布待办

> 在途批次索引、决策性记录与零散微项。已完成条目见 git 历史与 `../../CHANGELOG.md`；
> 待用户拍板的事项见 `../PENDING-DECISIONS.md`；待人工验收见 `pending-test.md`。

## 批次索引

> 已完成批次（全仓中文化 `4c767eb`、youc 吸收批 `6d10b14`、结构文档、端点复测与试水）见
> git 历史与 `../../CHANGELOG.md`；本表只保留在途与新条目。

| # | 变更 | 状态 | 备注 |
| --- | --- | --- | --- |
| 1 | 产品链修复轮（REV-20261010-001 的 6 P1 + 6 P2） | 已完成 | 修复轮于 2026-10-19 落盘（纯文本改动，未碰受保护面）；独立复审 `reviews/agentflow-product-chain/review-2026-10-19-003.md` 确认 F1–F12 全关闭、`decision: approved`（机器复核 `doc_chain_live` 与 `all` 全 PASS）；`docs/product/README.md` 需求评审门已可勾选。原「待排」为陈旧误记 |
| 2 | 质量提升批（feature-2026-10-13：门禁拆分 / 变异测试 / 计数脚本 / 角色场景 / 文档链） | 收尾中（看板 PLAN-QUALITY-001 已回写） | T01–T09 已闭（T04 于 2026-10-20 全量实跑 28/28 达成、G5 通过）；T10 本期不做。门变更均经独立评审 approved |

## 决策性记录

- **吸收 youc 模式**（2026-10-10 用户指示）：实例化本文件与 `pending-test.md`；建立
  `../PENDING-DECISIONS.md` 单点拍板清单；`AGENTS.md` 增「表达与沉淀纪律」；`SKILL` 增
  「首次接入（Init）」；「单真源 + 生成视图」推迟为设计项（原待拍板第 8 条：拍板为试点
  「结构文档目录树生成」；未开工，试点载体所在的手写目录树已随 2026-10-13 校正批删除——重启需另行立项）。
- **中文化口径**（用户指示「能改的都改」）：含受保护面；受保护改动的授权依据见相应提交信息与
  `CHANGELOG`，回溯评审登记为 `../PENDING-DECISIONS.md` 第 4 条。

## 零散微项

- ~~计划看板回写：`plans/PLAN-PRODUCT-001.md` 自 2026-09-19 起未回写~~——已回写（2026-10-10，T02/T04/T05/T06 + 概览行）。
- ~~复核 `--case-ids` 门变更有无 `CHANGELOG` 条目~~——已复核：确认无条目，按书面豁免（不改写历史条目）。
- ~~`check-write-scope.sh` 的「. 全树范围」缺陷~~——已修复（ISS-2026-041 + 双回归用例）。
- ~~`schemas/*.schema.json` 内部 description 字段是否汉化~~——已拍板：不翻。
- ~~`templates/index-template.md` 与 `templates/hub/index.md` 两份索引骨架重复~~——已删 index-template.md（2026-10-10；保留被 Init/模板清单接线的 hub/index.md）。
- ~~`host_adapter` 隔离路径认证失败待处置~~——已失对象关闭（2026-10-12：`host_adapter` 随评测装置整线裁撤，见 ISS-2026-052 与 `docs/design-decisions.md` §3；`../PENDING-DECISIONS.md` 对应条目已关闭）。
- ~~完整公开切片闭环授权（约 18 次调用）~~——已失对象关闭（装置裁撤后无可跑切片；授权条随业务尺子关闭，证据见 ISS-2026-046 与 `../PENDING-DECISIONS.md` 头部注记）。
- 产品链修复轮（REV-20261010-001）——`../PENDING-DECISIONS.md`（修复轮条）。
