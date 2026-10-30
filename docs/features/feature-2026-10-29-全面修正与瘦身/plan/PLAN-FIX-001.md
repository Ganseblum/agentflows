---
plan_id: PLAN-FIX-001
plan_version: 1.0.0
status: proposed
objective: 把散在三批的收敛议程收成一个任务表；让「未决项归口」「记录引用可复核」「评审档位」三件事从散文变成会判红的判据；必读面回到预算内；证据件与重复导航退场且不留悬空
recorded_at: 2026-10-29T00:30:00+08:00
updated_at: 2026-10-29T00:52:00+08:00
---

# PLAN-FIX-001 — 全面修正与瘦身执行计划

## 进展概览

- 总任务 24 项：T01–T24 `☑ 已完成`（逐行证据列回写命令与落点；T14 经第三轮 delta 复审独立委派 L2 `approved` 闭环），T18 `— 本期不做`（理由在该行）。
- 阻塞：无。T14 已由独立委派（`reviews/review-2026-10-29-006.md`，L2 `approved`）闭环，两个入口门关闭；其余任务无阻塞。
- 评审状态（如实）：两轮共四份独立评审记录均为 `changes_requested`（档位 L2）；其 P0/P1/P2 已在 T19 与本轮处置并实读核验。修复后的第三轮 delta 复审改由独立委派执行（非宿主额度受限的自动派发），返回 L2 `approved`（记录 `reviews/review-2026-10-29-006.md`），两个入口门已关闭，本批结论由 `partial` 升为完整。
- 权威状态：本表即唯一任务状态源；三批旧计划的状态不再各自表述（见 T02）。
- 必读面目标值已于 2026-10-29 由用户拍板为 C：**不设总量上限、只消副本**；`spec/qa/acceptance.md` 的
  G5-AC-01 同步改判，观测值 631 行 / 40,607 字符只作记录。T12 因此只剩「拆判据细则、消副本」一项实质工作。

## 分支策略

| 仓库 | 用途 | 基线 | 基线提交 | 开发分支 | 确认状态 | 确认依据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentflows | 门判据、表达面与记录面的实施与验证 | main | `6229a65` | `feature-2026-10-29-全面修正与瘦身` | 已确认 | 用户 2026-10-29「全面修正+升级瘦身」选项集选定「单批吸收三批未完成任务 / 证据件+重复导航删除 / 门四条全接 / 改到全绿+独立评审，不提交不推送」 | 开工前实测 `git status --porcelain` 为 0 行、`git worktree list` 仅一个条目；分支已切换，不 push、不合并、不重装 |

**落点校对表**（关键改动对照真实代码树，均为 2026-10-29 实测行号；行号随实施漂移时以函数名为准。
下表同时承接设计文件 §13 的五项核实结论：V-01 门走查链与 episode 校验现状、V-02 C18 标记常量与
两条分派路径、V-03 字形映射两份拷贝位置、V-04 `validate.py docs` 断言集合、V-05 自测夹具写法与
用例计数口径）：

| 事实 | 锚点 |
| --- | --- |
| 门项清单共 11 项，无 `records` 项 | `tools/lab/validate.py:321-333`（`ALL_CHECKS`，11 项）与 choices 节（实施后行号会再漂移，定位以常量名为准） |
| 五个记录根的唯一走查 | `tools/lab/gate/common.py:117`（`LIVE_RECORD_ROOTS`）→ `tools/lab/gate/workspace.py:41`（`validate_workspace_artifacts`，331 行 / CC 119，2026-10-26 审核 G31） |
| episode 校验只到 schema 与 id 一致性 | `tools/lab/gate/records.py:137`（`validate_episode_document`）、`:144-148`；`workspace.py:176`（分派）与 `:190-196`（去重） |
| Markdown 侧已有的引用校验 | `tools/lab/gate/records.py:91`（`validate_body_references`）、其 containment 段与引文豁免 `prose_without_quotations`、个人绝对路径判红条 |
| 评审记录校验与早退点 | `tools/lab/gate/records.py`（`validate_review_markdown`）（`validate_review_markdown`）、`:227`（`if errors: return errors`）、`:260-264`（`reviewed_docs` 同目录存在性） |
| review schema 现状 | `schemas/review.schema.json:7`（`additionalProperties: false`）、`:8`（required 8 项）、`:9-49`（properties，无 `review_tier`/`dispatch_errors`） |
| schema 子集校验器已支持 allOf | `tools/lab/gate/schema.py:170-171`、`:174-178`、`:322-328`（`SUPPORTED_SCHEMA_KEYWORDS`）、`:222-260`（shape 约束） |
| frontmatter 解析器只支持扁平形态 | `tools/lab/gate/common.py:202-264`，嵌套映射在 `:237` 报错 |
| C18 与批次级判据的注册点 | `tools/lab/docchain/checks.py:719-721`（三个标记常量）、`:1283`（`batch_traceability_findings`）、`:1302`（`repo_policy_findings`）；`--file` 分派在 `tools/lab/docchain/cli.py:52` |
| 自测夹具写法与用例计数 | `tools/lab/docchain/selftest.py:89`（`run_case`）、`:729`/`:735`（正反例范例）、`:964-979`（前缀式编号）、`:595`（手工 append）；地板 `gate/common.py:140`；逐案行数核验 `gate/checks.py:188` |
| 字形映射两份拷贝 | `tools/lab/gate/plan.py` 原基线 47 行（现为导入）+`:50`（消费于 `:137-143`）；`tools/lab/docchain/constants.py:173`（`TASK_STATUS_GLYPHS`，唯一份）+`:176`（同步义务注释 `:172-175`，消费于 `checks.py:280/282`）；零散字面量 `checks.py:396`、`:415`、`:997-999` |
| 新测试文件的登记点 | `tools/lab/gate/common.py:97-105`（`EXPECTED_TEST_FILES`，`validate.py:46` 再导出），消费于 `gate/checks.py:40-45`、`:65-67`、`:111-121`；`tests/test_gate_integrity.py:83/254/284/534` 钉住 |
| 生成树范围与新鲜度 | `packaging/build_runtime.py:24-32`（`RUNTIME_DIRECTORIES`）、`:37-40`（`RUNTIME_SUBTREES`）；`gate/manifests.py:220-222`（逐字节比对）、`:54-62`、`:67-75` |

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 本批文档链五段成文并通过链 linter | P0 | `docs/features/feature-2026-10-29-全面修正与瘦身/` | — | ☑ 已完成 | `.venv/bin/python tools/lab/doc_chain.py "docs/features/feature-2026-10-29-全面修正与瘦身"` → `PASS doc-chain`（2026-10-29 00:52 实测，退出码 0）；链五段见 `docs/features/feature-2026-10-29-全面修正与瘦身/README.md`；`validate.py artifacts` 同点 PASS |
| T02 | 议程归并：三批未完成任务映射进本表并逐处回写指针；`docs/features/README.md` 在途表、`index.md` 批次索引节、`docs/releases/todo.md` 批次索引、三批 README 四处口径收口 | P0 | `docs/features/feature-2026-10-25-总体评审吸收与修复/README.md`、`docs/features/feature-2026-10-28-表达面与角色治理/README.md`、`docs/features/feature-2026-10-28-评审欠账清偿/README.md`、`docs/features/README.md`、`index.md`、`docs/releases/todo.md` | T01 | ☑ 已完成 | 四处导航面逐处回写：`docs/features/README.md`（在途表 3 行状态 + 新增本批行）、`index.md`（批次索引节）、`docs/releases/todo.md`（批次索引第 12 行 + 三行状态回写）、三批 README 的承接关系节（`docs/features/feature-2026-10-25-总体评审吸收与修复/README.md` 等）；`superseded` 落在 `docs/features/feature-2026-10-28-表达面与角色治理/plan/PLAN-GOV-001.md`；复跑 `validate.py docs` 与 `doc_chain_live` 均 PASS，见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt` |
| T03 | 拍板口归口：8 条散落未决项按八列契约登记或写关闭结论；`AGENTS.md` 决策记录节与 `skills/agentflow/references/document-chain.md` 的 spec 节各补一行「链内台账 / 拍板口」分工 | P0 | `docs/PENDING-DECISIONS.md`、`AGENTS.md`、`skills/agentflow/references/document-chain.md` | T02 | ☑ 已完成 | `docs/PENDING-DECISIONS.md` 现 16 条数据行（新增第 19…25 条，含把 10-25 批 §六 与治理批 3 条确认项归口）；分工条款落在 `AGENTS.md` 的「两个「单点」的分工」条与 `skills/agentflow/references/document-chain.md` 的 spec 节；判别力反证（临时追加缺列行 → 当场判红，还原后转绿）见 `docs/issues/ISS-2026-10-29-拍板口改写中两处自述超出事实.md` 的回归检查节 |
| T04 | 门①：episode 字段级路径存在性判据（含 `N/A: 理由` 与 `仓库@修订:路径` 两种豁免），接在 `validate_episode_document` 之后；夹具 `EV-01…05`；反证在 `/tmp` 副本跑 | P0 | `tools/lab/gate/records.py`、`tools/lab/gate/workspace.py`、`tools/lab/docchain/selftest.py` 或 `tests/test_gate_records.py`（按 T05 的归属选择） | T03 | ☑ 已完成 | `tools/lab/gate/records.py`（`EPISODE_EVIDENCE_FIELDS` / `validate_episode_references` / 裸 `N/A` 不豁免）；接线反证见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/redteam/weakening-2026-10-29.md` B 行（删调用点后接线用例转红）；实跑输出见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt`（`PASS artifacts`） |
| T05 | 门①的回归用例落点：优先并入既有被钉住的 `tests/test_gate_records.py`，避免同时改 `EXPECTED_TEST_FILES`（`gate/common.py:97-105`）与 `protected-paths.txt` 两处清单；确需新建文件时同批登记两处并跑 `validate.py protected` | P0 | `tests/test_gate_records.py`、`tools/lab/gate/common.py`、`protected-paths.txt` | T04 | ☑ 已完成 | 新用例并入既有被钉住的 `tests/test_gate_records.py`（新增 `ReviewTierEnforcementTests` 与 `EpisodeEvidencePointerTests`），未新建测试文件，故 `EXPECTED_TEST_FILES` 与 `protected-paths.txt` 无需增补；实跑 `-m unittest discover -s tests` → Ran 194 tests OK（当时；本轮复跑已增至 201，现行数以实跑为准），见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt` |
| T06 | 门③：C18 归属家族扩射程——打标批次内「阻塞 + 未确认 + 属主为用户」的待决行必须带拍板口编号；夹具 `C18-01…03`；确认 `feature-2026-10-22`（0 行）不被误伤、`feature-2026-10-25` 在 T03 后转绿 | P0 | `tools/lab/docchain/checks.py`、`tools/lab/docchain/selftest.py`、`tools/lab/docchain/constants.py` | T03 | ☑ 已完成 | `tools/lab/docchain/checks.py`（`pending_ledger_findings` 按台账表头形状识别 + `decision_marker_presence_findings` 按声明行识别）与 `tools/lab/docchain/selftest.py` 的 `C18-01…C18-08`；`doc_chain.py --self-test` → 132/132；判据削弱反证见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/redteam/weakening-2026-10-29.md` A 与 D 行；上线当轮即抓出 5 条真实缺编号行（10-25 批 §六 Q-01/02/04/05 与本批 Q-06），已逐条补编号或按实测事实闭合 |
| T07 | 载体归属表与核验断言：新建 `skills/agentflow/references/carrier-map.md`（列：规则 / 权威载体 / 锚点或指针 / 副本处置），断言并入既有 `validate.py docs` 项而不新增门项；夹具 `GC-01…03` | P0 | `skills/agentflow/references/carrier-map.md`（待核实：新文件，实施时创建）、`tools/lab/gate/docs.py` | T03 | ☑ 已完成 | `skills/agentflow/references/carrier-map.md`（23 行归属）+ `tools/lab/gate/docs.py` 的 `validate_carrier_map`，并入既有 `validate.py docs` 项未新增门项；`PASS docs` 见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt`；首轮该表有 6 行锚点是猜的、1 行指向未创建的文件，由该断言当场判红后逐条改为真实标题 |
| T08 | 门④：`TASK_STATUS` 字形→词映射收为单一定义 + 另一处导入；四处零散字面量收口；`validate.py tests` 与 `all` 绿 | P1 | `tools/lab/gate/plan.py`、`tools/lab/docchain/constants.py`、`tools/lab/docchain/checks.py` | — | ☑ 已完成 | `tools/lab/docchain/constants.py` 的 `TASK_STATUS_GLYPHS` 为唯一定义，`tools/lab/gate/plan.py` 导入它，`tools/lab/docchain/checks.py` 的 C26 `valid_statuses` 与 `TASK_STATUS_ACCEPTED` 改为派生；实跑 `PASS tests` 与 `--self-test 132/132` 见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt` |
| T09 | 门②：`schemas/review.schema.json` 增 `review_tier`（枚举）与 `dispatch_errors`（字符串数组，受解析器扁平形态约束）+ 一条 `allOf`；`gate/records.py`（`validate_review_markdown`） 后接伪降级判定；`RT-01…05` 用例；跑 `packaging/build_runtime.py` 重建生成树 | P0 | `schemas/review.schema.json`、`tools/lab/gate/records.py`、`tests/test_gate_records.py`、`packaging/runtime/schemas/review.schema.json` | T05 | ☑ 已完成 | `schemas/review.schema.json` 两字段 + 一条 `allOf`；`tools/lab/gate/records.py` 的 `review_tier_findings` 接在 `validate_review_markdown`；`packaging/build_runtime.py` 已重跑，`PASS manifests` 见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt`；双层护栏各自独立的反证见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/redteam/weakening-2026-10-29.md` C/E/F 三行 |
| T10 | 存量失效引用逐条改写：episode 的 `evidence_ref`（12 文件 37 处）与现行导航面里的退役路径，按「现行事实 / 历史现场 / 已删对象」三类分别改写；改写前后各跑一次扫描脚本 | P0 | `episodes/`、`docs/releases/`、`index.md`、`docs/host-platform-facts.md` | T04 | ☑ 已完成 | 改写前后计数：字段级失效 14 处 → 0（14 处清单与逐条改写形态见本行下方记录与 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt` 的 `PASS artifacts`）；仍消失的对象写 `N/A: 理由 + 出处`，仅迁移的写现行真实路径（如 `plans/PLAN-PRODUCT-001.md` → `docs/features/feature-2026-09-19-产品线完善/plan/PLAN-PRODUCT-001.md`） |
| T11 | 噪声删除（引用先改、门先绿）：L3 批 `testing/**/evidence/` 原始证据件、`index.md`「L3 合并后修正」整节、`docs/PENDING-DECISIONS.md` 尾部已移出条目历史注记、`reviews/` 内部重复快照（外部逐字快照保留）；删除前 `dirty-guard snapshot --tar`，删除后 `verify` 与 `cleanup` | P0 | `docs/features/feature-2026-10-26-L3工作流增强/testing/`、`index.md`、`docs/PENDING-DECISIONS.md`、`reviews/` | T10 | ☑ 已完成 | L3 批 184 件原始证据删除（引用先改 36 处为 `agentflows@6229a65:` 形态，门先绿再删，删后 `PASS artifacts` / `PASS docs` / `doc_chain_live` 均绿，见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29.txt`）；删除前 `dirty-guard snapshot --tar`、删除后 verify 的逐条分辨见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/deletion-counts/dirtyguard-verify-2026-10-29.txt`（报红项全部落在本轮有意重写的行上，已 `--accept` 记录并 cleanup）；`index.md`「L3 合并后修正」整节移出；`docs/PENDING-DECISIONS.md` 表头 8 段与表尾 27 行历史注记移出并留出处。`reviews/` 内部快照去重经实测被 `reviewed_docs` 同目录存在性判据挡住，这些快照是承载件而非重复噪声，已按 T18 本期不做并写明理由 |
| T12 | 必读面收敛：四文件只消副本（2026-10-29 拍板 C，不设总量上限）；`SKILL.md` 去版本史散文与重复声明、宿主易变细节压成一句结论；`document-chain.md` 拆出判据细则文件并同步 4 处引用；同步义务条款退场（以 T07 的归属表为据） | P1 | `skills/agentflow/SKILL.md`、`skills/agentflow/references/document-chain.md`、`skills/agentflow/references/document-chain-checks.md`、`skills/agentflow/references/roles.md`、`agents/reviewer.md`、`skills/agentflow/references/contracts.md` | T07 | ☑ 已完成 | `agents/reviewer.md` 的两份深度清单移出（201 行/7,774 字符 → 144 行/5,336 字符），落点 `skills/agentflow/references/review-checklists.md`；`skills/agentflow/SKILL.md` 的审核节与文档交付链节改为指向各自权威；「改一处就改另一处」同步义务从五个规则载体退场并由 `validate.py docs` 断言钉住。判据细则已拆到 `skills/agentflow/references/document-chain-checks.md`（157 行；主契约 317 行），4 处引用同批更新（`SKILL.md`、`carrier-map.md` 两行、`review-checklists.md`）；`validate.py docs` PASS。实施后实测四文件 621 行 / 86,280 字符（SKILL 151、roles 124、contracts 197、reviewer 149）；行数只作观测值，不作判据 |
| T13 | 计数一致性：`docs/releases/pending-test.md`、`docs/releases/todo.md`、`docs/host-platform-facts.md` 中会过期的计数字面量改为实跑口径引用；`docs/issues/**` 与批次 `reviews/**` 的历史计数按引文保留（判定表见 `spec/be/backend.md` M-F-04） | P1 | `docs/releases/pending-test.md`、`docs/releases/todo.md`、`docs/host-platform-facts.md` | — | ☑ 已完成 | `docs/releases/pending-test.md` 三处、`docs/releases/todo.md` 一处、`docs/host-platform-facts.md` 两处、`README.md` 一处（门项数）改为「当日时点值 + 以实跑为准」口径；历史引文（`docs/issues/**`、批次 `reviews/**`、`CHANGELOG.md`）按 M-F-04 判定表保留不改写 |
| T14 | 全量复核与评审门：先两组委派探测定档（原始返回落 `testing/`），再派独立评审；评审记录含 `review_tier` 与派发依据；`validate.py all`、`doc_chain.py <本批>`、`--self-test`、`unittest` 四项原始输出留档 | P0 | `docs/features/feature-2026-10-29-全面修正与瘦身/reviews/`、`docs/features/feature-2026-10-29-全面修正与瘦身/testing/` | T06、T08、T09、T11、T12、T13 | ☑ 已完成 | 第一轮两路评审 `reviews/review-2026-10-29-001.md`/`-002.md` 与第二轮 `review-2026-10-29-003.md`/`-004.md` 均 `changes_requested`（档位 L2，原始返回见 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/dispatch-probe/`）；第二轮 11 条 findings 的修复已逐条复核并留 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/review-r2/l0-selfaudit-2026-10-29.txt`，全量门实跑 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29-r5.txt`（11 项 PASS，EXIT=0）。第三轮 delta 复审改由独立委派执行（非宿主额度受限的自动派发）：`reviews/review-2026-10-29-006.md` 为 L2 `approved`，6/11 findings 实读核验、全量门由委派独立复跑为 11/11（证据 `testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29-r6.txt`，EXIT=0、`--self-test` 136/136、unittest 205 OK）；两个入口门（需求评审、技术方案评审）据此关闭，本批结论由 `partial` 升为完整。委派运行无 `dispatch_errors`（属直接委派，非额度失败派发） |
| T15 | 实现角色深度对齐（随 10-28 治理批并入项）：`backend-engineer` / `frontend-engineer` / `technical-director` 逐条核对职责覆盖，补缺或写明由谁承担，守 ≤120 行上限 | P1 | `agents/backend-engineer.md`、`agents/frontend-engineer.md`、`agents/technical-director.md` | T07 | ☑ 已完成 | 三角色逐条核对后补齐「由谁承担」边界：backend 补基础设施/部署拓扑/凭据管理上报项；frontend 补视觉基线由 `design/ui` 与用户确定；technical-director 补计划回写/记录落盘/发布授权不归本角色。行数实测 34 / 44 / 22，均 ≤120（`agents/backend-engineer.md`、`agents/frontend-engineer.md`、`agents/technical-director.md`）。`validate.py docs` PASS |
| T16 | 前端/后端角色合并的实测裁决（随 10-28 治理批并入项）：复跑 28 例边界语料，按「不一致例数 / 所有权分歧项数 / 合并稿行数」三条件出数字并更新裁决段；裁决权在用户 | P2 | `docs/features/feature-2026-10-13-质量提升/testing/agentflows-role-boundary/`、`skills/agentflow/references/roles.md` | T15 | ☑ 已完成 | 复跑记录 `docs/features/feature-2026-10-13-质量提升/testing/agentflows-role-boundary/evidence/adjudication-2026-10-29.md`：可比 6 例中 4 例结论不同（4/6；28 例全量不可复现——8 例角色已裁撤、14 例角色专属）；所有权分歧 2 项（一票否决）；合并稿 44+35=79 行 >60。结论保持分立并写入 `roles.md` 裁决段，附三条重审触发条件 |
| T17 | 口径收口两件（随 2026-10-25 批 T13/T14 并入）：`roles.md` 测试链默认序列补评审角色、评审范围口径统一为「由 diff 形状决定」；`AGENTS.md` 的工具白名单措辞改为「仅 `tools` 已验证强制」，对齐 `docs/host-platform-facts.md` 的实测边界 | P1 | `skills/agentflow/references/roles.md`、`AGENTS.md`、`docs/host-platform-facts.md` | T12 | ☑ 已完成 | 核验两处口径已在位：`roles.md` 工作链「测试」行含 `Reviewer（流程合理性模式）`；`document-chain.md` 与 `agents/reviewer.md` 均写明「评审覆盖由 diff 形状决定，不由简报问没问决定」。实际改动只有 `AGENTS.md` 的 frontmatter 边界：改为「仅 `tools` 在 ZCode 实测强制；`disallowedTools` 在 Qoder 未验证，`maxTurns` 只声明」，并指向 `docs/host-platform-facts.md` 的 Z4/Q4/C7 行 |
| T18 | `reviews/` 内部重复快照去重——本期不做：实测 `schemas/review.schema.json` 要求每条评审记录的 `reviewed_docs` 每项在该记录同目录真实存在，archive 目录是判据的承载件而非重复噪声；要删它必须先改这条判据本身 | P2 | — | — | — 本期不做 | 判据依据：`schemas/review.schema.json` 的 `reviewed_docs` 声明与 `tools/lab/gate/records.py` 的存在性校验（`reviewed_docs` 项在同目录 `is_file()` 判定处）；反证方式：删任一 archive 目录即 `FAIL artifacts`，故不属可删噪声 |
| T19 | 评审吸收轮：两路独立评审 12 条 P0/P1/P2 逐条处置（判据可达性、逐路径判定、归属表接线断言、夹具判别力、字形字面量、授权出处、看板回写、行号时效） | P0 | `tools/lab/gate/records.py`、`tools/lab/gate/docs.py`、`tools/lab/docchain/`、`tests/test_gate_records.py`、`docs/issues/ISS-2026-10-29-新判据不可达与零覆盖四处.md` | T14 | ☑ 已完成 | 评审记录 `docs/features/feature-2026-10-29-全面修正与瘦身/reviews/review-2026-10-29-001.md` 与 `-002.md`；削弱反证逐字输出 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/redteam/weakening-2026-10-29.md`；修后门实跑 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/gate-runs/all-2026-10-29-r3.txt` |
| T20 | 改进环整体裁撤（#10 B）：删除 `skills/improve/`、四个治理角色、candidate / release-record 两份 schema 与 `examples/improve/`；episode 契约迁至 `schemas/episode.schema.json`；同步 manifest、保护清单、gate 必需条目与 schema 根、docchain 豁免表、活文档与产品链；设计知识与恢复清单留 `docs/design-decisions.md` §3 | P0 | `docs/design-decisions.md`、`schemas/episode.schema.json`、`.qoder-plugin/plugin.json`、`tools/lab/gate/{common,schema,examples}.py`、`tools/lab/docchain/constants.py`、`protected-paths.txt` | T19 | ☑ 已完成 | 删除与迁移已落：`test ! -e skills/improve`、`skills` 仅剩 `agentflow`、`agents` 10 个角色；`schemas/episode.schema.json` 承接 episode 契约；`gate/common.py` 的 `EPISODE_SCHEMA` 与 `REQUIRED_PROTECTED_PATHS`、`gate/schema.py` 的 schema 根、`gate/examples.py` 的 G10、docchain C13 豁免表与 `.qoder-plugin/plugin.json` 均已同步；三份历史记录中指向已删对象的 `files` 与 episode 指针按门 8 改为 `agentflows@f73a4e9:` + 摘录。`PASS schemas` / `PASS examples` / `PASS artifacts` / `PASS docs` / `PASS doc_chain_live`；设计知识与恢复清单见 `docs/design-decisions.md` §3 |
| T21 | `credentials` 字段加凭据形态 pattern（#12 C）：两份测试记录 schema 的 `credentials` 字段拒绝明显凭据形状，仅覆盖该字段 | P1 | `schemas/test-plan.schema.json`、`schemas/test-run.schema.json`、`tests/test_gate_schema.py` | T20 | ☑ 已完成 | 两份 schema 的 `credentials` 各加一条 pattern（`sk-` / `ghp_` / `Bearer ` / `token=` 等），description 明写「仅该字段、不做全正文扫描」；`tests/test_gate_schema.py::test_credentials_field_rejects_obvious_secret_shapes` 正反例全过；`PASS schemas` |
| T22 | C17 补 1–2 个变异项（#13 A）：`mutate.py` 的 `ITEMS`/`MUTATIONS` 纳入 `doc_chain.C17`，补「核验后修改 / 核验前修改」正反夹具并实跑杀死 | P1 | `tools/lab/mutate.py`、`tools/lab/docchain/checks.py`、`tools/lab/docchain/selftest.py` | T20 | ☑ 已完成 | 自测新增 `112`（核验后修改判红）与 `113`（核验前修改放行），总数 136/136；`tools/lab/mutate.py` 的 `--check doc_chain_selftest` 实跑 `总变异数 19 已杀死 19 存活 0 无效 0`（含 M53/M54 两条 C17）；夹具在 `tools/lab/docchain/selftest.py`；顺带修正一条既有失效锚点 M61（`.exists()` → `.is_file()`） |
| T23 | 委派契约补「定位即预算」（#14 A）：`read_scope` 一节写明定位质量与读取上限口径；同批重建 `packaging/runtime` | P1 | `skills/agentflow/references/contracts.md`、`packaging/runtime/` | T20 | ☑ 已完成 | `skills/agentflow/references/contracts.md` 的 read_scope 节新增「定位即预算」段：`path:line` 或可复核 Grep 模式、大文件片段交付、定位不足先索取、指向 SKILL 的评审简报定位义务；`PASS manifests` 证明 `packaging/runtime/` 与源逐字节一致 |
| T24 | 同题对照实验（#16 A）：选小型真实任务，with / without Agentflow 各跑一遍，记录执行方式、墙钟时间、门次数、返工轮次与正确性；报告写清代理指标与人时口径的差别 | P2 | `docs/evaluations/` | T23 | ☑ 已完成 | 报告 `docs/evaluations/AGENTFLOW-CONTROL-EXPERIMENT-2026-10-29.md`：隐藏验收两组 4/4；实现墙钟 49s vs 203s，含评审+修复约 632s；测试运行 2 vs 7；返工 0 vs 2；方法唯一可归因增量是评审抓到一处无判别力的测试 fixture。已写明 n=1、无人类参与、模型标签不可得等限制；两组工作副本与隐藏验收测试已归档 `docs/features/feature-2026-10-29-全面修正与瘦身/testing/agentflow-全面修正与瘦身/evidence/control-experiment-2026-10-29/` |

### 未决项

| # | 事项 | 推荐 | 拍板口编号 | 是否阻塞本表 |
| --- | --- | --- | --- | --- |
| 1 | 已关闭（2026-10-29 拍板 C）：前端/后端分立并补实现深度；三条件数字仍由 T16 产出 | 复跑后按数据裁决；语料不足时给保守结论 + 重审触发条件 | `docs/PENDING-DECISIONS.md` 第 22 条（已移出，见该文件表后出处段） | 否（只影响 T16 的产出形态） |
| 2 | 已关闭（2026-10-29 拍板 A+B）：本批维持现档，删档由下一批执行 | 下一批执行；本批先把引用改写口径做成判据 | `docs/PENDING-DECISIONS.md` 第 21 条（已移出，见该文件表后出处段） | 否 |
| 3 | 已关闭（2026-10-29 拍板 C/A）：凭据只给 `credentials` 加 pattern；C17 补两条变异 | 见 T21/T22 证据 | `docs/PENDING-DECISIONS.md` 第 12、13 条（已移出，见该文件表后出处段） | 否 |
| 4 | 已关闭（2026-10-29 拍板 A）：写范围执法器维持人工步骤，不接入 pre-push/CI | 登记在 `AGENTS.md` 与 `docs/releases/todo.md` | `docs/PENDING-DECISIONS.md` 第 15 条（已移出，见该文件表后出处段） | 否 |
| 5 | 已关闭（2026-10-29 拍板 C）：不设总量上限、只消副本 | 行数只作观测值 | `docs/PENDING-DECISIONS.md` 第 19 条（已移出，见该文件表后出处段） | 否 |
| 6 | 已关闭（2026-10-29 按落地事实）：载体表并入 `validate.py docs`；角色行数 34/44/22 ≤120 | 见 T07/T15 | `docs/PENDING-DECISIONS.md` 第 23、24 条（已移出，见该文件表后出处段） | 否 |
| 7 | 已关闭（2026-10-29 拍板 A）：维持移出 + 每次移出留可解析出处 | 见 `docs/PENDING-DECISIONS.md` 表后出处段 | `docs/PENDING-DECISIONS.md` 第 25 条（已移出，见该文件表后出处段） | 否 |
| 8 | 已关闭（2026-10-29 用户指示全部实施）：5 条已拍板项并入本批 T20–T24 | 按推荐实施 | `docs/PENDING-DECISIONS.md` 第 10、12、13、14、16 条（已移出，见该文件表后出处段） | 否 |

## 接口与共享机制

| 契约 | 变更 | 兼容性 | 消费方 |
| --- | --- | --- | --- |
| `schemas/review.schema.json` | 新增两字段 + 一条 `allOf` | 非破坏（字段可选，存量记录走「未声明」分支不红） | `tools/lab/gate/records.py`、`reviews/**`、批次 `reviews/**`（后者不受评审契约约束，见 `reviews/README.md` 校验范围条） |
| `validate.py artifacts` 的判据集合 | 新增 episode 字段引用校验与伪降级校验 | 行为增强，可能对现存记录判红 → 由 T10 逐条改写关闭 | `validate.py all`、宿主会话调用、`tests/test_gate_records.py` |
| C18 归属家族射程 | 扩至「未关闭待决行必须带拍板口编号」，仅对打 `agentflow 决策归属` 的批次生效 | 存量未打标批次不受影响；打标的两个批次中只有一个有待决行（T06 实测） | `doc_chain.py` 目录模式与 `--repo` 模式、`validate.py decision_gate` |
| 任务状态字形映射 | 双拷贝收为单源 | 无语义变更（两处消费方读同一份定义） | `gate/plan.py`（artifacts）、`docchain/checks.py` 的 C9 |
| `carrier-map.md` + `validate.py docs` 断言 | 新文件 + 既有门项扩断言 | 非破坏 | 表达面各载体、`packaging/runtime`（随插件交付需重建生成树） |
| 记录面引用改写口径 | `N/A: 理由 + 出处` 与 `仓库@修订:路径` 两种豁免成为机器可判形态 | 与 C23 对计划证据列的既有四种载体同源，不另立形态 | `episodes/**`、`docs/issues/**`、批次计划证据列 |

### 异常矩阵（关键路径各一条）

| 路径 | 失败形态 | 判定 | 处置 |
| --- | --- | --- | --- |
| T04 判据上线 | 首跑打红大批存量记录 | 命中数远超 37 处字段级预期 | 收窄白名单或补豁免，重跑；禁止摘标记转绿 |
| T04 判据上线 | 负例夹具不红（无判别力） | `EV-01` 通过失败 | 退回重写判据，不进 T10 |
| T09 schema 改动 | 改了源没重建快照 | `validate.py manifests` 报 `content differs from source` | 跑 `packaging/build_runtime.py`，不手改快照 |
| T09 伪降级判据 | 存量记录被追溯打红 | `RT-04` 转红 | 把「字段缺席 = 未声明不红」补回判据，不放行 |
| T11 删除 | 删除后仍有字段级悬空 | T10 的计数脚本 > 0，或 `validate.py docs` / `doc_chain_live` 红 | 从 git 历史恢复被删对象，补改写，再删；恢复必须重跑门才算数 |
| T11 删除 | 保全快照 `verify` 报红且消失的行不是本次改写 | 逐行比对 | 停止删除，先回查他人未提交内容 |
| T12 收敛 | 削掉了判据而门仍绿 | `--self-test` 用例数下降或 `decision_gate` 红 | 回退该处收敛，细则移回 |
| T14 评审 | 派发不可用 | 探测原始错误落档 | 记 `dispatch_errors`、档位 L0、结论上限 `partial`；不自审冒充清偿 |

### 发布顺序与回滚点

1. T01 → T02 → T03（文档与归口，纯文档面，可整节回退）。
2. T04 → T05 → T06 → T07 → T08 → T09（判据面；schema 与校验器**必须成对**回滚，
   退一留一会让记录被新约束拒绝或判据读不到字段）。
3. T10 → T11（先改引用后删对象；T11 的回滚点是 git 历史，工作树不保留副本）。
4. T12 → T13（表达面与导航面；T12 每处改写以 `carrier-map.md` 为据，可逐行回退）。
5. T14 收尾（评审门关闭前，本批结论上限 `partial`）。
6. T15 → T16（并入的深度项，不阻塞前四组）。

**评审门**：需求评审门与技术方案评审门各一轮，记录落 `reviews/`，档位由 T14 实测决定；
`changes_requested` 的 findings 一律转 `docs/issues/` 记录，不就地口头修复。

## 验证命令

```sh
# 全量门（11 项）——解释器用仓内 .venv，系统 python3 是 3.9.6 跑门必红
.venv/bin/python tools/lab/validate.py all
# 本批文档链
.venv/bin/python tools/lab/doc_chain.py "docs/features/feature-2026-10-29-全面修正与瘦身"
# 检查器自测（用例数不得比基线 124 少）
.venv/bin/python tools/lab/doc_chain.py --self-test
# 单元回归
.venv/bin/python -m unittest discover -s tests
# 受保护门清单完整性与生成树新鲜度
.venv/bin/python tools/lab/validate.py protected
.venv/bin/python tools/lab/validate.py manifests
# 安装面漂移（本批经授权不重装，预期报漂移，如实记录不冒充通过）
.venv/bin/python tools/lab/validate.py installed
```

**命令依据**：`标准`（`AGENTS.md`「接受任何产物之前」与 `tools/lab/README.md`）；解释器路径的依据是
人工确认：2026-10-29 实测仓内 `.venv/bin/python` 为 3.12.14，系统 python3 为 3.9.6，跑门必红。

## 残余风险

| 风险 | 责任人 | 触发信号 | 处置办法 |
| --- | --- | --- | --- |
| 判据过宽的残留：episode 字段值里存在「描述性路径」而非「指针」的写法 | 本批实施者 | T03 扫描命中里出现语义明显是叙述的值 | 按值改写为该字段的合法形态或 `N/A: 理由`；不改判据去迁就假绿 |
| 生成树不重装导致宿主读到旧文本 | 用户（决定何时重装） | `validate.py installed` 报漂移 | 已授权不含重装；漂移逐文件报告并给出 `packaging/build_runtime.py` 后的下一次安装动作 |
| 必读面 ≤450 的预算与「判据不缩」冲突 | 本批实施者 | T12 期间 `--self-test` 用例数下降 | 优先拆细则文件，其次压散文；宁可留判据超预算并如实报告，不删判据凑数 |
| 三批旧计划继续被其它会话引用 | 后续批次 | 会话读到旧批次状态与本批计划不一致 | T02 的四处回写是收口动作；漏一处即 G1-AC-02 红，按验收点补 |
| 独立评审推翻本批判据设计 | 评审轮 | 评审记录 `changes_requested` | findings 转 ISS，受影响的判据回到待修状态，不进 T11 之后的删除步骤 |
