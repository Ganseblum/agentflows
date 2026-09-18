# Agentflow 迭代记录

> 作用：按版本回答三个问题——**为什么迭代**（触发/证据）、**改了什么**、**解决了什么问题**，
> 并注明未决与未验证项。
> 发布级差异见 [CHANGELOG](../CHANGELOG.md)，会话级细节见
> [next-session-handoff.md](next-session-handoff.md)。
>
> 记录规则：只写有留档支撑的内容——提交、CHANGELOG、bug 记录、复盘文档；无法核实的标注
> 「未验证」。更早的插件版本（记录中可见 `0.2.0` 引用，见
> [`examples/bug-records/`](../examples/bug-records/)）早于本仓库的留档历史，不在此追溯。

## 总览

| 版本 | 日期 | 触发（为什么） | 解决了什么 | 证据入口 |
| --- | --- | --- | --- | --- |
| 0.3.1 | 2026-09-14 | 首轮角色评审后建立 Git 基线 | 独立 Plugin 仓库化，角色/契约/评测骨架可追溯 | commit `f11c3b6`；交接文档「已完成」 |
| 0.3.2 | 2026-09-14 | 真实模型 dogfood 暴露的宿主问题 + 吸收外部已验证机制 | 接受前编译、任务文本按数据、记录格式重构、宿主事实留档 | CHANGELOG 0.3.2；交接文档「第二批/第三批」 |
| 0.3.3 | 2026-09-14 | 复核 12 个角色在宿主上的实际强制力 | 工具白名单、候选禁区单点声明、预算纪律、Reviewer 检查协议 | CHANGELOG 0.3.3；commit `77e1577` |
| 0.3.4 | 2026-09-15 | 会话内三类事故 + 全项目门复核 | 硬边界 12、实验/恢复纪律、门缺口加固、横切机制纪律 | CHANGELOG 0.3.4；`records/bugs/2026-09-15/` |
| 0.3.5 | 2026-09-15 | 对话分享落地页复盘的 9 条补丁 | 运行时接线验收、参照物先行、替身面盘点、缺席断言纪律 | CHANGELOG 0.3.5；本文件 §0.3.5 |
| 0.3.6 | 2026-09-16 | 能力盘点发现「声明了但没有执法/度量」的四类缺口 | write_scope 执行层对照、断点恢复协议、episode 捕获纪律、方法级改动诚实标注 | CHANGELOG 0.3.6；本文件 §0.3.6 |
| 0.3.7 | 2026-09-16 | 记录语言混用（英文 title + 中文正文 + 英文章标题，跨机器又见中文 title） | 单语约定 + 章节标题固定中文字面量（门变更）+ 存量 6 条与示例统一 | CHANGELOG 0.3.7；本文件 §0.3.7 |
| 0.3.8 | 2026-09-16 | 再犯类无机器可查的落点；severity 档位不够直观 | P0–P3 优先级 + 类台账（未归纳/已归纳 + 归纳版本）+ 推导档位单次/再犯/归纳后再犯 | CHANGELOG 0.3.8；本文件 §0.3.8 |
| 0.3.9 | 2026-09-16 | 分不清问题是不是 Agentflow 产生的（自己写的计划/分析 vs 方法条款） | 必填 `provenance` + 归因铁律（schema 强制）+ 改进环过滤规则 | CHANGELOG 0.3.9；本文件 §0.3.9 |
| 0.4.0 | 2026-09-16 | 系统复盘 `aiwork-workflow-ai`：设计模板的工程血肉、issue 记录优点、双仓评审桥 | 设计完备性三纪律 + closure_criteria/fix_revision/变更记录 + `records/reviews/` 二次评审桥 | CHANGELOG 0.4.0；本文件 §0.4.0 |
| 0.4.1 | 2026-09-17 | 文档手工同步面漂移无机器检查（P1）；improve 环没有任务级燃料（P1） | `validate.py docs` 一致性门（首跑即抓到真实漂移）+ episode 最小落盘（复用既有契约）+ report 过滤参数 | CHANGELOG 0.4.1；本文件 §0.4.1 |
| 0.4.2 | 2026-09-17 | 兄弟会话在 infinite-canvas 立案的三条 workflow_policy 缺口（集成授权/git 层隔离/状态结论证据） | 硬边界 3 扩写 + SKILL 三处补丁（Intake/Delegate/Control）——首批由**外部会话记录驱动**的条款修复 | CHANGELOG 0.4.2；本文件 §0.4.2 |
| 0.5.0 | 2026-09-17 | 用户对比 aiwork Markdown 计划与 JSON 契约后选方案 A：人读性 + 机器校验融合 | plan 契约重设计为 Markdown 融合形态（看板式任务表 + 机器断言保留并扩展） | CHANGELOG 0.5.0；本文件 §0.5.0 |
| 0.5.1 | 2026-09-17 | 用户问 spec/design/proposal 是否吸取、如何方便后续使用 | 文档评审模式（按文档类型分档清单）进 reviewer；不重建模板体系 | CHANGELOG 0.5.1；本文件 §0.5.1 |
| 0.5.2 | 2026-09-17 | 用户要求自审 0.5.x 有无遗漏 | 一处静默门缺口（反例从未被拾取）+ 死代码 + 五处旧措辞 + 两处失效文档面 | CHANGELOG 0.5.2；本文件 §0.5.2 |
| 0.6.0 | 2026-09-17 | 用户要求消灭方法级改动的 `measurement: none`（做业务任务度量切片）；批内独立评审抓出四个运行时缺陷 | 业务评测仪器（种子缺陷确定性评分 + 业务面 runner/adapter + 门登记）、判断词可判定定义、CI、两处诊断/读取缺陷修复 | CHANGELOG 0.6.0；本文件 §0.6.0；`records/plans/PLAN-BUSINESS-EVAL-001.md` |
| 0.7.2–0.7.4 | 2026-09-18 | 审计整改阶段四、五：episode 可验证字段、发布 measurement 链、记录显式检索、版本与 demo 口径漂移 | revision/run/claims/evidence 对齐；measurement none/complete 语义；SQLite FTS5 读侧；0.7.x 迭代留档与 next-session 机器信息修正 | 本批文件、`records/episodes/2026-09-18/`、`tools/lab/record_store.py` |

---

## 0.3.1 — 首个受审基线（2026-09-14）

- **触发**：新插件仓库完成首轮角色评审后初始化本地 Git baseline；此前版本散落在旧
  Agentflow CLI 仓库与演练目录里，角色约定与记录格式不可追溯。
- **改了什么**：独立 Plugin 根目录、Codex/Claude manifest、两个 Skill、12 个角色文件；
  Bug/Plan/Episode 契约与正反例；10 个公开评测用例；确定性校验器、隔离检查、Policy Engine
  与显式宿主 Adapter 的 P0 切片。
- **解决了什么**：插件从「CLI 附属品」变为可独立安装、可对照评测的产品面；此后每一次
  迭代都有 git 基线可对照。
- **未决**：真实模型 dogfood 与完整 baseline 未做（延续到 0.3.2）。

## 0.3.2 — 宿主适配与记录重构（2026-09-14）

- **触发**：真实模型 dogfood 起步（AF-001 smoke、AF-002 诊断）暴露 `--json-schema`
  拒绝 Draft 2020-12 元声明、print 模式权限拦截、网关模型标签不一致等问题；同时从外部
  项目 `aiwork-workflow-ai` 吸收了「接受前编译」「任务文本按数据」两个已验证机制。
- **改了什么**：Adapter 剥离 `$schema`/`$id` 并加进度诊断；Supervisor「接受前编译」步骤；
  improve 步骤 9 schema 前置校验；10 条硬边界单点化；基线对照分诊；Bug 记录改为
  Markdown + frontmatter 并统一到 `records/`；`validate.py artifacts`；`host-platform-facts.md`；
  ZCode 本地目录安装；两个 Skill 的触发描述前置化。
- **解决了什么**：把 dogfood 的宿主噪声变成可复验的实测事实；记录从「机器格式」变成
  人可读、机可校验；「摘要不是验证」从口号变成确定性检查。
- **未决**：完整 baseline 受宿主网关/权限/超时阻塞（见交接文档「当前风险」）。

## 0.3.3 — 边界加固（2026-09-14）

- **触发**：复核 12 个角色设置是否合理——实测发现实现型角色继承全量工具（含委派、网络、
  MCP），与「委派不扩大权限」矛盾；且角色从安装快照加载，源改动会静默漂移。
- **改了什么**：实现型角色声明 `tools` 白名单；`protected-paths.txt` 单点声明候选禁区；
  `validate.py installed` 暴露快照漂移；硬边界 #1/#2/#6/#11 增补；Reviewer 检查协议
  （命令与预期由 Reviewer 给、只接受原始输出）；预算纪律与 `partial` 语义；
  AF-011 至 AF-014 四个评测用例；`AGENTS.md` 建立。
- **解决了什么**：把「纪律」尽可能升级为「宿主强制」或「确定性检查」；角色越权面收窄，
  候选改门的路径显式化。
- **未决**：`maxTurns` 仍未验证；路径级写入边界仍靠矩阵 + Supervisor diff 检查。

## 0.3.4 — 行为断言与门加固（2026-09-15）

- **触发**：同一会话内三类事故，均有 bug 记录：
  - `BUG-20260915-001`：axios 401 拦截器与「未登录是合法状态」页面冲突——暴露读取范围
    与横切机制纪律缺失；
  - `BUG-20260915-002`：故障注入在真实仓库执行，`git checkout`「恢复」冲掉未提交编辑；
  - `BUG-20260915-003`：连续三轮以推演代替实验的行为断言，第三轮掩盖了测试门的完整绕过。
  另经全项目复核发现四处门缺口（schema、测试目录、manifest、测试未接入 `all`）。
- **改了什么**：硬边界 12（工具行为断言 = 假设，须最小实验）；`AGENTS.md`「Experiments and
  recovery」；隐式行为纪律（`write_scope`/`read_scope` 分离、横切机制注册点搜索、表面 ×
  合法状态矩阵、`shared_mechanisms[]` 必填）；测试子目录绕过修复；`schemas/` 与钉住测试
  进禁区；`validate.py manifests` / `tests` 并入 `all`；AF-015。
- **解决了什么**：三类事故各有条款 + 检测兜底：行为断言有实验要求（含 supervisor 自己）、
  实验有安全规程、门缺口有回归断言。测试门绕过被实证修复并复验。
- **未决**：条款是否在真实运行中生效无对照评测（0.3.4 是开发版本发布）；同类断言再犯时
  按 improve 环升级为评测用例（记录 -003 Notes 已写触发条件）。

## 0.3.5 — 运行时验收与参照物纪律（2026-09-15，当前源码，宿主快照待重装）

- **触发**：外部项目「对话分享」落地页（一个跨层镜像页）的完整复盘，见
  `/Users/lihanghang1/Desktop/WorkProject/aiwork/aiwork-workflow-ai/docs/features/feature-2026-09-04-对话分享/复盘-agentflow优化建议.md`。
  两个门禁（编译接受、独立 review）整体正收益——两轮 review 抓到 11 个真实缺陷；但所有
  漏网集中在同一类：**运行时接线 / 布局 / 顺序**，静态阅读永远证明不了；同时最大的时间
  成本来自「对齐既有实现」没有以参照物为规格（同一页面来回补了 8 轮）。
- **改了什么**（9 条补丁，落点均经该复盘文档核对、逐字锚点验证后应用）：
  - 硬边界 13：缺席断言必须直接读权威落点（目录清单、接收表、队列、传输日志）；
    搜索引擎/缓存/采样面板查不到不算证据；
  - Final decision record 增加 `claims` 台账：每条用户可见断言 → 会失败的检查；
    只凭代码阅读记为 `unverified`，未验证的用户可见断言使结论降为 `partial`；
  - 简报三纪律：Replication briefs（参照实现即规格 + `path:line` 盘点 + 实测验收）、
    Mirror briefs（分支表先行）、Extension inventory（扩展契约前 grep 已有载体，重复即停）；
  - 新小节 `Verification stand-ins`：替身是验证装置，先盘点消费面，缺口记 verification gap
    并重跑，不得按替身能力裁剪检查范围；
  - SKILL.md step 8：e2e 先于 review 关门；后置用户可见改动重开门（可只审 delta）；
  - Reviewer 检查协议与 frontend-engineer：接线/布局/顺序断言不接受仅单测或仅阅读；
  - plan-architect：镜像面的 parity 清单任务、替身面清单、e2e 排在 review 门之前。
- **解决了什么**：把复盘归因的两类根因——「未验证与通过不可区分」「对齐任务没有参照物
  规格」——变成可执行的条款与验收格式；缺席断言与正向断言（边界 12）补成一对。
- **效果状态**：未验证。这些是提示词/契约约束，不是宿主强制，也没有 baseline/candidate
  对照证据；按 0.3.4 的先例，同类漏检再犯时升级为 AF-* 评测用例。
- **未决**：
  - 本机 ZCode 快照仍为 0.3.4；需刷新 marketplace 并重装后 `validate.py installed` 转绿，
    角色文件改动才实际生效；
  - 复盘文档中的 E4/E7（实现后才报出的镜像差异、supervisor 后期改动未重走 review）无
    留档过程记录，属会话内事件——条款按其自述应用，未独立复核。

## 0.3.6 — 执行层牙齿与诚实标注（2026-09-16，当前源码，宿主快照待重装）

- **触发**：用户发起的能力盘点发现四类「契约声明了、执行层没有对应物」的缺口：业务
  仓库里的 write_scope 只是约定（`isolation.py check-diff` 只管改进环候选树）；长编排
  无断点恢复；反馈闭环靠人记得触发（episode 不会自动收集）；方法级改动拿不出
  better/neutral/worse 度量（`evals/` 只测 Agentflow 自身）。另有两处小项：maxTurns 在
  ZCode 声明未验证（事实 Z6）、worker result 无 cost/duration 字段。
- **改了什么**：
  - 硬边界 14 + `skills/agentflow/scripts/check-write-scope.sh`（实测三种用例：界内 OK、
    越界逐路径点名、坏 revision 报错）：主管委派时记基线 revision，接受前对照实际
    改动面（tracked + untracked），越界路径一律退回；SKILL.md 步骤 7 与中文镜像同步；
  - Worker result 可选 `cost`/`duration`（实测或 `not reported`，禁止估算）；
  - Reviewer test-depth 的 revert 实验显式化：reviewer 无 Bash，由它指定还原命令与预期
    失败输出、Supervisor 执行回传原始输出；fixer 写的回归检查是下限不是独立验证；
  - SKILL.md 步骤 10：结果可能喂改进环时，会话结束前把决策记录落成持久形式；
  - SKILL.md 恢复节：会话中断从 `records/plans/` 版本化计划恢复，包状态从工作区重新
    推导，无证据视为未开始；
  - `references/roles.md` 补全 12 角色画像 + 任务形态路由表；
  - 四个角色 description 去掉 "for Agentflow" 限定，宿主在业务仓库里可正确路由；
  - improve SKILL 两条能力边界：方法级候选按 `measurement: none` 发布、不得称已验证；
    maxTurns 按意图元数据对待，预算纪律以提示词为准；
  - 交接文档待办重整为 P0/P1/P2 分级清单。
- **解决了什么**：四类缺口各有最小执行对应物——write_scope 有一条命令的执法、断点有
  恢复协议、episode 有捕获纪律、方法级改动有不可冒充的标注；「声明即约束」和「实际
  强制」之间的静默差距被显式化。
- **效果状态**：未验证（与 0.3.4/0.3.5 同一定位：开发版本发布，无对照评测）。脚本
  行为已实测；条款对真实运行的影响无度量。这本身就是本批声明的盲区之一——业务任务
  度量切片是 P1。
- **未决**：分级待办的完整清单见 `docs/next-session-handoff.md`「待办（分级）」。

## 0.3.7 — 记录语言统一（2026-09-16，当前源码，宿主快照待重装）

- **触发**：用户指出已有记录语言混用——同一文件内英文 `title` + 中文正文 + 英文章节
  标题（`## Symptom` 等）；另一台机器产出的记录用中文 title，语料层面三种做法并存。
  根因是没有写下来的记录语言约定。
- **改了什么**：
  - 约定写入 `records/README.md`：机器层英文 ASCII（frontmatter 键/枚举、slug/ID/路径、
    `project`）；章节标题为**固定中文字面量**（`## 现象`/`## 根因`/`## 修复`/`## 问题代码`/
    `## 审查`）；人读层一条记录单语、title 与正文同语言、默认中文；
  - **门变更（用户明确指示下由人工实施）**：`tools/lab/validate.py` 的
    `BUG_REQUIRED_HEADINGS` 与 Fix/Review 检查改为中文字面量，错误消息同步；负向实验
    验证：英文标题 → `body section '## 现象' is required`，中文标题 → 通过；
  - 存量 6 条记录 title + 章节标题中文化，各自刷新 `updated_at=2026-09-16T11:48:32Z`；
    examples 正反例全文翻译到同一形式（反例保持仅因 verified-缺审查而非法）；
  - `agents/bug-recorder.md`、`records/bugs/README.md`、中文镜像 `docs/agent-roles.md` 同步。
- **解决了什么**：记录内部不再混语；`validate.py report` 表格与正文同语言；新记录有
  校验器强制的写法（标题字面量）；跨机器/跨项目的记录有同一份约定可依。
- **未决**：宿主快照仍为 0.3.4，需刷新 marketplace 重装后 `installed` 转绿；本批含
  禁区（validator）变更，属人工实施；无对照评测证据（同 0.3.4–0.3.6 定位）。

## 0.3.8 — 再犯类台账与 P 级严重度（2026-09-16，当前源码，宿主快照待重装）

- **触发**：用户要求（1）严重度用更好懂的档位（P0–P3）标记；（2）建立"自迭代升级"追踪——
  同类问题改了又出现、再修再出现要加重标记，单独文件夹区分，并记录"在第几个升级里
  归纳修复、之后再犯没有"。现状缺口：记录之间没有字段关联，"这类问题在 0.3.4 归纳过、
  至今未再犯"只存在于正文散文，机器查不到。
- **改了什么**：
  - `severity` 改优先级档位 `P0`（critical）/`P1`（high）/`P2`（medium）/`P3`（low），
    存量 6 条与正反例同步迁移；`report` 第 4 列直接输出档位；
  - 新类台账 `records/bugs/recurrence/<class_id>.md`（契约 `schemas/recurrence.schema.json`）：
    `status` = `unconsolidated`（未归纳升级）/ `consolidated`（已归纳升级 + `consolidated_in`
    版本）；`occurrences` 列记录 id；记录的 `class_id` + `occurrence` 与之交叉关联；
  - 档位由事实**推导**（禁止手写）：新增 `validate.py recurrence` 输出 `single`（只有一次）/
    `recurred`（改了又出现）/ `escalated`（归纳后再犯——根据记录 `agentflow_version` 是否
    高于 `consolidated_in` 自动判定，是触发 improve 环升级的最高档加重标记）；
  - 门变更（用户指示下人工实施）：validator 遍历排除台账目录并新增台账校验 + 交叉引用
    检查（引用记录必须存在、带 class_id 的记录必须有台账且被台账列出、occurrence 唯一、
    已归纳类的记录必须带 agentflow_version）；新 schema 进必需保护区清单；钉住测试 +3 例；
  - 回填首个真实台账 `unverified-behavior-claims`（0.3.4 经边界 12 归纳，至今 0 次再犯）；
  - 角色与文档：`bug-recorder`（档位、台账职责、归纳状态只能来自真实发布）、
    `bug-investigator`（先查台账、提议 class_id/occurrence）、两份 records README、
    roles.md、improve SKILL（台账是一等 episode 源）、中文镜像。
- **解决了什么**：一类问题现在有完整的机器可查时间线（首现 → 归纳版本 → 再犯记录 →
  档位自动加重）；"改了又出现"不再依赖人记得比对旧记录。
- **效果状态**：条款与工具行为已在 /tmp 副本上做过四组负向实验 + 一组正向（escalated）
  验证；对真实运行的效果无对照评测（同前）。
- **未决**：宿主快照仍为 0.3.4；本批含 schemas/ 与 validator 的门变更，属人工实施；
  跨项目（aiwork 等）的类台账沿用同一目录、用 `project` 字段区分。

## 0.3.9 — 来源归属 provenance（2026-09-16，当前源码，宿主快照待重装）

- **触发**：用户指出——必须能区分问题是不是 Agentflow 产生的：会话里"自己写的计划和分析"
  与 Agentflow 条款/角色/门的产物混在一起，improve 环可能把模型即兴发挥的缺陷当成方法的
  证据去改；此前 `attribution` 只在"哪一层出错"上作答，没有"产物归谁"的字段。
- **改了什么**：
  - 新必填字段 `provenance`：`agentflow`（Agentflow 自身表面：条款/角色/门/评测/简报纪律/
    tools 工具）/ `session-artifact`（会话内即兴产出、无条款覆盖）/ `user-input` /
    `external`（业务仓既有代码、宿主、工具、环境）/ `undetermined`（必须写明缺的证据）；
  - **归因铁律**（schema 强制）：`attribution` 为 `workflow_policy`/`role_prompt` 时
    `provenance` 必须为 `agentflow`——不能既把责任归给 Agentflow 的规则、又承认产物不来自
    Agentflow；
  - 改进环过滤：improve SKILL 步骤 2/4 与 feedback-analyst 角色明确"只有 `agentflow` 记录是
    候选证据，其余是上下文/反例，`undetermined` 先解决归属"；
  - `validate.py report` 追加第 7 列（既有列号不变，`cut -f5` 等用法不受影响），支持
    `awk -F'\t' '$7=="agentflow"'` 过滤；存量 6 条与正反例迁移；
  - 判定依据要求：investigator 归 `agentflow` 须引用覆盖条款 `path:line`，归
    `session-artifact` 须写明无条款覆盖及理由。
- **解决了什么**：每条记录现在必须先回答"这是不是 Agentflow 的问题"，且答案受 schema
  一致性约束；改进环的证据面从"所有 bug 记录"收窄为"确属 Agentflow 的记录"。
- **效果状态**：规则在 /tmp 副本上做过负向实验（缺字段被拒、矛盾归因被拒、非 Agentflow
  取值合法）；对真实运行的效果无对照评测（同前）。
- **未决**：宿主快照仍为 0.3.4；本批含 schema/validator/钉住测试的门变更，属人工实施。

## 0.4.0 — 吸收 aiwork 仓库的优点（2026-09-16，当前源码，宿主快照待重装）

- **触发**：用户要求系统看 `aiwork-workflow-ai`（角色/rule/模板/docs/features 体系），
  合理吸收、避开坑点。评估结论：其设计模板有 agentflow 缺的「工程血肉」（时序/异常
  矩阵/发布顺序），issue 记录有关闭条件/修复落点/变更记录三个可吸收优点，且用户的实际
  用法（aiwork 产出、agentflow 二次评审）需要一座证据桥。
- **批 1（设计完备性 + issue 优点）**：
  - `contracts.md` 新增「重要特性设计完备性三件套」：关键链路时序（步骤表为基准、图
    作补充且不得不同口径）、异常矩阵（超时/重复/冲突/回调失败 × 检测/处理/重试方·次数·
    退避/幂等前提/用户可见/告警；废话兜底按缺陷退回）、发布顺序×回滚点配对——与既有
    隐式行为检查互补（那个管横切机制，这个管声明流程）；plan-architect、
    technical-director、中文镜像同步；
  - `closure_criteria`（verified 必填，可度量关闭判据）+ `fix_revision`（修复落点）+
    `## 变更记录` 正文约定（流转 append 流水）。
- **批 2（评审桥）**：
  - `records/reviews/<日期>/<project>-<slug>/`：review.md + archive/ 逐字快照 +
    `source_revision`；契约 `schemas/review.schema.json`；
  - 工作流（SKILL 新节 + 路由行 + reviews/README + 中文镜像）：先快照再评审、发现逐条
    进 `records/bugs/`、`provenance` 分流升级回路（external=升级业务仓模板的证据池，
    agentflow=升级本仓 review 契约）、`fix_revision` 闭环；
  - 校验器强制：快照在盘、findings 的 bug_id 存在、日期目录/命名格式。
- **避开的坑**（见交接文档第十四批记录）：不引入按阶段文档模板体系、不做双状态机、
  不写个人绝对路径、检查不许"条件允许时执行"。
- **效果状态**：负向实验（/tmp）：缺 closure_criteria 的 verified 被拒、review 引用
  不存在 bug_id 被拒、快照缺失被拒；对真实运行无对照评测（同前）。
- **未决**：跨仓再犯类 escalated 档位不能自动推导（consolidated_in 绑本仓 semver），
  先用 report 聚类；宿主快照重装；含 schemas/validator/钉住测试门变更，属人工实施。

- **发布前用户修订两处（0.4.0 未提交时并入）**：
  - **评审目录改为 feature 锚**：用户指出按日期分目录在「同一 feature 反复评审」场景下
    是错的——今天/明天/修完再评会散落在互不相干的日期目录里。改为
    `<project>-<feature-slug>/` 一个 feature 一个目录，每轮 `review-<日期>-<NNN>.md`
    （文件名 = review_id），快照进 `archive/<日期>-<序号>/`（同名文档跨轮不冲突），
    再评审聚焦上轮 delta；
  - **引用自包含**：用户提出可移植性缺口——仓给了别人，记录里引用的外部仓/文件就成了
    悬空引用。规则（validator 强制）：`files` 条目要么本仓路径（查在盘），要么仓限定
    `<repo>@<revision>:<path>`；裸外部路径 FAIL。仓限定是地址、正文内嵌片段/原文才是
    证据（代码贴 `## 问题代码`、文档引关键原文）；`@<revision>` 不自检，快照完整性由
    评审桥的 `archive/` 承担。正例已改为仓限定演示形式。
  - **片段规则升级为机器强制**（用户追问"能不能 copy 或记录片段"）：含仓限定引用的
    记录，正文必须存在内嵌片段（代码围栏块或文档引用块）**且**片段旁出现该仓限定地址
    原文，两者缺一 FAIL（`validate_external_excerpts`，钉住单测 + /tmp 负向实验各覆盖
    一条）；评审发现的 `files` 优先指向本仓快照
    `records/reviews/<feature>/archive/<轮次>/<doc>.md`（整份 copy 在 archive，本仓路径
    直接过在盘检查），原始仓限定地址写正文。
  - **正文引用规则**（用户明确"禁用引用、保留实际、关联的上下文/文档/代码也要处理"）：
    `validate_body_references` 应用于 bug 记录、评审记录与类台账——散文里的路径是记录
    自己的主张，必须在盘或仓限定；围栏块与内联代码是**引文**（逐字证据、含历史路径）
    豁免；个人绝对路径禁止；URL 至多补充、不得作证据。存量 6 条实测零误伤（3 处历史
    路径全在引文里，原样保留）；钉住单测覆盖拒绝/豁免/解析三种形态。
  - **发布前自审修复四个缺陷**（当批代码当批审，钉住单测 + /tmp 实验验证）：①正文路径
    模式不识别中文 token——aiwork 场景的核心形态（`docs/缺失文档.md`）会漏检，改用
    `\w` 类模式并实验确认版本号斜杠（`0.3.4/0.3.5`）不误伤；②review walker 按文件名
    匹配不看深度——archive 深处同名 `review-*.md` 快照会被误校验，改为仅第 4 层；③
    review_id 无全局唯一性检查；④review_id 日期与 recorded_at 不校验一致性。

## 0.4.1 — 文档一致性门与 episode 落盘（2026-09-17，当前源码，宿主快照待重装）

- **触发**：0.4.0 自审暴露"声明与实现不同步"缺陷家族后，P1 待办两条性价比最高项：
  ①角色-文档手工同步面无机器检查（manifest 漏 bump 的同类漂移风险）；②improve 环
  缺任务级证据（episode 只有会话级纪律，没有落盘形态）。
- **改了什么**：
  - `validate.py docs`（进 `all`，八项）：角色文件 frontmatter name = 文件名、SKILL 引用
    的 `agentflow:*` 必须有对应 agents 文件、文档提到的 `schemas/*.schema.json` 必须存在、
    中文镜像与 contracts.md 的 schema 引用面一致。**首跑抓到真实漂移**：硬边界 6 未点名
    新增的四份记录契约——已重写边界 6 逐一致引用；
  - episode 最小落盘：`records/episodes/<日期>/<EP-id>.json`，supervisor 会话收口时写；
    契约**复用** improve 环的 `skills/improve/references/episode.schema.json`（第一次
    起草了平行载体，被本仓"扩展契约先 grep 已有载体"纪律自拦，删除重来）——校验器
    编译 episode（schema、文件名=id、id 全局唯一）；SKILL 步骤 10 指明精确落点；已回填
    首条真实 episode（0.4.0 吸收会话）；
  - `validate.py report --project/--status/--provenance` 过滤参数，替代记忆列号拼 awk。
- **解决了什么**：漂移面从"人记得对照"变成机器断言（docs 门首跑即证明有效）；improve
  环有了 bug 记录之外的第二种证据形态，feedback-analyst 与 bug-investigator 的输入开始
  分化。
- **效果状态**：钉住单测 17 例（+2）；/tmp 负向实验三组（假角色名、假 schema 引用、
  episode 文件名不符）全按预期拒；negB 首次尝试还自查出一处测试目标选错（文件里本无
  该字符串）——重选目标后确认拦截有效。
- **未决**：episode 的实际写入密度（多少任务会真的落盘）待观察；宿主快照重装；方法
  有效性对照 smoke 仍待用户拍板端点与预算。

## 0.4.2 — 外部会话立案的三条条款修复（2026-09-17，当前源码，宿主快照待重装）

- **触发**：兄弟会话在 `infinite-canvas` 工作期间立案三条记录（BUG-20260917-01/02/03，
  已在 0.4.1 批次一并入库）：①推送被拒后未经授权自行 rebase 集成远端提交（集成操作
  不在授权边界清单内）；②同一分支被两个执行者并发写入（文件级隔离没延伸到 git 层）；
  ③状态类结论凭会话记忆不读仓库事实（待办清单已过期）。三条均为 `provenance: agentflow`
  的 workflow_policy 缺口，记录本身写出了修复方向。
- **改了什么**（用户指示落地记录提出的修复）：
  - `contracts.md` 硬边界 3 扩写：merge/rebase/cherry-pick/拉远端进共享分支 = 同一类
    需授权动作；推送被拒默认只读汇报（fetch + log/diff 列重叠面），集成方式由用户选；
  - `SKILL.md` 三处：Intake 增加状态结论必须先 `git fetch` 校准并附证据命令；Delegate
    增加 git 层写入隔离（各自分支/工作区、同分支单一写入者、发现占用即停并上报）；
    Preserve control 增加集成授权与推送被拒默认动作；
  - 中文镜像同步；三条记录转 `fixed-pending-review`（`regression_status: not-run` ——
    规则文本变更无自动化检测面，转 verified 前需评审人指定能证明约束生效的检查）。
- **解决了什么**：这是首批**由外部会话记录驱动**的条款修复——评审桥/记录池的反馈回路
  第一次真实运转（记录 → 归因 agentflow → 条款落地）。git 层的控制边界从"只列了
  push/deploy"补全为"集成与改写历史同权"。
- **效果状态**：无对照评测（同前）；三条记录等待独立评审转 verified。
- **未决**：规则约束生效与否的可证明检查手段（三条记录共同缺口，已写入各自变更记录）。

## 0.5.0 — plan 契约融合重设计（2026-09-17，当前源码，宿主快照待重装）

- **触发**：用户看不懂 JSON 计划、要求对照 aiwork 的 Markdown 计划评估。对比结论：aiwork
  形态人读性碾压（三视角任务表、计划即看板、实战信息密度），agentflow JSON 机器校验强
  （依赖图、唯一性、schema 编译）——两者其实在回答不同问题。用户选方案 A：融合。趁
  `records/plans/` 无存量，零迁移成本。
- **改了什么**：
  - `schemas/plan.schema.json` 重写为 frontmatter 信封（plan_id/版本/状态枚举/目标/
    时间戳/superseded_by）；
  - `validate_plan_markdown` 新校验链：正文看板（`## 进展概览`/`## 任务清单`/`## 验证命令`）
    + 机器断言——任务 ID 唯一、依赖可解析且无环、状态固定枚举
    （☐未开始/◐进行中/☑已完成/⚠阻塞/—本期不做，自由文本被拒）、**阻塞未决项未关闭不得
    approved**（吸收 aiwork 缺口登记门）、必需章节存在、文件名=plan_id；
  - 从 aiwork 吸收：三视角概览表（业务侧/技术侧/交付效果）、计划即看板（状态+证据回写列，
    最小 diff 纪律）、未决项阻塞门；既有设计完备性四件套（时序/异常矩阵/发布顺序×回滚）
    融入 `## 接口与共享机制` 章节；
  - 旧 JSON 契约与 invariants 删除（含钉住测试替换）；正例按对话分享真实密度重写
    （PLAN-DEMO-SHARE-001），反例 PLAN-INVALID-002 集环/重复 ID/非法状态/阻塞未决四缺陷；
  - plan-architect 角色重写为新格式指引；plans README/records 索引/SKILL 断点恢复段/
    中文镜像同步；mock 同步。
- **解决了什么**："计划给谁看"的矛盾消解——同一份文件既是人看的看板（进度、三视角、
  回写证据）又是机器校验的合同（无环、枚举、门）；断点恢复协议有了可读的锚。
- **效果状态**：钉住测试 18 例全过；/tmp 独立实验三断言（环/非法状态/阻塞未决）分别命中；
  开发中自抓并修复三处解析缺陷（表头误判、中文顿号分隔、"不阻塞"含"阻塞"子串误伤）。
- **未决**：首个真实跨层功能走规划流程后复盘格式是否顺手；宿主快照重装。
## 0.5.1 — 文档评审模式（2026-09-17，当前源码，宿主快照待重装）

- **触发**：用户问「要写 spec/design/proposal 需要吸取吗、怎么吸取方便后续用」。判断：
  吸收**质量判据**（按文档类型的评审清单），不重建模板体系（重模板正是要避的坑）；
  文档产出继续留在业务仓，agentflow 的价值在第二道评审有固定清单。
- **改了什么**：`agents/reviewer.md` 新增 Document review modes——proposal/PRD（范围
  in/out 可核查、判据可判定、场景落具体对象、不做清单、历史衔接）、spec（语义/边界/
  异常分支冻结、统一判定口径、降级、边界场景清单、上游缺口登记且阻塞关闭才算冻结）、
  design（设计完备性四件套 + 契约兼容/幂等/并发/事务 + 可观测性 + 验收口径不另造）；
  每条必须引用原文句或 `path:line`，引不出即未过、该有而没有本身就是发现。plan 走本仓
  契约、无需外部档。
- **配套**：评审桥 README 与 SKILL 步骤 2 写明按文档类型选档；roles.md reviewer 画像同步；
  mock 评审记录补「应用检查档」；版本 0.5.1 全套。
- **解决了什么**：二次评审从通用检查升级为按文档类型逐项引用原文——吸收的是 aiwork 各
  模板的强制项与判据（含 PRD 不合规登记、统一判定口径、验收不另造），不是它的目录形式。
- **未决**：真实评审一单 spec/design 后复盘清单是否够用、是否需增补轻量骨架。

## 0.5.2 — 0.5.x 自审修复（2026-09-17，当前源码，宿主快照待重装）

- **触发**：用户要求仔细检查 0.5.0/0.5.1 是否还有遗漏。
- **自审发现（按严重度）**：
  - **静默门缺口**：反例 `PLAN-INVALID-002.md` 从未被 examples 检查拾取——glob 只匹配小写
    `plan-` 前缀，而"必须含反例"的断言又被 bug-record 反例单独满足，门看着在跑、实际
    没测计划反例。修复：大小写不敏感匹配 + "有合法计划例必须有非法计划例"独立断言；
    /tmp 实验双验证（把反例改合法 → expected invalid 被拒；删掉反例 → both required 报错）；
    新增钉住回归测试（19 例）。
  - **死代码**：`schema_for` 仍把 `examples/invalid/plan-*` 映射到 plan schema（计划校验
    已改走 Markdown 路径），删除。
  - **旧措辞五处**（parallel lanes 时代残留）：plan-architect description、SKILL 计划段、
    roles.md 计划画像、中文镜像的 `shared_mechanisms[]` 句（改为「接口与共享机制」表 +
    注册点）、plans README 结构块（补评审门）。
  - **失效文档面两处**：records/README 的计划查询还是 `jq … plans/*.json`（已改
    grep frontmatter）；tools/lab/README 未记 `docs`/`report`/`recurrence` 三个目标、
    artifacts 描述未覆盖五种记录类型（已补）。
- **解决了什么**：门从"看起来在跑"回到"确实在跑"——这正是 BUG-20260917 系列的同一失败族
  （声明与执行不符），由自审 + 负向实验逐条抓出。
- **未决**：宿主快照重装；其余同前。

## 0.6.0 — 业务任务度量切片（2026-09-17，当前源码，宿主快照待重装）

- **触发**：方法级改动长期只能以 `measurement: none (method-level change, no instrumented
  business task)` 发布（0.3.6 起的诚实标注，用户要求把这个过渡态消灭）。
- **改了什么**：`evals/business/` 三用例（种子缺陷提交、内部矛盾、跨文档一致性）+
  种子缺陷确定性评分 `tools/lab/seed_grader.py`（进保护门）；runner/adapter 业务面
  （`--business-root` / `--seed-patch`、workspace-write 档、调用后快照文件集合 + `git diff`
  摘要复检、评分覆盖 `accepted`/`escaped_defects`）；`isolation.py` 第四位置；
  `validate.py` 接线 `validate_business_evals`；判断词可判定定义（小改动 / risky work /
  相同原因）进 SKILL 与中文镜像；episode `provenance` 收紧；GitHub Actions 校验 workflow；
  `run_codex` 结果文件读取与 `claude_failure_detail` 两处缺陷修复（各带回归测试）；业务跑对
  claude 追加 `--add-dir <快照根>`（`--print` 模式把工具文件访问限制在 cwd，首轮 smoke 因此
  读不到快照），含两条 argv 回归测试与 host-platform-facts C8 行。
- **批内独立评审**：一轮 `changes_requested`（fail-open 评分覆盖、业务身份绕过口、计划文件
  脱敏泄漏、锚点跨字段拼接）→ 修复轮 A/B → 终审 `approved`；修复轮后追加 delta 评审。
- **解决了什么**：一类方法级改动第一次具备可跑的对照仪器（工具与契约层面）；上述运行时与
  诊断缺陷关闭。
- **未决/未验证**：smoke 实跑（S02）处于进行中——状态与三次尝试的原始留痕见
  `records/plans/PLAN-BUSINESS-EVAL-001.md` 的 S01/S02 行（当时证据为本地 progress JSONL，
  不入仓）；数字只能定级为 smoke / 噪声底，不构成权威 baseline；U-01（可信端点）未决，
  U-02 已实测、U-03 已决（见同计划）；ZCode 未做 host adapter；`measurement: none` 在真实
  对照产出前不得宣称消灭。
