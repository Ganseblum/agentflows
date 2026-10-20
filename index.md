# agentflows 索引

> 全仓唯一文档索引。文档的新增、移动与删除必须同步维护本文件；相对链接带 `.md` 后缀。

## 从这里开始

| 场景 | 入口 |
| --- | --- |
| **第一次用 / 5 分钟上手** | `docs/quickstart.md`（先判断要不要用这套，再决定走哪条路） |
| 日常两轨 | 小修与零星事项走 `docs/issues/`；成批 / 跨层工作立 `docs/features/<批次>/`；拍板与待验收分别看 `docs/PENDING-DECISIONS.md` 与 `docs/releases/pending-test.md` |
| 改角色定义 | `agents/`（<!-- count:agents -->14<!-- /count --> 个角色文件） |
| 改方法契约与流程文本 | `skills/agentflow/`（`SKILL.md`、`references/`）、`skills/improve/` |
| 抄模板（提案/规格/方案/计划） | `skills/agentflow/templates/README.md` |
| 查批次与实施计划 | `docs/features/`（`feature-<YYYY-MM-DD>-<主题>/`；在途批次 `feature-2026-09-19-产品线完善`（部分任务未开始）、`feature-2026-10-13-质量提升`（部分模块已实施，见批次 README）） |
| 查缺陷与事项 | `docs/issues/README.md`（`ISS-<YYYY>-<NNN>`，含看板与归档规则） |
| 查对外评审落点 | `reviews/README.md` |
| 查发布与待验证清单 | `docs/releases/`：`todo.md`（待办与索引）· `pending-test.md`（待验收）；逐版本发布记录已停用，版本史见 `CHANGELOG.md` |
| 看设计、指南与事实 | `docs/`：`product/`（产品链）、`quickstart.md`（5 分钟上手）、`system-guide.md`（体系指南）、`design-decisions.md`（设计决策）、`host-platform-facts.md`（宿主事实） |
| 看仓库怎么分级、各面怎么装 | [`README.md`](README.md) 的「仓库布局」节与 [`tools/lab/README.md`](tools/lab/README.md)（手写的目录树已删除，避免与真实结构漂移） |
| 记录与改进环 | `docs/issues/`（缺陷与台账）、`docs/features/`（批次与计划）、`episodes/`（决策记录）、`docs/releases/`（在途与待验收）、`reviews/`（对外评审落点）；改进三件套已停用 |
| 校验与评测工具 | `tools/lab/` |

## 维护纪律

- 文档的新增、移动与删除必须同步维护本索引。
- 新增顶层目录或新的文档类型须先经用户确认，不得自动创建。
- 相对链接带 `.md` 后缀；文档正文不写会话角色词与裸代号（判据见 `skills/agentflow/references/document-chain.md` 的表达纪律节）。

## 迁移与清理记录

- 2026-10-19：新增根目录交付件 `AGENTFLOW-EVAL-PROMPT-2026-10-19.md`（多维度 · 多角色 · 证据优先的项目评测 prompt，先例同 `AGENTFLOW-EVALUATION-2026-10-12.md` / `AGENTFLOW-OPTIMIZATION-2026-10-12.md`；未触碰受保护门）。
- 2026-10-19 门健全批（用户指示「全部处理优化」）：`tools/lab/gate/` 全部 13 模块与 `mutate.py` 入受保护面（`protected-paths.txt` + `gate/common.py` 必需条目，门变更经授权）；`gate/schema.py` 新增 schema 关键字 fail-closed 守卫（G1/G14）；`gate/manifests.py` 运行态新鲜度检查纳入 manifests 门；整门变异复跑 51/51 全杀（16 存活项：15 补杀 + 1 项 EXEMPT 论证登记）；`doc_chain.py` C6 收紧（异常矩阵须有数据行）+ 自测 case 12b；`agents/release-governor.md` 晋级条款与 schema 对齐（H1）；`skills/agentflow/templates/testing/{plan,run}.md` 补齐模板缺口；`packaging/runtime` 随源面重建。`PLAN-QUALITY-001` 计划 T05/T07 回写完成、T08 阻塞在外部条件（待用户重装插件）。
- 2026-10-19 过期货清理批（机器门之外的内容性过期校正）：`feature-2026-10-13-质量提升` 批次状态回写（T02/T03 置完成、T05 明确「工具落盘未跑整门变异」，证据为当日复跑）；`docs/features/README.md` 在途批次表与 `CHANGELOG.md` 待发布节补该批条目；`docs/releases/` 两个工作文件中已失对象的验收步骤与指针就地标注（评测装置裁撤所致）；`expression-discipline-jargon` 台账按追加式补维护行；`packaging/runtime` 快照重建成 0.11.0（`document-chain-templates.md` 复活件消除）。无门层改动。
- 2026-10-18 合并批：`workbuddy/main-b0d8652c`（2026-10-12 历史线）并入 `main`；按用户拍板保留 `main` 的裁撤（评测装置不复活），只并入记录类内容——本批两份评审/优化报告留存仓库根（`AGENTFLOW-EVALUATION-2026-10-12.md`、`AGENTFLOW-OPTIMIZATION-2026-10-12.md`，其中提及的评测装置均指裁撤前状态）；缺口收尾 episode 重编为 `episodes/2026-10-12/EP-20261012-008.json` 与 `EP-20261012-009.json`（避开 `main` 已占用的 001–007）；收尾计划归位 `docs/features/feature-2026-09-19-产品线完善/plan/PLAN-OPT-CLOSEOUT-001.md`。
- 2026-10-13 文档面校正批：删除手写目录树 `docs/project-structure.md`（计数多处失实，且与 `index.md`、
  `README.md` 重复），引用改指 `README.md`「仓库布局」节与 `tools/lab/README.md`；同步修正 README、
  AGENTS、host-platform-facts、design-decisions、system-guide、product 链与待拍板清单的失实内容。
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
