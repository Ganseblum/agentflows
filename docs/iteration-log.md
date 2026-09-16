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
