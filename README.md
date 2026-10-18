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

- 一个共享的开发 Skill 与<!-- count:agents -->14<!-- /count -->个角色档案：前端/后端一对、Technical Director、
  Reviewer、Investigator → Fixer → Recorder bug 链、Plan Architect、Test
  Planner/Executor 链，以及改进环的 Feedback Analyst、Candidate Engineer、Evaluator 与
  Release Governor；
- 机器可读的记录契约 schema：bug 记录、计划、再犯分类、评审记录、测试计划与测试执行
  （`schemas/`），以及 episode、候选与发布记录（`skills/improve/references/`）；
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

`validate.py protected` 防止清单被悄悄删减。`validate.py all` 运行全套九项检查——schema、
examples、记录产物、受保护清单、五份 manifest 一致性、文档面（含版本散文守卫与断链 /
退役路径扫描）、`tests/` 回归测试、文档链 linter 的判别自测，以及文档链 linter 对活文档面
（`docs/product/`、`docs/features/`）的扫描。失败即编译错误：修好它，或把输出退回 worker。

> 注意：门工具依赖宿主的 git 与文件系统语义。个别宿主会在 Python 解释器注入路径拦截（例如拦截 `mkdir(exist_ok=True)`），导致 `tests` 子项出现环境相关的 error 而非仓库缺陷。若在本机观察到 `validate.py all` 的 `tests` 子项报 2 个 error，请先在无此类注入的干净宿主复跑确认，再判定是否真有回归——本会话即观察到此类环境假红。

三个 Bug 角色是可选择的能力，而不是每个问题都必须走的固定仪式。对 material、
不确定、反复出现、跨层或高风险的 bug，使用完整的
Investigator → Fixer → Reviewer → Recorder 流程。对已有已知复现的小型低风险 bug，
Supervisor 可以合并诊断或记录环节，同时保持同样的证据门。Plan Architect 写计划；
Supervisor 授权并协调执行。独立的 Execution Coordinator 预留给未来的持久控制面——该角色当前不存在，不是可委派的能力，不得写进委派简报。

改进工作流是一个受治理的骨架。用 `python3 tools/lab/record_store.py index` 构建一次性的
SQLite FTS5 词法索引，再用 `query` 做显式检索；源记录保持权威，且不使用向量数据库。跨会话遥测、持久
检索、私有 holdout 服务、canary 灰度上线与自动回滚尚未实现。人工批准是默认的发布边界。

工作区包含一组确定性的门与工具（`tools/lab/`）：一个无依赖的契约与记录校验器
`validate.py`（九项检查：schema、示例、记录产物、受保护清单、五份 manifest 一致性、
文档面、仓库回归测试、文档链自测与活面扫描，外加安装快照漂移检查 `installed`）、
一个文档链 linter（`doc_chain.py`）、一个候选禁区检查（`isolation.py check-diff`）与一个
产物摘要工具（`artifact_digest.py`）；`record_store.py` 提供记录的一次性 SQLite FTS5
词法检索，`trend.py` 把改进环已有的信号（再犯档位、活面发现数、评审发现数、套件规模）
追加记录到 `docs/trend.jsonl`。真实模型 dogfood、私有 holdout 服务与安装/发布切换
仍在有意待办；评测装置已于 2026-10-12 裁撤（见
[`docs/design-decisions.md`](docs/design-decisions.md) §3）。

## 仓库布局

全仓只有一份文档索引：[`index.md`](index.md)，按「场景 → 入口」说明每类东西放在哪。
本文件不再手工复制目录树与计数——那样会和真实结构漂移。要看清各目录内部的形状，
看各目录自己的 `README.md`（`tools/lab/`、`schemas/`、`docs/features/`、`docs/issues/`、
`reviews/`、`episodes/`、`packaging/` 各有一份）。

粗线条，按面记：

- **交付给宿主的面**：`agents/`（角色档案）、`skills/`（`agentflow` 开发工作流与
  `improve` 自迭代环），以及五份 manifest（`plugin.json`、`marketplace.json`、
  `.zcode-plugin/`、`.claude-plugin/`、`.codex-plugin/`）。
- **契约与门**：`schemas/` 是记录契约；`tools/lab/` 是确定性的检查与工具——
  `validate.py`（全套检查）、`doc_chain.py`（文档链 linter）、`isolation.py`（候选禁区检查）、
  `artifact_digest.py`（产物摘要）、`record_store.py`（记录的一次性 FTS5 检索）、
  `trend.py`（改进环信号趋势）；`tests/` 是这些门工具的回归测试；`examples/` 是校验器的正反例。
  这一面的多数在 [`protected-paths.txt`](protected-paths.txt) 内，改动即门变更。
- **记录**：`docs/issues/`、`docs/features/`、`docs/releases/`、`episodes/`、`reviews/`。
- **文档**：`index.md` 加 `docs/` 下的产品链、`docs/system-guide.md`、`docs/design-decisions.md`、
  `docs/host-platform-facts.md`。
- **打包**：`packaging/` 生成 ZCode 的安装快照，`marketplace.json` 的 `source` 指向它。

第一次用这套方法，先读 [`docs/quickstart.md`](docs/quickstart.md)——先判断要不要走流程、走哪条
路、哪些规矩不能省，五分钟内可以开始。日常走查从 [`docs/system-guide.md`](docs/system-guide.md) 开始——工作流怎么流转、
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
