# Agentflow

Agentflow 是一个宿主原生的多 agent 开发工作流，面向 Codex、Claude Code、ZCode，
以及兼容的 Agent Skills 宿主。宿主掌管模型、认证、工具、权限、会话历史与 agent
执行。Agentflow 提供角色契约、测试先行执行、独立评审，以及一套受治理的改进方法。

它不调用也不要求独立的 `agentflow` CLI。

## 先读这张图

第一次进这个仓库、不知道从哪看起，按下面的四个问题走：

| 问题 | 去哪 | 一句话 |
| --- | --- | --- |
| **这是什么** | [`docs/quickstart.md`](docs/quickstart.md) · [`docs/system-guide.md`](docs/system-guide.md) | 宿主原生的多 agent 开发工作流：角色契约 + 委派 + 独立评审 + 受治理改进环，不是独立 CLI。 |
| **谁该看** | [`index.md`](index.md) 的「从这里开始」 | 想用这套方法交付功能的开发者、要改角色/契约/流程维护仓库的人、以及独立评审与发布授权的把关人。 |
| **怎么装** | 本节「使用」 + [`skills/agentflow/references/hosts.md`](skills/agentflow/references/hosts.md) | Codex/Claude Code 装插件；ZCode 跑 `packaging/build_runtime.py` 再从本地 marketplace 装（指向 `packaging/runtime`，不是本目录）。 |
| **怎么参与** | [`AGENTS.md`](AGENTS.md) · [`index.md`](index.md) · [`docs/issues/README.md`](docs/issues/README.md) | 小修走 `docs/issues/` 立 ISS；跨层/成批走 `docs/features/<批次>/`；拍板与待验收分别看 `docs/PENDING-DECISIONS.md` 与 `docs/releases/pending-test.md`；改动前先 `python3 tools/lab/validate.py all`。 |

> 全仓只有一份文档索引：[`index.md`](index.md)，按「场景 → 入口」列全了每类东西在哪；本文件只补「四问」快表，不复制目录树。

## 使用

- Codex：安装插件并调用 `$agentflow`。仅在改进 Agentflow 自身时选择 **Agentflow Improve** 或
  调用 `$improve`。
- Claude Code：用 `claude --plugin-dir .` 启动开发，然后调用
  `/agentflow:agentflow` 或 `/agentflow:improve`。
- ZCode：运行 `python3 packaging/build_runtime.py`，再从
  [`marketplace.json`](marketplace.json) 中的本地 marketplace 安装（它指向 `packaging/runtime`，不是本目录）。
  Skill 通过 `.zcode/skills/` 符号链接解析，但 **agent 从安装快照加载**——改动 `agents/*.md` 之后，
  重新生成运行时树、刷新 marketplace 并重装，然后用 `python3 tools/lab/validate.py installed` 确认。
  若用过 Host Init（宿主级全局规则），重装后还要按 [`skills/agentflow/references/hosts.md`](skills/agentflow/references/hosts.md)
  重跑一次，让宿主全局指令文件里的托管块与当前版本对齐。

## 执行入口

日常按“查现状与定边界 → 准备与批准 → 连续执行与验证 → 独立评审与交付”阅读。执行细则集中在[执行与验证](skills/agentflow/references/execution.md)，轻量或完整材料按[文档档位](skills/agentflow/references/document-chain.md#文档档位)选择；证据工具随插件交付，不增加独立运行系统。

## 当前成熟度

版本只在五份 manifest 与 [CHANGELOG.md](CHANGELOG.md) 中声明一次；本文件从不重复它。交付形态：一个共享开发 Skill 加<!-- count:agents -->14<!-- /count -->个角色档案、六份记录契约 schema、Codex / Claude Code / ZCode 与可移植 Agent Plugin 清单。怎么流转、记录落哪、门怎么跑，看 [`docs/system-guide.md`](docs/system-guide.md)——本文件不复述，避免同一件事两处维护。

两条别处没有的边界说明：

- 实现型角色声明显式的工具白名单（`Read, Glob, Grep, Write, Edit, Bash`），宿主据此约束 worker 的工具面；Bash 仍遵循宿主的沙箱，且可能具备工具名未暗示的能力，网络隔离必须从宿主处核实，不得从这份清单推断。
- 独立的 Execution Coordinator 预留给未来的持久控制面——该角色当前不存在，不是可委派能力，不得写进委派简报。

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
examples、记录产物、受保护清单、五份 manifest 一致性（含 `packaging/runtime` 生成树新鲜度）、文档面（含版本散文守卫与断链 /
退役路径扫描）、`tests/` 回归测试、文档链 linter 的判别自测、文档链 linter 对活文档面
（`docs/product/`、`docs/features/`）的扫描、追溯类检查 decision_gate
（C15–C18 与 C22–C23，标记启用），以及 lint（ruff + mypy，依赖
`requirements-dev.txt`）。项数以 `python3 tools/lab/validate.py --list` 自报为准，本文不写它。
失败即编译错误：修好它，或把输出退回 worker。

> 注意一（`lint` 缺依赖是环境红，不是回归）：本机未装 `requirements-dev.txt` 里的 ruff/mypy 时，`validate.py all` 会以 `FAIL lint (2 error(s))` 退出 1——这是**有意的 fail-closed**。装好依赖后同一命令应全绿（CI 即如此，见 `.github/workflows/validate.yml` 的安装步）。`skills/agentflow/scripts/pre-push.sh` 对**待推送提交的临时检出**跑同一套门：缺 ruff/mypy 时把 `lint` 记为「未运行」并**默认拦下**推送，只有显式设 `AGENTFLOW_PREPUSH_ALLOW_UNRUN=1` 才放行并保留告警；其余项照常判红。用 `AGENTFLOW_GATE_PYTHON`（兼容 `AGENTFLOW_LINT_PYTHON`）指向装好依赖的解释器即可实跑 lint。
>
> 注意二（`tests` 子项可能环境假红）：门工具依赖宿主的 git 与文件系统语义。个别宿主会在 Python 解释器注入路径拦截（例如拦截 `mkdir(exist_ok=True)`），导致 `tests` 子项出现环境相关的 error 而非仓库缺陷。若在本机观察到 `validate.py all` 的 `tests` 子项报 2 个 error，请先在无此类注入的干净宿主复跑确认，再判定是否真有回归。

三个 Bug 角色是可选择的能力，而不是每个问题都必须走的固定仪式。对 material、
不确定、反复出现、跨层或高风险的 bug，使用完整的
Investigator → Fixer → Reviewer → Recorder 流程。对已有已知复现的小型低风险 bug，
主审可以合并诊断或记录环节，同时保持同样的证据门。Plan Architect 写计划；
主审授权并协调执行。

改进工作流是一个受治理的骨架：会话收口（一项工作收尾并落档）先落 episode，Feedback Analyst 归一化证据，
Candidate Engineer 在 candidate worktree 里实现单个候选，`isolation.py check-diff` 对照冻结
parent revision 拒绝触碰禁区，Evaluator 与 Release Governor 只读评审，最终由人批准。跨会话
遥测、持久检索、私有 holdout 服务、canary 灰度上线与自动回滚尚未实现；人工批准是默认的
发布边界。检索是一次性的 SQLite FTS5 词法索引（`record_store.py`），源记录保持权威，
不使用向量数据库。完整流程与两条诚实规则见
[`docs/system-guide.md`](docs/system-guide.md) §5。

工作区包含一组确定性的门与工具（`tools/lab/`）：契约与记录校验器 `validate.py`
（全套检查，项数与内容以 `python3 tools/lab/validate.py --list` 为准；另加安装快照漂移检查
`installed`；检查函数均已拆入 `tools/lab/gate/` 模块包，`validate.py` 保留为薄入口）、
文档链 linter（`doc_chain.py`）、候选禁区检查（`isolation.py check-diff`）与产物摘要工具
（`artifact_digest.py`）。逐项管什么、失败时第一反应是什么，见
[`docs/system-guide.md`](docs/system-guide.md) §7 与 [`tools/lab/README.md`](tools/lab/README.md)；
真实模型 dogfood、私有 holdout 服务与安装/发布切换仍在有意待办；评测装置已于 2026-10-12
裁撤（见 [`docs/design-decisions.md`](docs/design-decisions.md) §3）。

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
  `validate.py` 薄入口 + `gate/` 检查模块包（全套检查）、`doc_chain.py`（文档链 linter）、
  `isolation.py`（候选禁区检查）、`artifact_digest.py`（产物摘要）、`counts.py`（文档计数
  标记核对）、`mutate.py`（门变异测试）、`record_store.py`（记录的一次性 FTS5 检索）、
  `trend.py`（改进环信号趋势）；`tests/` 是这些门工具的回归测试；`examples/` 是校验器与
  文档链 linter 的正反例。
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

源码检出的版本活在 manifest 中（`python3 tools/lab/validate.py manifests` 断言五份一致，
并顺带核对 `packaging/runtime` 生成树与源面逐字节一致）。声明了
版本本身并不证明某个宿主正在运行该版本：ZCode 加载安装快照，Codex 可能加载单独的插件缓存。
dogfood 之前，用 `python3 tools/lab/validate.py installed
--path <installed-plugin-root>`（或宿主特定的默认值）比对实际的宿主快照并记录结果。
在首次人工门控的 dogfood 运行使用经验证的模型端点之前，不得切换安装。
