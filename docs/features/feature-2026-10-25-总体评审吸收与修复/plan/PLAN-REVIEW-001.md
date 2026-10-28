---
plan_id: PLAN-REVIEW-001
plan_version: 0.1.0
status: proposed
objective: 把 2026-10-25 总体评审的四维结论（安装面断裂、门逻辑绕过、声明与执行脱钩、记录面倒挂）转成 26 项带破坏例判据的修复任务；受保护路径任务与删除类任务各自等待授权后开工
recorded_at: 2026-10-25T16:23:53+08:00
---

# 总体评审吸收与修复批 — 执行计划（PLAN-REVIEW-001）

> 执行契约，不是改代码授权。每完成一项只回写「状态」与「证据」两列（最小 diff），绝不重写已完成行。
> `status: proposed` 的依据：立项授权是用户 2026-10-25 指示「提一个 feature……全都写进去」（授权范围＝成文）；
> 实施（尤其受保护路径上的门变更与五项删除动作）需 Q-01 至 Q-05 拍板及逐项授权后才转 approved 开工。
> 开工基线：`main` @ `a2725a5`，工作树干净（本批立项仅新增本目录三个文件与索引回写）。

## 进展概览

- 总任务 30 项：☐ 30 项未开始。其中受保护路径任务 13 项（T01 至 T09、T12、T16、T17、T29——触
  `tools/lab/` 或 `packaging/`，属门变更，需显式人工评审授权）；删除类任务 5 项（T18 至 T22，打包
  等 Q-04）；出提案不实施 2 项（T25、T26 部分）。
- 三视角概览：

| 视角 | 现在在哪 | 下一步 | 阻塞 |
| --- | --- | --- | --- |
| 方法维护者 | 问题清单、评分理由与方案已收口进提案；任务表带逐项落点与破坏例判据 | Q-01 至 Q-05 拍板；需求评审门与技术方案评审门勾选 | 拍板未完成前不转 approved |
| 工具链实现 | 四组门绕过有可复现步骤（提案 §2.2）；夹具与修法逐项对位 | 授权后按 T05 → T06 / T07 顺序开工（共享解析器先行） | 受保护路径逐项授权 |
| 交付效果 | 记录面基线 23,030 行已留档（提案 §八） | T18 至 T22 执行后复测产出比（目标 ≤ 2.5） | Q-04 删除授权 |

- 阻塞与风险：五个待拍板事项（Q-01 至 Q-05）全部登记于提案 §六；本计划不替用户预填任何选项。
  风险最高项：T05 统一解析器会同时改变 `artifacts` 与 `doc_chain` 两门对同一份产物的判定——必须
  先对三个存量批次跑改前基线（T03 前置的基线动作并入验证命令首行），判据过宽误伤存量文档时收窄
  实现并补夹具，禁止靠摘标记或删夹具转绿。

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
| T01 | 按 Q-01 选定路线闭合安装面：A——`packaging/build_runtime.py` 白名单纳入运行期所需检查器（`docchain/` 与精简校验入口），skill 内跨仓用法以 `--root` 写明可照抄；B——安装面文本撤回全部 `python3 tools/lab/` 命令，改为「需源码检出」前置声明（受保护） | P0 | `packaging/build_runtime.py`、`skills/agentflow/SKILL.md`、`skills/agentflow/references/document-chain.md`、`skills/improve/SKILL.md` | — | ☐ 未开始 | — |
| T02 | 修复安装态断链 4 文件 6 条（改仓限定引用或并入安装树）；`gate/manifests.py` 新增「安装树内相对链接可解析」断言并输出扫描对象计数（受保护，门变更） | P0 | `tools/lab/gate/manifests.py`、`skills/agentflow/SKILL.md`、`skills/agentflow/references/hosts.md`、`skills/agentflow/templates/host/README.md`、`skills/improve/references/evidence-and-release.md` | — | ☐ 未开始 | — |
| T03 | 门输出可审计三件：`validate.py` 各项 PASS 附扫描对象计数；`doc_chain.py --help` 打印用法退出码 0；`lint` 在 ruff/mypy 缺失时输出「未运行」而非失败（受保护；lint 语义变更随 Q-01 一并确认） | P1 | `tools/lab/validate.py`、`tools/lab/docchain/cli.py` | — | ☐ 未开始 | — |
| T04 | `record_store.py` 重建索引时在同一事务删除失效行（修「索引只增不删」）；`query` 的报错从 SystemExit 改普通异常（受保护） | P1 | `tools/lab/record_store.py` | — | ☐ 未开始 | — |
| T05 | 统一 Markdown 表格行解析：`gate/plan.py` 与 `gate/testing.py` 复用 `docchain` 的行解析器，接受无尾随竖线的 CommonMark 表格；依赖列与状态列一律按列名读取（消除 `cells[4]` 位置耦合）；补「无尾随竖线仍被两门读到」破坏例（受保护） | P0 | `tools/lab/gate/common.py`、`tools/lab/gate/plan.py`、`tools/lab/gate/testing.py`、`tools/lab/docchain/checks.py` | — | ☐ 未开始 | — |
| T06 | 取消测试运行记录的「旧版本免检」：结果表至少一行且四项摘要合计大于零成为硬性要求；`test_plan_version` 必须与所引计划 frontmatter 的 `test_version` 可对上；补「零用例 pass」破坏例（受保护） | P0 | `tools/lab/gate/testing.py`、`tests/test_gate_records.py` | T05 | ☐ 未开始 | — |
| T07 | 计划未决项门改按列名读取 `是否阻塞`，接受「是 / 否」与「阻塞 / 不阻塞」两种写法，官方三列模板形态进入检查；补 G2-AC-01 / G2-AC-02 两组破坏例（受保护） | P0 | `tools/lab/gate/plan.py`、`tests/test_gate_integrity.py` | T05 | ☐ 未开始 | — |
| T08 | schema 两处 fail-closed：`is_type` 对未知 `type` 报错；`check_schema_keywords` 校验 `type` 取值合法；补 `"type": "objct"` 破坏例（受保护） | P0 | `tools/lab/gate/common.py`、`tools/lab/gate/schema.py`、`tests/test_gate_schema.py` | — | ☐ 未开始 | — |
| T09 | 两条判据形态修复：`C3` 识别 `spec/checklist.md` 官方模板形态（「未确认」+「阻塞阶段」列）；`C16` 来源回溯对不存在的仓内 `ISS-*` 不再按外部来源放行（受保护） | P1 | `tools/lab/docchain/checks.py` | — | ☐ 未开始 | — |
| T10 | 0.15.0 测试契约「实现或撤回」二选一：来源列非空、`## 数据来源` 节、结果表实际结果列、run findings 的 `ISS` 存在性（撤掉 `workspace.py` 的 deferred）四项逐项落定；`tests/test_gate_records.py` 夹具同步改强契约；CHANGELOG 与 `test-records.md` 声明与实现逐条对齐（受保护） | P0 | `tools/lab/gate/testing.py`、`tools/lab/gate/workspace.py`、`tests/test_gate_records.py`、`skills/agentflow/references/test-records.md` | — | ☐ 未开始 | — |
| T11 | 角色文件缺漏修复：`plan-architect.md` 补 `## 分支策略` 章节要求；`test-planner.md` / `test-executor.md` 字段清单补 schema 全部必填项；`agents/README.md` 幽灵「产物归属表」指针改指各角色文件产物矩阵；`bug-recorder` 归档移动与三个无 Bash 记录角色的时间戳 / revision 供给协议补写（由主对话执行或供给） | P1 | `agents/plan-architect.md`、`agents/test-planner.md`、`agents/test-executor.md`、`agents/README.md`、`agents/bug-recorder.md` | — | ☐ 未开始 | — |
| T12 | `validate.py docs` 新断言：`agents/` 无角色文件即红、`skills/` 无 SKILL.md 即红、角色文件声明的固定章节与 schema 必填字段交叉核对（消灭「按角色文件字面产出被门拒」一类）（受保护，门变更） | P1 | `tools/lab/gate/docs.py`、`tools/lab/gate/common.py` | T10、T11 | ☐ 未开始 | — |
| T13 | 三处矛盾收口：`roles.md` 测试链默认序列补评审角色；评审范围口径统一为「由 diff 形状决定」（改 `roles.md` 一侧）；执行记录更正口径统一为「更正就地编辑并刷新 `updated_at`，同时在变更记录留痕」（受保护侧为 roles.md 不在清单内，普通改动） | P1 | `skills/agentflow/references/roles.md`、`agents/test-executor.md`、`skills/agentflow/references/test-records.md` | — | ☐ 未开始 | — |
| T14 | 工具白名单口径：清理或保留冗余 `disallowedTools` 声明，`AGENTS.md` 措辞改为「仅 `tools` 已验证强制」（对齐 `host-platform-facts.md` Z4 的实测边界） | P2 | `AGENTS.md` | T11 | ☐ 未开始 | — |
| T15 | 幽灵测试类勘误追平：`MutationKillCorpusTests` 与 `SchemaSubsetFailClosedTests` 在九处引用（计划 T05 行、评审记录两处、episode 两处、评测报告两处等）逐处补勘误标注——只追加，不改写原文 | P0 | `docs/features/feature-2026-10-13-质量提升/plan/PLAN-QUALITY-001.md`、`docs/features/feature-2026-10-13-质量提升/reviews/review-2026-10-19-001.md`、`episodes/2026-10-19/EP-2026-10-19-001.json`、`docs/evaluations/AGENTFLOW-EVALUATION-2026-10-20.md` | — | ☐ 未开始 | — |
| T16 | 新增「更正必须追平」检查：凡 CHANGELOG 或记录出现「从未进入 / 不实 / 勘误」更正语句，被更正标识符在全仓其余引用处须带勘误标注，否则门红；配破坏例夹具（受保护，门变更） | P1 | `tools/lab/gate/docs.py` | T15 | ☐ 未开始 | — |
| T17 | `C23` 增「断言可解析」层：证据列反引号引用的类名 / 文件名 / 函数名须在仓内可解析；以幽灵测试类构造正例夹具（受保护，门变更） | P1 | `tools/lab/docchain/checks.py` | — | ☐ 未开始 | — |
| T18 | `docs/product/` 结论（产品定位 / 方法行为规格要点）并入 `docs/design-decisions.md` 一节后整目录删除；两道挂起评审门的处置随迁说明；状态三说一并消失（删除类，Q-04） | P1 | `docs/design-decisions.md` | — | ☐ 未开始 | — |
| T19 | `docs/evaluations/` 留三删五：保留独立评测（6.43）、10-23 审核、评测任务书；7.6 / 7.7 加「历史自我评分，已被 6.43 证伪，勿引用」标注后归档；10-12 行动件清「待回填」占位后归档（删除类，Q-04） | P1 | `docs/evaluations/README.md` | — | ☐ 未开始 | — |
| T20 | 16 条外部项目记录（`ISS-2026-09-19-office计划缺异常矩阵` 至 `ISS-2026-09-19-office计划事件清理回放缺口`）迁出至 infinite-canvas 仓或单文件汇总；`docs/issues/recurrence/` 对应台账改指针（删除类，Q-04） | P1 | `docs/issues/ISS-2026-09-19-office计划缺异常矩阵.md` | — | ☐ 未开始 | — |
| T21 | CHANGELOG 改「每版 ≤10 行 + 细节入 episode」形态；旧内容随版本归档进 git 历史；0.15.0 安装面「同日 FAIL / PASS」改为时间线一句（删除类，Q-04；CHANGELOG 历史条目按原样保留的口径随本项一并定） | P2 | `CHANGELOG.md` | — | ☐ 未开始 | — |
| T22 | 执行既有删档规则：关闭 `feature-2026-09-19-产品线完善` 批（结论入 CHANGELOG 与 episode 后删目录）；`episodes/` 空轮次与无 claims 早期记录按月归档；`reviews/` 内部重复快照去重（外部快照保留）（删除类，Q-04） | P2 | `docs/features/feature-2026-09-19-产品线完善/README.md`、`episodes/归档/` | — | ☐ 未开始 | — |
| T23 | 术语表落地：`docs/system-guide.md` 首节一表（台账 / 拍板口 / 门 / 档位 / 收口 / 承接 / 落点 / 载体 / 批次 / 链 / 口径）；`README.md`、`index.md`、`docs/quickstart.md` 对照词表清零内部词裸用 | P1 | `docs/system-guide.md`、`README.md`、`index.md`、`docs/quickstart.md` | — | ☐ 未开始 | — |
| T24 | 最小必读面瘦身：四文件（skill + roles + contracts + reviewer，现 587 行）压到 ≤350 行——去重以引用代替复述、「分派前必读」改「按链必读」；方案先出，Q-05 拍板后实施 | P2 | `skills/agentflow/SKILL.md`、`skills/agentflow/references/roles.md`、`skills/agentflow/references/contracts.md`、`agents/reviewer.md` | — | ☐ 未开始 | — |
| T25 | 文档链默认档改轻提案：默认「一页提案 + 验收判据 + 计划看板」，全链为按需启用加强档；本任务只产提案文本（Q-02 拍板后另批实施） | P2 | `skills/agentflow/references/document-chain.md` | — | ☐ 未开始 | — |
| T26 | 改进环处置落地：按 Q-03（即 `docs/PENDING-DECISIONS.md` 第 10 条）拍板结果执行冻结 / 裁撤 / 保留；裁撤时设计知识留 `docs/design-decisions.md` §3，恢复清单口径不变 | P2 | `skills/improve/SKILL.md`、`agents/evaluator.md`、`agents/release-governor.md`、`agents/feedback-analyst.md`、`agents/candidate-engineer.md` | — | ☐ 未开始 | — |
| T27 | 决策登记册改只追加（D8 Tier 0/1）：`docs/PENDING-DECISIONS.md` 第 7 行规则改为「只追加、永不移出」，条目加 `DEC-<YYYY>-<NNN>` 前缀与修订链 r1…rN、终态三分（superseded / withdrawn / deferred）、`equivalent_to`；新增 `tools/lab/decisions.py view` 生成未决视图，撤销手工搬行 | P0 | `docs/PENDING-DECISIONS.md`；待核实（本批新建）：`tools/lab/decisions.py`、决策台账 schema | — | ☐ 未开始 | — |
| T28 | 下游声明依赖（D8 Tier 2）：批次 README 与阶段文档 frontmatter 支持 `decision_deps: [{id, rev}]` 或 `{id, invariant}`；文档链契约补该字段口径与「立账门槛」两条判据 | P1 | `skills/agentflow/references/document-chain.md`、待核实（本批新建）：`tools/lab/docchain/constants.py` 的依赖字段口径 | T27 | ☐ 未开始 | — |
| T29 | 横向检查（D8 Tier 3）：`tools/lab/decisions.py check` 扫全仓 frontmatter 算反向索引，只报真正受影响的文档（钉 r2 报红；钉 r1 且新版 `equivalent_to: r1` 保持绿）；每条只能「改文本并升版本」或「登记 `stale_reason` + 复核日期」；补正例、破坏例、不误伤例三组夹具（受保护，门变更） | P0 | 待核实（本批新建）：`tools/lab/decisions.py`、`tests/test_decisions.py`；`tools/lab/gate/checks.py` | T27、T28 | ☐ 未开始 | — |
| T30 | 决策索引机器生成（D8 Tier 4）：`decisions.py index --write` 产出 `docs/decisions/index.md`，手改即红（生成文件哈希断言） | P2 | 待核实（本批新建）：`tools/lab/decisions.py`、`docs/decisions/index.md` | T27 | ☐ 未开始 | — |

### 未决项

> 五项全部阻塞 `status: approved` 的转换；选项与推荐见提案 §六，此处只登记状态。

| 编号 | 问题 | 状态 | 是否阻塞 |
| --- | --- | --- | --- |
| Q-01 | 门工具交付路线（A 随插件打包 / B 撤回命令） | 尚未关闭 | 阻塞 |
| Q-02 | 文档链默认档改轻（T25 仅出提案不阻塞实施） | 尚未关闭 | 阻塞 |
| Q-03 | 改进环处置（以 `docs/PENDING-DECISIONS.md` 第 10 条为准） | 尚未关闭 | 阻塞 |
| Q-04 | 记录面五项删减授权（T18 至 T22） | 尚未关闭 | 阻塞 |
| Q-05 | 最小必读面瘦身幅度（T24 可先出方案） | 尚未关闭 | 不阻塞 |

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
| `python3 tools/lab/validate.py all` | 全部 PASS；每项附扫描对象计数；缺 ruff/mypy 时 lint 记「未运行」 | G2-AC-06 |
| `python3 tools/lab/validate.py manifests` 与 `installed` | manifests PASS（含新链接断言）；T01 选 A 路线后 installed 转绿（装后走查由用户执行并回写 `docs/releases/pending-test.md`） | G1-AC-01 至 G1-AC-03 |
| 可计数检索脚本（非裸 `grep`）：两个幽灵类名 × 勘误词；内部词词表 × 三份入口文档；`python3 tools/lab/` × 安装面文本 | 幽灵类未勘误处 = 0；入口文档内部词裸用 = 0；按 Q-01 路线核命令引用数 | G4-AC-01、G6-AC-01、G1-AC-02 |
| 记录面行数统计脚本（`docs/` + `episodes/` + `reviews/` + 根文件四类） | 相对基线 23,030 下降 ≥40%，输出留档 | G5-AC-02 |
| `/tmp` 副本：`record_store` 删除重建实测 | 删除源文件并重建索引后查询不再命中，逐字输出留档 | G2-AC-07 |
