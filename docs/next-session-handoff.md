# Agentflow 新对话交接清单

更新时间：2026-09-18

> 当前机器路径以本文件所在仓库为准；不要复制历史机器的绝对路径作为当前事实。阶段四、五已补齐 episode 可验证字段、SQLite FTS5 记录读侧和 measurement 语义；根目录对话记录/历史报告未删除，按 allowlist 打包时排除。

## 当前工作区

- Agent 项目目录（当前机器）：`/Users/hang/Documents/myProject/agentflow`
- 当前配置的 Git remote 为 `https://github.com/Ganseblum/agentflows.git`；`main` 与
  `origin/main` 一致。远程是否已同步以实际 `git remote -v` 和 fetch 结果为准，不把历史机器的
  仓库名当成事实。
- 本机 ZCode 已有可被 `validate.py installed` 默认发现的安装源：local-directory marketplace
  指向本仓库，快照缓存为 `~/.zcode/cli/plugins/cache/agentflow-local/agentflow/<version>/`。
  该快照在 2026-09-15 重装过一次；发布新版本后需刷新 marketplace 再重装，否则 `installed`
  会报"没有源码版本的快照"。Codex 侧 `0.3.1` 缓存路径来自上一台机器，仅作历史记录。
- 下文记录的上一台机器路径、旧 CLI 仓库、candidate/holdout 目录均只作历史证据，不代表当前
  工作区存在。
- 旧 CLI 仓库继续保留为历史 runtime 和研究实现，不再是 Plugin 的运行依赖。

## 已完成

- 2026-09-17 第十九批：0.5.2 自审修复（用户要求检查遗漏）：
  - **静默门缺口**：计划反例 `PLAN-INVALID-002.md` 从未被 examples 检查拾取（glob 小写
    `plan-` vs 大写文件名；"必须有反例"断言被 bug-record 反例单独满足）。修复：大小写
    不敏感 + 独立断言 + 钉住回归测试；/tmp 双实验证明修复后真的在测。
  - 死代码（schema_for 的 plan 分支）、五处旧"parallel lanes"措辞、两处失效文档面
    （records/README 的 jq 查询、tools/lab/README 目标清单）一并清理。

- 2026-09-17 第十八批：0.5.1 文档评审模式（用户问 spec/design/proposal 是否需要吸取）：
  - 判断：吸收**质量判据**（按文档类型的评审清单），不重建 aiwork 的模板体系；文档产出
    继续留在业务仓，agentflow 提供第二道评审的固定清单。
  - `agents/reviewer.md` 新增 Document review modes：proposal/PRD（范围可核查、判据可
    判定、场景落对象、不做清单、历史衔接）、spec（语义/边界/异常冻结、统一判定口径、
    降级、边界场景、上游缺口登记且阻塞关闭才算冻结）、design（设计完备性四件套 + 契约
    兼容/幂等/并发/事务 + 可观测性 + 验收口径不另造）；每条必须引用原文句/`path:line`，
    "该有而没有"本身就是发现；plan 走本仓契约。
  - 评审桥 README/SKILL 步骤 2/roles.md/mock 同步；版本 0.5.1 全套。
  - 顺带修复：iteration-log 一处内容错位（§0.4.0 的"发布前用户修订"段此前被排到 §0.5.0
    之后，已归位）。

- 2026-09-17 第十七批：0.5.0 plan 契约融合重设计（用户选方案 A，含**门变更**）：
  - 起因：用户看不懂 JSON 计划，对照 aiwork Markdown 计划后确认融合方向——人读性
    （三视角任务表/计划即看板）+ 机器校验（无环/枚举/门）合一。`records/plans/` 无存量，
    零迁移。
  - 新形态 `records/plans/<plan_id>.md`：frontmatter 信封 + `## 进展概览`（三视角表）+
    `## 任务清单`（任务表+`### 未决项`）+ `## 接口与共享机制` + `## 验证命令`；
  - 机器断言：文件名=plan_id、任务 ID 唯一、依赖可解析且无环、状态固定枚举
    （☐◐☑⚠—）、**阻塞未决未关闭不得 approved**；进度回写最小 diff（只改状态与证据列）；
  - 正例按对话分享真实密度重写；反例集四缺陷；钉住测试 18 例；/tmp 三断言独立命中；
    开发中自抓三处解析缺陷（表头/顿号/"不阻塞"子串）并修复；
  - plan-architect 重写；plans README/records 索引/SKILL/中文镜像/mock 同步。

- 2026-09-17 第十六批：0.4.2 外部会话记录驱动的条款修复（用户指示）：
  - 兄弟会话（infinite-canvas）立案的三条 P1（BUG-20260917-01/02/03）落地为条款：
    硬边界 3 覆盖 merge/rebase/cherry-pick（集成=同权需授权，推送被拒默认只读汇报）；
    Delegate 补 git 层写入隔离（各自分支/工作区、同分支单一写入者、发现占用即停）；
    Intake 补状态结论必须 `git fetch` 校准附证据命令；
  - 中文镜像同步；三条记录转 `fixed-pending-review`（regression_status: not-run，诚实标注：
    规则文本无自动化检测面，转 verified 前需评审人指定检查）；
  - 意义：**外部会话记录 → 条款修复的回路首次真实运转**（记录池不只归档，还驱动了修复）。
  - 另记一条本会话操作失误：0.4.1 提交时用 `git add -A` 未审先推了这三条他方记录——
    已如实报告并保留（内容合规、无危害）；今后提交逐文件指定路径。

- 2026-09-17 第十五批：0.4.1 文档一致性门 + episode 落盘（P1 两条，含**门变更**）：
  - `validate.py docs`（进 `all`，八项）：frontmatter name=文件名、SKILL 角色引用、
    schema 路径存在性、中文镜像引用面与 contracts.md 对齐——**首跑抓到真实漂移**
    （硬边界 6 未点名四份记录契约，已重写逐一致引用）；
  - episode 最小落盘：`records/episodes/<日期>/<EP-id>.json`，契约复用 improve 环
    episode.schema.json（首次起草平行载体被"扩展契约先 grep 载体"纪律自拦），校验器
    编译 + id 全局唯一；SKILL 步骤 10 指明落点；回填首条真实 episode（0.4.0 会话）；
  - `report --project/--status/--provenance` 过滤参数；
  - 钉住测试 17 例；/tmp 负向实验三组（假角色/假 schema/文件名不符）全按预期拒；
  - 待办清单 P1 两条相应关闭。

- 2026-09-16 第十四批：0.4.0 吸收 aiwork 仓库优点（用户指示，含**门变更**）：
  - 起因：用户要求系统评估 `aiwork-workflow-ai`（模板/issue/双仓用法），合理吸收。
  - 批 1：设计完备性三纪律（关键链路时序·步骤表基准 / 异常矩阵·四强制行 / 发布顺序×
    回滚点）进 contracts.md + plan-architect + technical-director + 中文镜像；
    `closure_criteria`（verified 必填）+ `fix_revision` + `## 变更记录` 约定。
  - 批 2：`records/reviews/` 评审桥——review.md + archive/ 逐字快照 + source_revision，
    契约 `schemas/review.schema.json`；SKILL 新节 + 路由行 + reviews/README；`provenance`
    分流（external=业务仓模板升级证据池 / agentflow=本仓 review 契约）。
  - **门变更**：2 个 schema 字段 + verified 条件 + review schema + validator reviews
    遍历/交叉引用 + 必需保护区条目 + 钉住测试。负向实验（/tmp）：缺 closure_criteria
    被拒、引用不存在 bug_id 被拒、快照缺失被拒。
  - 避开的坑（有意不吸收）：按阶段文档模板体系、双状态机（collaboration_stage×
    internal_phase）、个人绝对路径、巨型单 README、"条件允许时执行 validate"的松动、
    格式四轮迁移史。
  - 已知边界：跨仓再犯类 escalated 不能自动推导；先用 report 聚类。版本 0.4.0 全套。
  - **发布前用户修订两处（并入 0.4.0）**：①评审目录改 feature 锚
    （`<project>-<feature-slug>/` + 每轮 `review-<日期>-<NNN>.md` + `archive/<日期>-<序号>/`
    快照——同一 feature 反复评审不再散落日期目录）；②引用自包含（`files` 外部路径必须
    `<repo>@<revision>:<path>` 仓限定，裸外部路径 validator FAIL；**含外部引用的记录正文
    必须内嵌片段且片段旁标注仓限定地址原文，缺一 FAIL**——`validate_external_excerpts`
    + 钉住单测；评审发现的 `files` 优先指向本仓 archive 快照，整份 copy 由评审桥承担，
    记录只嵌决定性片段——回应"仓库给别人用"的可移植性问题）；③**正文引用规则**
    （`validate_body_references`，bug/评审/台账三链同用）：散文路径必须在盘或仓限定、
    围栏块与内联代码作引文豁免（存量 3 处历史路径零误伤）、个人绝对路径禁止、URL 只作
    补充不作证据——回应"禁用引用、保留实际、关联上下文也要处理"。

- 2026-09-16 第十三批：0.3.9 来源归属 `provenance`（用户指示，含**门变更**）：
  - 起因：用户要求记清"问题是不是 Agentflow 产生的"——区分 Agentflow 条款/角色/门的产物
    与会话内自己写的计划/分析，否则改进环会把非 Agentflow 的缺陷当证据。
  - 新必填字段 `provenance`：`agentflow` / `session-artifact` / `user-input` / `external` /
    `undetermined`（写明缺的证据）；
  - **归因铁律**（schema 强制）：`attribution` = `workflow_policy`/`role_prompt` ⇒
    `provenance` 必须 `agentflow`；
  - 改进环过滤（improve SKILL 步骤 2/4 + feedback-analyst）：只有 `agentflow` 是候选证据；
  - `report` 追加第 7 列（列号不变），`awk -F'\t' '$7=="agentflow"'` 可过滤；
  - **门变更**：schema 字段 + guard、report 列、钉住测试 +1 例；负向实验（/tmp）：
    缺字段被拒、矛盾归因（workflow_policy + external）被拒、`session-artifact` 合法；
  - 存量 6 条与正反例迁移；investigator/recorder/feedback-analyst/roles.md/两份 README/
    中文镜像同步；版本 0.3.9 全套。

- 2026-09-16 第十二批：0.3.8 再犯类台账 + P 级严重度（用户指示，含**门变更**）：
  - 起因：用户要求严重度用 P0–P3 好懂的档位；并建立自迭代升级追踪——同类问题"改了又
    出现/再修再出现"要加重标记、单独文件夹区分、记录"在第几个升级归纳、之后再犯没有"。
  - `severity`：`P0`/`P1`/`P2`/`P3`（原 critical/high/medium/low），存量 6 条与正反例迁移。
  - 类台账 `records/bugs/recurrence/<class_id>.md`（新契约 `schemas/recurrence.schema.json`）：
    `unconsolidated`/`consolidated` + `consolidated_in` 版本；记录侧 `class_id` + `occurrence`。
  - 档位**推导不手写**：`validate.py recurrence` 输出 `single`/`recurred`/`escalated`
    （escalated = 记录 `agentflow_version` 高于 `consolidated_in`，自动加重）。
  - **门变更**：validator 新增台账遍历/校验/交叉引用 + 新查询目标；新 schema 进必需保护区
    清单；钉住测试 +3。负向实验（/tmp 副本）：旧 severity 被拒、无台账的 class_id 被拒、
    台账未列出的记录被拒、已归纳类缺版本被拒；正向：合法再犯记录 → `escalated`。
  - 回填首个台账 `unverified-behavior-claims`（0.3.4 归纳，0 次再犯）。
  - 角色/文档：`bug-recorder`、`bug-investigator`、roles.md、两份 README、improve SKILL
    （台账为一等 episode 源）、中文镜像；版本 0.3.8 全套。发布性质同前：开发版本，无对照评测。

- 2026-09-16 第十一批：0.3.7 记录语言统一（用户指示，含**门变更**）：
  - 起因：记录混用——同文件内英文 `title` + 中文正文 + 英文章节标题；另一台机器的记录
    用中文 title。约定此前不存在于任何文档。
  - 约定（`records/README.md` + 中文镜像）：机器层英文 ASCII；章节标题固定中文字面量
    `## 现象`/`## 根因`/`## 修复`/`## 问题代码`/`## 审查`；人读层单语、title 与正文同语言、
    默认中文。
  - **门变更**：`tools/lab/validate.py` 标题字面量与 Fix/Review 检查改中文（用户明确指示
    下人工实施）。负向实验：英文标题 → `body section '## 现象' is required`；中文 → 通过。
  - 存量 6 条记录 title + 章节标题中文化（`updated_at=2026-09-16T11:48:32Z`）；examples
    正反例全文翻译；`agents/bug-recorder.md`、`records/bugs/README.md` 同步。
  - 版本：五 manifest 0.3.7、CHANGELOG、README 与三份设计文档引用、迭代记录 §0.3.7。
  - 发布性质同前：开发版本，无对照评测证据；宿主快照待重装。

- 2026-09-16 第十批：0.3.6「执行层牙齿与诚实标注」发布（用户授权，起因：能力盘点发现
  四类声明-执行缺口）：
  - **write_scope 执法**（此前业务仓库里纯约定，`isolation.py check-diff` 只管改进环候选
    树）：硬边界 14 + 新脚本 `skills/agentflow/scripts/check-write-scope.sh <base> <scope>...`
    （列出基线以来的全部改动——tracked/untracked/删除/双端改名——逐路径对照声明范围，越界
    即 FAIL 并点名）。实测三用例：界内 OK、越界精确点名 3 个 skills 路径、坏 revision 报
    usage error。SKILL.md 步骤 7、contracts.md、中文镜像同步。
  - **断点恢复协议**：会话中断从 `records/plans/` 版本化计划恢复，工作包状态从工作区
    重新推导（对委派基线的 diff、检查、review 决策），无证据视为未开始；持久队列/租约
    仍是未来 `execution-coordinator`。
  - **episode 捕获纪律**：SKILL.md 步骤 10——结果可能喂改进环时，会话结束前把决策记录
    （目标/结论/claims 台账/review 决策/成本）落成持久形式；对话一丢证据不可恢复。
  - **方法级改动诚实标注**：improve SKILL 显式声明 `evals/` 只测 Agentflow 自身契约用例，
    改变角色在业务仓库内行为的候选按 `measurement: none (method-level change, no
    instrumented business task)` 发布，不得称已验证；业务任务度量切片列为 P1。
  - **maxTurns 诚实声明**：ZCode 声明未验证（事实 Z6），预算纪律以提示词为准，frontmatter
    数字按意图元数据对待。
  - **小项**：worker result 增加可选 `cost`/`duration`（实测或 `not reported`，禁止估算）；
    reviewer test-depth 的 revert 实验显式化为「reviewer 定命令与预期、supervisor 执行回传
    原始输出」；`references/roles.md` 补全 12 角色画像 + 任务形态路由表；四个角色
    description 去掉 "for Agentflow" 限定；中文镜像 `docs/agent-roles.md` 全量同步。
  - 版本发布：五份 manifest 0.3.6、CHANGELOG、README、三份设计文档版本引用、迭代记录
    §0.3.6。发布性质同 0.3.4/0.3.5：开发版本，无 baseline/candidate 对照证据。
  - 本批含上一批遗留的 4 个未提交文件（reviewer 专项审查、investigator no-defect、
    roles.md 两条、SKILL.md step 8 浏览器归属），一并进入本版。

- 2026-09-15 第九批：应用「对话分享」复盘补丁 + 迭代记录（用户要求）：
  - 按外部项目复盘文档（`aiwork-workflow-ai` 的 `复盘-agentflow优化建议.md`）应用 P1–P9，
    应用前逐条核对锚点与源码一致：`contracts.md` 新增硬边界 13（缺席断言读权威落点）、
    Final decision record 增加 `claims` 台账、简报三纪律（Replication / Mirror /
    Extension inventory）、新小节 `Verification stand-ins`；`SKILL.md` step 8（e2e 先于
    关门 + 后置用户可见改动重开门）与 step 10（claims 台账）；`reviewer.md`、
    `frontend-engineer.md`、`plan-architect.md` 对应条款；中文侧 `docs/agent-roles.md` 同步。
  - 新增 [`iteration-log.md`](iteration-log.md)：按版本记录触发/改动/解决什么/未决；README
    已索引；CHANGELOG 记 0.3.5；五份 manifest 与 README/三份设计文档版本引用同步 0.3.5。
  - 状态：源码 0.3.5，本机 ZCode 快照仍 0.3.4 → `validate.py installed` 报红属预期；刷新
    marketplace 并重装后转绿。本轮为开发版本，无对照评测证据，不得表述为"已验证的改进"。
  - 补充：0.3.5 补丁的覆盖缺口——复盘未提议配套 AF-* 评测用例（与边界 12 先例一致：
    同类漏检再犯时升级用例）。
- 2026-09-15 第八批：0.3.4 发布（用户授权 push 与发布）：
  - 本会话第四~七批改动（横切机制契约、计划 `shared_mechanisms[]`、门缺口加固、事故记录）
    按主题拆成 4 个提交推送（`21062c0`、`abbffa9`、`985e631`、`8255df6`），均已到
    `origin/main`。
  - 发布：CHANGELOG `Unreleased` → `0.3.4 — 2026-09-15`；五份 manifest 同步 0.3.4
    （`validate.py manifests` 强制一致）；README 与三份设计/边界文档的当前版本引用同步。
  - **发布性质必须写明**：这是开发版本发布，**没有** baseline/candidate 对照评测证据。
    按 improve 环的定义它不是一次受治理的候选晋升（release-governor 门未参与），
    因此不得表述为"已验证的改进"。真实模型 dogfood 仍未完成。
  - 发布后状态：本机 ZCode 快照随后已重装到 0.3.4，`validate.py installed` 曾观测 PASS；
    第九批把源码推到 0.3.5，再次进入待刷新重装状态（报红属预期，已在风险节说明）。
  - 顺手修正交接文档的陈旧当前态（remote 名、HEAD、安装源描述在上一轮之后已过时）。

- 2026-09-15 第七批：事故的记录与防复发（用户问"这些事故能记录和避免吗"，答案落地）：
  - 两条正式 bug 记录入库（`records/bugs/2026-09-15/`，均 `fixed-pending-review`）：
    - `BUG-20260915-002`（severity: medium）：故障注入在真实仓库执行 + `git checkout`
      "恢复"把 `protected-paths.txt` 重置回提交版、冲掉未提交编辑 + 输出被吞、恢复未验证。
      归因 `missing-constraint` / `workflow_policy`——缺的是流程约束不是知识。
    - `BUG-20260915-003`（severity: high）：连续三轮"推演代替实验"的行为断言类（调用链、
      schema 可查性、`__init__` 机制三例），第三例掩盖了实际存在的完整绕过。同归因。
  - 防复发三层：`contracts.md` 硬边界 12（行为断言在最小实验复现前只是假设；是边界 4
    对 supervisor 自身推断的推广）；`AGENTS.md` 新增「Experiments and recovery」规则
    （注入只在 /tmp 副本、禁止用 checkout/restore 撤销实验、恢复必须复跑检查观察到绿、
    不得吞掉要主张成功率的命令输出）；既有门作检测兜底（本次 `validate.py protected`
    在一条命令内抓住回退，实证有效）。
  - 实务建议（给仓库所有者）：确认一批就提交一批。本次事故损失面（~25 个未提交文件被
    单文件 mishap 波及）完全来自长尾未提交；分批提交后同类 mishap 的恢复是一条命令。
  - 若边界 12 后同类断言再犯，按 improve 环升级为评测用例（记录 -003 Notes 已写明触发
    条件与本轮不加的理由）。

- 2026-09-15 第六批：门变更复审（用户授权）——修一个被我引入又被复验揪出的完整绕过，并补
  一处治理缺口：
  - **实证驱动的复审纠正了上一批的两处错误结论**：(1) `tests/__init__.py` 在
    `discover -s tests` 下惰性、根本不执行（实验 exit=0），上一批文档给它的"中和"能力是
    错的；(2) 真正的向量是**子目录**：`unittest discover` 会导入起点目录下的子目录包，
    导入副作用先于任何断言运行。实验中 `tests/asub/` 模块在导入时替换被钉住的测试方法，
    配合改坏的断言，`validate.py tests` 返回 PASS——**完整绕过实锤**。修复：内容断言从
    "拒绝未声明 .py"改为"拒绝一切未声明条目（含目录）"，`__pycache__` 除外。故障注入复验：
    同一攻击现在 FAIL 且点名 `tests/asub`；改坏断言仍 FAIL；有 `__pycache__` 仍 PASS。
  - **`skills/improve/references/` 整体进禁区**：`episode.schema.json` 是四个治理 schema 中
    唯一没被保护的。必需条目集合改为逐文件要求该目录全部五个文件，防止前缀收窄时静默
    丢保护。
  - **操作事故与教训（写在这里给后续会话看）**：本轮一次故障注入错误地在真实仓库而非
    副本上执行，随后用 `git checkout protected-paths.txt`"恢复"——但该文件已提交，
    checkout 把它重置回 0.3.3 提交版，冲掉了本会话全部未提交编辑（schemas/、tests/ 条目
    与注释块）；恢复时又用 `2>/dev/null` 吞掉了报错，且未验证结果。靠 `validate.py
    protected` 的 FAIL 才发现。两条纪律写入本节：**故障注入一律在 /tmp 副本上做**；
    **恢复操作必须观察验证结果（跑一次检查确认绿），未观察的恢复不算恢复**——与
    AGENTS.md"无法复现的检查记为未运行"同构。最终 `all` 七项全 PASS，文件内容已人工重建
    为目标状态。
  - 审计方法备注：本轮所有结论都以最小可复现实验落地（exit code 与输出原文），
    不以推演代替；上两批的两处过度表述教训已内化为本批的工作方式。

- 2026-09-15 第五批：全项目复核后补齐四处门缺口（用户授权，属门变更）：
  - `schemas/` 整体进 `protected-paths.txt`，回归测试按**文件**保护
    （`tests/test_lab_contracts.py`）。理由：记录 schema 是候选产物的编译目标、测试钉住
    `validate.py`/`isolation.py`，两者原本都可被"正在被它们评判的候选"编辑。
    `validate.py` 的必需条目集合同步要求覆盖两个记录 schema 与该测试文件。
  - 测试目录不用目录前缀保护，改用「声明内容」断言。原因是第一批实现暴露的真缺陷：
    整目录保护会让 `tests/__pycache__/*.pyc`（任何跑过检查的候选都会生成）匹配禁区前缀，
    于是门对每个跑过自己测试的候选误报 FAIL——门一旦误伤正常流程就会诱使人绕过它，
    比漏检更危险。断言改为拒绝目录内未声明的 `.py` 文件，堵住文件级保护单独留下的中和
    向量（放一个包 `__init__` 或垫片去 patch 被钉住的测试）；测试子进程同时带
    `PYTHONDONTWRITEBYTECODE=1`。
  - 新增 `validate.py manifests`：五份手工同步的 manifest 必须在插件名与版本上一致。此前漏
    bump 只在宿主重装后才暴露。
  - 新增 `validate.py tests`：仓库回归测试接入确定性检查集，`all` 从 5 项变 7 项。
    「测试存在但没人跑」的孤儿问题关闭。
  - 用故障注入验证四项检查都会失败：改一份 manifest 版本、删一条禁区条目、改坏一个断言、
    注入 `tests/__init__.py`；而残留的 `__pycache__` 不会触发阻断。
  - 单测（`tests/test_lab_contracts.py`）此前未接入任何门：无 CI、无 hook、不在 `all`、
    AGENTS.md 未提。现在 `all` 包含它，AGENTS.md 与 `tools/lab/README.md` 都写明可直接运行，
    并记录了一个交互：在候选工作树内跑 lab 工具会留下 `__pycache__`，`check-diff` 会把它列为
    changed path（因为包含被忽略文件），但不匹配禁区前缀因此不会 blocked。

- 2026-09-15 第四批：隐式行为纪律（起因：用户报告真实前端 bug——全局导航自动登录复用
  `login()`，方法本身正确，但 axios 封装的响应拦截器在 `code===401` 时跳登录页，与忘记/
  重置密码页的合法未登录态冲突，用户无法使用该流程）：
  - 诊断：写入范围被严格定义、读取范围空白；横切机制（拦截器/守卫/全局监听）类别在
    所有契约中不存在。该 bug 是两个缺陷叠加：追踪止步于复用方法自身逻辑（下一层就是
    拦截器），且缺少「表面 × 合法状态」交集检查（未登录在该页面是正确状态）。经两轮
    复核纠正了最初的两处过度表述（"不在调用链上"——其实追一层就能看见机制；"缺行可
    结构查出"——实际不可查，可查的是显式空声明）。
  - 落地（用户 2026-09-15 明确授权，含禁区/契约面变更，待人工最终确认）：
    `contracts.md` 简报拆 `write_scope`/`read_scope`（读取严格大于写入）+ 隐式行为检查
    （注册点搜索发现机制、显式声明空集、表面×状态矩阵、`path:line` 注册点引用为深度
    终止条件、残差声明）；`frontend-engineer.md`/`reviewer.md`/`bug-investigator.md` 条款
    （reviewer 要求行为级证据而非"读过代码"；investigator 对意外全局行为先枚举隐式代码、
    归因 `missing-constraint`）；`plan.schema.json` 必填 `shared_mechanisms[]`
    （`registration_ref` 必填，正反例已同步，反例仍只因循环依赖失败）；`AF-015` 用例与
    input；`BUG-20260915-001` 记录（`error_kind: missing-constraint`，
    `attribution: workflow_policy`）；中文侧 `agent-roles.md` 与 SKILL.md 步骤 4 同步。
  - 边界与残留：语义漏检做不出确定性检查，本纪律强制提问并要求证据、不能证明答案
    正确；异类新缺陷靠反馈环逐案吸收。外部项目（paipai-new-fe）自身的代码修复不在
    本仓范围。

- 2026-09-14 第三批：角色边界核查与 0.3.3 加固（起因：复核 12 个角色设置是否合理）：
  - 实测确认 ZCode 的插件 agents 生效，且 frontmatter `tools` 白名单生效（宿主 subagent
    列表里 bug-fixer 带工具限制、未声明 tools 的三个角色是全量工具）；`maxTurns` 未验证。
    已写入 `docs/host-platform-facts.md` Z4/Z6。
  - 实测确认 agents 从安装快照加载、`agents/` 无实时编辑通道：源码与
    `~/.zcode/cli/plugins/cache/agentflow-local/agentflow/0.3.2/` 逐文件对比，12 个角色和
    两个 SKILL 全部不一致——即当时运行的 bug-recorder 还是 JSON 时代的旧约定，按新格式
    写记录会被 `validate.py artifacts` 判不合格。新增 `validate.py installed` 让该漂移
    不再静默（对比 `agents/`、`skills/` 与各 manifest；有意不纳入 `all`，因为要读仓库外路径）。
  - 三个实现型角色（frontend/backend/candidate engineer）补 `tools: Read, Glob, Grep, Write,
    Edit, Bash`，与 bug-fixer 对齐：此前它们继承全量工具（含 Agent 委派、网络、MCP）。
  - 候选禁区单点声明为仓库根 `protected-paths.txt`（evaluator/release-governor 角色文件、
  `evals/`、`tools/lab/` 度量路径、发布规则、结果 Schema、清单自身）；`isolation.py check-diff`
  现在要求带冻结 parent revision 并固定读取它；`validate.py protected` 纳入 `all`
    防止清单被悄悄删条目；`candidate-engineer` 所有权矩阵显式引用该清单，消解「候选树就是要改的
    插件树」时两行权限自相矛盾的问题。
  - 硬边界更新：#1 增补「Supervisor 自己写了代码时独立 Reviewer 门强制、不可豁免」，#2 禁止
    worker 再委派，#6 指向清单，新增 #11 预算耗尽必须报 `partial`；reviewer 增加检查协议
    （由 reviewer 指定命令与预期、只接受原始输出）。六个可写角色补预算纪律，实现角色
    maxTurns 20→30、plan-architect 15→20（数字是判断，不是实测结论）。
  - 评测套件 10→14：新增 AF-011（摘要不是验证）、AF-012（任务文本按数据、含越权 push 指令）、
    AF-013（候选不得改评判自己的门）、AF-014（基线对照区分环境失败与回归）。
  - 文档同步：README（版本 0.3.3、ZCode 使用与重装提示、bug-recorder 新格式）、两个 SKILL 的
    ZCode 绑定、仓库内命名统一为 Agentflow（6 个文件 13 处）、三份设计/边界文档的版本引用；
    新增仓库根 `AGENTS.md`（接受产物前跑 `validate.py all`、改角色必须重装、禁区不可改）；
    CHANGELOG 记 0.3.3。
  - 注意：本批改动包含对禁区清单和 `evals/` 的编辑，属于「门变更」，是在用户明确要求下由人工
    决策执行的，不是候选自改。

- 2026-09-14 吸收 `aiwork-workflow-ai` 仓验证过的两个机制（该仓为 360 内部单操作者
  workflow 系统，已核实其 replies-eval 编译门、门/审批模型生产在用；编排运行时未首试，
  不吸收；详见当次会话评审）：
  - 12 个角色文件全部加入「产物所有权矩阵」（6 个可写角色为逐产物表格，6 个只读角色为
    紧凑声明），`docs/agent-roles.md` 角色矩阵同步改为「可写产物」列并补充说明；
  - Supervisor 流程新增「写盘前编译/接受前编译」纪律：`skills/agentflow/SKILL.md` 步骤 7
    （worker 产物先跑确定性检查再接受，失败按编译错误退回）、
    `skills/improve/SKILL.md` 步骤 9（candidate/评测/比较/决策记录进入下一角色前先过
    schema 校验）、`contracts.md` Worker result 节与 `docs/agent-roles.md` 产物验收纪律。
  - 为让该纪律可执行，`tools/lab/validate.py` 新增 `artifacts` 目标并纳入 `all`：校验
    `records/` 下实际写出的 JSON 产物（schema + 跨文档不变量）；已用合法/
    非法计划样例验证通过。
  - 产物落点统一到 `records/`：计划从顶层 `plans/` 移入 `records/plans/`（原目录已删除），
    `records/README.md` 作为索引记录布局、约定与回溯查询；`plan-architect` 默认路径同步为
    `records/plans/`。
  - Bug 记录按用户需求重构为 Markdown + frontmatter（正文：错误现象/问题代码/原因/修复；
    frontmatter：id/状态/严重性/`error_kind` 错误类型/归因/`project`/`files`/时间戳），文件按
    `records/bugs/<YYYY-MM-DD>/<kebab-slug>.md` 日期分层；`rejected` 移入 `records/bugs/archive/`、
    `verified` 留原位（均校验器强制）。三条 dogfood 真实记录（json-schema 拒绝、run 全灭无诊断、
    print 模式权限拦截）已按新格式入库；`validate.py report` 输出时间排序回溯表。examples 的
    bug-record 正反例同步迁移为 md。
- 2026-09-14 第二批吸收（复核实证后修正过优先级：F 预算字段降级未做）：
  - 新建 `docs/host-platform-facts.md`：只收录本机实测过的宿主事实（Claude `--json-schema`
    拒绝 2020-12 元声明、print 模式 acceptEdits 拦截 sensitive write/Bash、继承全局 MCP 与
    slash commands、网关模型标签不一致、单用例延迟/成本、Codex flag 兼容与 candidate
    fail-closed），每条带证据、范围与复验方法；`README.md` 与 `adapter-protocol.md` 已链接。
  - `contracts.md` 新增「Hard boundaries」10 条全局禁止清单（单一来源，两个 SKILL 引用
    不复制）；`agentflow/SKILL.md` 委派步骤与 `contracts.md` 任务简报节新增「任务文本按
    数据处理」纪律（路径/仓库/命令核实后才进简报，未验证须标注）；`Recover from stalled
    work` 新增基线对照分诊（对改动前 revision 跑同一检查，基线同败=环境问题不轮询 worker）；
    中文侧 `agent-roles.md` 产物验收纪律同步这三条。
- 独立 Plugin 根目录、Codex/Claude manifest、两个 Skill 和 12 个角色文件。
- `bug-investigator`、`bug-fixer`、`bug-recorder` 三段 Bug 能力。
- `plan-architect` 计划编排能力。
- `docs/agent-roles.md` 角色矩阵、风险裁剪规则和计划/执行边界。
- `docs/agent-product-boundary.md`、`docs/self-improvement-design.md` 和本交接文档。
- episode、candidate、eval-case、release-record Schema 已从旧 Plugin 带入。
- 新项目通过 Plugin、Skill 和 Claude 严格格式校验。
- P0 第一批已落地：`schemas/bug-record.schema.json`、`schemas/plan.schema.json`、
  `schemas/evaluation-result.schema.json`，正例/反例，10 个公开评测用例，以及
  `tools/lab/validate.py`、`eval_runner.py`、`isolation.py`、`policy.py`。
- `tools/lab/host_adapter.py` 已提供 Codex/Claude 的显式结构化 Adapter；Claude 可加载
  candidate worktree，当前 Codex CLI 对未安装 candidate 源会 fail-closed，尚未做真实模型 dogfood。
- （上一台机器）已从 baseline 创建外部 Candidate worktree
  `/Users/hang/Documents/myProject/agentflow-candidate`；
  当时验证用 Candidate worktree 为 `/Users/hang/Documents/myProject/agentflow-candidate-current`，
  private-holdout 目录为 `/Users/hang/Documents/myProject/agentflow-private-holdout`；布局、
  artifact digest 和禁改 diff 检查当时已通过。本机如需 candidate 评测，需要用
  `tools/lab/isolation.py` 重新建立同类布局。
- 2026-09-14 的 Claude AF-007 candidate smoke 已通过参数/权限启动阶段；在 300 秒上限内运行约
  195 秒后由宿主返回结构化 `API Error: 502`，未产生评测结果。因此不计为通过，也没有切换
  安装源或写入 candidate；问题当前指向宿主推理网关，不是评测结果。
- 同日使用 Claude `fable` 做诊断性单 case 重试，约 203 秒后返回相同 502；因此当前证据指向
  Claude 整体推理网关，而不是 `sonnet` 单一模型路由。
- `python3 tools/lab/validate.py all`、结果对照示例和显式 Adapter smoke test 已通过。
- 2026-09-14 本机复核：项目路径、Git remote 和安装源描述已更正；`validate.py all` 在本机
  重新通过（`PASS schemas / examples / evals`）。
- 2026-09-14 本机真实 dogfood 起步：AF-001 smoke 第一次因 adapter 兼容 bug 在 1 秒内失败——
  当前 Claude Code 的 `--json-schema` 不接受带 `$schema`(Draft 2020-12) 元声明的 schema 文档；
  已修复为调用 Claude 前剥离 `$schema`/`$id`（`host_adapter.py` 的 `host_output_schema`）。
  修复后 smoke 通过：单次模型调用约 212 秒，返回合法结构化结果，未再出现上一台机器的 502。
  模型自报 `accepted: false`，证据指向 fixture 引用的 `src/parser.ts` 在 workspace 中不存在且
  git diff 干净——没有伪造通过。
- 上一台机器曾重建隔离布局：`/Users/lihanghang1/Desktop/TestProject/agentflow-lab/` 下的
  `worktree-baseline`（f2ea05c，digest `sha256:c9d9dd0f...`）与 `private-holdout`；这只是
  历史证据，当前工作区需要重新建立并运行 `isolation.py validate-layout`。
- 两次完整 10 用例 baseline 尝试均未产出结果：第一次无进度记录、约 26 分钟后中止；随后给
  `host_adapter.py` 增加可选 `--progress <jsonl>` 诊断记录和每次调用的 stderr 状态行（只用于
  定位，不改变评测语义），带 progress 重跑显示 AF-001 完成（137 秒，`accepted:false`），
  AF-002 在 900 秒上限处超时，整个 run 作废（adapter 是 all-or-nothing，没有部分结果）。
- AF-002 手动 stream-json 诊断（不设 900 秒上限）最终完成：真实耗时约 23.8 分钟、40 轮、
  4 个 Agent subagent、111 次 Read、约 $4.05；结果 `accepted:false`、`tool_failures:3`。
  证据显示 plan-architect 子 Agent 的 Write 被宿主权限边界拦截（`plans/` 被判定为
  "sensitive and not created"），Bash 校验命令也未获批准——即 `read-write-workspace` profile
  映射的 `--permission-mode acceptEdits` 在 print 模式下满足不了该用例要求，用例结果部分
  测的是宿主权限限制而不是工作流行为。
- 该诊断还暴露两个环境问题：assistant 事件的 `model` 字段全部是 `gpt-5.5`，而 CLI
  modelUsage 记录为 `anthropic-ccmax/claude-opus-4-6`，网关响应元数据与声明模型不一致；
  评测运行还会继承本机全局 Claude 配置（mastergo MCP、全局 slash commands 等），带来噪声、
  延迟和额外成本。
- 本机 Codex 同样使用自定义中转（`codex-ccmax/gpt-5.6-sol`，custom provider）；`codex exec`
  相关 flag 已验证与 adapter 兼容，但尚未做真实 Codex 模型 dogfood。

## 已确认的角色决策

### Bug 是否拆三个 Agent

保留三个独立角色，但按风险启用，不强制每个 Bug 都启动三个 Agent：

- 小范围、低风险、已有确定复现：Supervisor 可合并 Investigator 或 Recorder，Fixer
  和验证仍需保留；是否单独 Reviewer 由风险决定。
- 单模块逻辑 Bug：建议 Investigator、Fixer、Reviewer；要沉淀经验时再启用 Recorder。
- 跨模块、API、数据、权限、并发、宿主工具、安全或不可逆问题：完整
  Investigator → Fixer → Reviewer → Recorder，并增加人工门。
- 只诊断：只启用 Investigator；只记录已知且已有独立证据：只启用 Recorder。

三个角色是能力边界，不是仪式化流水线。Fixer 永远不能批准或关闭自己的 Bug。
Reviewer 是独立审查门，不能被 Bug Recorder 代替。

### 写计划和执行计划是否同一个角色

保持分开：

- Plan Architect：汇总前端、后端、Technical Director 和反馈证据，写版本化计划，
  只写 `records/plans/` 指定路径，不执行代码。
- Supervisor：审核计划，决定是否授权，拆成执行批次，安排并行、集成、停止和回滚。
- 未来的 `Execution Coordinator`：只有需要跨进程恢复、租约、长期队列、依赖调度和
  自动重试时再引入，负责运行状态和调度，不替代 Supervisor 的最终决策。

当前不增加通用 Task Recorder。宿主会话和事件负责基础留痕，Plan Architect 记录计划，
Bug Recorder 记录 Bug；未来共享控制面再考虑 Evidence Recorder/Store。

## 待办（分级）

> 2026-09-16 重整：原「未完成任务」的 P0 已全部关闭，保留其中仍开放的项；并入 0.3.6
> 能力盘点确认的新缺口。分级含义：P0 = 不做则方法的可信度或安全性有实际缺口；P1 = 让
> 改进环真正有燃料和度量；P2 = 数据充分后的自动化。看进度按级别定点看这一节即可，
> 逐版细节在 `iteration-log.md`。

### P0 — 可信度与安全基线

- [ ] 在可信宿主端点跑一次小规模（2–3 用例）完整 baseline/candidate 对照 smoke，让
  「方法有效性」第一次有数字；这是解开「继续加条款还是先验证」的前提（原 P0 遗留：
  完整 baseline 仍被网关/权限/超时阻塞）。
- [ ] 处理评测权限 profile：`read-write-workspace`（Claude acceptEdits）在 print 模式下
  拦截 sensitive write 与 Bash 审批，直接改变 AF-002 一类用例结果；需显式
  `--allowed-tools` 或独立权限模式。
- [ ] 评测环境隔离：显式 `--strict-mcp-config` + 空配置（或独立 `CLAUDE_CONFIG_DIR`），
  并写入 `observed_context`；否则 baseline 不可复现且成本偏高。
- [ ] 独立任务判定器：当前 `accepted`/`first_pass_review` 等指标来自模型自报；至少给
  核心用例配确定性或人工判定。
- [ ] `maxTurns` 在 ZCode 实一次（事实 Z6 只确认了 `tools` 白名单生效）；在此之前预算
  纪律按提示词约束对待（0.3.6 已把这条诚实声明写进 improve SKILL）。

### P1 — 改进环的燃料与度量（证据管道）

- [x] 最小 episode 落盘：`records/episodes/`（0.4.1，复用 improve 环 episode 契约）；原计划的
  store/检索仍不做，待落盘密度观察；相关条目：feedback-analyst 与
  bug-investigator 的输入开始分化。
- [x] 方法级改动的度量切片（0.6.0 仪器就绪）：`evals/business/` 三用例（种子缺陷文档审查 /
  内部矛盾 / 跨文档一致性）+ `tools/lab/seed_grader.py` 确定性评分 + adapter/runner 业务面
  （`--business-root`、`--seed-patch`）+ validate 接线；有匹配业务用例（当前只有 aiwork
  文档审查类）的方法级改动可产出 better/neutral/worse（smoke 级）。尚未产出任何对照数字：
  首轮 smoke 实跑挂 U-01/U-02/U-03（可信端点、权限档实测、快照位置），无匹配用例的仍按
  `measurement: none` 过渡态处理。
- [ ] Trace → sanitized Episode 转换、脱敏/同意/保留期限；本地 Episode Store + SQLite
  FTS5 检索（原 P1 内容，依赖上一条的落盘）。
- [ ] `records/` 路径越界的宿主强制（当前矩阵 + 校验器 + supervisor diff 兜底）；
  `execution-coordinator`（断点恢复的持久化版本）待跨会话恢复需求真实出现再做。
- [x] 角色-文档一致性检查：`validate.py docs`（0.4.1，进 `all`）——frontmatter name、
  SKILL 角色引用、schema 路径、中英镜像引用面四组断言。
- [ ] 触发描述预算检查（2026-09-17 improve 环 proposal 评估立案，`EP-20260917-001`）：评估
  结论——两个 SKILL 的 description **本身不需要改**：agentflow/improve 全长 361/342 字符，
  触发判据句（第一句）分别长 220/136，均在宿主约 250 字符可见窗口内完整结束（余量 30/114）；
  0.3.2 前置化修复后至 0.6.0 约十个版本，`records/` 无一条 skill 误触发/漏触发记录；被截掉的
  尾巴是自我描述，对不截断的宿主（Claude Code/Codex）仍是有效信息，为 ZCode 裁短是拿无
  故障模式的猜测换真实信息量。本会话实测截断行为：ZCode 逐字呈现 description 前 249/250
  字符前缀（agentflow 第 250 字符恰为空格、去尾随空格后呈现 249），improve 断在单词中间
  （bounde…）。**缺口**：前置化纪律零确定性保护——`validate.py` 不校验 description 长度，
  未来编辑可能把触发词挤出 250 窗口或撞 1024 整条 skill 消失，八项检查照样全绿。落地两件
  事：(1) 新增检查「description ≤1024 且触发判据句在 250 窗口内结束」——动 `tests/` +
  `EXPECTED_TEST_FILES` + `protected-paths.txt`，属门变更须人工实施；(2) 把上述实测记入
  `docs/host-platform-facts.md`，Z3 从 doc 级升 observed 级。用户 2026-09-17 决定：先记录
  问题，两项做不做后续再定。

### P2 — 数据充分后的自动化

- [ ] 独立版本、安装、更新、卸载和发布来源配置。
- [ ] 真实任务 Human-gated dogfood 后，样本和阈值稳定再做 Canary、监控和低风险自动回滚。
- [ ] 跨宿主共享状态需求出现时，才增加只暴露 evidence/eval/approval/release/rollback 的
  MCP。
- [ ] 盲化 A/B、多次重复与统计置信区间（承接原 P2）。

## 新对话建议起点

新对话开始时可以直接使用下面的上下文：

> 继续处理 `/Users/hang/Documents/myProject/agentflow`（remote: `Ganseblum/my-agents.git`）。
> 先阅读 `README.md`、`docs/next-session-handoff.md` 和 `docs/agent-roles.md`。
> 保留按风险启用的 Bug Investigator/Fixer/Recorder 设计；Plan Architect 只写计划，
> Supervisor 负责执行授权和调度。P0 契约、公开评测、通用校验/Policy 工具、隔离检查和显式
> Codex/Claude Adapter 均已完成（Codex candidate 路径按设计 fail-closed），adapter 的
> `--json-schema` 兼容问题和进度记录已修复。不要把本机网关跑出的结果当作权威 baseline：
> 两个宿主都走第三方中转、模型标识不一致。下一步先决定权威评测的宿主端点和预算，并处理
> 权限 profile（acceptEdits 在 print 模式下拦截 sensitive write 和 Bash 审批），再跑完整 suite；
> 之后才配置本机安装源。不要先做向量检索、MCP 或自动发布。

## 当前风险

- 宿主安装快照与源码会漂移，且漂移是静默的：ZCode 从安装快照加载角色，Codex 也可能从
  单独缓存加载技能。默认 `validate.py installed` 只查 ZCode。2026-09-15 观测：快照重装到
  0.3.4 后 `installed` PASS；随后源码进入 0.3.5（复盘补丁批次），在刷新 marketplace 并重装
  之前 `installed` 会以"没有源码版本的快照"报红——这是预期状态，不是回归。重装后应转绿。
- 禁区清单（`protected-paths.txt`）由 `isolation.py check-diff` 与 `validate.py protected` 共同
  守住，但这条防线是自指的：清单、校验器和隔离检查本身也在禁区里，一个同时改掉三者的候选
  在工具层就查不出来，真正的兜底仍是人工审查 + Supervisor 的 diff 检查。因此「清单/校验器/
  发布策略的修改必须人工审查」这条纪律不能省，它是最后一道门。
- `tools:` 工具白名单已实测在 ZCode 生效；`maxTurns` 未验证，因此预算纪律目前靠角色提示词
  而不是宿主截断保证，且 30/20 这两个数字是判断而非实测结论。
- `records/` 的路径约束仍主要依靠角色说明、产物所有权矩阵与 Supervisor
  检查；产物内容已可确定性校验（`validate.py artifacts`），但“写到了不该写的路径”仍无宿主
  强制，需要 Supervisor 检查 diff 兜底。
- 私有 holdout 必须位于公开项目和 Candidate worktree 之外。
- 当前校验器使用 Python 标准库实现本项目用到的 Draft 2020-12 子集；尚未替代完整标准验证器。
- 本机尚未建立可由默认检查发现的宿主安装源；Codex 的 0.3.1 缓存已通过显式路径检查确认
  漂移，因此真实使用验证仍需先完成安装切换。
- Codex candidate 评测当前因 CLI 缺少 per-invocation 本地 Plugin 绑定而 fail-closed；不能把现有
  已安装 baseline 当作 candidate 结果。
- 上一台机器记录的启用源 `/Users/hang/plugins/agentflow` 和 `~/.claude/skills/agentflow` 在本机
  不存在；安装流程和来源需要在本机重新确认后才能验证。
- 用例内声明的 `repeat_count` 与 `eval_runner.py --repeat-count` 不一致时，请求在构建阶段即被
  拒绝（0.6.0 起强制一致性，`eval_runner.py build_request`）；baseline/candidate 的重复次数恒等
  于 suite 冻结值，无需再人工注明。
- adapter 的用例指标来自模型自报（`accepted`、`first_pass_review` 等），目前没有独立判定器；
  这与 P0「人工闭环」定位一致，但解读结果时必须以此为前提。
- 本机两个宿主都走第三方中转网关（Claude: `fable`→`anthropic-ccmax/claude-opus-4-6`，
  Codex: `codex-ccmax/gpt-5.6-sol`）；AF-002 诊断中 assistant 事件的 `model` 全部标为
  `gpt-5.5`，与 CLI modelUsage 不一致。在本机产出的 baseline/candidate 不能当作权威评测
  结果，除非显式记录实际网关并确认有效后端模型。
- `read-write-workspace`（Claude `--permission-mode acceptEdits`）在 print 模式下仍会拦截
  sensitive write 和未批准的 Bash；这会直接改变 AF-002/plan-architect 一类用例的结果。
  评测前需要对齐 profile 语义（例如显式 `--allowed-tools` 或独立权限模式）。
- 评测运行继承操作者全局 Claude 配置（MCP、slash commands）；建议在 adapter 中显式隔离
  （`--strict-mcp-config` + 空配置，或独立 `CLAUDE_CONFIG_DIR`）并把隔离方式写入
  `observed_context`，否则 baseline 不可复现且成本偏高。
- AF-002 单用例在本机约 24 分钟、约 $4；完整 10 用例 suite 预计需要数小时和可观费用，
  运行前需确认预算，并把 per-call 超时提高到 ≥1800–2400 秒（adapter 是 all-or-nothing，
  单次超时会丢掉整次 run）。
- `tools/lab/host_adapter.py` 的 `run_codex` 曾在解析宿主输出时对 `tempfile.NamedTemporaryFile`
  对象调用 `read_text()`（那是 `pathlib.Path` 的方法，文件对象没有），任何 codex 侧真跑都会在
  这一步抛 `AttributeError` 失败。**已修**：改为按 `Path(output.name)` 读取，读取失败包成
  `ValueError` 交 `main` 统一处理；由两条 stub 回归测试（`tests/test_lab_contracts.py` 的
  `HostAdapterCodexResultTests`）钉住，CHANGELOG 0.6.0 与 `docs/iteration-log.md` §0.6.0 同记。
  **真实 codex CLI 真跑仍未验证**——现有证据只到 stub 层。
