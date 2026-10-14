# agentflows 索引

> 全仓唯一文档索引。文档的新增、移动与删除必须同步维护本文件；相对链接带 `.md` 后缀。

## 从这里开始

| 场景 | 入口 |
| --- | --- |
| **第一次用 / 5 分钟上手** | `docs/quickstart.md`（先判断要不要用这套，再决定走哪条路） |
| 日常两轨 | 小修与零星事项走 `docs/issues/`；成批 / 跨层工作立 `docs/features/<批次>/`；拍板与待验收分别看 `docs/PENDING-DECISIONS.md` 与 `docs/releases/pending-test.md` |
| 改角色定义 | `agents/`（14 个角色文件） |
| 改方法契约与流程文本 | `skills/agentflow/`（`SKILL.md`、`references/`）、`skills/improve/` |
| 抄模板（提案/规格/方案/计划） | `skills/agentflow/templates/README.md` |
| 查批次与实施计划 | `docs/features/`（`feature-<YYYY-MM-DD>-<主题>/`；当前无在途批次，已完成批次随瘦身批删除，git 历史可回溯） |
| 查缺陷与事项 | `docs/issues/README.md`（`ISS-<YYYY>-<NNN>`，含看板与归档规则） |
| 查对外评审落点 | `reviews/README.md` |
| 查发布与待验证清单 | `docs/releases/`：`todo.md`（待办与索引）· `pending-test.md`（待验收）；逐版本发布记录已停用，版本史见 `CHANGELOG.md` |
| 看设计、指南与事实 | `docs/`：`product/`（产品链）、`quickstart.md`（5 分钟上手）、`system-guide.md`（体系指南）、`design-decisions.md`（设计决策）、`host-platform-facts.md`（宿主事实） |
| 看项目结构体系 | `docs/project-structure.md`（目录树、五个面、安装链路、约定速查） |
| 记录与改进环 | `docs/issues/`（缺陷与台账）、`docs/features/`（批次与计划）、`episodes/`（决策记录）、`docs/releases/`（在途与待验收）、`reviews/`（对外评审落点）；改进三件套已停用 |
| 校验与评测工具 | `tools/lab/` |

## 维护纪律

- 文档的新增、移动与删除必须同步维护本索引。
- 新增顶层目录或新的文档类型须先经用户确认，不得自动创建。
- 相对链接带 `.md` 后缀；文档正文不写会话角色词与裸代号（判据见 `skills/agentflow/references/document-chain.md` 的表达纪律节）。

## 迁移与清理记录

- 2026-10-12 评测装置裁撤批：`evals/`、runner/adapter/policy、三个 schema 与相关契约整线删除，
  设计知识与恢复清单留存 `docs/design-decisions.md` §3（ISS-2026-052）。
- 2026-10-12 归档批：三份设计文档合并为 `docs/design-decisions.md`（守卫清单收窄）；`evals/` 标注为仪器存量；待拍板第 4 条范围并入本日五批（ISS-2026-051）。
- 2026-10-12 结构改造批四期：`plan` 归入 `docs/features/<批次>/plan/`（顶层 `plans/` 撤销，跨批次拍板口提至 `docs/PENDING-DECISIONS.md`）；改进环死代码随停用机制清除（ISS-2026-049）。
- 2026-10-12 结构改造批三期：`issues/`、`plans/`、`releases/`（工作文件）迁入 `docs/`；逐版本
  发布记录与改进三件套停用；`docs/features/` 按 youc 形态重建（用户拍板，ISS-2026-048）。
- 2026-10-12 瘦身批：归档桶 `_archive/`、两个已完成 `features/` 批次与 mock/ 业务样板整体裁撤
  （用户授权，ISS-2026-047）；历史按 git 回溯，索引只描述现行结构。
- 2026-10 结构改造迁移执行批次（已完成）：记录树撤换为活区、审计/交接件入档、全仓引用改指与检索索引重建。
- 2026-10-09 彻底清理与防漂移批次：断链与退役路径收敛，`validate.py docs` 增断链/退役路径机器门。
