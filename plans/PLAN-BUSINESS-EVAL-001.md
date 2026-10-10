---
plan_id: PLAN-BUSINESS-EVAL-001
plan_version: 0.2.5
status: approved
objective: 以 aiwork 文档审查三用例与种子缺陷确定性评分建立方法级改动的业务任务度量切片，替换 measurement: none 过渡态，首次产出 better/neutral/worse（smoke 级）
recorded_at: 2026-09-17T04:00:00Z
updated_at: 2026-09-18T08:07:13Z
---

# 方法级改动的业务任务度量切片 — 实施计划

> 计划形态：Markdown 混合计划（frontmatter 机器信封＋正文执行回写面），文件名 = plan_id。
> 状态图例：`☐ 未开始` / `◐ 进行中` / `☑ 已完成` / `⚠ 阻塞` / `— 本期不做`。
> 回写纪律：完成后只改**状态**与**证据**两列（最小 diff），不改写已完成的任务行。
> 输入版本（已核实）：技术负责人架构决策 D1–D6（2026-09-17）；agentflow 0.5.2（main）；
> _archive/handoff-2026-10/next-session-handoff.md:445-447（P1 首项）；skills/improve/SKILL.md:53（Measured scope，
> `measurement: none (method-level change, no instrumented business task)` 过渡态）。目标仓
> aiwork-workflow-ai（本地 clone，路径只留本地；企业内部 remote，地址只留本地；pin 到全 sha 冻结；
> 快照与打种配方只留本地）。
> 门变更提示：T05–T09 触及保护门（见「门变更清单」），按仓库规则属人工审查变更，需用户逐条批准后
> 才可执行；本计划是执行契约，本身不是改代码的授权。
> 修订 v0.2.0（2026-09-17）：① pin 校验定为脏树式（S01/T08/C9：HEAD 保持＝pin，种子 patch 可逆重放）；
> ② 种子类别强制覆盖「术语歧义」与「跨文档值不一致」（T03，为在研方法级候选预留测量面）；
> ③ S03 定性为噪声底测量并补 unmatched 真实缺陷回流；④ 新增 U-05。
> 修订 v0.2.1（2026-09-17）：状态置 approved；T01–T04/T06/T07 完成回写；种子命中阈值统一记于用例级 `grading.min_seed_recall`；
> **业务权限档改为 workspace-write**（执行中发现：read-only 禁 Write/Edit/Bash 与「findings 写入 workspace」自相矛盾）——
> 快照只读改由「打种时 chmod 只读 + 每次宿主调用后快照 git status 校验」兜底；业务请求拒绝 read-only 档。
> 修订 v0.2.2（2026-09-17）：T10–T13 完成回写；**仪器就绪**（C1–C6 全绿，supervisor 实跑留痕）；新增 U-06/U-07。
> 修订 v0.2.3（2026-09-17）：独立评审（changes_requested）后的修复轮——F1 计划脱敏（去内部 remote/个人路径）、F2 评分覆盖 fail-open→fail-closed、F3 业务身份绕过口关闭、F4 简报归属规则补齐、F5 快照 diff 摘要复检（强化实现）、F6 测试补齐、F7 锚点跨字段拼接关闭、F8 看板状态、F9 文档面。
> 修订 v0.2.4（2026-09-17）：S01 置 ☑（物化与校验证据）；S02 置 ◐（三次尝试留痕，根因＝宿主 cwd 文件访问限制）；U-02 已测量关闭、U-03 已决关闭、U-06/U-07 已关闭；新增 U-08（业务跑须 `--add-dir`，修复落地待重跑验证）；同步进展概览与阻塞描述。
> 修订 v0.2.5（2026-09-18）：术语歧义类别判据放宽（用户反馈）——除发明词未定义外，覆盖惯性压缩词（基线/现网类）指代悬空变体；表达纪律候选择优级定为「换 > 释 > 删」，过度讲解按阅读负担计缺陷；打种约定补该变体锚点取法（既有原文唯一片段，不引入）。用例与种子清单文件不变；新变体种子待 U-01 解除后随 S 阶段补。S 阶段同步项：三份简报的计数句（inputs/BT-001.md、BT-002.md、BT-003.md「只有作者知道含义的，算问题」）须扩为两变体口径，否则压缩词变体的召回被简报结构性抑制——该编辑在受保护 evals/ 内，届时按门变更人工评审；本批不改简报。见 evals/business/README.md。

## 进展概览

**本期进度**：**14 / 16 已完成** · **1 进行中** · **1 阻塞** · **0 未开始**
**统计口径**：T01–T13 计入仪器就绪阶段（离线可判定）；S01–S03 计入 smoke 实跑阶段（挂 P0 未决项，见未决项表）。

| 序号 | 业务侧解读 | 技术侧解读 | 交付效果（完成后可验证） | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 方法级改动第一次有业务度量，不再一律 measurement:none | evals/business 三用例（BT-001/002/003）＋ business-case.schema.json ＋ validate 接线 | `validate all` 八项全绿；三用例过结构校验（T13，C2/C3） | ☑ |
| 2 | 好坏判定不再靠模型自报，可复算 | seed_grader 对 findings 工件确定性匹配：hits/missed/unmatched；accepted＝种子命中率≥阈值；escaped_defects＝漏检数 | golden 测试全绿；unmatched 只记录不扣分（T09） | ☑ |
| 3 | 企业仓可用而不泄漏 | 本地 pin 快照（全 sha）＋ isolation 第四位置 ＋ 脱敏边界 | validate-layout 四参通过（C5）；公开面零泄漏（真实名 grep 0 命中、九个锚点在目标文档全 0） | ☑ |
| 4 | 门面不蔓延，现有契约零改动 | 9 字段/8 指标/schema/policy 字节不变，只新增不改 | 字节不变断言全过（T13，C6） | ☑ |
| 5 | 首次产出 better/neutral/worse（smoke 级） | 18 次真实模型调用（3 用例 × 3 重复 × 2 源）＋ 评分覆盖 ＋ compare 七字段；本次两侧行为面未变，对照主要价值＝噪声底测量 | smoke 证据落袋（含噪声底记录），不称权威 baseline（S02、S03） | ⚠（挂 U-01、U-08；S02 进行中） |

**我们在哪**：T01–T13 完成、S01 物化完成；S02 进行中（三次尝试留痕，根因＝宿主 cwd 访问限制，修复中）；smoke 定级只挂 U-01。
**下一步**：用户批准本计划与门变更清单 → T01 对齐清单核对 → 数据面（T02–T04）与 isolation（T06）并行 → 接线（T05–T08）→ 钉死与收口（T09–T13）。
**阻塞/风险**：只剩 U-01（可信端点）阻塞 smoke 定级；U-02/U-03 已实测/已决，U-08（宿主机 cwd 访问限制）修复待重跑验证——见未决项表。P0 传导、评分器松紧、脱敏泄漏、门面蔓延、快照漂移五条风险与缓解见「接口与共享机制」。

**前提与假设**：

- aiwork-workflow-ai 本地 clone 可用，目标全 sha 可 checkout，打种配方引用的文件在该 sha 上存在；快照物化只在本地（企业 remote 不回推、不公开）。
- 三个用例的脱敏简报与抽象化种子清单可在不泄漏企业原文的前提下落公开仓；真实路径逐条过门审查后才进公开仓。
- claude host 安装版（baseline）与本地工作树（candidate）同机可用；read-only 权限档的实际行为在 S02 前实测（U-02）。
- 18 次真实模型调用预算随 U-01 获用户批准；dry-run 不产生模型调用。
- 首切片无业务 holdout；评分是对 agent findings 工件的事后离线确定性匹配，不进请求路径、无人工裁量。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| `T01` | 对齐清单核对（parity inventory，开工前置）：逐项读参照源真实实现——eval-case.schema.json、validate.py 的 schema_for（:416）/IMPROVEMENT_SCHEMA_NAMES（:37）/validate_evals、eval_runner.py 的 --suite（:387）/compare 七字段（:344）、host_adapter.py 的 validate_request（:53）/prompt_for_case（:130）/permission_args（:116）、isolation.py 的 layout_errors（:42）——按 replicate / omit-with-reason / defer 定案并回写「对齐清单」表；与计划不符时先回计划修订再开工。验收＝对齐清单表每行有决定与理由 | P0 | plans/PLAN-BUSINESS-EVAL-001.md（对齐清单表回写） | — | ☑ 已完成 | 2026-09-17 逐项对真实实现核对（validate.py 37/47/75/406/416/923/1060、eval_runner.py 37/68/119/332/387、host_adapter.py 29/53/85/116/130/250、isolation.py 14/42/120）；九行决定无需变更 |
| `T02` | 新 schema business-case.schema.json：eval-case 契约（schema_version/case_id/slice/objective/input_ref/acceptance_criteria/protected_guardrails/holdout/repeat_count）之上新增业务字段 target_id/target_pin（全 sha 格式）/seeds_ref/findings 产出契约/grading 阈值（min_seed_recall 等）；input_ref 仍指本仓内脱敏简报；holdout 恒 false；target_id/target_pin/seeds_ref 只做结构校验、不做存在性检查。验收＝C2 schemas 项过 | P0 | skills/improve/references/business-case.schema.json | T01 | ☑ 已完成 | 131 行，Draft 2020-12；三用例 0 error；十类负例全部报错（短/大写 sha、缺 seeds_ref、holdout=true、repeat=2、空 target_docs、多余属性、min_recall=1.5、required_fields 被改、空 guardrails） |
| `T03` | 首切片内容物：三用例 BT-001（种子缺陷文档审查）/BT-002（内部矛盾需求简报审查）/BT-003（跨文档一致性核查），repeat_count 3；脱敏简报 evals/business/inputs/BT-00x.md；抽象化种子清单 evals/business/seeds/BT-00x.seeds.json（每条 seed：seed_id/文件（中性快照路径）/类别/匹配策略；命中阈值在用例级 grading.min_seed_recall；真实路径逐条门审查后才落公开仓）；种子类别必须覆盖「术语歧义」（行话未就地说明）与「跨文档值不一致」（同一约束在多文档复述且不一致）——这两类是「表达纪律」（就地写清＋表格自包含）与「载体扫描」（改值前列全部载体）两个在研方法级候选的测量面，缺失会让首批被度量候选测出无信号。验收＝C3 结构校验过 | P0 | evals/business/BT-001.json–BT-003.json、evals/business/inputs/BT-001.md–BT-003.md、evals/business/seeds/BT-001.seeds.json–BT-003.seeds.json | T02 | ☑ 已完成 | 三用例+三简报+三种子清单（9 条：术语歧义 3、跨文档值不一致 4、文档内矛盾 1、表格不自包含 1）+README；pin=3b379b84（=业务仓 HEAD）；9 个锚点在各自目标文档出现次数全 0（supervisor 复跑）；真实 feature 名 grep 0 命中 |
| `T04` | 确定性评分器 seed_grader.py（新文件）：读种子清单与 agent findings 工件，按每 seed 声明的匹配策略与阈值做确定性匹配，输出 hits/missed/unmatched 与每 repetition 命中率；unmatched 非种子发现只记录不扣分；未知匹配策略 fail-closed。验收＝T09 golden 用例 | P0 | tools/lab/seed_grader.py | T03 | ☑ 已完成 | 330 行纯标准库；未知 strategy.type 与 findings 缺失/不可解析一律 fail-closed（退出码 2）；supervisor 复跑真实种子 BT-001：三 rep 命中 2/0/1，accepted 与 escaped_defects 数值正确，非种子 finding 正确记 unmatched |
| `T05` | validate 接线与门登记（同一人工审批批次、同一提交）：schema_for 增 evals/business → business-case.schema.json 分支；IMPROVEMENT_SCHEMA_NAMES 登记 business-case.schema.json（未登记会被 schema 自检静默跳过）；新增 validate_business_evals（结构校验，不查 target 存在性）并挂进 all；REQUIRED_PROTECTED_PATHS 加 tools/lab/seed_grader.py，protected-paths.txt 同批加一行（EXPECTED_TEST_FILES 不动；先加清单行再加必保集合，中间态可过 validate protected）。验收＝C2/C3 | P0 | tools/lab/validate.py、protected-paths.txt | T04 | ☑ 已完成 | schema 登记（:38）、schema_for 增 evals/business 映射、validate_business_evals（结构+种子交叉校验，不查 target 存在）、evals/all 接线（报告仍 8 行）；protected-paths.txt 增 seed_grader 一行且 check-diff 实测拦截；负例 9 条全部报错；supervisor 复跑 all/evals/protected 全绿 |
| `T06` | isolation 第四位置：layout_errors 增可选第四参（business 快照根），缺省时三参行为与现状逐字节一致（向后兼容）；提供时校验与 repository/candidate(workspace)/holdout 互不嵌套不重合；validate-layout 子命令加同名可选参数。验收＝C5＋T09 三参/四参回归 | P0 | tools/lab/isolation.py | T01 | ☑ 已完成 | layout_errors 可选第四参（缺省逐字节向后兼容；三参调用点未动）；validate-layout 增 --business-root；四参正/反例与三参回归实跑通过 |
| `T07` | eval_runner 业务面：--suite evals/business 套件感知；新增 --business-root（快照根）；请求透传业务字段（用例级 target_id/target_pin/seeds_ref＋请求级 business_root）；fixture_revision 约定 business/<slug>@<全 sha>；compare 七字段（suite_revision/host/model/permissions_profile/fixture_revision/repeat_count/suite_case_count）原样生效。验收＝C2＋T09 契约用例 | P0 | tools/lab/eval_runner.py | T02、T06 | ☑ 已完成 | 套件感知装载（public 路径逐字节不变）；请求透传 6 个业务字段+business_root；缺 --business-root 即拒绝；stub adapter 实测业务/公开两路径均通过 |
| `T08` | host_adapter 业务面：validate_request 业务分支（业务字段必填、business_root 存在且过 isolation 四位置；真跑校验快照 git HEAD 全 sha＝target_pin 且种子 patch 可干净重放（脏树式打种，`git apply --check --reverse` 通过；见 S01），dry-run 只校验结构与布局）；prompt_for_case 业务变体（快照绝对路径作只读输入写进 prompt；host cwd 仍为 workspace）；findings 写 workspace 下 findings/<case_id>/rep-<n>/ 独立子目录；跑后调 seed_grader 覆盖 accepted（种子命中率≥用例阈值）与 escaped_defects（漏检种子数）；first_pass_review 首切片保留自报、以 evidence_refs 指向评分工件标注；自报原始值（accepted/first_pass_review）落 progress JSONL；dry-run 输出业务调用计划。验收＝C4＋T09 正负例 | P0 | tools/lab/host_adapter.py | T04、T06、T07 | ☑ 已完成 | 业务请求分支（6 字段/同 pin/权限档 workspace-write/HEAD=pin/patch 可逆）；prompt 业务变体（快照只读+findings 契约）；每次调用后快照文件集合＋`git diff` 摘要校验；评分覆盖 accepted/escaped_defects 并落 grading.json；新增 --seed-patch；公开路径逐字节不变；supervisor 复跑 all/unittest 全绿 |
| `T09` | tests/test_lab_contracts.py 扩展（不新增测试文件，tests/ 目录内容不变）：seed_grader golden 双向夹具（该命中未命中＝过紧、不该命中命中＝过松）；METRIC_NAMES＝8 指标、repetition＝9 字段钉死断言；validate_business_evals 正负例；isolation 三参/四参回归；adapter 业务请求正负例与 dry-run 文档断言。验收＝C2 单测全绿 | P0 | tests/test_lab_contracts.py | T05、T06、T07、T08 | ☑ 已完成 | 新增 17 个测试（修复轮 B 再增 4，共 21 个新测试 / 40 总数，全绿）；定向变异实跑留痕：M1/M2/M4/M5b 与修复轮 B 三项守卫变异各自触发对应测试失败；M3（修复前）为不失败的反例——即 F6 的依据；supervisor 复跑 40 OK + validate all 8/8 |
| `T10` | 五份 manifest 版本 bump（0.5.2 → 0.6.0，走 minor；定号见 U-04）：plugin.json、marketplace.json、.zcode-plugin/plugin.json、.claude-plugin/plugin.json、.codex-plugin/plugin.json 同步。验收＝C2 manifests 项过 | P1 | plugin.json、marketplace.json、.zcode-plugin/plugin.json、.claude-plugin/plugin.json、.codex-plugin/plugin.json | T09 | ☑ 已完成 | 五份 manifest 0.5.2→0.6.0（各一行 diff，插件名与其余字段未动）；validate manifests/all 全绿；installed 报 0.3.9 快照滞后属预期（重装由用户另行决定） |
| `T11` | CHANGELOG.md 增 0.6.0 条目（含：开发发布、无权威 baseline 证据、安装快照滞后提示）；README.md 增业务切片说明（evals/business 布局与评分语义）。验收＝C2 docs 项过 | P1 | CHANGELOG.md、README.md | T09 | ☑ 已完成 | CHANGELOG 增 0.6.0 条目（含「开发版本、无对照评测证据、measurement: none 未消灭、smoke 挂 U-01/02/03、安装快照滞后」）；README 增 The business evaluation slice 段并同步版本声明；validate docs/all 全绿 |
| `T12` | docs 收口：skills/improve/SKILL.md Measured scope 段更新（有匹配业务用例的方法级改动跑 evals/business，无匹配仍 measurement:none；首切片仅覆盖 aiwork 文档审查类、结果定级 smoke）；docs/agent-roles.md 补业务切片条目；docs/agent-product-boundary.md evals 布局加 evals/business 行；_archive/handoff-2026-10/next-session-handoff.md P1 首项收口。验收＝C2 docs 项过 | P1 | skills/improve/SKILL.md、docs/agent-roles.md、docs/agent-product-boundary.md、_archive/handoff-2026-10/next-session-handoff.md | T09 | ☑ 已完成 | SKILL Measured scope 段更新（有匹配业务用例才可产对照、首切片 smoke 定级）；agent-roles 补业务切片节；product-boundary 布局加 business 行并按 0.6.0 重写描述段；handoff P1 首项收口 + 新增 codex 缺陷条目；contracts.md 未触碰（docs parity 检查 PASS） |
| `T13` | 仪器就绪验收门（离线可判定，不依赖 U-01/U-02/U-03）：validate all 八项全绿；单测全绿；adapter --dry-run 业务请求通过（快照目录用 stand-in：真实存在、互不嵌套的空目录即可，dry-run 不校验 HEAD 与内容）；isolation validate-layout 四参通过；门面字节不变断言通过；证据回写本计划 | P0 | —（验收门，无代码改动；跑「验证命令」C1–C6） | T10、T11、T12 | ☑ 已完成 | 2026-09-17 supervisor 实跑：C1 PASS artifacts；C2 validate all 8/8 + unittest 36 OK；C3 PASS evals；C4 业务 dry-run exit 0（9 次调用计划、prompt 含快照路径）；C5 isolation 四参 exit 0；C6 冻结面零字节差异（exit 0）。仪器就绪，S 阶段待 U-01/U-02/U-03 |
| `S01` | 本地物化 pin 快照：从本地 clone（路径与 remote 地址只留本地）一次性 clone 到第四位置 → checkout 全 sha 冻结 → 按 seeds 配方确定性打种（脏树式：种子以未提交改动落地，HEAD 保持＝pin；重建＝checkout pin＋重放 patch；开跑前校验 HEAD＝pin 且 patch 可逆重放）→ validate-layout 四参通过；快照本体、打种 diff、打种配方、符号→真实路径映射只留本地 | P1 | —（本地操作，产物不入公开仓） | T13 | ☑ 已完成 | 2026-09-17 物化完成（supervisor 实跑留痕）：全量 clone + checkout pin（HEAD==3b379b84…）；三目录改中性名 feature-A/B/C；9 条种子植入且锚点在各自目标文档恰 1 次、全库无真实 feature 名；`git add -A` 后 `diff HEAD` 生成 seed.patch（`apply --check --reverse` exit 0）；`validate_request(dry_run=False)` 四位置+HEAD+patch 全过；`docs/` chmod 只读（写入实测被拒）；diff 摘要两次计算一致 |
| `S02` | smoke 实跑：先 dry-run（不调模型）；baseline 侧＝claude host＋安装版，eval_runner run 跑 3 用例 × repeat_count 3＝9 次真实调用；candidate 侧＝重装本计划落库版本（C8 PASS 后）同规格 9 次；总成本 18 次真实模型调用，超预算须回计划修订；权限档 workspace-write（快照 chmod 只读＋调用后状态校验兜底）；progress JSONL 落本地 | P1 | tools/lab/eval_runner.py（运行入口，无代码改动） | S01 | ◐ 进行中 | 三次尝试（本地 progress JSONL 留痕，不入仓）：①启动约 4 分钟后被会话清理杀死；②宿主约 10.4 分钟后非零退出、诊断文本被 stderr 无害警告掩盖（已修 `claude_failure_detail` 并加测试）；③首调用 314s 跑通至宿主返回结果 JSON，但宿主未写 findings.json → 主动停止并做单调用诊断。fail-closed 已在真实工件上免调用验证（ungradable repetitions 报错）。U-02 已实测（acceptEdits 可写）、U-03 已决（快照位置见 S01）；U-01 可信端点仍未决，数字只作 smoke |
| `S03` | 评分与定级：seed_grader 对两侧 findings 评分（hits/missed/unmatched）；accepted/escaped_defects 覆盖进结果 manifest；first_pass_review 保留自报并经 evidence_refs 标注；compare 七字段产出 deltas → better/neutral/worse；定级为 smoke 证据、不称权威 baseline；本次两侧行为面未变、delta 应≈0——对照的主要价值是噪声底测量（显著偏离零＝仪器不可信，先修仪器再谈候选）；unmatched 中发现的企业文档真实缺陷经人工确认后可回流评审桥作输入；raw result manifest、progress JSONL、findings 只留本地，公开面只出聚合指标与 repo-qualified 引用（aiwork@<全 sha>:<path>）＋脱敏 blockquote 摘录 | P1 | tools/lab/seed_grader.py（运行入口，无代码改动） | S02 | ⚠ 阻塞 | 传导自 S02（见未决项） |
| — | 明确不做（范围外，详见「范围外」小节）：业务 holdout；canary/统计（P2）；ZCode 适配；episode store 集成（P1 下一条，依赖本条）；修复类任务与写权限档；ding-dong/infinite-canvas 第二目标仓；多目标混跑；METRIC_NAMES/结果与发布 schema/policy 变更；push/发布 | — | — | — | — 本期不做 | — |

### 执行与并行

- 执行者约定：仪器阶段由主会话按用户逐批批准执行——T05–T09 触及保护门，属人工审查变更，不作为 improve 环 candidate 执行；S 阶段实跑由 supervisor 派发，评分由 seed_grader 确定性完成（无人工裁量），作者不验证自己的改动。
- 可并行 lane：数据面（T02→T03→T04）与 isolation（T06）互不重叠可并行；T05、T07 依赖数据面后可并行推进；T08 收口接线；T10/T11/T12 互不重叠可并行；S01→S02→S03 严格串行。
- 必须串行：T05（门登记）与 T09（钉死）各自等待其全部依赖落地后才开工；T13 是阶段出口，S 阶段不得抢跑。

### 未决项

| 编号 | 问题 | 是否阻塞 | 状态 |
| --- | --- | --- | --- |
| U-01 | 可信端点：权威评测宿主端点、模型标识与预算未定（本机第三方中转、模型标识不一致，见 handoff「当前风险」） | 阻塞 S02–S03（smoke 实跑与定级）；不阻塞 T01–T13（仪器阶段，离线可判定） | 未关闭（待用户定端点与 18 次预算） |
| U-02 | 权限档：read-only 档在 claude host 的实际拦截行为待实测（print 模式下 sensitive write 与 Bash 审批） | 阻塞 S02；不阻塞 T01–T13 | 已测量关闭（2026-09-17：acceptEdits 无头写入实测成功（探针文件落盘）；业务档定为 workspace-write。**同时发现读侧约束**：cwd 之外的文件访问被工具层拒绝，见 U-08） |
| U-03 | 环境隔离：pin 快照放置位置与实跑环境隔离方案未定（第四位置目录约定、打种机） | 阻塞 S01–S03（smoke 阶段）；不阻塞 T01–T13 | 已决关闭（2026-09-17：第四位置＝本机 smoke 根下 `snapshot/`（路径不入仓），与 repository/workspace/holdout 四位置互不嵌套；S01 已按此物化并校验） |
| U-04 | 版本号：0.6.0（新增能力面，建议）还是 0.5.3 | 不阻塞（T10 合入前确认即可） | 未关闭 |
| U-05 | 评测结果长期落点：聚合指标进记录根（improvements/）还是 examples/（待改进控制面落地时定） | 不阻塞（smoke 结果只留本地） | 未关闭 |
| U-06 | 两处当前态版本横幅未收口：docs/self-improvement-design.md:3、docs/host-native-plugin-design.md:3 仍写 0.5.2（不在 T12 写范围） | 不阻塞 | 已关闭（2026-09-17 两处横幅已更新为 0.6.0 并补业务切片状态） |
| U-07 | codex 侧真跑缺陷：host_adapter.run_codex 用 NamedTemporaryFile 对象调 read_text()（HEAD 即存在），任何 codex 真跑必失败 | 不阻塞（S02 只用 claude host） | 已关闭（2026-09-17 修复落地：按 `Path(output.name)` 读取、失败包成 ValueError；两条 stub 回归测试钉住；真实 codex 真跑仍未验证） |
| U-08 | 宿主文件访问被限制在 cwd：业务跑必须给 claude 传 `--add-dir <快照根>`，否则四份目标文档 Read 全被拒、Bash 被 "only files under <cwd> are permitted" 拦（工具层拒绝、`permission_denials` 为空） | 阻塞 S02 重跑验证（修复已落地、未验证）；不阻塞 T01–T13（仪器阶段） | 修复落地待验证（2026-09-17：`run_claude` 业务命令加 `--add-dir`（解析为绝对路径）+ 两条回归测试 + host-platform-facts C8 留档；smoke 重跑确认前不视为关闭） |

### 评审结论与验证边界（独立评审终审 `approved`，2026-09-17）

本批 delta 经独立评审三轮（`changes_requested` → 修复 → `changes_requested` → 修复 → **`approved`**）。批准口径：**仪器阶段批准；S 阶段受 U-01/U-08 门控**。以下条目按「未验证」原样记录，不得升级为已验证：

1. **U-08 实机确认**：smoke 重跑产出前，`--add-dir` 的实际读写效果未验证——U-08 不关闭。
2. **GitHub Actions 实际运行**未验证（本地等价性已由 8 PASS + 58 OK 证明）。
3. **真实 codex CLI 真跑**未验证（现有证据止于 stub 层）。
4. **`claude_failure_detail` 残差**：`error: null` + 非空 `result` 时仍取 result 文本；真实宿主失败 payload 形状未观测。
5. **delta 变更面为作者声明**：基线 0.6.0 批次整体未提交，git 无法隔离 delta（K1 不可作隔离证据）。
6. **排除声明**：`.commandcode/`、`ANALYSIS-REPORT.md` 不属于本交付（untracked；该文件后已入库，2026-09-18 清理时移至 `_archive/audit-2026-09/`）。
7. **Backlog（人工授权变更，不夹带本批）**：`tools/lab/validate.py` 阻塞未决检测器的「不阻塞」整格豁免盲区；「受保护门工具行为变更须同轮同步 CHANGELOG + iteration-log + 计划看板」——本批第二次出现，建议记 bug/台账。

## 接口与共享机制

### 数据与接口契约

| 接口 | 契约 | 错误行为 | 兼容性 |
| --- | --- | --- | --- |
| business-case.schema.json | eval-case 契约＋业务字段 target_id/target_pin（全 sha 格式）/seeds_ref/findings 产出契约/grading 阈值（min_seed_recall 等）；holdout 恒 false；input_ref 指本仓内脱敏简报 | 缺字段或 target_pin 非全 sha → validate_business_evals FAIL；target_id/target_pin/seeds_ref 只做结构校验、不查存在性 | 只约束 evals/business/**；eval-case.schema.json 与 evals/public 校验字节不变 |
| 种子清单（evals/business/seeds/BT-00x.seeds.json） | 每条 seed：seed_id/文件（中性快照路径）/类别/匹配策略（命中阈值在用例级 `grading.min_seed_recall`）；类别覆盖「术语歧义」与「跨文档值不一致」（在研方法级候选的测量面）；随用例进公开仓，真实路径逐条门审查 | seed_grader 遇未知匹配策略 fail-closed | 无独立 schema 文件；结构由 T09 golden 用例钉死 |
| seed_grader（tools/lab/seed_grader.py） | 输入＝种子清单＋每 repetition 独立 findings 工件；输出＝hits/missed/unmatched＋命中率；accepted 覆盖＝命中率≥用例阈值、escaped_defects 覆盖＝漏检种子数；unmatched 只记录不扣分 | findings 缺失/不可解析 → 该 repetition 评分 fail-closed，不默认 0 分 | 纯事后离线工具，不进请求路径；9 字段/8 指标不动 |
| adapter 业务请求 | 请求级 business_root＋用例级 target_id/target_pin/seeds_ref；prompt 变体嵌入快照绝对路径（只读）；host cwd 仍 workspace；权限档 workspace-write（findings 需可写；快照只读靠 chmod＋调用后状态校验：文件集合＋`git diff` 摘要）；findings 写 workspace 下 findings/<case_id>/rep-<n>/；跑后调 seed_grader 覆盖 accepted/escaped_defects；first_pass_review 保留自报、evidence_refs 指向评分工件标注；自报原始值落 progress JSONL | 业务字段缺失/快照不存在或嵌套/真跑时快照 HEAD≠target_pin 或种子 patch 不能干净重放 → 请求拒绝；调用后快照内容漂移或评分覆盖集不等于期望 rep 集 → 运行失败；dry-run 只校验结构与布局 | 公开套件请求路径不变；结果 schema 字节不变 |
| isolation 第四位置 | layout_errors 可选第四参＝business 快照根；提供时校验与 repository/candidate(workspace)/holdout 互不嵌套不重合 | 嵌套/重合 → 布局 FAIL | 缺省时三参行为逐字节一致（向后兼容） |
| eval_runner 业务面 | --suite evals/business；--business-root；请求透传业务字段；fixture_revision 约定 business/<slug>@<全 sha>；compare 七字段原样生效 | 布局/一致性不符 → FAIL，不产出结果 | 既有 --suite evals/public 路径不变 |
| 评分结果语义 | evaluation-result.schema.json 字节不变；accepted/escaped_defects 只换值不换字段；语义标注经 evidence_refs＋文档＋发布记录表达，不加 schema 字段 | — | 顶层 17 字段、repetition 9 字段、summary 8 指标、policy 全部字节不变（硬验收线） |

### 共享机制（注册点）

| 共享机制 | 注册点 | 行为 | 受影响表面 |
| --- | --- | --- | --- |
| schema 分发表 | tools/lab/validate.py:416（schema_for）、:37（IMPROVEMENT_SCHEMA_NAMES）、:406（iter_schema_paths） | evals/business/ → business-case.schema.json 新分支；名字进 IMPROVEMENT_SCHEMA_NAMES 才会被 schema 自检（:411 未登记即静默跳过） | evals/public 分支与 eval-case.schema.json 不动 |
| 保护门清单 | tools/lab/validate.py:47（REQUIRED_PROTECTED_PATHS）＋ protected-paths.txt | T05 同一批加 tools/lab/seed_grader.py | validate protected 门面扩展；EXPECTED_TEST_FILES（validate.py:75）不动 |
| 隔离布局 | tools/lab/isolation.py:42（layout_errors）；调用点 tools/lab/host_adapter.py:85、tools/lab/eval_runner.py:242 | 可选第四参，缺省逐字节向后兼容；提供时四路互不嵌套 | 既有三位置断言不动；两处调用点同步透传 |
| 指标与结果契约 | tools/lab/eval_runner.py:37（METRIC_NAMES）、tools/lab/host_adapter.py:29（CASE_RESULT_SCHEMA → schemas/adapter-case-result.schema.json）、schemas/evaluation-result.schema.json、tools/lab/policy.py | 全部字节不变；accepted/escaped_defects 只换值；first_pass_review 保留自报 | T09 钉死断言＋T13 的 C6 字节不变检查 |
| 结果比较 | tools/lab/eval_runner.py:344（compare 七字段） | 原样生效；fixture_revision 复用 business/<slug>@<全 sha> | baseline/candidate 一致性门槛不变 |
| 权限档 | tools/lab/host_adapter.py:116（permission_args） | claude read-only＝plan 模式＋禁 Bash/Write/Edit；**业务请求改为 workspace-write**（findings 需写 workspace）；业务请求拒绝 read-only 档，快照只读由「打种时 chmod 只读＋每次调用后快照 git status 校验」兜底 | 公开套件权限映射不变；业务仓写入仍不做（快照只读） |

### 门变更清单（供用户人工审批）

| 路径 | 变更性质 | 说明 |
| --- | --- | --- |
| tools/lab/validate.py | 修改（保护门内） | schema_for/IMPROVEMENT_SCHEMA_NAMES/validate_business_evals/all 挂接/REQUIRED_PROTECTED_PATHS 加 seed_grader |
| tools/lab/eval_runner.py | 修改（保护门内） | 套件感知/请求透传业务字段/--business-root |
| tools/lab/host_adapter.py | 修改（保护门内） | 业务请求校验/prompt 变体/findings 子目录契约/评分器调用与覆盖 |
| tools/lab/isolation.py | 修改（保护门内） | layout_errors 可选第四参 |
| tools/lab/seed_grader.py | 新增（随本清单进保护门） | 确定性评分器 |
| protected-paths.txt | 修改（自指门） | ＋tools/lab/seed_grader.py 一行；EXPECTED_TEST_FILES 不动 |
| tests/test_lab_contracts.py | 扩展（保护门内） | 不新增测试文件，tests/ 目录内容不变 |
| evals/business/** | 新增 | evals/ 前缀已在清单内，无需改 |
| skills/improve/references/business-case.schema.json | 新增 | skills/improve/references/ 前缀已在清单内，无需改 |

### 验收断言：明确不动

- tools/lab/policy.py（:116/:120 上下文字段检查原样）
- schemas/evaluation-result.schema.json（顶层 17 字段、repetition 9 字段、summary 8 指标）
- skills/improve/references/release-record.schema.json
- schemas/adapter-case-result.schema.json（9 字段结果契约）
- skills/improve/references/eval-case.schema.json
- evals/public/**（AF-001–AF-015）
- agents/evaluator.md、agents/release-governor.md
- EXPECTED_TEST_FILES（tools/lab/validate.py:75；不新增测试文件）

### 脱敏边界

- 进公开仓：脱敏任务简报（evals/business/inputs/BT-00x.md）；抽象化种子清单（真实路径逐条门审查）；findings 产出契约；聚合指标。
- 只留本地：企业原文；打种 diff；pin 快照本体；符号→真实路径映射；raw result manifest 与 progress JSONL；打种配方。
- 引用规范：公开记录引用企业仓一律 repo-qualified（aiwork@<全 sha>:<path>）＋脱敏 blockquote 摘录；validator 对 target_id/target_pin/seeds_ref 只做结构校验、不做存在性检查（避免把企业路径拉进公开校验面）。

### 对齐清单（parity inventory，T01 回写处）

| 参照元素（真实来源） | 决定 | 说明 |
| --- | --- | --- |
| eval-case.schema.json 字段契约（skills/improve/references/eval-case.schema.json） | replicate＋扩展 | 业务字段为新增；原 schema 字节不动 |
| evals/public 用例布局与 input_ref 校验（tools/lab/validate.py:416 schema_for、validate_evals） | replicate | evals/business/ 平行目录；input_ref 仍指本仓内文件、存在性照查；业务字段只查结构 |
| --suite 装载（tools/lab/eval_runner.py:387） | replicate＋新参 | --suite evals/business；新增 --business-root；默认值不动 |
| adapter 请求契约（tools/lab/host_adapter.py:53 validate_request） | replicate＋业务分支 | 公开套件请求路径行为不变；业务请求走新分支 |
| prompt 构造（tools/lab/host_adapter.py:130 prompt_for_case） | replicate＋变体 | 业务变体嵌入快照绝对路径作只读输入；host cwd 仍 workspace |
| 隔离布局三位置（tools/lab/isolation.py:42 layout_errors） | replicate＋第四位置 | 可选第四参向后兼容；既有三位置断言不动 |
| compare 七字段（tools/lab/eval_runner.py:344） | replicate 原样 | fixture_revision 复用 business/<slug>@<全 sha> |
| holdout 机制（私有 holdout 与第三位置） | omit（有理由） | 首切片无业务 holdout（D5 明确不做，P2 再议） |
| canary/统计置信、ZCode 适配 | defer | 样本充分后（P2）；首切片只上 claude host |

### 风险与缓解

| 风险 | 缓解 | 落点 |
| --- | --- | --- |
| P0 阻塞传导：端点/权限档/环境隔离未决拖死整个交付 | 仪器就绪以离线判据收口（validate all＋dry-run），不依赖任何 P0 项；smoke 单独挂起并在未决项表分项标注 | T13、未决项表 |
| 评分器匹配规则过紧/过松：种子判不准，better/worse 失真 | 每 seed 显式声明匹配策略与阈值；golden 双向夹具（该命中未命中、不该命中命中）；unmatched 非种子发现只记录不扣分 | T04、T09 |
| 脱敏泄漏：findings/progress/raw manifest 携企业原文进公开仓 | 三类工件只留本地；进公开仓内容按脱敏边界逐条过审；validator 不做存在性检查 | T03、S03 |
| 门面蔓延：为业务切片顺手改指标/schema/policy | 明确不动清单＋C6 字节不变断言＋T09 钉死 METRIC_NAMES/9 字段；确需改契约时停下来提人工变更，不在本计划内夹带 | T05、T09、T13 |
| 快照漂移：上游 aiwork 推进导致快照不可复现 | 全 sha 冻结＋fixture_revision 记 business/<slug>@<全 sha>＋脏树式打种（HEAD 保持＝pin，重建＝checkout＋重放 patch）＋打种配方留本地；上游冲突时显式重 pin 并回写计划，不静默跟进 | S01 |
| F5 残差：补丁新增的未跟踪文件，其**内容**改写对 `git diff` 摘要不可见 | 该场景落在打种约定之外（打种只改文档内容、不改目录结构）；文件集合校验只覆盖其**存在性**；S01 实测快照确为只读并留痕 | S01 |

### 异常矩阵（smoke 链路）

| 异常场景 | 检测 | 处理 | 结果 |
| --- | --- | --- | --- |
| adapter 超时/宿主失败 | host_adapter 既有超时与 progress failed 事件 | 记失败不静默重试；预算内不追加调用 | progress JSONL failure 记录 |
| 评分器遇未知匹配策略 | seed_grader fail-closed | 报错退出，不猜测策略 | FAIL 输出，评分中止 |
| findings 工件缺失/不可解析 | seed_grader 前置检查 | 该 repetition 评分 fail-closed | FAIL 输出，不默认 0 分 |
| 快照 HEAD 与 target_pin 不符，或种子 patch 不能干净重放 | adapter 真跑前校验（HEAD 比对＋`git apply --check --reverse`） | 拒绝开跑 | 请求拒绝 |
| 调用后快照出现种子清单外改动或内容漂移 | adapter 每次调用后复检（文件集合＋`git diff` 摘要） | fail-closed，不继续后续调用 | 运行失败（progress failed＋非零退出） |
| 评分覆盖的 rep 集不等于期望集（多余/缺失 rep 目录） | seed_grader 返回后 adapter 校验 | fail-closed，不返回宿主自报值 | 运行失败 |
| 脱敏审查不过 | S03 公开面审查 | 相关内容只留本地，不进公开仓 | 待整改记录 |

### 评审门与回滚点

- 评审门 1（计划与门变更批准，用户，T01 前）：批准本计划＝授权仪器阶段开工；门变更清单需逐条人工批准后才可执行 T05–T09（AGENTS.md：保护路径/必保集合/发布策略的修改属人工审查变更）。
- 评审门 2（仪器门，T13）：C1–C6 全绿才算仪器就绪；证据回写本计划后 S 阶段才可排期。
- 评审门 3（smoke 门，S02 前）：U-01/U-02/U-03 关闭，或用户当次明确豁免（豁免记录进未决项表）。
- 评审门 4（定级复核，S03 后）：smoke 证据只证明管线贯通与评分器工作；P0 端点未决前不升级为权威 baseline，方法优劣结论不外推。
- 回滚点：每任务独立提交可 revert；T05 门变更单独成提交（revert 即同时退 validate.py 与 protected-paths.txt 两处）；T10 版本 bump 回滚需重装宿主快照并跑 C8 复验；S 阶段产物只在本机，删目录即回滚；不 push 不发布，远端无回滚面。

### 范围外（明确不做）

- 业务 holdout（防过拟合业务用例集）
- canary/统计置信区间（P2，样本充分后）
- ZCode 适配（首切片只上 claude host）
- episode store 集成（P1 下一条，依赖本条落地）
- 修复类任务与写权限档（首切片只做审查类＋read-only）
- ding-dong/infinite-canvas 第二目标仓
- 多目标混跑
- METRIC_NAMES/结果与发布 schema/policy 变更（字节不变是硬验收线）
- push/发布（本计划全程不推送不发布）

## 验证命令

命令在本仓根执行；尖括号 <…> 为运行期占位（sha、绝对路径、模型标识），执行时代入实际值并回写证据列。C1–C6 属仪器阶段（离线），C7 属 smoke 阶段，C8 属发布面，C9 属 smoke 前置（快照校验）。

```sh
# C1 计划与记录校验（本文件自身）
python3 tools/lab/validate.py artifacts
# 预期：PASS artifacts

# C2 仪器就绪门（T13；离线可判定，不依赖 U-01/U-02/U-03）
python3 tools/lab/validate.py all
# 预期：schemas / examples / evals / artifacts / protected / manifests / docs / tests 八项全 PASS
python3 -m unittest discover -s tests
# 预期：OK（含 seed_grader golden、METRIC_NAMES/9 字段钉死、isolation 三参四参、adapter 业务请求用例）

# C3 业务套件结构校验（T05 后随时可跑）
python3 tools/lab/validate.py evals
# 预期：PASS evals（evals/business 三用例与种子清单过结构校验；不检查 target 存在性）

# C4 adapter dry-run（T13；不发起模型调用；workspace/holdout/快照用真实存在、互不嵌套的目录，
#    快照可为空占位（stand-in 表面＝存在目录＋布局合法＋路径可入 prompt，不含 HEAD/内容校验））
python3 - <<'PY' | python3 tools/lab/host_adapter.py --host claude --dry-run
import json
repo = "<本仓绝对路径>"
cases = [
    {
        "case_id": f"BT-00{i}",
        "slice": "business-doc-review",
        "objective": "<用例 objective 原文>",
        "input_ref": f"evals/business/inputs/BT-00{i}.md",
        "holdout": False,
        "repeat_count": 3,
        "target_id": "aiwork-workflow-ai",
        "target_pin": "<40 位全 sha>",
        "seeds_ref": f"evals/business/seeds/BT-00{i}.seeds.json",
        "target_docs": ["<中性快照路径>"],
        "findings_contract": {
            "path_pattern": "findings/{case_id}/rep-{rep}/findings.json",
            "format": "json",
            "required_fields": ["path", "issue", "evidence"],
        },
        "grading": {"min_seed_recall": 0.5},
    }
    for i in (1, 2, 3)
]
print(json.dumps({
    "protocol_version": 1,
    "host": "claude",
    "source_kind": "baseline",
    "source_revision": "<安装版修订>",
    "artifact_digest": "sha256:<64 位十六进制>",
    "result_id": "DRY-BUSINESS-001",
    "agentflow_version": "<安装版版本>",
    "suite_revision": "<evals/business 冻结修订>",
    "model": "<模型标识>",
    "permissions_profile": "workspace-write",
    "fixture_revision": "business/aiwork-workflow-ai@<40 位全 sha>",
    "repository_root": repo,
    "workspace_root": "<workspace 绝对路径>",
    "holdout_root": "<holdout 绝对路径>",
    "business_root": "<pin 快照绝对路径>",
    "repeat_count": 3,
    "cases": cases,
}))
PY
# 预期：stdout 为 dry-run 调用计划（3 用例 × 3 repetition，prompt 含快照只读绝对路径），退出码 0，无模型调用

# C5 isolation 四位置布局检查（T06 后；缺第四参时输出与现状一致）
python3 tools/lab/isolation.py validate-layout \
  --repository <本仓绝对路径> --candidate <workspace 或 candidate worktree 绝对路径> \
  --holdout <holdout 绝对路径> --business-root <pin 快照绝对路径>
# 预期：输出含四根路径的 JSON，退出码 0；嵌套/重合时 FAIL isolation layout

# C6 门面字节不变（T13；<基线修订>＝T 阶段开工前的冻结提交）
git diff --exit-code <基线修订> -- \
  tools/lab/policy.py \
  schemas/evaluation-result.schema.json \
  skills/improve/references/release-record.schema.json \
  schemas/adapter-case-result.schema.json \
  skills/improve/references/eval-case.schema.json \
  evals/public \
  agents/evaluator.md \
  agents/release-governor.md
# 预期：退出码 0、零输出；EXPECTED_TEST_FILES 未动由 validate.py tests 断言

# C7 smoke 阶段（S01–S03；挂 U-01/U-02/U-03，解阻后执行）
python3 tools/lab/eval_runner.py run \
  --suite evals/business --source-kind baseline \
  --source-revision <安装版修订> --artifact-digest sha256:<候选工件摘要> \
  --agentflow-version <安装版版本> --suite-revision <evals/business 冻结修订> \
  --host claude --model <模型标识> --permissions-profile workspace-write \
  --fixture-revision business/aiwork-workflow-ai@<40 位全 sha> \
  --repeat-count 3 --result-id <结果 id> \
  --repository <本仓绝对路径> --workspace <workspace 绝对路径> \
  --holdout-root <holdout 绝对路径> --business-root <pin 快照绝对路径> \
  --adapter "<宿主 adapter 命令，含 --progress <本地 progress JSONL 路径>>" \
  --output <baseline 结果 JSON 路径>
# 预期：WROTE <baseline 结果 JSON>；candidate 侧先过 C8 重装，再同规格跑一次（source-kind candidate）
python3 tools/lab/eval_runner.py compare \
  --baseline <baseline 结果 JSON> --candidate <candidate 结果 JSON> --output <对比 JSON>
# 预期：七字段一致则产出 deltas（8 指标差值）；不一致 FAIL comparison inputs

# C8 发布面（T10 后重装宿主快照）
python3 tools/lab/validate.py installed
# 预期：重装后 PASS installed；未重装时 FAIL 属预期（快照滞后，见 handoff「当前风险」）

# C9 快照校验（S01/S02；脏树式：HEAD 保持＝pin，种子 patch 以未提交改动落地）
git -C <pin 快照绝对路径> rev-parse HEAD
# 预期：等于 target_pin 全 sha
git -C <pin 快照绝对路径> apply --check --reverse <种子 patch 路径>
# 预期：退出码 0（补丁已干净套上、可逆重放）；任一不过 → 拒绝开跑
```
