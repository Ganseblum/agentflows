# Agentflow 新对话交接清单

更新时间：2026-09-13

## 当前工作区

- Agent 项目目录：`/Users/hang/Documents/myProject/agentflow`
- 这是从旧仓库 Plugin 提取的独立工作区。
- 当前没有 `.git`，没有创建远程仓库，也没有切换现有 Codex/Claude 安装源。
- 旧 CLI 仓库：`/Users/hang/Documents/myProject/multi-agent-cli`，继续保留为历史 runtime 和研究实现。
- 当前 Codex 启用源为 `/Users/hang/plugins/agentflow`，Claude 启用源为
  `~/.claude/skills/agentflow`；它们都不是当前工作区。新项目经过审查后再切换。

## 已完成

- 独立 Plugin 根目录、Codex/Claude manifest、两个 Skill 和 12 个角色文件。
- `bug-investigator`、`bug-fixer`、`bug-recorder` 三段 Bug 能力。
- `plan-architect` 计划编排能力。
- `docs/agent-roles.md` 角色矩阵、风险裁剪规则和计划/执行边界。
- `docs/agent-product-boundary.md`、`docs/self-improvement-design.md` 和本交接文档。
- episode、candidate、eval-case、release-record Schema 已从旧 Plugin 带入。
- 新项目通过 Plugin、Skill 和 Claude 严格格式校验。
- P0 第一批已落地：`schemas/bug-record.schema.json`、`schemas/plan.schema.json`、
  `schemas/evaluation-result.schema.json`，正例/反例，10 个公开评测用例，以及
  `tools/lab/validate.py`、`eval_runner.py`、`isolation.py`、`policy.py`。
- `tools/lab/host_adapter.py` 已提供 Codex/Claude 的显式结构化 Adapter；Claude 可加载
  candidate worktree，当前 Codex CLI 对未安装 candidate 源会 fail-closed，尚未做真实模型 dogfood。
- `python3 tools/lab/validate.py all`、结果对照示例和显式 Adapter smoke test 已通过。

## 已确认的角色决策

### Bug 是否拆三个 Agent

保留三个独立角色，但按风险启用，不强制每个 Bug 都启动三个 Agent：

- 小范围、低风险、已有确定复现：Supervisor 可合并 Investigator 或 Recorder，Fixer
  和验证仍需保留；是否单独 Reviewer 由风险决定。
- 单模块逻辑 Bug：建议 Investigator、Fixer、Reviewer；要沉淀经验时再启用 Recorder。
- 跨模块、API、数据、权限、并发、宿主工具、安全或不可逆问题：完整
  Investigator → Fixer → Reviewer → Recorder，并增加人工门。
- 只诊断：只启用 Investigator；只记录已知且已有独立证据：只启用 Recorder。

三个角色是能力边界，不是仪式化流水线。Fixer 永远不能批准或关闭自己的 Bug。
Reviewer 是独立审查门，不能被 Bug Recorder 代替。

### 写计划和执行计划是否同一个角色

保持分开：

- Plan Architect：汇总前端、后端、Technical Director 和反馈证据，写版本化计划，
  只写 `plans/`，不执行代码。
- Supervisor：审核计划，决定是否授权，拆成执行批次，安排并行、集成、停止和回滚。
- 未来的 `Execution Coordinator`：只有需要跨进程恢复、租约、长期队列、依赖调度和
  自动重试时再引入，负责运行状态和调度，不替代 Supervisor 的最终决策。

当前不增加通用 Task Recorder。宿主会话和事件负责基础留痕，Plan Architect 记录计划，
Bug Recorder 记录 Bug；未来共享控制面再考虑 Evidence Recorder/Store。

## 未完成任务

### P0：先形成可验证的人工闭环

- [x] 定义 `bug-record.schema.json`，包含状态、复现、归因、严重性、版本、证据和回归结果。
- [x] 定义 `plan.schema.json`，包含目标、非目标、接口、依赖、并行批次、验收、风险、回滚和输入证据。
- [x] 给两套 Schema 补正例、反例和一致性校验工具。
- [x] 增加一个真实形态的 Bug 记录示例和一个前后端并行计划示例。
- [x] 建立 10 个最小公开评测用例，覆盖角色选择、接口对齐、Reviewer 独立、重复失败重规划和权限边界。
- [ ] 接入具体 Codex/Claude 宿主 Adapter；通用 Baseline/Candidate Runner 协议和结果归一化已实现。
- [x] 实现 Candidate worktree、private holdout 布局和候选 diff 禁区检查工具；实际 Git worktree dogfood 待新仓库初始化后执行。
- [x] 实现确定性 Policy Engine；LLM Governor 只能提出建议，不能直接发布。

### P1：反馈与检索

- [ ] 定义 Trace → sanitized Episode 的转换和脱敏/同意/保留期限。
- [ ] 建立本地 Episode Store，先做版本、宿主、任务类型、归因、结果和时间过滤。
- [ ] 使用 SQLite FTS5 检索脱敏摘要，命中结果返回 evidence id、来源、版本范围和适用边界。
- [ ] 分离 `evidence/normalized` 与 `memory/validated`，成功、失败和反例都保留。
- [ ] 从旧 CLI 抽象事件幂等、SQLite 原子写、审批租约、过期和失败聚类语义；不迁 Provider、TUI 或旧 Runner。

### P2：发布自动化

- [ ] 新项目完成首轮角色评审后再初始化 Git。
- [ ] 配置独立版本、安装、更新、卸载和发布来源。
- [ ] 用真实任务运行 Human-gated dogfood。
- [ ] 样本和阈值稳定后再做 Canary、监控和低风险自动回滚。
- [ ] 只有出现跨宿主共享状态需求时，才增加只提供 evidence/eval/approval/release/rollback 的 MCP。

## 新对话建议起点

新对话开始时可以直接使用下面的上下文：

> 继续处理 `/Users/hang/Documents/myProject/agentflow`。这是没有 Git 的独立 Agentflow
> 工作区。先阅读 `README.md`、`docs/next-session-handoff.md` 和 `docs/agent-roles.md`。
> 保留按风险启用的 Bug Investigator/Fixer/Recorder 设计；Plan Architect 只写计划，
> Supervisor 负责执行授权和调度。P0 契约、公开评测和通用校验/Policy 工具已完成；
> 下一步接入具体 Codex/Claude Adapter，做真实 human-gated dogfood，再考虑 Git 和安装切换。
> 不要先做向量检索、MCP 或自动发布。

## 当前风险

- `Write` 工具对 `records/bugs/` 和 `plans/` 的路径限制仍主要依靠角色说明与 Supervisor 检查。
- 私有 holdout 必须位于公开项目和 Candidate worktree 之外。
- 当前校验器使用 Python 标准库实现本项目用到的 Draft 2020-12 子集；尚未替代完整标准验证器。
- 新项目尚未切换宿主安装源，因此真实使用验证仍需单独进行。
- `codex plugin list` 显示当前启用源为 `/Users/hang/plugins/agentflow`，Claude 使用
  `~/.claude/skills/agentflow`；两者都不是当前工作区，切换前需要重新确认安装流程。
