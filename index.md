# agentflows 索引

> 全仓唯一文档索引。文档的新增、移动与删除必须同步维护本文件；相对链接带 `.md` 后缀。
> 本仓内部词（台账 / 拍板口 / 门 / 档位 / 收口 / 承接 / 落点 / 载体 / 批次 / 链 / 口径）的
> 首次含义见 [`docs/system-guide.md`](docs/system-guide.md) 的「术语对照」节，后文不再逐一加注。

## 从这里开始

| 场景 | 入口 |
| --- | --- |
| **第一次用 / 5 分钟上手** | `docs/quickstart.md`（先判断要不要用这套，再决定走哪条路） |
| 按风险选择材料 | [唯一分档判据](skills/agentflow/references/document-chain.md#文档档位)：琐碎静态自检；light 唯一 README（含最小用例/run/独审）；full 按选轨建链，材料权限优先 |
| 改角色定义 | `agents/README.md`（<!-- count:agents -->10<!-- /count --> 个角色文件 + 工作链调度入口） |
| 改方法契约与流程文本 | `skills/agentflow/`（`SKILL.md`、`references/`）；仓库整体审核契约见 [`skills/agentflow/references/repo-audit.md`](skills/agentflow/references/repo-audit.md) |
| 开工提问、设计压测 | [开工提问](skills/agentflow/references/intake.md)（六要素、红线、证据层级）· [压设计](skills/agentflow/references/grilling.md)（设计树、前沿、逐轮推荐）；**用户主动叫的直接入口**：[agentflow-intake](skills/agentflow-intake/SKILL.md) · [agentflow-grilling](skills/agentflow-grilling/SKILL.md) |
| 画、改、评设计图 | [设计图](skills/design-diagram/SKILL.md)（时序/状态/架构/ER；三层选图、事件号、九列表、失败分支与安全红线）· [门禁报错对照](skills/design-diagram/references/gate-findings.md) |
| 配宿主级全局规则 | `skills/agentflow/references/hosts.md`（三层分工、托管块、宿主矩阵）· `skills/agentflow/templates/host/global-rules.md`（规则正文） |
| 抄模板（提案/规格/方案/计划） | `skills/agentflow/templates/README.md`（含目标仓工程基线的可复制骨架） |
| 查计划形态与看板约定 | `docs/features/README.md`（批次目录结构、计划形态） |
| 看设计、指南与事实 | `docs/`：`quickstart.md`（5 分钟上手）、`system-guide.md`（体系指南）、`design-decisions.md`（设计决策）、`design-decisions-archive.md`（已裁撤项的历史设计与恢复清单）、`host-platform-facts.md`（宿主事实） |
| 构建、安装与检查 | [打包和安装指南](packaging/README.md) |
| 目标仓侧工具（init 安装 / 立项 / 评审快照） | `skills/agentflow/scripts/`：[init_workspace.py](skills/agentflow/scripts/init_workspace.py)（多宿主安全安装）· [new_feature.py](skills/agentflow/scripts/new_feature.py)（一键立项）· [review_snapshot.py](skills/agentflow/scripts/review_snapshot.py)（评审快照） |
| 模板与工作流改进 | [批次入口](docs/features/feature-2026-11-23-模板与工作流改进/README.md) · [执行计划](docs/features/feature-2026-11-23-模板与工作流改进/plan/PLAN-2026-11-23-WORKFLOW-QUALITY.md)；提案、规格及设计在批次入口 |
| 0.41.0 审计修复与历史重放 | [批次入口及浏览器重放](docs/features/feature-2026-11-05-审计修复/README.md) · [交付决策](docs/features/feature-2026-11-05-审计修复/decision.md) |
| 看每个版本为何变更 | [`CHANGELOG.md`](CHANGELOG.md) |

## 维护纪律

- 文档的新增、移动与删除必须同步维护本索引。
- 新增顶层目录或新的文档类型须先经用户确认，不得自动创建。
- 相对链接带 `.md` 后缀；文档正文不写会话角色词与裸代号（判据见 `skills/agentflow/references/document-chain.md` 的表达纪律节）。

## 非权威工作区（不纳入仓内结构）

- `.workbuddy/`（已被 `.gitignore` 排除）：本机调试 / 复盘 / 记忆的**草料区**，内容不入版本库、不进入任何交付物；其中结论若可复用，应落回 `docs/` 后才算现行记录。活文档面（索引、README、AGENTS）不引用其路径。

## 版本与基线

版本只在 manifest（`plugin.json` / `marketplace.json` / 各宿主插件清单）与 [`CHANGELOG.md`](CHANGELOG.md) 中声明一次。本仓库的方法演进历史与每个版本的改动以 CHANGELOG 为准；自 2026-11-04 起以清理后的精简基线重新计数，不再回溯更早的批次目录与评测报告。
