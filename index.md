# agentflows 索引

> 全仓唯一文档索引。文档的新增、移动与删除必须同步维护本文件；相对链接带 `.md` 后缀。

## 从这里开始

| 场景 | 入口 |
| --- | --- |
| 改角色定义 | `agents/`（14 个角色文件） |
| 改方法契约与流程文本 | `skills/agentflow/`（`SKILL.md`、`references/`）、`skills/improve/` |
| 抄模板（提案/规格/方案/计划） | `skills/agentflow/templates/README.md` |
| 查批次与实施计划 | `features/`（`feature-<YYYY-MM-DD>-<主题>/`） |
| 查缺陷与事项 | `issues/README.md`（`ISS-<YYYY>-<NNN>`，含看板与归档规则） |
| 查对外评审落点 | `reviews/README.md` |
| 查发布与待验证清单 | `releases/README.md` |
| 看设计、指南与事实 | `docs/`：`product/`、`system-guide.md`、`agent-roles.md`、`host-platform-facts.md`、`iteration-log.md` |
| 翻冻结历史 | `_archive/README.md`（三级冻结规则） |
| 记录与改进环 | `issues/`（缺陷与台账）、`episodes/`（决策记录）、`plans/`（执行计划）、`improvements/`（改进三件套）、`releases/`（发布记录）、`reviews/`（对外评审落点） |
| 校验与评测工具 | `tools/lab/` |

## 维护纪律

- 文档的新增、移动与删除必须同步维护本索引。
- 新增顶层目录或新的文档类型须先经用户确认，不得自动创建。
- 相对链接带 `.md` 后缀；文档正文不写会话角色词与裸代号（判据见 `skills/agentflow/references/document-chain.md` 的表达纪律节）。

## 待迁移清单（已完成 — 2026-10 结构改造迁移执行批次）

- [x] `records/bugs/` → `issues/`（统一 `ISS-<YYYY>-<NNN>`；仅 `rejected` 记录进 `issues/归档/<日期>/`）
- [x] `records/plans`、`records/episodes`、`records/reviews`、`records/tests`、`records/improvement` → 批次目录与 `releases/`
- [x] `docs/audit-2026-09-18/`、`docs/audit-2026-09-18-followups.md`、`docs/next-session-handoff.md` → `_archive/`（未决项先出表）
- [x] 全仓引用改指与检索索引重建

逐文件「旧路径 → 新路径」对照见
[`features/feature-2026-10-09-结构改造/plan/migration-mapping.md`](features/feature-2026-10-09-结构改造/plan/migration-mapping.md)；
迁移契约见同目录 `migration-spec.md`。

## 冻结历史

（条目 · 冻结日期 · 承接位置）
