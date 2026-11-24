# Agentflow 角色路由

> **加载者**：`skills/agentflow/SKILL.md` 路由「角色路由」行 + 第 3/4 步；各 `agents/*.md` 反向声明自己的归属。选角色与交接时读。

角色是能力，不是必走的阶段。只选择那些能降低风险或允许有效并行的角色。

选角色分两步：**先认链**（下节「工作链」五条），**再查明细**（后文「路由表」与实际角色文件）。链是默认入口，角色文件是难 case 的备用深度；两者同一批角色，不是两套角色。

## 阶段 × 角色速查（文档链） <span id="阶段--角色速查文档链"></span><span id="阶段-角色速查文档链"></span>

一条 feature 的文档面按 `proposal → spec → design → plan` 推进；每段谁产出、产出什么、哪道门把关，一张表速查。完整契约见 [`references/document-chain.md`](document-chain.md)，本表只做快速定位。

| 阶段 | 谁产出 | 产出物（按角色镜像） | 门 |
| --- | --- | --- | --- |
| 提案（proposal） | 主审收集范围、现状与取舍，用户决定产品问题 | 目标、非目标、影响面、验收方向与未决项 | Reviewer 核对边界与可判定的目标 |
| 规格（spec） | 主审组织；前后端提供事实和契约，Test Planner 提供验收 | 已确认行为、失败路径、字段和验收点 | Reviewer 对照提案和可执行验收 |
| 设计（design） | Technical Director 给架构决策；前后端工程师和 Test Planner 补各自设计内容 | 所选轨道的设计、接口/数据、失败恢复与测试策略 | Reviewer 核对规格、风险、回退和引用 |
| 计划（plan） | Plan Architect 把已定结论转成可执行任务；主审负责接受 | 真实依赖、状态、检查、回退与可观察成果 | Reviewer 核对冻结设计、依赖和可执行性；计划作者之外的主审接受 |

三轨职责一句话：**Backend engineer** 定对象模型、状态机、接口契约、DDL；**Frontend engineer**
定页面规格、文件落点、类型契约、字段映射；**QA（Test planner）** 定验收口径、边界矩阵、用例库。
`spec/ui` 与 `design/ui` 是可选扩展，启用与否在 feature README 元信息声明一行。

本表用于 full，QA 必需，BE/FE/UI 按实际影响选轨；light 的同义内容留在唯一 README。按[文档交付链](document-chain.md)映射实际载体。角色默认返回分工范围内的建议；需直接编辑一份文档时，在简报中明确其准确文件或章节以及写入范围。Technical Director 与 Reviewer 保持只读。无独立 Reviewer 时按[能力分级](contracts.md#评审能力分级)登记并补审。

## 工作链（默认入口）

从下表选择适用的链及必要角色。仓库审核等单独工作按主技能的专项入口选择核查方式。

| 链 | 默认序列 | 默认可省 | 不可省的一步（硬边界，跳过即改变结论效力） |
| --- | --- | --- | --- |
| 实现 | 按层选择工程师或由 Supervisor 实现 → 必需独审 | 琐碎静态改动只做适用自检；light 可不派工程师 | light 行为与 full/material 需要独审，与作者身份无关；L0 如实 partial |
| 缺陷 | Bug investigator → Bug fixer → Reviewer → Bug recorder | 已复现的小 bug 可合并诊断与记录环节 | Fixer 不得批准或关闭自己的修复；Recorder 不得凭 Fixer 摘要标 `verified` |
| 测试 | Test planner → Test executor → Reviewer（流程合理性模式） | 无计划的少量手工核对可不立案 | Executor 不改被测对象；失败先分离真 red 与 flaky，再立案 |
| 规划 | Technical Director → Plan Architect | 无架构决策时省略 TD；有界计划可由主审起草 | 作者之外按计划状态接受；主审负责调度，回滚依现有权限 |
| 独立评审 | Reviewer（单点） | 无 | 评审期间不编辑实现、不运行受候选控制的命令；无基线须声明，不得假定符合 |

选链的顺序与判据：

1. **先按风险选材料与独审**（唯一判据见[文档档位](document-chain.md#文档档位)）。不按作者身份、文件数量或有无 UI 另立阈值；角色只在有具体工作时启用。
2. **需要诊断还是需要决策**：要"哪里坏了、为什么"走缺陷链，要"边界怎么划、接口谁定"走规划链。
3. **跨链串联**：测试执行出现失败或覆盖缺口，从测试链转入缺陷链；实现过程中出现契约冲突，先从实现链升到规划链取 TD 决策，再回到实现链——升级是一次指派，不是在实现里顺手决定。
4. **只取链上真正有工作的角色**：链是默认序列，不是必须全员到场的仪式；省掉哪一步要能说出它为什么没有工作，而不是因为它麻烦。

## 路由表

按任务形态选角色，不按名字的资历。完整清单是为难 case 准备的；大多数任务只用一两行。

| 任务形态 | 启用的角色 |
| --- | --- |
| 琐碎静态小改 | Supervisor 做内容与适用静态检查；不机械启动角色 |
| 单层低风险行为、复现明确 | Supervisor 或一名工程师实现 + 独立 Reviewer；light 材料集中 README |
| 有界范围的前端或后端实现 | 按风险选一名工程师与必要独审，不因 worker 作者而免审 |
| 用户行为事件的新增/修改、事件采集端点、事件表结构或看板聚合口径变更 | 工程师（按 `design/fe` 事件契约实现并自验 payload）+ Reviewer（埋点专项，清单见 [`telemetry.md`](telemetry.md)）；三条运行时判据只认端到端路径证据或网络日志 |
| 跨层功能、契约变更、迁移 | Technical Director → 双工程师（可并行调查）→ Reviewer |
| 纯规划请求、暂不写码 | 专家并行 → Plan Architect |
| 行为变更的目标验证、独立自动化测试或遗留补测 | Test Planner → Test Executor（宿主浏览器步骤由 supervisor 执行；禁 Edit，只写运行记录、不改被测对象）→ Reviewer（流程合理性模式） |
| 测试执行产出失败或覆盖缺口 | Executor 证据 → bug 链路（Investigator → Fixer → Reviewer → Recorder） |
| 重要、不确定、反复或跨层的 bug | Bug Investigator → Bug Fixer → Reviewer → Bug Recorder |
| 已有验证复现的小 bug | Supervisor 自己做诊断/修复/检查；Supervisor 亲写的改动独立 Reviewer 门仍然强制；需要沉淀时再记录 |
| 评审按另一系统规则编写的文档 | 主审冻结并映射材料 + Reviewer；处理和授权落点见[外部文档评审](repo-audit.md#外部文档二次评审另一套规则下产出的文档) |
| 任务本身是带解冲突的分支合并 | Supervisor 解决并验证 + 独立 Reviewer（supervisor 亲解代码冲突时强制；报完成前留存合并后确定性检查的原始输出） |

> 「专家」指宿主按任务域提供的领域专家角色（专家中心 / 专家市场按域选用）：它产出建议与判断依据，不写计划、不执行改动；上表「专家并行」即按任务域同时启用多名专家，交汇结论交 Plan Architect。

## Supervisor

当前宿主的主任务就是 supervisor。它负责接案、分解、权限、集成、最终验证和最终决策。它可以实现小的粘合改动，但必须检查委派工作而不是信任摘要，并按风险执行同一独审要求，不因谁写而增免。

supervisor 决定是否委派，保持范围不重叠，并停止不再产出新证据的循环。

分析、状态或审阅报告交付前按[表达纪律](document-chain.md#表达纪律)核对内容、引用和适用检查。用户要求独立复核或报告将作为高风险决定的证据时，安排独立 Reviewer。

前后端工程师保持不同写范围。三个只读角色按输出分工：调查员返回诊断，技术负责人返回架构决策，Reviewer 返回独立评审。共享已核查的证据，避免让不同角色重复生成同一正文。

## 角色文件是详细职责权威

本表只导航，不再复制角色提示词。产物所有权、工具限制、专项深度和预算以实际文件为准；实现方法统一读取[执行与验证](execution.md)。

**记录位置**：主审按目标仓实际约定，指派准确的功能、计划、测试、缺陷、评审与发布记录位置。角色文档的示例路径相对于已确认的功能或缺陷目录。实现角色只写分配范围；需要更新记录时回交相应角色或主审。

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

遗留补测是测试链的盘点模式，继续使用 Test planner / Test executor / Reviewer，不创建第七条链或新的执行角色。补测不自动授权生产修复；依赖分流、原生报告和覆盖复核按执行协议处理。
