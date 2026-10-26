---
name: improve
description: 仅当用户要求演进、优化、评测、版本化、晋级或回退 Agentflow plugin 或其角色指令时使用。它从明确的用户反馈与真实任务结果出发，运行一个受控的改进环：证据分诊、单个有界候选、证据化评审，以及可审计的发布或回退决策（仪器化基线对照仅在评测装置恢复后启用——2026-10-12 裁撤后按「人工评审」口径晋级）。
---

# Agentflow 改进

为 Agentflow 插件运行受控的改进环。模型、工具、权限与 Agent 均由当前宿主提供。不得调用独立的 Agentflow CLI。

执行的 Agent 可以发现并创建候选，但不得批准自己的证据，也不得静默替换已安装的插件。分析、候选实现、评测与发布决策必须保持为分离的角色。

创建候选前阅读[证据与发布规则](references/evidence-and-release.md)。检索相关既有记录由 **Supervisor 执行**——它运行 `python3 tools/lab/record_store.py index` 继而 `python3 tools/lab/record_store.py query '<terms>'`，把命中结果连同路径一起纳入给 feedback analyst 的简报。这只是词法 SQLite FTS5 读侧索引，不是向量库，也绝不替代各记录根下的记录文件。feedback analyst 的工具面禁 Bash，无法自行运行检索命令，因此不得把该命令写进它的指派。

## 把角色绑定到宿主

- 以主任务作为 **improvement Supervisor**；执行期间它是计划状态与证据回写的唯一写入者，并负责规范记录路由。
- 指派只读的 **feedback analyst**，负责归一化证据并识别失败模式。
- 指派 **candidate engineer** 在插件源码中实现单个有界假设。
- 指派未参与实现该候选的只读 **evaluator**。
- 指派只读的 **release governor**，判定证据是否满足已声明的门。
- 在 Claude Code 中，优先使用插件 agent `agentflow:feedback-analyst`、`agentflow:candidate-engineer`、`agentflow:evaluator` 与 `agentflow:release-governor`。
- 在 ZCode 中，优先使用同一批插件 agent（`agentflow:feedback-analyst`、`agentflow:candidate-engineer`、`agentflow:evaluator`、`agentflow:release-governor`），证据收集需要只读诊断时再加 `agentflow:bug-investigator`。Agent 角色从已安装的插件快照加载，因此角色指令改动只有重装后才可观察；检查 `python3 tools/lab/validate.py installed`。

若宿主无法提供独立 Agent，可准备提案，但不得声称独立评测或自动晋级。除非宿主确实强制分离的工具白名单与工作区，否则角色分离只是流程性的。绝不因为候选的提示词说不编辑受保护文件，就声称它被隔离。

候选写范围排除 [`protected-paths.txt`](../../protected-paths.txt) 中声明的每一个路径——Evaluator 与 Release Governor 角色文件、`tools/lab/` 下的度量路径（digest / isolation）、发布规则、记录 schema 以及清单自身。在候选被评测前用 `isolation.py check-diff` 强制执行，而不是读候选的摘要。该检查由 **Supervisor 从受信源码 checkout 运行**——不交给候选自己跑：那等于让被检查者挑选检查器。会话强制的工具白名单（agent frontmatter 中的 `tools:`）是第二层；路径排除仍依赖该检查加 Supervisor 的 diff 复核。

## 运行改进环

1. **冻结基线**：确定当前插件版本、源码 revision、相关 Skill 与 Agent 文件与宿主/模型设置（原「评测套件 revision」随 2026-10-12 装置裁撤；恢复仪器化时按 `docs/design-decisions.md` §3 重建）。
2. **收集 episode**：使用明确的用户反馈、验收结果、测试结果、reviewer 决策、回归、回退、事故，以及可得任务摘要。Bug 记录带有必填的 `provenance` 字段：只有 `provenance: agentflow` 的记录是关于 Agentflow 自身的候选证据；`session-artifact`（agent 自己即兴产出、无条款覆盖的计划、分析、决策或代码）、`user-input` 与 `external` 记录是上下文，不是 Agentflow 证据，`undetermined` 记录必须先解决归属才能使用。再犯类台账（`docs/issues/recurrence/`）是一等 episode 来源：档位为 `escalated` 的类——occurrence 记录在比其 `consolidated_in` 更新版本上的类——是本环最强的信号，先前的归纳必须视为不充分（重新归纳它，本环当前以条款加固为主，不再配自动 eval 用例）。没有投诉不等于成功。不要声称能访问宿主无法暴露的过往会话。
3. **保护语料**：移除凭据与不必要的个人或项目数据。保留来源与同意元数据，但不把敏感转录内容复制进插件。
4. **归因失败**：把提示词或角色策略失败与上下文缺失、工具失败、模型局限、仓库缺陷、环境失败区分开。记录的 `provenance` 是门：`agentflow` 表示行为归 Agentflow 自身表面所有（条款、角色、门、评测或工具）；其它任何取值——`session-artifact`、`user-input`、`external`，或未解决的 `undetermined`——不能单独支撑源码改动。只有证据指向 Agentflow 时才改 Agentflow。
5. **写一个假设**：写明观察到的模式、提议机制、受影响文件、预期改进、回归风险与否决标准。
6. **预先声明评测**：在实现候选前声明主成功指标、护栏与受保护任务切片，以及什么算最低可接受证据、什么算否决。注意这些字段当前是**声明的意图，不是机器测量的指标**——公开套件与 holdout 已随评测装置裁撤，没有可挂载它们的 runner；恢复仪器化时才重新产生可测量的 holdout 用例。
7. **创建候选**：编辑规范源码，或隔离的分支/worktree。不要编辑已安装的运行副本。把 evaluator 规则、已声明的受保护路径与 holdout 答案保持在候选写范围之外。先冻结父 revision，然后在评测前从受信源码 checkout 运行 `isolation.py check-diff --candidate <tree> --base <frozen-parent-revision>`，使已提交、已暂存、未暂存、已删除、重命名、被忽略与未跟踪的改动都被比较。该检查始终读取受信 checkout 的 `protected-paths.txt`，因此门表面是声明出来的而不是靠回忆；改动受保护文件来源或使用覆盖策略，本身就是需人工审查的门变更。
8. **公平比较（仅在仪器化度量可用时）**：评测套件与隔离 runner 已随 2026-10-12 装置裁撤，今天没有可跑的对照；恢复仪器化后，让隔离的 runner 在相同用例与设置上执行 Baseline 与 Candidate，包含代表性的成功、已知失败、边界情况与对抗性用例。给 evaluator 不可变的结果记录，而不是允许它运行受候选控制的命令。runner 把结果与比较记录逐字写到 Supervisor 指派的落点（改进三件套记录根已随 2026-10-12 瘦身批停用；启用对照时由 Supervisor 指派批次目录或临时落点）；evaluator 读取它们，且不得编辑它们。记录任务级结果、可得的成本/时延，以及不确定性。
9. **消费产物前先编译**：环中交换的每一条记录——候选记录、发布决策——在下一角色读取前先对其 schema 校验（`tools/lab/validate.py`）。当前装置下可编译的改进契约只有 `candidate.schema.json` 与 `release-record.schema.json`（评测结果与比较的原契约已随装置裁撤删除）。方法级改动一律 `measurement: none` 口径，不产出仪器化三件套；若未来恢复仪器化，落点由 Supervisor 显式指派并声明契约，只有在 `python3 tools/lab/validate.py artifacts` 与装置自身的校验通过后才算可读。非法记录是编译错误：修记录，绝不把它作为证据引用或转发。冻结 runner 无法产出的结果记为无结果。
10. **独立评审**：evaluator 报告证据而不修复候选。release governor 返回 `promote`、`revise`、`reject` 或 `rollback`。晋升按[证据与发布规则](references/evidence-and-release.md)的同一条规则判定：`measurement: complete` 时需 `evaluation_result: better`；`measurement: none` 的方法级改动需 `basis` 写为人工评审并附评审引用。
11. **准备发布**：递增版本，记录父版本、变更组件、证据、评测结果、批准、发布策略与回滚目标——完成后的发布记录写入 Supervisor 指派的落点（`docs/releases/` 现只保留在途索引与待验收这类工作文件；逐版本发布 JSON 已随 2026-10-12 瘦身批停用）。
12. **请求门**：默认模式下，把完整候选与评测呈现给用户做一次最终晋级决策。在该批准之前不得发布、重装或替换当前生效的版本。
13. **晋级后监控**：把 canary 结果与基线护栏比较。已声明阈值不达标时回滚到不可变的上一版本。（当前装置下 canary 不可达——无自动监控与回滚执行面，见*晋级模式*的注。）

## 晋级模式

- **proposal**：分析证据并提出假设；不改动源码。
- **human-gated**：创建并评测候选，然后等待用户晋级它。默认使用本模式。
- **canary**：自动把已批准的低风险候选暴露给一个有界任务切片，并带预设的回滚阈值。
- **automatic**：只保留给成熟、有统计支撑的工作流。不要仅因若干任务成功就启用它。

> **当前装置下 canary 与 automatic 均不可达（2026-10-26 审核 G07）**：自动遥测、私有 holdout、
> 自动灰度尚未实现（`docs/design-decisions.md` §3），因此 canary 的「自动监控 + 自动回滚」没有
> 执行面——今天要用只能人工切流、人工比对；`automatic` 则**结构上不可能通过**——它要求
> `evaluation_result: better`，而 `measurement: none` 时 schema 的 `allOf` 禁止 `better`。
> 这不是缺陷而是有意保留的恢复期形态：schema 枚举不改（恢复仪器化后它是对的），此处只把
> 「有入口无出口」写明，避免读者以为这两个模式现在能用。恢复时按 §3 重建清单启用。

对权限、工具访问、hook、MCP 连接、发布策略、evaluator 指令、holdout 数据或自动晋级阈值的改动，一律需人工审查。绝不让候选放松用来批准它自己的门。

**度量范围与晋升规则。** 公开套件与业务切片、评测装置已于 2026-10-12 整线裁撤：**当前没有任何自动回归度量**。改变角色在*业务仓库内*行为的方法级候选——reviewer 清单、简报纪律、验收步骤——其证据是推理加上触发它的任何事故或评审发现，其发布记录必须写明 `measurement: none`，且不得表述为已验证的改进；恢复度量按 `docs/design-decisions.md` §3 的重建清单执行。

该状态下的晋升规则（[release-record.schema.json](references/release-record.schema.json) 与[证据与发布规则](references/evidence-and-release.md)同一条）：**`measurement: none` 时，`promote` 要求 `basis` 写为人工评审并附评审引用（approvals 中至少一条 `approved` 带 `evidence_ref`），`evaluation_result` 不再被要求为 `better`；当度量恢复为 `measurement: complete` 时，`promote` 重新要求 `evaluation_result: better`。** 一条记录不能同时声称 `none` 与 `better`——那是把「无人评审的推断」记成「已验证的改进」。

**预算字段是声明的，不是强制的。** agent frontmatter 中的 `maxTurns` 并非在每个宿主上都被验证（在 ZCode 上声明但未验证）。各角色提示词里的预算纪律——最后一轮留给结果，目标未成返回 `partial`——才是生效约束；frontmatter 数字按意图元数据对待，不当作保证的截断。

agentflow skill 的[契约](../agentflow/references/contracts.md#硬边界)中的硬边界清单同样适用于每一个改进角色。

## 停止坏循环

若两个候选循环因同一原因失败，停止生成变体。重查归因、数据质量、evaluator 有效性，以及宿主或模型是否才是真正的约束。

证据薄弱时宁可选择不发布。neutral 结果不是改进。
