# Agentflow 项目深度评审报告

> 评审日期：2026-10-12 · 评审者：WorkBuddy（宿主原生 agent）
> 评审范围：v0.10.0，全仓逐文件通读（14 角色 + 2 skill + 9 工具 + 2 测试 + 9 schema + 18 评测 + 45 issue + 29 episode + 6 plan + 14 改进件 + 3 发布 + 7 评审 + 2 批次 + 12 归档 + 14 文档）
> 方法：6 路并行只读子代理逐文件精读 + 门实跑（validate.py all / unittest）+ 竞品横向调研（16 次检索 + 12 次 GitHub API）
> 注：本报告是交付件，**未登记进 `index.md`、未触碰 `protected-paths.txt`**，故意排除在受治理文档面之外；可任意移动/删除。

---

## 一、六维评分总览

| 维度 | 评分 | 一句话结论 |
| --- | --- | --- |
| 架构设计 | **7/10** | 五面分离 + 失败关闭很扎实，但门控多为提示词级、policy.py 与环文档脱节、schema 重复×4 |
| 目录结构 | **8/10** | 映射清晰、manifest 一致；个别批次链不完整、mock/examples 双份维护 |
| 文档内容 | **7.5/10** | `host-platform-facts` 证据强度全仓最高；但冗余、死链、未修自相矛盾数处 |
| 代码质量 | **7.5/10** | 自研门工具高于平均；真实 bug 十余处，最严重的是手写 schema 子集「静默失明」 |
| Agent/Skill 质量 | **7/10** | 角色分类严谨；但 recorder 漏列必填字段、判断词定义冲突、模板断号导致 linter 必红 |
| 整体效果与能力 | **6.5/10** | 愿景连贯、可审计性强于 BMAD/superpowers；但核心差异点（确定性测量 + 受治理发布）**尚未真正落地** |

**综合：7.1/10**。一个"方法论严谨度 > 工程落地度"的项目——设计哲学领先，执行验证滞后。

---

## 二、架构设计（7/10）

### 亮点
- **五面分离**（插件/实验室/记录/文档/发布链）职责清晰，且每面有独立消费者与纪律（project-structure.md）。
- **失败关闭（fail-closed）** 贯穿：`measurement=none` 不自动记 0 分、未知匹配策略一律退回、非编译产物即编译错误。
- **受保护门清单单点声明**（`protected-paths.txt`）+ `validate.py protected` 反向校验，防清单被悄悄删减。
- **记录即编译**：issue/episode/plan 写完即过 schema 校验，FAIL 即编译错误——比大多数"文档即代码"实践更硬。

### 硬伤
1. **门的强制力主要是提示词级，不是机械级**。`README:38` 自承"宿主不会对 `Write` 工具强制任意路径约束"；8 个持 `Write` 角色的"产物归属矩阵"只是提示词，真实强制靠事后 `check-write-scope.sh` 对照。即：**预防靠剥夺工具，路径约束靠事后审计**。`agents/bug-fixer.md:20` 禁 git 发布只是自述，零机制。
2. **policy.py 是孤儿门**。`skills/improve/SKILL.md` 与 `evidence-and-release.md` 全文未提 `policy.py`；而实跑显示它对 0.8.6 判 `evaluation_result: invalid / decision: reject`（9 条理由），releases/0.8.6.json 却记 `better/promote`——**确定性门与发布裁决完全相反**（subagent C 证据 7）。
3. **schema 结果集形状四份拷贝**：`release-record.schema.json:357-487` 的 `$defs/resultSet` 与 `evaluation-result.schema.json` 是同一 runner 结果的"两个版本"，`comparison.schema.json` 又存第 3、4 份，零共享。指标增减须改四处。
4. **validate.py 单体 + 三处重复登记**：`all`/`单目标`/`choices` 三处分发表（:3196-3218），新增检查须同步三处；且 import 即 `sys.path.insert`（:24），副作用外泄给所有导入方。
5. **"全绿"声明被实跑反驳**：`validate.py all` 在本环境 `FAIL tests (2 errors)`。已确认 2 错误源自 WorkBuddy 的 Python shim（`sitecustomize.py` 的 `_brokered_path_mkdir` 不 honor `exist_ok=True`），非仓库 bug；但这意味着仓库反复声称的「全绿」**无法在本机独立复现**。诚信上应改为"在干净宿主环境全绿"，而非绝对化。

---

## 三、目录结构（8/10）

- 映射近乎完美：`project-structure.md` 给了一份可信的目录树、五个面、安装链路、约定速查。
- manifest 五份名字/版本由 `validate.py manifests` 强制一致（plugin.json/marketplace.json/.zcode/.claude/.codex）。
- **问题**：
  - `features/feature-2026-10-09-结构改造` 仅 README + plan×5，**无 proposal/spec/design/reviews、无轻量声明、无 linter 留档**——批次链不完整（subagent F 证据 12）。
  - `mock/plans/PLAN-DEMO-SHARE-001.md` 与 `examples/plans/PLAN-DEMO-SHARE-001.md` **逐字节相同**：同一正例双份维护，任一处漂移即两门判定分歧（subagent E 证据 8）。
  - 整个 `features/` 只有 2 个批次，文档交付链的设计尚未规模化验证。

---

## 四、文档内容（7.5/10）

- **最高证据强度**：`docs/host-platform-facts.md` 每行 "Observed + 逐字报错 + 时间戳 + 复验命令"，是全仓最经得起审计的文档，值得作为样板。
- **冗余与漂移**：
  - `iteration-log.md` 基本是 `CHANGELOG.md` 标题改写，且缺 0.7.0/0.7.1 专节、:33 引死路径（subagent F 证据 11）。
  - `agent-roles.md` 与角色文件 / SKILL 重述同一内容。
  - 活跃面 102 个相对链接 **0 断链**（机器门有效，赞），但**内联死引用 21 处**（CHANGELOG 10 + iteration-log 10 + 其他），含 `docs/audit-2026-09-18-followups.md` 这类已迁移路径（subagent F 证据）。
- **已立案却未修的自相矛盾**：
  - `method-spec.md:52` 称"12 条硬边界"，实际 contracts.md 编号 1–14、SKILL.md:61 写"硬边界 14"（REV-20261010-001 F3 已立案未修）。
  - `proposal.md:37` 称 U-01"live 对照进行中"，同文件:92 称"无可信 claude 族端点……无法执行"，而 `PLAN-LOOP-SMOKE-001.md:53` 与 host-platform-facts C12 已逐字记录"U-01 已关闭（2026-10-10 3/3 通过）"（已立案未修）。
- **记录面的系统性脱节**：台账 `occurrences`、episode `evidence_ref`、计划"未决项"三处尤为突出（详见第六节）。

---

## 五、代码质量（7.5/10）

> 全仓无 TODO/FIXME、无裸 `except:`/`except Exception`，异常全 typed 且转化或重抛——基础素养显著高于一般自研工具。

### 已确认的真实 bug / 风险（节选，均有 `文件:行号`）
1. `validate.py:2659` `except OSError`：非 UTF-8 的受保护清单 → `UnicodeDecodeError`(ValueError) 逃逸成 traceback（同文件 :177 已抓 ValueError，唯此漏）。
2. `validate.py:375-381` 漏捕 `TypeError`：JSON Pointer 命中字符串节点（如 `#/title/x`）直接崩溃。
3. `isolation.py:124` `f"{base}^{{commit}}"`：base 以 `-` 开头（如 `--help`）时被 git 当选项 → 静默 `PASS`（fail-open 参数注入，无 shell 注入风险）。
4. `eval_runner.py:405-412` adapter 子进程**无 timeout**：挂起的 adapter 永久挂死门。
5. `build_runtime.py:108-112` `assert_safe_destination` 只拒 ROOT/packaging/源树，**不拒包含仓库的目录**：`--destination ..` 会 `rmtree` 掉仓库根全部内容——破坏性默认值。
6. `check-write-scope.sh:44` 无 `-z`：git 对非 ASCII 路径默认 C-quote（已实测复现 `features/feature-2026-10-09-\345\...`），中文 scope 永配 → **误 FAIL**，重演 ISS-2026-041 同根因；且进程替换吞掉 git 退出码，失败时 "OK exit 0"（fail-open）。
7. **手写 schema 子集静默失明**：`validate_schemas`(:1437) 不限定词汇表，用了未实现关键字的 schema 被静默不校验（缺 `exclusiveMinimum/multipleOf/patternProperties/unevaluatedProperties`），当前 schema 恰在子集内故潜伏。
8. `host_adapter.py:167` `snapshot_diff_digest` 未传 `--no-renames/--no-textconv`，摘要依赖操作者 git config，跨机器不确定。
9. `seed_grader.py:388-390` main 调 `grade_case` 不传 `target_docs` → off_target 与每文档 unmatched 上限在文档化路径上全部失效。

### 测试覆盖真相
27 类 164 例密度高（policy 决策矩阵、seed_grader 8 组黄金用例含 fail-closed、check_diff 前缀阻断、PATH stub 掉 codex/claude 均有）。**但**：题设点名的三关键路径其实有实质测试；真正空白在 `validate_mock_fixtures`/`validate_installed`/`validate_doc_chain` 包装 0 引用、`run_adapter` 仅测前置拒绝、CLI 层 0、record_store 无 FTS5 缺失/非 UTF-8 用例。

---

## 六、Agent / Skill 质量（7/10）

### 角色分类（14 角）
- 严谨面：六个只读角色 `tools` 白名单完全同构（R/G/G + 禁 Bash/Write/Edit），`disallowedTools` 与正文互相印证；三只读角色不合并（investigator/analyst/TD/reviewer 输入契约异质）有文档依据（roles.md:33）。
- **问题**：
  - `agents/bug-recorder.md:21` frontmatter 清单**漏列** schema 必填字段（`verified` 需 reviewer/review_decision/regression_status/closure_criteria；`rejected` 需 rejection_reason；正文还需 `## 变更记录` 节）。照此产出必被 schema 拒——而实证记录（ISS-2026-043 等）确实带这些字段，说明契约真实存在、recorder 指令面却漏列。
  - `agents/evaluator.md:3` description 称"**compares** with frozen baseline **on predeclared cases**"，正文却是不跑命令、只读 runner 产出的"对照结果记录"。路由者会被描述误导。
  - `agents/bug-fixer.md:26` 与 `candidate-engineer.md:39-41` partial 规则复制粘贴两遍，稀释"绝不报完成"的单一权威。
  - `roles.md:14/91` 裸用"专家"一词无定义；test-executor 的 Edit 禁用语义未进入路由表。

### Skill（agentflow）
- 十步工作流咬合紧密，但**不自含**：新 feature 的接入/访谈散在"文档交付链"节，第 1 步又依赖它。
- **判断词定义冲突**：`小改动`(:70)"不需架构门" vs `risky`(:71)"满足任一即触发架构门"——单文件改持久化默认值可同时满足，且 :68"按此顺序应用"**未裁决优先级**（subagent B 证据 12）。"小改动"定义域实际只覆盖 bug fix，却未声明非修复类改动永不可判"小"。
- **模板断号导致 linter 必红**：`design/be/backend.md:27-28` 列 `## 2` 后直接 `## 4`，缺 §3；`spec/be/backend.md:5` 首个下级即 `### 1.4` 无 1.1–1.3；`design/fe/frontend.md` 无 linter 要求的 ≥2 张线框槽位——**照模板填的链必挂 C7/C8**（subagent B 证据 3、5）。
- **document-chain.md 两张"可选层"清单**(:51-53 vs templates/README.md:21-26)不一致、无互引，必然漂移。

### Skill（improve）
- 改进环门控强度 = "提示词自觉"：SKILL.md:24 自认"除非宿主确实强制分离的工具白名单与工作区，否则角色分离只是流程性的"。
- evaluator 无 Bash，实跑由 Supervisor 代劳，而 Supervisor 同时是候选写入者——**角色集中风险**。
- 见第二节 policy.py 孤儿门与"确定性晋升链在真实循环中被绕开"。

---

## 七、整体效果与能力（6.5/10）

### 记录面是"活的"还是"仪式的"？
- 45 份 issue：仅 **15 份**走完 `open→fixed-pending-review→verified` 全流程（001-009、026-029、043-045，closure_criteria 带可执行命令）；**16 份** open 后未动（010-025，单次外部评审 findings，无 updated_at）；**0 份** rejected，且 `归档/` 目录不存在（归档规则空转）。
- 29 个 episode：`review_roundtrips` 16 个有实质内容（EP-20260921-001 六轮逐条 finding+resolution 可审计），**13 个为 `[]`**；`evidence_ref` 大量是叙述句/`/tmp` 易失路径/个人绝对路径；**最新 7 个 EP（10-08~10-10）的 signals.evidence_ref 大面积缺席**（5/5、4/4）——证据密度随时间递减。
- 计划看板：PLAN-LOOP-SMOKE-001 与 git 高度吻合（赞）；但 PLAN-PRODUCT-001 概览"4 未开始"与任务表 5 个 ☐ 算术不符（6+1+4+2=13≠14），U-02"未关闭"而 T05 已 ☑ 且 commit 在 origin/main。

### 核心差异点尚未兑现
- **确定性测量从未真正发生**：0.8.4/0.8.5/0.8.6 发布记录 `measurement.status` 全为 `none`；业务切片 BT-001/002/003 设计严谨却**零实测**；全部 `repeat_count=1`，无方差/CI。
- **确定性晋升链在真实循环被绕开**：0.8.6 的 candidate 的 primary_metrics 不在 `KNOWN_METRICS`、protected_slices 与实际 case slice 不重合，policy.py 判 invalid；release 却记 better/promote（subagent C 证据 7）。
- 结论：作为"受治理自我改进"的范本，Agentflow **设计比执行成熟约一个版本**。

---

## 八、横向对比（竞品）

| 项目 | 形态 | 活跃度 | 与 Agentflow 的核心差异 | 强于 A | 弱于 A |
| --- | --- | --- | --- | --- | --- |
| **superpowers** | CC 插件 | 297.8k★ | 技能框架，靠资深工程师方法论 | 星标生态、触发工程 | 无确定性门、无自迭代环 |
| **BMAD-METHOD** | 安装器 | 54.0k★ | 全流程文档仪式 | 社区/跨工具 | 仪式重、无自迭代 |
| **Codex AGENTS.md** | 开放约定 | 60k+ 项目 | 单一规范 | 跨工具事实标准 | 无角色/流程/门 |
| **Claude Code subagents** | 平台 | 官方 | 提供载体 | 原生上下文隔离+hooks | 不提供方法论 |
| **CrewAI/LangGraph** | 库 | 59k/43k★ | 代码编排 | 生产状态/HITL | 非插件形态 |
| **OpenHands** | 平台 | 90k★ | 沙箱执行 | 沙箱/基准 | 重、难嵌入 |
| **spec-kit** | CLI | 140.8k★ | 规范驱动 | GitHub 官方 | 无角色团队 |
| **ai-data-agents** | 插件 | 较新 | Supervisor+15 agents | 数据域 MCP | 仅数据域 |

**三条技术路线**：(a) 提示词/角色契约驱动（A 在此，天花板=模型+寄生 harness）；(b) 代码编排框架（生产态，但被官方 SDK 收编、最脆弱）；(c) 单一 agent+强规范（"默认选项"的胜利）。

**自我改进方向研究现状**：已成独立学术领域（survey 2507.21046；Voyager 技能库；Darwin Gödel Agent 系 SWE-bench 20%→50%、SICA 17%→53%；ADAS/AFlow 把拓扑设计形式化为搜索）。**工业界集中在技能/记忆层**（Hermes、OpenAI Evals、RFT）。**"确定性门 + 受治理发布"的同类设计：未找到完全对应的开源工作流框架**——这是 Agentflow 的真实空白创新点，但缺工程验证。

**定位结论：约 70% 重复造轮子（角色卡 + 技能生态拥挤，面对 297k/140k 头部），30% 真实空白（`确定性门 + 受治理发布`）。** 对外叙事应押注"确定性门的严格程度"，而非角色数量。

---

## 九、纵向对比（与 WorkBuddy 自身）

| 维度 | Agentflow | WorkBuddy（本宿主） |
| --- | --- | --- |
| 角色/技能载体 | 14 角色文件 + 2 skill，宿主从**安装快照**加载 | 用户级/项目级 skills + experts + connectors，同样快照加载 |
| 强制力来源 | **提示词为主**，路径约束靠事后审计 | **宿主沙箱真实拦截**（本会话的 path broker 即实例）+ 权限档 |
| 产物校验 | schema + validate.py 编译期 | 无编译期 skill 产物校验（LLM 验收为主） |
| 失败关闭 | 设计哲学贯穿 | 工程强制（沙箱/权限/只读） |
| 自迭代 | 完整受治理改进环（理想态） | 记忆层（云/本地/工作区）+ 自动化，无同行评审门 |

**最有讽刺意味的证据**：Agentflow 反复主张"提示词不变量 + 事后审计"足够，而我（WorkBuddy）运行它的 own tests 时，恰恰是**宿主的 Python path broker** 让 2 个用例假红——这正面印证了"宿主真实强制 > 提示词声明"的论断。Agentflow 的架构若想兑现其确定性承诺，最该补的不是更多角色，而是**把路径/权限约束下沉为宿主可强制的机制**（例如 Codex/Claude 的 hooks、WorkBuddy 式的沙箱白名单），而非停留在硬边界 14 的事后 diff。

---

## 十、最该修的 10 件事（按优先级）

1. **补 policy.py 与环文档的接线**（SKILL.md/evidence-and-release.md 显式引用并消费其裁决），消除 0.8.6 的 invalid/reject ↔ better/promote 矛盾。
2. **修 build_runtime.py:108 的 `..` rmtree 漏洞**（破坏性默认值）。
3. **修 isolation.py:124 的 `-` 开头 base 静默 PASS**（fail-open 注入）。
4. **补 check-write-scope.sh 的 `-z` + 退出码回传**，根除中文路径误 FAIL（ISS-2026-041 修复不完整）。
5. **收敛 resultSet 四份拷贝**为单一 `$defs` 共享。
6. **修 validator 的异常逃逸**（validate.py:2659/:375、isolation:115/:138）。
7. **给 bug-recorder 补列 schema 必填字段**，消除"照指令产出必被拒"。
8. **修模板断号**（§3 缺失、1.1–1.3 缺失）让 linter 不再必红；统一 document-chain 的两张可选层清单。
9. **兑现"全绿"诚信**：改绝对化表述为"在干净宿主环境全绿"，并实际跑一遍无 broker 的 CI。
10. **把 measurement 从 none 推进到 baseline/candidate 首对照**，否则"受治理改进"始终停留在宣言。

---

## 十一、最终裁决

Agentflow 是一个**设计哲学明显领先于工程落地的受治理多 agent 工作流框架**。它的失败关闭、五面分离、记录即编译、受保护门清单等设计，在开源角色卡赛道（BMAD/superpowers）里确实更硬、更可审计。但它有两个结构性软肋：

1. **确定性靠声明多于靠强制**——核心路径约束在提示词层，真实强制寄望于宿主 hooks（尚未落地）。
2. **核心差异点（确定性测量 + 受治理发布）尚未被自己的门真正验收过**——release 记录与 policy.py 互相打脸，measurement 全 none。

它不像 CrewAI/LangGraph（那是另一条赛道），也不像 OpenHands（那是平台）。它在拥挤的"角色卡"赛道里占了 70% 的重叠，仅以 30% 的真实空白创新（确定性受治理自迭代）立身。**这一空白成立的前提，是它先把"门的强制力"从提示词下沉到宿主机制、并让自己通过自己的门。** 否则，它会是又一份设计精美但验证缺席的方法论——而它自己最反对的，正是这件事。

---

## 十二、勘误（复核后修正，2026-10-12）

> 本评审在后续逐文件二次复核（见行动件 `AGENTFLOW-OPTIMIZATION-2026-10-12.md` 〇章）中发现 **4 处路径/事实错误**，均因原评审未核对真实文件路径即下结论所致。此处集中勘误，**不掩饰、不删除原结论**，原报告正文保留不改；完整修正与改动见行动件。

| # | 原报告说法 | 复核后事实 | 对原结论的影响 |
|---|---|---|---|
| E1 | `resultSet`「四份拷贝」（二/3、十/5） | `grep` 实测 `resultSet` 仅定义 1 次（`skills/improve/references/release-record.schema.json:358`），`:26/:29` 以 `$ref` 复用（**良好做法**）；`schemas/` 下的 `evaluation-result`/`comparison` 是独立顶层 schema，其 `summary` 形状与 `resultSet` 同构但未用 `$ref` | 撤回「四份拷贝」批评；改为「8 指标 summary 形状跨文件重复，应抽共享 `$defs`」（已落实为 T2.12） |
| E2 | `isolation.py:124` 以 `-` 开头 base 会「静默 PASS / fail-open」（二/2、五/3） | 实测 `git rev-parse --verify -x^{commit}` 与 `--help^{commit}` 均 exit=128 → 抛 RuntimeError → `check_diff` 返回 1（**fail-closed**） | 撤回「存在活动漏洞」措辞；保留为纵深加固项 T0.3 |
| E3 | `docs/method-spec.md:52`「12 条硬边界」（四、十/7） | 该路径**不存在**；真实文件为 `docs/product/spec/method-spec.md:52` 与 `:194`；「12 条」内容属实，仅路径写错 | 修正路径引用；「12 条→14 条」修订已落实为 T1.7 |
| E4 | `templates/design/be/backend.md` 等「断号导致 linter 必红」（六、十/8） | 仓库根 `templates/**` Glob 返回**无文件**；真实模板在 `skills/agentflow/templates/`（feature/hub/issue/releases + index-template.md），原文件不存在 | 撤回原说法；改为「先定位真实模板逐项核查」，真实 `skills/agentflow/templates/feature/design/be/backend.md` 缺 §3 属实，已补占位 §3（T2.10） |

**诚实说明**：以上 4 处均非 Agentflow 代码缺陷，而是评审自身未逐文件核对路径与事实即下结论，恰好印证了本报告「核心差异点尚未被自己的门真正验收」的元批评——**评审本身也犯了"验证缺席"的同源错误**。后续已通过 T0–T3 共 16 项改动收敛问题（含把 `policy.py` 接入改进环、补诚实性披露、结构去重），详见 `AGENTFLOW-OPTIMIZATION-2026-10-12.md`。
