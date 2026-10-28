# 追溯闭环与证据在场批 — 验收标准（spec/qa）

> 前置输入：`proposal/proposal.md`、`spec/be/backend.md`。
> 来源优先级声明：本文件各验收点的口径按「proposal 原文 > spec/be」顺序裁决；两份上游冲突且都可
> 引用时以靠前者为准，并把冲突登记进 §0.1 缺口台账，不静默择一。

## 0. 来源对齐缺口与待确认台账

### 0.1 缺口台账

| 编号 | 待对齐文档或实现 | 影响阶段 | 关闭条件 |
| --- | --- | --- | --- |
| GAP-01 | `tools/lab/gate/checks.py` 的自测用例数下限守卫与新增 C22/C23 夹具数 | 实施 | 新增夹具后复跑 `doc_chain.py --self-test`，用例数只增不减且门绿 |
| GAP-02 | `decision_gate` 的仓扫入口是否会把 C22 应用到未打标批次 | 实施 | 实现后实测：未打标批次 findings 为 0，打标批次命中 |
| GAP-03 | 16 条外部开放记录登记 `deferred` 后，`report` 子命令的过滤列是否需要同时输出该字段 | 评审 | 评审给出结论：本轮不改 `report` 输出，登记为后续事项 |

### 0.2 待确认事项

| 编号 | 问题 | Owner | 是否阻塞 design | 结论 |
| --- | --- | --- | --- | --- |
| OQ-01 | 门变更授权范围 | 用户 | 否（2026-10-22 已授权「全部」，含 C22、C23、`disposition` 与门清单同步） | 已关闭 |
| OQ-02 | 发版范围 | 用户 | 否（选「本地 bump + 快照重建」） | 已关闭 |

## 1. 目标范围与不做

| 类型 | 内容 | 依据或承接口 |
| --- | --- | --- |
| 实现改动范围 | M-A 至 M-F | `spec/be/backend.md` §5；proposal §1.3 |
| 范围外 | 领域模板、效果测量、历史批次全量接入、改进环角色处置、推送与重装 | proposal §1.3 与 §四 范围决策表 |

## 2. 边界与异常覆盖

| 类型 | 条件或触发 | 正确结果 | 关联验收点 |
| --- | --- | --- | --- |
| 缺承接 | 打标批次里某目标在 spec 与 plan 都无落点 | C22 finding，退出码 1 | G1-AC-01 |
| 幻影引用 | 承接表写了 `T99`，计划任务表里没有 | C22 finding | G1-AC-02 |
| 状态不一致 | 承接表写 ☑ 已完成，所引任务行仍是 ☐ 未开始 | C22 finding | G1-AC-03 |
| 证据散失 | ☑ 行证据只写 `/tmp/xxx.txt` | C23 finding | G2-AC-01 |
| 提交号可解析 | ☑ 行证据含 `1be1905`，git 历史有该提交 | 通过 | G2-AC-02 |
| git 不可用 | 只有提交号可用，但环境无 git | 不算可复核，判 finding（失败关闭，不放行） | G2-AC-03 |
| 外部仓引用 | 证据写 `other-repo@abc123:docs/x.md` | 通过（跨仓事实本仓不可达，按记录契约同等处理） | G2-AC-02 |
| 未打标批次 | 历史批次无承接标记 | C22 不触发（标记启用）；C23 仍按既有计划契约判证据列——归属是可选治理，证据义务不是 | G1-AC-04 |
| 契约扩展 | 记录写 `disposition: deferred` | schema 通过；写非法值被拒（`examples/invalid/bug-record-disposition-unknown.md` 钉住）；字段不参与状态机 | G3-AC-01 |

## 3. 判据（预先写定，落地后不得放宽）

| 判断项 | 通过条件 | 未满足时 |
| --- | --- | --- |
| 新门确实照到活文件 | `doc_chain.py --repo .` 的扫描对象里，带 C15/C16/C18 或 C22 标记的**非夹具**文件数 ≥2，且这些文件当前 findings 为 0 | 不得靠摘掉标记转绿，须补齐载体 |
| 新门有判别力 | C22、C23 各至少 1 正 1 负自测夹具，且负例的 finding 串含对应检查号 | 视为未实现，不接受「代码写了」的摘要 |
| 既有行为不回退 | `validate.py all` 全套检查通过；`doc_chain.py docs/features/feature-2026-10-13-质量提升` 与 `docs/product` 的既有 findings 不因本批新增而变红 | 回退新增判据，或如实登记为放行项并说明 |
| 证据可复核 | 三个批次计划里每个 ☑ 行的证据列都能被 C23 判定为含可复核载体 | 补落盘证据或把状态改回真实值，不允许改判据 |

## 4. 工程模块验收点

### G1 目标承接可机判（M-A）

| 验收点 | 验收目标 | 场景或条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G1-AC-01 | 目标缺承接即红 | 打标批次里删掉某目标的 plan 引用 | `doc_chain.py <批次>` 输出含 `C22 目标承接`，退出码 1 | P0 | proposal §1.2 G1 |
| G1-AC-02 | 幻影任务号红 | 承接表写 `T99`（计划无此行） | finding 点名 `T99` 不存在 | P0 | proposal §1.2 G1 |
| G1-AC-03 | 状态列与看板一致 | 承接表 ☑ 而任务行 ☐ | finding 指明状态不一致 | P1 | proposal §1.2 G1 |
| G1-AC-04 | 未打标批次不误伤 | 对 `docs/features/feature-2026-09-19-产品线完善` 跑目录模式 | 不产生 C22 findings（既有检查行为不变） | P0 | proposal §1.3 范围外条款 |
| G1-AC-05 | 仓扫入口生效且批次集合与目录模式一致 | `doc_chain.py --repo .` 在本仓跑，遍历 `docs/features/*/` 全部批次目录（不以「有没有 README」为门槛） | 打标批次的承接问题与所有批次计划的证据列都进入 `decision_gate`；归零的前提是 8 行历史散失证据按 `N/A: 理由 + 出处` 显式登记，不是无人可判 | P0 | `tools/lab/doc_chain.py` 的 `repo_policy_findings` |

### G2 任务证据可在盘（M-B）

| 验收点 | 验收目标 | 场景或条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G2-AC-01 | 仅 `/tmp` 证据判红 | 计划 ☑ 行证据写成 `/tmp/a.txt` | `C23 证据在场` finding | P0 | proposal §1.2 G2 |
| G2-AC-02 | 四类载体都放行 | 分别用仓内存在路径、`repo@rev:path`、可解析提交号、`N/A: 理由` | 各自 PASS，无 C23 finding | P0 | proposal §1.2 G2 |
| G2-AC-03 | git 缺失时失败关闭 | 证据只有提交号且环境无 git | 判 finding，不放行 | P1 | proposal §1.1 实证二 |
| G2-AC-04 | 本期不做行不误判 | `— 本期不做` 行无证据 | 不检查（只判 ☑ 已完成行） | P1 | proposal §1.3 |

### G3 决策门照到活文件（M-C）

| 验收点 | 验收目标 | 场景或条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G3-AC-01 | 豁免通道进契约 | 记录加 `disposition: deferred` | `validate.py schemas` 与 `artifacts` PASS；非法值被拒 | P0 | proposal §1.1 实证三 |
| G3-AC-02 | 拍板口八列化 | `docs/PENDING-DECISIONS.md` 表格 | 表头含八列且带 `agentflow 决策记录` 标记，`decision_gate` PASS 于该文件 | P0 | `AGENTS.md`「决策记录与台账」节（该节现位于 `AGENTS.md:110`，行号会随文档改动漂移，故按节名引用） |
| G3-AC-03 | 开放记录有归属 | 16 条 open 记录 | 逐条含 `disposition` 与追加的变更记录行，`C18 ownership` findings 为 0 | P0 | proposal §1.2 G3 |
| G3-AC-04 | 核验不过期 | 拍板口「现状核验」引用被改动路径，且核验与改动同日 | 原语义在数学上不可能同日转绿（第二轮评审 P1-1）；已授权把 C17 改为**日粒度**比较，同日不误伤、隔日仍抓，并由 `tests/test_lab_contracts.py` 的 `ReviewRoundTwoFixTests` 钉住 | P1 | `AGENTS.md`「决策记录与台账」节 |

### G4 规范文本自洽（M-D）

| 验收点 | 验收目标 | 场景或条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G4-AC-01 | 缺陷清单逐条闭合 | `spec/be/backend.md` §7 的 D-01 至 D-08 | 每条在计划行有落点与证据，复跑命令不再命中原文 | P1 | proposal §1.2 G4 |
| G4-AC-02 | 双源收口为指针 | 工作链表与表达纪律的定义处 | 全仓各只剩一处定义，另一处为指针句；`validate.py docs` PASS | P1 | proposal §1.2 G4 |
| G4-AC-03 | 门项计数不手写 | `AGENTS.md`、`README.md` | 不再出现门项数字字面量，改以 `--list` 自报；`validate.py docs` PASS | P2 | proposal §1.2 G4 |

### G5 发布可核（M-E、M-F）

| 验收点 | 验收目标 | 场景或条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G5-AC-01 | 门基线与变异报告在盘 | 副本跑完落 `testing/agentflows-gate-evidence/` | 报告文件存在且被计划证据列引用 | P0 | proposal §1.2 G5 |
| G5-AC-02 | 独立评审留证 | 门变更由只读评审者评审 | `reviews/` 下评审记录 `decision: approved`，episode 含轮次 | P0 | 硬边界 1 |
| G5-AC-03 | 版本与生成树一致；安装面差异如实登记 | 五份 manifest 同步、`packaging/build_runtime.py` 重建 | `validate.py manifests` PASS 且逐字留档；`validate.py installed` 的 FAIL 必须**写进待验收面并标注为未验证**，不写进本批的通过项 | P0 | proposal §1.2 G5（重装属范围外） |

## 5. 验收点与用例覆盖映射

| 验收点 | 关联用例（见 `design/qa/testing.md` §2） | 状态 |
| --- | --- | --- |
| G1-AC-01、G1-AC-02、G1-AC-03 | TC-TRACE-01、TC-TRACE-02、TC-TRACE-03 | ☑ 已覆盖（`tools/lab/doc_chain.py --self-test` 用例 87/88/89，2026-10-23 实跑 106/106） |
| G1-AC-04、G1-AC-05 | TC-TRACE-04、TC-TRACE-05 | ☑ 已覆盖（用例 92 与 97 钉住「未打标不误伤」；`doc_chain.py --repo .` → `PASS decision-gate`；`docs/features/feature-2026-09-19-产品线完善` 目录模式 PASS） |
| G2-AC-01、G2-AC-02 | TC-EVID-01、TC-EVID-02 | ☑ 已覆盖（用例 93/94 + `tests/test_lab_contracts.py` 的 `test_commit_sha_counts_only_when_git_can_resolve_it`） |
| G2-AC-03、G2-AC-04 | TC-EVID-03、TC-EVID-04 | ☑ 已覆盖（无 git 时提交号判不可核；用例 95 与 `test_rows_that_are_not_done_carry_no_evidence_duty`） |
| G3-AC-01 至 G3-AC-04 | TC-LEDS-01、TC-LEDS-02 | ☑ 已覆盖（`examples/invalid/bug-record-disposition-unknown.md` 被拒、`examples/issues/ISS-2026-10-23-开放记录显式延后归属.md` 通过；拍板口八列化后 `decision_gate` 对其零 finding） |
| G4-AC-01 至 G4-AC-03 | TC-TEXT-01 | ☑ 已覆盖（八条缺陷逐项闭合，证据见 `plan/PLAN-TRACE-001.md` T09 行；`validate.py docs` PASS） |
| G5-AC-01 至 G5-AC-03 | TC-REL-01、TC-REL-02 | ◐ 进行中（TC-REL-01 报告落盘与 TC-REL-02 版本/快照比对在 T10、T12 收口） |

## 6. 发布要求与结论

| 判断项 | 通过条件 | 未满足时 |
| --- | --- | --- |
| 核心能力与主链路 | G1、G2、G3 的 P0 验收点全部通过 | 阻塞发布 |
| 边界与异常 | 未打标批次不误伤（G1-AC-04）、git 缺失失败关闭（G2-AC-03） | 阻塞发布 |
| 遗留风险 | 领域模板缺口与 `report` 输出列（GAP-03）如实登记，不在本批关闭 | 写入待办与待拍板清单 |

**结论**：G1 至 G4 的验收点已逐项以命令原始输出闭合（状态列与 `plan/PLAN-TRACE-001.md` 看板同步回写）；G5 的发布侧三项待 T10/T12。独立评审（需求评审门与技术方案评审门）尚未勾选——本文件的「成文并通过机器检查」不等于「已过评审门」。
