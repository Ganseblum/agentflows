# Agentflow 反馈驱动自迭代设计

> 状态：`v0.7.5` 已落地自迭代 Skill、角色分工，以及 episode、评测用例、候选和发布记录 JSON Schema。当前独立工作区已补齐 Bug/Plan 契约、公开评测基线、通用 Adapter 结果协议、隔离检查、显式 Codex/Claude Adapter 和确定性 Policy Engine；业务任务度量切片（`evals/business/`）仪器就绪，smoke 实跑待 U-01/U-02/U-03；真实模型 dogfood、自动遥测、持久检索、私有 holdout 服务和自动灰度尚未实现。当前版本仍是受治理的人工闭环，不是已经闭合的自动学习系统。

## 判断

反馈驱动自迭代是合理方向，但不能设计成“Agent 觉得自己哪里不好，然后直接改掉自己的提示词并上线”。安全、可信的自迭代是一个受治理的版本发布系统：执行 Agent 可以发现问题和生成候选，独立评测器验证候选，发布治理角色按预先声明的门槛决策，最终通过不可变版本完成发布或回滚。

```text
真实任务与用户反馈
        │
        ▼
  Evidence Episodes ── 去敏、溯源、结果标注
        │
        ▼
  Feedback Analyst ─── 问题聚类与归因
        │
        ▼
  Improvement Hypothesis
        │
        ├──────────────► 预先声明 Eval 与拒绝条件
        ▼
  Candidate Engineer ── 只修改候选源码
        │
        ▼
  Independent Evaluator ── Baseline vs Candidate
        │
        ▼
  Release Governor ─── promote / revise / reject / rollback
        │
        ▼
  人工批准（默认）──► Canary ──► Promote 或 Rollback
```

## 六个边界

### 1. 反馈驱动

证据包括用户明确接受、拒绝和纠正，验收测试，独立 Reviewer 结论，回滚和事故，重试、工具失败、延迟与成本。没有投诉不能算成功，Agent 自己说“已完成”只能作为最低权重信号。

每条证据必须带来源、Agentflow 版本、宿主、目标和结果，并经过凭证和私人内容去敏。当前 Skill 只处理用户提供、当前会话可见或仓库已有的证据；没有跨会话接口时不能假装自动读取所有历史任务。

### 2. 候选改进

先归因再修改。失败可能来自 Agentflow 的工作流规则、角色提示，也可能来自上下文不足、宿主工具、模型能力、产品代码或错误的评测。只有证据指向 Agentflow 时才生成候选。

一个候选只验证一个可证伪假设，记录父版本、证据、影响文件、预期指标、风险和拒绝条件。候选修改源码或隔离分支，不能直接修改已安装版本。

### 3. 独立评测

评测计划先于候选实现冻结。Baseline 和 Candidate 使用相同宿主、模型、权限、用例和重复次数，并按任务类型分别比较，避免平均分掩盖关键回归。

候选实现者不能修改评测器、发布门或 holdout 答案。Evaluator 只输出 `better`、`neutral`、`worse` 或 `invalid`，不能在评测轮里顺便修代码。

### 4. 版本、审计和回滚

Git 保存源版本，语义化版本标识发布。每个候选记录父版本、源码 revision、评测集 revision、结果、批准、灰度策略和回滚目标。发布记录追加写入，不能修改过去的证据来美化结果。

发布是把安装指针切到一个已经评测的不可变版本；回滚是切回已记录的旧版本，不是在生产安装目录里临时修补。

### 5. 自动化级别

| 级别 | 行为 | 建议 |
|---|---|---|
| Proposal | 只分析并给出假设 | 数据不足时使用 |
| Human-gated | 自动生成和评测候选，由人批准发布 | 默认模式 |
| Canary | 人批准策略后，小流量自动试用和阈值回滚 | 第二阶段 |
| Automatic | 自动发布满足门槛的低风险候选 | 评测成熟后再考虑 |

权限、工具、Hook、MCP、评测规则、holdout 数据和自动发布阈值的修改始终人工审核。候选不能降低批准自己的门槛。

### 6. 全链路留痕

完整链路至少记录：任务证据、归因、假设、候选、Baseline、评测、发布决策、人工批准、灰度结果和回滚。记录的是决策与证据，不是模型隐藏思考过程。

## 当前 Plugin 实现

`skills/improve` 定义跨 Codex 和 Claude Code 的自迭代工作流。Claude Code 额外提供：

- `feedback-analyst`：只读证据归因；
- `candidate-engineer`：只修改候选源码；
- `evaluator`：只读独立对照评测；
- `release-governor`：只读发布决策。

Codex 由同一 Skill 使用原生子 Agent 承担这些角色。Codex 的 `allow_implicit_invocation` 已关闭，避免普通开发任务自动触发自修改流程。

当前强制边界与流程约束必须区分：Claude 的技术决策、普通审查、反馈分析、评测和发布治理 Agent 已移除
`Bash`、`Write` 和 `Edit`；候选 Agent 仍需要在宿主提供的独立 worktree 或等价隔离中
运行。Codex 侧的只读角色目前主要依靠任务范围和宿主权限约束。独立 worktree、私有
holdout 和候选 diff 禁区已由 `tools/lab/isolation.py` 检查，确定性发布 Policy Engine
也已实现；但 `records/` 的路径约束仍主要靠角色说明和 Supervisor 检查，且真实
模型 dogfood 尚未完成，因此不能把角色分工宣传为已经验证的完整安全隔离。

发布 JSON Schema 会拒绝最明显的非法组合，例如评测结果不是 `better` 却请求
`promote`、没有人工批准却请求发布，或高风险候选请求自动发布。但 Schema 只校验记录
结构和部分条件，不能代替授权系统；最终发布仍需独立 Policy Engine 检查源码、评测集、
制品摘要、批准和回滚目标。

## 下一步实现顺序

当前 P0 的仓库、Schema、公开用例、隔离检查、Adapter 和 Policy Engine 已落地，但真实行为评测
仍受 fixture、权限、运行恢复和独立判定限制。下一步按以下顺序收敛：

1. 修复候选 diff 必须带冻结基线的门控，并补齐 Agent 安全 frontmatter 与 Schema 校验的回归测试。
2. 将插件源码、任务 fixture、评测控制面和 private holdout 分离；每个 repetition 独立重置并保存可恢复结果。
3. 持久化原始轨迹，核实 provider/model 身份，隔离宿主全局配置，并加入独立的任务判定器。
4. 在可信端点上运行 2–3 个真实 smoke，再决定是否运行完整公开 suite 和冻结阈值。
5. 评测闭环稳定后，再建设本地反馈池；阶段四已提供 SQLite FTS5 读侧索引/query（显式调用，源记录仍是权威），再建设 Canary。
6. 最后才考虑跨宿主反馈仓库和可选 MCP；MCP 只承担状态、证据和审批，不运行另一套 Agent 循环。
