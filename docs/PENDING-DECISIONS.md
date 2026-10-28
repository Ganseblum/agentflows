# 待用户拍板的事项

> 跨计划的「等用户拍板」事项统一登记在本文件（来源、问题、推荐、状态）。会话与计划会有
> 很多份，拍板口只有一个——这里是唯一需要用户逐条回复的清单。
>
> 规则：新事项登记为 `未决`；拍板后写成 `已拍板（日期 · 结论）`，并在各自载体落证据后
> **从本表移出**（本表只保留未决与未完结项）；实现若偏离被拍板的结论，不得回写成已拍板，
> 另行登记新条目再向用户确认。
>
> 2026-10-10：原十项已全部拍板/执行完毕（证据：提交 `4c767eb`、`6d10b14`、EP-20261010-001/002、
> `CHANGELOG`「待发布」节），已从本表移出。2026-10-12 精简批：第 5 条已随 mock/ 整体裁撤关闭
> （证据随本批提交）；业务尺子随本批裁撤，原第 2/3 条失去对象关闭；当前保留 2 条未决。
>
> 2026-10-13 核实：两条未决仍成立——产品链需求评审门（`docs/product/README.md` 第 3 节）仍是
> `☐`，`method-spec.md` 的会话角色词命中仍在；回溯独立评审在 `reviews/` 下无对应记录。
> 第 1 条的复审命令已更新为现行活面门（旧写法 `doc_chain.py docs/product` 需该目录另有 `plan/`
> 才可能通过，而产品链计划落在 `docs/features/<批次>/plan/`，故换用 `validate.py doc_chain_live`）。
>
> 2026-10-18 合并批：`workbuddy/main-b0d8652c` 已并入 `main`（按用户拍板保留 `main` 的裁撤，
> 评测装置不复活，只并入记录类内容；当时 `validate.py all` 全部子项全绿留证——当时的 `all`
> 尚为九项，`lint` 子项于 2026-10-19 加入）。该次合并带出三条新事项，
> 登记为下表第 5–7 条。
>
> 2026-10-19 过期货清理批：第 7 条并入 G14（同属 gate/ 门健全）；新增第 8 条（质量提升批收尾拍板）。
> 2026-10-19 产品链修复轮与分支处置：第 1 条 F1–F12 修复已落并完成独立复审（approved，见文末）；第 6 条已执行并移出（见文末）。门健全批次（第 5、7 条）已拍板落地并移出（见文末）。受保护面回溯评审（第 4 条）已执行并移出（见文末）。

| # | 来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 2026-10-20 评测报告拍板项 P1/G28（`docs/evaluations/AGENTFLOW-EVALUATION-2026-10-20.md` 第十七节） | improve 治理机器怎么处置：A 冻结（不删文件，只在路由与对外描述里写明当前停用，并清掉 `improve/SKILL.md` description 与 `openai.yaml` 里残留的「独立基线对照」话术；代价是四个角色文件与两份 schema 继续留在保护面与文档面里）；B 砍掉（按 2026-10-12 瘦身批先例整体裁撤，设计知识留 `docs/design-decisions.md` §3；代价是恢复时要照重建清单重建，且属受保护面门变更）；C 保留现状（不动；代价是继续 0 候选 0 发布记录的空转，且对外描述与实际能力的差距要靠人反复澄清） | 2026-10-23 `python3.12 -c "from pathlib import Path; roots=[Path('episodes'),Path('docs/releases')]; ps=sorted(p for r in roots if r.exists() for p in r.rglob('*') if p.is_file() and p.suffix in {'.json','.md'} and p.name != 'README.md' and ('candidate' in p.name.lower() or 'release' in p.name.lower())); print('记录文件数:',len(ps)); [print(p) for p in ps]"` | A 冻结：不再投入、路由降权、保留记录面与恢复清单，恢复条件成熟再启用 | 用户在 A/B/C 中书面选定，并记日期与选定后的落点（选 A 或 B 时由当次批改动 `skills/improve/` 与两份 schema 的路由与描述） | P2 | 多模块(skills/improve/ 执行面、agents/evaluator.md 与 agents/release-governor.md 两个受保护角色、skills/improve/references/ 的 candidate 与 release-record 两份 schema) | N | 未决 |
| 11 | 2026-10-23 本批走查发现的存量范围问题（`docs/features/README.md` 在途批次表） | C22 目标承接表要不要覆盖存量批次：A 全量接入（把三个历史批次都补承接表并打标；代价是历史不回改是本仓硬边界，且大量已散失证据需重跑或改状态）；B 只对新批次生效（新批次立项当天打标；代价是存量批次的目标失踪风险继续靠人自查）；C 只对接入中的两个活批次生效（代价：C23 已覆盖 `docs/features/feature-2026-09-19-产品线完善`，选择性接入会让同一仓出现两套口径） | 2026-10-28 复跑（df77ced 改了被引的 docs/features/README.md 后）`python3 tools/lab/doc_chain.py docs/features/feature-2026-09-19-产品线完善` → PASS（退出码 0；该批次 8 行散失证据已按 `N/A: 理由` 回写。历史刷新：2026-10-26 因立项总体评审吸收批修改 `docs/features/README.md` 刷新一次；2026-10-27 因 L3 工作流增强批再次修改该文件，重跑同一命令仍 PASS） | B 只对新批次生效，存量不回改；把「打标」写进立项动作清单 | `docs/features/README.md` 的立项纪律节与 `skills/agentflow/references/document-chain.md` 的门清单各补一行，并注明存量批次的处理口径 | P2 | 多模块(tools/lab/doc_chain.py 的 C22 判据、docs/features/ 三个批次的 README 打标状态、skills/agentflow/references/document-chain.md 的门清单) | N | 未决 |
| 12 | 2026-10-26 整体审核 G19（`docs/evaluations/AGENTFLOW-AUDIT-2026-10-26.md` 第 72 行） | 凭据值形状无机器检查：A 不机器检查（明文凭据本就不该进记录，属流程纪律而非 schema 形状；在 `AGENTS.md` / `docs/system-guide.md` 写明纪律即可）；B 在 gate 加凭据形态扫描（`records.py` 或 `testing.py` 扫正文禁止 `sk-` / `token=` / `Bearer ` 等形态，而非给 `credentials` 加 pattern）— 两条路择一 | 2026-10-28 复跑（被引文件于 51e6754 改动后）`grep -n pattern schemas/test-plan.schema.json schemas/test-run.schema.json` → 13 处 pattern 全部是 id 格式（`^TP-`/`^TR-`/`^ISS-`/数字），`credentials` 字段只有 `type`/`minLength`，无凭据形状 pattern；`tools/lab/gate/` 无凭据值扫描。该字段语义是「凭据如何送达执行者（如 session 注入的环境变量、不落盘）」，并非凭据值本身 | B 在 gate 加凭据形态扫描（扫描正文比给 `credentials` 加 pattern 更稳：前者拦所有字段的明文凭据，后者只拦该字段） | 用户在 A/B 中拍定；选 B 属受保护面门变更（`schemas/`、`tools/lab/gate/` 均在 `protected-paths.txt`），需逐项授权 | P2 | 多模块(schemas/test-plan.schema.json、schemas/test-run.schema.json、tools/lab/gate/testing.py 或 records.py 的扫描逻辑) | N | 未决 |
| 13 | 2026-10-26 整体审核 G20（`docs/evaluations/AGENTFLOW-AUDIT-2026-10-26.md` 第 73 行） | C17 变异覆盖最薄：A 补 1–2 个变异项（给 `doc_chain.C17` 加进 `ITEMS` 与 `MUTATIONS`，配正反夹具，由 `mutate.py` 实跑证明变异被杀死）；B 不纳入变异覆盖（C17 已有 `doc_chain.py --self-test` 与 `validate.py decision_gate` 间接守护，变异覆盖只是纵深，不补亦可）— 两条路择一 | 2026-10-28 复跑（被引文件于 51e6754 改动后）`python3 tools/lab/mutate.py --list` → `doc_chain.C17` 不在 `ITEMS`（无覆盖）；`coverage_gaps()` 当前不把 C17 列为缺口（它只比对 `ITEMS` 与 `EXEMPT`）。`ITEMS` 覆盖 24 个检查项；C17 实现于 `tools/lab/docchain/checks.py:750-789` 的 `staleness_findings` | A 补 1–2 个变异项（把最薄的 C17 纳入变异网，纵深更齐；成本是一次 mutate.py + 夹具改动，属受保护面门变更） | 用户在 A/B 中拍定；若选 A，`mutate.py` + `checks.py` 改动 + 夹具属受保护面门变更（`tools/lab/mutate.py`、`tools/lab/docchain/checks.py` 均在 `protected-paths.txt`），需逐项授权 | P2 | 多模块(tools/lab/mutate.py 的 ITEMS/MUTATIONS、tools/lab/docchain/checks.py 的 C17 实现、examples/decisions/ 或 doc_chain 自测夹具) | N | 未决 |
| 14 | 2026-10-27 评审耗时复盘（`skills/agentflow/references/contracts.md:119` 的 read_scope 只约束下限） | `skills/agentflow/references/contracts.md` 的 `read_scope` 只约束读取下限（必须覆盖改动经过的一切），没有要求简报提供可核实定位，也没有对应的读取上限或定位质量判据：A 在契约里补「定位即预算」条——简报对要求核实的字段/调用必须给 `path:line` 或可复核 Grep 模式，大文件以片段交付，worker 因定位不足须扩读时先索取定位（代价：`contracts.md` 在保护面内，属门变更，需逐项授权）；B 只在角色层约束，契约不动（代价：目标仓的 Supervisor 读不到角色文件，派发时仍可能只给文件名）；C 维持现状（代价：本轮已由 `agents/reviewer.md` 与 `SKILL.md` 第 4 步局部兜住，但契约层仍是单侧约束）— 三条路择一 | 2026-10-28 复跑（被引文件于 51e6754 改动后）`grep -n "read_scope" skills/agentflow/references/contracts.md` → 第 35 行字段定义、第 119 行「读取范围大于写范围」、第 121 行设计引用，三处均为下限约束，无定位质量或读取上限条款；`grep -n "读取" agents/reviewer.md` → 本轮新增的读取纪律属角色层，非契约层 | A 在契约里补「定位即预算」条（契约层才是 Supervisor 的实际依据，角色层的补充不能替代） | 用户在 A/B/C 中书面选定；选 A 属受保护面门变更（`skills/agentflow/references/contracts.md` 在 `protected-paths.txt` 第 80 行），需逐项授权并在同一变更内重建 `packaging/runtime` | P2 | 多模块(skills/agentflow/references/contracts.md 的 read_scope 契约、agents/reviewer.md 的读取纪律、skills/agentflow/SKILL.md 第 4 步的简报要求) | N | 未决 |
| 15 | 2026-10-28 评测报告 B1（`docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md` §二） | 写范围执法器 `check-write-scope.sh` 是否接入自动路径（pre-push 或 CI）：A 先登记为已知人工步骤、不自动接入（误报面未评估，dirty 树的无关变更会阻断合法推送）；B 接入 pre-push 但需先评估误报面并给出豁免机制 | 2026-10-28 `grep -rn check-write-scope .github/ skills/agentflow/scripts/ tools/` → 非注释调用点仅 `tools/lab/gate/common.py:82` 的「保护它自己」条目；宿主不强制 Write 路径（`docs/host-platform-facts.md` C7 行） | A 先登记为已知人工步骤（2026-10-26 审核 P2 同向建议） | 用户在 A/B 中拍定；若选 B 需同时给出误报豁免机制与 pre-push 实测输出 | P2 | 多模块(skills/agentflow/scripts/check-write-scope.sh、skills/agentflow/scripts/pre-push.sh、.github/workflows/) | N | 未决 |
| 16 | 2026-10-28 评测报告 G34（`docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md` §五 第 1 条） | 成本收益缺对照组：「不用 agentflow 需要多少成本」从未实测，存在意义维度只有推理支撑：A 补一次同题对照实验（选一个小型真实任务，with/without 各跑一遍，记录人时、门次数、返工轮次）；B 不做对照，对外叙事明确不押「成本更低」 | 2026-10-28 全仓检索无对照实验载体（`docs/evaluations/` 十份档案均为单向评测）；本报告 §五 已如实列入无证据推测清单 | A 补一次同题对照实验（存在意义是该方法的核心理由，唯一缺的证据就是它） | 实验协议与结果落盘后关闭；选 B 则须在 README 对外叙事处写明不主张成本优势 | P3 | 多模块(docs/evaluations/、README.md 对外叙事) | N | 未决 |
| 17 | 2026-10-28 评审欠账清偿批 T04（`docs/features/feature-2026-10-28-评审欠账清偿/plan/PLAN-DEBT-001.md`） | 是否为 `review_tier` 伪降级判据授权改动受保护面：A 授权（改 `schemas/review.schema.json` 增 `review_tier`/`dispatch_errors` 两字段与一条 `allOf`、改 `tools/lab/gate/records.py` 判伪降级、新增 `tests/` 用例、跑 `packaging/build_runtime.py` 重建生成树；代价是门变更一次、需独立评审）；B 不授权（G2 只能停在「清单可清点」，`review_tier: L0` 而无 `dispatch_errors` 的伪降级继续无人校验） | 2026-10-28 实测 `grep -rn "review_tier" tools/ schemas/ tests/ skills/agentflow/scripts/` → 零命中（无任何校验器读它）；`schemas/review.schema.json` 的 `additionalProperties: false` 且属性表无该字段；改源 schema 不重建生成树时 `validate.py manifests` 实测报 `packaging/runtime/schemas/review.schema.json: content differs from source` | A 授权（判据没有不受保护面的落点；B 等于让已写入契约的三条不变式继续空转） | 用户在 A/B 中拍定并记日期；选 A 时同一变更内须含 schema、校验器、单测与生成树重建四件，且 `EXPECTED_TEST_FILES` 与 `protected-paths.txt` 同步登记 | P2 | 多模块(schemas/review.schema.json、tools/lab/gate/records.py、tests/test_gate_records.py、packaging/runtime/schemas/review.schema.json、tools/lab/validate.py 的 EXPECTED_TEST_FILES、protected-paths.txt) | N | 未决 |
| 18 | 2026-10-28 评审欠账清偿批（`skills/agentflow/references/contracts.md:42-43` 的载体与实际声明位置不一致） | `review_tier` 的权威载体选谁：A 补进契约点名的两处（`skills/improve/references/episode.schema.json` 增字段、决策记录契约加该字段；代价是两份受保护面 schema 一起改，门变更面扩大）；B 改契约措辞指向实际载体（把「决策记录或 episode」改写为「评审记录或批次 README/计划」，代价是改 `contracts.md` 受保护面正文）；C 维持现状（本批的真实欠账在批次 README/计划层，由派生清单覆盖；代价是契约点名处仍无该字段，读契约的人仍会去找不存在的载体） | 2026-10-28 实测：`skills/improve/references/episode.schema.json` 为 `additionalProperties: false` 且无 `review_tier`；决策记录无 schema，`docs/PENDING-DECISIONS.md` 八列无该字段；两批真实 L0 声明均在批次 README/计划正文，不受任何记录契约校验 | C 维持现状（本批已用派生清单覆盖真实载体；A/B 都是受保护面门变更，收益不足以单独开一次） | 用户在 A/B/C 中书面选定；选 A 或 B 均属受保护面门变更，需逐项授权 | P3 | 多模块(skills/improve/references/episode.schema.json、skills/agentflow/references/contracts.md、docs/PENDING-DECISIONS.md 的决策记录契约) | N | 未决 |

> 2026-10-23 按八列契约重建本表并打上 `agentflow 决策记录` 标记，使 C16 与 C17 第一次照到活文件
> （此前该标记只出现在规则载体与 `examples/decisions/` 夹具里，门绿在夹具上）。同批把原第 9 条
> 按「拍板后移出本表」的既有规则移出：第 9 条（批次内 `reviews/` 是否受评审契约校验）已于
> 2026-10-19 由用户选 (b) 落地——`reviews/README.md` 新增「校验范围」条，明写批次内 reviews 仅为
> 文档链材料、不受评审契约约束；选项 (a)（纳入 `validate_review_markdown`）仍是待授权的门变更，
> 如后续要启用，按新条目重新登记。

> 2026-10-22：第 8 条已执行并按规则移出——② M-D/T08 闭合：ZCode 缓存已有 `0.12.0` 快照，`validate.py installed` PASS（2026-10-22 复核）；①③④⑤ 已于 2026-10-19 落地（证据见下方同日记录与 `PLAN-QUALITY-001` T04/T05/T07/T08/T09）。

> 2026-10-12：原第 5 条（examples/mock 计划样板逐字节重复的单源化）已关闭——本批直接删除整个
> `mock/`（用户授权的精简批），examples/ 侧自然成为唯一样例；`MOCK_RECORD_ROOTS` 与 mock 检查
> 一并摘除。
>
> 2026-10-12：业务尺子随精简批裁撤（用户授权「保公开、裁业务」），原第 2 条（完整切片闭环与业务
> 尺子授权）、第 3 条（`host_adapter` 隔离路径认证）失去对象关闭；原计划 `plans/PLAN-BUSINESS-EVAL-001.md`
> 随瘦身批删除（git 历史可回溯）。
>
> 2026-10-19：第 8 条 ① 的四问不是并列选项，而是一条依赖链——**Q-01（是否实现 M-F）→ Q-03（预算与宿主
> 可用性）→ G1（结论可为「无定论」）→ Q-02（角色取向；prd「先测后改」要求等 G1 结论）**。Q-02 已按方案 D
> 落地，但它只覆盖「入口收敛」，不覆盖「是否合并角色文件」，后者仍等 G1。按并列题逐条作答，容易得出与
> 批次规则冲突的结论（例如在 G1 之前合并角色）。
>
> 2026-10-19：第 6 条已执行并按规则移出——`git tag workbuddy-merge-2026-10-18 9e30460`（合并点
> 留底）、本地分支 `workbuddy/main-b0d8652c` 已删、对应 worktree 已移除（该分支无 upstream、
> 从未推送；内容已在 `main` 且经 tag 可回溯）。
>
> 2026-10-19：第 5、7 条已拍板并执行完毕，按规则移出——
> 第 5 条（gate/ 入保护清单）：已拍板（2026-10-19 · 用户「全部处理优化」授权）。`tools/lab/gate/` 全部 13 模块入 `protected-paths.txt`（leniency=checked），`gate/common.py` `REQUIRED_PROTECTED_PATHS` 增 `gate/` 与 `mutate.py` 条目；`validate.py protected` 门自证清单完整，`isolation.py check-diff` 实测拦截 gate 修改。证据：PLAN-QUALITY-001 T07 行。T09 独立评审 2026-10-19 approved（见 `PLAN-QUALITY-001` T09 行）。
> 第 7 条（G1/G14 门健全）：已拍板（2026-10-19 · 同一门健全改动）。G1/G14 已落：`gate/schema.py` 新增 `SUPPORTED_SCHEMA_KEYWORDS` 与 `check_schema_keywords`（未实现关键字、format 值、数组式 items 一律拒载），（注：当时所述 `SchemaSubsetFailClosedTests` 测试类经 2026-10-20 复核从未进入被提交的历史树，函数实现本身属实，负例覆盖由既有测试承担。）G2 查证闭环：`artifact_digest.py` 不经过 git diff（直接扫描文件树），原改进描述的对象机制不存在，不实施。证据：门（当时九项）PASS + 单测 78 项 OK（**2026-10-20 勘误**：原记「95 = 78 + 9 SchemaSubsetFailClosedTests + 8 MutationKillCorpusTests」——两个测试类从未进入被提交的历史树，95 为当时工作树未提交增补的计数，实跑为 78）。T09 独立评审 2026-10-19 approved（见 `PLAN-QUALITY-001` T09 行）。
>
> 2026-10-19：第 4 条已执行并按规则移出——
> 第 4 条（受保护面回溯独立评审）：已执行（2026-10-19 · 用户「全部修复处理」授权）。评审覆盖 4c767eb（本地化）、6d10b14（youc 吸收）、8996016（结构瘦身）三个提交的受保护面 diff（13267 行）。结论：**approved**（status: complete）。8 项发现均为 P2/信息性，无阻塞。评审记录：`docs/features/feature-2026-10-13-质量提升/reviews/review-2026-10-19-002.md`。
>
> 2026-10-19：第 1 条已执行并按规则移出——
> 第 1 条（产品链修复轮复审）：已执行（2026-10-19 · 用户「全部开始处理 执行」授权下的收尾）。首轮独立复审确认 F1–F12 中 10 项修复成立；聚焦复检确认剩余三项：F4（台账 OQ-2 行补 owner 单元格，5 列对齐、关闭条件可判定）、F8（proposal 新增 §1.4 范围决策表，12 行全覆盖且每行带引用出处）、N3（live 证据措辞精确化为端点健康类，与 C12/X1 事实相符）。机器复核：三条 `doc_chain.py --file` 退出 0 + `validate.py doc_chain_live` PASS。总体结论 **approved**，F1–F12 全关闭。复审记录：`reviews/agentflow-product-chain/review-2026-10-19-003.md`（快照 `archive/2026-10-19-003/`）；`docs/product/README.md` 第 3 节需求评审门已勾选。残留 P3 观察（不阻塞）：§六首项「组织图产品化」未在决策表行内逐一枚举，该行已引用 §六。
