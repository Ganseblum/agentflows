# Agentflow Agent 产品边界决策

> 决策：将 `plugins/agentflow` 提取为独立主仓库。旧 `multi-agent-cli` 保留为历史
> runtime 和控制面研究项目，不再作为 Agentflow Plugin 的安装或运行依赖。

## 为什么现在拆

当前仓库已经包含两个生命周期不同的产品：根目录是负责模型调用、Provider、TUI、
YAML Workflow、会话和工具执行的 Go CLI；`plugins/agentflow` 是让 Codex、Claude Code
等成熟宿主执行的 Agent/Skill 工作范式。Plugin 明确禁止调用旧 CLI，并且没有导入
任何 Go 包。继续同仓会让 README、安装方式、版本和发布对象保持歧义。

新仓库建议使用 `agentflow`；名称冲突时使用 `agentflow-plugin`。用户安装和使用的产品
只有 Plugin。评测脚本、证据存储或 MCP 属于维护与治理控制面，不提供第二套聊天 CLI。

## 新仓库边界

```text
agentflow/
  plugin.json
  .codex-plugin/
  .claude-plugin/
  skills/
    agentflow/             日常开发工作流
    improve/               受治理的自迭代工作流
  agents/                  Claude 原生角色
  schemas/                 跨宿主证据和发布契约
  evals/
    public/                可见回归用例
  examples/
  tools/
    lab/                   证据、评测和发布维护工具，不运行聊天 Agent
```

Codex 和 Claude Code 继续负责模型、认证、代码工具、权限、对话和子 Agent 生命周期。
Agentflow 负责角色、协作步骤、交接契约、评审门、自迭代规则和版本治理。

## 自迭代控制面

```text
Host task result
      │
      ▼
Trace adapter ── 只接收宿主明确暴露的事件和结果
      │
      ▼
Evidence normalizer ── 去敏、来源校验、Prompt Injection 隔离
      │
      ▼
Episode store + retriever
      │
      ▼
Candidate manifest ── 绑定 Git revision 与内容摘要
      │
      ├──────────────► isolated candidate worktree
      ▼
Frozen eval plan + private holdout
      │
      ▼
Deterministic metrics ── LLM judge 只作为一个信号
      │
      ▼
Policy gate ── 检查 diff 禁区、证据、门槛、批准和回滚目标
      │
      ▼
Human approval ── 默认必需
      │
      ▼
Immutable release pointer / rollback
```

Trace 和 Episode 是不同对象。Trace 表示实际发生的事件；Episode 是经过脱敏、归因、
结果标注和保留策略处理后，允许进入反馈池的证据。原始任务文本和 Agent 输出都按不可信
输入处理，不能直接进入 Prompt、Memory 或正式评测集。

## 检索与 Memory

日常任务中的仓库检索继续使用宿主原生能力。跨任务经验检索先使用 SQLite 元数据过滤和
FTS5，不急于引入向量数据库。最小过滤字段包括 Plugin 版本、宿主、任务类型、归因层、
结果、组件、时间、证据权重和适用边界。每条命中必须返回 evidence ID、来源、版本范围、
置信度和反例，不能只返回一段相似文本。

反馈池与生产 Memory 分开。私有 holdout 位于候选 worktree 和公开 Plugin 仓库之外，
由评测环境以只读方式提供：

```text
evidence/normalized   可归因的脱敏证据，包括成功、失败和用户纠正
memory/validated      经过评测与发布门批准的可复用经验
evals/public          普通回归与开发用例
private-evals/holdout 候选不可见、仓库外只读提供的防过拟合用例
releases/records      追加写入的候选、评测、批准和回滚记录
```

只有被验证的经验才能进入 `memory/validated`。失败尝试也要保存，但必须带失败原因和适用
边界，避免以后重复采用。

## 审核机制

审核分为三层：

1. 普通任务由 Supervisor 管范围和集成，Technical Director 处理高成本架构决策，
   Reviewer 独立检查实现。
2. 自迭代由 Feedback Analyst 归因、Candidate Engineer 生成单一候选、Evaluator
   读取冻结结果、Release Governor 给出建议。角色分工本身不等于安全隔离。
3. 确定性 Policy Engine 检查候选摘要、评测集 revision、禁改路径、指标门槛、批准和
   回滚目标；人类默认作出最终发布决定。

候选必须在独立 worktree 中运行。评测器、holdout、权限、Hook、MCP 和发布策略对候选
不可写；高风险变更不能自动发布。LLM 的 `promote` 文本永远不能直接触发安装或发布。

## 旧 CLI 的处理

保留旧仓库，不继续发展 TUI、Provider 和第二套 Agent loop。以下思想可以抽象后用于控制面：

- `run_id + sequence` 的追加事件、幂等重放和冲突拒绝；
- SQLite 原子投影、归档摘要和失败聚类；
- 审批请求的持久化、租约、过期、幂等 resolve 和授权范围；
- Token 与成本元数据规范化。

不要直接迁移旧 `runner.Event`、Session、Provider、Workflow Runner 或 TUI。它们耦合旧
CLI 字段和模型执行循环。评测执行器需要新的宿主适配协议，而不是复用旧 Workflow Runner。

## 迁移顺序

1. 给旧 CLI 当前状态建立历史快照标签。
2. 使用 `git subtree split --prefix=plugins/agentflow` 保留 Plugin 的提交历史。
3. 将提取结果作为新仓库根目录，并迁移本设计和自迭代设计。
4. 更新 Manifest 中仍指向 `multi-agent-cli` 的仓库地址。
5. 增加 Plugin 专用 README、CHANGELOG、安装、更新、卸载和双宿主验证。
6. 切换本机 Codex、Claude Code 安装来源并验证，再从旧仓删除 Plugin 源码，只保留链接。

## 实现优先级

### P0：得到可验证的人工发布闭环

1. 独立仓库与不可变版本。
2. 示例记录和 Draft 2020-12 Schema/关联一致性校验。
3. 10–20 个最小离线评测用例。
4. Baseline/Candidate 宿主评测适配器和结构化结果。
5. Candidate worktree、私有 holdout 和候选 diff 禁区。
6. 确定性 Policy Engine 与 Human-gated 发布记录。

### P1：得到跨任务反馈与检索闭环

1. 本地 Episode Store、结构化查询和 FTS5。
2. 宿主明确授权的 Trace Adapter 与脱敏器。
3. 经验有效期、版本范围、反例和删除策略。
4. 可选 MCP：只暴露 evidence、evaluation、approval、release 和 rollback 状态工具。

### P2：数据充分后增加自动化

1. 盲化 A/B、多次重复和统计置信区间。
2. 语义检索和跨项目召回。
3. 低风险 Prompt/Skill 的小流量 Canary 与阈值回滚。
4. 长期证据充分后，才允许低风险类别进入自动发布。

当前 `0.3.3` 应对外描述为：已具备受治理自迭代的工作流契约和数据契约；评测执行器、
持久反馈检索与发布控制面仍待实现。
