---
plan_id: PLAN-REVIEW-001
plan_version: 0.1.0
status: approved
objective: 把 2026-10-25 总体评审的四维结论（安装面断裂、门逻辑绕过、声明与执行脱钩、记录面倒挂）转成 26 项带破坏例判据的修复任务；受保护路径任务与删除类任务各自等待授权后开工
recorded_at: 2026-10-25T16:23:53+08:00
---

# 总体评审吸收与修复批 — 执行计划（PLAN-REVIEW-001）

> 执行契约，不是改代码授权。每完成一项只回写「状态」与「证据」两列（最小 diff），绝不重写已完成行。
> `status: approved` 的依据：2026-10-29 用户对受保护路径门变更给了整体授权，Q-01 至 Q-05 已逐条关闭；
> 2026-10-30 用户指示「全部完成」，本批活任务已落地。删除类 T18–T22 按 2026-10-29 拍板留下一批。
> 开工基线：`main` @ `a2725a5`；2026-10-30 收口时工作树含此前未提交的第二段改动。

## 进展概览

- 总任务 30 项：☑ 30 项已完成 / — 0 / ☐ 0。删除类 T18–T22 已于 2026-10-30 执行。
  受保护路径任务 13 项已全部落地；删除类 5 项已于 2026-10-30 完成。出提案不实施 2 项（T25、T26）已于 2026-10-29 完成。
- 三视角概览：

| 视角 | 现在在哪 | 下一步 | 阻塞 |
| --- | --- | --- | --- |
| 方法维护者 | 30 项已闭，Q-01 至 Q-05 全部关闭；删除类 5 项已于 2026-10-30 执行 | 删除后复测产出比 | 无 |
| 工具链实现 | 四组门绕过逐项修复；删除类已执行 | 复跑全量门 | 无 |
| 交付效果 | 记录面基线 23,030 行已留档；本批未执行删除，产出比复测随下一批 | 下一批删除后复测（目标 ≤ 2.5） | 无 |

- 阻塞与风险：无阻塞。Q-01 至 Q-05 已全部关闭；T05 统一解析器按「先基线、后统一」执行，
  2026-10-30 的 `doc_chain_live` 与三份存量批次实跑均未因解析器统一而新增红。

## 分支策略

| 仓 | 基线 | 开发分支 | 纪律 |
| --- | --- | --- | --- |
| 本仓（agentflows） | `main` @ `a2725a5` | 直接在 `main` 执行，不新建分支（沿用追溯批先例） | 提交、推送、发布、宿主重装各自需用户当次授权；同一文件同一时刻单一写入者——T05 涉及的四个工具文件串行改，不并行；门变更完成后必须经独立评审，作者不验收自己的改动 |
| `/tmp` 一次性副本 | 从受信检出 `cp -r` | 不在副本上提交 | 破坏性探针与变异测试只在副本运行；恢复只在检查复跑并观察到转绿后才算数 |

## 任务清单

> 「受保护」＝任务落点在 `protected-paths.txt` 清单内，属门变更：候选不得直接实施，需用户显式授权
> 并走人工评审。全部任务状态为 ☐ 未开始，证据列待回写。

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 按 Q-01 选定路线闭合安装面：A——`packaging/build_runtime.py` 白名单纳入运行期所需检查器（`docchain/` 与精简校验入口），skill 内跨仓用法以 `--root` 写明可照抄；B——安装面文本撤回全部 `python3 tools/lab/` 命令，改为「需源码检出」前置声明（受保护） | P0 | `packaging/build_runtime.py`、`skills/agentflow/SKILL.md`、`skills/agentflow/references/document-chain.md` | — | ☑ 已完成 | `packaging/build_runtime.py` 的 RUNTIME_SUBTREES 含 `tools/lab/docchain`；`skills/agentflow/SKILL.md` 的跨仓用法写明 `--root`；`validate.py manifests` 2026-10-30 实跑 PASS |
| T02 | 修复安装态断链 4 文件 6 条（改仓限定引用或并入安装树）；`gate/manifests.py` 新增「安装树内相对链接可解析」断言并输出扫描对象计数（受保护，门变更） | P0 | `tools/lab/gate/manifests.py`、`skills/agentflow/SKILL.md`、`skills/agentflow/references/hosts.md`、`skills/agentflow/templates/host/README.md` | — | ☑ 已完成 | `tools/lab/gate/manifests.py` 的 shipped-surface 链接断言；`tests/test_gate_integrity.py` 的 test_shipped_runtime_broken_relative_link_is_reported 2026-10-30 实跑 OK |
| T03 | 门输出可审计三件：`validate.py` 各项 PASS 附扫描对象计数；`doc_chain.py --help` 打印用法退出码 0；`lint` 在 ruff/mypy 缺失时输出「未运行」而非失败（受保护；lint 语义变更随 Q-01 一并确认） | P1 | `tools/lab/validate.py`、`tools/lab/docchain/cli.py` | — | ☑ 已完成 | `tools/lab/validate.py` 的 `_scan_count`/report 计数已上线；`tools/lab/docchain/cli.py` 的 --help 退出 0；`tests/test_gate_integrity.py` 的计数用例实跑 OK。lint 缺依赖仍红（2026-10-26 审计的 lint fail-closed 项，fail-closed 保留）；解释器优先级 `AGENTFLOW_LINT_PYTHON` → `.venv` → 当前解释器（2026-10-28 评测 B3） |
| T04 | `record_store.py` 重建索引时在同一事务删除失效行（修「索引只增不删」）；`query` 的报错从 SystemExit 改普通异常（受保护） | P1 | `tools/lab/record_store.py` | — | ☑ 已完成 | `tools/lab/record_store.py` 重建索引同事务删除失效行、query 抛 RecordQueryError；`tests/test_record_store.py` 的 test_reindex_removes_rows_for_deleted_files 与 test_query_raises_ordinary_exception_not_system_exit 实跑 OK |
| T05 | 统一 Markdown 表格行解析：`gate/plan.py` 与 `gate/testing.py` 复用 `docchain` 的行解析器，接受无尾随竖线的 CommonMark 表格；依赖列与状态列一律按列名读取（消除 `cells[4]` 位置耦合）；补「无尾随竖线仍被两门读到」破坏例（受保护） | P0 | `tools/lab/gate/common.py`、`tools/lab/gate/plan.py`、`tools/lab/gate/testing.py`、`tools/lab/docchain/checks.py` | — | ☑ 已完成 | `tools/lab/gate/common.py` 的 header_columns 与共享 split row；`tests/test_gate_schema.py` 的 test_task_table_without_trailing_pipes_is_still_read 实跑 OK |
| T06 | 取消测试运行记录的「旧版本免检」：结果表至少一行且四项摘要合计大于零成为硬性要求；`test_plan_version` 必须与所引计划 frontmatter 的 `test_version` 可对上；补「零用例 pass」破坏例（受保护） | P0 | `tools/lab/gate/testing.py`、`tests/test_gate_records.py` | T05 | ☑ 已完成 | `tools/lab/gate/testing.py` 的结果表至少一行与版本匹配判据；`tests/test_gate_records.py` 的 test_zero_case_pass_run_is_rejected 与 test_run_pinning_a_plan_version_that_never_existed_is_rejected 实跑 OK |
| T07 | 计划未决项门改按列名读取 `是否阻塞`，接受「是 / 否」与「阻塞 / 不阻塞」两种写法，官方三列模板形态进入检查；补 G2-AC-01 / G2-AC-02 两组破坏例（受保护） | P0 | `tools/lab/gate/plan.py`、`tests/test_gate_integrity.py` | T05 | ☑ 已完成 | `tools/lab/gate/plan.py` 的 _blocking_cell 按列名读取；`tests/test_gate_schema.py` 的 test_blocking_decision_is_read_from_the_column_not_the_prose 实跑 OK |
| T08 | schema 两处 fail-closed：`is_type` 对未知 `type` 报错；`check_schema_keywords` 校验 `type` 取值合法；补 `"type": "objct"` 破坏例（受保护） | P0 | `tools/lab/gate/common.py`、`tools/lab/gate/schema.py`、`tests/test_gate_schema.py` | — | ☑ 已完成 | `tools/lab/gate/common.py` 的 SUPPORTED_JSON_TYPES 与 is_type fail-closed；`tools/lab/gate/schema.py` 的 check_schema_keywords type 校验；`tests/test_gate_schema.py` 的 test_unknown_schema_type_fails_closed 实跑 OK |
| T09 | 两条判据形态修复：`C3` 识别 `spec/checklist.md` 官方模板形态（「未确认」+「阻塞阶段」列）；`C16` 来源回溯对不存在的仓内 `ISS-*` 不再按外部来源放行（受保护） | P1 | `tools/lab/docchain/checks.py` | — | ☑ 已完成 | `tools/lab/docchain/checks.py` 的 C3 checklist 形态与 C16 ISS 解析；`tools/lab/docchain/selftest.py` 用例 59a–59c/68a–68b；`doc_chain.py --self-test` 146/146 |
| T10 | 0.15.0 测试契约「实现或撤回」二选一：来源列非空、`## 数据来源` 节、结果表实际结果列、run findings 的 `ISS` 存在性（撤掉 `workspace.py` 的 deferred）四项逐项落定；`tests/test_gate_records.py` 夹具同步改强契约；CHANGELOG 与 `test-records.md` 声明与实现逐条对齐（受保护） | P0 | `tools/lab/gate/testing.py`、`tools/lab/gate/workspace.py`、`tests/test_gate_records.py`、`skills/agentflow/references/test-records.md` | — | ☑ 已完成 | `tools/lab/gate/testing.py` 的来源列/实际结果列校验；`tools/lab/gate/workspace.py` 的 run findings ISS 交叉核对（deferred 注释已删）；`tests/test_gate_records.py` 两个新用例与 `skills/agentflow/references/test-records.md` 的撤回声明 |
| T11 | 角色文件缺漏修复：`plan-architect.md` 补 `## 分支策略` 章节要求；`test-planner.md` / `test-executor.md` 字段清单补 schema 全部必填项；`agents/README.md` 幽灵「产物归属表」指针改指各角色文件产物矩阵；`bug-recorder` 归档移动与三个无 Bash 记录角色的时间戳 / revision 供给协议补写（由主对话执行或供给） | P1 | `agents/plan-architect.md`、`agents/test-planner.md`、`agents/test-executor.md`、`agents/README.md`、`agents/bug-recorder.md` | — | ☑ 已完成 | 前四项随 `4c5c17a` 落地（分支策略节、必填十项、幽灵指针改产物矩阵、归档移动归主对话）；2026-10-29 补最后一项——`agents/plan-architect.md`、`agents/test-planner.md`、`agents/bug-recorder.md` 各增「时间戳与 revision 的供给」段（无 Bash 角色由主对话供给，未给写「待主对话供给」）。验证：`validate.py docs` PASS、`validate.py manifests` PASS（生成树已重建） |
| T12 | `validate.py docs` 新断言：`agents/` 无角色文件即红、`skills/` 无 SKILL.md 即红、角色文件声明的固定章节与 schema 必填字段交叉核对（消灭「按角色文件字面产出被门拒」一类）（受保护，门变更） | P1 | `tools/lab/gate/docs.py`、`tools/lab/gate/common.py` | T10、T11 | ☑ 已完成 | `tools/lab/gate/docs.py` 的 ROLE_SCHEMA_CONTRACTS/role_contract_findings 与 skills 空壳断言；`tests/test_gate_schema.py` 的两个 role 交叉核对用例实跑 OK |
| T13 | 三处矛盾收口：`roles.md` 测试链默认序列补评审角色；评审范围口径统一为「由 diff 形状决定」（改 `roles.md` 一侧）；执行记录更正口径统一为「更正就地编辑并刷新 `updated_at`，同时在变更记录留痕」（受保护侧为 roles.md 不在清单内，普通改动） | P1 | `skills/agentflow/references/roles.md`、`agents/test-executor.md`、`skills/agentflow/references/test-records.md` | — | ☑ 已完成 | 三处均随 `4c5c17a` 落地：`skills/agentflow/references/roles.md` 测试链默认序列补 Reviewer、评审范围统一为「由 diff 形状决定」；`skills/agentflow/references/test-records.md` 第 38–40 行写明执行记录更正由主对话执行并刷新 `updated_at`（仅追加的历史不为讲圆故事改写）。2026-10-29 复核三处原文在场 |
| T14 | 工具白名单口径：清理或保留冗余 `disallowedTools` 声明，`AGENTS.md` 措辞改为「仅 `tools` 已验证强制」（对齐 `host-platform-facts.md` Z4 的实测边界） | P2 | `AGENTS.md` | T11 | ☑ 已完成 | `AGENTS.md`「编辑角色或 skill」节已写「只有 `tools` 在 ZCode 实测被宿主强制执行；`disallowedTools` 在 Qoder 等宿主未验证，`maxTurns` 只声明、未验证」；`agents/README.md` 第 42 行同步声明其不构成隔离保证。**决定：保留** 7 个角色文件的 `disallowedTools` 声明（`agents/bug-investigator.md`、`agents/bug-recorder.md`、`agents/plan-architect.md`、`agents/reviewer.md`、`agents/technical-director.md`、`agents/test-executor.md`、`agents/test-planner.md`）——它们表达意图且已被文档标注为非强制，删除会丢失意图 |
| T15 | 幽灵测试类勘误追平：`MutationKillCorpusTests` 与 `SchemaSubsetFailClosedTests` 在九处引用（计划 T05 行、评审记录两处、episode 两处、评测报告两处等）逐处补勘误标注——只追加，不改写原文 | P0 | `docs/features/feature-2026-10-13-质量提升/plan/PLAN-QUALITY-001.md`、`docs/features/feature-2026-10-13-质量提升/reviews/review-2026-10-19-001.md`、`episodes/归档/2026-10/2026-10-19/EP-2026-10-19-001.json`（2026-10-29 随月度归档移入）、`docs/evaluations/AGENTFLOW-EVALUATION-2026-10-20.md` | — | ☑ 已完成 | 2026-10-30 复扫：逐条命中与计数见 `testing/agentflow-review/evidence/erratum-scan-2026-10-30.txt`（含命令、扫描面与 path:line 原文）；按 T16 的「更正来源 + 未带勘误/N/A」口径，未追平引用 = 0，`validate.py docs` PASS；N/A: 两类均为幽灵测试类，从未进入提交历史；扫描原文见 `testing/agentflow-review/evidence/erratum-scan-2026-10-30.txt`。原 9 处由 `4c5c17a` 补勘误，`9ef0b0e` 重写 T05 证据列；2026-10-30 又给 `AGENTFLOW-EVALUATION-2026-10-20.md` 与 `review-2026-10-19-001.md` 的剩余两处补了勘误标注 |
| T16 | 新增「更正必须追平」检查：凡 CHANGELOG 或记录出现「从未进入 / 不实 / 勘误」更正语句，被更正标识符在 `docs/`、`reviews/`、`agents/`、`skills/`、`episodes/` 下 md 与根 README/AGENTS/CHANGELOG/index 的其余引用处须带勘误标注（episodes JSON 为历史证据，不在扫描面）；实现触发词为「从未进入/不实/勘误/证伪」，追踪对象限反引号包裹的 `*Tests`/`*Cases` 形标识符，文件级证据由 C23 承担，否则门红；配破坏例夹具（受保护，门变更） | P1 | `tools/lab/gate/docs.py` | T15 | ☑ 已完成 | `tools/lab/gate/docs.py` 的 correction_propagation_findings；`tests/test_gate_schema.py` 的 test_correction_propagation_flags_unannotated_references 实跑 OK |
| T17 | `C23` 增「断言可解析」层：证据列反引号引用的类名 / 文件名 / 函数名须在仓内可解析；以幽灵测试类构造正例夹具（受保护，门变更） | P1 | `tools/lab/docchain/checks.py` | — | ☑ 已完成 | `tools/lab/docchain/checks.py` 的 assertion_resolvability_findings；`tools/lab/docchain/selftest.py` 用例 95a–95e；`doc_chain.py --self-test` 146/146 |
| T18 | `docs/product/` 结论（产品定位 / 方法行为规格要点）并入 `docs/design-decisions.md` 一节后整目录删除；两道挂起评审门的处置随迁说明；状态三说一并消失（删除类，Q-04） | P1 | `docs/design-decisions.md` | — | ☑ 已完成 | docs/design-decisions.md §4 已并入产品链结论；`docs/product/` 5 个文件删除；两道评审门处置随节说明；原文 git 40147df。 |
| T19 | `docs/evaluations/` 留三删五：保留独立评测（6.43）、10-23 审核、评测任务书；7.6 / 7.7 加「历史自我评分，已被 6.43 证伪，勿引用」标注后归档；10-12 行动件清「待回填」占位后归档（删除类，Q-04） | P1 | `docs/evaluations/README.md` | — | ☑ 已完成 | `docs/evaluations/README.md` 已加「留三归档五」；10-12 两件、7.6/7.7、Youc 复盘共 5 件移入 `docs/evaluations/archive/`，7.6/7.7 加证伪标注。 |
| T20 | 16 条外部项目记录（`ISS-2026-09-19-office计划缺异常矩阵` 至 `ISS-2026-09-19-office计划事件清理回放缺口`）迁出至 infinite-canvas 仓或单文件汇总；`docs/issues/recurrence/` 对应台账改指针（删除类，Q-04） | P1 | `docs/issues/ISS-2026-09-19-office计划采纳汇总.md` | — | ☑ 已完成 | 16 条 office 记录已汇总为 `docs/issues/ISS-2026-09-19-office计划采纳汇总.md`；原记录删除；评审 findings 与 recurrence 指针改汇总号。 |
| T21 | CHANGELOG 改「每版 ≤10 行 + 细节入 episode」形态；旧内容随版本归档进 git 历史；0.15.0 安装面「同日 FAIL / PASS」改为时间线一句（删除类，Q-04；CHANGELOG 历史条目按原样保留的口径随本项一并定） | P2 | `CHANGELOG.md` | — | ☑ 已完成 | `CHANGELOG.md` 压缩为 0.23.0 与 2026-10-30 各 3 行；详细记录移入 `docs/changelog-archive.md`；0.15.0 同日 FAIL/PASS 保留在归档时间线。 |
| T22 | 执行既有删档规则：关闭 `feature-2026-09-19-产品线完善` 批（结论入 CHANGELOG 与 episode 后删目录）；`episodes/` 空轮次与无 claims 早期记录按月归档；`reviews/` 内部重复快照去重（外部快照保留）（删除类，Q-04） | P2 | `docs/design-decisions.md`、`episodes/2026-10-30/EP-2026-10-30-001.json` | — | ☑ 已完成 | 产品线批次已关闭删除（结论见 `CHANGELOG.md` 与 `episodes/2026-10-30/EP-2026-10-30-001.json`）；episodes 无空轮次；reviews 无同轮重复快照可去重，外部快照保留。 |
| T23 | 术语表落地：`docs/system-guide.md` 首节一表（台账 / 拍板口 / 门 / 档位 / 收口 / 承接 / 落点 / 载体 / 批次 / 链 / 口径）；`README.md`、`index.md`、`docs/quickstart.md` 对照词表清零内部词裸用 | P1 | `docs/system-guide.md`、`README.md`、`index.md`、`docs/quickstart.md` | — | ☑ 已完成 | `docs/system-guide.md` §0「术语对照」已建 11 词表（台账 / 拍板口 / 门 / 档位 / 收口 / 承接 / 落点 / 载体 / 批次 / 链 / 口径）；`index.md` 顶部有词表指针；`docs/quickstart.md` 与 `README.md` 的「文档档位」均为指向定义的链接。2026-10-29 清理 `README.md` 最后一处裸用：「批次流程」→「成批流程」、「会话收口」→「会话收尾」 |
| T24 | 最小必读面瘦身：四文件（skill + roles + contracts + reviewer）只消副本、不设总量上限（Q-05 2026-10-29 拍板 C）——去重以引用代替复述、「分派前必读」改「按链必读」 | P2 | `skills/agentflow/SKILL.md`、`skills/agentflow/references/roles.md`、`skills/agentflow/references/contracts.md`、`agents/reviewer.md` | — | ☑ 已完成 | 由 FIX T12 落地：`skills/agentflow/SKILL.md` 152 行、`skills/agentflow/references/roles.md`、`skills/agentflow/references/contracts.md`、`agents/reviewer.md` 已只消副本；四文件实测 622 行（152/124/197/149）；见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` T12 行 |
| T25 | 文档链默认档改轻提案：默认「一页提案 + 验收判据 + 计划看板」，全链为按需启用加强档；本任务只产提案文本（Q-02 拍板后另批实施） | P2 | `skills/agentflow/references/document-chain.md` | — | ☑ 已完成 | `skills/agentflow/references/document-chain.md` 末新增「待拍板提案：默认档改轻（Q-02）」节（文件 317 → 345 行），含问题陈述、A/B/C 三选项与各自做/不做后果、推荐 B 及理由、落地前置四项；节首明标「提案，未生效」。**只出提案不实施**，契约正文未改 |
| T26 | 改进环处置落地：按 Q-03（即 `docs/PENDING-DECISIONS.md` 第 10 条）拍板结果执行冻结 / 裁撤 / 保留；裁撤时设计知识留 `docs/design-decisions.md` §3，恢复清单口径不变 | P2 | `docs/design-decisions.md` | — | ☑ 已完成 | 2026-10-29 用户拍板 B（整体裁撤），由 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 的 T20 实施；设计知识与恢复清单见 `docs/design-decisions.md` §3 |
| T27 | 决策登记册改只追加（D8 Tier 0/1）：`docs/PENDING-DECISIONS.md` 第 7 行规则改为「只追加、永不移出」，条目加 `DEC-<YYYY>-<NNN>` 前缀与修订链 r1…rN、终态三分（superseded / withdrawn / deferred）、`equivalent_to`；新增 `tools/lab/decisions.py view` 生成未决视图，撤销手工搬行 | P0 | `docs/PENDING-DECISIONS.md`；待核实（本批新建）：`tools/lab/decisions.py`、决策台账 schema | — | ☑ 已完成 | `tools/lab/decisions.py` 的 view/parse_ledger；`docs/PENDING-DECISIONS.md` 只追加规则与 DEC 修订列（一次性迁移例外：2026-10-30 前 15 条按旧规则移出，保留注记与 git 历史）；`tests/test_decisions.py` 29 用例实跑 OK |
| T28 | 下游声明依赖（D8 Tier 2）：批次 README 与阶段文档 frontmatter 支持 `decision_deps: [DEC-YYYY-NNN#rN]` 或 `[DEC-YYYY-NNN#invariant=原文]`；文档链契约补该字段口径与「立账门槛」两条判据 | P1 | `skills/agentflow/references/document-chain.md`、待核实（本批新建）：`tools/lab/decisions.py` 的 extract_decision_deps 与 `skills/agentflow/references/document-chain.md` 第 10 条 | T27 | ☑ 已完成 | `skills/agentflow/references/document-chain.md` 第 10 条 decision_deps 口径；`tools/lab/decisions.py` 的 extract_decision_deps；`tests/test_decisions.py` 正/破坏/不误伤三组夹具 |
| T29 | 横向检查（D8 Tier 3）：`tools/lab/decisions.py check` 扫全仓 frontmatter 算反向索引，只报真正受影响的文档（钉 r2 报红；钉 r1 且新版 `equivalent_to: r1` 保持绿）；每条只能「改文本并升版本」或「登记 `stale_reason` + 复核日期」；补正例、破坏例、不误伤例三组夹具（受保护，门变更） | P0 | 待核实（本批新建）：`tools/lab/decisions.py`、`tests/test_decisions.py`；`tools/lab/gate/checks.py` | T27、T28 | ☑ 已完成 | `tools/lab/decisions.py` 的 check；`tools/lab/gate/checks.py` 的 decision_gate 无条件调用 check/verify_index；`tests/test_decisions.py` 的 gate 接线用例与 29 用例实跑 OK |
| T30 | 决策索引机器生成（D8 Tier 4）：`decisions.py index --write` 产出 `docs/decisions/index.md`，手改即红（生成文件哈希断言） | P2 | 待核实（本批新建）：`tools/lab/decisions.py`、`docs/decisions/index.md` | T27 | ☑ 已完成 | `tools/lab/decisions.py` 的 render_index/verify_index/write_index；`docs/decisions/index.md` 生成文件与 digest；`tests/test_decisions.py` 的 test_index_hand_edit_trips_digest 实跑 OK |

### 未决项

> 五项全部阻塞 `status: approved` 的转换；选项与推荐见提案 §六，此处只登记状态。

| 编号 | 问题 | 状态 | 是否阻塞 |
| --- | --- | --- | --- |
| Q-01 | 门工具交付路线（A 随插件打包 / B 撤回命令） | 已关闭（2026-10-29 用户拍板 **A**：检查器随插件打包，skill 内跨仓用法以 `--root` 写明） | 阻塞 |
| Q-02 | 文档链默认档改轻（T25 仅出提案不阻塞实施） | 提案已交付（T25，见 `skills/agentflow/references/document-chain.md` 末节）；翻转默认档属契约与 C26 判据变更，另批实施 | 不阻塞 |
| Q-03 | 改进环处置（以 `docs/PENDING-DECISIONS.md` 第 10 条为准） | 已关闭（2026-10-29 拍板 B 整体裁撤；T26 已完成） | 阻塞 |
| Q-04 | 记录面五项删减授权（T18 至 T22） | 已关闭（2026-10-29 用户授权删除，删前先跑引用改写判据） | 阻塞 |
| Q-05 | 最小必读面瘦身幅度（T24 可先出方案） | 已关闭（2026-10-29 拍板：只消副本、不设总量上限；T24 由 FIX T12 落地） | 不阻塞 |

## 接口与共享机制

| 机制 | 注册点或落点 | 本批如何经过它 | 冲突面 |
| --- | --- | --- | --- |
| 受保护路径清单 | `protected-paths.txt`（单点声明） | T01 至 T09、T12、T16、T17 共 12 项触及清单内路径，全部按门变更走人工评审授权；候选不得直接实施 | 清单覆盖不足则 `validate.py protected` 红 |
| 回归测试登记 | `tools/lab/gate/checks.py` 的 `EXPECTED_TEST_FILES` 与 `protected-paths.txt` | T06 至 T08 若新增测试文件，同一变更内登记进两张清单 | 漏登记即 `tests` 门红 |
| 生成树联动 | `packaging/build_runtime.py` → `packaging/runtime` | T11、T13、T14、T24、T25、T26 改 `agents/` 或 `skills/` 后必须重建生成树并复跑 `manifests` | 未重建会静默装出旧角色 |
| 表格行解析 | `gate/common.py` 与 `docchain/` 两套 | T05 合一（以 `docchain` 口径为准）；此后任何新判据禁止另起解析正则 | 两套方言在不同批次给出不同绿（提案 §2.2 L3） |
| 自测用例下限 | `tools/lab/gate/common.py` 的 `MIN_DOC_CHAIN_SELF_TEST_CASES` | 只增不减，不改下限数值 | 夹具缩水即门红 |
| 计划回写纪律 | 各批次 `plan/` 任务表 | 只回写状态与证据两列；承接表状态列随看板聚合同步（README 承接表） | 与 `C22` 状态聚合读取同源 |
| 目标编号口径 | 本计划与批次 README 承接表共用 G1 至 G6 | 新增目标须同时进提案 §1.2 与承接表，否则 `C22` 红 | 幻影目标 / 缺承接都会红 |

## 验证命令

> 每条在对应任务完成后执行并留逐字输出；基线动作（第一行）在 T05 动第一行工具代码之前完成。

| 命令 | 预期结果 | 关联验收点 |
| --- | --- | --- |
| `python3 tools/lab/doc_chain.py docs/features/feature-2026-09-19-产品线完善` 及另外两个存量批次目录（改动前留基线） | 三份基线输出落盘；T05 之后复跑，findings 变化逐条解释（存量批次不因解析器统一而新增红） | G2-AC-04 |
| `python3 tools/lab/doc_chain.py docs/features/feature-2026-10-25-总体评审吸收与修复` | `PASS doc-chain`，退出码 0 | G1-AC-01、G3-AC-03 |
| `python3 tools/lab/doc_chain.py --repo .` | `PASS decision-gate`，输出附扫描对象计数 | G2-AC-06 |
| `python3 tools/lab/doc_chain.py --help` | 打印用法，退出码 0 | G2-AC-06 |
| `python3 tools/lab/doc_chain.py --self-test` | N = M 且 N 只增不减；新增破坏例（未决项三态、零用例 pass、无尾竖线、未知 type、假 ISS、勘误未追平、断言不可解析）逐例在场 | G2-AC-01 至 G2-AC-05、G4-AC-02、G4-AC-03 |
| `python3 -m unittest discover -s tests` | `Ran N tests` 且 N ≥ 92，OK | G2-AC-01 至 G2-AC-04 |
| `python3 tools/lab/validate.py all` | 全部 PASS；每项附扫描对象计数；lint 缺依赖仍红（2026-10-26 审计的 lint fail-closed 项），解释器按 `AGENTFLOW_LINT_PYTHON` → `.venv` → 当前解释器（B3） | G2-AC-06 |
| `python3 tools/lab/validate.py manifests` 与 `installed` | manifests PASS（含新链接断言）；T01 选 A 路线后 installed 转绿（装后走查由用户执行并回写 `docs/releases/pending-test.md`） | G1-AC-01 至 G1-AC-03 |
| 可计数检索脚本（非裸 `grep`）：两个幽灵类名 × 勘误词；内部词词表 × 三份入口文档；`python3 tools/lab/` × 安装面文本 | 幽灵类未勘误处 = 0；入口文档内部词裸用 = 0；按 Q-01 路线核命令引用数 | G4-AC-01、G6-AC-01、G1-AC-02 |
| 记录面行数统计脚本（`docs/` + `episodes/` + `reviews/` + 根文件四类） | 相对基线 23,030 下降 ≥40%，输出留档 | G5-AC-02 |
| `/tmp` 副本：`record_store` 删除重建实测 | 删除源文件并重建索引后查询不再命中，逐字输出留档 | G2-AC-07 |
