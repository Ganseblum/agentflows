# Agentflow 整体功能、文档与模板审核（2026-10-23）

审核结论：需要修改。项目的角色分工、文档链、独立评审和确定性校验具备明确用途，适合复杂、跨层、需要追溯的开发任务。主要问题是规则之间存在冲突，部分实施状态与验收结论不一致，模板默认负担偏重，以及安装后必需工具的交付路径没有闭合。建议先修这些问题，再扩充规则或角色。

本次是现状审核，未修改业务规则、角色、模板或检查器。新增本报告并更新索引。下文的“应修改”是审核建议，不代表已实施。P1 表示可能阻断主流程或导致错误判断，P2 表示影响一致性、可维护性或结论可信度；未发现有证据支持的 P0。

## 1. 审核对象、方法和边界

- 审核基线：本地 `HEAD=20c60a30737bf2a0fc3c464f6ada312dd1358598`，同时读取工作树中已有的未提交修改，包括新增 `spec/checklist.md`。本报告不判断远端是否有更新。
- 方法：主审核检查维护工具与验证结果，三名独立审核者分别检查模板、角色工作流和现有文档记录，活文档重点全文阅读，历史记录按状态与引用抽查，再由主审核核对决定性原文。发现均以实际文件为依据。
- 审核期间发现另有写入者持续编辑模板和角色。以下路径、行号指向本次观察到的文本，后续修改可能改变行号；原文摘要用于复核。正在编辑中的问题不等于已发布版本具有同样问题。
- 完整通读：全部 14 个角色及其 README、两个 SKILL、开发与改进 references、全部 24 份 Markdown 模板和 HTML 原型、5 份产品文档。活跃批次的 proposal/spec/design、当前计划及评审证据与维护说明按第7节范围交叉阅读。现有记录经过全量机器校验，历史记录及快照按下列覆盖说明阅读。
- 功能检查聚焦仓内确定性工具；没有执行真实业务仓交付、宿主角色调度、插件重装或浏览器端到端验证，因此不推断这些运行行为已经通过。

| 内容面 | 判断 | 建议 |
| --- | --- | --- |
| 功能边界 | 宿主负责运行、插件负责方法的定位清楚；安装后的检查器定位不完整 | 保留定位，补齐工具交付路径 |
| 角色体系 | 职责分离有价值，存在少量权限与产出职责不一致 | 保留按需调用，先修边界，不按文件数量合并角色 |
| 文档链 | 上下游承接、异常处理、验收依据比较完整 | 统一权威来源及阶段前置条件 |
| 模板内容 | 复杂业务所需内容充分；部分模板示例违反自身规则 | 先纠正矛盾，再按适用条件裁剪 |
| 格式 | Markdown、表格、图、frontmatter 基本统一 | 分离标题与填写说明，减少宽表 |
| 现有文档质量 | 可追溯性较好；进度与验收结论仍会漂移 | 让状态取自任务和验收证据，减少多处手写 |
| 自动检查 | 全套通过；主要证明结构、记录和已编码判据符合要求 | 补齐高价值语义判据，避免把全绿解释成全部功能成立 |

## 2. 应优先修改的问题

### F01 · P1 · 安装后的接入流程缺少必需检查器

证据：`skills/agentflow/SKILL.md:24` 要求在目标项目执行 `python3 tools/lab/doc_chain.py <feature-dir>`；`packaging/build_runtime.py:24` 起的白名单不交付 `tools/`，且把它列为禁止进入运行时的目录。`packaging/README.md:26` 也承认若干链接只在源码检出中可解析。

影响：插件安装用户与新接入的目标仓通常没有这些同名脚本，必需阶段门无法直接执行；把命令写入目标仓 AGENTS 后问题仍然存在。

建议：明确选择一种可执行方案：把可移植检查器及依赖随插件交付，并从插件安装绝对路径调用、用 `--root` 指向目标仓；或者把额外源码检出列为必要前提，给完整定位与调用命令。仅修相对链接不足以解决工具缺失。

### F02 · P1 · 并行失败被直接排除为产品缺陷

证据：`agents/test-executor.md:68` 与 `skills/agentflow/references/roles.md:139` 写“单跑通过、只在全量并行运行中失败”的用例是环境或 flaky 信号，“不是缺陷”。

影响：竞争更新、缓存污染、重复提交等真实产品缺陷可能正好依赖并发条件；这条规则会丢弃关键线索。

建议：改为“单跑通过说明失败依赖并行或共享状态；保留原始并发条件，重复复现，再区分产品竞态、测试相互污染和环境问题”。

### F03 · P2 · 默认计划文件的适用规则不一致

证据：`skills/agentflow/references/document-chain.md:72`、`:81` 使用 `plan/execution.md`，`:75` 又要求新批次统一 `plan/<plan_id>.md`；`:152` 默认复用混合形态。`templates/feature/plan/execution.md:5` 明确自己是“目标仓默认形态”，却无 frontmatter，标题也不同于混合形态精确匹配要求。

影响：默认形态没有唯一入口，不同作者可能选择不同文件名、信封与标题，造成不必要的转换和评审争议。模板已有混合形态转换说明，本次未实测同一文件遭遇相反验收结论。

建议：集中写一张适用表，明确目标仓既有约定、目标仓默认模板、本插件内部混合计划三种情形的文件名、信封和检查命令。把模板转换步骤改成可直接复制的完整形态。

### F04 · P1 · 测试预期被要求取自实现的真实响应

证据：`skills/agentflow/templates/testing/plan.md:52` 及 `references/document-chain.md:401` 写“看不到真实响应就别写预期结果”。

影响：实现之前无法依据冻结规格设计接口用例；实现错误时，也容易把错误响应当作期望。

建议：预期结果引用已冻结 spec、协议或确认结论；真实响应写入执行记录的实际结果。仅在缺少权威契约时阻塞预期定义。

### F05 · P1 · 活跃批次实施先于前置评审门，机器检查未判失败

证据：质量批 `docs/features/feature-2026-10-13-质量提升/README.md:29`、`:36` 两道门仍为 ☐，`:40` 已记 T01–T09 执行完成；追溯批 README 的同类前置门未关闭，而 `plan/PLAN-TRACE-001.md:44` 起已完成实施任务。产品 README 的门语义明确要求前置评审与设计冻结。`tools/lab/doc_chain.py:542` 的 C2 只检查两种门的文字存在，未验证门关闭与实施状态的关系。

影响：当前文件不能证明实施前已满足门条件；结构校验通过仍会容纳“门未关、实现已做”的记录。

建议：先核查是否已有对应阶段的独立评审证据。存在则由有权评审者据证回写；不存在则补审并如实记录执行顺序偏离，不能倒填成事前通过。若加强机器检查，应区分草稿、批准和实施阶段，避免阻断正常起草。此项涉及受保护门，需走人工评审。

### F06 · P1 · 质量批验收结论高于现有证据

证据：质量批 `spec/qa/acceptance.md:66` 要求存活变异为零或逐项豁免，`:97` 明记仍有未关闭项，`:106` 规定 P0 不通过应阻塞，`:110` 却写 M-A 至 M-E 已逐项闭合。最新证据与 `docs/issues/ISS-2026-10-23-变异存活项长期无逐项处置.md` 记录 7 个存活项未逐项处置。

影响：“变异实验执行完毕”被混同为“验收标准全部达成”。存活也不自动证明门失效，需要逐项判断语料缺口、错误变异或真实漏检。

建议：保留实验执行完成状态，把相关验收点标为未满足或有条件接受；每个存活项给处置、依据与复跑结果。本问题已有 ISS-2026-10-23-变异存活项长期无逐项处置 承接，不重复立案。

## 3. 应修改的一致性与功能问题

| 编号 | 问题与证据 | 影响与建议 |
| --- | --- | --- |
| F07 · P2 | `spec/checklist.md:3` 说它是问题唯一登记处，但 `spec/qa/acceptance.md:14` 仍提供 OQ 问题状态表，BE/FE/UI 也保留问题表；集中模板 `:8` 没有阻塞字段 | 关闭状态会出现多个来源。集中表增加阻塞阶段、来源和确认日期；角色反审表保留审计证据并引用集中问题，避免重复维护状态 |
| F08 · P2 | `templates/feature/plan/execution.md:77`、`:103` 要求“待 Coding”引用的补脚本任务已勾选；`:21` 又禁止计划确认前开工 | “待 Coding”既指尚待实施，又要求任务已完成；若评审前必须满足此自检项，补脚本便形成前置循环，规则未明确生效阶段。计划评审时允许引用未完成任务，首次执行命令前再要求完成并回写实际命令 |
| F09 · P2 | `references/document-chain.md:98` 称 spec 是需求事实唯一权威，`:100` 却允许新增事实回到 proposal 或 design | 技术设计可能新增未被需求验收覆盖的业务语义。明确业务事实先确认并回写 proposal/spec；design 新增的是实现决策与代码勘察事实 |
| F10 · P2 | `docs/product/design/product-design.md:22` 已注明仪器裁撤，`:35` 仍把 digest 拒判、seeds fail-closed 当应对，`:59` 架构仍含独立评测与 policy，`:70` 仍列评测与策略职责 | 当前架构包含不在场能力。当前图和职责只列在场能力，退役设计放入有日期的历史说明；旧批次“新增5文件”等叙述注明原批次范围 |
| F11 · P2 | `skills/agentflow/SKILL.md:88` 写父 revision 同样失败就“是环境问题” | 基线也可能有既存产品或检查器缺陷。应只推导“不是本次新增回归”，继续区分既存缺陷、环境和无效检查 |
| F12 · P2 | `docs/quickstart.md:7` 要求前项成立就停，第一项单文件单层直接改，高风险判断在第三项；主 SKILL 要求先判 risky | 单文件权限、持久化或契约变更可能走错路。上手入口沿用主契约判定顺序，完整保留独立评审条件 |
| F13 · P2 | `agents/evaluator.md:18` 强制相同 fixture、重复次数和逐用例不可变对照，`:20` 缺失即 partial 且不得过门；improve SKILL `:37`、`:39` 允许无度量的人工评审晋升 | 当前改进模式没有与之相容的 evaluator 输入分支。明确无度量时如何审查事故证据、假设、diff、确定性检查及人工批准，不把它叫已测量改进；恢复仪器后再强制对照输入 |
| F14 · P2 | `tools/lab/record_store.py:59`–`:70` 仅更新仍存在的文件，从不删除源中已消失的行 | 临时目录已复现：首次索引1条，删除文件后重新索引0条，查询仍返回已删除记录。建议明确定义重建语义，在事务中同步删除失效记录，处理显式根范围变化；数据库仍为可丢弃读侧索引 |
| F15 · P2 | `tools/lab/trend.py:66`–`:80` 的 `open_review_findings` 累加全部历史发现列表，不查询缺陷当前状态 | 已关闭发现仍被计入“open”，同一问题多轮也可能重复。当前函数返回14，而复审 `reviews/agentflow-product-chain/review-2026-10-19-003.md:35` 已明确 F1–F12 全关闭。应改名为历史发现条目数，或按 finding ID 去重并读取状态后统计未关闭项 |
| F16 · P2 | `templates/feature/design/fe/frontend.md:203`、`design/qa/testing.md:11` 允许抓包/debug/spy 三选一；`references/telemetry.md:78` 对发送顺序、双端和去重要求端到端路径或网络日志 | 按模板做 spy 仍不足以通过上位门。字段 payload 可单测，三项流程行为明确补运行时证据并引用统一清单 |
| F17 · P2 | `templates/decision/decision-record.md:5` 约束“状态列”，`:9` 的固定八列却没有状态；`:15` 称七段，brief 实为九段 | 官方模板无法完整表达自身要求。明确八列是必需列还是全部列、状态放哪里，并修正段数；不要默默改门 |
| F18 · P2 | `templates/feature/design/fe/frontend.md:111` 禁止用宽表写算法，紧接着 `:112` 就给七列算法表；`design/ui/visual.md:27`、`:70` 要求变更记录但没有对应章节 | 直接复制会制造不合格文档。算法提供一个完整小节示例，表如保留则仅作索引；UI 模板补变更记录章节 |
| F19 · P2 | `templates/hub/README.md:15` 规定所有内容及链接 `.md` 且“不中英混排”，但官方原型为 `prototype/index.html`，技术标识符须保留 | 接入后即规则冲突。限定叙述性文档采用中文 Markdown，代码、标识符、原型与证据采用原生格式 |
| F20 · P2 | `docs/product/spec/acceptance-matrix.md:11` 把 S2 十步流程写“绿”，检查只是 episode 编译与 review_roundtrips；method-spec 同项承认缺顺序标尺 | 记录存在不等于顺序正确。拆成“记录编译通过”与“流程顺序未验证”，总状态写部分 |
| F21 · P2 | `PLAN-TRACE-001.md:19` 说 T01–T10 完成，`:25`–`:27` 仍说检查集合没有承接与证据判定、随后实现C22 | 同一计划恢复入口给出相反的下一步。进展概览从任务表导出或同步维护，旧基线说明显式标注日期 |
| F22 · P2 | `docs/PENDING-DECISIONS.md:29` 的“现状核验”命令只统计 improve Markdown 数量，再打印字面量“候选与发布记录0份”；变量 ps 未使用 | 命令不能证实决策依据。实际扫描相关记录、打印路径/类型/计数；将“没有活跃载体”和“历史从未存在”区分，保留查证范围 |

补充发现 F23 · P2：质量批 `proposal/prd.md:70` 的 Q-01–Q-04、`spec/qa/acceptance.md:17` 的 OQ 仍待确认，`spec/be/backend.md:69` 仍要求新增 experiment.py；README及PENDING历史记录已记录相关问题的拍板。方案D直接影响M-F及Q-01/Q-03的承接，M-F本期不做；Q-02/Q-04的关闭依据应分别核验，不能用同一个选项概括。保留提案原文，追加决策结果及出处；下游现行规格应明确范围变化，避免接手者重复提问或实现已取消模块。

补充发现 F24 · P2：追溯批 `design/be/backend.md:14` 写 C23 无标记覆盖所有批次，`:15`、`:302`、`:329` 又承诺未打标批次不进入 C23、结果不变，与 `spec/be/backend.md:37` 的适用范围冲突。该设计 `:344` 和 `design/qa/testing.md:43` 仍要求 installed PASS，而 proposal 和 spec/qa 已允许不重装、只声明安装差异。建议按已确认范围统一设计和验证条件；不以修改安装或缩小检查范围来掩盖文档冲突。

低成本的状态修正还包括：`docs/features/README.md:25` 的在途表遗漏追溯批；`reviews/README.md:19` 仍把第9条写成待决，而 PENDING 已记录拍板。产品规格中的旧安装 PASS 属有日期的证据，不应抹掉；建议标明“历史快照，当前请复跑”，并指向 `docs/releases/pending-test.md` 的失效说明。

## 4. 适合精简与优化的地方

这些建议不是当前规则违规，不宜靠一次批量删改实施。

1. **保留角色职责，收敛常用入口。** 默认展示按任务选择的工作链；14角色明细留作按需阅读。不能为了减少文件，合并掉作者与评审、候选与评估、测试设计与执行的独立性。
2. **按能力选择必填章节。** 在 feature 入口集中声明有无界面、持久化、异步流程、外部依赖、埋点与跨部署；据此选择章节。继续保留异常与验收，但减少无关轨道反复填写 N/A。需要改变现行强制规则时，按契约变更处理。
3. **一条信息只维护一次。** 问题状态放集中问题记录，实施状态放任务行，验收结果放验收点，安装状态放带日期的验证证据。其余位置引用或自动聚合。当前回写规则若只许改计划两列，概览就不宜继续手工写实时结论。
4. **标题只放标题。** 将 `<填：...>` 移到正文注释，拆开一行双标题，提供短的完整示例。表格用于索引、映射和比较；算法、失败处理、决策理由用小节表达。
5. **给一份最小完整示例。** 复用现有 examples 目录，覆盖一条小 feature 从原文到验收的过程，展示可省内容、问题引用与证据回写。现有正反例主要服务检查器，不足以教用户估计合理文档体量。
6. **把历史说明从日常入口移开。** SKILL 中反复解释不存在的 execution-coordinator、仪器裁撤与记录根迁移，可集中到一处能力状态说明。README 中特定会话的“2个error”等环境诊断移入有宿主版本、命令与输出的事实记录。
7. **补清角色产出边界。** roles 把 spec/design 的 QA 产出归给 Test Planner，但其文件只允许写 testing 计划；product design 又让只写计划的 Plan Architect 起 spec。明确这些由主会话起草、角色提供只读建议，或正式调整角色写范围。按宿主区分工具白名单的实测强制能力，避免从 ZCode 外推所有宿主。
8. **限制新增流程复杂度。** HISTORY 入口先补完整样例再推荐；统一问题与验收编号说明。评审角色补“现状审核”输入形式，无 diff 时接受固定文件清单与版本。严重度按实际后果定义，避免把所有验收问题都标 P0。

## 5. 建议处理顺序与接受条件

| 顺序 | 范围 | 接受条件 |
| --- | --- | --- |
| 1 | F01–F06：工具交付、错误判断、默认计划、测试预期、评审及验收状态 | 新接入路径有可执行命令；给并发缺陷保留正确出口；官方计划有唯一适用规则；验收结论不高于证据 |
| 2 | F07–F24：问题真源、阶段条件、历史残留与工具错误 | 所有受影响模板与引用同步；索引重建不返回已删除记录；趋势口径与名字一致；现状核验实际计算事实 |
| 3 | 低成本目录和状态回写 | 批次入口、计划、验收与实际证据一致，保留历史日期 |
| 4 | 模板裁剪、入口精简与最小示例 | 用一个小功能和一个复杂功能试填，检查必要内容未丢且重复填写减少，再决定改默认模板 |

门工具、schema、受保护测试和 evaluator 属受保护路径。本报告仅给修改方案，实施前按仓库既有人工评审规则处理。已有未决选择（改进环保留方式、存量批次接入范围）继续以 PENDING 为准，不在本次审核中代替用户拍板。

## 6. 检查结果与解释

首次运行 `python3 tools/lab/validate.py all`：10个子项通过，lint 因当前解释器没有 ruff/mypy 失败，退出1。随后创建临时虚拟环境并按仓内 `requirements-dev.txt` 安装锁定依赖，使用同一工作树重跑全套，所有子项通过，退出0。没有把首轮依赖缺失记成代码回归。

`python3 tools/lab/validate.py installed` 默认检查 ZCode：失败，源码版本0.13.0没有同版本缓存，缓存最高0.12.0。这只能证明所查 ZCode 缓存与当前源码不同，不能推断本次 Codex 会话加载了什么，也不自动授权切换安装。

`python3 tools/lab/counts.py`：退出0，4处标记一致，当前角色14、批次3、schema6、测试方法92。计数只对应本次工作树；测试实际执行以全套检查为准，不用静态方法数代替执行证明。

索引删除复现只在临时数据目录中进行，没有改真实记录或已存在数据库。其原始输出为：

```text
first index count: 1
first query: [('<temporary>/records/gone.md', '# Deleted\\n[uniqueauditmarker]')]
second index count: 0
query after deletion and reindex: [('<temporary>/records/gone.md', '# Deleted\\n[uniqueauditmarker]')]
```

全套检查通过与上述语义发现并不矛盾：例如 C2 目前只要求出现门名称，发现统计只数列表，检查器没有证明每句规则与每项实际功能相符。

## 7. 阅读覆盖说明

- 角色及方法：`agents/*.md` 全部15份，两个 SKILL、agentflow 五份 references、improve 四份 references（含 schema）、五份 manifest、packaging 源码与说明、宿主事实、quickstart。
- 模板：`skills/agentflow/templates/` 全部24份 Markdown（含本次已有未跟踪的 checklist）和 `feature/prototype/index.html`；逐份核对内容、可复制格式与上位契约。
- 当前文档：产品链5份、三个 feature 批次的 proposal/spec/design/plan、批次及类别 README、PENDING、releases 双文件、system-guide、design-decisions、index，以及历史评测报告和复盘的目录、关键结论与本次发现关联章节。现有缺陷记录与评审记录结合状态和引用阅读。
- 代码：主审核检查 validate 入口、gate 检查范围与记录/计划/安装/文档/manifest 判据、doc_chain 的相关规则、打包、isolation、digest、检索、计数和趋势实现。全部现有测试和文档链自测由全套检查运行。没有声称逐行审计每个 Python 分支。
- 历史：episodes、评审归档和 examples 由编译门全量扫描；人工重点阅读与当前结论关联的记录、快照和正反例。没有逐字重审每份历史外部业务文档；不把冻结历史按今天的模板追改。

## 8. 交付复核输出

以下由本报告成稿后的实际命令补入，包含退出码及原始输出。以后工作树变化，须重新运行才能对新状态下结论。

```text
$ /tmp/agentflow-audit-20261023-venv/bin/python tools/lab/validate.py all
exit=0
PASS schemas
PASS examples
PASS artifacts
PASS protected
PASS manifests
PASS docs
PASS tests
PASS doc_chain
PASS doc_chain_live
PASS decision_gate
PASS lint
```

```text
$ python3 tools/lab/doc_chain.py --file docs/evaluations/AGENTFLOW-AUDIT-2026-10-23.md
exit=0
PASS doc-chain --file docs/evaluations/AGENTFLOW-AUDIT-2026-10-23.md
```

```text
$ python3 tools/lab/validate.py installed
exit=1
FAIL installed (1 error(s))
  - ~/.zcode/cli/plugins/cache/agentflow-local/agentflow: no snapshot for source version 0.13.0; installed versions: 0.11.0, 0.12.0, 0.8.2, 0.8.4, 0.8.6. Refresh the marketplace and reinstall — source edits do not reach the installed copy, so role behavior still comes from the stale snapshot.
```

```text
$ python3 tools/lab/counts.py
exit=0
计算值：tests=92  schemas=6  agents=14  batches=3
OK：标记共 4 处，全部与计算值一致。
```

独立复核：模板审核者返回 `changes_requested`，指出F03影响表述过强、F08前置循环需限定条件；正文已按意见收窄。记录审核者补读两个活批次全部设计与提案后确认F05/F06/F21/F22，并补充F24。最终增量复核为 `approved`、`status: complete`，范围仅是本报告与索引。非阻塞意见要求区分F23不同问题的决策依据，已在正文说明。此批准不代表被审核项目的问题已经修复。

最终复核后的重跑：

```text
$ /tmp/agentflow-audit-20261023-venv/bin/python tools/lab/validate.py all
exit=0
PASS schemas
PASS examples
PASS artifacts
PASS protected
PASS manifests
PASS docs
PASS tests
PASS doc_chain
PASS doc_chain_live
PASS decision_gate
PASS lint
```

最终复核后的重跑：

```text
$ python3 tools/lab/doc_chain.py --file docs/evaluations/AGENTFLOW-AUDIT-2026-10-23.md
exit=0
PASS doc-chain --file docs/evaluations/AGENTFLOW-AUDIT-2026-10-23.md
```

## 9. “全部改一下”后的实施状态

本轮已按可直接编辑的范围处理以下问题：F02、F03、F04、F07、F08、F09、F10（当前架构及裁撤能力说明）、F12、F16、F17、F18、F19、F20、F21、F22、F24；同时修正 F23 的现行规格范围，并更新活跃批次入口及已决定事项的链接。F06 已把变异存活项改成明确阻塞验收，未把实现完成当作全部通过。更新 `packaging/runtime` 生成快照，使其与源码一致。

以下事项仍未关闭：

- **F01**：检查器仍不在安装快照里。`packaging/build_runtime.py` 与交付白名单属于受保护路径；本轮未更改打包门，需先评审并决定将检查器纳入运行包，或正式规定源码检出为执行前提。
- **F05**：活跃批次的需求与设计阶段评审门仍未勾选。本轮只澄清批次状态、修正追溯批进度概览；没有独立评审证据，不能代替 Reviewer 关闭该门。
- **F11**：基线错误分类规则位于已有未提交修改的 `skills/agentflow/SKILL.md`，本轮未覆盖他人修改。
- **F13**：`agents/evaluator.md` 是受保护角色文件；无度量评审输入模式仍需经人工评审后修改。
- **F14–F15**：`record_store.py` 与 `trend.py` 是受保护工具，本轮未改门工具。索引陈旧记录的复现和趋势统计语义问题仍在。
- **F23**：已在活动规格标明 M-F 本期不做，并按验收证据更新状态；Q-02 与 Q-04 的独立决策依据尚未逐条校准，不能统一推断为同一方案关闭。

仓库规则将 `tools/lab/`、evaluator 角色和 `packaging/build_runtime.py` 等列为受保护路径，要求候选先提交方案并经人工评审；此外阶段评审门只能由独立评审勾选。因此这些项需要相应门的评审证据，不能由同一作者在本次修订里自我关闭。

本轮最终复核：`/tmp/agentflow-audit-20261023-venv/bin/python tools/lab/validate.py all` 退出码 0，11 项全部 PASS；两个活跃批次分别运行 `python3 tools/lab/doc_chain.py <批次目录>` 均 PASS。`python3 tools/lab/validate.py installed` 仍退出码 1，原因是 ZCode 没有源码版本 0.13.0 的快照，已有版本最高为 0.12.0；这项需要实际刷新并安装后重验。`python3 tools/lab/counts.py` 在本轮运行时显示 14 个角色、3 个批次、6 个 schema、92 个测试方法，4 个文档计数标记一致。
