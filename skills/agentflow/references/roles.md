# Agentflow 角色路由

角色是能力，不是必走的阶段。只选择那些能降低风险或允许有效并行的角色。

选角色分两步：**先认链**（下节「工作链」六条），**再查明细**（后文「路由表」与实际角色文件）。链是默认入口，角色文件是难 case 的备用深度；两者同一批角色，不是两套角色。

## 阶段 × 角色速查（文档链）

一条 feature 的文档面按 `proposal → spec → design → plan` 推进；每段谁产出、产出什么、哪道门把关，一张表速查。完整契约见 [`references/document-chain.md`](document-chain.md)，本表只做快速定位。

| 阶段 | 谁产出 | 产出物（按角色镜像） | 门 |
| --- | --- | --- | --- |
| proposal | Supervisor（采集访谈）+ owner 决策 | `proposal/proposal.md` | — |
| spec | Supervisor 起草或各角色 | `spec/{be,fe,qa,ui}/` | Spec 反审门（spec §0 反审 proposal） |
| design | Technical director（接口）+ 各角色 | `design/{be,fe,qa,ui}/` | 需求评审门 → Design 评审门（Reviewer 独立） |
| plan | Plan architect | `plan/<plan_id>.md`（本仓约定，文件名 = `plan_id`；目标仓无自有约定时用 `plan/execution.md`） | Plan 前置条件（plan 引用已冻结的 design 结论） |

三轨职责一句话：**Backend engineer** 定对象模型、状态机、接口契约、DDL；**Frontend engineer**
定页面规格、文件落点、类型契约、字段映射；**QA（Test planner）** 定验收口径、边界矩阵、用例库。
`spec/ui` 与 `design/ui` 是可选扩展，启用与否在 feature README 元信息声明一行。

判定各阶段是否齐全看批次 README 的段落映射表（落点非空且非「—」的段落可缺失，其余段落
齐全）；plan 的 `## 分支策略` 节与 design 的图/形态要求（`spec/<角色>/` 或 `design/<角色>/`
任一含 `.md` 即触发）是 linter 会判失败的硬项。**链路收口通读**不是 plan 阶段的门：它定义在
[`document-chain.md`](document-chain.md) 的门清单第 6 条，是链尾门——最后一份文档落地、宣布
完成之前，由非作者通读整条链；门 6 是它的定义处，此处只作引用，不重复定义。

## 工作链（默认入口）

任务是先落到一条链上，再从链里取角色。六条链覆盖全部任务形态，链与链的区别是**输入契约**，不是资历；链外没有第七种入口，「专家并行」是链内的取证手段，不是独立的链。

| 链 | 默认序列 | 默认可省 | 不可省的一步（硬边界，跳过即改变结论效力） |
| --- | --- | --- | --- |
| 实现 | 工程师（frontend / backend，按层选一或并行）→ Reviewer | 单层小修可只留 Supervisor | 独立评审门：Supervisor 亲写的改动也强制，不得自免 |
| 缺陷 | Bug investigator → Bug fixer → Reviewer → Bug recorder | 已复现的小 bug 可合并诊断与记录环节 | Fixer 不得批准或关闭自己的修复；Recorder 不得凭 Fixer 摘要标 `verified` |
| 测试 | Test planner → Test executor → Reviewer（流程合理性模式） | 无计划的少量手工核对可不立案 | Executor 不改被测对象；失败先分离真 red 与 flaky，再立案 |
| 规划 | Technical director → Plan architect | 无跨层或契约决策时可跳过 TD | 计划只由 Plan architect 写；批准、指派执行与回滚决定归 Supervisor |
| 改进 | Feedback analyst → Candidate engineer → Evaluator → Release governor | 无（四步各自承担一项独立性） | Candidate 不自评、不自放行；Evaluator 与 Release governor 全程只读 |
| 独立评审 | Reviewer（单点） | 无 | 评审期间不编辑实现、不运行受候选控制的命令；无基线须声明，不得假定符合 |

选链的顺序与判据：

1. **先判 material**（定义见 [`../SKILL.md`](../SKILL.md) 的判断词可判定定义节）。小改动仍只留在 Supervisor 手里，但独立评审门不因此豁免。
2. **需要诊断还是需要决策**：要"哪里坏了、为什么"走缺陷链，要"边界怎么划、接口谁定"走规划链。
3. **跨链串联**：测试执行出现失败或覆盖缺口，从测试链转入缺陷链；实现过程中出现契约冲突，先从实现链升到规划链取 TD 决策，再回到实现链——升级是一次指派，不是在实现里顺手决定。
4. **只取链上真正有工作的角色**：链是默认序列，不是必须全员到场的仪式；省掉哪一步要能说出它为什么没有工作，而不是因为它麻烦。

## 路由表

按任务形态选角色，不按名字的资历。完整清单是为难 case 准备的；大多数任务只用一两行。

| 任务形态 | 启用的角色 |
| --- | --- |
| 单层小修、复现明确 | Supervisor 自己做；任何 Supervisor 亲写的改动仍适用独立 Reviewer 门 |
| 有界范围的前端或后端实现 | 一名工程师 + 改动重要时启用 Reviewer |
| 用户行为事件的新增/修改、事件采集端点、事件表结构或看板聚合口径变更 | 工程师（按 `design/fe` 事件契约实现并自验 payload）+ Reviewer（埋点专项，清单见 [`telemetry.md`](telemetry.md)）；三条运行时判据只认端到端路径证据或网络日志 |
| 跨层功能、契约变更、迁移 | Technical Director → 双工程师（可并行调查）→ Reviewer |
| 纯规划请求、暂不写码 | 专家并行 → Plan Architect |
| 行为变更的目标验证、独立自动化测试或遗留补测 | Test Planner → Test Executor（宿主浏览器步骤由 supervisor 执行；禁 Edit，只写运行记录、不改被测对象）→ Reviewer（流程合理性模式） |
| 测试执行产出失败或覆盖缺口 | Executor 证据 → bug 链路（Investigator → Fixer → Reviewer → Recorder） |
| 重要、不确定、反复或跨层的 bug | Bug Investigator → Bug Fixer → Reviewer → Bug Recorder |
| 已有验证复现的小 bug | Supervisor 自己做诊断/修复/检查；Supervisor 亲写的改动独立 Reviewer 门仍然强制；需要沉淀时再记录 |
| 评审按另一系统规则编写的文档 | Supervisor（归档 + 评审记录）+ Reviewer；findings 落成带 `provenance: external` 的 bug 记录 |
| 任务本身是带解冲突的分支合并 | Supervisor 解决并验证 + 独立 Reviewer（supervisor 亲解代码冲突时强制；报完成前留存合并后确定性检查的原始输出） |
| 插件/角色指令改进 | Feedback Analyst → Candidate Engineer → Evaluator → Release Governor |

> 「专家」指宿主按任务域提供的领域专家角色（专家中心 / 专家市场按域选用）：它产出建议与判断依据，不写计划、不执行改动；上表「专家并行」即按任务域同时启用多名专家，交汇结论交 Plan Architect。

## Supervisor

当前宿主的主任务就是 supervisor。它负责接案、分解、权限、集成、最终验证和最终决策。它可以实现小的粘合改动，但必须检查委派出去的工作而不是信任摘要，并且不得豁免自己亲写代码的独立评审门。

supervisor 决定是否委派，保持范围不重叠，并停止不再产出新证据的循环。

会话中交给用户的独立书面交付物（分析报告、状态报告——任何文档链之外的东西）遵循 document-chain.md 表达纪律（术语）条款——包括代号裸用与模式词分域两种形态：先对照该条款做交付前自检，并跑机器检查 `python3 tools/lab/doc_chain.py --file <路径>`，之后才交付；交付物带重要结论，或用户明确在盯措辞质量时，指派独立 reviewer。

### 收敛注记

bug investigator、feedback analyst、technical director 与 evaluator 与 reviewer 画像同构（只读、证据进、结构化结论出），且**有意不**收敛进它：四者的输入契约与产出不同——分别是带复现与归因的诊断、归一化证据聚类、带边界与排序的架构决策、对不可变结果记录的四值对照判定（`better`/`neutral`/`worse`/`invalid`）——折成 reviewer 的模式会掩盖简报必须满足哪个输入契约。它们保持独立角色文件，是一个显式的过渡态；合并或重塑它们会改动公开角色面，属产品决策，不作为常规编辑执行。

2026-10-19 拍板（Q-02 方案 D）：**角色文件数量不合并**——收敛发生在「工作链」入口层，不在角色文件层。理由有两条：一是默认路径已经按需加载，慢的不是加载而是"从条目里现拼流程"；二是 14 个角色里 2 个在 `protected-paths.txt` 的保护面内，另有四组独立性（候选不自评、候选不自放行、修复者不写验收记录、测试设计与执行分离）会因合并而消失。唯一仍待议的合并对是 frontend / backend engineer（同属实现层、按层选一），是否合并由角色边界测试（`docs/features/feature-2026-10-13-质量提升/testing/agentflows-role-boundary/` 的 28 例）的通过率与"同场景判定是否可区分"决定；evaluator 与 release-governor 不进入合并候选。

## 角色文件是详细职责权威

本表只导航，不再复制角色提示词。产物所有权、工具限制、专项深度和预算以实际文件为准；实现方法统一读取[执行与验证](execution.md)。

| 角色 | 何时读取 |
| --- | --- |
| [Frontend engineer](../../../agents/frontend-engineer.md) | 页面、状态、样式、可访问性与客户端接口 |
| [Backend engineer](../../../agents/backend-engineer.md) | API、持久化、授权、迁移与服务边界 |
| [Technical director](../../../agents/technical-director.md) | 高成本接口、权限、数据、时序或难回退选择 |
| [Plan architect](../../../agents/plan-architect.md) | 把已审设计转成执行计划，不自行批准 |
| [Test planner](../../../agents/test-planner.md) | 验收映射、用例库、补测盘点及边界 |
| [Test executor](../../../agents/test-executor.md) | 执行已定用例，只写实际结果与证据 |
| [Reviewer](../../../agents/reviewer.md) | 独立评审、需求符合度和断言/覆盖质量 |
| [Bug investigator](../../../agents/bug-investigator.md) | 复现、归因与可证伪诊断 |
| [Bug fixer](../../../agents/bug-fixer.md) | 有诊断后的修复和同路径回归 |
| [Bug recorder](../../../agents/bug-recorder.md) | 经验证后的缺陷记录，不凭修复摘要关闭 |
| [Feedback analyst](../../../agents/feedback-analyst.md) | 仅改进环的反馈归因 |
| [Candidate engineer](../../../agents/candidate-engineer.md) | 仅实现有界改进候选 |
| [Evaluator](../../../agents/evaluator.md) | 只读评价候选证据 |
| [Release governor](../../../agents/release-governor.md) | 只读发布建议，最终授权仍归人 |

遗留补测是测试链的盘点模式，继续使用 Test planner / Test executor / Reviewer，不创建第七条链或新的执行角色。补测不自动授权生产修复；依赖分流、原生报告和覆盖复核按执行协议处理。
