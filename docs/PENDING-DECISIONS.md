# 待用户拍板的事项

> 跨计划的「等用户拍板」事项统一登记在本文件（来源、问题、推荐、状态）。会话与计划会有
> 很多份，拍板口只有一个——这里是唯一需要用户逐条回复的清单。
>
> 规则：**只追加、永不移出**。新事项登记为 `未决`，赋予 `DEC-YYYY-NNN` 编号；
> 拍板后写成 `已拍板（日期 · 结论）`，并随结论演进推进修订链 `r1…rN`（每改一次正文升一版）。
> 一条决策关闭后**不移除**，而是转入终态三分之一——`superseded`（被新版本取代）/
> `withdrawn`（撤回）/ `deferred`（推迟）——留在表内，编号持续可引用（G7-AC-01）。
> 一条修订的文本若与早前某版等价（仅换表述不改约束），在 `等价` 列登记 `r<N>`，
> 钉定该早版的下游客体因此不误红（G7-AC-03）。实现若偏离被拍板的结论，不得回写成已拍板，
> 另行登记新条目再向用户确认。未决视图由 `tools/lab/decisions.py view` 生成，手工搬行数为 0。
> 2026-10-29 曾以「拍板后移出本表」为规则；2026-10-30 本批（T27）改为「只追加、永不移出」，
> 以终结「手工搬行 + 表后留出处」的腐烂源（D8 设计，提案 §4.2）。
> **一次性迁移例外**：2026-10-30 之前按旧规则移出的 15 条已闭合条目保留在表后注记与 git 历史
> （如 `agentflows@6229a65`），不追溯重建为 DEC 行；新规则自 2026-10-30 起对新增/未关闭决策生效。
>
> agentflow 决策记录
>
> 本行标记是**启用门检查的声明**，不是注释：`tools/lab/docchain/checks.py` 的
> `DECISION_MARKER` 常量（定义在 836 行附近，消费在 `repo_policy_findings`）以此字符串为开关，
> 去掉它 C16（八列形态）与 C17（核验过期）就不再照本文件。引用它请按**符号名**找，别按行号——
> 本文件此前写的 `checks.py:719` 已经过时（那一行现在是 C19 的报错字面量），2026-11-02 全量核对时更正。
> 2026-10-29 移出表尾历史注记时曾把它一并删掉，`decision_gate` 当场转为「不检查所以绿」，
> 已按「不得靠摘标记转绿」的既有规则恢复并把它单独成行。
>

| # | 来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策 | 状态 | DEC编号 | 修订 | 撤回 | 等价 | 终态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `agentflows@c8ed0b2:docs/features/feature-2026-10-25-总体评审吸收与修复/plan/PLAN-REVIEW-001.md` Q-05（T24） | 最小必读面瘦身幅度：A 维持现状 B 压到 ≤350 行 C 压到 ≤450 行；2026-10-29 用户改拍「只消副本、不设总量上限」（原 C 的 ≤450 不再适用） | 2026-10-30 `wc -l skills/agentflow/SKILL.md skills/agentflow/references/roles.md skills/agentflow/references/contracts.md agents/reviewer.md` 实测合计 622 行（152 / 124 / 197 / 149）；用户 2026-10-29 改拍「只消副本、不设总量上限」，T24 由 FIX T12 落地 | 只消副本、不设总量上限（B 的 ≤350 与 C 的 ≤450 均不再作为上限） | 已关闭：2026-10-29 用户拍板 C | P2 | 多模块(`skills/agentflow/SKILL.md`、`skills/agentflow/references/roles.md`、`skills/agentflow/references/contracts.md`、`agents/reviewer.md`) | N | 已拍板（2026-10-29 · C：只消副本、不设总量上限） | DEC-2026-001 | r2 |  |  |  |
| 2 | `skills/agentflow/templates/testing/plan.md:10`（ac_refs 字段，2026-11-04 可用性批新增；实锤=2026-11-02 登录批次 spec/qa 27 处「待覆盖」与 testing 30/30 并存，桌面四份复盘一致推荐） | C28「AC↔用例双向闭合与覆盖回写」是否进 doc_chain：A 新增——spec/qa 定义的 AC 集合 = testing plan `ac_refs` 并集，plan 落盘后残留「待覆盖」即红（代价：无 AC 体系的批次需写豁免声明一行）；B 不新增——维持门外 `check-testcases.py` 按需跑（代价：没人跑时 27 处残留复发，与本次事故同型）；C 改判据——只查「待覆盖」残留不查集合相等（代价：漏删用例不报警） | 2026-11-04 `grep -c C28 tools/lab/docchain/checks.py` = 0（检查不存在）且 `grep -c C30 tools/lab/docchain/checks.py` = 0；`skills/agentflow/templates/testing/plan.md` frontmatter 已加 `ac_refs`；`skills/agentflow/scripts/check-testcases.py`（门外）已实现同等校验、自测 4/4 | A 新增（推荐）：模板已铺好字段，门只做机器执法；无 AC 体系的项目按现有豁免声明跳过 | 用户拍板 A/B/C 后按结论实施（属 protected 面，人工编写） | P1 | 多模块(`tools/lab/docchain/checks.py`、`tools/lab/docchain/constants.py`、`tools/lab/docchain/selftest.py`、`skills/agentflow/templates/testing/plan.md`) | N | 未决 | DEC-2026-002 | r1 |  |  |  |
| 3 | `skills/agentflow/templates/feature/design/be/backend.md:70`（§1.3.2 已改「DDL 或等效结构契约」，2026-11-04 可用性批；实锤=2026-11-02 登录批次 design/be 以 `N/A: 无数据库` 一句通过全部 8 轮评审，连实体字段表都没有） | C29「实体字段表」是否进 doc_chain：A 新增——design/be 声明无 DDL 或无数据库时必须存在逐实体字段表（字段名/类型/空值/默认/唯一性/敏感性），一句话 N/A 判红，只许「无表」不许「无结构」（代价：无领域实体的纯转发接口要多写一行 `N/A: 无领域实体+理由`）；B 不新增——靠模板与 reviewer 自觉（代价：模板改了但无机器执法，弱模型批次复发）；C 改判据——仅要求声明「有无领域实体」不要求字段表（代价：字段靠读代码猜的现状不变） | 2026-11-04 `grep -c 实体字段表 tools/lab/docchain/checks.py` = 0（检查不存在）；`skills/agentflow/templates/feature/design/be/backend.md` §1.3.2 已改必填节、§1.3.5 已加核对行（工作树在案） | A 新增（推荐）：门判「形」（字段表存在且列头齐备），判不了「对不对」 | 用户拍板 A/B/C 后按结论实施（属 protected 面，人工编写） | P1 | 多模块(`tools/lab/docchain/checks.py`、`tools/lab/docchain/constants.py`、`tools/lab/docchain/selftest.py`、`skills/agentflow/templates/feature/design/be/backend.md`) | N | 未决 | DEC-2026-003 | r1 |  |  |  |
| 4 | `skills/agentflow/templates/hub/repo-rules.md:60`（§4 状态单点门条款，2026-11-04 可用性批；实锤=2026-11-02 登录批次同一事实 5 处措辞、收口漏改 todo 与 index「已完成」并存） | C30「状态单点比对」是否进 doc_chain：A 新增硬红——抽取批次各文档状态词与计数（已落盘/已通过评审/待覆盖/用例数等）与 plan 任务表权威值等值比对，不一致判红（代价：状态短语词典需维护，误报面要先评估）；B 新增软警告——先一个批次只警告不红（代价：软警告期漂移仍可能漏改）；C 不新增——靠 repo-rules 门条款自觉（代价：与本次事故同型的扇出失败继续靠人肉追） | 2026-11-04 `grep -c C28 tools/lab/docchain/checks.py` = 0（同上，C30 亦无）；`templates/hub/repo-rules.md` §4 已加「状态单点」条款、`templates/releases/todo.md` 已删批次索引表、`templates/feature/README.md` 已加缺陷台账与验收记录节（工作树在案） | B 先软后硬（推荐）：先试运行一个批次评估误报面，再转硬红，避免 `check-write-scope.sh` 式误报阻断合法工作 | 用户拍板 A/B/C 后按结论实施（属 protected 面，人工编写） | P2 | 多模块(`tools/lab/docchain/checks.py`、`tools/lab/docchain/constants.py`、`tools/lab/docchain/selftest.py`、`skills/agentflow/templates/hub/repo-rules.md`、`skills/agentflow/templates/feature/README.md`) | N | 未决 | DEC-2026-004 | r1 |  |  |  |

> 分工口径（2026-10-29 全面修正与瘦身批 T03 加入，同见 `AGENTS.md` 决策记录节与
> `skills/agentflow/references/document-chain.md` 的 spec 节）：本文件是**唯一需要用户逐条回复的清单**；
> 批次链内的 `spec/checklist.md` 承载需求侧待决行的运行时台账（哪条阻塞什么、由谁关闭），
> 其中「需用户抉择且尚未关闭」的行必须携带本文件的条目编号——两个「单点」由此不再互相覆盖。

> 已闭合条目的历史注记（2026-10-10 至 2026-10-19 共 8 段 + 表后 27 行）已于 2026-10-29 按「拍板后移出本表」
> 的既有规则移出，不再以注记形式留在本文件。移出前的原文可在
> `agentflows@6229a65:docs/PENDING-DECISIONS.md` 逐行取回；各条的结论与证据载体分别在
> `CHANGELOG.md` 对应节与 `episodes/归档/2026-10/2026-10-18/`、`episodes/归档/2026-10/2026-10-19/` 下的 episode（月度归档后的现行路径）。

> 2026-10-29 拍板并移出（结论与载体）：第 17 条 A（四件已落地）→ Q-03 与 `tools/lab/gate/records.py`、`schemas/review.schema.json`；第 19 条 C「不设总量上限、只消副本」→ `spec/qa/acceptance.md` 的 G5-AC-01 与 `spec/checklist.md` Q-05；第 20 条 A「完整链维持默认」→ Q-10；第 21 条 A+B「本批维持、下一批执行」→ Q-07 与 `docs/releases/todo.md`；第 22 条 C「分立并补实现深度」→ Q-06 与计划 T16；第 25 条 A「维持移出并留出处」→ Q-13 与本文件规则正文。另第 23 条（载体表并入既有 `docs` 项）与第 24 条（实现角色 ≤120 行）按已落地事实关闭：前者见 `spec/checklist.md` Q-11 与本批 T07，后者见 Q-12、`agents/` 三个实现角色实测 34 / 44 / 28 行（2026-11-02 复测；本行原写 22，是 `bug-fixer` 内容增补前的旧值），且第 22 条所选 C 本身以 ≤120 行为前提。

> **当前无未决项。** 2026-10-29 第二轮拍板与实施（结论与载体逐条可定位）：

> - 第 10 条 B「砍掉改进环」→ `docs/design-decisions.md` §3 的设计知识与恢复清单 + 本批计划 T20；
>   删除面见 `skills/`（仅剩 `agentflow`）、`agents/`（10 个角色）与 `schemas/`（episode 契约迁入）。
> - 第 11 条 B「C22 打标只对新批次生效」→ `docs/features/README.md` 的「纪律」节 + `skills/agentflow/references/document-chain.md` 门 8。
> - 第 12 条 C「只给 `credentials` 加 pattern」→ `schemas/test-plan.schema.json`、`schemas/test-run.schema.json`
>   同名字段 + `tests/test_gate_schema.py::test_credentials_field_rejects_obvious_secret_shapes`（T21）。
> - 第 13 条 A「C17 补变异项」→ `tools/lab/mutate.py` 的 `doc_chain.C17` 两条变异 + `tools/lab/docchain/selftest.py` 的 112/113 夹具（T22）。
> - 第 14 条 A「契约补定位即预算」→ `skills/agentflow/references/contracts.md` 的 `read_scope` 节（T23）。
> - 第 15 条 A「写范围执法器登记为已知人工步骤」→ `AGENTS.md` 的「接受任何产物之前」节与 `docs/releases/todo.md` 的零散微项条。
> - 第 16 条 A「补同题对照实验」→ `docs/evaluations/AGENTFLOW-CONTROL-EXPERIMENT-2026-10-29.md`（T24）。
> - 第 18 条 C「维持现状」→ `schemas/review.schema.json:47` 起的 `review_tier` 字段已可承载；episode 与决策记录两处不补。

> - Q-05（最小必读面瘦身，原活跃表第 1 条）于 2026-10-29 晚些改拍 **C**：只消副本、不设总量上限（原 B 的 ≤350 与 C 的 ≤450 均不再作为上限）；四文件实测 622 行，硬边界条款（`contracts.md` 的禁区与简报/结果契约）只做引用化不做删除；T24 由 `feature-2026-10-29-全面修正与瘦身` 的 FIX T12 落地。
