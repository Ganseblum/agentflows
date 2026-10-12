# Agentflow

Agentflow 是一个宿主原生的多 agent 开发工作流，面向 Codex、Claude Code、ZCode，
以及兼容的 Agent Skills 宿主。宿主掌管模型、认证、工具、权限、会话历史与 agent
执行。Agentflow 提供角色契约、委派规则、独立评审，以及一套受治理的改进方法。

它不调用也不要求独立的 `agentflow` CLI。

## 使用

- Codex：安装插件并调用 `$agentflow`。仅在改进 Agentflow 自身时选择 **Agentflow Improve** 或
  调用 `$improve`。
- Claude Code：用 `claude --plugin-dir .` 启动开发，然后调用
  `/agentflow:agentflow` 或 `/agentflow:improve`。
- ZCode：运行 `python3 packaging/build_runtime.py`，再从
  [`marketplace.json`](marketplace.json) 中的本地 marketplace 安装（它指向 `packaging/runtime`，不是本目录）。
  Skill 通过 `.zcode/skills/` 符号链接解析，但 **agent 从安装快照加载**——改动 `agents/*.md` 之后，
  重新生成运行时树、刷新 marketplace 并重装，然后用 `python3 tools/lab/validate.py installed` 确认。

## 当前成熟度

版本只在五份 manifest 与 [CHANGELOG.md](CHANGELOG.md) 中声明一次；本文件从不重复它。当前发布提供：

- 一个共享的开发 Skill 与十四个角色档案：前端/后端一对、Technical Director、
  Reviewer、Investigator → Fixer → Recorder bug 链、Plan Architect、Test
  Planner/Executor 链，以及改进环的 Feedback Analyst、Candidate Engineer、Evaluator 与
  Release Governor；
- 机器可读的 bug、计划、episode、候选、评测用例、评测结果与发布记录 schema；
- Codex、Claude Code、ZCode 与可移植的 Agent Plugin 清单。

实现型角色声明显式的工具白名单（`Read, Glob, Grep, Write, Edit, Bash`），因此
worker 不会通过该白名单获得宿主原生的委派工具或 MCP 工具。Bash
仍遵循宿主的沙箱，且可能具备工具名未暗示的能力；网络隔离必须从宿主处核实，
不得从这份清单推断。`bug-recorder` 只写 `docs/issues/` 下被显式指派的脱敏记录，
`plan-architect` 只写批次 `plan/` 下被显式指派的计划。两个角色都不能关闭 bug、
授权代码执行或发布 Plugin。Supervisor 必须检查产出的实际路径与验证证据，因为宿主
不会对 `Write` 工具强制任意路径约束；见 [AGENTS.md](AGENTS.md)。

候选门面——evaluator 与 governor 角色文件、测量路径（digest / isolation）、发布规则、
`schemas/` 下的记录 schema、钉住的回归测试，以及清单本身——在
[`protected-paths.txt`](protected-paths.txt) 中声明一次。`isolation.py check-diff` 拒绝
触碰它的候选 diff。从受信源码检出出发，以冻结的 parent revision 运行它：

```sh
python3 tools/lab/isolation.py check-diff \
  --candidate <tree> \
  --base <frozen-parent-revision>
```

`validate.py protected` 防止清单被悄悄删减。`validate.py all` 运行全套检查——schema、
examples、记录产物、受保护清单、manifest 一致性、
文档面（含断链与退役路径扫描）、文档链 linter 的判别自测，以及仓库自身的回归测试。

三个 Bug 角色是可选择的能力，而不是每个问题都必须走的固定仪式。对 material、
不确定、反复出现、跨层或高风险的 bug，使用完整的
Investigator → Fixer → Reviewer → Recorder 流程。对已有已知复现的小型低风险 bug，
Supervisor 可以合并诊断或记录环节，同时保持同样的证据门。Plan Architect 写计划；
Supervisor 授权并协调执行。独立的 Execution Coordinator 预留给未来的持久控制面。

改进工作流是一个受治理的骨架。用 `python3 tools/lab/record_store.py index` 构建一次性的
SQLite FTS5 词法索引，再用 `query` 做显式检索；源记录保持权威，且不使用向量数据库。跨会话遥测、持久
检索、私有 holdout 服务、canary 灰度上线与自动回滚尚未实现。人工批准是默认的发布边界。

工作区包含 P0 实现切片：Bug Record 与 Plan 契约、脱敏的正/反例、十五个公开评测用例、
一个无依赖的契约校验器（含安装快照漂移检查）、一个显式的宿主适配器结果协议、
隔离检查、一个 fail-closed 的 Codex/Claude 宿主适配器包装器，以及一个确定性策略评估器。
真实模型 dogfood、私有 holdout 服务与安装/发布切换仍在有意待办。

## 仓库布局

| 路径 | 内容 |
| --- | --- |
| `agents/` | 宿主加载的十四个角色档案（公开角色面） |
| `skills/` | `agentflow`（开发工作流）与 `improve`（受治理的自迭代环），及其参考契约 |
| `schemas/` | 编译步骤强制执行的记录与结果契约（受保护） |
| `tools/lab/` | 确定性门与工具：`validate.py`、`doc_chain.py`、`isolation.py`、`record_store.py`、`artifact_digest.py`（受保护） |
| `tests/` | 门工具的钉住回归测试（受保护） |
| `index.md` | 唯一的文档索引：场景 → 入口、维护纪律、迁移清单 |
| `features/` | 按批次的文档链：`feature-<date>-<topic>/{README, proposal, spec, design, plan, reviews, testing, episodes, improvement}` |
| `docs/issues/` | 缺陷与事项流：平铺的 `ISS-<YYYY>-<NNN>-<slug>.md` 记录、`recurrence/` 台账、`归档/` 存放被拒记录；看板与规则见 `docs/issues/README.md` |
| `episodes/` | 任务级决策记录（`EP-*.json`）——改进环的燃料（规则见 `episodes/README.md`） |
| `docs/features/` | 批次目录（五段骨架；含批次内计划 `<batch>/plan/<plan_id>.md`；规则见 `docs/features/README.md`） |
| `docs/releases/` | 在途批次索引（`todo.md`）与待验收清单（`pending-test.md`）；逐版本发布记录已停用，版本史见 `CHANGELOG.md` |
| `reviews/` | 外部仓库的评审记录（`<project>-<feature-slug>/review-<date>-<NNN>.md` 加归档快照；规则见 `reviews/README.md`） |
| `examples/` | 校验器 fixture——正例、反例与完整示例 |
| `docs/` | 设计、指南与事实文档：产品设计链、体系使用指南、宿主平台事实 |
| `packaging/` | 生成的 ZCode 安装面（`build_runtime.py` → `runtime/`）；marketplace 的 `source` 指向这里 |
| `protected-paths.txt` | 候选门面，只声明一次 |
| manifests | `plugin.json`、`marketplace.json`、`.zcode-plugin/`、`.claude-plugin/`、`.codex-plugin/` |

日常走查从 [`docs/system-guide.md`](docs/system-guide.md) 开始——工作流怎么流转、
改进环怎么运行、什么记录到哪里、失败如何处理（含图示与完整示例）；角色路由见
[`skills/agentflow/references/roles.md`](skills/agentflow/references/roles.md)。然后参见
[`docs/design-decisions.md`](docs/design-decisions.md) 了解产品边界、宿主形态与自迭代的设计决策，
[`docs/host-platform-facts.md`](docs/host-platform-facts.md) 了解已观察到的宿主约束；
每个版本为何变更见 [`CHANGELOG.md`](CHANGELOG.md) 各版本条目。

源码检出的版本活在 manifest 中（`python3 tools/lab/validate.py manifests` 断言五份一致）。声明了
版本本身并不证明某个宿主正在运行该版本：ZCode 加载安装快照，Codex 可能加载单独的插件缓存。
dogfood 之前，用 `python3 tools/lab/validate.py installed
--path <installed-plugin-root>`（或宿主特定的默认值）比对实际的宿主快照并记录结果。
在首次人工门控的 dogfood 运行使用经验证的模型端点之前，不得切换安装。
