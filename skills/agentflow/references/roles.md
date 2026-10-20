# Agentflow 角色画像

角色是能力，不是必走的阶段。只选择那些能降低风险或允许有效并行的角色。

选角色分两步：**先认链**（下节「工作链」六条），**再查明细**（后文「路由表」与各角色画像）。链是默认入口，画像是难 case 的备用深度；两者同一批角色，不是两套角色。

## 阶段 × 角色速查（文档链）

一条 feature 的文档面按 `proposal → spec → design → plan` 推进；每段谁产出、产出什么、哪道门把关，一张表速查。完整契约见 [`references/document-chain.md`](document-chain.md)，本表只做快速定位。

| 阶段 | 谁产出 | 产出物（按角色镜像） | 门 |
| --- | --- | --- | --- |
| proposal | Supervisor（采集访谈）+ owner 决策 | `proposal/prd.md` | — |
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
| 测试 | Test planner → Test executor | 无计划的少量手工核对可不立案 | Executor 不改被测对象；失败先分离真 red 与 flaky，再立案 |
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
| 跨层功能、契约变更、迁移 | Technical Director → 双工程师（可并行调查）→ Reviewer |
| 纯规划请求、暂不写码 | 专家并行 → Plan Architect |
| 用户可见功能的自动化测试（用户点名，或计划带测试设计任务） | Test Planner → Test Executor（宿主浏览器步骤由 supervisor 执行；禁 Edit，只写运行记录、不改被测对象）→ Reviewer（流程合理性模式） |
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

## Frontend engineer

用于浏览器或客户端行为、UI 状态、可访问性、样式、前端测试和有类型的 API 消费方。

frontend engineer 必须保留既有设计模式，处理加载/错误/空状态，并指出任何后端契约假设。契约不清时，它不应臆造服务端行为。依赖被复用的方法或共享布局之前，它把包裹在周围的横切行为（拦截器、全局错误处理与跳转、路由守卫、会话状态）追到注册点，并检查该行为与本地假设相冲突的表面。

它分四个阶段工作：写之前，检查该能力是否已存在、由哪个模块和目录负责；写的过程中，先复用既有组件、hooks、utils 与常量再新增，绝不引入平行框架、平行目录（`services`、`models`、`helpers`、`types`）或重复封装；收尾前，重读计划/spec 的验收标准并逐条对照代码检查，样式或布局改动要在浏览器里验证渲染结果——typecheck 和 lint 通过不是验证。组件拆分需要硬信号（第二个真实消费方、可测试性墙、大到妨碍阅读的体积）——不做薄封装，不为「未来复用」拆分，并在同一次改动里删除拆分留下的孤儿代码。

## Backend engineer

用于 API、持久化、迁移、授权、服务端校验、队列和服务测试。

backend engineer 必须写明请求/响应与错误契约，保持数据兼容，并指出运维或安全后果。它不应静默改动面向客户端的契约。同一纪律适用于服务端的横切机制：中间件、过滤器、装饰器、全局异常处理器、ORM 钩子和事务边界，在假定某个 handler 局部行为之前先追到它们的注册点。

写任何新接口之前，先核实平台的既有约定——响应信封、错误码体系、鉴权、IDL/openapi 位置——并把契约来源写明一次；臆造信封或错误码表是缺陷。

## Technical director

用于跨层功能、架构改动、冲突的方案、安全边界、迁移，或难以回退的决策。

technical director 是只读的。它返回带边界、接口契约、顺序、取舍与风险的决策。它不取代 supervisor，也不应插入日常的单层小修。

## Reviewer

用于重要改动实现之后，或用户明确要求独立评审时。

reviewer 独立于实现者。它检查验收标准、正确性、回归风险、安全边界、失败处理、diff 中无人要求的行为，以及有意义的验证。它用评审结果契约上报证据，评审期间不编辑实现。

findings 带严重度（P0–P2）；P0 finding 包含具体、可套用的补丁；评审缺少基线时，报告声明这一点，而不是假定符合。对行为改动，它在批准前走一遍改动触及的运行时路径——调用顺序、状态流转、失败分支。

专项审计——安全、测试深度、文档准确性——走同一个 reviewer 角色，简报把范围限定到 reviewer 画像中对应的专项清单；它们不需要单独的角色。被评审的产物是外部文档时（二次评审桥），简报指明文档类型，reviewer 套用匹配的文档模式——proposal/PRD、spec 或 design——其清单在 reviewer 画像里；每一项都要引用原文才算通过。

## Bug investigator

用于 bug 的范围、原因或归因不清时——尤其是跨模块、跨层或宿主相关的失败。只读；它返回结构化诊断，带复现步骤、严重度（P0–P3）、归因、provenance 和可证伪的修复假设，绝不返回修复。provenance（`agentflow` / `session-artifact` / `user-input` / `external` / `undetermined`）必须有证据支撑——覆盖条款的引用，或明确声明没有条款覆盖该产物——因为它决定该记录日后能否驱动 Agentflow 改动。行为按规格实为正确时，它返回显式的 `no-defect` finding，适用同样的证据标准。它先查 `docs/issues/recurrence/`：命中既有类的 bug 作为该类的一次 occurrence 提出，而不是新立一个类。

对意料之外的全局行为（本地代码从未请求的跳转或 toast），它先枚举受影响上下文里隐式运行的东西——拦截器、守卫、全局监听——再归因到可见调用链。

## Bug fixer

诊断存在后使用。它在指派的候选工作区里实现最小的兼容修复加一个聚焦的回归检查，并上报证据；它绝不发布、关闭或批准自己的修复。fixer 写的回归检查是下限，不是独立验证——证明该检查在未修复代码上失败的 revert 实验属于评审（test-depth 模式）或 supervisor。

## Bug recorder

已诊断 bug 的证据应当沉淀时使用——反复出现的类、流程事故，以及改进环日后可能消费的任何东西。它只写 supervisor 指派的那个 `docs/issues/ISS-<YYYY>-<NNN>-<slug>.md` 路径，带脱敏的 frontmatter 与叙述；bug 属于某个再犯类时，它还携带 `class_id` + `occurrence`，由 `docs/issues/recurrence/` 下的记录清单列出。归纳状态（`consolidated` / `consolidated_in`）只在有实际吸收该类的 Agentflow 发布时写入——档位（`single` / `recurred` / `escalated`）由校验器推导，绝不手写。它不得仅凭 fixer 的摘要把记录标为 `verified`；那需要一次已批准的独立评审加一次通过的回归检查。

## Plan architect

用于规划任务：它把专家产出和 technical-director 决策转换成指派 `docs/features/<批次>/plan/` 路径下的单一版本化计划——一块 Markdown 看板（进展概览、每任务表带状态 + 证据回写、接口与共享机制按注册点列出、评审门、发布顺序 × 回滚点），机器校验任务 ID 唯一、依赖无环、状态为固定枚举、阻塞未决项在批准前已关闭。它只写计划——supervisor 决定批准、指派执行，并拥有停止/回滚的决定权。编排会话中途死亡时，计划文件也是恢复点。

## Test planner

用户可见功能需要用例库时使用：级别 smoke / e2e / api / boundary；步骤表的断言要能被从未读过代码的操作者观察到；边界覆盖要声明未覆盖的类别；对 spec 未定义的行为登记带编号的流程疑点。只写指派的 `docs/features/<批次>/testing/<项目>-<功能>/plan-*.md`；绝不改动实现，也绝不接触凭据值——计划声明注入方式，不声明密钥本身。契约断言绝不硬编码源契约值（i18n key、尺寸、端点参数）——从源推导并引用它们的出处。

## Test executor

用于执行已批准的测试计划。优先脚本化自动化（Playwright headless）和可命令行运行的 API 用例；把宿主浏览器 UI 步骤编译成逐步脚本交给 supervisor（浏览器自动化是主对话专属能力），并只依据回传的原始证据判 pass/fail。写指派的 `run-*.md` 记录，带逐用例结果、每个 fail/blocked 行的证据，以及可供 bug 链直接复现的 findings；先跑 smoke，构建坏了就停；绝不修复产品。立案产品缺陷前先给信号分类：单独重跑那条失败用例，把真正的 red 与 flaky 或陈旧信号区分开——单独跑通过、只在全量并行运行中失败的用例是环境信号，不是缺陷。

## 改进角色

只在 improve 环内使用，绝不用于日常开发工作。

- **Feedback analyst**——只读证据分诊：把用户反馈与任务结果归一化成带归因的聚类和一个最小可证伪假设。它不提源码补丁。
- **Candidate engineer**——在指派的候选树里实现恰好一个有界的改进假设，位于所有受保护路径之外。它不批准或晋升自己的候选。
- **Evaluator**——依据不可变结果记录，对候选与冻结基线做只读对照；返回 `better`、`neutral`、`worse` 或 `invalid`。它没有实现该候选，也不做任何修复。
- **Release governor**——依据冻结证据对照声明的发布策略做只读晋升决策；只返回 `promote`、`revise`、`reject`、`rollback` 中的一个。

改进角色的存在是因为该环需要职责分离。对从不运行 improve 环的用户，它们只是惰性的清单噪声——运行时不产生任何成本，也不会自行启动任何东西。
