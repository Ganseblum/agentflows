# 变更日志

## 待发布 — 2026-10-10

> 本节记录两批尚未定版本号的改动；五份 manifest 的版本 bump 与本节改号随下次发布批执行。
> `measurement: none`（方法级改动，无仪器化业务任务）。

- **全仓中文本地化（用户指示「能改的都改」，推送于 `4c767eb`）**：71 个文件一次性汉化——
  14 个角色文件与两个 SKILL、契约 references、README / AGENTS / docs / tools / packaging /
  examples 文档面、受保护面（evaluator 与 release-governor 角色、improve 规则书、`schemas/` 与
  `evals/` 下的 README 与公开用例）、三个脚本的注释与消息、CHANGELOG 全文。frontmatter 宿主
  规范字段、标识符、枚举、路径与代码块逐字保留；`validate.py all` 全绿、`installed` PASS、
  runtime 重建并与 cache 逐字节同步。受保护改动的授权依据与回溯登记见
  `plans/PENDING-DECISIONS.md`。
- **youc-workflow-ai 模式吸收 + 巡检收尾（用户指示「直接开始改」）**：实例化
  `releases/todo.md` 与 `releases/pending-test.md`，新建 `plans/PENDING-DECISIONS.md` 单点拍板
  清单（`artifacts` 门随批放行三个声明工作文件 + 测试钉子）；`AGENTS.md` 增「表达与沉淀
  纪律」；SKILL 增「首次接入（Init）」；`index.md` 与 `docs/project-structure.md` 双轨化并新增
  结构地图；`check-write-scope.sh` 的「.」全树范围缺陷修复（ISS-2026-041，含双回归用例）；
  `PLAN-PRODUCT-001` 看板按实况回写；宿主事实登记端点复测（U-01 解除）。
- **端点与第一次改善闭环**：`claude --print` 一词探测 3/3 通过（22–24s 返回、end_turn 干净）
  后，按 `PLAN-LOOP-SMOKE-001` 以 AF-001 × 冻结重复数 3 完成试水实跑（3 轮共 21.7 分钟；
  时延 540/322/438s，`accepted=false`×3，`tool_failures` 8/0/6，denials 0；成本未落盘为已知
  观测缺口）；完整对照的授权待用户裁决；结果回写 `releases/pending-test.md`。

## 0.10.0 — 2026-10-09

全库清理与防漂移清查，用户指令（"要一步到位 去除之前不合理的地方，保证后续
都是最新 无残留和过时干扰"）：结构大改造遗留的残留被清除，机器门现在能检测两类
残留。方法级改动；`measurement: none`。

- **残留修复**：三处失效相对链接重新改指（两处在 `iteration-log`，一处在
  `system-guide`；生成的 runtime 链接属已声明限制项）；当前态文档中的过期路径提及
  已收敛（`system-guide` §6 流程图、`index.md` 迁移清单、`spec-fact-check-design`、
  `plans/` 措辞）；`README.md`、`system-guide` 与 `docs/product/*` 中 "nine checks"
  的过期计数被移除或改指运行本身，枚举检查集处补上 `doc_chain`；
  `iteration-log` 补上缺失的 0.9.0 小节（标注 补记）、修复一处畸形总览行，
  以及 0.8.4–0.10.0 总览行。
- **评审遗留收口**：N4（条款措辞现在精确点名 linter 豁免的
  括号配对形态）、N6（模板 README 恢复写前自检，点名两种形态）、
  N7 经核实已在 0.9.0 重写中解决。
- **本地残留删除**：两份会话 HTML 导出与一次性的 FTS5 索引。
- **门变更（用户授权）**：`validate.py docs` 新增对现行文档面的两项扫描——失效相对链接、
  退役路径表述。围栏/行内代码属引用，mermaid 图是内容、照常扫描；
  `_archive/`、生成的 runtime 树、`CHANGELOG.md`、`docs/iteration-log.md` 与迁移执行
  记录目录属已声明豁免项。
  `tests/test_lab_contracts.py` 钉住判别用 fixture。
- **验证**：修复前的树 + 新检查器 = 9 项发现（红，逐字归档）；修复后的树转绿；
  一次性副本上的故障注入观察到 FAIL → restore → PASS；`validate.py all`
  10×PASS；`doc_chain.py --self-test` 38/38；unittest 159 OK；`isolation.py check-diff`
  `blocked=[]`，两张已授权门文件在一次性副本中复原；`validate.py
  installed` 对刚安装的 0.10.0 快照转绿（宿主客户端中的 marketplace 刷新与
  重装仍需用户侧完成）。独立评审轮次（第 1 轮
  `changes_requested`——七项发现修复；第 2 轮 `changes_requested`——两项文本级
  条目按记录在案的维护者先例修复并发布）记录于本批 `reviews/` 与
  `EP-20261009-002`。注：五份 manifest 的中文描述本地化
  （观察于 2026-10-09 23:24，本批之外完成）被排除在此发布提交之外，并遵循用户指示
  在后续 chore 提交中提交。
- **治理通道**：直接的用户指令改动（与 0.9.0 同一通道）；
  受保护路径的编辑在用户的明确批准下完成，并记录在本批 episode 中供回溯评审；
  无 candidate/evaluation/comparison 集；不描述为已验证的
  改进。
- **measurement: none**（方法级改动，无仪器化业务任务）。

## 0.9.0 — 2026-10-09

仓库结构生成变更，用户指令（"不要 records 了…全部改成类似
youc-workflow-ai 的结构" + "全部完成，然后把没用、过期的都删除"）：
`records/` 树退役，记录面迁至根级活区，模板变为真实文件，
文档链、角色与检查全部改指。结构与方法级改动；
`measurement: none`。

- **结构**：`index.md`（单一索引：场景 → 条目、维护纪律、迁移清单）；活区——
  `issues/`（缺陷与条目同属一个 `ISS-<YYYY>-<NNN>` 家族；复发台账；
  仅存拒收记录的 `归档/`）、`episodes/`、`plans/`、`improvements/`
  （候选/评测/对照）、`releases/`、`reviews/`；`_archive/` 冻结桶按
  三级冻结规则（冻结而非删除；冻结原件保留历史引用——
  校验器中的单点豁免）；`docs/` 收窄为 design / guide / fact 文档；
  `AGENTS.md` 新增两条规则（索引同步；未经确认不得新增顶层目录）。
- **模板**：12 合 1 的模板单体拆分为真实文件，落在
  `skills/agentflow/templates/{feature,issue,releases}/` 下并配 manifest；
  新增 issue、release（`todo` + `pending-test`）与根索引骨架；feature README 模板
  新增 light-mode 声明；旧单体路径保留为指针，
  使历史引用仍可解析。
- **方法文本**：`document-chain.md`——布局现有两种形态（文档枢纽 vs 业务
  仓库）、light mode、证据落点、新门 7（评审落点 + 验收词汇）、评审桥落在 `reviews/`；
  `contracts.md`——"Asking before assuming"、越界意图的边界报告、
  "Record freezing and archive"；角色与角色文件——
  FE 四阶段条款（浏览器验证、不建平行目录、拆分信号）、BE 先验证契约、
  reviewer finding 严重度、test-planner 断言纪律、
  test-executor 真红/flaky 分类。
- **迁移**：107 个文件移出 `records/`；40 条缺陷记录重编号为
  `BUG-… → ISS-2026-001…040`（文件名、`bug_id`、台账、交叉引用——映射表在
  `features/feature-2026-10-09-结构改造/plan/migration-mapping.md`）；移动后的文件内
  273 处机械路径改指；`records/` 外壳与操作系统垃圾文件移除；审计与交接
  文档冻结进 `_archive/`；校验器、测试、fixture、schema、角色与评测
  全部改指，且未放宽任何检查；`record_store.py` 为六个活区建索引（重建 94
  条记录）；runtime 重建。
- **验证**：`validate.py all` 10×PASS；`doc_chain.py --self-test` 38/38；执行前计划评审
  两轮（F1–F9 `changes_requested` → 修复；R1–R2 + R3–R10
  `changes_requested` → 全部修复，reviewer：可发布）；迁移后复验转绿；
  `validate.py installed` 报告预期中的漂移（源码领先于已安装的 0.8.7
  快照——marketplace 刷新 + 重装属用户侧，待办）。
- **治理通道**：直接的用户指令结构变更（与 0.8.2 / 0.8.7 同一通道）。
  受保护路径的编辑（校验器、测试、schema、evaluator/governor 文本、评测）在
  用户的明确指令下完成，并记录在本批 episode 中供回溯评审；
  无 candidate/evaluation/comparison 集；不描述为已验证的
  改进。
- **measurement: none**（方法级改动，无仪器化业务任务）。

## 0.8.7 — 2026-10-08

执行侧接线 + proposal 阶段的提问程序，用户指令（"实现和执行的时候
老是跑偏…遇到阻塞不思考、不确认、不参考" + "提问比较重要"），方法来源逐字读自
mattpocock/skills 仓库（grilling、wayfinder、diagnosing-bugs、prototype、
writing-for-agents、code-review、retro），每个采纳的机制都重新锚定在本仓库自己的
条款与 episode 上。方法级改动；`measurement: none`。

- **E——intake interview（proposal 阶段）**：`document-chain.md` 新小节——围绕决策
  **frontier** 的轮次（每轮覆盖整个 frontier，每个分支一个问题并附推荐
  答案），事实由作者查证而非去问，决策提交给 owner 并等其答复，
  完成 = frontier 为空 + owner 确认，轮次持续扩张时给出 scope 拆分信号。
  问题格式：≤3 个选项（维持现状 / 最省可用 / 推荐），每项各带一行
  适用条件与代价，绝不写利弊论文；推荐项要写明在什么条件下它是错误选择；
  自由形式回答（"pick one / pick one and amend /
  none of them"——最后一种会重新打开该分支）；选项字母为轮内局部（台账中记 白话（代号））。
  **Challenge-the-answer** 规则（答案与冻结文本/代码的冲突，在它们抵达的
  那一轮裁决）、**ungrillable → throwaway prototype** 出口（结论回写
  台账，原型按 线框/原型 路径保留为证据），以及 **台账回写**
  （可判定的闭合条件、日期、确认人；一张「未成型」迷雾清单，含晋级规则）。
  接入 Gate 1、Role wiring、SKILL.md 的文档交付段落，以及 proposal
  模板的 待冻结问题台账 占位符。
- **A——未被要求的行为**：reviewer 新增一个可引用的 finding 类别，从两个
  方向读取 diff（投机的抽象、不必要的重构、搭车的无关改动）；每条
  finding 引用其 hunk 以及它不服务于的那句目标。worker 侧得到
  正面动作（`contracts.md` **Change discipline**）：不需要的工作以具名
  条目退回，一个改动集只服务一个目标。`roles.md` 的 reviewer 清单更新。
- **B——首次遇阻协议**（`contracts.md` 新小节、`SKILL.md` 条目）：不是失败循环的
  首次阻塞走四步——枚举已尝试过什么（"stuck" 与任何断言同一证据标准）、
  自行查清事实并继续不依赖它们的工作、
  只把属于 owner 的决策连同推荐默认值提交（Spec 反审门的形态）、
  然后以最小决策 `blocked`。重复失败规则不变。
- **C——design_refs**：plan 行的「关联 design 条目」进入 brief（`design_refs` 进
  read_scope）与结果（`design_refs_implemented`，分歧需带理由）；reviewer
  核实每处引用可解析、行为与其援引的决策一致；两个工程师
  角色文件现在指向契约，而不再拖着一份过期字段清单。
- **D——contracts.md 去重**：重复的 `## Worker result` 与 `## Review result` 小节
  各自合并为一处（失败语义、降级、cost/duration、接受前编译、
  预算纪律全部保留——经 reviewer 与单副本 grep 核实），并加
  一行头声明单一来源。
- **验证**：`doc_chain.py --self-test` 38/38；unittest 155 OK；`validate.py all` 10×PASS
  （schemas examples evals artifacts mock protected manifests docs tests doc_chain）；独立
  评审两轮——第 1 轮 `changes_requested`（4 项发现：方向错误的引用、
  原型保留矛盾、门名不精确、工程师角色中的过期字段枚举）
  全部修复，第 2 轮 `approved`、0 项必改；`validate.py installed` 修复后
  重跑：exit 1，恰为预期中的 8 文件漂移；runtime 对
  `cache/agentflow-local/agentflow/0.8.7` 重建后转 PASS（注：`validate.py installed` 比较
  源码树与按版本命名的 cache 目录，而非宿主 registry——宿主 registry
  仍指向 0.8.3；应用内 marketplace 刷新 + 重装待办，在其运行之前
  本仓库之外的宿主加载的仍是旧条款）。`isolation.py check-diff`（候选副本、
  门三件套已回退，基线 d7461e6）：`blocked: []`。范围外的既有未提交
  编辑（AGENTS.md、protected-paths.txt、tools/lab/validate.py——文档链自测门
  接线）按用户决定刻意留在各自的轨道上。
- **治理通道（显式）**：本批是**直接的用户指令方法改动，而非
  improve 环治理下的晋级**——没有为其产出 candidate/evaluation/comparison/release 记录集
  （0.8.4–0.8.6 各自都带四件套工件）。因此它不得被
  描述为已验证或已评测的改进；其证据是本 episode 及记录其中的两轮
  reviewer 评审。若为对齐格式需要该环的完整记录集，那是一个
  后续批次。由此产生的一处混合已披露：`packaging/runtime/protected-paths.txt`
  与 `cache/0.8.7` 快照携带的受保护清单状态包含
  `tools/lab/doc_chain.py` 一行（构建快照时未提交；门三件套在同一次推送中
  以独立提交发出），因为 runtime 重建会从
  工作树复制 `protected-paths.txt`。
- **measurement: none**（方法级改动，无仪器化业务任务；预防效果
  待首次真实交付对照验证）。

## 0.8.6 — 2026-09-22

表达纪律作用域扩展到会话交付物，用户指令（"agentflow 写
的东西还是有黑话"——用户不得不手工建九词黑话解码表）。方法级
改动；`measurement: none`。

- **作用域缺口收口（BUG-20260922-01，provenance agentflow / attribution workflow_policy）**：
  表达纪律套件（条款、模板提醒、linter、reviewer 文档模式）
  只锚定文档链，而会话内交付的分析报告——
  aiwork 交付漏斗/聚合分析报告——零覆盖。条款文本未命名的两个
  子形态：代号手柄在定义一次后被裸用作正文主词汇
  （「A 桶/D 桶/G 桶」），以及 schema token 充当正文主语（「prepared 会话」,「Run」）。
- **方法**：两条新条款规则——代号裸用（以平实词作主语，代码总与
  平实注释配对；检验 = 定义表不翻转）与 模式词分域（标识符留在
  code/SQL 语境，正文用业务措辞；用户自己的规则：正文用「执行」，代码和 SQL
  里保留 Run）——外加一条显式作用域声明，把纪律扩展到会话
  交付物。Supervisor 交付前自检（roles.md）与两个可引用的 reviewer 条目，
  附一条委派路径。
- **可用装置**：`doc_chain.py --file <path>` 单文件模式（文本形态检查 C12–C14，
  结构检查跳过）与 **C14 代号裸用**（单个大写字母 + 桶，定义表 /
  code-span / 配对注释豁免）。自测 26→38 例。C15（schema token lint）已评测
  并被有意降级为条款+reviewer 治理——真实语料洪泛风险记录于
  自测用例 34。
- **语料证据**：对被标记的 AIPPT 报告跑 `--file` → 4 项 C14 发现（:40/:274/:280/:648）；
  干净的伴随报告与一个 Youc "IP 桶" 文件 → 零误报。同批内对两份被标记报告
  按用户自己的映射表就地去黑话（机器门 exit 0，
  数字/SQL 未动）。
- **验证**：自测 38/38；unittest 155 OK；`validate.py all` 9×PASS；isolation
  blocked=[]；evaluator pass（0 阻塞 / 8 非阻塞，N1–N8 已在
  EP-20260922-002 中处置）；release-governor promote（人工把关）。
- **measurement: none**（方法级改动，无仪器化业务任务；evals/business
  不覆盖会话交付物面）。

## 0.8.5 — 2026-09-22

文档链的 UI 轨（spec/ui + design/ui 骨架），由 Youc office-agent 文档链试点驱动
（EP-20260922-001）。方法级改动；`measurement: none`。

- **spec/ui 与 design/ui 骨架**（`document-chain-templates.md`）：与 spec/fe、design/be|fe
  家族同构（§0 反审/自检、固定节标题 0–6、真源引用不复制、变更记录承载用户迭代）；
  `document-chain.md` 声明 ui 轨启用规则（proposal 保持单一；linter 对 ui 文件仅做
  存在性/围栏/时效性检查，形态质量靠反审+README 门禁兜底）。
- **验证**：自测 26/26（当时）; Youc 试点 linter PASS（含 ui 文件被扫描）;
  `validate.py all` 9×PASS; isolation blocked=[]; independent evaluator 修复轮（linter
  覆盖面措辞收窄、试点 design/ui 标题对齐模板、README 启用声明、治理记录补齐）后 pass;
  release-governor promote（人工把关）。
- **measurement: none**（方法级改动，无仪器化业务任务）。

## 0.8.4 — 2026-09-21

文档链收口批（BUG-20260921-01~05）——过期前向引用、经 brief 注入的会话角色词、
存在性≠形态的填鸭式复发、方法 vs 模板的冲突裁决、
episode 信号完整性。见发布记录与 `records/bugs/recurrence/` 升级记录；
linter C12/C13（自测 26 例）。`measurement: none`。

## 0.8.3 — 2026-09-20

自我立账的缺陷批与防漂移加固，用户指令（"把你犯的错记录一下" /
"加点模板处理，不然一句话会偏移"）。方法级改动；`measurement: none`。

- **三条自我立账 bug 记录（`verified`，独立 reviewer 两轮，最终
  approved）**：BUG-20260920-02 首轮文档链密度失败（无字段级
  契约 / 无失败分支图 / plan 无落点 / 阻塞项从未提交给
  需求 owner——修复 = 门 1–5 + density floor + `doc_chain.py`，评审于
  EP-20260920-002）；BUG-20260920-03 生造黑话「爆炸半径」，违反 0.7.3
  表达纪律（修复 = 换>释>删 全量替换、零 grep、纪律条款补入）；
  BUG-20260920-04 全文件重写静默丢承诺内容（图目录
  条目、一个小节、C6 fixture——修复 = 图覆盖检查 C4/C7/C8 + 18→20 例
  判别自测 + 承诺内容清单纪律）。
- **三本复发台账**（`doc-chain-generation-density` / `expression-discipline-jargon`
  / `full-rewrite-drop-promised-content`，consolidated_in 0.8.3——收尾增量
  在本版发出，而非 0.8.2）。
- **生成契约中的表达纪律**：不许生造黑话，也不许使用
  指向随读者而变的压缩词；修复优先序 换 > 释 > 删；过度解释
  同样计为阅读负担缺陷。
- **语料推导装置**（对业务仓库的 30 个 feature 普查）：plan↔design
  关联列、落点校对表、统一错误码表标准、OQ owner/blocked-by
  字段、QA 层纪律（N/A 必须指明验收落在哪里）、8 条文档
  反模式清单。
- **带固定标题字面量的填空模板**（`document-chain-templates.md`，12 个
  骨架，含 README 入口看板与 QA 三件套）+ linter C11 结构检查
  （经 README 声明行做标记门控；自测 20 例）。
- **验证**：自测 20/20；真实链 `PASS doc-chain`；`validate.py all` 9×PASS；
  快照已重装。

## 0.8.2 — 2026-09-20

合并/集成质量门：触发面与契约现在覆盖这种任务形态——
"任务本身是一场需要解冲突的 git merge"（BUG-20260920-01，类别
`merge-integration-quality-gate`）。方法级改动；`measurement: none (method-level
change, no instrumented business task)`——不是已验证的改进；预防效果
待发布后对照验证。

- **触发面。** `agentflow` skill 描述枚举 *分支集成与
  冲突解决（合并必须手工解冲突的分支）*；
  路由表（`roles.md` + `docs/agent-roles.md` 中文镜像）新增对应行：
  Supervisor 解冲突并验证 + 独立 Reviewer，当 Supervisor
  亲手解了代码冲突时强制适用。
- **集成步骤的合并门（SKILL.md 步骤 6）。** 由 Supervisor 亲手解冲突的合并
  ——或其结果改变用户可见行为——属 material 改动：
  步骤 8 的评审门适用，Supervisor 自己的冲突取舍也不豁免。
  在报告完成之前，跑能证明合并产物可构建、行为正常的确定性检查
  （按受影响的部署单元跑构建/编译 + 测试套件，如 `go build
  ./...` + `go test ./...`、各应用 `tsc --noEmit`；涉及迁移的合并跑一次
  迁移），并保留原始输出。冲突标记 grep 是分诊，绝不是验收——
  这是漏网的 `validate()` 重复定义背后的具名反模式。禁止例行
  构建/测试的工作区规则只是迭代默认值，不是豁免：跑检查或
  升级给用户，绝不静默跳过。
- **授权 ≠ 验证（contracts.md 硬边界 3）。** 授权只解决
  集成可否发生；它不验证结果——亲手解决的合并
  仍受评审门（边界 1）与确定性检查纪律
  （边界 4）约束；清掉冲突标记不算一次检查。
- **验证**：`validate.py all` 9×PASS EXIT=0；`isolation.py check-diff`（候选
  树 vs 冻结基线 `5da90f2`）`blocked: []`；冻结锚点 2026-09-20T04:18:55Z，工件
  摘要 `sha256:e40d281cb2a8f6186405148a318ca9372c0fb9910f26d747a94be340e93e85e0`。
  证据：BUG-20260920-01、EP-20260920-001。宿主快照待用户的
  marketplace 刷新 + 重装；工作区 `.zcode/skills/` 活路径经 symlink
  承载新措辞。

## 0.8.1 — 2026-09-18

0.8.0 装后闭环复核：剩余的 C 域契约残余项（装后复核时
发现 0.8.0 台账附录漏列）、D1 收敛矛盾
以有记录的过渡态消解、最后一条 `open` bug 记录转入
`fixed-pending-review`。方法级改动；`measurement: none`。

- **C 域残余收口。** `contracts.md` 新增 worker 失败语义：`crash` →
  `blocked` 并具名原因（先做环境 vs 工作的分诊），`timeout` → `partial`，
  未验证的在途工作丢弃，`empty/invalid return` → 退回一次并具名缺陷，
  然后立 bug 记录——Supervisor 依证据分类，崩溃的 worker 绝不
  自我分类，静默超预算重试或改标签的崩溃都算 Supervisor
  缺陷。`SKILL.md` 步骤 7 现在要求在每个验收点做 plan 看板回写
  （仅状态 + 证据列），步骤 10 在结果回喂改进环时
  援引失败语义。
- **D1 以显式过渡态消解（选项 a）。** `roles.md` 与中文镜像
  声明 bug-investigator / feedback-analyst / technical-director 有意与
  reviewer 保持分离，尽管形态相近，并给出输入契约层面的理由；
  合并它们仍是保留的产品决策。与收敛原则的矛盾
  已消除，且未改动公开角色面。
- **BUG-20260914-003 → `fixed-pending-review`。** 最后一条 `open` 记录（print 模式权限
  画像阻塞 plan 编写用例）与 0.8.0 的 `--allowed-tools` /
  `--isolate-host-config` 机制——即该记录自己提出的 "option A"——吻合，现携带
  `fix_revision: agentflows@95de103`、`regression_status: not-run`（如实：仅桩级
  验证；`verified` 等首次真实评测，G4）。
- **验证**：`validate.py all` 9×PASS（含用户刷新 marketplace + 重装到
  0.8.0 后的 `installed`）；149 个单元测试 OK。

## 0.8.0 — 2026-09-18

第二轮审计整改（依据 `docs/audit-2026-09-18-followups.md`）：度量效度
S0 项收口（B1/B3）、P0 清单中的评测隔离前置条件、
诚实文档批（E2/E3/E5/E8）、记忆层契约收口（F3/G2/G3），以及审计报告 §6 中剩余的
确定性残余项。包含 **门变更（受保护路径），于 2026-09-18 在
明确人工指令下应用**：`host_adapter.py`、`eval_runner.py`、`policy.py`、
`validate.py`、`artifact_digest.py`、`schemas/`、`skills/improve/references/`、
`agents/release-governor.md`、`tests/`。方法级改动，尚无仪器化业务任务
运行过；`measurement: none`。

- **B1——种子答案不再可从被测树读取。** 被测工作区下存在任何 `*.seeds.json` 时
  业务请求 fail closed（含 dry run），可信 `repository_root` fixture 副本缺少
  评分所读的种子时同样 fail closed；runner 侧
  契约（从被测副本中剥离 `evals/business/seeds/`）记录于
  `evals/business/README.md`。残余如实声明：codex 读取范围未验证，
  因此权威 codex baseline 在确认前不可信。
- **B3——一项护栏改为宿主观测而非自报。** claude adapter 以
  `--output-format stream-json --verbose` 运行，扫描出错工具结果中的拒绝措辞
  （本仓库自己的 print 模式诊断观察到的那批），并写入 `observed_permission_denials`
  （按重复次数，adapter 所有，覆写模型的值；两个结果 schema 中
  均为可选）。该通道是带标注的启发式，待首次实机验证；codex 没有
  该通道，键缺席表示 "not observed"，绝不是 0。
- **P0 隔离前置条件。** 请求级 `allowed_tools`（逗号拼接进 `--allowed-tools`）
  与 `isolate_host_config`（`--strict-mcp-config` + 一次性 `CLAUDE_CONFIG_DIR`）取代
  仅画像语义（claude），在 codex 上则明确拒绝；记录于
  `observed_context` 的 `allowed_tools`/`mcp_isolated`；runner CLI `--allowed-tools`
  /`--isolate-host-config`；权威运行必须同时携带两者。
- **B5——rollback 是声明的，而非照抄的。** `policy.py` 决策携带 `rollback` 块，
  其中核实目标等于所测 baseline 版本（candidate 版本与其
  父版本相等现在视为无效），并显式声明安装态验证属于
  release governor——其角色文件现在要求此举；promotion 的后续动作必须包含
  复发台账 `consolidated_in` 回写（F3）。
- **B8——审计 §6 残余修复。** `validate.py`：`load_bug_markdown` 把
  `UnicodeDecodeError` 呈现为结构化错误；正文引用路径在仓库内做
  包含性检查（`ROOT/../` 逃逸不再通过）；`tests/` 的已声明内容
  断言不再豁免点号条目。`policy.py`：未知指标被标记，且不再
  抛崩溃形态的 `KeyError`、不产方向行；容差下限（`1e-9`）加 policy
  表适用于主指标与受保护切片，末位浮点噪声不能读作
  回归、也不能冒充改进；显式空的 `protected_slices` 列表保护每个
  被观测切片。`eval_runner.py`：省略 `repeat_count` 的用例被拒绝，而不再
  静默继承 `--repeat-count`。`artifact_digest.py`：mode 位仅归一化到
  可执行位，摘要不再依赖创建时的 umask（旧版本的摘要
  在算法变更后不可比）。
- **E8——mock/ 现在由门编译。** `validate.py mock`（在 `all` 中）把树拷到
  临时目录，将 `mock/records` 叠加到副本的 `records/` 上，在那里跑完整
  artifacts 编译；偏离契约的 fixture、或与真实记录
  id 冲突，现在直接失败，而不再等人工 `/tmp` 实验。`mock/README.md` 如实
  写明该机制。
- **E2/E3/E5——活跃误导移除。** 版本字面量从四个
  当前成熟度文档面移除（README + 三份设计文档；`validate.py docs` 现在会在
  它们重现时报错）；`iteration-log.md` 的十二个 "当前源码" 头按历史做了时间限定；
  交接文档中的 remote 字符串与实际仓库一致——推送揭示它在 GitHub 上
  被改名为 `Ganseblum/agentflows.git`，于是本地 origin URL 也一并更新
  （旧名经重定向仍可用）；虚假的 "excluded by packaging
  allowlist" 横幅被观察到的事实取代：本地目录 marketplace 会
  对整目录做快照（host-platform-facts Z10）。
- **G2/G3——记忆层契约收口。** `review_roundtrips` 成为 episode
  schema 的必填项；五个 0.7.2 之前的 episode 回填 `[]`，外加显式的
  `review_roundtrips_backfill` 信号（未捕获 ≠ 无评审）；负向结果
  （`rejected`/`partial`/`failed`）被宣告为对抗幸存者偏差的
  一等 episode 证据。D2：边界 7 现在写明 evaluator/governor 分离是角色分离，而非
  环境隔离。D1（角色收敛）仍是经深思的产品决策，暂缓。
- **验证**：`python3 tools/lab/validate.py all` 9×PASS；149 个单元测试 OK；
  在 `/tmp` 副本上的故障注入确认 `mock` 与版本散文护栏 fail closed，且
  恢复过程被观测。

## 0.7.5 — 2026-09-18

审计驱动的加固：门、评测身份、评分、角色/环契约、episode/release
一致性，以及 `records/` 的首个本地读侧。方法级改动，不涉及带
仪器化业务任务的行为变化；`measurement: none`。

- **门现在会运行，且 fail-closed。** `.github/workflows/validate.yml` 从可信检出对
  冻结基线 revision 运行 `isolation.py check-diff`，并保护
  `.github/`；`isolation.changed_paths` 改用 NUL 分隔的 Git 输出，空格、
  引号、换行与非 ASCII 路径不再逃过受保护前缀检查，且
  检查器在自己的根就是候选或与其嵌套时拒绝运行。
- **`validate.py` fail-closed。** `records/` 缺失或为空时 `artifacts` 报错；
  记录遍历器拒绝隐藏条目，`.DS_Store` 除外；回归套件门现在解析
  末尾的 `Ran N tests` 汇总，拒绝任何 `skipped > 0`，并保留下限。已把
  `tests/test_record_store.py` 加入钉住测试清单与 `REQUIRED_PROTECTED_PATHS`。
- **确定性 policy/adapter 修复。** `policy.main` 在 `reject` 时返回非零；Codex
  与 Claude adapter 现在先解析宿主 JSON、只注入一次 `latency_ms`、只校验一次，
  并把非对象载荷转换为结构化失败而非 traceback；`eval_runner` 保持
  `suite` 在仓库内，并把 baseline/candidate 的用例覆盖键统一为
  `(case_id, slice, holdout)`。
- **业务评分不再可被刷分。** `seed_grader` 拒绝路径穿越与
  偏离目标的 finding，限制 finding 总数与单字段长度、去重，并施加
  单目标文档的未匹配上限；`target_docs` 之外的 finding 记为 `off_target`，
  不影响召回。`evals/business/README.md` 记录防刷分约束。
- **episode/release 完整性与读侧。** Episode schema 新增 `revision`、`run`、`claims`
  与 `evidence`；release schema 新增结构化的 `measurement`（`status` + `basis` +
  `business_case_ids`）与更紧的 promotion 约束：`promote` 需要 `better` 与
  一次批准，而 measurement-`none` 的发布不能被记错为已验证的改进。新增
  `tools/lab/record_store.py`，为 `records/` 提供一次性的 SQLite FTS5 读侧；Intake
  被记录为在简报前用它检索。
- **角色/环契约收敛。** 路由、`roles.md`、`docs/agent-roles.md` 与各 SKILL
  现在一致：仅由 Supervisor 承担的小改动仍须过不可豁免的独立 reviewer；
  `test-executor` 区分脚本化无头浏览器自动化与宿主交互式
  浏览器自动化；worker brief 与结果携带 `task_id`/`baseline_revision` 以及
  一个单独的 `status: partial` 语义；`plan-architect`/`test-planner`/`bug-recorder` 得到
  其契约所需的 `Edit`；缺失的改进环角色绑定补齐；改进
  SKILL/角色 指定 Supervisor 为执行期间 plan 状态/证据的唯一写者。

## 0.7.4 — 2026-09-18

措辞清理遍，关闭从 0.7.2/0.7.3 带过来的 reviewer 残余项：

- `records/README.md` 的 episode 行现在写明放宽后的触发条件——自 0.7.2 起每个 material
  改动都必写，含评审往返轮——这是最后一块仍带
  旧「仅改进环」口径的文档面。
- `mock/README.md` 的 episode 行同步为同一口径（material 改动必写，含
  `review_roundtrips`）。
- `PLAN-BUSINESS-EVAL-001` 的 frontmatter `plan_version` 与其最新修订行对齐
  （0.2.3 → 0.2.5）；无任务行或内容改动。
- 仅文档；无代码、schema、seed 或用例改动。度量状态不变（仍
  被 U-01 阻塞）。

## 0.7.3 — 2026-09-18

黑话纪律判据依用户反馈放宽：术语歧义（terminology-ambiguity）
类别现在明确覆盖高频变体——习惯性压缩词
（基线 / 现网 一类），其指代随读者与时间漂移——而不只是生造的
未定义术语。修复纪律的排序是 **换 > 释 > 删**：先换成具体对象
（commit、版本、环境、取值——通常更短、零阅读负担）；只有当术语必须保留时
才就地给一行定义；否则删掉该词、直接陈述行为。
过度解释计为阅读负担缺陷。种子植入说明已按
该变体更新：锚点取目标文本中一个唯一既存片段，无需植入。
用例与 seed 文件未动；新变体种子待 U-01 清除后随 S 阶段落地。
门变更（受保护路径 `evals/business/README.md`），会话内人工授权；
度量状态不变（仪器已建、尚未运行——U-01/U-08 仍卡着 S）。

## 0.7.2 — 2026-09-18

分歧可审计性切片：流程中段的评审分歧获得持久、机器可查的
载体，记录获得渲染器安全的可视层。**门变更，会话内
人工授权**：`skills/improve/references/episode.schema.json`（在 `protected-paths.txt` 内）
新增一个可选字段——不触碰其他任何门路径。

- **episode 承载评审往返轮。** `review_roundtrips[]`（at / reviewer / decision /
  finding / resolution / evidence_ref，`additionalProperties: false`）记录每个
  独立评审轮——返回 `changes_requested` 的那些轮、分歧是
  什么、如何解决的。episode 触发条件放宽：每个 **material**
  改动（任何打开过评审门的改动）都在会话结束前落一个 episode，而
  不只限改进环候选。流程中段的评审分歧在对话结束之后
  仍可审计，而不只是最终裁决。
- **可视标注约定**（`records/README.md`）：固定词汇表的
  GFM callout——`> [!IMPORTANT]` 未决分歧/阻塞, `> [!WARNING]` 残余风险/已知缺口, `> [!NOTE]`
  口径澄清——外加用于前后对比或 A/B 对比的 ` ```diff ` 围栏。固定字面量
  前缀保持 callout 可 grep；frontmatter 枚举与固定小节仍是
  权威语义层。行内 HTML 颜色与自定义 `[!...]` 告警类型
  被拒绝（渲染器不可移植，污染可 grep 层）。
- 示例演示这些约定：bug 记录示例新增 `> [!WARNING]`
  残余风险 callout，plan 示例新增 `> [!WARNING]`（外部依赖风险）与
  `> [!NOTE]`（非阻塞待决项）——镜像进 `mock/`。
- 文档同步：`docs/agent-roles.md`（episode 触发 + 标注约定）、
  `records/episodes/README.md`（字段清单 + 触发），两份 SKILL.md 副本（步骤 10）。
- 度量：none——文档约定外加一个可选 schema 字段；不涉及
  带仪器化业务任务的行为变化。

## 0.7.1 — 2026-09-18

测试角色吸收轮，素材来自业务侧准入标准与一套既有的
YAML 驱动 Playwright 套件（材料汇总于 EP-20260918-001）：用例库
现在说目标引擎的词汇，执行在开浏览器之前先验证收集，
失败在进入 bug 链之前完成分类。方法级改动，
无门变更——`schemas/`、`tools/lab/` 与钉住测试均未动。

- `test-planner` 新增四条纪律：编写用例前的 **准入检查**（缺失的
  路由、预期结果、前置条件、角色/数据，以编号缺口登记在
  `## 流程疑点`——绝不生造、绝不打扮成更弱的断言）；**目标引擎
  对齐**（元素经注册表别名引用，动作与预期结果按
  引擎的拆分，可复用的前置条件引用而非拷贝，环境取值用
  变量，只用项目声明的文件名）；**会话顺序**（注销 / 清 cookie
  用例放最后或隔离，绝不混入已登录会话）；以及一条 **能力边界
  规则**（框架已记录能力之外的行为标 TODO /
  不可自动化并带原因）。一份交付 **自检清单** 镜像 reviewer 将要
  检查的内容。
- `test-executor` 新增目标 runner 适配与失败分诊：**先做收集试跑**
  （`--collect-only` 式——在开浏览器之前抓住坏引用；
  没有注册表条目的用例目录会被静默地永不收集；套件在
  其用例文件存在之前就已注册）；**按 runner 的解析顺序取证**（运行报告 →
  失败截图 → 日志，逐行引用具体工件）；注册表缺口记录
  在结论中，而不是内联一个裸 locator；每个失败都**先分类
  再立案**——产品缺陷 → bug 链；用例/注册表漂移 → 更新注册表 + 重跑；
  环境/数据 → `blocked`——每类都具名修复落点，让 bug 池保持
  无噪声。
- `records/tests/README.md` 新增 **Target-project mapping** 小节：对齐链
  （前端 test id ↔ locator 注册表 ↔ 用例库 ↔ 引擎用例 ↔ 流程 ↔ 套件注册表
  ↔ 环境配置），逐环写明必须一致的内容与改动的落点——同一张
  表也用来路由失败修复。
- `docs/agent-roles.md`（中文镜像）记录对齐链与失败分诊。
- `measurement: none (method-level change, no instrumented business task)`——与
  0.7.0 同类；不是已验证的改进。

## 0.7.0 — 2026-09-18

自动化测试能力切片——用户可见功能现在能由方法本身端到端地测试：
带可执行步骤与边界覆盖的用例库、带证据的执行、
失败立案进 bug 链，以及对整次运行的流程合理性评审。
由用户的明确反馈触发（EP-20260917-003）：真实浏览器自动化（宿主浏览器
MCP / Playwright）、凭据运行时注入、细致的边界用例、运行报告，以及
smoke/e2e 评分。

- 新增 `test-planner` 角色（`agents/test-planner.md`）：在显式
  `records/tests/<project>-<feature-slug>/plan-*.md` 路径设计用例库——用例注册表，层级
  smoke/e2e/api/boundary、优先级 P0–P3；逐用例步骤表的断言
  对从未读过代码的操作者也可观察（元素文本、导航、
  网络请求是否触发）；边界覆盖矩阵（空输入、非法格式、超长
  输入、特殊字符、重复提交、会话过期、数据缺失、网络故障——
  未覆盖类别须声明，绝不静默）；以及 `## 流程疑点` 登记 spec
  未定义的行为。凭据只以注入方式出现，绝不出现在取值里。
- 新增 `test-executor` 角色（`agents/test-executor.md`）：执行已批准的 plan——先脚本化
  自动化（Playwright 无头）、API 用例走命令，宿主浏览器 UI 步骤
  编译成步骤脚本，由 Supervisor 在主对话中执行（浏览器
  自动化在 Claude Code 与 ZCode 上仅限主对话），仅凭返回的
  原始证据判定 pass/fail。每轮写一份 `run-*.md`，含逐用例结果（固定枚举
  `pass / fail / blocked / not-run`，fail/blocked 行必须有证据）、扁平汇总
  计数、一个决定，以及可复现的 finding。`Edit` 被禁止：运行记录
  是只追加的历史。先 smoke；构建坏了就停止全集。
- 新增记录类别 `records/tests/`（契约：`records/tests/README.md`）：按 feature 锚定的
  目录，存放 plan（就地修订、`test_version` 递增）与逐轮运行
  记录，后者钉住 plan id/版本与实际被测试的 `target_revision`。运行的
  `findings` / `flow_findings` 引用既有 bug 记录；运行记录的原始证据
  兼作评审门的端到端路径证据。
- 新增 schema `schemas/test-plan.schema.json` 与 `schemas/test-run.schema.json`。
  校验器接入该类别：布局与文件名↔id 一致、用例注册表解析
  （`TC-*` id 唯一、层级/优先级枚举、`case_count` 相等、每用例一个明细
  标题）、运行结果表检查（枚举、fail/blocked 有证据、id 能在 plan 的
  注册表中解析、汇总计数等于表、`decision: pass` 要求零 fail/blocked）、
  plan 在同一 feature 目录内解析、运行钉住当前 plan 版本时
  全用例计账、finding 能解析进 bug 池。合法的 plan/run 示例在
  `examples/test-records/` 下；结果枚举反例在 `examples/invalid/` 下。
- 角色/方法增补：`plan-architect` 现在要求每个带用户可见行为的 plan 都有一个
  测试设计任务（指派给 `test-planner`），并在
  验证命令 中引用 smoke 集；`reviewer` 新增 *Flow reasonableness (test evidence)* 专家模式
  （未定义的超时/重复提交/中断路径、跨面错误消息
  一致性、不可达状态——"should have failed but did not" 即为一条 finding）；
  agentflow skill 新增 *Automated testing* 工作流小节，两份宿主绑定的角色
  清单现在都点名两个新 agent；`roles.md` 与中文镜像（`docs/agent-roles.md`）
  承载路由行与画像。
- 钉住的回归测试增至 118 个（新增 10）：随附示例通过、反例
  被拒、plan/run 不变量逐规则被演练（case_count 不一致、汇总
  不一致、未知 plan、无证据的 fail 行、注册表外的行、用例覆盖缺失、
  pass 决定带失败）。
- 门变更，人工指令：为落地本批，编辑了 `schemas/`（两个新记录契约）、`tools/lab/validate.py`
  与 `tests/test_lab_contracts.py`，并获用户会话内的
  明确批准（0.6.0 先例）。
- 独立评测与发布决定：独立 evaluator 对照文件核实全部八条
  验收标准（结论 `neutral`——真实、内部一致、
  门执法与声称完全一致；按 policy 未度量），release governor 返回
  `promote` 并附条件（measurement:none 原样沿用；重装以用户
  批准为条件；后续项在下一个方法级发布前完成）。评审后后续项落于
  本条目：agentflow skill 的 Automated testing 小节中的 smoke 先行
  顺序句、用例明细标题扫描收窄到 `## 用例` 小节并带
  空标题守卫，以及 executor 的 `scratch/` 目录在测试契约
  表中声明。
- `measurement: none (method-level change, no instrumented business task)`——`evals/` 没有
  登录流程切片；本发布不得被描述为已验证的改进。一个带种子的
  业务切片（含植入校验缺陷的快照）是这一能力未来自然的
  度量仪器。

## 0.6.0 — 2026-09-17

方法级改动的首个度量面——这类改动改变角色在
业务仓库内的行为方式，且在 `evals/public/` 中没有回归信号。三个文档评审
用例对一个真实企业仓库的钉住快照运行，快照在植入种子时
转为只读，并在每次宿主调用后复查；确定性评分器将 agent 的 finding
对照运行前植入的缺陷评分。公开面只携带脱敏 brief 与
抽象化的种子清单——快照、种子补丁、符号到路径映射，以及全部原始
结果都留在本地。

- 新增 `evals/business/` 套件：`BT-001` 种子缺陷文档评审、`BT-002` 内部
  矛盾、`BT-003` 跨文档一致性，各带一份脱敏 brief（在 `inputs/` 下）
  与抽象化种子清单（在 `seeds/` 下）。仅当一条 finding 点名
  被植入种子的文档、且其文本包含该种子某个字面锚点时，种子才计为命中。
- 新增 `skills/improve/references/business-case.schema.json`：评测用例契约外加
  `target_id`、`target_pin`（完整 sha）、`target_docs`、`seeds_ref`、`findings_contract` 与
  `grading.min_seed_recall`。target 字段有意只做结构检查——
  公开校验器不得依赖私有快照的存在。
- 新增 `tools/lab/seed_grader.py`：确定性离线评分，产出 `hits` / `missed` /
  `unmatched`；`accepted` 被覆写为 "seed recall at or above the case threshold"，
  `escaped_defects` 为漏过种子数。未匹配 finding 只记录、不扣分。
  未知匹配策略、或 findings 工件缺失/不可解析时 fail closed（退出码 2），
  而不是评零分。
- Runner 与 adapter 业务面：`eval_runner.py --business-root`；宿主 adapter 的
  业务请求分支要求六个业务用例字段、一个共享 pin，以及一个
  `workspace-write` 权限画像（只读画像无法写 findings 工件）；
  真实运行还要求 `--seed-patch`，把快照 HEAD 对照 `target_pin` 检查，要求
  种子补丁可干净回退，并在每次宿主
  调用后复查快照文件集与 `git diff` 摘要。
  `isolation.py layout_errors` 新增一个可选的第四位，用于快照根。
- `validate.py` 把 `evals/business/` 接入 schema 映射与 `validate_business_evals`，
  `tools/lab/seed_grader.py` 加入受保护门清单。钉住测试文件新增 39 个测试
  （共 58 个）。
- 门变更，人工指令：为落地本批，编辑了 `validate.py`、`eval_runner.py`、
  `host_adapter.py`、`isolation.py`、`protected-paths.txt` 与
  `tests/test_lab_contracts.py`。
- 评审后后续项（人工指令）：决定门是否适用的判断词现在在
  agentflow skill 中给出定义（`small change`、`risky work`、`the same
  cause`），并镜像到 `docs/agent-roles.md`；改进 episode schema 约束
  `provenance`（必填 `carrier` 与 `sanitized`，不许额外键）；`validate.py` 重复的
  `docs` CLI 选项被移除；一个 GitHub Actions 工作流在
  push 与 pull request 上运行确定性检查；两个诊断缺陷修复——`run_codex` 现在按路径
  读结果文件（其 `NamedTemporaryFile` 句柄没有 `read_text`，导致每次 codex 运行都失败），
  失败的 claude 调用现在从其 stdout JSON 报错，而不再用
  过去掩盖它的无害 stderr 警告；业务运行还会传
  `--add-dir <snapshot root>`（解析为绝对路径），因为 claude 的 `--print` 模式
  把工具文件访问限制在工作目录，最初几次 smoke 尝试根本读不到
  快照——由两个 argv 回归测试与一行 host-platform-facts 覆盖。
- 开发版本发布：无 baseline/candidate 评测证据。业务 smoke 运行
  被三个未结 P0 项阻塞——可信端点（U-01）、可度量的权限画像（U-02）、
  快照放置（U-03）——因此方法级改动的 `measurement: none` 过渡态
  **并未** 被本发布终结。在刷新 marketplace 并重装插件之前，
  宿主安装快照仍落后于源码。

## 0.5.2 — 2026-09-17

对 0.5.0/0.5.1 文档面的自审：一处静默门缺口、一条死代码路径、五处陈旧
措辞点，以及两处陈旧文档面得以修复。

- 静默缺口（重要的一处）：非法 plan 示例 **从未被演练**——
  示例检查器匹配小写 `plan-` 前缀，而文件名是 `PLAN-INVALID-002.md`，
  且合并的「非法项集合必填」断言仅靠 bug 记录反例
  就满足了。匹配现在不再区分大小写，合法或非法 plan 示例缺失时
  检查直接失败。在一次性副本上验证：把反例改成合法会得到
  "expected invalid example to be rejected"，删掉它会得到 "a valid plan example and an
  invalid plan example are both required"。新增钉住回归测试（共 19）。
- 死代码：plan 校验迁到 Markdown 路径后，`schema_for` 仍把 `examples/invalid/plan-*`
  映射到 plan schema；已移除。
- 陈旧措辞清扫（`parallel lanes` 时代）：plan-architect 的 description、SKILL
  规划段落、角色参考中的 plan 画像、中文镜像的
  `shared_mechanisms[]` 句（现为带注册点的 接口与共享机制 表），以及
  plans README 结构块——后者现在也在 `## 接口与共享机制` 内
  点名评审门（评审门）。
- 陈旧文档面：records/README 的 plan 查询用过 `jq … records/plans/*.json`（JSON 时代），
  现在 grep Markdown frontmatter；tools/lab/README 记录 `artifacts` 覆盖全部
  五类记录，并描述 `docs`、`report` 与 `recurrence` 三个目标。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.5.1 — 2026-09-17

文档评审模式：吸收 proposal/spec/design 流水线的 *质量判据*，而非
其模板体系（用户问题：spec/design/proposal 是否吸收——以及如何让
后续使用更方便）。评审桥本就在评审外部撰写的文档；缺的
是一份按文档类型固定的检查清单。

- `agents/reviewer.md` 新增面向外部文档的 **Document review modes**，每项都锚定
  被评审系统自己的模板要求加上本仓库的纪律：
  - *Proposal / PRD*：范围写入范围且可核查（不可证伪的范围外声明
    即缺陷）、可判定的成功标准、具体场景拆分、显式的「不做」
    清单、显式链接到既有能力。
  - *Spec*：冻结字段语义 / 边界规则 / 异常分支；写明裁决
    规则（哪个结果胜出、什么强制重算、哪些历史不得用于推断
    资格）；默认与降级；边界场景（刚成功 / 刚过期 /
    空 / 非法枚举 / 脏历史）；上游缺口登记且阻塞项关闭
    之后，spec 才算冻结。
  - *Design*：设计完备性工件（时序步骤表、带
    重试四段规则的异常矩阵、发布顺序 × rollback、影响分级）、契约兼容 +
    幂等/并发/事务边界、可观测性，以及指向 spec/QA 源
    而非另造一套的验收标准。
  - *Plan*：本仓库自己的契约——无外部模式。
  每一项只有带原句或 `path:line` 引用才算通过；清单要求某项时，
  "missing" 本身就是一条 finding。
- 评审桥工作流（`records/reviews/README.md`、SKILL 步骤 2、角色参考）现在写明
  模式选择：brief 点名文档类型，reviewer 套用对应
  检查清单。演示用的评审 mock 展示所适用的模式行。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.5.0 — 2026-09-17

plan 契约重设计：执行 plan 变为 **Markdown 融合形态**（用户对比
aiwork-workflow-ai 的 Markdown 计划与 agentflow JSON 契约后选了 option A——
前者人读性更好，后者校验性更好；融合形态两者兼得）。无需
迁移：`records/plans/` 中没有真实 plan。

- 新 plan 形态 `records/plans/<plan_id>.md`：frontmatter 信封（`plan_id` / `plan_version`
  / `status` draft→proposed→approved→superseded / `objective` / 时间戳 / `superseded_by`）
  加上从 aiwork 的 plan 纪律吸收的正文看板——`## 进展概览`（一行进展
  + 一张三受众总览表：业务侧解读 / 技术侧解读 / 交付效果 + 我们在哪/下一步/
  阻塞）、`## 任务清单`（任务表，含 ID/任务/优先级/代码落点/依赖/状态/证据回写 与
  `### 未决项`）、可选的 `## 接口与共享机制`（契约 + 异常矩阵 + 发布顺序
  × rollback 点）、`## 验证命令`。
- 机器断言保留并扩展（`validate_plan_markdown`）：文件名 = plan_id；任务 ID
  唯一；依赖引用可解析且无环；任务状态为固定枚举
  ☐ 未开始 / ◐ 进行中 / ☑ 已完成 / ⚠ 阻塞 / — 本期不做（拒绝自由文本）；**一条未关闭的阻塞
  未决项会挡住 `status: approved`**（aiwork 的缺口登记门，
  已吸收）；必需小节存在。旧的 JSON 不变量（工作包环、泳道
  覆盖）由任务表等价物取代；旧的 `validate_plan_invariants`
  移除。
- 进展回写纪律（aiwork 的看板模型）：plan 就是进展面——
  任务完成后只改其 状态 与 证据回写 两列（最小 diff）；已完成
  行绝不重写。会话中断恢复协议现在读这块看板。
- 示例替换：一份贴近现实的正例 plan（`PLAN-DEMO-SHARE-001`，按真实
  对话分享 plan 的密度建模）与一份多缺陷反例（`PLAN-INVALID-002`：环、重复 ID、
  非法状态、未关闭的阻塞决策）。钉住测试 18 个（新增两个：信封枚举/superseded、
  任务表拒绝）。`plan-architect` 已为融合形态重写；plans README、records
  索引、SKILL 恢复说明与中文镜像更新。
- 门变更，人工指令：plan schema 重写、plan 校验重写、示例
  替换。由单元测试与一次性副本实验验证（环 + 非法状态 +
  未关闭阻塞决策，各自被单独拒绝）。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.4.2 — 2026-09-17

三条 workflow_policy 缺口由在 `infinite-canvas` 仓库工作的兄弟会话
立为 BUG-20260917-01/02/03，在此以用户指令的规则补丁修复
（即记录本身提出的修复）：

- **集成需要授权**（BUG-20260917-01）：硬边界 3 与 SKILL 控制
  小节现在覆盖 `git merge` / `rebase` / `cherry-pick`，以及把远程改动拉入
  共享分支——逐次用户授权，因为选哪种方法、冲突取哪一侧
  是用户的决定。推送被拒时的默认动作是只读报告
  （`fetch` + `log`/`diff`：新增的 commit、改动的文件、重叠部分）；选集成
  方法并推送不是 Supervisor 能自己定的。
- **Git 层写隔离**（BUG-20260917-02）：委派步骤指明，文件不重叠
  并不隔离 commit/rebase/push——并行写者各用独立分支或 worktree，
  一个分支同一时间只有一个写者；写者发现目标被占（其他会话的未提交
  编辑、分支上的新 commit）即停止并报告。
- **状态结论需要仓库证据**（BUG-20260917-03）：intake 现在要求状态
  结论（已完成什么、下一步是什么）用 `git fetch` 加
  `log`/`status` 校准，并带上证据命令——会话记忆不是仓库事实，
  在另一个写者推送的那一刻就会过时。
- 三条记录从 `open` → `fixed-pending-review`，`regression_status: not-run`
  （已记录：规则文本改动没有可执行的回归面；在置 `verified` 之前，
  须由独立 reviewer 指出能证明该约束成立的检查）。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.4.1 — 2026-09-17

文档漂移门与改进环缺失的燃料，两个长期存在的 P1 项。

- 新增 `validate.py docs` 目标（在 `all` 中，现共八项检查）：断言每个 agent 文件的
  frontmatter 名等于文件名；SKILL 引用的每个 `agentflow:<role>` 都能解析
  到一个 agent 文件；docs/records/skills/agents/README 中出现的每个
  `schemas/*.schema.json` 路径都存在；中文镜像的 schema 引用集与
  `contracts.md` 的一致。它首跑就抓到一处真实漂移（硬边界 6 未点名
  新的记录 schema；已通过重写边界 6 使其援引全部四条记录契约路径来修复）。
  钉住测试断言当前树通过；一次性副本实验验证了全部三条
  拒绝路径。
- episode 最小落盘（P1 的第一项，关闭「改进环没有燃料」
  缺口）：`records/episodes/<YYYY-MM-DD>/<EP-id>.json`——Supervisor 在会话结束前
  捕获任务的最终决策记录（目标、结果、claims、评审决定、成本）。
  契约 **复用** 改进环受保护的
  `skills/improve/references/episode.schema.json`，而不是引入一份平行载体
  （对我自己初稿的一次 "extension inventory" 抓漏）。校验器编译 episode
  （schema、文件名 = episode_id、id 全局唯一）；SKILL 步骤 10 现在写明确切
  目的地；首个真实 episode 记录 0.4.0 的 aiwork 吸收会话。
- `validate.py report --project/--status/--provenance`：过滤时无需记住列
  号。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.4.0 — 2026-09-16

吸收自对 `aiwork-workflow-ai` 的系统复盘（其设计模板、issue 记录
与 spec 先行工作流），按用户的明确指示——作为纪律与契约，而非
模板，保持本仓库单一 plan 契约的形态。

批 1——设计完备性与 issue 记录优点：

- `contracts.md` 新增 "design completeness for material features" 纪律（以及
  plan-architect / technical-director 提示词与中文镜像）：(1) 关键路径
  时序，以步骤表为基线，mermaid 时序图只作必须一致的伴随物
  （不一致则图即缺陷；流程步骤绝不堆进
  架构图）；(2) 每条关键路径一个异常矩阵——超时、重复请求、
  状态冲突、回调失败——每行回答检测、处理、重试
  责任人/次数/退避、幂等前置条件、用户可见结果；缺这些
  具体项的重试，或笼统的 "fail-safe fallback"，都算缺陷；`N/A` 须带理由，绝不空白；
  (3) 发布顺序，每一步都配对其回滚点。这些补足
  既有的隐式行为检查（那个守横切机制；这些守
  声明的流程）。
- `closure_criteria`（`verified` 必填）：可度量的闭合条件——具名指标、
  日志缺席，或检查输出；"works as expected" 不是判据。
- `fix_revision`：修复落在哪里（commit/PR/release，跨仓库时带仓库限定）。
- `## 变更记录` 正文约定：每次状态迁移追加一行，让历史不丢于
  单一的 `updated_at` 时间戳。
- 门变更，人工指令：两个 schema 字段 + verified 条件；钉住测试
  扩展（闭项条件必填、verified 样例更新）。

批 2——外部文档评审桥：

- 新记录子树 `records/reviews/<YYYY-MM-DD>/<project>-<slug>/`（契约
  `schemas/review.schema.json`）：`review.md` 加被评审文档的逐字快照
  （在 `archive/` 下），`source_revision` 钉住目标仓库的 commit。
- 评审桥工作流（SKILL "Second-pass review of external documents"、路由表行、
  `records/reviews/README.md`、中文镜像）：先归档、评审快照、把每条
  finding 立为 bug 记录，再交叉链接。`provenance` 拆分两条升级环——`external`
  finding 是升级目标系统规则/模板的证据池（所述用例：
  `aiwork-workflow-ai`），`agentflow` finding 升级本仓库的评审契约；
  目标系统升级落地时由 `fix_revision` 闭环。
- 门变更，人工指令：校验器遍历 `records/reviews/`（评审记录被校验；
  归档的证据副本原样接受），交叉检查每个 `reviewed_docs` 条目
  在磁盘上存在、每个 `findings` 的 bug_id 在 `records/bugs/` 下存在；评审 schema
  加入必保护集合。
- 评审布局按 feature 锚定，而非按日期锚定（发布前的用户纠正）：每个
  被评审 feature 一个目录（`<project>-<feature-slug>`），每轮一个 `review-<YYYY-MM-DD>-<NNN>.md`
  文件（文件名等于 review_id），每轮一个 `archive/<date>-<NNN>/` 快照子目录
  ——同一 feature 可以反复被评审，多轮堆叠在一个目录中，
  而不是散落在不同日期里。
- 自包含引用（用户提出的可移植性缺口：交给没有另一个仓库的人
  的记录必须仍可读）：`files` 条目要么在本仓库内可解析，
  要么以 `<repo>@<revision>:<path>` 形式带仓库限定；哪里都不存在的裸路径
  会被校验器拒绝。带仓库限定的引用是地址，不是证据：记录正文
  必须嵌入决定性片段（代码用围栏代码块，文档
  段落用引用块），并在旁边引用限定地址——两者都由校验器强制，且有一个
  钉住回归测试。对于二次评审产生的 finding，首选的 `files` 条目
  是 `records/reviews/.../archive/` 内的归档快照（逐字副本已经
  存在于本仓库）；整文档副本是评审归档的职责，记录只嵌入
  片段。
- 正文引用规则（用户指示：到处禁悬空引用，记录必须携带
  真实证据）：在普通正文中，每个文档/代码路径都是记录自己的断言——它必须
  在本仓库内（或记录旁边）可解析，或带仓库限定。围栏块与
  行内代码是引用——含历史路径的逐字证据——豁免。
  个人绝对路径（`/Users/...`、`~/...`）一律禁止；URL 无法被校验，
  至多是补充，绝不是证据。由 `validate_body_references` 在
  bug 记录、评审记录与复发台账上强制；既有语料零
  误报通过（其中三条历史路径位于引用内，保持不动）；
  钉住测试覆盖拒绝、豁免与解析。
- 同批自审轮在发布前修掉四个缺陷：正文路径
  模式现在识别 CJK 路径 token（aiwork 用例中的主流形态），同时
  仍忽略类版本号的斜杠（`0.3.4/0.3.5` 不是路径）；评审遍历器只
  把 feature 目录层级的 `review-*.md` 当记录（`archive/` 更深处
  同名的快照此前被误校验）；`review_id` 现在跨评审全局
  唯一；且 `review_id` 的日期必须与 `recorded_at` 一致。全部经
  钉住测试与一次性副本实验验证。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.3.9 — 2026-09-16

provenance：一个回答 "is this Agentflow's problem" 的必填字段，按用户的明确
指示引入。没有它，agent 自己临时写出的 plan 或分析所产生的缺陷
就可能被改进环当作关于 Agentflow 的证据消费。

- 新增必填 frontmatter 字段 `provenance`：`agentflow`（Agentflow 自己的面——条款、
  角色、门、评测、brief 纪律、`tools/lab/` 工具）、`session-artifact`（无条款覆盖的
  临时会话输出——agent 自己的 plan、分析、决策或代码）、
  `user-input`、`external`（既有产品代码、宿主、工具、环境）、`undetermined`
  （缺失的证据必须被点名）。六条记录与两个示例全部迁移。
- schema 强制的矛盾守卫：`attribution: workflow_policy` 或 `role_prompt` 强制
  `provenance: agentflow`——Agentflow 的策略不能认领一个载体并不属于
  Agentflow 的缺陷。
- 改进环过滤（improve SKILL 步骤 2 与 4、feedback-analyst 提示词）：只有
  `agentflow` 记录才是关于 Agentflow 本身的候选证据；`session-artifact`、
  `user-input` 与 `external` 是上下文与反例；`undetermined` 必须先解决其
  provenance 才能进入聚类。
- `validate.py report` 把 provenance 追加为第 7 列；既有列位置不变
  （`cut -f5` 仍选取 error kind）。过滤用
  `python3 tools/lab/validate.py report | awk -F'\t' '$7=="agentflow"'`。
- 门变更，人工指令：schema 字段、守卫规则、report 列与钉住测试（必填
  字段、矛盾拒绝，以及非 Agentflow 取值被接受）。一次性副本上的反例
  测试：缺 `provenance` 的记录被拒；`attribution: workflow_policy`
  配 `provenance: external` 被拒；`session-artifact` 配无关 attribution
  通过。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.3.8 — 2026-09-16

复发跟踪与 P 档 severity，按用户的明确指示。一个 bug 与其后来的
复发之间没有机器可见的联系，而 "which upgrade absorbed this class, and has it come
back since" 只活在正文里。

- `severity` 现在用优先级档——`P0`（严重：数据丢失、安全、发布阻塞）、
  `P1`（高）、`P2`（中）、`P3`（低）——取代 low/medium/high/critical；`validate.py
  report` 直接打印档位。六条记录与两个示例全部迁移。
- 新增复发台账：`records/bugs/recurrence/<class_id>.md`（契约
  `schemas/recurrence.schema.json`）——每个复发过或被
  归纳的失败类别一个文件；只发生一次的普通 bug 不建。`status` 为 `unconsolidated`（未归纳升级）
  或 `consolidated`（已归纳升级），`consolidated_in` 指名吸收该类的发布；
  `occurrences` 列出记录 id，版本从记录自身读取。同一
  类别的记录携带 `class_id` + `occurrence`。
- 档位是推导出来的，绝不手工标注：`validate.py recurrence` 打印 `single` / `recurred` /
  `escalated`，其中 `escalated` 指记录在比归纳版本更新的版本上的
  一次发生——这个加重标记触发改进环升级（带一个评测用例
  重新归纳；improve SKILL 把台账当作一等 episode 来源）。
- 门变更，人工指令：校验器遍历并交叉检查台账——被引用的
  记录必须存在；带 `class_id` 的记录必须有台账且被登记；occurrence
  编号必须唯一；已归纳类别的记录必须携带 `agentflow_version`。
  `schemas/recurrence.schema.json` 加入必保护集合；钉住测试扩展
  （severity 档、归纳要求、文件名/class_id 一致）。一次性副本上的反例测试：
  遗留的 `severity: high` 被拒；无台账的 `class_id` 被拒；未登记的
  occurrence 被拒；无版本的已归纳 occurrence 被拒；结构合法的
  归纳后 occurrence 报 `escalated`。
- 首本台账回填：`unverified-behavior-claims`（0.3.4 经硬边界
  12 归纳，此后零复发）。
- 角色与文档：`bug-recorder`（档位、台账职责、仅依真实发布写归纳）、
  `bug-investigator`（先查台账、提议类别 + occurrence）、
  两份记录 README、角色参考与中文镜像。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.3.7 — 2026-09-16

记录语言约定，按用户的明确指示执行。档案在每个文件内部混用语言
（英文标题盖着中文正文），且必填正文章节标题是英文字面量；
在别处产出的记录已经选了中文标题。

- 新约定（`records/README.md`）：机器层保持英文/ASCII——frontmatter 键
  与枚举值、slug、id、路径、`project`。正文章节标题也是固定字面量，
  用中文——`## 现象`, `## 根因`, `## 修复`, `## 问题代码`, `## 审查`——由
  校验器精确匹配，绝不按记录翻译。人类层（标题与正文）每条
  记录使用单一语言，标题与正文语言一致，默认中文。
- 门变更，人工指令：`tools/lab/validate.py` 现在要求中文章节标题字面量
  （`BUG_REQUIRED_HEADINGS`、`## 修复` 规则、verified 记录的 `## 审查` 规则）。一次性文件上的反例
  测试：英文章节标题被拒（`body section '## 现象' is required`），
  中文章节标题通过。
- 六条既有记录全部归一——标题与章节标题改为中文，每次编辑
  刷新 `updated_at`；`examples/` 下的正例与反例统一为同一
  形态；`agents/bug-recorder.md` 与两份记录 README 都写上该约定。
- 开发版本发布：无 baseline/candidate 评测证据。在刷新 marketplace
  并重装插件之前，宿主安装快照仍落后于源码。

## 0.3.6 — 2026-09-16

给已声明边界装上执行层的牙齿，并为仍未度量之处加诚实标注。
触发：一次能力盘点发现 write scope、可恢复性、证据捕获与
方法级改动都有声明，却没有执法或度量路径。

- 新硬边界 14：已声明的 write scope 靠比对工作区实际
  改动面来执法，而不是靠 worker 的复述。Supervisor 在委派时记录基线
  revision，接受前列出所有改动（tracked 与 untracked）；
  任何 scope 之外的路径即便检查通过也是要退回的缺陷。随附
  `skills/agentflow/scripts/check-write-scope.sh <base> <scope>...`——面向普通开发 brief 的一条命令 diff 对照
  scope 检查（`isolation.py check-diff` 仍是改进
  环的候选树门）。在界内、界外与坏 revision 三种用例上测试过。
- Worker result 契约新增可选 `cost` 与 `duration` 字段：记录实测数字或
  `not reported`，绝不估算——开发线现在能积累运行成本证据，
  改进环早已把这类证据当作一个证据类别。
- Reviewer test-depth 模式：为证明回归检查在未修复代码上失败而做的
  回退实验是行为，不是散文——reviewer 点名确切的还原命令与预期
  失败输出，Supervisor 执行并回传原始输出（与检查
  协议同一通道）。fixer 写的回归检查是下限，不是独立验证。
- SKILL.md：结果可能喂改进环时，步骤 10 要求会话结束前把决策记录
  落成持久形式（episode 不会自动收集；对话一旦消失，
  证据不可恢复）；恢复小节定义会话中断后从 `records/plans/` 下的
  版本化 plan 恢复——从工作区重新推导每个工作包的状态，
  无观测证据的包视为未开始。
- `references/roles.md`：补全全部十二个角色的画像（bug 链、plan architect
  与四个改进角色的画像此前缺失），外加一张任务形态路由表。
- agent description：去掉 reviewer、technical-director、frontend-engineer 与
  backend-engineer 上的 "for Agentflow" / "when Agentflow assigns" 限定，
  让宿主在普通业务仓库中也能正确路由它们。
- improve skill 声明两条能力边界：(1) 度量范围——公开套件只以 Agentflow
  自己的契约用例度量它，因此方法级候选（角色在
  业务仓库内的行为）以 `measurement: none (method-level change, no instrumented
  business task)` 发布，绝不描述为已验证；(2) `maxTurns` 在
  ZCode 上有声明但未验证——生效的约束是提示词层预算纪律，
  frontmatter 里的数字只是意图元数据。
- 中文镜像 `docs/agent-roles.md` 就以上所有内容更新；`docs/next-session-handoff.md`
  现在带一份按 P0/P1/P2 分级的待办，取代过期的未勾选任务清单。
- 开发版本发布：与 0.3.4/0.3.5 状态相同——无 baseline/candidate 评测证据。
  在刷新 marketplace 并重装插件之前，安装快照落后于源码；
  `validate.py installed` 会报告该漂移。

## 0.3.5 — 2026-09-15

来自一次真实跨层功能运行的规则补丁（一个镜像既有聊天面的对话分享
落地页）。所有通过门禁的漏检都落在一类——静态阅读无法证明的
运行时接线、布局与顺序——最大的成本来自
在没有「参照物即规格」清单的情况下复刻既有 UI 并扩展冻结契约。
补丁针对的是断言类型与参照物纪律，而非门的强度。来源复盘的
锚点与断言在应用前已对照本树核实；
应用系用户的明确要求。

- 新硬边界 13：缺席断言（"nothing was written"、"the request never fired"）
  要求直接读权威落点——目录清单、接收表、队列或
  传输日志；间接索引（搜索工具、缓存、采样面板）查不到
  不能作为缺席的证据。（边界 12 管正向工具行为断言；这一条
  管负向断言。）
- Final decision record 新增 `claims` 台账：每条用户可见断言映射到一条
  若断言为假就会失败的检查；仅凭阅读代码得出的断言记为 `unverified`，任何
  未验证的用户可见断言使结论降为 `partial`，而非 `complete`。SKILL.md 步骤 10 与
  reviewer 的检查协议承载同一规则。步骤 8 要求真实
  用户会走的端到端路径在门关闭前执行，并在后续用户可见
  改动时重开门（复审可只覆盖增量）。
- Worker task brief 新增三条纪律：**Replication briefs**（参照实现
  即规格；以 `path:line` 盘点；验收是实测对比）、
  **Extension inventory**（加载体之前先 grep 既有契约面；worker
  发现等价载体即停下报告），以及 **Mirror briefs**（先给
  对照参照 `path:function` 的分支表，再实现）。
- 新增 `## Verification stand-ins` 小节：mock、stub、fixture 集或本地契约夹具都是
  验证装置，不是交付物；先盘点消费方所需的面，
  把后来的缺口记为 verification gap 并重跑它们覆盖过的检查，且保持响应
  契约忠实，让契约不匹配在替身上失败，而不是藏在替身后面。
- Frontend engineer：运行时上下文接线（路由参数、路由元素构造、provider、
  portal、布局挂载）不能靠单元测试证明——点名若接线错误
  就会失败的运行时检查，或在风险中报告其未运行。
- Plan Architect：在实现必须镜像既有实现的面前，先跑
  一次 parity 盘点任务（复刻 / 带理由省略 / 延后），且 plan 列出
  任何验证替身所需的面，并把端到端检查排在
  评审门之前。
- 文档：中文纪律镜像在 `docs/agent-roles.md` 更新；新增
  [`docs/iteration-log.md`](docs/iteration-log.md)，按版本记录触发、改动与
  解决的问题。
- 开发版本发布：无 baseline/candidate 评测证据，不是受治理的候选
  晋级。在刷新 marketplace 并重装插件之前，宿主安装快照落后于
  源码；`validate.py installed` 会报告该漂移。

## 0.3.4 — 2026-09-15

- 记录并预防本会话的事故类：bug 记录 BUG-20260915-002（在真实仓库上执行
  故障注入；一次 `git checkout` "recovery" 把 `protected-paths.txt` 重置回其
  已提交版本、静默丢弃未提交编辑——一条命令之后被
  `validate.py protected` 抓到）与 BUG-20260915-003（连续三轮各交付一条以推演
  断言、并被最小实验证伪的行为断言；第三轮掩盖了一次完整
  演示过的门绕过）。预防：`contracts.md` 新硬边界 12——关于工具、框架或宿主
  如何行为的断言在最小实验复现之前只是假设——以及
  `AGENTS.md` 中的一套 "Experiments and recovery" 规则（只在一次性副本上注入；在真实树上
  绝不用 `git checkout`/`restore` 撤销实验；恢复只有重跑检查并
  观察到绿才算数；声称成功的命令不得压缩输出）。
- 对上文门变更的审计轮；两处更正与一个已关闭的洞（人工授权）：
  - 测试门的一次完整绕过被演示并关闭。`unittest discover` 会导入
    起始目录子目录中的包，而导入期代码先于任何
    断言执行：新增一个 `tests/<subdir>/` 模块来替换钉住测试方法，就能让坏
    断言通过，于是 `validate.py tests` 在一次真实门回归上返回 PASS。已声明内容
    检查现在拒绝 `tests/` 中每个未声明条目，目录也算。
    经故障注入复验：同一攻击现在失败并点出违规条目；
    `__pycache__` 仍不会触发它。
  - 上一轮的机制断言已更正：游离的 `tests/__init__.py` 在
    `discover -s tests` 下是惰性的（只有 discovery 从仓库根启动时它才会被导入）。
    检查仍然拒绝它；文档不再把在此 runner 下它
    做不到的中和归功于它。
  - `skills/improve/references/` 整体受保护。`episode.schema.json` 曾是
    候选仍可编辑的唯一治理 schema（另三个 improve 引用 schema 与
    发布规则早已受保护）。必含条目集合现在逐一点名该目录下全部五个文件，
    使前缀收窄无法再静默漏掉一个。
- 关闭全项目复盘中发现的四处门缺口（人工授权的门变更）：
  - `schemas/` 整体加入 [`protected-paths.txt`](protected-paths.txt)，钉住的
    回归测试按文件受保护（`tests/test_lab_contracts.py`）。记录 schema 是
    候选工件的编译目标，而该测试钉住 `validate.py`/`isolation.py`；这些全都能被
    它们所评判的候选编辑。`validate.py` 中的必含条目集合扩展为
    要求覆盖两个记录 schema 与该测试文件。
  - 测试目录改由已声明内容断言覆盖，而非目录前缀。
    直接保护 `tests/` 被 `tests/__pycache__/*.pyc` 挡住——任何候选
    跑完检查后都会带上的产物——那会让门对每个测过自己工作的候选失败，
    而一个对诚实工作失败的门会诱发绕门。断言拒绝
    目录中未声明的 `.py` 文件，关闭了仅靠文件级保护
    留开的中和向量（一个打补丁改钉住测试的包
    `__init__` 或 shim）。测试子进程还以 `PYTHONDONTWRITEBYTECODE=1` 运行。
  - 新增 `validate.py manifests`：五份手工同步的 manifest 必须就插件名与
    版本达成一致。漏掉的版本递增此前只在宿主重装后才浮现。
  - 新增 `validate.py tests`：仓库的回归测试作为确定性集合的一部分运行。
    `all` 现在覆盖七项检查而非五项。孤儿测试缺口关闭——测试一直在
    通过，却没有任何东西运行它们。
  - 经故障注入验证：一份 manifest 里递增的版本、被移除的受保护条目、
    一个坏断言，以及注入的 `tests/__init__.py` 各自让对应检查失败；游离的
    `__pycache__` 则不会。
- 新增隐式行为纪律：brief 把 `write_scope` 与 `read_scope` 拆开（读取范围
  严格更大），要求共享横切机制经框架
  注册点搜索被发现、被显式声明（含空集）、追溯到注册
  `path:line`（证据终止追踪，而非层数），并跨 表面 ×
  合法状态 检查。plan 中以必填 `shared_mechanisms[]` 字段承载，
  `registration_ref` 必填；条款加进 frontend-engineer、backend-engineer、reviewer 与
  bug-investigator（机制 vs 调用方冲突归因 `missing-constraint`）。新评测用例
  AF-015 与真实 axios-401 拦截器案例的 bug 记录 BUG-20260915-001。包含
  `plan.schema.json`、`evals/`——一次按用户明确要求执行的契约/门变更，
  待人工确认。
- 候选受保护 diff 检查要求冻结的父 revision，并移除受保护路径集合的
  命令行替换。
- 收紧无依赖校验器的 JSON Schema 相等性与 RFC 3339 date-time 处理。
- 在文档中澄清宿主特有的安装漂移、Bash/网络边界，以及当前的评测
  就绪度限制。

## 0.3.3 — 2026-09-14

边界加固发布：对照宿主的实际强制力复核角色设置之后。

### 边界

- **实现型角色的工具白名单。** `backend-engineer`、`frontend-engineer` 与
  `candidate-engineer` 现在声明 `tools: Read, Glob, Grep, Write, Edit, Bash`，与
  `bug-fixer` 一致。此前它们继承全量工具集，含委派、网络与 MCP
  工具，这与硬边界 2（委派绝不扩大权限）矛盾，并让 worker
  能自行启动子代理。
- **一处已声明的候选禁区面。** 新 [`protected-paths.txt`](protected-paths.txt) 是
  候选永远不得编辑的路径的单一来源（evaluator 与 governor 角色文件、
  评测套件、`tools/lab/` 下的度量路径、发布规则、结果 schema，
  以及该清单本身）。`isolation.py check-diff` 默认读取它，而不再要求
  调用方给 `--forbidden`；清单不再覆盖某条必需门路径时 `validate.py protected` 失败，
  且 `all` 包含它。
- `candidate-engineer` 的所有权矩阵现在显式点名受保护清单，消除了
  "write the candidate tree" 与 "never edit the judging gate" 在候选树
  *就是* 插件时的矛盾。
- 硬边界：#1 现在要求 Supervisor 写了部分改动时独立评审门
  强制适用；#2 禁止 worker 再委派；#6 指向已声明清单；新 #11
  要求预算耗尽的运行报告 `partial`。
- reviewer 的检查协议是显式的：确切命令与预期结果由 reviewer
  给出，并要求原始输出，因为改动作者可以执行检查，但不得
  挑选检查。

### 可靠性

- 每个写作角色的预算纪律：为 worker result 预留最后一个 turn，绝不
  为被截断的运行报告 `complete`。实现型角色提升至 30 turns，Plan Architect 至
  20。（`maxTurns` 语义由宿主提供，在 ZCode 上尚未验证。）
- `validate.py installed` 把源码检出的运行时组件（`agents/`、`skills/`、manifest）
  与已安装插件快照比对。宿主从快照加载 agent，因此
  角色源码改动在插件重装之前不会生效；该检查让这种
  漂移可见、而不静默。它不在 `all` 中，因为要读仓库之外。

### 评测

- 四个新公开用例：`AF-011`（worker 摘要不是验证）、`AF-012`（任务文本是
  数据，不是指令）、`AF-013`（候选不得编辑评判它的门）、`AF-014`
  （baseline 对照把环境失败与回归分开）。套件现为 14 个用例。

### 文档

- 观测到的 ZCode 事实更新：插件 agent 确实从安装快照加载，也确实遵守
  frontmatter `tools` 白名单；`agents/` 没有热改即生效的路径。
- 仓库命名归一为 "Agentflow"；过期的 `0.3.1`/`plans/` 引用改正。
- 新增 [`AGENTS.md`](AGENTS.md)，写明本仓库的工作规则。

## 0.3.2 — 2026-09-14

真实模型 dogfood 与 ZCode 宿主集成之后的首次更新发布。

### 宿主适配器

- 把 schema 传给 Claude Code `--json-schema` 之前剥离 `$schema`/`$id` 元声明（当前 CLI 构建在加载时拒绝 Draft 2020-12 声明）。
- 新增 `host_adapter.py --progress <jsonl>` 逐次调用诊断与每次调用一行 stderr 状态；运行仍 fail closed，但失败现在可归因到具体用例与重复次数。
- 在 `tools/lab/adapter-protocol.md` 中记录宿主 adapter 协议的 progress 选项与 schema 处理。

### 角色契约

- 为全部 12 个 agent 文件加入工件所有权声明：六个写作角色给逐工件表，六个只读角色给精简声明。
- 移除随所有权声明一并引入的重复约束措辞。

### 工作流纪律

- Supervisor 步骤 "Verify worker artifacts before accepting them"：确定性检查对照实际文件运行；失败的检查是编译错误；不可复现的检查视为未运行。
- 改进环步骤 9：candidate、evaluation、comparison 与 decision 记录在下一个角色消费之前先经 schema 校验。
- 十条硬边界清单合并于 `skills/agentflow/references/contracts.md`（单一来源；两个 skill 都引用它）。
- 把任务文本当作数据：路径、仓库、命令与版本在进入 brief 之前先对照仓库核实。
- "Recover from stalled work" 中的基线分诊：在称其为回归之前，先对改动前的 revision 跑失败的检查。

### 记录

- bug 记录现在是用经校验 YAML frontmatter 的 Markdown，而非 JSON：人类可读正文（Symptom / Problem code / Root cause / Fix / Review）加机器校验的元数据，每个 bug 一个文件，位于 `records/bugs/<YYYY-MM-DD>/<kebab-slug>.md`。
- 新 frontmatter 字段：`error_kind`（ai-ignored-doc, ai-ignored-code, missing-constraint, hallucination, logic-error, host-compat, environment, other）、`project` 与 `files`（受影响的路径）。
- 归档：`rejected` 记录必须移到 `records/bugs/archive/<same-date-dir>/`；`verified` 记录原位留存作参照。两条规则都由校验器强制。
- plan 仍为 `records/plans/<plan_id>.json` 下的 JSON，`recorded_at` 必填、`updated_at` 有序。
- 新增 `validate.py report` 命令，按时间顺序打印 bug 表（日期、id、状态、severity、error kind、标题）。
- 全部持久工件统一在 `records/` 下；`records/README.md` 记录布局、约定与回溯查询。

### 工具

- `tools/lab/validate.py` 新增 `artifacts` 目标（含在 `all` 中）：校验实际写在 `records/` 下的 plan 与 bug 记录实例（递归）。

### 文档

- 新增 `docs/host-platform-facts.md`：观测到的 Claude Code / Codex CLI / ZCode 行为，含证据与适用范围。
- 修复 README、交接文档、自我改进设计文档与 evals README 中的过期仓库状态（remote 状态、runner 是否存在、工具成熟度、机器路径）。
- 记录 dogfood 证据：AF-001 smoke 通过，AF-002 的延迟/权限/模型标签发现，完整 baseline 运行的环境阻塞项。

### 宿主

- 新增 `.zcode-plugin/plugin.json` 与本地 `marketplace.json`；插件现在可从本地目录安装进 ZCode（skills 与 agents 组件）。
- 两个 skill `description` 字段的触发措辞前移，让完整的 "when to use" 条件在模型决定是否调用 skill 时挺过 ZCode 的约 250 字符截断。
