# agentflows 索引

> 全仓唯一文档索引。文档的新增、移动与删除必须同步维护本文件；相对链接带 `.md` 后缀。

## 从这里开始

| 场景 | 入口 |
| --- | --- |
| 日常两轨 | 小修与零星事项走 `issues/`；成批 / 跨层工作立 `features/<批次>/`；拍板与待验收分别看 `plans/PENDING-DECISIONS.md` 与 `releases/pending-test.md` |
| 改角色定义 | `agents/`（14 个角色文件） |
| 改方法契约与流程文本 | `skills/agentflow/`（`SKILL.md`、`references/`）、`skills/improve/` |
| 抄模板（提案/规格/方案/计划） | `skills/agentflow/templates/README.md` |
| 查批次与实施计划 | `features/`（`feature-<YYYY-MM-DD>-<主题>/`） |
| 查缺陷与事项 | `issues/README.md`（`ISS-<YYYY>-<NNN>`，含看板与归档规则） |
| 查对外评审落点 | `reviews/README.md` |
| 查发布与待验证清单 | `releases/`：`todo.md`（待办与索引）· `pending-test.md`（待验收）· 发布记录与 `README.md` |
| 看设计、指南与事实 | `docs/`：`product/`、`system-guide.md`、`agent-roles.md`、`host-platform-facts.md`、`iteration-log.md` |
| 看项目结构体系 | `docs/project-structure.md`（目录树、五个面、安装链路、约定速查） |
| 翻冻结历史 | `_archive/README.md`（三级冻结规则） |
| 记录与改进环 | `issues/`（缺陷与台账）、`episodes/`（决策记录）、`plans/`（执行计划 + 待拍板事项）、`improvements/`（改进三件套）、`releases/`（发布记录）、`reviews/`（对外评审落点） |
| 校验与评测工具 | `tools/lab/` |

## 维护纪律

- 文档的新增、移动与删除必须同步维护本索引。
- 新增顶层目录或新的文档类型须先经用户确认，不得自动创建。
- 相对链接带 `.md` 后缀；文档正文不写会话角色词与裸代号（判据见 `skills/agentflow/references/document-chain.md` 的表达纪律节）。

## 迁移与清理记录

- 2026-10 结构改造迁移执行批次（已完成）：记录树撤换为活区、审计/交接件入档、全仓引用改指与检索索引重建。
- 2026-10-09 彻底清理与防漂移批次：断链与退役路径收敛，`validate.py docs` 增断链/退役路径机器门。

逐文件「旧路径 → 新路径」对照与迁移契约见
[`features/feature-2026-10-09-结构改造/plan/migration-mapping.md`](features/feature-2026-10-09-结构改造/plan/migration-mapping.md)（`migration-spec.md` 同目录）。

## 冻结历史

（条目 · 冻结日期 · 承接位置）
