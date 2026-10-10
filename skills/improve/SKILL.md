---
name: improve
description: Use only when the user asks to evolve, optimize, evaluate, version, promote, or roll back the Agentflow plugin or its role instructions. Runs a governed improvement cycle from explicit user feedback and real task outcomes: evidence triage, one bounded candidate, independent baseline comparison, and an auditable release or rollback decision.
---

# Agentflow Improve

为 Agentflow 插件运行受控的改进环。模型、工具、权限与 Agent 均由当前宿主提供。不得调用独立的 Agentflow CLI。

执行的 Agent 可以发现并创建候选，但不得批准自己的证据，也不得静默替换已安装的插件。分析、候选实现、评测与发布决策必须保持为分离的角色。

创建候选前阅读[证据与发布规则](references/evidence-and-release.md)。在 Intake 期间，用 `python3 tools/lab/record_store.py index` 继而 `python3 tools/lab/record_store.py query '<terms>'` 显式检索相关既有记录；这只是词法 SQLite FTS5 读侧索引，不是向量库，也绝不替代各记录根下的记录文件。

## 把角色绑定到宿主

- 以主任务作为 **improvement Supervisor**；执行期间它是计划状态与证据回写的唯一写入者，并负责规范记录路由。
- 指派只读的 **feedback analyst**，负责归一化证据并识别失败模式。
- 指派 **candidate engineer** 在插件源码中实现单个有界假设。
- 指派未参与实现该候选的只读 **evaluator**。
- 指派只读的 **release governor**，判定证据是否满足已声明的门。
- 在 Claude Code 中，优先使用插件 agent `agentflow:feedback-analyst`、`agentflow:candidate-engineer`、`agentflow:evaluator` 与 `agentflow:release-governor`。
- 在 ZCode 中，优先使用同一批插件 agent（`agentflow:feedback-analyst`、`agentflow:candidate-engineer`、`agentflow:evaluator`、`agentflow:release-governor`），证据收集需要只读诊断时再加 `agentflow:bug-investigator`。Agent 角色从已安装的插件快照加载，因此角色指令改动只有重装后才可观察；检查 `python3 tools/lab/validate.py installed`。

若宿主无法提供独立 Agent，可准备提案，但不得声称独立评测或自动晋级。除非宿主确实强制分离的工具白名单与工作区，否则角色分离只是流程性的。绝不因为候选的提示词说不编辑受保护文件，就声称它被隔离。

候选写范围排除 [`protected-paths.txt`](../../protected-paths.txt) 中声明的每一个路径——Evaluator 与 Release Governor 角色文件、评测套件、`tools/lab/` 下的度量路径、发布规则、结果 schema 以及清单自身。在候选被评测前用 `isolation.py check-diff` 强制执行，而不是读候选的摘要。会话强制的工具白名单（agent frontmatter 中的 `tools:`）是第二层；路径排除仍依赖该检查加 Supervisor 的 diff 复核。

## 运行改进环

1. **冻结基线**：确定当前插件版本、源码 revision、相关 Skill 与 Agent 文件、评测套件 revision，以及宿主/模型设置。
2. **收集 episode**：使用明确的用户反馈、验收结果、测试结果、reviewer 决策、回归、回退、事故，以及可得任务摘要。Bug 记录带有必填的 `provenance` 字段：只有 `provenance: agentflow` 的记录是关于 Agentflow 自身的候选证据；`session-artifact`（agent 自己即兴产出、无条款覆盖的计划、分析、决策或代码）、`user-input` 与 `external` 记录是上下文，不是 Agentflow 证据，`undetermined` 记录必须先解决归属才能使用。再犯类台账（`issues/recurrence/`）是一等 episode 来源：档位为 `escalated` 的类——occurrence 记录在比其 `consolidated_in` 更新版本上的类——是本环最强的信号，先前的归纳必须视为不充分（重新归纳它，通常配一条 eval 用例）。没有投诉不等于成功。不要声称能访问宿主无法暴露的过往会话。
3. **保护语料**：移除凭据与不必要的个人或项目数据。保留来源与同意元数据，但不把敏感转录内容复制进插件。
4. **归因失败**：把提示词或角色策略失败与上下文缺失、工具失败、模型局限、仓库缺陷、环境失败区分开。记录的 `provenance` 是门：`agentflow` 表示行为归 Agentflow 自身表面所有（条款、角色、门、评测或工具）；其它任何取值——`session-artifact`、`user-input`、`external`，或未解决的 `undetermined`——不能单独支撑源码改动。只有证据指向 Agentflow 时才改 Agentflow。
5. **写一个假设**：写明观察到的模式、提议机制、受影响文件、预期改进、回归风险与否决标准。
6. **预先声明评测**：在实现候选前选定主成功指标、护栏、任务切片、最低证据与 holdout 用例。
7. **创建候选**：编辑规范源码，或隔离的分支/worktree。不要编辑已安装的运行副本。把 evaluator 规则、已声明的受保护路径与 holdout 答案保持在候选写范围之外。先冻结父 revision，然后在评测前从受信源码 checkout 运行 `isolation.py check-diff --candidate <tree> --base <frozen-parent-revision>`，使已提交、已暂存、未暂存、已删除、重命名、被忽略与未跟踪的改动都被比较。该检查始终读取受信 checkout 的 `protected-paths.txt`，因此门表面是声明出来的而不是靠回忆；改动受保护文件来源或使用覆盖策略，本身就是需人工审查的门变更。
8. **公平比较**：让隔离的 runner 在相同用例与设置上执行 Baseline 与 Candidate。包含代表性的成功、已知失败、边界情况与对抗性用例。给 evaluator 不可变的结果记录，而不是允许它运行受候选控制的命令。runner 把结果与比较记录逐字写到 Supervisor 指派的 `improvements/` 路径下；evaluator 读取它们，且不得编辑它们。记录任务级结果、可得的成本/时延，以及不确定性。
9. **消费产物前先编译**：环中交换的每一条记录——候选记录、评测结果、比较、发布决策——在下一角色读取前先对其 schema 校验（`tools/lab/validate.py`、`eval_runner.py validate`）。四类产物落在 `improvements/{candidates,evaluations,comparisons}/` 与 `releases/` 下，只有在 `python3 tools/lab/validate.py artifacts` 与 runner 自身的 validate 通过后才算可读。非法记录是编译错误：修记录，绝不把它作为证据引用或转发。冻结 runner 无法产出的结果记为无结果。
10. **独立评审**：evaluator 报告证据而不修复候选。release governor 返回 `promote`、`revise`、`reject` 或 `rollback`。
11. **准备发布**：递增版本，记录父版本、变更组件、证据、评测结果、批准、发布策略与回滚目标——完成后的发布记录落在 `releases/` 下。
12. **请求门**：默认模式下，把完整候选与评测呈现给用户做一次最终晋级决策。在该批准之前不得发布、重装或替换当前生效的版本。
13. **晋级后监控**：把 canary 结果与基线护栏比较。已声明阈值不达标时回滚到不可变的上一版本。

## 晋级模式

- **proposal**：分析证据并提出假设；不改动源码。
- **human-gated**：创建并评测候选，然后等待用户晋级它。默认使用本模式。
- **canary**：自动把已批准的低风险候选暴露给一个有界任务切片，并带预设的回滚阈值。
- **automatic**：只保留给成熟、有统计支撑的工作流。不要仅因若干任务成功就启用它。

对权限、工具访问、hook、MCP 连接、发布策略、evaluator 指令、holdout 数据或自动晋级阈值的改动，一律需人工审查。绝不让候选放松用来批准它自己的门。

**度量范围。** `evals/` 下的公开套件度量的是 Agentflow 自己的契约用例。改变角色在*业务仓库内*行为的候选——reviewer 清单、简报纪律、验收步骤——在那里没有回归度量。当这样的方法级假设有匹配的业务用例时，经由 `evals/business/` 下的业务切片做比较：在业务仓钉死的只读快照上跑三个文档评审用例，由 `tools/lab/seed_grader.py` 对照运行前埋入的缺陷做确定性评分，从而能产出本环的 `better / neutral / worse` 标准。覆盖面目前很窄——只有 aiwork 文档评审一类——任何无匹配业务用例的方法级改动仍属未度量：其证据是推理加上触发它的任何事故或评审发现，其发布记录必须写明 `measurement: none (method-level change, no instrumented business task)`，且不得表述为已验证的改进。首个业务切片按 **smoke** 评级：它证明流水线与评分器可用，其数字在可信端点、实测权限档与快照位置（PLAN-BUSINESS-EVAL-001 的 U-01 / U-02 / U-03）关闭之前不是权威基线。

**预算字段是声明的，不是强制的。** agent frontmatter 中的 `maxTurns` 并非在每个宿主上都被验证（在 ZCode 上声明但未验证）。各角色提示词里的预算纪律——最后一轮留给结果，目标未成返回 `partial`——才是生效约束；frontmatter 数字按意图元数据对待，不当作保证的截断。

agentflow skill 的[契约](../agentflow/references/contracts.md#硬边界)中的硬边界清单同样适用于每一个改进角色。

## 停止坏循环

若两个候选循环因同一原因失败，停止生成变体。重查归因、数据质量、evaluator 有效性，以及宿主或模型是否才是真正的约束。

证据薄弱时宁可选择不发布。neutral 结果不是改进。
