# agentflows 索引

> 全仓唯一文档索引。文档的新增、移动与删除必须同步维护本文件；相对链接带 `.md` 后缀。

## 从这里开始

| 场景 | 入口 |
| --- | --- |
| **第一次用 / 5 分钟上手** | `docs/quickstart.md`（先判断要不要用这套，再决定走哪条路） |
| 日常两轨 | 小修与零星事项走 `docs/issues/`；成批 / 跨层工作立 `docs/features/<批次>/`；拍板与待验收分别看 `docs/PENDING-DECISIONS.md` 与 `docs/releases/pending-test.md` |
| 改角色定义 | `agents/README.md`（<!-- count:agents -->14<!-- /count --> 个角色文件 + 工作链调度入口） |
| 改方法契约与流程文本 | `skills/agentflow/`（`SKILL.md`、`references/`）、`skills/improve/` |
| 配宿主级全局规则 | `skills/agentflow/references/hosts.md`（三层分工、托管块、宿主矩阵）· `skills/agentflow/templates/host/global-rules.md`（规则正文） |
| 抄模板（提案/规格/方案/计划） | `skills/agentflow/templates/README.md` |
| 查批次与实施计划 | `docs/features/README.md`（活跃批次入口与状态）；具体任务状态只看各批次 `plan/` 看板 |
| 查缺陷与事项 | `docs/issues/README.md`（`ISS-<YYYY>-<NNN>`，含看板与归档规则） |
| 查对外评审落点 | `reviews/README.md` |
| 查发布与待验证清单 | `docs/releases/`：`todo.md`（待办与索引）· `pending-test.md`（待验收）；逐版本发布记录已停用，版本史见 `CHANGELOG.md` |
| 看设计、指南与事实 | `docs/`：`product/`（产品链）、`quickstart.md`（5 分钟上手）、`system-guide.md`（体系指南）、`design-decisions.md`（设计决策）、`host-platform-facts.md`（宿主事实） |
| 看仓库怎么分级、各面怎么装 | [`README.md`](README.md) 的「仓库布局」节与 [`tools/lab/README.md`](tools/lab/README.md)（手写的目录树已删除，避免与真实结构漂移） |
| 记录与改进环 | `docs/issues/`（缺陷与台账）、`docs/features/`（批次与计划）、`episodes/`（决策记录）、`docs/releases/`（在途与待验收）、`reviews/`（对外评审落点）；改进三件套已停用 |
| 校验与评测工具 | `tools/lab/` |
| 查本仓自评（评测报告 / 缺口清单 / 拍板项） | `docs/evaluations/`；最新整体审核见 [2026-10-23 功能、文档与模板审核](docs/evaluations/AGENTFLOW-AUDIT-2026-10-23.md)；历史报告按文件日期查阅 |

## 维护纪律

- 文档的新增、移动与删除必须同步维护本索引。
- 新增顶层目录或新的文档类型须先经用户确认，不得自动创建。
- 相对链接带 `.md` 后缀；文档正文不写会话角色词与裸代号（判据见 `skills/agentflow/references/document-chain.md` 的表达纪律节）。

## 迁移与清理记录

> 详细改动记录见 [`CHANGELOG.md`](CHANGELOG.md) 与 git 历史；本节只保留批次索引（按日期倒序），
> 不再复述改动细节——索引只描述现行结构。

- 2026-10-25 测试链路 Ego Light 切换批 / 门与测试拆分批（0.15.0）
- 2026-10-24 宿主接入批（Host Init：跨仓全局规则分发、托管块模板、0.14.0）
- 2026-10-23 追溯闭环与证据在场批（门变更：文档链新增 C22 目标承接闭环与 C23 证据在场；记录契约补 `disposition`；拍板口八列化；八条文本缺陷收口）
- 2026-10-22 文档面收尾批（角色计数口径、0.12.0 状态回写、门清单补齐、索引去重）
- 2026-10-21 收尾批 / 跨仓吸收批 / 决策可追溯实施批
- 2026-10-20 角色层收口批 / 评测修复批 / 评测归档批
- 2026-10-19 门健全批 / 过期货清理批
- 2026-10-18 合并批
- 2026-10-13 文档面校正批
- 2026-10-12 评测装置裁撤批 / 归档批 / 结构改造批四期 / 三期 / 瘦身批
- 2026-10 结构改造迁移执行批次
- 2026-10-09 彻底清理与防漂移批次
