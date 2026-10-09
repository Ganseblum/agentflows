# 设计文档事实核对（spec fact-check）设计

> 状态：讨论稿，未实施。起草于 2026-09-14。
>
> 关联：[AGENTS.md](../AGENTS.md)、[agent-roles.md](agent-roles.md)、
> [skills/agentflow/SKILL.md](../skills/agentflow/SKILL.md)、
> [references/contracts.md](../skills/agentflow/references/contracts.md)、
> [plan.schema.json](../schemas/plan.schema.json)、[protected-paths.txt](../protected-paths.txt)

## 1. 背景与问题

外部观察到一个有效但当前 Agentflow 没有显式承载的流程：

- 输入：BE/FE design、proposal、spec、plan、接口文档、README；
- 动作：到 `be/<repo>`、`fe/<repo>` 核对方案依赖的代码事实（成对键、状态、消息 DTO、
  异常边界）；
- 输出：逻辑/异常边界缺口，按优先级排序的发现报告。

现状问题：

1. 缺少显式的"文档断言 vs 代码事实"核对步骤与输出契约。现有 planning 流程
   （[SKILL.md](../skills/agentflow/SKILL.md) 计划段）从专家结论直接进 plan-architect，
   没有"断言核验"这一环。
2. findings 没有 artifact 归宿：原记录树当时只有 `bugs/` 与 `plans/` 两个子树
   （原说明已冻结，见 [_archive/records-2026-10/readmes/records-README.md](../_archive/records-2026-10/readmes/records-README.md)）。
3. reviewer 被借来审文档是错配：它的契约是**实现之后**的独立判定
   （[reviewer.md](../agents/reviewer.md):3），输出 `approved / changes_requested /
   blocked` 决策而非发现清单（:27），且它不能运行命令，只能指定命令由 Supervisor 执行
   （:14-18）。docs 虽在其只读范围内（:12），但它没有跨仓代码事实核对的职责。
4. FE/BE 工程师具备域知识，但现有角色契约偏实现（frontend-engineer.md:20、
   backend-engineer.md:20），没有可直接复用的只读调查 brief 模板。

## 2. 现状映射

| 需求环节 | 现有承载 | 依据 | 缺口 |
| --- | --- | --- | --- |
| 核对本仓代码事实 | frontend / backend-engineer（只读 brief 可约束） | contracts.md:34；frontend-engineer.md:20；backend-engineer.md:20 | 无 findings 输出格式 |
| 跨仓接口矛盾裁决 | technical-director | roles.md:25-27 | 无 |
| 汇总成计划 | plan-architect | plan-architect.md:21-27；plan.schema.json | 计划此前没有核验步骤的输入约定 |
| 独立审查 | reviewer | reviewer.md:3、:22 | 只审实现，不审提案/文档事实 |
| 证据输出契约 | Worker result / Review result | contracts.md:38-66 | 无 findings 专用形态（可按 verdict 归类） |
| 任务文本不可信规则 | Supervisor 步骤 4 | SKILL.md:44；contracts.md:36 | 规则已有，缺"核对产物"的格式约定 |

## 3. 方案 A：写成工作流步骤（推荐先行，不加角色）

理由：角色是能力边界不是流水线（roles.md:3），"无活不设岗"（contracts.md:19）；
FE/BE 的域能力已覆盖事实核对，缺的是步骤、brief 模板与输出契约。改动不触碰 protected
路径，落地成本最小。

### 3.1 步骤定义（拟插入 SKILL.md 计划段）

> 当计划/设计来自外部文档（proposal、spec、接口文档、README、上下游 design），在
> plan-architect 动手前先做一轮**设计事实核对**：Supervisor 为每个被文档引用的仓库各发
> 一个只读 brief（contracts.md 调查模式），要求逐条核对文档断言与真实代码，证据精确到
> `path:line`；接口矛盾交 technical-director 裁决；核对结论按严重度排序汇总，verified 项
> 进入计划的 `input_evidence`，contradicted/unverifiable 项进入 `unresolved_decisions`
> 或转为工作包。核对未完成不外发计划。

### 3.2 findings 输出契约（拟加入 contracts.md）

```yaml
findings:
  - finding_id: stable slug
    claim: 文档断言（带出处，如 proposal §3.2 / 接口文档 v2）
    verdict: verified | contradicted | unverifiable
    evidence: path:line 或原始命令输出；contradicted/unverifiable 必填理由
    boundary: logic | error | data_compat | permission | state
    severity: blocker | major | minor
    suggestion: 最小修复或需澄清的问题（可选）
```

排序：severity 降序；同 severity 按 boundary 聚类。先把该结构作为 Worker result 同级的
`findings` 字段/响应对象约定，仍不新增 schema；待真实核对样本稳定后，再决定是否将其固化
为受校验的契约。

### 3.3 与计划字段的映射

| findings 结论 | plan.schema.json 字段 | 约束 |
| --- | --- | --- |
| verified 断言 | `input_evidence`（evidence_id/source_ref） | 必须有来源引用 |
| 接口相关结论 | `interfaces`（error_behavior、compatibility、verification_ref） | 矛盾必须在批准前裁决 |
| unverifiable | `assumptions` + `unresolved_decisions` | `approved` 计划要求 `unresolved_decisions` 为空（schema:240-252） |

### 3.4 角色用法与边界

- BE/FE：只读调查 brief，范围写死仓库与目录；不写文件、不接实现任务。
- technical-director：只处理跨层接口/架构矛盾，不负责核对清单。
- reviewer：仅在需要独立判定时使用（例如 findings 会直接影响验收）。它指定的检查命令由
  Supervisor 执行并回传原始输出（reviewer.md:14-18）。
- plan-architect：只消费 already-verified 的结论，不承担核对。
- 已知限制：路径边界仍是提示词 + Supervisor diff 兜底（C7、agent-roles.md:123），brief
  必须显式声明仓库与范围；多仓场景沿用宿主现有工作区权限，不新开权限。

### 3.5 改动面、验证与风险

- 改动文件：`skills/agentflow/SKILL.md`、`skills/agentflow/references/contracts.md`，
  可选 `references/roles.md`；均不在 protected-paths.txt。
- 验证：`python3 tools/lab/validate.py all`；重装插件后 `python3 tools/lab/validate.py
  installed`（角色/技能从安装快照加载，Z5；技能描述前 250 字符有效，Z3）。
- 风险：本机网关模型标签不可信（C6），findings 结论以代码证据为准而非模型自述；
  brief 委派不扩权（contracts.md:12）。

## 4. 方案 B：新增只读角色（条件触发，备选）

### 4.1 触发条件（必须有证据，来自 improve 环）

- 文档事实核对成为高频独立任务，且 FE/BE 工程师被反复占用；
- reviewer 文档评审反复失败且归因为 `role_prompt` / `workflow_policy`；
- findings 报告本身成为交付物（需要独立于实现与计划的 artifact）。

### 4.2 角色草案

```yaml
---
name: spec-auditor
description: Verifies external design and interface documents against actual repository code facts, returning prioritized, evidence-linked findings without changing code.
model: inherit
maxTurns: 20
tools: Read, Glob, Grep
disallowedTools: Bash, Write, Edit
---
```

- 产物所有权：全部只读；只返回 findings，不做 decision，不修代码/文档。
- 职责边界：与 reviewer 的分工是"核事实 vs 判实现"；与 technical-director 的分工是
  "发现矛盾 vs 裁决矛盾"。
- 输出：3.2 的 findings 契约 + 未决问题列表。

### 4.3 artifact 决策点（未定）

- 选项 1：不新增记录类型，findings 作为 brief 结果进入 plan 的 `input_evidence`。
- 选项 2：新增 findings 记录类（落点未定）+ schema，供跨任务回溯。新增 schema 不在 protected
  列表内，但属于新的契约面，需要人工评审；并与记录树说明同步。
- 倾向：先选项 1，等出现"同一文档被多次核对""findings 需要跨会话引用"的真实需求再升级。

### 4.4 落地与治理

- 按 [skills/improve](../skills/improve/SKILL.md) 治理环：feedback-analyst →
  candidate-engineer（新角色文件与注册改动不在 protected 内）→ evaluator（baseline 与
  candidate 同宿主、同模型、同用例，evidence-and-release.md）→ release-governor。
- 注册清单：SKILL.md 宿主绑定、references/roles.md、docs/agent-roles.md、README 角色
  列表、CHANGELOG、至少一条公开评测用例（evals/ 为 protected，改动需人工审查）。
- 门控提醒：evaluator / release-governor 角色文件与评测套件在 protected-paths.txt 内，
  候选不得编辑；本机真实模型 dogfood 尚未完成（host-platform-facts.md C5/C6），先跑
  确定性校验与 policy 引擎，再谈真实模型对照。

## 5. 对比与建议

| 维度 | 方案 A：工作流步骤 | 方案 B：新角色 |
| --- | --- | --- |
| 改动面 | 2-3 个 Skill 文件 | 新 agent + 多处注册 + 评测用例 |
| 受 protected 约束 | 否 | 部分相邻（evals、治理角色） |
| 独立性 | 依赖 Supervisor 编排 | 角色级独立 |
| 输出 | findings 进计划证据 | 独立 findings 契约 |
| 适用 | 当前缺口：无步骤、无格式 | 高频、移交、跨会话回溯 |

建议：先落方案 A 并用 2-3 个真实任务观察；出现 4.1 的信号再启动方案 B。

## 6. 未决问题（待人工确认）

1. findings 是否要持久化为仓库 artifact？复用 plan `input_evidence` 还是新开
   findings 记录类？
2. reviewer 是否仍允许用于纯文档独立门，还是文档类审查一律走新流程？
3. 新角色命名：`spec-auditor` / `doc-auditor` / `design-fact-auditor`？
4. 多仓库场景中 brief 的仓库边界是否需要宿主级路径权限（当前仅有提示词约束，C7）？
5. 方案 A 的步骤放在 Skill 正文还是另开 reference，避免触发描述超过 250 字符预算（Z3）？

## 7. 验证清单

- [ ] `python3 tools/lab/validate.py all`
- [ ] 重装插件后 `python3 tools/lab/validate.py installed`
- [ ] 若采纳方案 A：准备一条"文档断言与代码矛盾"的公开评测用例（evals/ 需人工审查）
- [ ] 若采纳方案 B：先冻结 baseline 与归因证据，再进 improve 环

## 8. 现状设计评估：问题、自闭环与角色自动流转（讨论记录）

结论：**能升级，但"自动"只能到 Human-gated 闭环 + 规则驱动的角色流转；完全自闭环和
子代理互相唤起，当前宿主与治理规则都不支持，也不应做。** 以下问题约束本设计的落地方式。

### 8.1 现存问题（按严重度）

- **编排单点**：Supervisor 就是主会话，没有持久状态；长任务依赖会话历史，跨进程恢复、
  租约、重试全部空缺，Execution Coordinator 仅为预留（agent-roles.md:106-107、
  SKILL.md:34-35）。
- **流转结构性受限**：worker 默认禁止再委派（contracts.md:12）；在当前角色白名单配置下，
  每一跳由主循环驱动。宿主可以提供 agent→agent 通道，但若未来显式授予该工具，必须重新
  审查流转约束，不能假设为默认能力。
- **强制力不足**：`maxTurns` 未验证（Z6）、路径级权限不存在（C7）；工具级白名单由宿主
  强制时可以形成硬边界，预算纪律与路径范围仍需 Supervisor diff 和人工门兜底。
- **评测可信度**：adapter 指标为模型自报，缺独立判定器（`_archive/handoff-2026-10/next-session-handoff.md:227`）；
  本机模型标签不可信（C6）；真实模型 dogfood 未完成（self-improvement-design.md:3、:92）。
- **文档漂移**：角色在 agents/*.md、references/roles.md、docs/agent-roles.md 三处重复，
  无跨文件一致性校验。
- **本设计自身的局限**：方案 A 的 findings 契约与"核对未完成不外发计划"只是约定，无
  确定性检查；多仓 brief 的仓库边界无法强制。

### 8.2 自闭环升级路径与天花板

- 现状是 Human-gated（自动生成与评测候选、人工批准发布，self-improvement-design.md:66），
  路线已定义：遥测/反馈池 → 持久检索 → 私有 holdout → Canary（:99-108）。
- 两条天花板是设计内的：发布门、权限、工具、Hook、MCP、评测规则、自动阈值永远人工
  （evidence-and-release.md:109、self-improvement-design.md:70）；改门必须人工审查
  （AGENTS.md）。终态是"自动到候选和评测、人工把门"，不是全自动自修改。

### 8.3 角色自动流转的可行形态

- 近期：把序列规则写成技能内的状态机（bug 链、planning 链已有雏形，SKILL.md:21-37），
  补逐跳进入/退出条件与评测用例，让 Supervisor"按规则自动跑"而非自由发挥。
- 中期：只有出现跨进程/队列刚需才上 Execution Coordinator（管运行状态，不替代决策）。
- 长期：宿主 Hook/MCP 只承载状态、证据、审批，不跑第二套 Agent 循环
  （host-native-plugin-design.md:89）。
- 红线：变更作者不能批准自己的变更，独立门不可豁免（contracts.md:11）。

### 8.4 对本设计的含义

先补"独立判定器 + 可信任模型端点"两个闭环前提，再谈流转自动化；否则自动化只会放大
不可信证据。方案 A 可先行，但应把 findings 的确定性校验（至少 schema/格式）列为升级项，
避免重演"约定无强制"的问题。

### 8.5 复核更正与补充（2026-09-14，修正追加不改写上文）

**更正 8.1 的两处表述：**

1. "宿主没有 agent→agent 通道"不准确。ZCode 上**没有** `tools` 白名单的角色会继承委派
   （Agent）、网络与 MCP 工具（Z4）。当前 12 角色边界成立是因为全部声明了白名单并被宿主
   强制——是"白名单挡住"，不是"宿主无通道"。推论：任何新增角色漏写 `tools:` 即破界，
   方案 B 的角色文件必须把工具白名单列为硬性要求，并在注册清单中加"frontmatter 审查"项。
2. "写权限靠提示词"不准确。工具级白名单是宿主强制的（Z4 实测）；不可强制的只是路径级
   边界（C7，记录根等路径约束靠角色文本 + Supervisor diff，self-improvement-design.md:91）。
   纯提示词的只有预算纪律（Z6 `maxTurns` 未验证）。

**补充遗漏的问题：**

- **评测执行不可行（当前最高优先）**：C2 使 plan-architect 在 `--print` 下写 `plans/` 被拒，
  该类用例结果无意义（issues/ISS-2026-003-print-mode-plan-write-blocked.md）；C5 使单用例
  最长 ~24 分钟、~$4，默认 900 秒超时不足，且 adapter 修复后仍丢弃内存中已完成结果、断点
  续跑未实现（issues/ISS-2026-002-eval-run-all-or-nothing.md）——完整 baseline 目前
  跑不完也跑不起。
- **可复现性污染**：C3，print 模式继承用户 MCP 与全局 slash commands，隔离 flag 未验证。
- **评测覆盖单宿主**：X2，Codex 对 candidate 源 fail-closed，候选对照目前只能 Claude。
- **dogfood 环境受限**：Z2，本仓库 workspace skills 遮蔽插件 skills 副本，插件侧行为验证
  必须换工作区。
- **manifest 同步无源内校验**：5 份 manifest（根、marketplace、.zcode/.claude/.codex-plugin）
  版本号手工同步；`validate.py` 的 `INSTALLED_FILES` 只做 source-vs-snapshot 文件 diff
  （tools/lab/validate.py:57-65），不检查源内跨 manifest 版本一致——漏 bump 只会在重装后
  以宿主看到旧版本的形式暴露。
- **无 CI/hook 强制**：全部确定性校验依赖人工运行纪律，无 pre-commit/CI 门。
- **样本与阈值**：公开 suite 仅 14 例，阈值未冻结，Canary 缺统计基础。
- **证据单机性**：所有宿主事实来自一台机器 + 自定义网关（host-platform-facts.md 头部声明），
  外推到其他环境属未验证。

**修正后的优先级**：先解 C2/C5（权限 profile + 断点续跑/部分结果落盘），让完整 baseline
可运行；再补独立判定器与可信端点；manifest 版本一致性校验可作为 `validate.py` 的低成本
增强，但它会修改 protected 的 gate 文件，必须走人工审查后再落地，不能当作候选的普通只读改动。

## 9. 角色的专业性与准确性：领域检查单分层（讨论稿，待确认后再改）

问题：怎么保证 agent 的专业性——前端能否判断何时封装组件、hooks 设计、API 封装层；
服务端是否考虑幂等性、接口扩展性？当前有无对应描述？

### 9.1 现状：逐项对照（2026-09-14 核查）

| 专业维度 | 当前角色契约覆盖 |
| --- | --- |
| 前端组件封装判断（何时抽组件） | 无；仅 "follow its local instructions and existing UI patterns"（frontend-engineer.md:20） |
| React hooks 设计规范 | 无；仓库内所有 "hooks" 均指宿主权限 Hook |
| API 封装层设计 | 无；仅 description 的 "typed API integration"（:3） |
| 服务端幂等性 | 无；backend-engineer 只要求声明 request/response/error/authorization/compatibility（backend-engineer.md:20） |
| 接口扩展性（演进/版本化/additive） | 部分；"compatibility" 有，扩展路径无 |
| 迁移与外部契约谨慎 | 有（"deliberate decisions"，:20） |

### 9.2 这是定位使然，不是遗漏

Agentflow 是跨项目方法论插件（host-native-plugin-design.md:11），两个 engineer 角色显式把
领域规范外包给目标仓库的本地指令（"follow its local instructions"）。设计假设：项目级
规范住在目标仓库（AGENTS.md/docs），角色负责强制读取。把"何时封装组件"写死进插件会把
跨项目方法论变成某个团队的规范库。

### 9.3 分层：项目特定项 vs 跨项目通用项

- **项目特定项**（组件粒度、hooks 约定、API 层封装模式）→ 补目标仓库的
  AGENTS.md/审查清单，不动 Agentflow。
- **跨项目通用项**（幂等性、接口演进/扩展性、并发语义、事务边界）→ 进角色契约。
  先例：error contract 漏检被写死进 reviewer 契约 + AF-007 用例
  （examples/issues/ISS-2026-906-reviewer-missed-error-contract.md:41-47）。

### 9.4 拟议条款草稿（未写入角色文件）

- backend-engineer 增："State idempotency and retry semantics for every mutating
  endpoint; declare the extension path (versioning, additive fields) for externally
  visible contracts."
- reviewer 增："Check mutating endpoints declare idempotency/retry behavior; check
  contracts state an extension path."
- 对应新增一条公开评测用例（AF-007 模式：backend 变更未声明幂等性/扩展路径，断言
  reviewer/worker 必须指出），把检查项变成可回归断言。

### 9.5 上限与闭环机制

条款只强制注意力到位（"必须回答幂等性"），判断对错仍取决于模型 + 仓库证据；角色名
不是资历。可靠性来自三件套：检查单条款 × 证据强制（path:line / raw output，
contracts.md:63）× 回归用例。漏检一次按 improve 环沉淀一次；同类候选两轮无效即止损，
归因到模型或上下文（skills/improve/SKILL.md:58）。此前结论仍然成立：角色分工未经验证
（self-improvement-design.md:92），"保证"目前只是机制设计，不是实测事实。

### 9.6 待确认事项

1. 9.4 两条草稿是否采纳（改 backend-engineer.md / reviewer.md，走 improve 环）？
2. 项目特定项先在哪个目标仓库落 AGENTS.md 检查单（paipai-new-fe / safe-agent-nexus）？
3. 是否同步新增幂等性/扩展性评测用例（evals/ 为 protected，需人工审查）？
