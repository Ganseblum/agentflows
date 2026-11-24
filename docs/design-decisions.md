# Agentflow 设计决策记录

> 用途：产品边界 / 宿主插件形态 / 自迭代三份早期设计文档于 2026-10-12 合并为本记录——保留决策、
> 边界原则与现时状态，去掉已实施的过程细节。版本以 manifest 与 `CHANGELOG.md` 为准，
> 本文不重复版本号。原三份文档的完整推理过程见 git 历史。
>
> 与产品链的关系：原 `docs/product/`（proposal → spec → design → plan）已于 2026-10-30 并入本文件 §4；
> 本记录为**决策出处**——被产品链引用为结论来源，冲突时以产品链为准并在此补翻案记录。

---

## 1. 产品边界：拆出独立主仓库

**决策**：将 Agentflow 提取为独立主仓库；旧 `multi-agent-cli` 保留为历史 runtime 与控制面研究项目，
不再作为本插件的安装或运行依赖。

**为什么**：原仓库含两个生命周期不同的产品（Go CLI 与跨宿主 Agent/Skill 范式），继续同仓会让
README、安装方式、版本与发布对象保持歧义。用户安装和使用的产品只有 Plugin；评测脚本、证据存储
或 MCP 属于维护与治理控制面，不提供第二套聊天 CLI。

**仓库边界**：插件源码包括 `agents/`、`skills/` 及宿主清单。打包生成 `packaging/runtime`。
项目说明和历史批次见[索引](../index.md)。

**宿主职责划分**：Codex / Claude Code 负责模型、认证、代码工具、权限、对话与子 Agent 生命周期；
Agentflow 负责角色、协作步骤、交接契约、评审、自迭代规则与版本治理。

**旧 CLI 的处理**：不继续发展 TUI、Provider 和第二套 Agent loop。可抽象复用的思想只有
`run_id + sequence` 追加事件与幂等重放、SQLite 原子投影、审批租约与幂等 resolve、Token 与成本
元数据规范化。不要直接迁移 `runner.Event`、Session、Provider、Workflow Runner 或 TUI——评测执行器
需要新的宿主适配协议。

---

## 2. 宿主原生 Plugin 形态

**目标产品**：一套可移植的开发范式——用户留在成熟编码宿主里，Agentflow 只定义如何组织工作。
运行路径中不调用本仓库的可执行文件、不启动第二层 TUI、不需要额外 Provider 凭证。

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

**为什么是 Skill + 薄宿主包装**：Codex 与 Claude Code 都支持基于 `SKILL.md` 的可复用工作流；
共享 Skill 定义主工作流，两边只保留必要差异。

| 能力 | Codex | Claude Code |
| --- | --- | --- |
| 调用入口 | `$agentflow` | `/agentflow:agentflow` |
| 工作流定义 | 共用 `skills/agentflow/SKILL.md` | 共用同一文件 |
| 多 Agent 执行 | 宿主原生 subagents | 宿主原生 subagents |
| 专用角色 | Skill 在任务简报中指定角色 | Plugin 提供实现/架构/审查/Bug/改进治理角色 |
| 权限与认证 | 继承当前任务 | 继承当前会话 |
| 留痕 | 任务与子 Agent 历史 | 会话与 Agent 历史 |

主工作流的权威定义在 [`skills/agentflow/SKILL.md`](../skills/agentflow/SKILL.md)（现为十步，含
Intake、架构门、角色选择、实现、集成、独立复核、有界修复、决策记录、记录落盘与升级判定）；
Supervisor 由当前会话担任，技术总监负责高成本技术决策。

**`my-agent` 的参考价值**：吸收五原则——Adapter 保持薄层、简报/回执/评审决策用稳定结构、
Supervisor 与技术决策与独立复核职责分离、重试有边界（连续相同失败触发重新规划）、能力不足时
明确降级。不照搬六阶段常驻治理进程、外部 Node adapter、SQLite 服务、发布供应链与执行文件哈希
固定——它们解决持久运行与企业治理问题，不是第一阶段必要条件。

**MCP 什么时候才需要**：当前不需要。只有出现「跨宿主查询同一份 Run 状态」「评审决策进集中审计」
「组织级审批/预算/身份/租户边界」「连接宿主没有的外部任务系统」时才增加可选 MCP；即使增加，
它也只提供状态、决策与审计工具，不负责启动另一套模型循环或 TUI。

**宿主规范依据**：[Codex Skills](https://learn.chatgpt.com/docs/build-skills) ·
[Codex Plugins](https://learn.chatgpt.com/docs/build-plugins) ·
[Codex Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) ·
[Claude Code Skills](https://code.claude.com/docs/en/skills) ·
[Claude Code Plugins](https://code.claude.com/docs/en/plugins)

---

## 3. 反馈驱动自迭代（已裁撤）

改进环与评测装置已于 2026-10-29 整体裁撤。六个设计边界、评测套件设计原则、度量口径、
宿主适配协议与恢复清单见 [设计决策归档](design-decisions-archive.md#3-反馈驱动自迭代历史)。
当前方法改动走「明确反馈 + 有界候选 + 独立评审 + 人工授权」的批次流程；方法级改动一律
`measurement: none`，不表述为已验证的自动学习系统。

## §4 产品链历史（2026-10-30 并入，原 docs/product/）

2026-10-30 关闭「产品线完善」批，原文可从 Git 修订 `40147df:docs/product/` 取回。
下列内容记录当时的决定；现行入口见[文档交付链](../skills/agentflow/references/document-chain.md)和[打包与安装](../packaging/README.md)。

- **产品定位**：宿主原生多角色协作方法插件，不是运行时、Flow 画布或组织图；方法写一次，
  循环交给宿主。分发形态为 ZCode / Claude Code / Codex 插件，`marketplace.json` 的 `source`
  指向 `packaging/runtime` 生成树。
- **角色与默认路径**：10 个角色是按需取用的能力清单，默认路径短；角色分离 ≠ 环境隔离。
  Supervisor 是主会话，不是独立进程。
- **文档链**：proposal → spec → design → plan；spec 反审 proposal、design 冻结前独立评审、
  plan 引用冻结后的 design。
- **关键决策**：只做方法不做运行时；宿主插件载体；受治理的人工闭环；保护门单点声明；
  schema + 编译门；Markdown 融合计划；失败语义成文；瘦快照分发；manifest/CHANGELOG 是版本单点；
  评测仪器 2026-10-12 整线裁撤，方法级改动 `measurement: none`；文档链吸收（D12）与校验（D13）；
  边界如实声明（D14）。
- **评审处置**：需求评审 REV-2026-10-19-003 `approved`（F1–F12 全关闭）；技术方案评审
  一条评审记录经独立委派 L2 `approved`（2026-10-29，Design 冻结）。
- **计划处置**：PLAN-PRODUCT 8 ☑ / 6 本期不做；PLAN-LOOP 5 ☑ / 5 本期不做；T02 与 LOOP T09
  的对象已随评测装置/改进环裁撤注销，PRODUCT T09 的 Intake FTS5 再犯类检索已落。

---

## 对外口径（版本号以 manifest 为准）

Agentflow 提供风险分档、角色协作、独立评审和证据工具。机器检查范围以工具命令为准，
文档内容和业务验收由目标仓检查、主审与独立评审共同确认。方法改动按批次推进，无度量证据时记
`measurement: none`。已退役的评测与反馈设施见[历史归档](design-decisions-archive.md)。
