# Agentflow 宿主原生 Plugin 设计与 `my-agent` 参考评估

> 状态：`v0.3.1` 已形成 Codex + Claude Code 共用的开发 Skill、自迭代 Skill 和双宿主 Plugin；不依赖 Agentflow CLI 或 MCP。

> 仓库边界已经重新评审：Plugin 应作为主产品拆到独立仓库，旧 Go CLI 保留为历史
> runtime 和控制面研究实现。详细决策及迁移步骤见
> [Agent 产品边界决策](agent-product-boundary.md)。

## 产品边界

目标产品是一套可移植的开发范式：用户留在 Codex、Claude Code 等成熟编码宿主里，由宿主负责模型、登录、工具、权限、终端体验和 Agent 生命周期，Agentflow 只定义如何组织工作。

```text
Codex / Claude Code / Agent Skills host
                  │
                  ▼
         Agentflow shared Skill
      ┌───────────┼────────────┐
      ▼           ▼            ▼
 frontend      backend   technical director
      └───────────┬────────────┘
                  ▼
           supervisor integrates
                  ▼
        independent reviewer gate
```

Plugin 运行路径中不调用本仓库的 `agentflow` 可执行文件，不启动第二层 TUI，不读取 Agentflow YAML，也不需要 `OPENAI_API_KEY` 或其他额外 Provider 凭证。现有 CLI 可以保留为历史实现和独立实验，但不再是这套跨宿主方案的依赖。

## 为什么是 Skill + 薄宿主包装

Codex 与 Claude Code 都支持基于 `SKILL.md` 的可复用工作流。共享 Skill 定义 Intake、架构门、角色选择、实现、集成、独立复核、有限修复和最终决策记录。

两边只保留必要差异：

| 能力 | Codex | Claude Code |
|---|---|---|
| 调用入口 | `$agentflow` | `/agentflow:agentflow` |
| 工作流定义 | 共用 `skills/agentflow/SKILL.md` | 共用同一文件 |
| 多 Agent 执行 | Codex 原生 subagents | Claude Code 原生 subagents |
| 专用角色 | Skill 在任务简报中指定角色 | Plugin 同时提供四个 `agents/*.md` |
| 权限与认证 | 继承 Codex 当前任务 | 继承 Claude Code 当前会话 |
| 留痕 | Codex 任务和子 Agent 历史 | Claude Code 会话和 Agent 历史 |

Claude Code 原生支持 Plugin 内的 Agent 定义，所以提供 frontend engineer、backend engineer、technical director 和 reviewer。Codex 的 Plugin 只需要共享 Skill，由 Skill 为原生子 Agent 注入相同角色契约。核心范式一致，宿主适配保持薄层。

反馈驱动的自迭代由独立 `skills/improve` 控制面处理，设计与发布边界见 [反馈驱动自迭代设计](self-improvement-design.md)。它不会在日常任务结束后自行修改已安装 Plugin。

## 工作流

1. **Intake**：主任务读取真实代码、规则、当前 diff 和测试，明确目标与验收条件。
2. **Architecture gate**：跨层、迁移、安全或高返工成本任务由技术总监给出只读决策；普通小改动跳过。
3. **Role selection**：只启用有价值的角色。前端任务不强制创建后端 Agent。
4. **Implementation**：前端和服务端在边界稳定、文件范围不冲突时并行，否则按依赖顺序执行。
5. **Integration**：Supervisor 检查共享工作区、解决接口冲突并运行整体校验。
6. **Review gate**：独立 Reviewer 只检查，不在同一轮偷偷修复，输出 `approved`、`changes_requested` 或 `blocked`。
7. **Bounded repair**：只进行一轮定向修复和再次复核；相同原因连续失败两次时重新检查假设与实际代码。
8. **Decision record**：Supervisor 给出结果、证据、评审结论、风险和下一步。

Supervisor 是当前 Codex 任务或 Claude Code 主会话，不需要再创建一个“总监外面的总监”。技术总监负责高成本技术决策，Supervisor 负责范围、调度、权限、集成和向用户交付。

## `my-agent` 的参考价值

`my-agent` 的 Intake、Planner、Gatekeeper、Dispatcher、Department、CompletionGate 分层，以及 SQLite/WAL 权威状态、统一 application command、版本化 adapter protocol，适合长任务、跨进程恢复和合规审计。

本方案直接吸收五个原则：

1. Adapter 保持薄层，不在 Codex 和 Claude 两边复制业务状态机。
2. 任务简报、Worker 回执和 Reviewer 决策使用稳定结构。
3. Supervisor、技术决策和独立复核职责分离。
4. 重试有边界，连续相同失败触发重新规划。
5. 能力不足时明确降级，不假装具有并行或独立复核能力。

不直接照搬的是六阶段常驻治理进程、外部 Node adapter、SQLite 服务、发布供应链和执行文件哈希固定。它们解决的是持久运行与企业治理问题，不是第一阶段“在成熟 CLI 中复用开发范式”的必要条件。

两个项目的领域仍然高度重叠。如果未来确实需要统一的跨宿主持久状态，应选一个治理 Core，另一个只保留协议适配或迁移入口，不能长期维护两套审批、状态机和审计实现。

## MCP 什么时候才需要

当前不需要 MCP。角色编排、代码读写、测试、权限和会话历史都由宿主原生能力完成。

只有出现以下需求时才增加可选 MCP：

- Codex 和 Claude Code 需要查询同一份跨会话 Run 状态；
- Reviewer 决策要进入集中审计或团队面板；
- 需要组织级审批、预算、身份和租户边界；
- 需要连接外部任务系统，而宿主没有现成工具。

即使增加 MCP，它也只提供状态、决策和审计工具，不负责启动另一套模型循环或 TUI。

## 后续优先级

1. 用真实的前后端跨层任务分别在 Codex 和 Claude Code 做行为测试，记录角色误触发、漏触发和上下文丢失。
2. 增加最小评测用例，覆盖小任务不拆分、跨层任务先定接口、Reviewer 独立和重复失败重规划。
3. 根据实测缩短任务契约和角色提示，控制 token 与等待成本。
4. 将 `plugins/agentflow` 抽成独立仓库，使它与旧 CLI 的版本生命周期解耦。
5. 只有出现跨宿主持久治理需求后，再评估共享 MCP/Core。

## 宿主规范依据

- [Codex Skills](https://learn.chatgpt.com/docs/build-skills)
- [Codex Plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Codex Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code Plugin Reference](https://code.claude.com/docs/en/plugins-reference)
