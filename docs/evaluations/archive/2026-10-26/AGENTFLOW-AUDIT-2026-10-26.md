# Agentflow 仓库整体审核报告（2026-10-26）

> **评测者**：主审（本次审核的发起会话）派发四个只读子代理——R1 架构与治理（D1/D6/D7/D9）、R2 门禁与代码（D2/D3/D4/D10）、R3 契约与记录（D5/D8/D11）、R4 定位与竞品（D13）。四者独立上下文、并行执行。
> **被审核 revision**：`ef7da3f`（`git status` 干净，基线时间 2026-10-26T15:38:54+08:00）
> **模型**：`zcode / new-provider:cn:step-5-preview`（主会话与四个子代理同一宿主、同一模型；观察标签即本次审核所报告模型的标识，未经网关转换）
> **来源 revision**：`agentflows@ef7da3f6b3a05cd3547e53b922d28da89054437a` + 工作树（审核期间无写入者）
> **recorded_at**：2026-10-26T16:04:18+08:00
> **方法**：宿主支持并行子代理，四个角色真并行；每角色只发该角色的任务书与铁律。
> **声明**：本报告未修改被审核仓库任何文件；所有变异与故障注入均在 `/tmp` 的 `cp -r` 副本上进行。审核前后 `git status --porcelain` 均为空、HEAD 始终为 `ef7da3f`。

---

## 〇、总览

### 十二维分数表

| 维度 | 分数 | 一句话锚定 |
|---|---|---|
| D1 架构与设计一致性 | **8/10** | 五面分离在代码层与文档层双向验证成立，fail-closed 有实跑证据；三条 P2 全是口径/漂移面 |
| D2 门禁有效性（×2） | **8/10** | 25 个变异中 19 个抓住，schema 词汇表闭集走查零漏；lint 口径矛盾、测试下限过松、自测计数可向上谎报、负例钉不住目标判据 |
| D3 代码质量与安全 | **7/10** | 38 个异常 handler 全 typed、零注入面；一条真实 fail-open（不可读的违约文件静默通过 decision_gate） |
| D4 代码工艺与可读性 | **8/10** | 注释解释「为什么」且带审计编号，是本仓最突出优势；两个函数复杂度异常点 + tests/ 31 处未用导入 |
| D5 Agent/Skill 契约质量 | **8/10** | 14/14 frontmatter 一致、路由表可解析、schema 无漂移；三条未立案矛盾均已有计划任务号 |
| D6 结构合理性 | **8/10** | 引用矩阵无环、5 个常见任务 1 跳可达、零 `.gitkeep` 空壳；`.workbuddy/` 未登记造成可发现性缺口 |
| D7 逻辑链路 | **7/10** | 主流程闭环、缺陷链四角色边界成对；门 6 链路收口通读是死条款、canary/automatic 只进不出 |
| D8 文档与记录活性 | **8/10** | 索引计数机器对齐、记录面持续更新、看板算术 3/3 自洽；C23 对「证据列无载体」仍瞎 |
| D9 治理与发布闭环 | **7/10** | `measurement: none` 被 schema 机器强制、角色分离诚实自承「非环境隔离」；两份改进契约零真实记录被编译 |
| D10 安全与权限边界 | **7/10** | 候选隔离确要求受信检查器根且机械强制；写范围执法器不在任何自动路径上 |
| D11 实现的效果 | **7/10** | 61 条 ISS 中 40 条 verified 且四字段零缺失、47 轮评审 25 轮 changes_requested；改进环 0 候选、反馈闭环最后一环不可见 |
| D13 竞品比对 | **8/10** | 覆盖 8 个对比对象、每条带来源与检索日期；真实空白在「记录必须可复核 + 机器拒绝自改门」 |

### 综合分

- 十二维算术平均（D2 计一次）：**93 / 12 ≈ 7.75**
- **D2 计两遍（门禁是本仓自声名的地基）：101 / 13 ≈ 7.77**

**一句话裁决**：这是一套**门真实有效、记录真实可复核、自我披露诚实**的工作流插件——「确定性门 + 记录即编译」两个核心主张经本轮实跑与变异实证成立，且相对 2026-10-20 的上一轮评测（同口径 7.7）在门项计数漂移、归档死条款、CHANGELOG 计数不实三处已有实质修复；剩余硬伤集中在**「该在场的东西是否在场」这一类门尚未泛化**（死条款、零实例契约、未登记目录），以及三处口径双源（lint、T09 证据基准、测试下限）。**综合 7.8/10，属「主体扎实、已定位硬伤、每条有解锁路径」档。**

### 对四个问题的直接回答

1. **门和契约是否真的抓住声称的违规？** 机械级：**是，且边界比上轮更清**。25 个变异实验中 19 个让门变红，schema 未实现关键字被闭集拒载（M1），`isolation.py check-diff` 在 10 个边界场景全部 fail-closed，`measurement: none` 禁 `better` 由 schema `allOf` 结构保证（构造记录实证）。但有 4 个变异**没有**让门变红，其中两个是真缺口：自测计数可向上谎报（M9a/M9d 报 `200/200` 仍 PASS）、负例钉不住它名义上钉的那条判据（M22 改掉状态词仍 PASS）。另有 2 个是已声明的设计（CHANGELOG 豁免 token 扫描、mermaid 算内容），不算缺口。提示词级：`write_scope` 靠主审记得跑 `check-write-scope.sh`——全仓非注释调用点为 0。
2. **结构与链路是否合理、是否闭环？** 五面分离真实、引用矩阵无环、可发现性 5 任务均 1 跳（优于 3 跳要求）。闭环有三处缺口：门 6「链路收口通读」是死条款（文本定义 + 四个批次/六份计划/43 个 episode 零命中 + 无机器判据）、改进环 canary/automatic 有入口无出口且 `automatic` 在 `measurement: none` 下**结构上不可能通过**、计划审批 `proposed→approved` 边在主工作流十步里无落点。
3. **实际跑出什么效果、为何值得存在？** 61 条 ISS 中 40 条 verified 且四类必填字段零缺失（不是只改状态字）；47 轮独立评审中 25 轮 `changes_requested`，每轮带逐字 finding 与 resolution；7 份 `partial` 负向 episode 在场，其中一条主动标 `failed` 否证自己的合并提交；变异测试 58 项的仓内 JSON 载体与计划行声称逐项对上。**确有可验证疗效**。但改进环 0 候选 0 发布记录，其发布门的运行时正确性无证据。
4. **核心差异点兑现到哪一步？** 确定性门**充分兑现**（本轮 25 个变异实证）；记录即编译**基本兑现**（C23 证据在场是活的，但 G05 显示它对「证据列全是裸配置片段」这一形态仍瞎）；受治理发布**兑现为人工批准 + git hook 承担发布前强制**，治理角色的晋升判定当前无输入。

---

## 一、发现总表（按严重度排序）

> 完整逐条证据在对应维度节；本表是唯一的编号与状态权威。**P0 = 阻断主流程或让错误结论通过门；P1 = 可能导致错误判断或主流程某步无法执行；P2 = 影响一致性/可维护性/结论可信度；P3 = 记录性、可延后。** 本轮无 P0。

| # | 严重度 | 发现 | 位置 | 解锁条件 | 整改状态 | fix_revision |
|---|---|---|---|---|---|---|
| G01 | **P1** | CHANGELOG 的 lint SKIP 声称在 `validate.py` 本身不成立，两个口径并存 | `CHANGELOG.md:7,:42`；`validate.py:250-282` | 选定 (a) 让 validate.py 也 SKIP 或 (b) 改 CHANGELOG 措辞；均需人工评审 | 已修 | CHANGELOG.md:86 逐字勘误（方案 b）；validate.py 保持 fail-closed |
| G02 | **P1** | `docchain/checks.py:1142` 对不可读文件 fail-open：`chmod 000` 使 8 findings 变 PASS | `checks.py:1141-1142` | 改为 append finding（与 `doc_chain_live` 同构）+ chmod 000 夹具 | 已修 | tools/lab/docchain/checks.py:1314 改为 append finding，注释引 G02 |
| G03 | **P1** | `templates/feature/plan/execution.md` 照抄产出必被本仓门拒 | `execution.md:14` vs `gate/plan.py` 的 `PLAN_REQUIRED_HEADINGS` | 模板改混合形态标题，或 plan 门接受编号族；补「抄模板→跑门→PASS」夹具 | 已修 | ISS-2026-10-27-计划模板验证标题不匹配 verified：改模板标题不放宽检查器 + 新增照抄模板回归 |
| G04 | **P1** | `test-records.md` 与 `test-executor.md` 对「能否编辑已写执行记录」给出矛盾指令 | 两处逐字相反 | 统一为「executor 不编辑自己的记录」；`test-records.md` 改为指针引用角色档案 | 已修 | test-records.md:36-38 改为指针引用角色档案，与 test-executor 同向 |
| G05 | **P1** | C23 对「证据列无载体」判绿 | `PLAN-PRODUCT-001` T07 证据列无四类载体仍 PASS | `evidence_carriers` 加反向判据；T07 行补载体或 `N/A: 理由` | 已修 | C23 反向判据证据列空/无载体即红（docchain/checks.py:413,1077） |
| G06 | **P1** | 门 6「链路收口通读」是死条款：文本定义 + 四批次/六计划/43 episode 零命中 + 无机器判据 | `document-chain.md:232-250`、`roles.md:24-26` | 加记录载体 + opt-in C25（打标即承诺）；属门变更需人工评审 | 已修 | C25 链路收口标记落地（docchain/checks.py:108）+ 定义处 document-chain.md:286 |
| G07 | **P1** | canary/automatic 只进不出，且 `automatic` 在 `measurement: none` 下结构上不可能通过 | `improve/SKILL.md` 步骤 13 + `release-record.schema.json` 的 rollout.mode | 三处载体各加「当前不可达」标注；构造 automatic 记录实证被拒 | 已修 | improve/SKILL.md 两处标注 canary/automatic 当前不可达 |
| G08 | **P1** | 写范围执法器不在任何自动路径上：非注释调用点 = 1 且是「保护它自己」 | `check-write-scope.sh` | 接入 pre-push 或 CI（需评估误报面），或显式登记为已声明未缓释 | 已登记待拍板 | PENDING-DECISIONS 第 11 条：登记为已知人工步骤，不自动接入 |
| G09 | **P1** | `verified` 的 `closure_criteria` 行号会过期且无门看守 | ISS-2026-09-20-先写契约后核实平台约定 声称 284-286，实为 387-389 | 记录侧改「条款名 + 路径」；门侧加弱校验或登记为 C17 扩展 | 已修 | ISS-2026-09-20-先写契约后核实平台约定 closure_criteria 改为条款名+路径，不再引行号 |
| G10 | **P1** | 两份改进契约零真实记录被编译；改进环四角色边裁撤后零走通 | 候选/发布记录文件数 = 0 | `examples/` 下为正反例各放一对并登记进 `INVALID_EXAMPLES`；todo.md 含现状行 | 已修 | 4bb29dc：examples/ 补候选与发布记录正反例，门钉 none⇒not-better |
| G11 | **P1** | `.workbuddy/` 是未登记的活目录：gitignore 但盘上多份 md，活文档零提及 | `.gitignore:14` | 删除 / 冻结并登记 / 标注为非权威，三选一需用户确认 | 已修 | index.md:35 登记 .workbuddy 为非权威草料区 |
| G12 | **P2** | 自测计数可向上谎报：摘要改 `200/200` 或硬编码 `110/110`+`ok=True` 均 PASS | `gate/checks.py:135-164` | 从输出结构（逐条结果行数）交叉验证 N | 已修 | gate/checks.py:183-194 逐案 PASS/FAIL 行数交叉验证，注释引 G12 |
| G13 | **P2** | 负例钉不住它名义上钉的那条判据 | `gate/examples.py:118-120` | `INVALID_EXAMPLES` 加「必须出现的错误子串」字段 | 已修 | gate/examples.py:138-150 钉到 measurement:none⇒not-better 精确路径 |
| G14 | **P2** | 单元测试下限过松：清空 4 文件（消失 51.6%）仍 PASS | `gate/common.py:127` `MIN_UNIT_TEST_COUNT = 20` | 下限提到与稳态同量级，或改为逐文件至少 1 个测试 | 已修 | gate/checks.py:106-119 逐文件下限（每文件≥1 test），注释引 G14 |
| G15 | **P2** | 安装树 6 条相对链接断链，`manifests` 门不扫 | `packaging/runtime/` 内 6 处跨树引用 | 改仓限定地址或纯文字；manifests 加链接可解析断言 | 已修 | packaging/runtime 断链扫描 0 条（本批实测） |
| G16 | **P2** | 质量批门状态双源：README 两道门 `☐` vs 元信息/发布索引「approved」 | 质量批 README 第 3/5 节 vs 其元信息节 vs `docs/releases/todo.md` 第 1 行 | 两道门改 `☑` 并附 reviews 相对链接 | 已修 | 质量批 README 门状态改为 ☑ 并附 reviews 链接 |
| G17 | **P2** | 幽灵类名勘误未追平：两个类名全仓 12 处 / 8 处命中，部分无勘误标注 | `review-2026-10-19-001.md:43,122` 等 | 按 PLAN-REVIEW-001 T16 落成 gate 检查 | 已修 | 4bb29dc 追平幽灵类名勘误标注（7 处带勘误） |
| G18 | **P2** | 批次完成率换分母：README 7/12 vs 看板 7/14；5/9 vs 10 行 | `PLAN-PRODUCT-001` / `PLAN-LOOP-SMOKE-001` | 两处改为同一组数字 | 已修 | PLAN-PRODUCT/LOOP-SMOKE 批量改分母与看板同组数字 |
| G19 | **P2** | 凭据值形状无机器检查：`credentials: "sk-xxx"` 通过 schema | `schemas/test-{plan,run}.schema.json` | 加 pattern 或形状扫描（schemas 在保护面，需人工评审） | 已登记待拍板 | PENDING-DECISIONS 第 12 条（受保护面门变更，待用户选 A/B） |
| G20 | **P2** | 13/24 个 C 检查无 mutate 变异项，C17 最薄 | `mutate.py:63-116` | 为 C17 加 1–2 个变异项 | 已登记待拍板 | PENDING-DECISIONS 第 13 条（C17 变异项，受保护面） |
| G21 | **P2** | `trend.jsonl` 四版本未更新；`pending-test.md` 安装面行陈旧 | 末行 unittest_count 89 vs 实跑 92；pending-test 写 0.15.0 | 跑一次 `trend.py --append`；pending-test 改指针式写法 | 已修 | trend.jsonl 已刷新；pending-test 改指针式写法 |
| G22 | **P2** | README:63 环境假红注记指向 `tests`，本机可复现的红项是 `lint` | `README.md:63` | 按实况改写，两处都写并各给复现命令 | 已修 | README.md:67/:69 拆成两条注记并各给复现命令 |
| G23 | **P2** | 安装面带门清单副本但安装校验不覆盖它 | `build_runtime.py:41-44` vs `gate/common.py:153-159` | 纳入 `INSTALLED_FILES`，或从 runtime 移除 | 已修 | gate/common.py:159-166 INSTALLED_FILES 已含 protected-paths.txt |
| G24 | **P2** | 四个 shell 脚本硬编码十项目标清单，与 `--list` 十一项双源 | `pre-push.sh:38` 等四处 | 改为解析 `--list` 输出 | 已修 | pre-push.sh:147 改为解析 --list，且校验待推送提交 |
| G25 | **P2** | `tests/` 31 处未用导入 + 1 个孤儿 `.pyc` | `tests/__pycache__/test_lab_contracts.cpython-312.pyc` 源文件已不存在 | 删导入（受保护文件需人工授权）+ 删孤儿 pyc | 已修 | 4bb29dc 清未用导入与孤儿 pyc |
| G26 | **P2** | T09 证据列双基准：仓根路径不在盘，靠 C23 双根解析 PASS | `PLAN-QUALITY-001` T09 证据列 | 改写为批次内完整路径或仓限定写法 | 已修 | PLAN-QUALITY-001 T09 证据列改批次内完整路径 |
| G27 | **P2** | 计划审批边在主工作流无落点：`proposed→approved` 边无对应步骤 | `SKILL.md` 步骤 3 | SKILL 步骤 3 补输入/输出契约 | 已修 | SKILL.md 步骤 3 已补计划批准为显式一步 |
| G28 | **P2** | `rejected` 归档边零触发：目录不存在、记录 0 条、动作未演练 | `docs/issues/README.md:11-13` | `/tmp` 副本跑一次归档演练并把结论写进 README | 未修 | docs/issues/归档/ 仍不存在；README:11 保留规则 |
| G29 | **P2** | 「建议值草案」过渡态是死条款：定义在盘，记录零发生 | `document-chain.md:217-221` | 在计划形态节加一句让它有记录入口 | 已修 | document-chain.md:248 建议值草案已有记录入口 |
| G30 | **P2** | `system-guide.md`/`index.md` 内部词裸用：`台账` ×17 等 | 对照 `AGENTS.md` 表达纪律 | 按 PLAN-REVIEW-001 T23 对照词表清零 | 已修 | system-guide.md:18 术语对照表；index.md:4 加指针对齐 |
| G31 | **P3** | `validate_workspace_artifacts`（331 行 / CC 119）与 `lint`（266 行 / CC 129）是复杂度异常点 | `gate/workspace.py:41`、`docchain/checks.py:277` | 拆分或降复杂度；两者均有充分行内注释，不阻塞 | 未修 | workspace.py:41 与 docchain/checks.py:429 复杂度未拆（P3） |
| G32 | **P3** | `TASK_STATUS` glyph→词映射两份拷贝（有注释标注同步义务） | `gate/plan.py:47-50` vs `docchain/constants.py:157-163` | 单源化；当前未漂移 | 未修 | gate/plan.py:47-50 与 docchain/constants.py:170 仍双拷贝（P3） |
| G33 | **P3** | 9 个返回 bool 的函数不带 `is_/has_` 前缀；`doc_chain.py` 是唯一不用 argparse 的 CLI | D4 抽样 50 | 统一命名惯例；不影响正确性 | 未修 | bool 命名惯例未统一（P3） |
| G34 | **P3** | 成本收益缺对照组：「不用 agentflow 需要多少成本」未实测（原 D12 子项，该维已删） | 已删维度的遗留项 | 若要恢复存在意义维度，先补一次同题对照 | 已登记待拍板 | PENDING-DECISIONS 第 14 条：成本对照协议登记，实验待跑 |
| G35 | **P3** | 三条竞品论断缺可核查来源：BMAD agent 数量、LangGraph 图原语、superpowers hooks 事件类型 | D13，已如实标注「页面未指定」 | 补检索或明确标注为「未核实」并说明影响 | 未修 | 三条竞品论断缺来源仍如实标注「未核实」（P3） |

---

## 二、D1 架构与设计一致性（8/10）

**意图卡片**：职责=以「宿主原生多 agent 工作流」形态交付可移植范式，宿主即运行时；自述契约=五面分离、无第二套 CLI、fail-closed 贯穿工具层、版本单点声明；消费者=三个宿主的 agent 与人。

**亮点（证据）**
- 五面分离在代码层不可能被破坏：Python 源码只分布在 `packaging`（7 个）与 `contract`（31 个），记录面与文档面**不含任何 `.py`**。
- 「无第二套 CLI」有全仓入口点扫描支撑：所有 `argparse`/`sys.argv` 都在门工具与打包脚本内，无业务编排 CLI/TUI/MCP server。
- fail-closed 到 schema 工具层有实证：`gate/schema.py:286` 白名单 + `:351` 位置级走查，注入 `exclusiveMinimum` 立刻 `FAIL schemas`。
- 版本散文守卫真实生效：`gate/docs.py:47-53` 对 README 与 design-decisions 逐字匹配 `x.y.z`，两文现均无版本字面量。

**硬伤（证据 + 触发条件）**
1. **P2 · 安装面携带门清单副本，安装校验不覆盖它**：`packaging/build_runtime.py:41-44` 的 `RUNTIME_FILES` 含 `protected-paths.txt`，但 `gate/common.py:153-159` 的 `INSTALLED_FILES` 只列五份 manifest。安装树的清单漂移时 `installed` 不报。
2. **P2 · README:63 的环境假红注记指向 `tests` 子项，本机可复现的红项是 `lint`**：注记说「tests 报 2 个 error」，实跑是 `FAIL lint (2 error(s))`。排障方向被误导。
3. **P2 · 四个 shell 脚本各自硬编码十项目标清单，与 `validate.py --list` 的十一项不是同一真源**：`pre-push.sh:38`、`publish.sh` 第 3 步、`upgrade-codex.sh`、`upgrade-zcode.sh` 逐字重复。新增门项时脚本不会跟着变。

---

## 三、D2 门禁有效性（8/10，权重 ×2）

**意图卡片**：职责=验证「确定性检查门」真能拦违规；自述契约=11 项检查、schema 闭集、isolation fail-closed、protected 双向自证；消费者=接受产物的人。

**实跑**：`validate.py all` → 11 项，10 PASS + `FAIL lint`（环境缺失）；`--list` 自报 11 项；`doc_chain.py --self-test` → `110/110`；`unittest` → `Ran 92 tests` / `OK`。

**25 个变异实验（副本 `/tmp/gw_mut/repo`）**：19 个让门变红，4 个没有，2 个是已声明设计。

| 变异 | 结果 | 性质 |
|---|---|---|
| schema 加 `exclusiveMinimum` | `FAIL schemas` exit 1 | 抓住 |
| ISS 状态改非法值 | `FAIL artifacts` exit 1 | 抓住 |
| manifest 版本改坏 | `FAIL manifests (3 errors)` exit 1 | 抓住 |
| 从 protected 删条目 | `FAIL protected` + `blocked` exit 1 | 抓住 |
| README 引入断链 | `FAIL docs` exit 1 | 抓住 |
| README 加版本字面量 | `FAIL docs` exit 1 | 抓住 |
| README mermaid 内加退役 token | `FAIL docs` exit 1 | 抓住（mermaid 算内容） |
| CHANGELOG 加退役 token | `PASS docs` | **已声明设计**（`HISTORICAL_DOC_CARRIERS` 豁免） |
| tests 新增文件 / 子目录 | `FAIL tests` exit 1 | 抓住（挡导入期劫持） |
| runtime 版本/内容漂移 | `FAIL manifests` exit 1 | 抓住 |
| protected 加不存在路径 / `..` 逃逸 | `FAIL protected` exit 1 | 抓住 |
| isolation 十场景（`-` base、坏 base、嵌套、中文路径、忽略文件…） | 全部 fail-closed | 抓住 |
| **清空 4 个测试文件（剩 30 tests）** | **`PASS tests`** | **缺口 G14** |
| **自测摘要谎报 `200/200`** | **`PASS doc_chain`** | **缺口 G12** |
| **负例状态词改成合法值** | **`PASS examples`** | **缺口 G13** |
| 测试打印假 `skipped=5` | `FAIL tests` | 抓住（机制可被单方面弄红） |

**失效模式 / 扣分项**
- **H1（P1）lint 口径矛盾**：CHANGELOG 0.17.3 与 0.18.2 声称「缺 dev 依赖时输出 SKIP 并放行，可用 `AGENTFLOW_LINT_PYTHON` 实跑」。该声称**只在 4 个 shell 脚本里成立**；`validate.py` 本身无 `AGENTFLOW_LINT_PYTHON` 代码路径（`tools/lab/` 下 0 处命中）、无 SKIP 分支，缺依赖即 `FAIL lint` + exit 1。push 前放行、本地 `all` 必红，两个口径并存。
- **H2（P2）测试下限过松**：`MIN_UNIT_TEST_COUNT = 20` 对 92 的稳态，清空 4 个文件（消失 32/62 = 51.6%）仍 PASS。注释自称「far above a trivial suite」不成立。
- **H3（P2）自测计数可向上谎报**：`gate/checks.py` 只校验 `passed != total`、`total == 0`、下界。谎报 `200/200` 或硬编码 `110/110` + `ok=True` 均 PASS。
- **H5（P2）负例钉不住目标判据**：`gate/examples.py:118-120` 只断言「该文件被拒」，不断言「被它名义上钉的那条判据拒」。改掉状态词后仍因其它违约被拒，`TEST_RESULT_STATUSES` 的钉住作用静默消失。

---

## 四、D3 代码质量与安全（7/10）

**意图卡片**：职责=`tools/lab/` 各工具的真实 bug/异常逃逸/fail-open/注入/非 ASCII；自述契约=异常 typed 且转化或重抛；消费者=CI 与主审。

**亮点（证据）**
- 38 个异常 handler 全部 typed，**0 个裸 `except:`、0 个 `except Exception`**；转化模式全域统一。
- 20 处 `subprocess.run` 全部 `shell=False` + 列表传参；唯一字符串拼接进 argv 的两处分别由 `SHA_RE` 与 `--` 分隔符保护。**无注入面。**
- 非 ASCII 在两条路径都正确：`isolation.py:120-121` 用 NUL 分帧 + surrogateescape；`check-write-scope.sh` 实证中文路径、空格路径、删除文件、被忽略文件全部正确处理。
- 覆盖真相：5 个测试文件全部被测、全部被 `validate.py tests` 运行，无包装后 0 引用；`mutate.py` 52 个门检查项中 49 个有变异。

**硬伤（证据 + 触发条件）**
- **P1 · `docchain/checks.py:1141-1142` 的 `except OSError: continue` 是真实 fail-open**：实证一份含 8 条 C16 违约的决策记录，可读时 `FAIL decision-gate (8 findings)`，`chmod 000` 后 `PASS decision-gate`、exit 从 1 变 0。**违规文件越不可读，门越绿。** 同仓的 `doc_chain_live` 路径同场景是 fail-closed 的（`gate/checks.py:272-273` 补 finding）——团队知道正确写法，只是漏了一处。
- **P2 · 13/24 个 C 检查无 mutate 变异项**，其中 C17 覆盖面最薄（自测 0 条、回归测试仅一条）。
- **P2 · `tests/` 31 处真未用导入**，是 0.15.0 按面拆分时复制 import 块的残渣。

---

## 五、D4 代码工艺与可读性（8/10）

**意图卡片**：职责=好不好读、好不好改；自述契约=命名自解释、注释解释为什么、无死代码；消费者=后续维护者。

**亮点（证据）**
- **注释质量是本仓最突出的工艺优势**：几乎每条非显然取舍都带审计编号与日期——`isolation.py:122-127`（G06 由来）、`docchain/checks.py:196-206`（C15 为何不用闭集启发式 + 真实洪水案例）、`:736-738`（C17 日粒度的「数学上不可能同日转绿」由来）、`gate/examples.py:49-54`（大小写 glob 静默漏负例）。
- TODO/FIXME/XXX/HACK 全仓 1 处，且是历史陈述（`gate/common.py:125`）而非待办。
- 死代码生产面 0 个；`validate.py` 的大量 re-export 是显式声明的测试兼容面（文件头 `# ruff: noqa: F401` + `_RootAwareModule` 注释）。

**硬伤（证据 + 触发条件）**
- `gate/workspace.py:41 validate_workspace_artifacts`（331 行 / CC 119）与 `docchain/checks.py:277 lint`（266 行 / CC 129）是真实复杂度异常点——但两者都有充分行内注释解释每个分支，属「为可读性付出过努力的长函数」。
- `TASK_STATUS` glyph→词映射在 `gate/plan.py:47-50` 与 `docchain/constants.py:157-163` 两份拷贝（有注释标注同步义务，仍是漂移风险）。
- 9 个返回 bool 的函数不带 `is_/has_` 前缀；`doc_chain.py` 是唯一不用 argparse 的 CLI。

---

## 六、D5 Agent/Skill 契约质量（8/10）

**意图卡片**：职责=14 角色 + 两 SKILL + references + templates + schemas 的交叉一致性；自述契约=frontmatter 名=文件名、工具面与正文互证、判断词可判定；消费者=宿主路由 + 派发者。

**亮点（证据）**
- 14/14 frontmatter `name` == 文件名；五个只读角色的 `disallowedTools` 与正文「对一切只读」互证；`test-executor` 的 `disallowedTools: Edit` 与正文「只写新建的执行记录」精确对应。
- SKILL 引用的 `agentflow:<role>` 全部可解析（差集为空）；improve 13 步与 `release-record.schema.json` 的 `allOf` 逐字对应。
- schema 无重复定义：`skills/improve/references/` 三份与 `schemas/` 六份求交为空，9 份 `$id` 全唯一。
- templates 无断号，固定标题契约完整；telemetry「十条」是编号清单不是散文注水。

**硬伤（证据 + 触发条件）**
- **P1 · `templates/feature/plan/execution.md` 照抄产出必被本仓门拒**：`:14` 写 `## 0. 分支策略`，而 `gate/plan.py` 的 `PLAN_REQUIRED_HEADINGS` 只认 `## 进展概览`/`## 任务清单`/`## 验证命令`。目标仓用户照抄模板填完跑 `doc_chain.py` 会因缺节而红。该问题 2026-10-20 评测已记录为「未立案」，至今 6 天。
- **P1 · `test-records.md:36-37` 与 `agents/test-executor.md:21-25` 对「能否编辑已写执行记录」给出矛盾指令**：一条让 executor 自己改并刷新 `updated_at`，另一条禁 Edit、要求交给主审。两条同时生效时执行者无所适从。
- **P2 · 安装树 6 条相对链接断链，`manifests` 门不扫**：`packaging/runtime/` 内 6 处跨树引用（如 `skills/agentflow/SKILL.md → ../../reviews/README.md`）不可解析。`validate_runtime_freshness` 只比对字节一致性与存在性，不断言链接可解析。

---

## 七、D8 文档与记录活性（8/10）

**意图卡片**：职责=索引同步、链接可解析、文档无矛盾、记录在更新；自述契约=「文档新增/移动/删除必须同步维护 index」；消费者=所有查文档的人。

**亮点（证据）**
- `index.md` 内嵌计数标记与 `counts.py` 机器对齐（`tests=92 schemas=6 agents=14 batches=4`，4 处全一致）。
- 记录面持续更新：ISS 61 条、最新 `recorded_at` 2026-10-23；`trend.jsonl` 随会话实时追加。
- 计划看板算术 3/3 自洽；`recurrence/` 9 本台账与记录面严格对账（9/9 match）；`PENDING-DECISIONS.md` 带机器校验且真实维护。
- 相对 2026-10-20 评测的实质改进：**手写门项计数声明已全清**（活文档面 0 处「九项/十项」），README:60 改为「项数以 `--list` 自报为准」。

**硬伤（证据 + 触发条件）**
- **P1 · C23 对「证据列无载体」仍判绿**：`PLAN-PRODUCT-001` T07 的 ☑ 行证据列逐字是 `source=./packaging/runtime；生成树仅含运行时面…`——没有任何仓内路径、`仓库@修订:路径`、git 提交号或 `N/A: 理由`，`doc_chain.py` 实跑 PASS。`PLAN-TRACE-001` DEV-03/DEV-05 自己记录了同类盲区（「那个 PASS 是 blindness 而不是 clean」），修复只补了反引号任务号方言。
- **P2 · 同批次门状态双源**：质量批 README 推进进度两道门写 `☐ 待独立评审勾选`，而同文件元信息与 `docs/releases/todo.md` 写「门变更均经独立评审 approved」，且 `reviews/review-2026-10-19-001.md` 确实在盘（decision: approved）。
- **P2 · 勘误追平未闭环**：`SchemaSubsetFailClosedTests`/`MutationKillCorpusTests` 两个从未进入提交历史的类名，全仓仍有 12 处 / 8 处命中，其中 `review-2026-10-19-001.md` 两处未见勘误标注。

---

## 八、D9 治理与发布闭环（7/10）

**意图卡片**：职责=把「改 Agentflow 自己」装进受治理的环；自述契约=候选不自评、`measurement: none` 不称 better、晋升需人工评审引用、发布=人工批准；消费者=改进环发起者、四个治理角色、人。

**亮点（证据）**
- **`measurement: none` 口径被 schema 机器强制，不是口头纪律**：构造 `status:"none" + evaluation_result:"better" + decision:"promote"` 过校验器 → `must not match the forbidden schema`；`basis` 未提人工评审 → 两条 `does not match`；改为 `human review: reviewer approved` → valid。
- 角色分离的机器级部分真实存在，且仓库诚实自承边界：SKILL:24 逐字「除非宿主确实强制分离的工具白名单与工作区，否则角色分离只是流程性的」；硬边界 7「这是角色分离，不是环境隔离」。
- `isolation.py check-diff` 实证拦下受保护路径改动（`blocked: ["schemas/plan.schema.json"]`，exit 1 + stderr 点名 + JSON 三处一致）。
- 五份 manifest 实跑 PASS；CHANGELOG 顶条 0.18.2 与 manifest 双向一致、序列严格降序。
- 装置裁撤后无活面死引用（现行活文档对退役 token 的引用均为「已裁撤 + 恢复清单见 §3」的现状表述）。

**硬伤（证据 + 触发条件）**
- **P1 · `candidate.schema.json` 与 `release-record.schema.json` 是「无消费者的活契约」**：全仓候选/发布记录文件数 = 0。两份契约的 `allOf` 条件分支从未在真实记录上编译过——本轮是手工构造记录才验证了它们的强制力。
- **P1 · 改进环四角色的边在裁撤后零走通**：43 个 episode 中无 `test`/`incident`/`rollout` 型；提及四个治理角色的 episode 全部早于 2026-10-12。0.13.0→0.18.2 六次发布无一记录改进环被派发。
- **P2 · `trend.jsonl` 四版本未更新**：末行 `unittest_count: 89`（2026-10-23），今日实为 92。
- **P2 · `pending-test.md` 安装面行陈旧**：第 5 行写 0.15.0 快照 PASS，源面已 0.18.2。

---

## 九、D10 安全与权限边界（7/10）

**意图卡片**：职责=write_scope 是提示词级还是机械级、候选隔离是否要求受信检查器根、凭据纪律、fail-open 面全集；自述契约=硬边界 14 条；消费者=主审与候选。

**亮点（证据）**
- 候选隔离**确要求受信检查器根且机械强制**：`isolation.py:132-136` 对 checker 与 candidate 嵌套/相等即 FAIL；清单只从 `checker-root/protected-paths.txt` 读，候选树里放伪造清单无效。
- 写范围执法器自身与硬边界文本都在保护面内：改 `check-write-scope.sh` 或 `contracts.md` 会被 `check-diff` 拦（M4 实证）。
- 凭据纪律三处一致：SKILL:46、两份 schema 的 `credentials` description「Values are forbidden」、`gate/records.py:94-101` 对个人绝对路径报错。

**硬伤（证据 + 触发条件）**
- **P1 · 写范围执法器不在任何自动路径上**：`check-write-scope` 在 `.github/` + `skills/agentflow/scripts/` + `tools/` 下的非注释命中只有 1 处，且是 `gate/common.py:82` 的「保护它自己」条目。没有任何 hook、CI 步骤或 `validate.py` 子项调用它。宿主又不强制 Write 路径（`host-platform-facts.md` C7 行如实自承）——两者叠加意味着「write_scope 是机械级」只在主审记得跑脚本时成立。
- **P2 · 凭据值形状无扫描**：`credentials: "env: ADMIN_TOKEN=sk-xxx"` 会通过 schema（合法字符串）且不触发个人路径规则。声明「Values are forbidden」无机器支撑。

---

## 十、D11 实现的效果（7/10）

**意图卡片**：职责=用仓库自己的历史证据回答「实际跑出了什么」；自述契约=统计 + 抽查验证；消费者=判断这套方法是否值得继续。

**亮点（证据）**
- 61 条 ISS：`verified` 40（65.6%）、`open` 17、`fixed-pending-review` 4。40 条 verified 中 `reviewer`/`regression_status`/`closure_criteria` **缺失均为 0**——不是只改状态字。
- 47 轮独立评审中 25 轮 `changes_requested`（53.2%），每轮带逐字 finding 与 resolution。
- 7 份 `partial` 负向 episode 在场，其中 `EP-2026-10-18-001` 有一条 claim 主动标 `failed`，否证自己的合并提交（「提交信息称只并入记录类内容，实际 14 个文件中 6 个不是记录类」）。
- 变异测试仓内载体可核：`mutation-results-2026-10-23.json` 58 项 = 51 杀死 / 7 存活，与计划行声称逐项对上。
- 门红后修复链完整：`EP-2026-10-23-001` 第二轮发现「五处载体把十一项全 PASS 写成事实依据，而冻结提交上 `decision_gate` 实为红」→ 修 → 复绿。

**硬伤（证据 + 触发条件）**
- **P2 · 改进环疗效证据为零**：0 候选 0 发布记录，其发布门的运行时正确性（含 schema `allOf`）只有静态校验背书。与 G10 同一事实，此处从「疗效」角度计分——D9 已就「契约无消费者」扣过分，本维扣的是「方法产出不可考」。
- **P2 · 反馈闭环最后一环不可见**：35 份 `user_feedback` episode，但 `recurrence` 9 本台账档位是 `recurred` ×4 / `single` ×5，没有一本降到 single 后再未复发——「记录→修复→不再犯」在数据上不可见。
- **P2 · 批次完成率换分母**：`PLAN-PRODUCT-001` README 写 7/12，看板实为 14 行（☑7/◐1/☐1/—5）；`PLAN-LOOP-SMOKE-001` 写 5/9，看板 10 行。
- **P1 · `verified` 的 `closure_criteria` 行号会过期且无门看守**：抽核 ISS-2026-09-20-先写契约后核实平台约定，其声称 `document-chain.md:284-286 契约先核实条款`，而该条款现已漂到 `387-389`（284-286 现在是一条代码围栏收尾）。事实为真、行号过期，属 C17 类核验过期，但 ISS 记录的 `closure_criteria` 不在 C17 检查范围内。

---

## 十一、D13 竞品比对（8/10）

**意图卡片**：职责=横向对比、找真实空白、定叙事；自述契约=一切用可核查公开事实，注明来源与检索日期；消费者=对外叙事。

**对比矩阵**（8 个对象，检索日期均为 2026-10-26）：superpowers、BMAD-METHOD、spec-kit、Claude Code subagents、Codex AGENTS.md、OpenHands、CrewAI、LangGraph。

| 维度 | agentflow | 竞品最强对等物 |
|---|---|---|
| 确定性强制力 | **机器级**（11 项 validate + 24 条 C 判据 + protected 机器拒绝，本轮 25 变异实证） | superpowers 靠 bootstrap 注入 + 「Mandatory workflows」措辞；spec-kit 的 convergence 是结论判定不是路径拦截 |
| 记录与审计 | **记录即编译**（schema 不合即编译错误 + C23 证据在场：`/tmp` 不算） | spec-kit 有模板与文档化结果，无「frontmatter 不合 schema 即编译错误」机制 |
| 自迭代/治理 | **当前空转**（0 候选 0 发布记录）；发布前强制由 `pre-push.sh` 承担 | CrewAI 有 guardrails + human review；均无「候选不得编辑评判自己的门」 |
| 上手成本 | 中高（quickstart 自称 5 分钟，必读面 12 份） | Codex AGENTS.md 极低（一个 md）；spec-kit 低（六条命令） |

**真实空白创新点**：① 记录必须可复核，`/tmp` 不算（C23 自测用例逐字含「a ☑ row whose only evidence is a cleaned /tmp path trips」）；② 门自身的受保护面 + 机器拒绝自改门（本轮双向实证）；③ 「不可判定定义」作为产品机制（小改动六条合取 + 固定应用顺序）；④ 宿主差异的实证台账（Z12/X3 两条「同一操作两宿主行为相反」的一手记录）。

**重复造轮子**：文档链四阶段骨架 ≈ spec-kit 的 specify/plan/tasks；角色委派 ≈ Claude Code subagents 原生能力；改进治理环 ≈ 一个没有 runner 的 CI。

**对外叙事该押注什么**：押「门是机器，不是格言」（可当场复现三连：`--list` 11 项、`--self-test` 110/110、碰禁区 exit 1 + blocked 逐字）；押「记录必须可复核，`/tmp` 不算」；押「同一个情形每次同样处理」。**不要押「受治理自迭代」**（一条 `ls` 即可证伪），**不要押「跨宿主一致」**（Z12/X3 证明两宿主安装面行为相反）。

---

## 十二、无证据推测清单（全角色汇总，单独成节）

1. 「跨轨契约不一致如果没有独立评审门会进入交付」——基于两个案例的机制推断，未做「无 agentflow 对照组」实验。
2. 「单人开发者场景 material 纯文档批次成本倒挂」——由 3347 行最终留存为 CHANGELOG 一节推得，未实测「不用 agentflow 需要多少行」。
3. 「竞品 X 没有机制 Y」——基于官方页面未提及，不等于实现中不存在（spec-kit 的 clarification/checklists 细节未读全文）。
4. 「improve 环四角色是清单噪声」——引用 roles.md 自述 + 0 候选核验，但「噪声」这个价值判断本身无证据。
5. `.workbuddy/` 下历史复盘所指事项今日是否仍成立——未逐字比对两份文本全部差异。
6. `publish.sh`/`upgrade-*.sh` 非 dry-run 路径的真实行为——未实跑，CHANGELOG 对其端到端实测的声称本轮未复现。
7. 宿主是否真的按 `disallowedTools` 强制拦截、`maxTurns` 是否生效——依据是 `host-platform-facts.md` 的已观察记录，非本轮现场实验。
8. `PLAN-PRODUCT-001` 其余 `verified` 记录的 `closure_criteria` 是否同样行号漂移——本轮只抽核了 ISS-2026-09-20-先写契约后核实平台约定 一条。
9. `MIN_UNIT_TEST_COUNT = 20` 的原始选取理由——注释只写「far above a trivial suite」，未记载权衡过程。

---

## 十三、整改路径（分批推进表）

| 批次 | 范围 | 完成标准 |
| --- | --- | --- |
| 1 · 口径对齐 | G01 lint 口径、G22 README 注记、G24 脚本清单、G26 T09 基准 | 同一解释器下 `validate.py lint` 与 `pre-push.sh` 结论一致；README 注记每个断言可被一条命令复现；四个脚本跑项清单自动跟随 `--list` |
| 2 · 堵 fail-open | G02 不可读文件、G12 自测谎报、G13 负例钉判据、G14 测试下限 | 四个变异（chmod 000 / 200-per-200 / 改状态词 / 清空测试文件）全部让门变红；`--self-test` 仍 110/110 |
| 3 · 门该在场的东西在场 | G05 C23 载体、G06 门 6、G07 canary 标注、G20 C17 变异 | 四个新判据各有正反夹具；副本上把 T07 证据列还原为现样应转红 |
| 4 · 契约自洽 | G03 模板、G04 记录更正、G15 安装树链接 | `/tmp` 副本照抄模板填最小内容 → 双 PASS；安装树链接扫描零死链 |
| 5 · 记录面收敛 | G09 行号、G16 门状态、G17 勘误追平、G18 分母、G25 清理 | 40 条 verified 重跑新校验；三个批次 README 与看板同组数字；两个类名未带勘误的命中数 = 0 |
| 6 · 待拍板 | G08 写范围自动化、G10 改进契约 examples、G11 `.workbuddy/` 处置 | 三项均需用户确认（G08 涉 CI 误报面、G10 涉 examples 声明、G11 涉新目录登记） |

每批修完独立复审后再评下一批。**关 Issue、补文档或单测变绿，都不能单独保证升分。**

---

## 十四、勘误节（本审核自身错误的集中披露）

本轮未发现「结论与证据相反」的错误。两处需要如实记录：

1. **R2 纠正了主审派发的任务描述本身的指向错误**：任务书写「README 自承宿主不对 Write 工具强制路径约束」，R2 逐行检索现行 README 未找到该句，真实位置是 `docs/host-platform-facts.md` C7 行。R2 的 D10 分析以 C7 行为据，未采用任务描述的文件指向。这是任务描述（数据）未先对照仓库核实的实例——恰是本仓自己列为「出现即缺陷」的那一类。
2. **R2 自我勘误 3 处**：M5 初判「README 断链不会被 docs 抓住」被实跑证伪；D4 布尔命名初列 24 个，核对后发现 15 个实际返回 `X | None`（检测器把 PEP 604 联合类型误判为 bool），修正为 9 个；M22 首轮锚字符串写错导致无效记录，第二轮重做后确认 PASS 是真实结果但成因与其它违约有关。首轮无效记录不计入结论。

**抽核规模与结果见附录 B**（7 条全部一致），此处不重复。

---

## 十五、最终裁决

**设计–执行差距判断**：本仓的设计声明与实现之间**没有系统性差距**，剩下的是三类局部问题——口径双源（lint、T09 基准、测试下限）、门对「该在场的东西是否在场」尚未泛化（死条款、零实例契约、未登记目录）、以及一批记录面的行号/勘误/分母漂移。这三类都有明确解锁路径，且多数已有计划任务号或可登记为拍板项。

**存在意义结论**：成立。核心差异点是「门是机器不是格言」与「记录必须可复核（`/tmp` 不算）」，二者都经本轮实跑与变异实证，且在 8 个对比对象中未见对等物。最该对外澄清的一条是「受治理发布」当前是治理空转，发布前强制实际由 `pre-push.sh` 承担。

**砍掉什么它反而更好**（按「砍掉后损失最小、收益最大」排序）：
1. **砍掉 improve 治理环的执行面**（四个治理角色 + 两份 schema 的路由），保留恢复清单——这是全仓最大的「声明在场但无输入」面，`PENDING-DECISIONS` 第 10 条的推荐列自己写着「A 冻结」。
2. **砍掉批次文档的长期留存义务**，改为一等公民的 CHANGELOG + episode 双载体——质量批 3347 行的最终留存物是 CHANGELOG 一节。
3. **砍掉 SKILL 里对已裁撤能力的反复解释**（execution-coordinator「当前不存在」两处、记录根适用范围、埋点三处），集中到一处能力状态说明。

**最高杠杆下一步**：第二批「堵 fail-open」——G02/G12/G13/G14 四条都是「门看起来比实际宽」的类型，正是这个仓库自己列为最高优先级的故障类（验证缺席）。四条修完，D2 的「红的边界」才与声明真正对齐。

**拍板项清单**（推荐默认值 + 框定它的证据）：

| # | 待决问题 | 推荐 | 框定它的证据 |
|---|---|---|---|
| P1 | G01 lint 口径选 (a) 让 `validate.py` 也 SKIP，还是 (b) 改 CHANGELOG 措辞 | **(b) 改措辞**——`validate.py` 的 fail-closed 性是「缺工具即红」，这正是它该有的行为；脚本的 SKIP 是发布链路的便利，两者各自诚实比强行统一更符合仓库「未运行 ≠ 失败」的自述 | CHANGELOG:7/:42 的措辞；`validate.py:250-282` 无 SKIP 分支 |
| P2 | G08 写范围执法器是否接入自动路径（pre-push 或 CI） | **先登记为已知人工步骤，不自动接入**——`check-write-scope.sh` 的误报面（dirty 树的无关变更）未被评估，贸然接入会阻断合法推送；等价于把 G08 从 P1 降为「已声明未缓释」 | 非注释调用点 = 1；`check-write-scope.sh:26-28` 自己要求人工扣除已知 dirty 路径 |
| P3 | G11 `.workbuddy/` 如何处置 | **(c) 标注为非权威草料区并在 index 加一行**——它含 8 份 R1–R8 历史复盘，删除会丢掉审查历史，登记为权威又会与活文档面口径冲突 | `git check-ignore` 命中但盘上多份 md；活文档零引用它 |
| P4 | G10 改进契约是否补 examples | **补**——这是把「契约无消费者」从隐状态变成可见事实的最低成本做法，且不需要先拍板 improve 治理机器的存废（PENDING 第 10 条） | 候选/发布记录文件数 = 0；`INVALID_EXAMPLES` 机制已存在 |
| P5 | `docs/evaluations/` 的十份历史档案是否要按 Q-04「留三删五」精简 | **不在本轮处置**——Q-04 属另一批次的未决项，本审核只新增不覆盖，不动既有档案 | `PLAN-REVIEW-001` proposal §Q-04 |

---

## 附录 A：实跑命令与逐字输出（关键条目）

```
$ date "+%Y-%m-%d %H:%M:%S %Z"
2026-10-26 15:38:54 CST

$ git rev-parse HEAD
ef7da3f6b3a05cd3547e53b922d28da89054437a

$ git status --porcelain=v1
（无输出）

$ PYTHONDONTWRITEBYTECODE=1 python3 tools/lab/validate.py all
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
FAIL lint (2 error(s))
  - lint/ruff: ruff is not installed in this interpreter; run `pip install -r requirements-dev.txt`
  - lint/mypy: mypy is not installed in this interpreter; run `pip install -r requirements-dev.txt`
EXIT=1

$ python3 tools/lab/validate.py --list
schemas examples artifacts protected manifests docs tests doc_chain doc_chain_live decision_gate lint
all runs 11 checks

$ PYTHONDONTWRITEBYTECODE=1 python3 tools/lab/doc_chain.py --self-test
110/110 self-test cases pass
EXIT=0

$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
Ran 92 tests in 1.409s
OK
EXIT=0

$ python3 tools/lab/validate.py installed
PASS installed
EXIT=0

$ python3 tools/lab/counts.py
计算值：tests=92  schemas=6  agents=14  batches=4
OK：标记共 4 处，全部与计算值一致。
```

**变异实验**：25 个变异中 19 个让门变红、4 个没有、2 个是已声明设计，逐项结果见第三节 D2 的变异表。`isolation.py check-diff` 的 10 个边界场景与 `check-write-scope.sh` 的 9 个场景全部 fail-closed 或正确放行，逐项结果同在 D2 与 D10 节。

## 附录 B：元评审结论（证据链审计）

主审对四个角色的关键结论抽核 7 条，逐条重跑或重读原文：

| 抽核项 | 报告声称 | 抽核结果 |
|---|---|---|
| `doc_chain.py --self-test` | 110/110 | ✅ `110/110 self-test cases pass` |
| `.workbuddy/` 未登记 | 活文档零提及 | ✅ index/README/AGENTS 零命中；`.gitignore:14` 命中 |
| 门 6 链路收口通读零发生 | 四批次/六计划/43 episode 零命中 | ✅ 全仓 7 处命中中仅 2 处为定义处，其余为 ISS-2026-09-21-文档链陈旧前向引用无收口（另一问题）、`.workbuddy` 历史、生成树副本 |
| T09 证据列双基准 | 仓根路径不在盘 | ✅ `reviews/review-2026-10-19-001.md` 仓根不存在，批次内存在 |
| trend.jsonl 陈旧 | 末行 unittest_count 89，实跑 92 | ✅ 逐字一致 |
| `checks.py:1142` fail-open | `except OSError: continue` | ✅ 逐字在 `:1141-1142` |
| `MIN_UNIT_TEST_COUNT = 20` | 值 20 + 注释自称 far above trivial | ✅ `common.py:127` 逐字一致 |

**验证缺席检查**：未发现「有结论无实跑」的条目。四个角色都在未读清单中列明了未读范围与原因，且 D13 明确标注了哪些竞品论断缺来源。

**评分锚定检查**：12 个维度分全部指名了通用锚点档位，且每个分数至少有硬证据。D2 的 8 分明确说明「25 个变异中 19 个抓住、4 个未抓住、2 个为已声明设计」——即扣分项本身也是实证出来的，不是印象分。

## 附录 C：覆盖与证据

### C.1 仓库规模（`git ls-files` 机器统计）

| 面 | 文件数 | 行数 |
|---|---:|---:|
| docs | 134 | 16155 |
| packaging | 83 | 9137 |
| skills | 47 | 5024 |
| episodes | 44 | 4103 |
| examples | 34 | 1224 |
| tools | 27 | 7566 |
| agents | 15 | 756 |
| reviews | 11 | 1351 |
| root（根目录文件） | 8 | 1962 |
| schemas | 7 | 526 |
| tests | 5 | 1869 |
| .claude-plugin / .codex-plugin / .zcode-plugin / .github | 4 | 92 |
| **合计** | **421** | **47865** |

### C.2 按面的覆盖状态

| 范围 | 覆盖方式 | 状态 |
|---|---|---|
| `tools/lab/` 31 个 `.py`（含 `gate/` 13 模块 + `docchain/`） | R2 逐文件读 + 25 个变异实证 | **已核实** |
| `tests/` 5 个 `.py` | R2 全部阅读 + `unittest` 92 项实跑 | **已核实** |
| `agents/` 14 个角色 + README | R3 逐份读 frontmatter 与正文；R1 用 `counts.py` 验证计数 | **已核实** |
| `skills/agentflow/`（SKILL + references 6 份 + scripts 4 个 + templates 24 份 + 原型） | R3 读 SKILL/references/templates 标题结构与内容；R2 读 4 个 `.sh` | **已核实**（`upgrade-codex.sh` 非 `AGENTFLOW_LINT_PYTHON` 段未逐行读） |
| `skills/improve/`（SKILL + references 4 份 + openai.yaml） | R3 全量读；R1 读 SKILL 与 release-record schema | **已核实** |
| `schemas/` 6 份 + README | R3 读定义与 `$id` 比对；R2 走查 119 个 schema 位置 | **已核实** |
| `docs/` 134 份 md | R3 按状态与引用抽查（PENDING-DECISIONS、trend、system-guide、design-decisions、quickstart、host-platform-facts 全量） | **部分核实**（`docs/product/` 三份正文只读 README 与门禁勾选状态） |
| `docs/issues/` 61 份 ISS + recurrence 9 本台账 + README | R3 全量机器统计 + 抽核 4 份全文 | **统计全量、语义抽查** |
| `docs/features/` 4 个批次（6 份计划 + proposal/spec/design + README） | R3 读 README 元信息与看板算术 + ☑ 行载体逐行查；正文按引用抽查 | **看板全量、正文抽查** |
| `docs/releases/`（todo + pending-test） | R1/R3 全量读 | **已核实** |
| `episodes/` 43 份 JSON | R3/R4 统计聚合 + 读 6 份结构；R1 读 claims 明细验证边 | **统计全量、语义抽查** |
| `reviews/` 3 份评审记录 + archive | R3 读 README 与门状态；R2 读 trend 相关节 | **已核实** |
| `docs/evaluations/` 10 份历史档案 | 只读 README 收存清单与两份报告的相关片段 | **按需引用**（历史快照不作为现行依据） |
| `packaging/runtime/` 生成树（83 份） | 未逐文件读；由 `manifests`（逐字节）+ `installed`（PASS）覆盖 | **机器覆盖** |
| `packaging/build_runtime.py` + README | R1 读 `RUNTIME_FILES` 与白名单；全文未读 | **部分核实** |
| `.github/workflows/` | R2 读 validate.yml（含 pip install dev 依赖步与 checker-root 用法） | **已核实** |
| `.workbuddy/`（gitignore，未登记） | 发现其存在与内容规模；未逐份读（8 份 R1–R8 历史复盘） | **未读**（作为 G11 发现登记） |

### C.3 运行证据清单

| 命令 | 结果 | 用于 |
|---|---|---|
| `validate.py all` | 10 PASS + `FAIL lint`（环境缺失），EXIT=1 | D1/D2/D9 |
| `validate.py --list` | `all runs 11 checks` | D1/D2（口径真源） |
| `validate.py` 11 个单项逐个 | 全部 PASS，EXIT=0 | D2 |
| `validate.py installed` | PASS，EXIT=0 | D1/D9 |
| `validate.py manifests` | PASS，EXIT=0 | D1/D9 |
| `doc_chain.py --self-test` | `110/110 self-test cases pass`，EXIT=0 | D2/D5 |
| `doc_chain.py --repo .` | PASS decision-gate | D8 |
| `unittest discover -s tests` | `Ran 92 tests` / `OK`，EXIT=0 | D3/D4 |
| `counts.py` | `tests=92 schemas=6 agents=14 batches=4`，4 处全一致 | D1/D6/D8 |
| `trend.py` | EXIT=0，输出 `unittest_count: 92` | D3/D9 |
| `isolation.py check-diff` 10 场景 | 全部 fail-closed 或正确放行 | D2/D10 |
| `check-write-scope.sh` 9 场景 | 中文/空格/删除/忽略/`.` 全树全部正确处理 | D10 |
| **25 个变异实验**（`/tmp/gw_mut/repo` 副本） | 19 抓住 / 4 未抓住 / 2 已声明设计 | D2/D3 |
| `chmod 000` 决策记录（副本） | 8 findings → PASS（fail-open 实证） | D3 |
| `record_store.py index` | 生成 `.agentflow-records.sqlite3`，用后已删 | — |
| `git status --porcelain`（审核前后各一次） | 均无输出 | 只读铁律自证 |
| `git rev-parse HEAD`（审核前后各一次） | 均为 `ef7da3f` | 只读铁律自证 |

**失败的运行**：`validate.py all` 的 `lint` 子项因本解释器未装 ruff/mypy 而 FAIL。按仓库判据这是**环境缺失**而非代码回归，已在 G01/G22 单独处置，未计入任何维度的高分依据。`publish.sh`/`upgrade-*.sh` 的非 dry-run 路径未实跑（会真推送与安装）。

### C.4 按角色的阅读覆盖

| 角色 | 已读 | 未读（含原因） |
|---|---|---|
| R1 架构与治理 | README/AGENTS/index/CHANGELOG/design-decisions/system-guide/quickstart/PENDING-DECISIONS、两 SKILL、五份 manifest、packaging README+build_runtime、protected-paths、目录实况、`ls -R` | agents 14 份正文（D1 只用计数，已用 counts.py 机器验证）；`docs/evaluations/` 全部（历史档案不作为依据）；`packaging/runtime/**`（已由 manifests 逐字节 + installed 覆盖）；hosts/telemetry/test-records 三份 references（与五面分离无直接判定关系） |
| R2 门禁与代码 | `tools/lab/` 全部 .py（含 gate/ 13 模块）、`tests/` 5 个文件全部、`check-write-scope.sh`、`pre-push.sh`、`publish.sh` | `docchain/selftest.py` 约 700 行夹具字符串字面量（判别力靠 25 个变异实证而非阅读）；`upgrade-codex.sh` 非 AGENTFLOW_LINT_PYTHON 段；`build_runtime.py` 全文（D2 只经 manifests 实证其产物） |
| R3 契约与记录 | agents 14 份 + README、两 SKILL、references 6 份、templates 24 份 + 原型、schemas 6 份 + README、`docs/` 全量、`docs/issues/` 全部（含 recurrence）、`docs/features/` 全部、`docs/releases/` 全部、`episodes/` 43 份、`reviews/` 全部 | `publish.sh`/`upgrade-*.sh` 只读文件名与 CHANGELOG 描述，未逐行读；`docs/evaluations/` 8 份只读 README 与两份报告的相关片段；`docs/product/` 三份正文只读 README 与门禁勾选状态 |
| R4 定位与竞品 | 8 个竞品的官方 README/文档页 + 存在意义相关仓内件（SKILL、quickstart、design-decisions、CHANGELOG、PENDING-DECISIONS） | 竞品仓库源码（仅官方页面）；Cursor rules 详情、Gemini CLI/OpenCode/Pi 插件形态；spec-kit SDD walkthrough 全文；BMAD v7 alpha skills 清单；`templates/` 27 份正文、`docs/product/`、agents 14 份全文、43 份 episode 中读 6 份、61 份 ISS 中读 4 份 |

### C.5 未读清单（集中声明）

**未逐行读完的源码**
- `tools/lab/docchain/selftest.py` 约 700 行夹具字符串字面量——判别力由 25 个变异与 110 例自测实证，不依赖逐字阅读。
- `packaging/build_runtime.py` 全文——只读 `RUNTIME_FILES` 与白名单段。
- `skills/agentflow/scripts/upgrade-codex.sh` 非 `AGENTFLOW_LINT_PYTHON` 段——本轮不评发布链路端到端正确性。

**未逐行读完的文档**
- `docs/product/` 三份正文（proposal/spec/design）——只读 README 与门禁勾选状态；其机器健康由 `doc_chain_live` PASS 覆盖。
- `docs/features/<批次>/proposal|spec|design` 正文——D7 判「链的边是否走过」不判「链的内容质量」。
- `docs/evaluations/` 8 份历史报告——按该目录自己的声明是只读快照，只按需引用已核对片段。
- `.workbuddy/` 8 份历史复盘——gitignore 且未登记，作为 G11 发现登记，未作为证据源。

**未读的记录**
- 61 份 ISS 中读 4 份全文，其余靠机器统计与 frontmatter。
- 43 份 episode 中读 6 份结构，其余靠统计聚合。
- 6 份计划看板全量查算术与 ☑ 行载体，任务叙述按引用抽查。

**未做的运行验证**
- 未在 ZCode / Codex / Claude Code 宿主内实际派发 worker 并观察其 Write 行为——「宿主不强制 Write 路径」依据是 `host-platform-facts.md` C7 行的已观察记录，非本轮现场实验。
- 未验证 `agents/*.md` frontmatter 的 `maxTurns` 是否被宿主强制执行（`host-platform-facts.md` Z6 行自述「未实际触发」）。
- 未实跑 `publish.sh`/`upgrade-*.sh` 完整发布链路。

### C.6 排除项与覆盖比例

**排除项**：`.git/`、所有 `__pycache__/`、所有 `*.pyc`、`packaging/runtime/`（生成树，除非审打包正确性，读其生成器而非产物）。四个角色的必读清单之外均未扩大读取范围。

**覆盖比例**：本审核是**按维度只读审核**，不是逐文件语义审查——源码面（`tools/lab/` 31 个 `.py` + `tests/` 5 个 + 4 个 `.sh`）为 R2 逐文件读；契约面（14 角色 + 两 SKILL + references + templates + schemas）为 R3 逐份读；记录面（ISS 61、episode 43、计划 6、批次 4、reviews 3）为**全量机器统计 + 抽查验证**，每条统计至少抽 1 条原文核对；文档面（`docs/` 134 份）为 R3 按状态与引用抽查。**因此本报告不代表所有文件已被语义审查**，未逐行读完的部分已在 C.5 集中列明。

---

## 附录 D：评分卡

> **分数权威在〇总览的分数表与正文各章节标题**，本附录不重复维度分，只记正文没有的细粒度证据。
> 状态三态：`已核实`（有证据）· `未验证`（查了但缺运行证据）· `未读`。只有「已核实」计入高分依据。
> 每维 5 个子项，每子项满分 2 分，维满分 10 分。**扣分列是本附录独有的**——正文只写「有硬伤」，
> 不写硬伤对应多少分；两处合起来才能复算一个维度分。

### D.1 架构与设计一致性

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 五面分离真实成立、无跨面污染 | 已核实 | Python 源码仅分布 packaging(7) 与 contract(31)，记录面/文档面零 `.py` | 0 |
| 「无第二套 CLI」被遵守 | 已核实 | 全仓入口点扫描：argparse/sys.argv 全在门工具与打包脚本内 | 0 |
| fail-closed 贯穿工具层 | 已核实 | `gate/schema.py:286` 白名单 + M1 注入 `exclusiveMinimum` → FAIL exit 1 | 0 |
| manifest 与关键计数一致 | 已核实 | `manifests` PASS；`counts.py` → `tests=92 schemas=6 agents=14 batches=4` 全一致 | 0 |
| 口径无漂移 | 已核实（有硬伤） | G23 安装面带 protected-paths 副本但 `INSTALLED_FILES` 不含；G22 README:63 指向 tests 而实况是 lint；G24 四脚本硬编码十项 vs `--list` 十一项 | −2 |

### D.2 门禁有效性（权重 ×2）

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| schema 词汇表闭集、未实现关键字即编译错误 | 已核实 | 119 个 schema 位置走查「NOT in SUPPORTED: 0」；19 个已实现未用关键字为将来契约预留 | 0 |
| 门会红（变异实证） | 已核实 | 25 个变异中 19 个让门变红（M1–M5、M7/M8、M11/M12、M14、M17–M21） | 0 |
| isolation fail-closed | 已核实 | 10 个边界场景全 fail-closed（`-` base、坏 base、嵌套、清单缺失、中文路径、忽略文件…） | 0 |
| protected 双向自证 | 已核实 | 47 条必需条目全被 24 条声明覆盖且全部存在；M17/M18 实证 | 0 |
| 门的边界与声明一样宽 | 已核实（有硬伤） | G12 自测谎报 `200/200` PASS；G13 负例改状态词仍 PASS；G14 清空 4 测试文件 PASS；G01 lint 口径矛盾 | −2 |

### D.3 代码质量与安全

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 异常 typed 且转化或重抛 | 已核实 | 38 个 handler 全 typed，0 裸 `except:`、0 `except Exception` | 0 |
| 无命令/参数注入面 | 已核实 | 20 处 subprocess 全 `shell=False` + 列表传参；两处字符串拼接分别由 `SHA_RE` 与 `--` 保护 | 0 |
| 非 ASCII 路径处理正确 | 已核实 | `isolation.py:120-121` NUL 分帧 + surrogateescape；`check-write-scope.sh` 中文/空格/删除/忽略全对 | 0 |
| 测试覆盖真相 | 已核实 | 5 个测试文件全部被测、全部被 `validate.py tests` 运行；mutate 52 项中 49 项有变异 | −0.5（13/24 个 C 检查无变异项，C17 最薄） |
| 无 fail-open 面 | 已核实（有硬伤） | **G02**：`checks.py:1142` `except OSError: continue`，`chmod 000` 使 8 findings 变 PASS | −2.5 |

### D.4 代码工艺与可读性

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 注释解释「为什么」且有关键取舍 | 已核实 | `isolation.py:122-127`、`checks.py:196-206`、`:736-738`、`examples.py:49-54` 均带审计编号与日期 | 0 |
| 无死代码、无 TODO/FIXME 残留 | 已核实 | 生产面死名字 0；TODO/FIXME 全仓 1 处且是历史陈述（`common.py:125`） | 0 |
| 命名表意、风格一致 | 已核实（抽样 50） | 缩写惯例全域一致；9 个 bool 函数不带 `is_/has_` 前缀 | −0.5 |
| 函数长度与复杂度可控 | 已核实（有硬伤） | `workspace.py:41` 331 行 / CC 119；`checks.py:277` 266 行 / CC 129（均有充分行内注释） | −1 |
| 一致性 + 无重复漂移 | 已核实（有硬伤） | `TASK_STATUS` glyph→词映射两份拷贝（有注释标注同步义务）；tests/ 31 处未用导入；doc_chain CLI 唯一不用 argparse | −0.5 |

### D.5 Agent/Skill 契约质量

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 角色 frontmatter 与正文互证 | 已核实 | 14/14 `name` == 文件名；五只读角色 disallowedTools 覆盖 Bash/Write/Edit；test-executor 禁 Edit 与正文精确对应 | 0 |
| 路由表可解析、无悬空引用 | 已核实 | SKILL 引用的 `agentflow:<role>` 差集为空；schema 路径 6 条全在盘 | 0 |
| 判断词可判定、优先级裁决 | 已核实 | 小改动六条合取 + risky 五条析取 + 固定应用顺序；「相同原因」有规范化签名定义 | 0 |
| schema 无重复定义或漂移 | 已核实 | improve/references 三份与 schemas 六份求交为空；9 份 `$id` 全唯一 | 0 |
| 契约之间无矛盾、模板可照抄 | 已核实（有硬伤） | **G03** `execution.md:14` 编号标题 vs `PLAN_REQUIRED_HEADINGS` 三节（照抄即被拒）；**G04** test-records 与 test-executor 对更正记录给出相反指令；**G15** 安装树 6 条断链 | −2 |

### D.6 结构合理性

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 引用矩阵无环、方向正确 | 已核实 | 记录面→契约面仅 2 条合规指针；record→delivery 仅 1 条文档指引 | 0 |
| 无「为了结构而结构」 | 已核实 | 全仓 `.gitkeep` 零命中 | 0 |
| 深度可控 | 已核实 | 源树最深 depth=8；depth=9 全在生成树 | 0 |
| 可发现性实测达标 | 已核实 | 5 个常见任务全部 1 跳直达（优于 3 跳要求） | 0 |
| 命名全域一致 + 无未登记活目录 | 已核实（有硬伤） | agents frontmatter 14/14、plan 文件名 6/6；**G11** `.workbuddy/` gitignore 但盘上多份 md、活文档零提及；**G26** T09 证据列双基准 | −2 |

### D.7 逻辑链路

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 主工作流十步闭环 | 已核实 | 十步标题逐字可抽；7→8 分支、8→9 回环、9 有界、10 终态均成对；mermaid 双证 | 0 |
| 缺陷链四角色边界成对 | 已核实 | 61/61 ISS 带 `## 变更记录`；状态分布与三态机吻合 | 0 |
| 三条链切换点定义 | 已核实 | `roles.md:45` 逐字定义测试→缺陷、实现→规划的升级是一次指派 | 0 |
| 状态机无死路 | 已核实（有硬伤） | **G06** 门 6 链路收口通读死条款（四批次/六计划/43 episode 零命中）；**G29** 建议值草案零发生；**G28** rejected 归档边零触发 | −1.5 |
| 无只进不出的吸收态 | 已核实（有硬伤） | **G07** canary/automatic 有入口无出口，且 automatic 在 `measurement: none` 下结构上不可能通过；**G27** 计划审批边在主流程无落点 | −1.5 |

### D.8 文档与记录活性

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 索引与实际同步 | 已核实 | 计数标记与 `counts.py` 机器对齐；index 4 条链接全解析 | 0 |
| 记录面持续更新 | 已核实 | ISS 61 条最新 2026-10-23；trend.jsonl 随会话追加 | 0 |
| 看板算术自洽、台账对账 | 已核实 | 3/3 计划概览行对上；9/9 台账与记录面 match | 0 |
| 手写计数声明已清理 | 已核实 | 活文档面「九项/十项」零命中；README:60 改为「以 `--list` 自报为准」（相对 2026-10-20 的实质改进） | 0 |
| 无矛盾、无死链、C23 真的在看 | 已核实（有硬伤） | **G05** T07 证据列无四类载体仍 PASS；**G16** 质量批门状态双源；**G17** 幽灵类名勘误未追平；**G30** system-guide/index 内部词裸用 | −2 |

### D.9 治理与发布闭环

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| `measurement: none` 口径诚信 | 已核实 | schema `allOf` 结构保证 none 禁 better；构造记录实证被拒；basis 未提人工评审被拒 | 0 |
| 角色分离的机器级部分真实 | 已核实 | 五治理角色 frontmatter 只读；isolation check-diff 实证 blocked + exit 1 | 0 |
| 晋升规则三载体一致 | 已核实 | SKILL:55 / evidence-and-release:134-140 / schema `allOf` 逐字一致 | 0 |
| 五份 manifest 与 CHANGELOG 一致 | 已核实 | manifests PASS；CHANGELOG 0.18.2 与 plugin.json 双向一致、序列严格降序 | 0 |
| 改进环真的转过 | 已核实（有硬伤） | **G10** 候选/发布记录文件数 = 0，两份契约零真实记录被编译；**G07** 四角色边裁撤后零走通；**G21** trend 四版本未更新 + pending-test 陈旧 | −3 |

### D.10 安全与权限边界

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 候选隔离要求受信检查器根 | 已核实 | `isolation.py:132-136` 嵌套/相等即 FAIL；清单只从 checker-root 读，伪造清单无效 | 0 |
| 执法器自身在保护面内 | 已核实 | M4 实证改 `check-write-scope.sh`/`contracts.md` → blocked | 0 |
| 凭据纪律文档与工具一致 | 已核实 | SKILL:46 + 两份 schema description + `gate/records.py:94-101` 个人路径报错 | 0 |
| write_scope 是机械级 | 已核实（有硬伤） | **G08** 非注释调用点 = 1 且是「保护它自己」；宿主不强制 Write 路径（host-platform-facts C7） | −2 |
| 无 fail-open 面 | 已核实（有硬伤） | **G19** 凭据值形状无扫描（`credentials: "sk-xxx"` 通过 schema）；dirty 树需人工扣除 | −1 |

### D.11 实现的效果

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| issue 走完全流程且字段真实 | 已核实 | 61 条中 40 verified；四类必填字段缺失均为 0 | 0 |
| 独立评审真实轮次密集 | 已核实 | 47 轮中 25 轮 changes_requested，每轮带逐字 finding 与 resolution | 0 |
| 负向结果被真实收录 | 已核实 | 7 份 partial；EP-2026-10-18-001 一条 claim 主动标 failed 否证自己的合并提交 | 0 |
| 门红后修复链完整 | 已核实 | EP-2026-10-23-001 + PLAN-TRACE-001 T03 双向证据；变异 58 项目仓 JSON 与计划行对上 | 0 |
| 疗效可全考 | 已核实（有硬伤） | **G10** 改进环 0 候选；**G09** closure_criteria 行号过期无门看守（ISS-2026-09-20-先写契约后核实平台约定 声称 284-286 实为 387-389）；**G18** 完成率换分母；反馈闭环最后一环不可见 | −3 |

### D.12 竞品比对

| 子项 | 状态 | 证据 | 扣分 |
|---|---|---|---|
| 覆盖主要竞品 | 已核实 | 8 个对象，每条带来源 URL 与检索日期 2026-10-26 | 0 |
| 差异化结论回到本仓实证 | 已核实 | 三个创新点全部有本轮实跑或自测用例支撑 | 0 |
| 有「砍什么」的建设性判断 | 已核实 | 砍治理环执行面 / 砍批次长期留存 / 砍对裁撤能力的反复解释 | 0 |
| 叙事建议可执行 | 已核实 | 押「门是机器」三连可当场复现；明确不要押「受治理自迭代」与「跨宿主一致」 | 0 |
| 论断全部有来源 | 已核实（有硬伤） | BMAD agent 精确数量、LangGraph 图原语细节、superpowers hooks 事件类型「页面未指定/未检索到可核查来源」——已如实标注，未猜 | −1 |

### D.14 每维「达到 8 分必须证明的事」

| 维度 | 达到 8 分必须证明的事 | 当前差距 |
|---|---|---|
| D1 | 安装面清单纳入 `INSTALLED_FILES`（或从 runtime 移除）；README 环境注记按实况改写；四脚本清单解析 `--list` | G22/G23/G24 |
| D2 | 四个「未抓住」变异（chmod 000 / 200-per-200 / 改状态词 / 清空测试文件）全部让门变红；lint 口径二选一落地 | G01/G12/G13/G14 + G02 |
| D3 | `checks.py:1142` 改为 append finding 并有 chmod 000 夹具；13 个无变异项的 C 检查补齐（至少 C17） | G02/G20 |
| D4 | 两个 CC>100 的函数拆分或降复杂度；`TASK_STATUS` 双拷贝单源化；tests/ 31 处未用导入清零 | 无编号（工艺项） |
| D5 | `/tmp` 副本照抄 `execution.md` 填最小内容 → doc_chain + artifacts 双 PASS；记录更正口径单源；安装树链接零死链 | G03/G04/G15 |
| D6 | `.workbuddy/` 有明确处置行；T09 证据列改批次内完整路径后单根解析也在盘 | G11/G26 |
| D7 | 门 6 有记录载体 + opt-in C25 自测三例全过；canary/automatic 三处载体都有「当前不可达」标注且 automatic 记录实证被拒；计划审批写进主流程步骤 | G06/G07/G27 + G28/G29 |
| D8 | T07 行补载体后副本上还原为现样应转红；质量批两道门改 ☑ 并附 reviews 链接；两个类名未带勘误命中数 = 0 | G05/G16/G17/G30 |
| D9 | 两份改进契约的正反例进 `examples/` 且反例被拒；todo.md 含「0 候选 0 发布记录」现状行；trend/pending-test 刷新 | G10/G21 |
| D10 | 写范围执法器接入自动路径（或显式登记为已声明未缓释）；凭据值形状有机器检查 | G08/G19 |
| D11 | 40 条 verified 重跑新校验，过期行号从静默变显式 finding；三个批次 README 与看板同组数字；改进环至少跑通一次候选（或按拍板冻结并如实描述） | G09/G18/G10 |
| D13 | BMAD/LangGraph/superpowers 三条缺来源的论断补到可核查，或明确标注为「未核实」并说明影响 | 三条缺来源 |

**注意**：关 Issue、补文档或单测变绿，都不能单独保证升分。升分的充要条件是上表「必须证明的事」逐条有当前 revision 的运行证据。
