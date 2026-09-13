# Agentflow 角色与协作协议

Agentflow 的角色是能力边界，不是每个任务都必须启动的固定流水线。Supervisor 根据任务
选择角色，宿主负责模型、工具、权限和生命周期。

| 角色 | 主要职责 | 是否改代码 | 主要产物 |
| --- | --- | --- | --- |
| Supervisor | 明确范围、调度、集成、最终交付 | 可以在集成阶段 | 决策与交付结果 |
| Frontend Engineer | 前端实现、状态、交互和客户端契约 | 是 | 前端变更与验证 |
| Backend Engineer | API、数据、服务端逻辑和迁移 | 是 | 后端变更与验证 |
| Technical Director | 跨层接口、架构、风险和顺序决策 | 否 | 技术决策 |
| Reviewer | 独立检查实现、回归和权限边界 | 否 | review 决定 |
| Bug Investigator | 发现、复现描述和根因归因 | 否 | Bug 诊断 |
| Bug Fixer | 在候选工作区实施单个 Bug 修复 | 是 | 修复与回归检查 |
| Bug Recorder | 保存脱敏 Bug 记录和适用边界 | 只写记录 | `records/bugs/*` |
| Plan Architect | 汇总专业意见并生成可执行计划 | 只写计划 | `plans/*` |

## Bug 标准完整流程

三个 Bug 角色保留为独立能力边界，但不是每个问题都必须启动三个独立 Agent。完整流程
还包含 Reviewer 这个独立审查门：

```text
用户反馈 / 失败轨迹
        ↓
Bug Investigator
        ↓
Bug Fixer（隔离候选工作区）
        ↓
确定性测试 + Reviewer
        ↓
Bug Recorder
        ↓
反馈池 / 后续评测
```

Bug Recorder 不能把“Agent 说已修复”当作验证结果。至少要有可追溯的复现证据、回归
检查和 Reviewer 结论。未确认的 Bug 也可以记录，但状态必须保持 `open` 或
`fixed-pending-review`。

按风险裁剪：

| 场景 | Investigator | Fixer | Reviewer | Recorder |
| --- | --- | --- | --- | --- |
| 小范围、低风险、已有确定复现 | Supervisor 可合并 | 需要 | 可由 Supervisor 自检 | 可合并或记录 `fixed-pending-review` |
| 单模块逻辑 Bug | 建议启用 | 需要 | 建议启用 | 要沉淀经验时启用 |
| 跨模块、API、数据、权限、并发或宿主问题 | 必须 | 必须 | 必须 | 建议启用 |
| 安全、数据损坏、发布或不可逆影响 | 必须，可加 Technical Director | 隔离工作区 | 必须独立审查 | 必须，并需要人工发布门 |
| 只做诊断或只记录已知问题 | 诊断时需要 | 不需要 | 使用已有证据 | 记录时需要 |

角色合并不等于跳过阶段。Supervisor 仍要保存诊断、修复、验证、审查和记录字段；
Fixer 永远不能批准或关闭自己修复的 Bug。

## 计划流程

```text
需求
  ├── Frontend Engineer
  ├── Backend Engineer
  └── Technical Director
          ↓
    Plan Architect
          ↓
  计划审查 / 用户确认
          ↓
    并行执行与集成
```

Plan Architect 的产物是执行合同，不是代码变更授权。计划中必须把前后端接口、状态、
错误处理、依赖、可并行工作包、验收方式、Reviewer 门和回滚点写清楚。计划本身需要
版本号和输入证据引用，后续才能比较“计划问题”与“执行问题”。

Plan Architect 只负责把证据转换成版本化计划。计划通过后，由 Supervisor 负责执行授权、
角色调度、并行批次、集成、停止和回滚。未来需要跨进程恢复、租约、重试和长期队列时，
再增加 `Execution Coordinator`；它负责运行状态和调度，不取代 Supervisor 的最终决策。

当前不新增通用的“任务记录 Agent”。宿主会话和事件历史负责基础留痕，Plan Architect
负责计划记录，Bug Recorder 负责 Bug 证据；只有出现跨宿主持久控制面需求时，才增加
统一 Evidence Recorder/Store。

## 与自迭代的关系

Bug 记录是 Episode 的一种来源，不是生产 Memory。只有经过归因、独立评测和发布门的
经验才能进入 `memory/validated`。计划记录则提供 workflow 和执行顺序的证据，可用于
发现“遗漏接口、并行冲突、审核过晚”等系统性问题。

当前 `bug-recorder` 和 `plan-architect` 的写入范围主要靠角色说明与宿主权限约束；
在实现确定性 Policy Engine 前，必须由 Supervisor 检查输出路径和 diff。
