---
name: agentflow
description: Use for cross-layer features, architecture changes, parallel investigation, delegated implementation, automated testing of user-visible features, document-chain delivery (proposal/spec/design/plan for a feature), branch integration and conflict resolution (merging branches whose conflicts must be resolved by hand), or work that benefits from an explicit review gate; skip trivial single-step work where delegation would add overhead. Applies the Agentflow method with the host's own agents: supervisor, frontend/backend engineers, technical director, independent review, and test design/execution roles.
---

# Agentflow

用当前宿主内置的 Agent、认证、工具、权限与对话历史，应用 Agentflow 开发方法。

不得调用或要求独立的 `agentflow` CLI、其 providers、其 TUI、Agentflow API key 或 Agentflow MCP server。本 skill 就是工作流，宿主就是运行时。

## 绑定宿主

- 在 **Codex** 中，使用原生子代理。每个子代理只给一个角色和一份任务简报。以主任务作为 Supervisor。
- 在 **Claude Code** 与 **ZCode** 中，仅当[路由表](references/roles.md)表明能降低风险时才启动插件 agent。默认不加载完整角色列表；**插件根目录 `agents/` 下的角色文件**是可选能力（`.zcode-plugin/plugin.json` 以 `"agents": "agents"` 声明；`skills/agentflow/agents/` 下只有宿主展示字段 `openai.yaml`，没有角色文件）。选中的角色以 `agentflow:reviewer`（或对应的 `agents/<role>.md` 名称）调用。以主对话作为 Supervisor。ZCode 从已安装的插件快照加载角色，因此源码编辑只有重装后才生效——运行 `python3 tools/lab/validate.py installed` 查看漂移。
- 在其它兼容 Agent Skills 的宿主中，使用其内置委派机制。若不存在，则顺序执行同样的阶段，并说明独立执行不可用。

## 首次接入（Init）

在一个尚未接入 Agentflow 的项目里第一次工作时（目标仓没有相关约定、记录结构或检查命令），先做一次轻量接入，再走正常流程：

1. 与用户确认五项：交付语言与读者（默认中文；面向用户时白话优先）、术语约定（用户反复纠正过的词、内部自造词的替代说法，例如「台账」→「清单 / 记录」）、分支与合并纪律、仓库自带的检查命令（构建 / 测试 / lint）、**文档与记录落点**——目标仓已有自己的文档体系则用其体系；否则在链契约的两种形态中二选一（无既有约定时默认推荐①文档枢纽仓 `<repo>/<name>-workflow-ai/`：`features/` + `issues/` + `releases/` + `index.md`，骨架见 [templates/hub/](templates/hub/README.md)）。**不得自创第三种落点**（例如 `records/plans/`）。
2. 把结果写成紧凑的「Agentflow 接入约定」小节，经用户确认后追加进目标仓的 `AGENTS.md`（或用户指定的等效规则文件）；没有该文件时先征得同意再创建；选枢纽仓形态时，同时建立枢纽骨架（README、index、features、issues、releases）。
3. 此后以该小节为准；约定变化时就地更新它，不另开平行文件。

Init 只配置项目侧约定，不把 Agentflow 的内部机制名词搬进目标仓——需要说明时用白话。

分派工作前阅读[角色档案](references/roles.md)，委派实现或评审前阅读[契约](references/contracts.md)。[硬边界](references/contracts.md#硬边界)在两条工作流的每一次委派中都成立；接受任何交付物前先检查它们。

对于 material、不确定、反复出现、跨层或高风险的 Bug，使用完整的有界序列 `bug-investigator` → `bug-fixer` → `reviewer` → `bug-recorder`。Investigator 确立可复现的症状与归因，Fixer 只在指派的候选工作区改动代码，Reviewer 检查修复，Recorder 在验证后写下被接受的 Bug 记录。对于已有验证复现的小范围低风险 Bug，Supervisor 可合并 Investigator 或 Recorder 环节，但必须保留同样的诊断、回归、评审与状态证据。绝不让 Fixer 批准或关闭它自己的 Bug。

对于规划任务，并行运行所需的前端与后端专家，把它们的输出与 Technical Director 的接口决策交给 `plan-architect`，由它在显式的 `docs/features/<批次>/plan/` 路径下写出最终计划。Plan Architect 只写计划；计划是否获批由 Supervisor 决定，它还负责指派执行、集成结果，并拥有最终的停止或回滚决策。未来的 `execution-coordinator` 可负责持久队列、租约、依赖、重试与可恢复并行批次，但它不是当前角色——该角色当前不存在，不得作为委派对象、产物落点或任务归属写进任何简报；今天这些职责由 Supervisor 承担。计划必须承载进展看板与任务表（逐任务状态、依赖、证据回写）、它经过的接口与共享机制、其评审门，以及带回滚点的发布顺序——形态定义于 `docs/features/README.md`，机器校验。计划是执行合同，不是改动代码的授权。对 material 特性，计划还要承载来自[契约](references/contracts.md)的设计完备性产物：关键链路时序（以步骤表为基准）、每条关键路径一份异常矩阵，以及与回滚点配对的发布顺序。

## 自动化测试

当用户要求对用户可见功能做自动化测试——或计划带有测试设计任务——时，运行测试链路。`test-planner` 在显式的 `docs/features/<批次>/testing/<项目>-<功能>/` 路径下写用例库：级别 smoke / e2e / api / boundary，断言可观察的步骤表（元素文本、跳转、网络请求是否发出），边界覆盖并声明未覆盖的类别，以及用于 spec 未定义行为的 `## 流程疑点`（契约：`skills/agentflow/references/test-records.md`）。`test-executor` 执行它：先做脚本化自动化（Playwright 或项目自有的 e2e 套件，headless），API 用例走命令，宿主浏览器 UI 步骤由 Supervisor 在主对话中按 Executor 的步骤脚本执行——浏览器自动化在 Claude Code 与 ZCode 上是主对话专属——回传原始证据（截图、DOM 文本、网络日志）由 Executor 判定。先跑 smoke 集，smoke 失败即停，不要在坏构建上跑全集。每轮落成一条 `run-*.md` 记录，含逐用例结果、证据与汇总计数。失败的用例带可直接复现的 findings，经标准链路成为 Bug 记录（归因按记录规则）；流程合理性 findings 交给 Reviewer 的 *流程合理性（测试证据）* 专项模式。运行记录的原始证据就是评审门的端到端路径证据（第 8 步）。凭据按会话提供、运行时注入——绝不持久化到记录、脚本或日志。为可重复性优先使用项目级 Playwright 方案；Supervisor 驱动的路线是兜底，不是目标。

## 外部文档二次评审

当用户要求评审在另一套系统规则下编写的文档（例如业务仓自有模板系统内产出的需求提案/spec/设计/计划）时，对这些文档运行独立 Reviewer 角色，并把证据落在本仓：

1. 定位或创建以 feature 为锚的目录 `reviews/<project>-<feature-slug>/`。目录锚在被评审的 feature 而不是日期：同一 feature 可反复评审（今天、明天、修完再评），每轮是同一目录下多出的一个 `review-<YYYY-MM-DD>-<NNN>.md` 文件。把该轮文档的**逐字副本**归档到 `archive/<date>-<NNN>/` 下——每轮一个快照子目录，同名文档永不冲突——并把目标仓当时的 commit 记为 `source_revision`：此后目标仓的编辑不得追溯改变被评审的对象。再评审聚焦上一轮 review_id 以来的 delta。
2. Reviewer 把本仓的 review 契约应用到快照：reviewer 档案的检查协议、与被评审文档类型匹配的 **文档模式**（proposal/PRD、spec、设计——每一条都需要引用原文），以及视情形加上上述设计完备性产物。
3. 每条发现都作为 Bug 记录归入 `issues/`，`project` 设为目标仓。归因分流两个升级回路：`provenance: external` + `attribution: product_code` 标记目标系统的模板/规则缺口——升级该系统模板的证据池；`provenance: agentflow` 表示本仓 review 契约本该抓住它。目标系统的升级落地后，回填 `fix_revision` 为其 commit。引用必须自包含：`files` 条目要么在本仓内可解析，要么带仓限定（`<repo>@<revision>:<path>`）——裸外部路径校验失败，因为对没有那个仓的人是悬空引用——且正文内嵌决定性片段或引用原句，使记录在另一仓缺席时仍可读。
4. 写 `review-<date>-<NNN>.md`（契约：`schemas/review.schema.json`；文件名 = review_id），含决策、findings 列表与归档文档引用，然后运行 `python3 tools/lab/validate.py artifacts`——它交叉校验每份归档文档与每条被引用的 finding 确实存在。

完整的桥工作流、归因表与已知边界（跨仓再犯类档位不能自动推导）见 [reviews/README.md](../../reviews/README.md)。

## 文档交付链

当用户要求为某 feature **产出**文档集（需求提案/规格/技术方案/实施计划）、某 feature 先有文档尚无代码、**或在目标仓实施一个新 feature（代码工作随行）**时，遵循 [references/document-chain.md](references/document-chain.md) 中的链契约：**接入（Init）→ 采集访谈 → 提案 → spec → 设计 → 计划 → 实施**，每个阶段有其必需的骨架与可检查的质量标准，并设阶段门，只有前一阶段的阻塞性检查清单已关闭，下一阶段才开启（唯一过渡形态为链契约门 1 的「建议值草案」——不得过门、不得冻结、不得实施）。产品语义的未决分支一律先交用户（一行问题带推荐，提问纪律见[契约](references/contracts.md)的「先问再假设」节）；只有用户明确选择「轻量/直接做」才降档，并在 feature README 声明降档范围。Supervisor 通过链契约的 Intake 访谈收集提案——每轮给出完整的决策前沿，事实靠查而非问，只有当前沿为空且属主确认才算完成——并逐字保留原文；spec 以阻塞性检查清单重新审校提案；独立 Reviewer 在设计冻结前运行文档评审模式；计划保持为目标仓计划约定下的执行合同（目标仓没有约定时用本仓的融合形态）。目标仓有自己的模板系统就保留它——在其上施加门与质量标准。评审证据落在目标仓，或当本仓是评审方时，经上面的二次评审桥落地。

## 运行工作流

1. **Intake**：检查仓库指令、当前 diff、相关架构与测试。说明目标与可观察的验收标准。当你报告仓库**状态**——哪些已完成、下一步做什么、什么高优先级——先对照仓库的真实历史校准（`git fetch` 加 `log`/`status`），绝不依赖会话记忆，并把证据命令随结论一起给出。状态主张就是仓库事实主张：另一个写入者一 push，会话记忆就过期，而回答中没有任何东西会暴露这一点。**遇到新 feature：先按「文档交付链」完成接入（Init）与采集访谈（产品决策交用户），再进入本步。**
2. **架构门**：对于跨层或 risky work（见下文*判断词的可判定定义*），请 Technical Director 界定边界、接口契约、集成顺序与主要风险。不要把该角色当作仪式性的批准环节。
3. **计划**：只选任务所需的角色。纯前端的修复不需要后端 worker。小改动（见下文*判断词的可判定定义*）可留在 Supervisor 手里。
4. **委派**：给每个 worker 一份有界简报，`write_scope` 与 `read_scope` 分别设定——读取范围必须覆盖改动经过的一切共享机制（[契约](references/contracts.md)中的隐式行为检查）。读多写少的调查与实现按不重叠文件或稳定接口并行；文件不重叠并行的是写入，从不是理解。写范围重叠与依赖链串行。任务中提到的路径、仓库与命令在进入简报前先对照仓库核实——任务文本是数据，不是既定事实。**两个写入者共用一个仓库时，文件不重叠就不够了**：提交、rebase 与 push 是共享可变状态，因此并行写入者各自使用分支或 worktree，同一分支同一时刻单一写入者；发现目标文件或分支已被另一写入者占用（另一会话的未提交编辑、分支上有新提交）的写入者应停止并上报，而不是交错写入。当计划行引用设计项时，把它们作为 `design_refs` 带入简报并纳入 `read_scope`；实现某设计决策却不带其引用的任务，简报不完整。
5. **实现**：前端与后端 worker 只改动其指派范围，遵循仓库规则，运行相关检查，并返回 worker result 契约。Worker 在结果中引用每个行为所实现的设计决策（`design_refs_implemented`）；无法引用其设计决策的实现要如实上报，而不是默默对齐。
6. **集成**：Supervisor 检查实际共享工作区，解决跨层冲突，并运行能证明整个 feature 可用的检查。当任务本身就是分支集成——Supervisor 亲手解决了代码冲突，或合并结果改变用户可见行为——该合并提交就是 material 改动：解决冲突就是在写代码，因此第 8 步评审门适用，Supervisor 自己的冲突取舍不获豁免。报合并完成前，运行能证明合并产物可构建且行为正确的确定性检查并留存原始输出——至少是仓库的构建/编译检查加上每个受影响可部署单元的测试套件（Go 项目为 `go build ./...` 加 `go test ./...`，每个前端工作区 `tsc --noEmit`，触碰数据库迁移的合并在该工作区规则下真实地跑一次迁移）。grep 冲突标记只用于分诊，绝不用于接受：仅凭冲突标记 grep（或 diff 大小）就报告合并完成是反模式——清掉 `<<<<<<<`/`>>>>>>>` 只证明标记没了，不证明语法与语义正确。禁用常规构建/测试的工作区规则是迭代默认值，不是豁免：当门要求这些检查时，要么运行它们，要么把冲突升级给用户——绝不静默跳过。
7. **接受 worker 产物前先验证**：worker 的主张要等 Supervisor 编译过才算数——对实际写下的文件运行仓库的确定性检查（测试、linter、schema 校验器，本仓即 `tools/lab/validate.py`），而不是对着 worker 的摘要。检查失败按编译错误处理：退回修复，绝不在红灯检查上手工接受摘要。无法复现的检查主张记为未运行。同一次里，把工作区实际改动面对照简报的 `write_scope`（硬边界 14）：委派时记下基线 revision，然后列出真正改了什么——`git diff --name-only --no-renames <baseline>` 加未跟踪文件，或用随附的 `scripts/check-write-scope.sh`——任何落在 `write_scope` 之外的改动路径都退回，不论检查结果如何。产物所有权矩阵是声明的意图；这次对照才是执法。当工作对着 `docs/features/<批次>/plan/` 下的版本化计划运行时，在这个接受点把被接受任务的状态与证据回写进计划（最小 diff——只改那两列），不要留到会话结束：计划是恢复锚点，与已接受工作漂移的计划是虚假记录。
8. **评审门**：material 改动之后，指派独立 Reviewer。当 Supervisor 自己写了部分改动时，此门强制且不可豁免——作者不是验证者。Reviewer 拟出确切的检查命令与预期结果，并基于原始输出工作；Supervisor 可执行它们，但不得替换它们。Reviewer 带具体证据报告 `approved`、`changes_requested` 或 `blocked`，且不静默修复它所评判的代码。此门关闭前，先真实走一遍真实用户会走的端到端路径——批准一个主用户可见路径从未执行过一次的构建，是在审代码而不是审行为。此后任何影响用户可见行为的改动都重新开门，不论作者是谁；重审可按上次已审 revision 以来的 delta 范围进行。当宿主的**交互式浏览器**自动化是主对话专属（子代理无法加载它）时，由 Supervisor 亲自负责那次浏览器操作——任何被委派的 Reviewer 都跑不了——并把原始输出（截图、DOM 或文本断言）交给 Reviewer，作为用户可见前端主张的检查证据。
9. **只修一次**：评审要求改动时，指派一轮聚焦修复，并再次评审。保持循环有界。
10. **决策**：Supervisor 依据[契约](references/contracts.md)产出最终决策记录，含实现、验证、评审结果与残余风险。记录承载断言台账：每条用户可见断言映射到若为假会失败的检查；只有代码阅读支撑的断言记为 `unverified`，任何未验证的用户可见断言使结论降为 `partial` 而非 `complete`。当结果可能进入改进环时，在会话结束前把决策记录落成 `episodes/<YYYY-MM-DD>/<EP-id>.json` 下的 episode（契约：`skills/improve/references/episode.schema.json`——复用，绝不另设平行载体），因为对话一旦消失，episode 不可恢复，也没人会记得去收集它。（适用范围：本条指**在插件仓中进行的方法开发与反馈会话**；在目标仓里工作的会话不读写插件仓的内部记录，其决策记录落目标仓文档枢纽——运行的证据需要时，由插件仓一侧在反馈与复盘的环节补记。）自 0.7.2 起，这对每一个 **material** 改动都是强制的——凡开过独立评审门的改动——不只是改进环候选。每个 Reviewer 轮次都记入 episode 的 `review_roundtrips` 字段（at、reviewer、decision、finding、resolution）：返回 `changes_requested` 的轮次、分歧是什么、如何收场——让中途评审分歧在对话消失后仍可审计，而不只留最终判定。当结果可能进入改进环时，对任何未产出结果的 worker 按[契约](references/contracts.md)中的 worker 失败语义分类（崩溃 → `blocked` 并带原因，超时 → `partial`，空/非法返回 → 退回一次后记录）——Supervisor 依据证据分类，崩溃的 worker 不会自我分类。

## 判断词的可判定定义

三个词决定门是否适用。定义写在这里，为的是同一情形每次得到同样处理，且事后可核对而不是靠争论。按此顺序应用它们：它们限定或触发门；绝不豁免「作者不是验证者」这条规则。

- **小改动**——不需要 worker 角色，也不需要架构门。须**同时**满足：单文件单层；不改契约（schema、API 形状、CLI 参数、配置键、记录格式）；不触碰共享横切机制（拦截器、全局错误处理、路由守卫、监听器、中间件）；覆盖它的确定性检查在实际文件上通过；且所修缺陷有已验证的复现。任一条不满足即属 **material**。本类不影响评审门：当 Supervisor 写下部分改动——不论小还是 material——该改动的独立评审门强制且不可豁免（硬边界 1）。
- **risky work**——满足**任一**即触发架构门（Technical Director）：改动被其它层或其它仓库消费的接口或契约；改持久化或数据模型；改安全、授权或权限边界；改共享流程的时序或幂等语义；或改动难以回退（迁移、发布顺序、已公开的 schema 或记录格式）。
- **相同原因**——同一条检查以同一规范化签名失败：检查 id 或命令相同，且剥掉时间戳与绝对路径后的错误文本或 `error_kind` 相同，即为连续两次失败同一原因。签名不同但怀疑同根因时，写明你准备改掉的假设并记录你比较了什么，不得静默重试。

## 从停滞的工作中恢复

首个阻塞且不是失败循环——契约不清、事实缺失、需求未定义——时，遵循[契约](references/contracts.md#阻塞任务先找第一个阻塞点)中的阻塞协议：枚举已尝试的动作，查清事实，把未决决策连同建议默认值交给属主，只为剩下无法解决的部分返回 `blocked`。不要等第二次失败才升级，也不要扩大改动来绕过阻塞。

在把失败的检查当作回归之前，先对改动前的 revision 跑同一检查——父提交的 worktree 即可。若那里同样失败，该失败是环境问题（工具、网络、宿主、网关）：修环境或如实上报，不要让 worker 在它上面打转。只有基线通过而改动失败的检查才算回归证据。

把连续两次相同原因的失败（见*判断词的可判定定义*）视为停止重复尝试的信号。重读代码与错误证据，重述失败掉的假设，并选择不同的做法（不同工具、不同路径或不同方法）或更小的任务边界。

若有界重试后修复/评审循环仍无法通过，带证据上报阻塞，并给出需要用户做的最小决策。不要让 Agent 在不变的输入上持续空转。

编排中途中断的会话从 `docs/features/<批次>/plan/` 下的版本化计划恢复（Markdown 看板：每个任务行带有状态与证据，状态可重新推导），而不是靠记忆：重新下简报前，先从工作区重新推导每个工作包的状态（对委派基线的 diff、检查、评审决策），没有观察到证据的包视为未开始。持久队列、租约与可恢复并行批次是未来 `execution-coordinator` 角色的职责（该角色当前不存在，不承载任何职责）；今天计划文件加仓库状态就是唯一的 checkpoint。

## 保持控制与可追溯性

- 遵循宿主的权限与沙箱规则。委派绝不扩大权限。
- 无会话内既有授权的 push、部署、发布、远端数据删除或对外发消息一律不做。**集成他人改动与改写历史是同一类动作**：`git merge`、`rebase`、`cherry-pick`，或把远端改动拉进共享分支，都需要当次用户授权，不得从先前的指令推断。推送被拒时，默认动作是只读汇报——`git fetch` 加 `log`/`diff` 列出远程新增了哪些提交与文件、重叠面在哪——由用户选择集成方式；不要自行选 merge 或 rebase、解冲突并推送。
- **目标仓会话不读写插件仓的内部记录**：skill 与 references 里提到的 `issues/`、`episodes/`、`plans/`、`reviews/` 等记录根，是 **Agentflow 插件自身仓库**（方法开发仓）的记录；在目标仓里工作时不要到插件仓里检索或写入它们——方法契约在 skill 文本内自包含。目标仓的文档与记录落 Init 确认的文档枢纽（feature 目录、`issues/`、`releases/`）；角色档案里的记录根与产物路径（如 `docs/features/<批次>/plan/`、`docs/features/<批次>/testing/`）属插件仓约定，写进委派简报前映射为该枢纽下的确切路径。
- 使用稳定的任务名，并把父目标带入每一份委派简报。
- 记录决策与证据，而不是隐藏的思维链。默认以宿主的任务与对话历史作为留痕。仅当用户要求持久的项目产物时才创建仓库留痕文件。
- 让 Supervisor 保持有用：它应解决冲突并作最终裁决，而不只是汇总 worker 消息。
