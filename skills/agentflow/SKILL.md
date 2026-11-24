---
name: agentflow
description: 用于跨前端与后端的功能、接口契约、数据模型、安全或权限边界改动，并行调查与委派实现，需要独立评审的改动，影响用户可见行为的自动化测试，反复出现或跨层的 Bug 排查 / 修复 / 回归闭环，以及规划、文档交付链与手工解冲突的分支合并。以宿主自身的 agent 应用 Agentflow 方法：supervisor、frontend/backend 工程师、technical director、独立 reviewer、test-planner/test-executor。琐碎单步工作可跳过。
when_to_use: 跨前端后端的功能或契约改动、并行调查、委派实现、独立评审、影响用户可见行为的测试、反复出现或跨层的 Bug、需要手工解冲突的分支合并；或用户主动说「走 agentflow」「多智能体」「评审一下这个改动」。琐碎单步改动不用。
---

# Agentflow

用当前宿主内置的 Agent、认证、工具、权限与对话历史，应用 Agentflow 开发方法。

不得调用或要求独立的 `agentflow` CLI、其 providers、其 TUI、Agentflow API key 或 Agentflow MCP server。本 skill 就是工作流，宿主就是运行时。

## 绑定宿主

- 在 **Codex** 中，使用原生子代理。每个子代理只给一个角色和一份任务简报。以主任务作为 Supervisor。
- 在 **Claude Code** 与 **ZCode** 中，仅当[角色路由](references/roles.md)表明能降低风险时才启动插件 agent。默认不加载完整角色列表；**插件根目录 `agents/` 下的角色文件**是可选能力（`plugin.json` 以 `"agents": "agents"` 声明；`skills/agentflow/agents/` 下只有宿主展示字段，没有角色文件）。选中的角色以 `agentflow:reviewer`（或对应的 `agents/<role>.md` 名称）调用。以主对话作为 Supervisor。
- 在 **Qoder** 中，插件按已安装快照加载，角色以 `agentflow:<role>` 注册。本地目录安装优先用 `qoder plugins install <插件根> --scope user`（需要独立的 Qoder CLI）；只有 IDE 时用桌面端的扩展安装入口（见宿主事实 Q5）。本仓的插件根是 `packaging/runtime`；源编辑需重建该生成树后重装。角色 `tools` / `disallowedTools` 在该宿主是否被强制执行未验证，不得把提示词纪律当作宿主强制。
- 在其它兼容 Agent Skills 的宿主中，使用其内置委派机制。若不存在，则顺序执行同样的阶段，并说明独立执行不可用。
- 跨仓库的全局纪律不随插件安装自动生效。需要它们在该宿主的每个会话默认生效时，按[宿主接入](references/hosts.md)做一次 Host Init，写进宿主自己的全局指令文件。宿主全局文件是跨项目写操作，与合并、推送同级，需要当次明确确认；写完要做 hosts.md 第 6 条的三项校验（块外内容、块内容、宿主复述首行），拿不到加载证据就记 `blocked`。

## 先读哪份规则

**按任务选择入口。** 委派前读角色路由与契约，并按当前任务选择表中的其他规则。

| 当前工作 | 权威入口 |
| --- | --- |
| 开工、测试先行、预检、选测、证据复用、补测、失败分流 | [执行与验证](references/execution.md) |
| 选择角色与交接、简报/结果字段、硬边界 | [角色路由](references/roles.md) · [契约](references/contracts.md) |
| 独立评审要加载哪几份深度清单、评审档位与交付前自检 | [评审清单](references/review-checklists.md) |
| 功能文档的档位与必需骨架 | [文档交付链](references/document-chain.md) |
| 需求说不清、开工前对齐、任务简报 | [开工提问](references/intake.md) · 用户主动叫入口：[agentflow-intake](../agentflow-intake/SKILL.md) |

**按产物触发**（命中该产物才读；不在主干里，读到这一行就够了）：

| 场景 | 入口 |
| --- | --- |
| 第一次接一个新项目（六问、接入约定、基线对齐） | [Init 细则](references/init.md) |
| 方案已成形、设计冻结前压漏洞 | [压设计](references/grilling.md) · 用户主动叫入口：[agentflow-grilling](../agentflow-grilling/SKILL.md) |
| 写测试计划 / 执行记录、Bug 状态联动 | [测试记录](references/test-records.md) |
| 写代码（服务端 / 数据模型 / 前端工程底线） | [服务端](references/standards/server-side.md) · [数据模型](references/standards/data-model.md) · [前端](references/standards/frontend.md) |
| UI 视觉方向、设计稿还原与走查 | [前端标准](references/standards/frontend.md)（FE-12 / FE-13） |
| 安全审计、API 契约与 Git 规范 | [安全审计](references/standards/security.md) · [API 契约](references/standards/api-docs.md) · [Git 规范](references/standards/git-commits.md) |
| 缺陷发现 → 落账 → 复发台账 | [问题闭环](references/issue-tracking.md) |
| 核对真实入口、端到端验收与证据层级 | [验证分级](references/verification-grading.md) |
| 设计测试用例（AC 权威在 plan 注册表） | [测试用例](references/testcases.md) |
| 进入某类功能前主动穷举范围维度 | [范围维度](references/intake-scope-dimensions.md) |
| 产品决策简报（分类头 + 九段） | [决策简报模板](templates/decision/decision-brief.md) |
| 画、改、评设计图（时序 / 状态 / 架构 / ER） | [设计图](../design-diagram/SKILL.md) |
| 跨仓全局纪律、Host Init 协议、宿主矩阵 | [宿主接入](references/hosts.md) |
| 用户行为事件与埋点评审 | [埋点契约](references/telemetry.md) |
| 仓库整体审核 / 体检 / 复盘 | [审核契约](references/repo-audit.md) |
| 只读代码调研、实现说明、数据流梳理（不审核、不改） | [只读调研](references/repo-audit.md#只读调研非审核) |
| 证据工具 seal / verify / run 的命令语义 | [证据工具用法](references/workflow-tool.md) |
| 载体归属（哪份规则落在哪个物理文件） | [载体地图](references/carrier-map.md) |

**规则预算。** 对照当前任务选取规则。新增强制条款前明确执行者、证据位置和失败信号；缺少其中一项时，使用评审清单。硬边界的实际执行面见[契约](references/contracts.md#执行面)。

同一任务可以命中多项，但只读取实际适用的内容。规则、状态和行为正文各维持一个权威来源，不复制第二套流程或记录。

## 首次接入（Init）

目标仓没有相关约定、记录结构或检查命令时，先做一次轻量接入再走正常流程。**执行细则见 [Init 细则](references/init.md)**（脚本先行 → 六问集中确认 → 写接入约定小节 → 已有批次先对齐基线），此处只留三条不变式：**脚本先行**（`python3 <skill>/scripts/init_workspace.py <目标仓根> --dry-run` 先出计划，确认后实跑；宿主既有文件只追加托管块，**绝不覆盖**，冲突与用户逐条裁决）；**接入必须带可执行的验收条款**（宣布完成前，对每个批次按文档链人工核对材料并运行目标仓真实文档检查（如有）、对每次实现跑适用仓库构建/测试，并把原始输出随结论给出——只写「走主流程」等于没接）；**工程基线只收实测事实**（查不到写缺口，不按通用默认推断，不搬运别的项目的业务数值与部署流程）。

分派工作前阅读[角色档案](references/roles.md)，委派实现或评审前阅读[契约](references/contracts.md)。[硬边界](references/contracts.md#硬边界)在每一次委派中都成立；接受任何交付物前先检查它们。

缺陷链按[角色路由](references/roles.md#工作链默认入口)分工。用户可见缺陷应在相同入口留存修前、修后证据，路线按[执行与验证](references/execution.md#执行路线与数据)选择。缺陷状态按[测试记录](references/test-records.md)由主审或记录角色回写。

规划任务按[角色路由](references/roles.md)选择有工作的专家，按[文档交付链](references/document-chain.md)使用已确认的计划位置和材料。默认 full 用功能目录下的 `plan/execution.md`，light 用唯一 README；已有文档体系按实际路径映射。计划记录依赖、任务状态、检查与回退点。接受计划与授权实施是独立动作。

## 宿主级接入（Host Init）

Init 管目标仓，Host Init 管跨仓。目标仓的 `AGENTS.md` 只在该仓工作时加载，换一个仓就没有；分支与合并纪律、证据纪律这类跨仓条款要写进宿主的全局指令文件才默认在场。协议（写入、备份、幂等、三项校验、权限降级与留痕）以[宿主接入](references/hosts.md)为唯一权威，规则正文用 [templates/host/global-rules.md](templates/host/global-rules.md)，只替换版本号。三条硬约束：默认 dry-run；只改托管块（begin / end 两条注释）之间的内容，块外一字不动；写入后必须做 hosts.md 第 6 条的三项校验，宿主复述首行拿不到就记 `blocked`，不算接入完成。插件升级或模板变更后托管块版本与新 manifest 不一致即为漂移，重跑一次；**改模板必须同时 bump 插件版本**，否则同版本重跑是 no-op。

## 自动化测试

按[测试记录](references/test-records.md)确定载体与分工。light 可在唯一 README 写用例、运行与评审；full 采用目标仓确认的测试计划和运行记录。测试顺序、环境预检、选测、浏览器路线、数据和凭据纪律统一遵守[执行与验证](references/execution.md)。

## 外部文档二次评审

当用户要求评审在另一套系统规则下编写的文档（例如业务仓自有模板系统内产出的需求提案/spec/设计/计划）时，对这些文档运行独立 Reviewer，把评审证据与结论留存为评审记录，并按`provenance` 分流「目标系统模板缺口」与「本仓 review 契约缺口」两个升级回路。**四步桥工作流、归档快照与 `source_revision`、自包含引用要求、评审记录契约都以 [审核契约](references/repo-audit.md#外部文档二次评审另一套规则下产出的文档) 为唯一权威**，本文不复述。

## 仓库整体审核

按[审核契约](references/repo-audit.md)读取仓库、验证实际命令并给出带证据的发现。默认把报告交回会话。需要持久化时，使用用户授权的落点；方法改进在有明确授权的修复批次里推进。

## 文档交付链

实施新功能或产出功能文档时先按[文档档位](references/document-chain.md#文档档位)确定材料。full 走接入、访谈、提案、规格、设计、计划、实施；light 在唯一 README 中组织同义内容。沿用目标仓已有模板及已确认的路径；按[阶段评审](references/document-chain.md#阶段评审与完成证据)核对文档，再按实施入口核对行为与验证。产品语义未决时交用户，确定内容回写单一来源。

## 埋点

改动新增、修改或删除用户行为事件，或触及事件采集端点、事件表结构、看板聚合口径时，按 [埋点契约](references/telemetry.md) 评审——它是检查清单的唯一真源，本文不复述那十条，也不断章摘句。走文档交付链的项目，埋点在三处连成一线：`proposal` 的埋点决策 → `spec/fe` 的口径 → `design/fe` 的事件契约，验收落在 QA；三处互相矛盾、或任一处缺席，按缺口处理而不是可选装饰。事件手册不与档案链重复：沿档链工作的项目，`design/fe` 的契约节就是它的事件手册；目标仓本就既有手册时以后者为准，契约节只登记本期的差异与出处。

## 运行工作流

1. **开工**：读取仓库指令、实际分支和改动，明确交付物、验收与证据基线。只有任务要求确认远端状态时校准远端，并报告来源。按需使用[开工提问](references/intake.md)、[范围维度](references/intake-scope-dimensions.md)、[首次接入](references/init.md)与[问题闭环](references/issue-tracking.md)。
2. **架构门**：跨层或高风险工作由 Technical Director 核对契约、消费方、交付顺序与恢复方案。方案未定时按[压设计](references/grilling.md)先核实事实，再把必须由用户决定的事项交用户。
3. **计划**：按[计划状态](references/document-chain.md#计划状态与交付状态)准备、评审和接受计划。full 需要独立计划角色时用 Plan Architect。light 在唯一 README 保留适用任务和证据。
4. **委派**：按[委派契约](references/contracts.md#worker-任务简报)给出目标、基线、`read_scope`、`write_scope`、`design_refs` 和检查。简报中的工作区、分支、路径与命令先核实。独立写入者分别使用分支或 worktree，重叠或依赖写入串行。
5. **实现**：按[执行与验证](references/execution.md)做有效失败、最小实现与受影响回归，结果记录各设计引用、变更路径、实际命令及剩余风险。
6. **集成**：Supervisor 检查实际共享工作区，解决跨层冲突，并运行能证明整个 feature 可用的检查。当任务本身就是分支集成——Supervisor 亲手解决了代码冲突，或合并结果改变用户可见行为——该合并提交就是 material 改动：解决冲突就是在写代码，因此第 8 步评审适用，Supervisor 自己的冲突取舍不获豁免。报合并完成前，运行能证明合并产物可构建且行为正确的确定性检查并留存原始输出——至少是仓库的构建/编译检查加上每个受影响可部署单元的测试套件（Go 项目为 `go build ./...` 加 `go test ./...`，每个前端工作区 `tsc --noEmit`，触碰数据库迁移的合并在该工作区规则下真实地跑一次迁移）。grep 冲突标记只用于分诊，绝不用于接受：仅凭冲突标记 grep（或 diff 大小）就报告合并完成是反模式——清掉 `<<<<<<<`/`>>>>>>>` 只证明标记没了，不证明语法与语义正确。禁用常规构建/测试的工作区规则是迭代默认值，不是豁免：当要求这些检查时，要么运行它们，要么把冲突升级给用户——绝不静默跳过。合并一个**曾被回滚**的分支时，先用 `git log --grep='This reverts commit' --oneline` 找到回滚提交，再用 `git show --name-status <revert>` 取文件清单逐项对账，逐文件确认合并结果；评审 diff 必须包含源分支一侧——源分支还在时用 `source_branch..merge_result`，源分支已删除时用 `merge_result^2..merge_result`；只给 `merge_result^1..merge_result`（第一父提交基线）的评审看不见「源分支有、合并结果没有」的漏项。测试失败时不得用跳过 pretest、`--ignore-scripts`、只跑子集或缩小 glob 的方式换成绿色——那与静默跳过同罪；要么修，要么把红作为阻塞升级给用户并保留原始输出。这组规则的宿主级副本载体与同步机制登记在[载体归属表](references/carrier-map.md)：改模板必须同时 bump 插件版本并重跑 Host Init，漂移由版本号判定，不靠「记得同步另一处」的人工记忆。
7. **验证与接受任务**：主审读取实际产物，复核仓库检查的命令、退出码和原始结果，并核对委派基线以来的已跟踪、未跟踪改动与 `write_scope`。未通过的检查退回，未运行写明原因。按[计划状态](references/document-chain.md#计划状态与交付状态)更新实际任务，独审与交付收口按各自证据回写。
8. **评审**：按[文档档位](references/document-chain.md#文档档位)决定需不需要独审。按[对象入口](references/contracts.md#按对象核对入口)派发独立 Reviewer，记录 `review_tier`；L0 按[能力降级](references/contracts.md#评审能力分级)留痕并补审。文档评审核对阶段材料；实施评审另核冻结实现、原计划任务及真实执行证据。未提交对象用 [review_snapshot.py](scripts/review_snapshot.py) 生成快照；重审优先按已审对象的差异与遗留发现。
9. **按进展修复与重审**：评审要求改动时做聚焦修复，按新 revision 重开必要评审；不设固定轮数。重审默认 delta，按[契约](references/contracts.md#评审结果)的入口/出口条件收口；同一原因连续两次失败或一轮无进展就停下重新规划或升级。纯机械非语义变更记录其判定与检查，不能借此跳过行为或契约变化的独审。
10. **交付结论**：按[最终决策记录](references/contracts.md#最终决策记录)交代实现、证据、评审及残余风险。用户可见断言附可证伪检查；缺证据写 `unverified`。在已授权的记录位置引用各轮评审和处置；未授权持久化时交回会话。

## 分档默认值

使用[证据深度](references/execution.md#评审与测试的成本分档按改动量定证据深度不按轮次惯性)的 L、S、M 优先级选择验证深度。按[预览规则](references/document-chain.md#原型与页面预览)选原型或真实页面。

## 评审简报的定位义务

Reviewer 只读、不跑命令，它的取证轮次完全由简报的定位质量决定：只给文件名的简报会让它把大量轮次花在「找这句话在哪」，而不是「判断对不对」。因此：

- **主审先运行已知适用的检查**，保留命令、退出码和逐字输出。Reviewer 核查覆盖和断言质量，需要不同观察或补证时给出确切命令或步骤。
- **其余断言给出可定位的核实点**：被评审 diff 的确切范围（`source_branch..merge_result`，或源分支已删时的 `merge_result^2..merge_result`）、每条断言对应的 `path:line` 或可复核的 Grep 模式、上轮 `review_id` 与未关闭 finding 清单（重审时）、已跑完的确定性检查的原始输出。给不出定位时写明「该断言无定位，需 reviewer 自行检索」，不要让它去猜。
- **不要要求 reviewer 执行命令**（工具集是 `Read, Glob, Grep`，`Bash` 在 `disallowedTools` 里）；需要 diff 时给 diff 正文或 `.diff` 文件路径。
- **用脚本生成简报**：`python3 <skill>/scripts/gen_review_brief.py --review-type document|implementation --out <简报> --objective <目标> --files <文件...> --reviewed-revision <提交或快照>`。实施评审加 `--task-status <映射文件> --task-ids <受评任务 ID...>`。delta 加 `--diff-base <基线快照>` 并指明上轮结论或无遗留的原文；详细字段和命令见[评审契约](references/contracts.md#评审简报必填字段缺一-reviewer-可直接判-blocked)。

## 判断词的可判定定义

材料与独审要求只由[文档档位](references/document-chain.md#文档档位)判定，不再另立单文件、行数或作者身份阈值。以下词供调度与停止条件引用：

- **小改动**——符合该节琐碎静态或 light 条件的有界任务；可由 Supervisor 实现，不强制工程师全员到场。静态自检与 light 行为独审按该节区分。
- **material**——需 full 材料、改变方法/公开契约或高风险边界、以及手工解冲突的合并；按范围加载必要专业角色与独审，不能只因 diff 小就降级。
- **risky work**——满足**任一**即触发架构评审（Technical Director）：改动被其它层或其它仓库消费的接口或契约；改持久化或数据模型；改安全、授权或权限边界；改共享流程的时序或幂等语义；或改动难以回退（迁移、发布顺序、已公开的 schema 或记录格式）。
- **相同原因**——同一条检查以同一规范化签名失败：检查 id 或命令相同，且剥掉时间戳与绝对路径后的错误文本或 `error_kind` 相同，即为连续两次失败同一原因。签名不同但怀疑同根因时，写明你准备改掉的假设并记录你比较了什么，不得静默重试。

## 从停滞的工作中恢复

首个阻塞且不是失败循环——契约不清、事实缺失、需求未定义——时，遵循[契约](references/contracts.md#阻塞任务先找第一个阻塞点)中的阻塞协议：枚举已尝试的动作，查清事实，把未决决策连同建议默认值交给属主，只为剩下无法解决的部分返回 `blocked`。不要等第二次失败才升级，也不要扩大改动来绕过阻塞。

在把失败的检查当作回归之前，先对改动前的 revision 跑同一检查——父提交的 worktree 即可。若那里同样失败，只能说明该失败不是本次改动新增的回归；继续区分既存产品缺陷、既存检查器缺陷、环境问题或失效夹具，并按证据修复或如实上报。只有基线通过而改动失败的检查才算本次回归证据。

把连续两次相同原因的失败（见*判断词的可判定定义*）视为停止重复尝试的信号。重读代码与错误证据，重述失败掉的假设，并选择不同的做法（不同工具、不同路径或不同方法）或更小的任务边界。

若有界重试后修复/评审循环仍无法通过，带证据上报阻塞，并给出需要用户做的最小决策。不要让 Agent 在不变的输入上持续空转。

中断后从已确认的计划、light README 或目标仓同义文件恢复，检查当前 diff、已验事实及未关闭发现，再派发剩余任务。

## 工程内容标准与问题闭环

实现与评审按实际改动选用[服务端](references/standards/server-side.md)、[数据模型](references/standards/data-model.md)、[前端](references/standards/frontend.md)、[安全审计](references/standards/security.md)、[API 契约](references/standards/api-docs.md)和[Git 规范](references/standards/git-commits.md)标准。跟进已确认缺陷按[问题闭环](references/issue-tracking.md)登记；用户入口、证据层级与验收来源分别见[验证分级](references/verification-grading.md)和[测试用例](references/testcases.md)。

## 保持控制与可追溯性

- 遵循宿主的权限与沙箱规则。委派绝不扩大权限。
- 无会话内既有授权的 push、部署、发布、远端数据删除或对外发消息一律不做。**集成他人改动与改写历史是同一类动作**：`git merge`、`rebase`、`cherry-pick`，或把远端改动拉进共享分支，都需要当次用户授权，不得从先前的指令推断。推送被拒时，默认动作是只读汇报——`git fetch` 加 `log`/`diff` 列出远程新增了哪些提交与文件、重叠面在哪——由用户选择集成方式；不要自行选 merge 或 rebase、解冲突并推送。
- 目标仓按接入时确认的功能目录、缺陷目录与证据位置工作。以插件随包规则和模板为方法来源；只在维护本插件时使用插件仓自己的内部记录。
- 使用稳定的任务名，并把父目标带入每一份委派简报。
- 记录决策与证据，而不是隐藏的思维链。默认以宿主的任务与对话历史作为留痕。仅当用户要求持久的项目产物时才创建仓库留痕文件。
- 让 Supervisor 保持有用：它应解决冲突并作最终裁决，而不只是汇总 worker 消息。
