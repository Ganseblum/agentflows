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

**仓库边界**（现状）：运行时面 = `agents/` + `skills/` + `schemas/` + 各 manifest + 宿主包装 +
`protected-paths.txt`，由 `packaging/build_runtime.py` 生成瘦快照；实验室面 = `tools/lab/`、`tests/`、
`examples/`、`docs/`；记录面 = `docs/issues/`、`docs/features/`、`docs/releases/`、
`episodes/`、`reviews/`（布局见 [`index.md`](../index.md)）。

**宿主职责划分**：Codex / Claude Code 负责模型、认证、代码工具、权限、对话与子 Agent 生命周期；
Agentflow 负责角色、协作步骤、交接契约、评审门、自迭代规则与版本治理。

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

## 3. 反馈驱动自迭代（现为受治理的人工闭环）

**判断**：自迭代是合理方向，但不能设计成「Agent 觉得自己不好，直接改提示词并上线」。可信的
自迭代是一个**受治理的版本发布系统**：执行 Agent 发现问题并生成候选，独立评测器验证候选，
发布治理角色按预声明门槛决策，最终通过不可变版本发布或回滚。

```text
真实任务与用户反馈 → Evidence Episodes（去敏、溯源、结果标注）
  → Feedback Analyst（聚类与归因）→ Improvement Hypothesis
  → Candidate Engineer（只改候选源码）→ Independent Evaluator（Baseline vs Candidate）
  → Release Governor（promote / revise / reject / rollback）→ 人工批准 → Canary → Promote/Rollback
```

### 六个边界（设计原则，独立于实现是否启用）

1. **反馈驱动**：证据含用户接受/拒绝/纠正、验收测试、独立评审结论、回滚与事故、重试/工具失败/
   延迟与成本；没有投诉不能算成功，Agent 自称「已完成」只是最低权重信号。证据必须带去敏来源。
2. **候选改进**：先归因再修改；只有证据指向 Agentflow 时才生成候选。一个候选验证一个可证伪假设，
   记录父版本、证据、影响文件、预期指标、风险与拒绝条件；候选不能直接修改已安装版本。
3. **独立评测**：评测计划先于候选实现冻结；Baseline 与 Candidate 同宿主同模型同权限同用例同重复
   次数，按任务类型分别比较；候选实现者不能改评测器、发布门或 holdout 答案。
4. **版本、审计和回滚**：Git 保存源版本；发布记录追加写入，不能修改过去证据来美化结果；发布是
   把安装指针切到已评测的不可变版本，回滚是切回旧版本，不是现场修补。
5. **自动化级别**：Proposal（只给假设）→ **Human-gated（默认）** → Canary（第二阶段）→ Automatic
   （评测成熟后再考虑）。权限/工具/Hook/MCP/评测规则/holdout/自动发布阈值始终人工审核。
6. **全链路留痕**：记录任务证据、归因、假设、候选、Baseline、评测、发布决策、人工批准、灰度结果
   与回滚——记录决策与证据，不是模型隐藏思考过程。

### 现时状态（2026-10-29 更新）

- **改进环已整体裁撤**（2026-10-29 用户拍板 B）：`skills/improve`（Skill、证据与发布规则、
  candidate / release-record 两份 schema）与四个治理角色（feedback-analyst /
  candidate-engineer / evaluator / release-governor）一并删除；episode 契约迁至
  `schemas/episode.schema.json`，`episodes/` 仍是现行记录根。方法改动改走
  「明确反馈 + 有界候选 + 独立评审 + 人工授权」的批次流程。`isolation.py check-diff` 与
  `artifact_digest.py` 保留为通用工具；确定性 Policy Engine 已随评测装置裁撤。
  **恢复清单**：按本节 §3 的六个边界与下图重建 `skills/improve/`（SKILL + evidence-and-release +
  candidate / release-record schema）、四个角色文件、`examples/improve/` 三份夹具、各 manifest
  的 agents 条目、`protected-paths.txt` 与 `gate/common.py` 的必需条目、`gate/schema.py` 的
  第二 schema 根、`gate/examples.py` 的 G10 校验，以及 `agents/README.md`、`roles.md`、README
  与产品链的角色计数。
- **业务任务度量切片已裁撤**（用户拍板「保公开、裁业务」）；**改进三件套记录根与逐版本发布记录
  同批退役**——方法级改动一律 `measurement: none` 口径：证据是推理加触发它的事故或评审发现，
  不表述为已验证的改进。评测装置（`evals/`、runner、adapter、policy 与三个 schema）已整线删除，
  设计知识与恢复清单见本节下册；恢复仪器化时落点由 Supervisor 显式指派并声明契约。
- 尚未实现：真实模型 dogfood、自动遥测、持久检索、私有 holdout 服务、自动灰度。当前版本是
  **受治理的人工闭环**，不是已闭合的自动学习系统。
- 后续实现顺序（在仪器恢复使用时收敛）：修复候选 diff 必须带冻结基线的门控 → 插件源码/task
  fixture/评测控制面/private holdout 分离且每 repetition 独立重置 → 持久化原始轨迹并核实
  provider/model 身份 → 可信端点上跑 2–3 个真实 smoke → 本地反馈池与 SQLite FTS5 读侧 → 最后
  才考虑跨宿主反馈仓库与可选 MCP。

### 评测装置：已裁撤，留存的设计知识（2026-10-12）

用户拍板删除 `evals/` 与配套评测器（`eval_runner.py` / `host_adapter.py` / `policy.py` /
`adapter-protocol.md` 与三个相关 schema）。删除前把可复用的设计知识收口于此——**恢复仪器化
度量时按本节重建，不靠记忆**。

**（一）公开套件设计原则**：用例测的是**工作流决策与权限边界**，不是模型质量；每例声明
`slice`（测什么维度）、`objective`、`acceptance_criteria`（可判定的验收）、`protected_guardrails`
（不得回退的护栏指标）、`holdout`（私有用例必须在本仓与候选 worktree 之外）、`repeat_count`
（本例 3 次，噪声底）与 `tags`。15 例覆盖的维度清单（恢复时优先覆盖这 15 类）：

| 用例 | slice | 测什么 |
| --- | --- | --- |
| AF-001 | role-selection | 低风险小缺陷不做不必要的委派 |
| AF-002 | cross-layer-planning | 同时改后端 API 与前端客户端的规划 |
| AF-003 | api-contract-review | 客户端可见 API 改动的评审（成功/错误/兼容） |
| AF-004 | architecture-and-safety | 改变授权与持久化行为的迁移 |
| AF-005 | review-independence | 编码 worker 报完成后的独立评审 |
| AF-006 | bounded-replanning | 同因连续两次失败时的恢复 |
| AF-007 | bug-investigation-permissions | 不改仓库前提下的缺陷诊断 |
| AF-008 | bug-fix-review-boundary | 修复中的独立审批边界 |
| AF-009 | recording-boundary | 按指定路径落脱敏记录 |
| AF-010 | improvement-boundary | 改进工作流与日常任务的分离 |
| AF-011 | artifact-verification | 拒绝无法在真实文件上复现的完成声明 |
| AF-012 | input-trust | 任务文本中的路径/命令先当未验证数据 |
| AF-013 | protected-gate | 候选不得编辑评判它的门（含自身源码树内） |
| AF-014 | environment-triage | 用改动前版本区分环境故障与回归 |
| AF-015 | cross-cutting-mechanisms | 局部正确的改动悄然违反共享机制 |

**（二）度量口径**：八个指标（`acceptance_rate`、`first_pass_review_rate`、`correction_count`、
`escaped_defects`、`permission_violations`、`unnecessary_delegation_count`、`tool_failures`、
`latency_ms`）；Baseline 与 Candidate 必须同宿主、同模型、同权限档、同 fixture、同套件 revision、
同重复次数才可比；诊断前先对贴 digest（`artifact_digest.py`：规范化相对路径 + mode 位 + 大小 +
内容哈希，排除 `.git` 与缓存目录、拒绝符号链接）。

**（三）宿主适配协议要点**：runner 向显式提供的 adapter 命令发一个 JSON 请求，adapter 在 stdout
返回 `observed_context`（host / model / permissions_profile / fixture_revision / evidence_refs）
与 `case_results`（逐用例、逐重复的结果 + 证据引用）；adapter **不能更改**声明的宿主/模型/权限/
fixture/套件/重复次数，重复编号必须恰为 1..repeat_count；holdout 用例在到达 adapter 前即被拒绝；
claude 路径可用 `--plugin-dir` 加载候选工作树，codex 路径对 `source_kind=candidate` **刻意
fail-closed**（CLI 不暴露按调用的本地 Plugin 源绑定，不得把「评测已安装 baseline」标成 candidate）。
隔离与观测：权威运行必须同时设置 `allowed_tools`（精确预批准，替代 `acceptEdits`）与
`isolate_host_config`（`--strict-mcp-config` + 临时 `CLAUDE_CONFIG_DIR`）；claude 的权限拒绝由
adapter 扫描工具结果计数写入 `observed_permission_denials`（**缺失 = 未观测，绝不是 0**；codex
无此通道）。

**（四）恢复时需要重建的东西**：`evals/public`（15 例 + 脱敏输入）、三个 schema（用例结果 /
评测结果 / 对照）、runner 与 adapter、policy（对照方向与容差的确定性判定）、`artifact_digest.py`
（**仍在**——它是通用摘要工具）、`isolation.py check-diff`（**仍在**——候选 diff 禁区检查）、
`examples/evaluation-results` 样例。恢复时落点由 Supervisor 显式指派并声明契约，并重新评估
是否仍需 `measurement: none` 口径。

## §4 产品链结论（2026-10-30 并入，原 docs/product/）

2026-10-30 关闭「产品线完善」批：产品链结论并入本节，`docs/product/` 与批次目录删除；原文可从
git 历史 `40147df:docs/product/` 取回。自此产品链状态只有本节、`CHANGELOG.md` 与该日 episode 三处
同源记录，不再存在「method-spec 生效 / acceptance-matrix 部分 / pending-test 已验证」的状态三说。

- **产品定位**：宿主原生多角色协作方法插件，不是运行时、Flow 画布或组织图；方法写一次，
  循环交给宿主。分发形态为 ZCode / Claude Code / Codex 插件，`marketplace.json` 的 `source`
  指向 `packaging/runtime` 生成树。
- **角色与默认路径**：10 个角色是按需取用的能力清单，默认路径短；角色分离 ≠ 环境隔离。
  Supervisor 是主会话，不是独立进程。
- **文档链**：proposal → spec → design → plan；spec 反审 proposal、design 冻结前独立评审、
  plan 引用冻结后的 design。
- **关键决策**：只做方法不做运行时；宿主插件载体；受治理的人工闭环；保护门单点声明；
  schema + 编译门；Markdown 融合计划；失败语义成文；瘦快照分发；manifest/CHANGELOG 是版本单点；
  评测仪器 2026-10-12 整线裁撤，方法级改动 `measurement: none`；文档链吸收（D12）与门禁（D13）；
  边界如实声明（D14）。
- **评审门处置**：需求评审 REV-2026-10-19-003 `approved`（F1–F12 全关闭）；技术方案评审
  `reviews/review-2026-09-19-001.md` 经独立委派 L2 `approved`（2026-10-29，Design 冻结）。
- **计划处置**：PLAN-PRODUCT 8 ☑ / 6 本期不做；PLAN-LOOP 5 ☑ / 5 本期不做；T02 与 LOOP T09
  的对象已随评测装置/改进环裁撤注销，PRODUCT T09 的 Intake FTS5 再犯类检索已落。

---

## 对外口径（版本号以 manifest 为准）

已具备受治理的方法演进流程与数据契约（十条主工作流、<!-- count:agents -->10<!-- /count --> 角色能力库、14 条硬边界、独立评审门、
确定性检查门与记录契约）。业务任务度量切片已裁撤，改进三件套与逐版本发布记录同批退役；
改进环本身于 2026-10-29 整体裁撤，方法改动走批次流程，方法级改动一律 `measurement: none`
口径，不表述为已验证的自动学习系统。评测装置已整线裁撤（设计知识与恢复清单见 §3）；
持久反馈检索与自动发布控制面未实现。
