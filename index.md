# agentflows 索引

> 全仓唯一文档索引。文档的新增、移动与删除必须同步维护本文件；相对链接带 `.md` 后缀。

## 从这里开始

| 场景 | 入口 |
| --- | --- |
| **第一次用 / 5 分钟上手** | `docs/quickstart.md`（先判断要不要用这套，再决定走哪条路） |
| 日常两轨 | 小修与零星事项走 `docs/issues/`；成批 / 跨层工作立 `docs/features/<批次>/`；拍板与待验收分别看 `docs/PENDING-DECISIONS.md` 与 `docs/releases/pending-test.md` |
| 改角色定义 | `agents/README.md`（<!-- count:agents -->15<!-- /count --> 个角色文件 + 工作链调度入口） |
| 改方法契约与流程文本 | `skills/agentflow/`（`SKILL.md`、`references/`）、`skills/improve/` |
| 抄模板（提案/规格/方案/计划） | `skills/agentflow/templates/README.md` |
| 查批次与实施计划 | `docs/features/`（`feature-<YYYY-MM-DD>-<主题>/`；在途批次 `feature-2026-09-19-产品线完善`（部分任务未开始）、`feature-2026-10-13-质量提升`（部分模块已实施，见批次 README）） |
| 查缺陷与事项 | `docs/issues/README.md`（`ISS-<YYYY>-<NNN>`，含看板与归档规则） |
| 查对外评审落点 | `reviews/README.md` |
| 查发布与待验证清单 | `docs/releases/`：`todo.md`（待办与索引）· `pending-test.md`（待验收）；逐版本发布记录已停用，版本史见 `CHANGELOG.md` |
| 看设计、指南与事实 | `docs/`：`product/`（产品链）、`quickstart.md`（5 分钟上手）、`system-guide.md`（体系指南）、`design-decisions.md`（设计决策）、`host-platform-facts.md`（宿主事实） |
| 看仓库怎么分级、各面怎么装 | [`README.md`](README.md) 的「仓库布局」节与 [`tools/lab/README.md`](tools/lab/README.md)（手写的目录树已删除，避免与真实结构漂移） |
| 记录与改进环 | `docs/issues/`（缺陷与台账）、`docs/features/`（批次与计划）、`episodes/`（决策记录）、`docs/releases/`（在途与待验收）、`reviews/`（对外评审落点）；改进三件套已停用 |
| 校验与评测工具 | `tools/lab/` |
| 查本仓自评（评测报告 / 缺口清单 / 拍板项） | `docs/evaluations/`（六份评测交付件：2026-10-12 两份、2026-10-19 任务书、2026-10-20 三份报告；含已登记拍板结论） |

- 2026-10-20 评测修复批（用户指示「按 8.5 分标准处理」）：按 `docs/evaluations/` 三份评测报告的缺口清单修复——① CI 装依赖（`validate.yml` 增 `pip install -r requirements-dev.txt`，G02）+ 门项数口径统一为十项并以 `validate.py --list` 自报（README/AGENTS/method-spec/pending-test/批次 README 共 9 处，G01）；② `trend.py` 修复（review-2026-10-19-003 补「## 发现摘要」节）并重录 `docs/trend.jsonl`（G07）；③ `isolation.py` 的 `changed_paths` 过滤 `__pycache__`（诚实跑门不再自陷，G06）；④ `mutate.py` 退出码语义修复（存活=1、无效=2）+ 51/51 与 95/96 注水数字全仓勘误（CHANGELOG/index/PLAN-QUALITY-001/EP-20261019-001/PENDING-DECISIONS/pending-test，实跑基线：变异 43/6/2、单测 78，G08/G09）；⑤ `skills/agentflow/scripts/` 与 `references/contracts.md` 入受保护面（候选不得改写写范围执法器，G03，门变更）；⑥ 幽灵断言删除（「中文镜像段落对应」三处声称，G05）；⑦ docs 门内联代码正则不跨行 + CHANGELOG 断链修复（G16）；⑧ `check-write-scope.sh` 计入被忽略文件（与 isolation 同口径，G29）；⑨ `record_store.py` FTS5 畸形表达式结构化报错（G21）；⑩ 归档规则明文化（目录随首个 rejected 记录创建，G13）；⑪ 契约自洽：`BUG-*`→`ISS-*`（两处）、hub 模板路径、review_id 措辞、计划模板补双形态说明、`gate/plan.py` 状态列改按列名读（与 C9 统一，G10）、testing 落点放行 `evidence/`/`scratch/`（G11，门变更）；⑫ `packaging/runtime` 重建 + 宿主缓存同步。终验：`validate.py all` 十项全 PASS（dev 依赖装于 /tmp venv）+ `installed` PASS + 单测 78 OK。存活变异 6 项的语料补齐、G04（schema required 基线比对）等留待后续批次。

## 维护纪律

- 文档的新增、移动与删除必须同步维护本索引。
- 新增顶层目录或新的文档类型须先经用户确认，不得自动创建。
- 相对链接带 `.md` 后缀；文档正文不写会话角色词与裸代号（判据见 `skills/agentflow/references/document-chain.md` 的表达纪律节）。

## 迁移与清理记录

- 2026-10-21 收尾批：根目录两份交付件（`AGENTFLOW-YOUC-ADOPTION-REVIEW-2026-10-21.md`、`AGENTFLOW-DECISION-TRACEABILITY-PROPOSAL-2026-10-21.md`）移入 `docs/evaluations/` 并登记收存清单，仓库根回到只留入口类文档；删除 `中文说明.md`（上批误入的一行占位残留）；`packaging/README.md` 过时计数与「其余八项检查毫无感知」表述改为以 `--list` 自报为准；`templates/README.md` 注册两份决策模板；提案头部状态改「已实施」。

- 2026-10-21：承接 `AGENTFLOW-YOUC-ADOPTION-REVIEW-2026-10-21.md` 落两批改动——**非门面吸收批**（`SKILL.md` 首次接入补三句跑门条款与既有仓基线对齐、`AGENTS.md` 实验与恢复补裸 grep 中文漏报与验收脚本打印命中两条、`document-chain.md` 增「跨仓运行与既有仓基线」段、模板补「落点基准」元信息行并修状态枚举自相矛盾）与**门变更批**（用户显式授权：C9 裸字形方言与落点基准声明、C19 qa 验收在场、C20 埋点贯通、C21 ui 轨原型；自测 63→85 case）。`packaging/runtime` 随两批重建；`validate.py all` 十一项十项 PASS（`lint` 环境红）、unittest 78 OK。详录见 `CHANGELOG.md` 待发布节同日两条。

- 2026-10-21：新增根目录交付件 `AGENTFLOW-DECISION-TRACEABILITY-PROPOSAL-2026-10-21.md`（决策可追溯提案：以 Youc R1–R9 两轮返工为语料，归因到三个设计缺口——台账可替代记录、决策最小形态被定义成「一行问题 + 三选项 + 推荐」、只检查路径存在性不检查变更时间；给出 M1 台账降级为索引 / M2 决策五列 / M3 过期检测 / M4 归属检查 / M5 简报模板五个机制，每项标注授权级别与能否机器拦，并附 R1–R9 正反例语料与「不做什么」边界）。**该文件已随同日收尾批移至 `docs/evaluations/`**。

- 2026-10-21 决策可追溯实施批（用户「改动吸收」授权，P0+P1 落地）：① 新增模板 `skills/agentflow/templates/decision/decision-record.md`（拍板口八列：来源/待决问题/现状核验/推荐/关闭条件/优先级/影响范围/自动决策，含 P0–P3 评级与自动决策政策——仅 P3 可自动且自动也须写全规则与理由）与 `decision-brief.md`（分类头 + 九段简报，≥3 方案、每选项写做/不做两种后果、影响范围必须列具体模块/项目名）；② `tools/lab/doc_chain.py` 新增 C15 ledger-index / C16 decision-record / C17 staleness / C18 ownership 四检查，全部**标记启用**（文件携带 `agentflow 决策记录` / `agentflow 问题台账` / `agentflow 决策归属` 方进入检查，沿用 C11 惯例——未采纳八列形态的存量台账不被强制改写），新增 `--repo` 模式，self-test 扩至 72 例；③ `validate.py` 新增第 11 个子项 `decision_gate`（`gate/checks.py` 新增 `validate_decision_gate`，经 `doc_chain.py --repo` 子进程运行并解析输出）；④ 示例 `examples/decisions/good-r6-channel-knowledge.md`（R6 真实八列记录 + 九段简报 + P3 自动决策演示，带标记入检查范围）与 `examples/decisions/ledger-example.md`（C15 索引式台账正反例）；⑤ `AGENTS.md` 新增「决策记录与台账」节（四条纪律）；⑥ `packaging/runtime` 重建。门变更授权范围：`doc_chain.py`、`gate/checks.py`、`validate.py`、self-test 扩容；未动 `schemas/`（M4b 的 `target_feature`/`disposition` schema 版仍留待单独一批）。终验：`doc_chain.py --self-test` 72/72，`validate.py all` 9 PASS / 1 FAIL（`lint` 为本机未装 ruff/mypy 的环境红，无新增红项）。

- 2026-10-21：新增根目录交付件 `AGENTFLOW-YOUC-ADOPTION-REVIEW-2026-10-21.md`（对 Youc 空间近三天会话的 agentflow 采用情况与摩擦点复盘：版本核查三层事实、把 `doc_chain.py --root <Youc>` 原样搬到 Youc 27 个批次实跑得 27 FAIL/0 PASS 的分布与真缺口/口径噪声拆分、A 类可避免 7 条 / B 类不可避免 9 条 / C 类最新源码正在治但接不上 5 条、四步迭代方案）。只读复盘产物，未触碰受保护门；`validate.py all` 写入前后同为 9 PASS / 1 FAIL（`lint` 为本机未装 ruff/mypy 的环境红）。

- 2026-10-20 角色层收口批（承接「agent 能力补充」评估）：不做能力扩张（角色面本为高分项，D5 扣分已在前一批修复），只清三处声明与事实欠账——① `skills/improve/SKILL.md` 与 `skills/improve/agents/openai.yaml` 的「独立基线对照 / 与 baseline 对照」残留文案改为与装置裁撤后口径一致（仪器化对照仅在恢复后启用，现口径为人工评审晋级）；② `protected-paths.txt` 头部注释里已删除的 eval-case schema 提法勘误；③ 新增 `agents/README.md`（交付面唯一此前无入口的目录的索引：工作链表 + 14 角色清单 + 调度要点），`gate/docs.py` 的 agents 遍历相应放行 README（不含角色 frontmatter）；`packaging/runtime` 重建并同步宿主缓存。终验：`validate.py all` 十项全 PASS + `installed` PASS。

- 2026-10-20 评测修复批（用户指示「按 8.5 分标准处理」）：按 `docs/evaluations/` 三份评测报告的缺口清单修复——① CI 装依赖（`validate.yml` 增 `pip install -r requirements-dev.txt`，G02）+ 门项数口径统一为十项并以 `validate.py --list` 自报（README/AGENTS/method-spec/pending-test/批次 README 共 9 处，G01）；② `trend.py` 修复（review-2026-10-19-003 补「## 发现摘要」节）并重录 `docs/trend.jsonl`（G07）；③ `isolation.py` 的 `changed_paths` 过滤 `__pycache__`（诚实跑门不再自陷，G06）；④ `mutate.py` 退出码语义修复（存活=1、无效=2）+ 51/51 与 95/96 注水数字全仓勘误（CHANGELOG/index/PLAN-QUALITY-001/EP-20261019-001/PENDING-DECISIONS/pending-test，实跑基线：变异 43/6/2、单测 78，G08/G09）；⑤ `skills/agentflow/scripts/` 与 `references/contracts.md` 入受保护面（候选不得改写写范围执法器，G03，门变更）；⑥ 幽灵断言删除（「中文镜像段落对应」三处声称，G05）；⑦ docs 门内联代码正则不跨行 + CHANGELOG 断链修复（G16）；⑧ `check-write-scope.sh` 计入被忽略文件（与 isolation 同口径，G29）；⑨ `record_store.py` FTS5 畸形表达式结构化报错（G21）；⑩ 归档规则明文化（目录随首个 rejected 记录创建，G13）；⑪ 契约自洽：`BUG-*`→`ISS-*`（两处）、hub 模板路径、review_id 措辞、计划模板补双形态说明、`gate/plan.py` 状态列改按列名读（与 C9 统一，G10）、testing 落点放行 `evidence/`/`scratch/`（G11，门变更）；⑫ `packaging/runtime` 重建 + 宿主缓存同步。终验：`validate.py all` 十项全 PASS（dev 依赖装于 /tmp venv）+ `installed` PASS + 单测 78 OK。存活变异 6 项的语料补齐、G04（schema required 基线比对）等留待后续批次。

- 2026-10-20 评测归档批（用户拍板「整体新增一个评测目录」）：新建 `docs/evaluations/`（新文档类型经用户确认），六份评测交付件从仓库根迁入（2026-10-12 评测与行动件、2026-10-19 评测任务书为 `git mv`；2026-10-20 三份报告此前未跟踪，一并归档），新增目录 `README.md`（收存清单 + 拍板结论登记）。随迁移修复：两份 2026-10-12 文件内指向根的相对链接改为 `../`、对已删 `schemas/` 评测装置 schema 的路径式引用改写为不带 `schemas/` 前缀的引文、`AGENTFLOW-EVAL-REPORT-2026-10-20-redo.md` 附录 C 的退役路径 `records/` 散文改写（迁移后该文件首次进入 docs 门扫描，暴露 1 处违例）。**同批登记拍板结论**：评测拍板项 P6/G12「方法疗效先不测量」已拍板（见 `docs/evaluations/README.md`）。评测结论的回写（「all 实为十项」「单测 78」「变异 43/51」等）仍待另立批次。
- 2026-10-20：新增根目录交付件 `AGENTFLOW-EVALUATION-2026-10-20.md`（按 `AGENTFLOW-EVAL-PROMPT-2026-10-19.md` 做的 13 维 · 8 角色 · 证据优先评测报告：十三维分数与综合分 6.43/10、32 条缺口清单、11 条拍板项、证据链元评审；先例同 `AGENTFLOW-EVALUATION-2026-10-12.md` / `AGENTFLOW-OPTIMIZATION-2026-10-12.md`。报告为**只读评测产物**，未触碰受保护门；其结论中「`validate.py all` 实为十项（含 `lint`）」「单测 78（记录写 95/96）」「变异 43/51（记录写 51/51）」等项**尚未回写到本仓文档面**，需另立批次处理）。评测过程全程未修改仓库既有文件。**该文件已随评测归档批移至 `docs/evaluations/`**，同批另有两份同日报告（`AGENTFLOW-EVAL-REPORT-2026-10-20.md` / `-redo.md`）一并归档。
- 2026-10-19：新增根目录交付件 `AGENTFLOW-EVAL-PROMPT-2026-10-19.md`（多维度 · 多角色 · 证据优先的项目评测 prompt，先例同 `AGENTFLOW-EVALUATION-2026-10-12.md` / `AGENTFLOW-OPTIMIZATION-2026-10-12.md`；未触碰受保护门）。
- 2026-10-19 门健全批（用户指示「全部处理优化」）：`tools/lab/gate/` 全部 13 模块与 `mutate.py` 入受保护面（`protected-paths.txt` + `gate/common.py` 必需条目，门变更经授权）；`gate/schema.py` 新增 schema 关键字 fail-closed 守卫（G1/G14）；`gate/manifests.py` 运行态新鲜度检查纳入 manifests 门；整门变异复跑当时报 51/51 全杀（2026-10-20 评测复核：该轮报告存 /tmp 已散失，同日树复跑为 43 杀死 / 6 存活 / 2 无效——存活为语料缺口、非门失效实证，退出码语义随后修复为存活≠0）；`doc_chain.py` C6 收紧（异常矩阵须有数据行）+ 自测 case 12b；`agents/release-governor.md` 晋级条款与 schema 对齐（H1）；`skills/agentflow/templates/testing/{plan,run}.md` 补齐模板缺口；`packaging/runtime` 随源面重建。`PLAN-QUALITY-001` 计划 T05/T07 回写完成、T08 阻塞在外部条件（待用户重装插件）。
- 2026-10-19 过期货清理批（机器门之外的内容性过期校正）：`feature-2026-10-13-质量提升` 批次状态回写（T02/T03 置完成、T05 明确「工具落盘未跑整门变异」，证据为当日复跑）；`docs/features/README.md` 在途批次表与 `CHANGELOG.md` 待发布节补该批条目；`docs/releases/` 两个工作文件中已失对象的验收步骤与指针就地标注（评测装置裁撤所致）；`expression-discipline-jargon` 台账按追加式补维护行；`packaging/runtime` 快照重建成 0.11.0（`document-chain-templates.md` 复活件消除）。无门层改动。
- 2026-10-18 合并批：`workbuddy/main-b0d8652c`（2026-10-12 历史线）并入 `main`；按用户拍板保留 `main` 的裁撤（评测装置不复活），只并入记录类内容——本批两份评审/优化报告留存仓库根（`AGENTFLOW-EVALUATION-2026-10-12.md`、`AGENTFLOW-OPTIMIZATION-2026-10-12.md`，其中提及的评测装置均指裁撤前状态）；缺口收尾 episode 重编为 `episodes/2026-10-12/EP-20261012-008.json` 与 `EP-20261012-009.json`（避开 `main` 已占用的 001–007）；收尾计划归位 `docs/features/feature-2026-09-19-产品线完善/plan/PLAN-OPT-CLOSEOUT-001.md`。
- 2026-10-13 文档面校正批：删除手写目录树 `docs/project-structure.md`（计数多处失实，且与 `index.md`、
  `README.md` 重复），引用改指 `README.md`「仓库布局」节与 `tools/lab/README.md`；同步修正 README、
  AGENTS、host-platform-facts、design-decisions、system-guide、product 链与待拍板清单的失实内容。
- 2026-10-12 评测装置裁撤批：`evals/`、runner/adapter/policy、三个 schema 与相关契约整线删除，
  设计知识与恢复清单留存 `docs/design-decisions.md` §3（ISS-2026-052）。
- 2026-10-12 归档批：三份设计文档合并为 `docs/design-decisions.md`（守卫清单收窄）；`evals/` 标注为仪器存量；待拍板第 4 条范围并入本日五批（ISS-2026-051）。
- 2026-10-12 结构改造批四期：`plan` 归入 `docs/features/<批次>/plan/`（顶层 `plans/` 撤销，跨批次拍板口提至 `docs/PENDING-DECISIONS.md`）；改进环死代码随停用机制清除（ISS-2026-049）。
- 2026-10-12 结构改造批三期：`issues/`、`plans/`、`releases/`（工作文件）迁入 `docs/`；逐版本
  发布记录与改进三件套停用；`docs/features/` 按 youc 形态重建（用户拍板，ISS-2026-048）。
- 2026-10-12 瘦身批：归档桶 `_archive/`、两个已完成 `features/` 批次与 mock/ 业务样板整体裁撤
  （用户授权，ISS-2026-047）；历史按 git 回溯，索引只描述现行结构。
- 2026-10 结构改造迁移执行批次（已完成）：记录树撤换为活区、审计/交接件入档、全仓引用改指与检索索引重建。
- 2026-10-09 彻底清理与防漂移批次：断链与退役路径收敛，`validate.py docs` 增断链/退役路径机器门。
