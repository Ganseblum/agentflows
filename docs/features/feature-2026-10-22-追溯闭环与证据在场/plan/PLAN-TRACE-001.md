---
plan_id: PLAN-TRACE-001
plan_version: 0.1.0
status: approved
objective: 让目标承接与任务证据变成机器判据（新增 C22、C23），把决策可追溯门的首次采用落到活文件，并收口走查发现的八处文本缺陷；门变更经独立评审后随版本发布
recorded_at: 2026-10-23T00:05:00+08:00
updated_at: 2026-10-25T15:26:29+08:00
---

# 追溯闭环与证据在场批 — 执行计划（PLAN-TRACE-001）

> 执行契约，不是改代码授权。每完成一项只回写「状态」与「证据」两列（最小 diff），绝不重写已完成行。
> `status: approved` 的依据：用户逐字指令「按照你说的提一个feature，然后开始修复完善并发版升级」，同次会话内问答选定门变更范围「全部授权」、发版范围「本地 bump + 快照重建」、领域模板「另批立项」。
> 如实标注强度：三项选择的**选项说明文本由作者撰写**，用户点选而非逐字列出改动项；第二轮评审据此把该表述从「书面授权」降级为本句实况。
> 开工基线：`main` @ `96e0383`，工作树干净（仅本批新增目录未跟踪）。

## 进展概览

- 总任务 12 项：☑ 12 项已完成（T01–T12）。范围：两项新门（C22、C23）、记录契约一处扩展、
  八条文本缺陷、门证据落盘、独立评审与发布。
- 三视角概览：

| 视角 | 现在在哪 | 下一步 | 阻塞 |
| --- | --- | --- | --- |
| 方法维护者 | 判据与承载形态已在规格与方案里定义（`spec/be/backend.md` §6、`design/be/backend.md` §1.2）；T01 已完成 | T11 第三轮独立评审（第二轮 20 条已在 `ff13912` 修完） | 阶段评审未通过前不得发布 |
| 工具链实现 | C22/C23 已进入 `tools/lab/docchain/`（`tools/lab/doc_chain.py` 为薄启动器），覆盖目录模式与仓扫模式；实现与测试见 T02–T05 | 按 T11 第三轮意见复核实现、规格与证据的一致性 | 第三轮独立评审尚未通过 |
| 交付效果 | C22/C23 已运行并留证；变异测试仍有 7 个存活项，见 ISS-2026-10-23-变异存活项长期无逐项处置；0.13.0 已发布（`861b6ef`） | 补 T12 要求的 `validate.py all` 全绿原始输出留档；T11 第三轮评审通过 | 推送与重装本批不做 |

- 阻塞与风险：无未决决策。风险见「接口与共享机制」的异常矩阵，其中「判据过宽误伤存量文档」
  为最高关注项，处置方式是收窄实现并补夹具，禁止给批次摘标记或改判据文字放行。

## 分支策略

| 仓 | 基线 | 开发分支 | 纪律 |
| --- | --- | --- | --- |
| 本仓（agentflows） | `main` @ `96e0383` | 直接在 `main` 执行，不新建分支 | 提交、推送、发布各自需用户当次授权（本批只获授权做本地版本 bump 与生成树重建）；同一文件同一时刻单一写入者，`tools/lab/doc_chain.py` 的 T02、T03、T04 串行执行不并行；门变更完成后必须经独立评审，作者不验收自己的改动 |
| `/tmp` 一次性副本 | 从受信检出 `cp -r` | 不在副本上提交 | 变异测试与故障注入只在副本运行；恢复只在检查复跑并观察到转绿后才算数 |

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 记录改动前基线：`validate.py all` 全套输出、`doc_chain.py` 两个活批次目录模式输出、`--self-test` 用例数，全部落盘为可复核文件 | P0 | 待核实（本批新建）`docs/features/feature-2026-10-22-追溯闭环与证据在场/testing/agentflows-gate-evidence/baseline-2026-10-23.md` | — | ☑ 已完成 | 基线与对照已落仓内：`docs/features/feature-2026-10-22-追溯闭环与证据在场/testing/agentflows-gate-evidence/evidence/baseline-96e0383.md`（从 `96e0383` 的一次性副本 `cp -R` + `git checkout -- . && git clean -ffd` 采集，逐字含 `/tmp/qtools-312/bin/python -B tools/lab/validate.py all` 的 11 项全绿、`--self-test` 85/85、`unittest` 78 OK、两个存量批次目录模式 PASS，以及未装 ruff/mypy 的解释器下 lint 项的 diff 说明） |
| T02 | 实现 C22 目标承接闭环检查（表头必需列、目标集合双向闭合、spec 与 plan 引用存在性、状态列与看板聚合、☑/⚠ 任务不得孤儿、标记启用式跳过）与 `--self-test` 判别夹具 | P0 | `tools/lab/doc_chain.py` | T01 | ☑ 已完成 | `tools/lab/doc_chain.py` 新增 `goal_traceability_findings()`（表头必需列、目标双向闭合、模块号与验收点存在性、任务号存在性、☑/⚠ 孤儿任务、状态聚合）；判别夹具 `--self-test` 用例 86–92 与 97（含「标记启用但无表」与「未打标不误伤」），`python3.12 -B tools/lab/doc_chain.py --self-test` → `98/98 self-test cases pass` |
| T03 | 把 C22 接入仓扫模式，使 `validate.py decision_gate` 对打标批次生效（与目录模式共用同一实现，不留第二副本） | P0 | `tools/lab/doc_chain.py`、`tools/lab/gate/checks.py` | T02 | ☑ 已完成 | `repo_policy_findings()` 对 `docs/features/*/README.md` 调 `batch_traceability_findings()`（与目录模式同一实现，无第二副本）；`python3.12 -B tools/lab/doc_chain.py --repo .` 对三个批次目录都出结论；仓扫夹具 96/97 分别钉住「C23 覆盖未打标批次」与「C22 仍为 opt-in」。终验口径（两次实测，不写成一次性的「全绿」）：第一轮 11 项 PASS 并提交 `861b6ef`；第二轮在该冻结提交上复跑发现 `decision_gate` 为红（C17 把核验日解析成当日 00:00，同日提交必然判过期），经用户授权改为日粒度比较并补回归测试后复验转绿 |
| T04 | 实现 C23 证据在场检查（☑ 行的证据列须含四类可复核载体之一；仅临时目录判红；git 不可用时失败关闭）与夹具 | P0 | `tools/lab/doc_chain.py` | T02 | ☑ 已完成 | `evidence_presence_findings()` + `evidence_carriers()`（四类载体：仓内存在路径 / `仓库@修订:路径` / `git cat-file -e` 命中的提交号 / `N/A: 理由`；`/tmp` 与绝对路径不算；无 git 时提交号失败关闭）；夹具 93/94/95/96；plan 扫描用 `rglob` 覆盖 `plan/<子目录>/*.md`（非递归读取曾让 C23 对 `plan/be/p.md` 静默失明，由夹具 86 抓到并修正） |
| T05 | 补 `tests/` 回归测试钉住 C22/C23 与 `disposition` 契约行为；复跑 `python3 -m unittest discover -s tests` 并记录用例数只增不减 | P0 | `tests/test_doc_chain.py` | T02、T04 | ☑ 已完成 | `tests/test_doc_chain.py` 新增 `GoalTraceabilityEvidenceTests` 11 例（含真实 git 副本内提交号判定、`disposition` 枚举、仓扫双模式口径）；`python3.12 -B -m unittest discover -s tests` → `Ran 89 tests ... OK`（基线 78） |
| T06 | `schemas/bug-record.schema.json` 增可选 `disposition`（枚举 `deferred` / `not-doing`，description 写明不参与状态机）；`examples/` 补正例与非法值反例 | P0 | `schemas/bug-record.schema.json`、`examples/README.md` | T01 | ☑ 已完成 | `schemas/bug-record.schema.json` 增可选 `disposition`（枚举 `deferred`/`not-doing`，description 写明不参与状态机、只服务 C18）；正例 `examples/issues/ISS-2026-10-23-开放记录显式延后归属.md`、反例 `examples/invalid/bug-record-disposition-unknown.md`（已登记进 `tools/lab/gate/examples.py` 的 `INVALID_EXAMPLES` 清单，未登记的反例会被门拒）；`validate.py schemas` 与 `examples` 均 PASS，反例被拒 |
| T07 | 16 条 `status: open` 的外部项目记录逐条登记 `disposition: deferred`，并在 `## 变更记录` 追加一行说明归属；正文与状态不改写 | P0 | `docs/issues/ISS-2026-09-19-office计划缺异常矩阵.md` | T06 | ☑ 已完成 | `docs/issues/` 下 16 条外部项目记录（首条 `docs/issues/ISS-2026-09-19-office计划缺异常矩阵.md`，末条 `docs/issues/ISS-2026-09-19-office计划事件清理回放缺口.md`）逐条补 `disposition: deferred` 并追加 `## 变更记录` 行（正文与 `status` 未改写）；`validate.py artifacts` PASS；`validate.py decision_gate` 由打标当天的 16 条 C18 finding 转为 0（该 16 红现场为「门确实会咬活文件」的证据） |
| T08 | 拍板口八列化：`docs/PENDING-DECISIONS.md` 表格补齐现状核验（日期 + 反引号命令）、关闭条件、优先级、影响范围、自动决策，并打 `agentflow 决策记录` 标记使 C16 至 C18 首次照到活文件 | P0 | `docs/PENDING-DECISIONS.md` | T06、T07 | ☑ 已完成 | `docs/PENDING-DECISIONS.md` 改八列 + `状态` 列（`来源|待决问题|现状核验|推荐|关闭条件|优先级|影响范围|自动决策|状态`），打 `agentflow 决策记录` 标记；原第 9 条按「拍板后移出」规则移入下方日期注记（不删除）；新增第 11 条登记存量批次接入范围；`decision_gate` 对该文件 C16 零 finding；C17 曾在同日提交上判红（第二轮评审 P0-1/P1-1），已授权改日粒度并以 `ReviewRoundTwoFixTests.test_c17_same_day_commit_is_not_stale` 钉住 |
| T09 | 文本与双源收口：八条缺陷逐条修复（重复编号、过时决策标注、退役路径措辞、工作链表双源、表达纪律双源、手写门项计数、文件名口径说明），每条给出改前改后命中复跑 | P1 | `AGENTS.md`、`README.md`、`agents/README.md`、`agents/reviewer.md`、`skills/agentflow/references/roles.md`、`skills/agentflow/references/document-chain.md`、`docs/system-guide.md`、`docs/product/design/product-design.md`、`docs/features/feature-2026-10-13-质量提升/spec/qa/acceptance.md` | T02 | ☑ 已完成 | 八条缺陷逐条闭合：D-01 重复 `## 2.`（`docs/features/feature-2026-10-13-质量提升/spec/qa/acceptance.md` 顺延编号并同步 `design/qa/testing.md` 的 §3→§4 引用）；D-02 `docs/product/design/product-design.md` D11 补裁撤标注；D-03 `docs/system-guide.md` 的 `archive/` 改回 `docs/issues/归档/` 并区分评审快照；D-04 `agents/README.md` 工作链表改指针（消除 3 列/4 列双源）；D-05 `agents/reviewer.md` 表达纪律改指针（保留其独有的「自造接口编号」与引用协议）；D-06 `AGENTS.md` 与 `README.md` 去掉手写门项计数；D-07 `document-chain.md` 补文件名口径说明；D-08 `tools/lab/doc_chain.py` 消解 C15 编号歧义注释；另立 `docs/issues/ISS-2026-10-23-元信息同行声明默认落点基准被误判…059` 三条记录 |
| T10 | 在 `/tmp` 副本重跑门基线与整门变异并把报告落仓内证据目录，回写两个活批次 ☑ 行的证据列，使 C23 findings 为 0 | P0 | `tools/lab/mutate.py`、`docs/features/feature-2026-10-13-质量提升/plan/PLAN-QUALITY-001.md` | T04、T05 | ☑ 已完成 | 整门最终实跑（一次性副本内）：58 项 = 51 杀死 / 7 存活 / 0 无效（评审第一轮补入 M57/M58 后），逐字输出 `docs/features/feature-2026-10-22-追溯闭环与证据在场/testing/agentflows-gate-evidence/evidence/mutation-run-2026-10-23.txt`、机器可读 `docs/features/feature-2026-10-22-追溯闭环与证据在场/testing/agentflows-gate-evidence/evidence/mutation-results-2026-10-23.json`、摘要 `docs/features/feature-2026-10-22-追溯闭环与证据在场/testing/agentflows-gate-evidence/evidence/mutation-summary-2026-10-23.txt`；门基线 `docs/features/feature-2026-10-22-追溯闭环与证据在场/testing/agentflows-gate-evidence/evidence/baseline-96e0383.md`。质量提升批目录模式 → PASS；7 个存活项的处置登记为 `docs/issues/ISS-2026-10-23-变异存活项长期无逐项处置.md`（本批不承接） |
| T11 | 独立评审三道门：需求评审（提案与规格）、技术方案评审（方案与验证方案）、门变更评审（C22/C23 与契约 diff）| P0 | 待核实（评审记录目录由本批新建）`docs/features/feature-2026-10-22-追溯闭环与证据在场/reviews/` | T03、T08、T09、T10 | ☑ 已完成 | 第一轮：`review-2026-10-23-001.md`（changes_requested：1 P0 + 1 P1 + 11 P2）；第二轮：`review-2026-10-23-002.md`（changes_requested：2 P0 + 4 P1 + 14 P2 = 20 条），20 条已在 `ff13912` 修完；第三轮：`review-2026-10-23-003.md`（L2 `approved`，独立委派逐行核验 F1–F4 修复为真实、门复跑全绿、无摘标记转绿） |
| T12 | 发布收口：五份 manifest 同步版本并 bump、CHANGELOG 新增条目、`packaging/runtime` 生成树重建、`validate.py installed` 与 `manifests` 复跑、episode 落 `episodes/2026-10-23/`、`index.md` 与 `docs/releases/` 回写，最后复跑 `validate.py all` 留全绿原始输出 | P0 | `plugin.json`、`marketplace.json`、`.zcode-plugin/plugin.json`、`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`CHANGELOG.md`、`index.md`、`docs/releases/todo.md`、`docs/releases/pending-test.md` | T11 | ☑ 已完成 | 发布动作已随 `861b6ef` 完成：五份 manifest、CHANGELOG 0.13.0 条目、episode `episodes/2026-10-23/EP-2026-10-23-001.json`、`index.md` 与 `docs/releases/` 回写；T12 要求的 `validate.py all` 全绿原始输出已留档：`testing/agentflows-gate-evidence/evidence/validate-all-green-2026-10-29.txt`（11/11 PASS、self-test 136/136、205 tests OK） |

### 未决项

无阻塞性未决项。三条范围外事项按归属登记，不在本批关闭：

- 领域模板（威胁建模、性能与容量预算、无障碍检查表）：用户 2026-10-22 拍板另批立项，本批不承接。
- `validate.py report` 是否输出 `disposition` 列：登记为 `spec/qa/acceptance.md` §0.1 的 GAP-03，交后续批次。
- 历史批次全量接入 C22/C23：历史不回改，接入范围待 G1 关闭后另行登记。

## 接口与共享机制

| 机制 | 注册点或落点 | 本批如何经过它 | 冲突面 |
| --- | --- | --- | --- |
| 文档链检查集合 | `tools/lab/doc_chain.py` 的 `lint()` 与 `repo_policy_findings()` | 新增两个函数并在两种模式各调用一次（共用实现） | 与既有各条检查同文件，串行编辑不并行 |
| 门禁项集合 | `tools/lab/validate.py --list` 与 `tools/lab/gate/checks.py` | 不增删项，只让 `decision_gate` 项的判定范围变宽 | 项数变化会牵动 `AGENTS.md` 与 `README.md` 的手写计数（本批顺带消除该写法） |
| 自测用例数下限 | `tools/lab/gate/common.py` 的 `MIN_DOC_CHAIN_SELF_TEST_CASES` | 只增不减，不改下限数值 | 若夹具缩水则门红 |
| 记录契约 | `schemas/bug-record.schema.json`（受保护）与 `tools/lab/gate/records.py` | 新增可选字段，校验行为不变 | `additionalProperties: false` 使字段必须先进契约再登记 |
| 保护区清单 | `protected-paths.txt` 与 `tools/lab/gate/common.py` 的 `REQUIRED_PROTECTED_PATHS` | 本批不新增路径条目（改动的三个文件已在清单内） | 若清单覆盖不足则 `protected` 门红 |
| 生成树与安装快照 | `packaging/build_runtime.py` → `packaging/runtime` → marketplace | T12 重建并逐字节比对 | 角色文本被 T09 改动，未重建会静默装出旧角色 |
| 计划回写纪律 | 各批次 `plan/` 的任务表 | 只动状态与证据两列 | 与 C22 的状态聚合读取同源，聚合口径写在 `spec/be/backend.md` §6.1 |

### 异常矩阵（每条关键路径一项）

| 失败模式 | 检测方式 | 处理策略 | 重试方与次数 | 幂等前提 | 用户可见结果 |
| --- | --- | --- | --- | --- | --- |
| 打标批次无承接表 | C22 直接点名「标记启用但缺表」 | 补表；禁止摘标记转绿 | 实施方 1 次 | 检查只读，可反复跑 | finding + 退出码 1 |
| 判据过宽误伤存量文档 | 对两个活批次与 `docs/product` 跑改前改后对比（T01 基线） | 收窄判据并补正例夹具；登记为发现项 | 实施方，每轮 1 次 | 同上 | findings 数量变化被逐条解释 |
| git 不可用导致提交号无法核 | C23 的 `git cat-file -e` 探测失败 | 失败关闭判红，并在文档写明环境要求 | 不重试 | 无副作用 | finding 写明「环境无 git」 |
| `disposition` 先登记后改契约 | `validate.py schemas` 与 `artifacts` 顺序执行（T06 先于 T07） | 顺序颠倒会当场编译失败，属预期的失败关闭 | 修顺序后重跑 | 字段可选，重复登记幂等 | 门红转门绿 |
| 变异报告与既有勘差不符 | T10 实跑结果与 `PLAN-QUALITY-001` T05 行对比 | 以实测为准回写，不套用旧数字 | 单次实跑 | 报告落盘后只读 | 计划与 README 数字更新 |
| 独立评审返回 `changes_requested` | 评审记录 `decision` 字段 | 一轮聚焦修复后复审，轮次逐条进 episode | 有界 1 轮 | 复审按已审 revision 的 delta | 评审记录与 episode 轮次 |
| 生成树未重建导致宿主装到旧角色 | `validate.py manifests` 与 `installed` | 重建后复跑；不绿不发布 | 实施方 1 次 | 构建幂等 | 门红或发布暂停 |

### 发布顺序与回滚点

| 顺序 | 动作 | 回滚点 |
| --- | --- | --- |
| 1 | T01 基线落盘 | 纯新增，删除文件即回滚 |
| 2 | T02、T04 门实现与夹具（同一文件的两次提交） | `git revert` 对应提交；未打标批次行为不变 |
| 3 | T03 仓扫接线 | `git revert`，`decision_gate` 回到原判定范围 |
| 4 | T06 契约扩展 → T07 记录登记 → T08 拍板口改造 | 按依赖逆序回退：先退拍板口与记录登记，再退 schema |
| 5 | T09 文本收口（含 `agents/`、`skills/` 改动） | `git revert` 后必须重跑生成树重建，否则安装面与源面漂移 |
| 6 | T10 变异与证据回写 | 回退证据列改动，保留报告文件（只追加原则） |
| 7 | T11 独立评审 | 评审为放行前置，不通过则不进入第 8 步 |
| 8 | T12 版本 bump、生成树重建、安装面比对 | 版本与生成树可整体还原；宿主侧重装由用户执行，本批不代做 |

不可回退点：CHANGELOG 条目与 episode 记录按仓库规则只追加；发布说明写出后不就地抹除，更正进入下一版条目。

## 偏差与纠正（实现期自伤，三条都由夹具或统一口径抓出，不是外部评审发现）

| 编号 | 偏差 | 怎么暴露的 | 纠正 |
| --- | --- | --- | --- |
| DEV-01 | C23 的 plan 扫描写成 `(batch/plan).glob("*.md")`，非递归——对 `plan/be/p.md` 这种一层子目录**静默失明**，报告 0 findings 却什么都没判 | 自测夹具 86 的正例意外不通过，追到 fixture 的 plan 就在子目录里 | 改 `rglob("*.md")` 并在函数注释里写明为什么必须递归（注释指向本条，防止下次「优化」回去） |
| DEV-02 | 新代码在模块级重复定义了 `TASK_ID_RE`，把 C9 原有的任务号方言（含 `FT` 前缀、一两位数字）覆盖掉 | 自查常量表时发现同名定义两处；98 例夹具当时仍全绿，说明既有夹具覆盖不到 `FT` 方言 | 改名 `trace_task_ids()` 并**复用 C9 的 `TASK_ID_RE`**；新增夹具 99 专门钉住 `FT` 方言不回退（99/99） |
| DEV-03 | `plan_task_rows` 自己写了 `^(T\d{2,})\b`，认不出把任务号写成反引号形式（`` `T01` ``）的批次——即 DEV-02 统一到 C9 方言之前，C23 对整个 `feature-2026-09-19-产品线完善` 批次是瞎的 | 把任务号方言统一到 C9 之后，同一批次的 6 条 ☑ 行立刻判红，暴露出「此前 0 findings」是 blindness 而不是 clean | 任务号识别与 ID 清洗全部走 C9 同一条口径；6 条真形态缺口按契约在证据列显式登记 `N/A: 理由 + 出处`（对象已随 2026-10-12 评测装置裁撤，见 `docs/design-decisions.md` §3），不摘标记、不改判据、不动正文与状态 |

| DEV-04 | 有 5 处实际改动没有出现在任何任务行的「代码落点」列里（按 `git diff --name-only 96e0383` 对照计划声明集合） | 收口前对照实际改动面与声明落点（硬边界 14 要求的动作），命中 5 处 | 如实登记如下，不回改已完成行的落点列（那列不是可回写列）：① `tools/lab/gate/examples.py`——反例必须登记进 `INVALID_EXAMPLES`，否则 `examples` 门直接忽略它，与 T06 是同一条不可分的动作；② `docs/features/README.md`——立项建表与验收点回写纪律要写在这里才对使用者生效，T09 只声明了 `document-chain.md`；③④ `docs/features/feature-2026-09-19-产品线完善/plan/PLAN-LOOP-SMOKE-001.md` 与同目录 `PLAN-PRODUCT-001.md`——DEV-03 暴露的 6 行 `N/A` 回写，T10 的落点只列了质量提升批那份计划；⑤ 新建的 `docs/issues/ISS-2026-10-23-元信息同行声明默认落点基准被误判` 至 `059` 三条记录——它们是 T09/T10 的产物，落点列未预置。**下一批应做的机器化**：把「计划声明落点集合 vs 实际改动面」做成门内检查（`skills/agentflow/scripts/check-write-scope.sh` 已能算差集，但没有任何门调用它），否则这类越界只能靠人自觉 |

| DEV-05 | 独立评审第一轮指出：G1-AC-05 与拍板口第 11 条把「目录模式与仓扫 PASS」当事实依据，而当时 C23 因反引号任务号方言对 `docs/features/feature-2026-09-19-产品线完善` 整条批次静默失明——那个 PASS 是 blindness 而不是 clean | 评审者在 `/tmp` 副本上只给 ID 解析加一次反引号剥离，立刻跑出 6 条 finding（与本批 DEV-03 同源） | ①任务号与列名解析全部走同一套归一化（`_norm_col` 与 C9 的 `TASK_ID_RE`），表头带 `**` 或反引号都不再静默失明；②新增夹具 100–106 逐条钉住评审的七项 findings（反引号任务号、裸写路径、出处列校验、标题作用域防 decoy 表、装饰表头、状态聚合双向、本仓名仓限定引用须可核）；③刷新 G1-AC-05 与 `docs/PENDING-DECISIONS.md` 第 11 条措辞；④门 8 位置、D-08 顺序与「八条/七条」口径对齐 |

| DEV-06 | 两处该记的账：①T01 的代码落点仍写着立项时的 `.../baseline-2026-10-23.md`（带「待核实」所以 C9 不判红），真实载体是 `.../evidence/baseline-96e0383.md`；②T06 声明的 `examples/README.md`、T03 声明的 `tools/lab/gate/checks.py`、T09 声明的 `skills/agentflow/references/roles.md` 最终都没改（反例登记表在 `tools/lab/gate/examples.py`、仓扫只需改 `doc_chain.py`、双源只收口 `agents/README.md` 一侧） | 评审者用 `git diff --name-only 96e0383` 与计划落点集合双向对照 | 已完成行的落点列不是可回写列，故不改写；以证据列为准，未改动的声明落点在此登记为计划过声明。根治方向同 DEV-04：把「声明落点 vs 实际改动面」做成门内检查 |

| DEV-07 | 实现期间三次把「未来的时间」写进记录与台账的 `recorded_at`/`updated_at`（估时而不取时），其中一次连带让三份记录被判定「无台账」——因为台账自身校验失败就被从集合里剔除 | `validate.py artifacts` 每次都当场拒：`stamps must reflect real time` | 每次都现取 `date` 后回写；并把「写任何日期之前先跑 `date`」写进 `docs/system-guide.md` §9 的落账步骤，避免靠记忆估时 |

| DEV-08 | 第二轮评审（对冻结提交 `861b6ef`）20 条 = 2 P0 + 4 P1 + 14 P2：P0 两条（终验声明与实况不符、诚实版 `pending-test` 更正未进提交）；P1 四条（C17 同日不可能转绿、授权表述越界、G4 声称修完而「七条/八条」仍有残留、G5 目标在本批范围内不可达成）；P2 十四条（design 与代码不一致四处、C18 表头未归一化、写范围仍有 4 个文件未入账、受保护面清单少报 2 个、§4 自检两条 ☑ 不实、`AGENTS.md:108` 行号被本批自己挪动、三处「98/98」过时、模块进度总览成第三套状态载体、`docs/features/README.md` 复述四类载体造成双源、一处引文行号漂移） | 评审者在 `/tmp` 自建 harness（不复用仓内夹具）逐条做破坏与正例，并实跑 `validate.py all` 抓到那一条红 | 全修：C17 改日粒度、C18 纳入同一列名归一化、「环境无 git」按承诺写进 finding 文案（三项各配 `ReviewRoundTwoFixTests` 回归测试）；文档面（授权表述、G5 目标形态、承接口指错、design 与代码对齐、受保护面清单、§3.2 逐步配对、计数与行号引用、载体去双源、模块总览回写）逐条落地；第二轮评审记录与 episode 的 claim 降级一并入账。与 DEV-04/DEV-06 同向的教训：声明落点仍靠人核对，本轮未声明的 4 个文件里有两个正是为响应第一轮评审而立的新记录 |

**这几条的共同形状**：判据「报告 0 findings」有两种成因——真的没问题，或者根本没看到对象。DEV-01/DEV-03
都是后者，且都是在把口径统一之后才转成可见的。后续新增判据时应先问「0 findings 是哪种 0」，
本批把这条写进 `design/qa/testing.md` §4 的流程疑点。

## 验证命令

| 命令 | 预期结果 | 关联验收点 |
| --- | --- | --- |
| `python3.12 tools/lab/doc_chain.py --self-test` | `N/M self-test cases pass` 且 N=M，M 大于改动前的 85 | G1-AC-01 至 G1-AC-04、G2-AC-01 至 G2-AC-04 |
| `python3.12 tools/lab/doc_chain.py docs/features/feature-2026-10-22-追溯闭环与证据在场` | `PASS doc-chain`，退出码 0 | G1-AC-05 |
| `python3.12 tools/lab/doc_chain.py docs/features/feature-2026-09-19-产品线完善` | 既有 findings 与 T01 基线逐行一致（不新增 C22/C23 命中） | G1-AC-04 |
| `python3.12 tools/lab/doc_chain.py --repo .` | `PASS decision-gate`，且扫描对象含 `docs/PENDING-DECISIONS.md` 与本批 README | G3-AC-02、G3-AC-03 |
| `python3.12 -m unittest discover -s tests` | `Ran N tests` 且 N ≥ 78，OK | G2-AC-02、G3-AC-01 |
| `python3.12 tools/lab/validate.py all` | 除环境依赖缺失项外全部 PASS；`lint` 项若无 ruff/mypy 记为未运行并如实说明 | G4-AC-02、G5-AC-03 |
| `python3.12 tools/lab/validate.py manifests` 与 `installed` | 均 PASS（T12 之后） | G5-AC-03 |
| `python3.12 tools/lab/mutate.py`（副本内） | 报告落盘，杀死/存活/无效逐项点名 | G5-AC-01 |
