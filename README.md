# Agentflow

Agentflow 是一个宿主原生的多 agent 开发工作流，面向 Codex、Claude Code、ZCode，以及兼容的 Agent Skills 宿主。宿主掌管模型、认证、工具、权限、会话历史与 agent 执行。Agentflow 提供角色契约、测试先行执行、独立评审，以及一套受治理的方法演进流程。

它不调用也不要求独立的 `agentflow` CLI。

## 先读这张图

第一次进这个仓库、不知道从哪看起，按下面的四个问题走：

| 问题 | 去哪 | 一句话 |
| --- | --- | --- |
| **这是什么** | [`docs/quickstart.md`](docs/quickstart.md) · [`docs/system-guide.md`](docs/system-guide.md) | 宿主原生的多 agent 开发工作流：角色契约 + 委派 + 独立评审 + 受治理的方法演进，不是独立 CLI。 |
| **谁该看** | [`index.md`](index.md) 的「从这里开始」 | 想用这套方法交付功能的开发者、要改角色/契约/流程维护仓库的人、以及独立评审与发布授权的把关人。 |
| **怎么装** | 本节「使用」 + [`skills/agentflow/references/hosts.md`](skills/agentflow/references/hosts.md) | Codex/Claude Code 装插件；ZCode 跑 `packaging/build_runtime.py` 再从本地 marketplace 装（指向 `packaging/runtime`，不是本目录）。 |
| **怎么参与** | [`AGENTS.md`](AGENTS.md) · [`index.md`](index.md) | 小修走会话结论；跨层/成批走 `docs/features/<批次>/`；改动前先确认产物对实际文件成立。 |

> 全仓只有一份文档索引：[`index.md`](index.md)，按「场景 → 入口」列全了每类东西在哪；本文件只补「四问」快表，不复制目录树。

## 使用

- Codex：安装插件并调用 `$agentflow`。
- Claude Code：用 `claude --plugin-dir .` 启动开发，然后调用 `/agentflow:agentflow`。
- ZCode：运行 `python3 packaging/build_runtime.py`，再从 [`marketplace.json`](marketplace.json) 中的本地 marketplace 安装（它指向 `packaging/runtime`，不是本目录）。Skill 通过 `.zcode/skills/` 符号链接解析，但 **agent 从安装快照加载**——改动 `agents/*.md` 之后，重新生成运行时树、刷新 marketplace 并重装，让宿主全局指令文件里的托管块与当前版本对齐（见 [`skills/agentflow/references/hosts.md`](skills/agentflow/references/hosts.md)）。

## 执行入口

日常按“查现状与定边界 → 准备与批准 → 连续执行与验证 → 独立评审与交付”阅读。执行细则集中在[执行与验证](skills/agentflow/references/execution.md)，轻量或完整材料按[文档档位](skills/agentflow/references/document-chain.md#文档档位)选择；证据工具随插件交付，不增加独立运行系统。

## 当前成熟度

版本只在 manifest 与 [CHANGELOG.md](CHANGELOG.md) 中声明一次；本文件从不重复它。交付形态：一个共享开发 Skill 加 <!-- count:agents -->10<!-- /count --> 个角色档案、Codex / Claude Code / ZCode / Qoder 与可移植 Agent Plugin 清单。怎么流转、记录落哪、方法怎么演进，看 [`docs/system-guide.md`](docs/system-guide.md)——本文件不复述，避免同一件事两处维护。

两条别处没有的边界说明：

- 实现型角色声明显式的工具白名单（`Read, Glob, Grep, Write, Edit, Bash`），宿主据此约束 worker 的工具面；Bash 仍遵循宿主的沙箱，且可能具备工具名未暗示的能力，网络隔离必须从宿主处核实，不得从这份清单推断。
- 独立的 Execution Coordinator 预留给未来的持久控制面——该角色当前不存在，不是可委派能力，不得写进委派简报。

三个 Bug 角色是可选择的能力，而不是每个问题都必须走的固定仪式。对 material、不确定、反复出现、跨层或高风险的 bug，使用完整的 Investigator → Fixer → Reviewer → Recorder 流程。对已有已知复现的小型低风险 bug，主审可以合并诊断或记录环节，同时保持同样的证据要求。Plan Architect 写计划；主审授权并协调执行。

改进环已于 2026-10-29 整体裁撤：方法改动改走「明确反馈 + 有界候选 + 独立评审 + 人工授权」的成批流程；跨会话遥测、持久检索、私有 holdout 服务、canary 灰度上线与自动回滚未实现；人工批准是默认的发布边界。检索是一次性的 SQLite FTS5 词法索引（`记录检索`，若仍随本仓提供），源记录保持权威，不使用向量数据库。

## 仓库布局

全仓只有一份文档索引：[`index.md`](index.md)，按「场景 → 入口」说明每类东西放在哪。本文件不再手工复制目录树与计数——那样会和真实结构漂移。要看清各目录内部的形状，看各目录自己的 `README.md`。

**先分清你是哪类使用者**——同一个仓库装着两件东西，它们平时不该互相干扰：

### A. 产品面（装进宿主、给目标仓用的）

| 路径 | 是什么 |
| --- | --- |
| `agents/` | 10 个角色档案（reviewer、backend-engineer…） |
| `skills/agentflow/` | 主方法：`SKILL.md` + `references/` + `templates/` + `scripts/` |
| `skills/agentflow-intake/`、`skills/agentflow-grilling/` | 两条方法的**直接调用入口**（用户主动叫时用） |
| `skills/design-diagram/` | 设计图能力 |
| `packaging/runtime/` | 上面这些的**生成副本**，`marketplace.json` 装的就是它 |

### B. 维护面（维护这套方法自己用的，目标仓看不到）

| 路径 | 是什么 |
| --- | --- |
| `docs/` | 本仓的设计文档、使用指南、宿主事实与计划形态说明 |
| `packaging/` | 生成 ZCode 的安装快照，`marketplace.json` 的 `source` 指向它 |
| `index.md` · `README.md` · `AGENTS.md` | 仓内索引与纪律 |

### 粗线条，按面记

- **交付给宿主的面**：`agents/`（角色档案）、`skills/`（`agentflow` 开发工作流），以及各 manifest（`plugin.json`、`marketplace.json`、`.zcode-plugin/`、`.claude-plugin/`、`.codex-plugin/`、`.qoder-plugin/`）。
- **文档**：`index.md` 加 `docs/` 下的产品链、`docs/system-guide.md`、`docs/design-decisions.md`、`docs/host-platform-facts.md`。
- **打包**：`packaging/` 生成 ZCode 的安装快照，`marketplace.json` 的 `source` 指向它。

第一次用这套方法，先读 [`docs/quickstart.md`](docs/quickstart.md)——先判断要不要走流程、走哪条路、哪些规矩不能省，五分钟内可以开始。日常走查从 [`docs/system-guide.md`](docs/system-guide.md) 开始——工作流怎么流转、什么记录到哪里、失败如何处理（含图示与完整示例）；角色路由见 [`skills/agentflow/references/roles.md`](skills/agentflow/references/roles.md)。然后参见 [`docs/design-decisions.md`](docs/design-decisions.md) 了解产品边界、宿主形态与自迭代的设计决策，[`docs/host-platform-facts.md`](docs/host-platform-facts.md) 了解已观察到的宿主约束；每个版本为何变更见 [`CHANGELOG.md`](CHANGELOG.md) 各版本条目。

源码检出的版本活在 manifest 中；声明了版本本身并不证明某个宿主正在运行该版本：ZCode 加载安装快照，Codex 可能加载单独的插件缓存。dogfood 之前，先确认本机重装完成、宿主实际加载的是新版本。
