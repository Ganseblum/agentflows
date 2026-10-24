# 发布待办

> 在途批次索引与决策性记录。已完成条目见 git 历史与 `../../CHANGELOG.md`；
> 待用户拍板的事项见 `../PENDING-DECISIONS.md`；待人工验收见 `pending-test.md`。

## 批次索引

| # | 变更 | 状态 | 备注 |
| --- | --- | --- | --- |
| 1 | 质量提升批（feature-2026-10-13：门禁拆分 / 变异测试 / 计数脚本 / 角色场景 / 文档链） | 收尾中（看板 PLAN-QUALITY-001 已回写） | T01–T09 已闭（T04 于 2026-10-20 全量实跑 28/28 达成、G5 通过）；T10 本期不做。门变更均经独立评审 approved。2026-10-23 追溯闭环批为本批补上 T01/T04 的仓内证据载体并回写了 `spec/qa` 的验收点状态列 |
| 2 | 追溯闭环与证据在场批（feature-2026-10-22：文档链新增 C22 目标承接闭环与 C23 证据在场、记录契约补 `disposition`、拍板口八列化、八条文本缺陷收口） | 执行中（看板 `docs/features/feature-2026-10-22-追溯闭环与证据在场/plan/PLAN-TRACE-001.md`） | 门变更经用户 2026-10-22 当次授权；发版口径为本地 bump 与生成树重建，不推送、不动宿主安装 |
| 3 | 宿主接入批 2026-10-24：Host Init（`skills/agentflow/references/hosts.md`、`skills/agentflow/templates/host/`、SKILL 宿主级接入节）、0.14.0 版本 bump | 本地 bump，待真实宿主验收 | 未推送、未安装到宿主；真实宿主写入与加载验证见 `pending-test.md` 第 4 行 |

已完成批次：产品链修复轮（REV-20261019-003 approved，2026-10-19）、全仓中文化、youc 吸收批、结构文档、端点复测与试水、2026-10-22 文档面收尾批——详见 `CHANGELOG.md` 与 git 历史。

## 决策性记录

- **吸收 youc 模式**（2026-10-10 用户指示）：实例化本文件与 `pending-test.md`；建立
  `../PENDING-DECISIONS.md` 单点拍板清单；`AGENTS.md` 增「表达与沉淀纪律」；`SKILL` 增
  「首次接入（Init）」；「单真源 + 生成视图」推迟为设计项（原待拍板第 8 条：拍板为试点
  「结构文档目录树生成」；未开工，试点载体所在的手写目录树已随 2026-10-13 校正批删除——重启需另行立项）。
- **中文化口径**（用户指示「能改的都改」）：含受保护面；受保护改动的授权依据见相应提交信息与
  `CHANGELOG`，回溯评审登记为 `../PENDING-DECISIONS.md` 第 4 条。

## 零散微项

- 当前无未关闭微项。历史微项（计划看板回写、`--case-ids` 复核、`check-write-scope.sh`「.」缺陷、
  schema description 汉化、`index-template.md` 去重、`host_adapter` 隔离认证、公开切片授权）
  均已在 2026-10-09–2026-10-22 期间关闭，证据见 `CHANGELOG.md` 与 git 历史。
