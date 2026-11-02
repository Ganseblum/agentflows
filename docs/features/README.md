# features — 批次与实施计划

成批 / 跨层工作以批次目录组织（形态对齐 youc-workflow-ai 与 aiwork-workflow-ai）：每个批次
一个目录，命名 `feature-<YYYY-MM-DD>-<主题>/`，按文档链五段落位。

```text
docs/features/
  feature-<YYYY-MM-DD>-<主题>/
    README.md      # 批次入口：背景、范围、段落映射、推进进度
    proposal/      # 提案：为什么做、做什么
    spec/          # 规格：验收口径与契约
    design/        # 方案：怎么做（异常矩阵、时序图、状态图随需要）
    plan/          # 计划：任务表与执行契约
    reviews/       # 评审落点（可选）
    testing/       # 测试计划与运行记录（可选）
```

段落可为空但必须在批次 README 的「段落映射」表里写明落点。

**段落映射豁免（统一规则）**：批次 README 的段落映射表中，某段落落点写了非空且不为「—」的位置时，
该段目录可缺失（内容由该落点承载，例如产品链的 `docs/product/`，不重复造册）；否则该段目录必须存在且含 `.md`。

## 在途批次

**当前无在途批次。** 2026-10-13 至 2026-10-29 的 10 个批次已全部完成（看板逐任务 ☑ 或「本期不做」，
入口门与独立评审均已闭环），按本文件「纪律」节「完成批次不长期留存」的既有口径，随 2026-11-02
瘦身批删除目录：结论权威在 [`../../CHANGELOG.md`](../../CHANGELOG.md) 的对应版本节与
[`../../index.md`](../../index.md) 的批次索引节；逐批原文（提案 / spec / 设计 / 计划 / 评审 /
测试证据）以 git 历史为归档，按 `agentflows@c8ed0b2:docs/features/<批次目录>` 取回。

这里不再留第二份逐批状态表——表若还写着状态结论，就和已删除的计划看板打架，长出第二个真源。

## 纪律

- 立项当天建表：批次 README 打 `agentflow 目标承接` 标记时必须同时写目标承接表（列：目标 /
  proposal 出处 / spec 承接 / plan 任务 / 状态），否则 C22 判「标记启用但缺表」。承接表的状态列
  随计划看板回写，回写口径见 `skills/agentflow/references/document-chain.md` 的门 8。
- **C22 打标只对新批次生效**（2026-10-29 拍板 B）：立项动作清单里加入「打 `agentflow 目标承接`
  标记并建承接表」一项；存量批次不回改、不补打标，其目标失踪风险按历史不回改原则保留。C23
  证据在场对全部批次生效，不受此条影响。
- 回写不止计划两列：计划任务行的状态与证据两列之外，`spec/qa/acceptance.md` 的验收点状态列同样
  要在验收发生时更新——「计划已闭而验收表还写待覆盖」是假记录的一种（2026-10-22 走查实证）。
- 立项与收尾同日更新四处索引：本文件「在途批次」表、`index.md` 的批次索引节、
  `docs/evaluations/README.md` 的收存清单（若产出评测/审核报告）、
  `docs/releases/pending-test.md`（若有未验收的发布动作）。漏一处即「自述与实现面不同步」——
  2026-10-28 批实测漏了这三处索引外加一个脚本消费点，已立为
  `docs/issues/ISS-2026-10-28-整改批自述与实现面不同步.md`。
- 改动一个机制时先枚举它的**全部消费点**再动手：2026-10-28 批把 `.venv` 解释器探测只加进了
  `pre-push.sh`，另外三个同样消费 lint 的脚本（`publish.sh`、`upgrade-*.sh`）被漏下，
  正是本仓反复出现的「同一规则多处维护、改一处漏三处」形态。
- 目录由「首次接入 / 批次立项」创建；对实际目录跑
  `python3 tools/lab/doc_chain.py <feature-dir>` 接受文档链，全绿才算链完成。该命令是独立命令：
  结构检查 C1–C11，文本形态检查 C12–C14。同一 linter 另由 `python3 tools/lab/validate.py doc_chain_live`
  以 `--file` 模式扫描 `docs/product/`、`docs/features/` 下全部 `.md`（已接入 `validate.py all`），任一发现即门红。
- 批次内的 `plan/<plan_id>.md` 受计划契约校验（文件名 = `plan_id`、固定状态枚举、任务表
  依赖图无环——完整断言见下节）；其他段落由文档链 linter 管。
- 完成批次不长期留存：结论写进 `CHANGELOG.md` 与 episode 后随瘦身批删除，git 历史
  即归档（2026-10-12 起本仓不保留归档桶）。
- 开放事项：缺陷走 `docs/issues/`，跨批次待拍板走 `docs/PENDING-DECISIONS.md`。

## 计划形态（原 `docs/plans/README.md`，随 2026-10-12 归位并入）

`plan-architect` 仅在获得明确输出路径时才写入版本化执行计划。计划是
**Markdown 混合体**——frontmatter 是机器校验的信封，正文是给人读的叙述与进展看板。它是
执行契约，不是改动代码的授权。`status` 记录**审批状态**，不是执行进度；已执行但未走正式
approval 门的路线图可保留 `proposed`，执行事实以任务表为准。

```text
---
plan_id / plan_version / status (draft|proposed|approved|superseded)
objective / recorded_at / updated_at   (+ superseded_by when superseded)
---

## 进展概览            # 一行进度 + 三视角概览表 + 我们在哪/下一步/阻塞
## 分支策略            # 工作分支与依据（文档链 C9 要求计划声明分支策略）
## 任务清单            # T01… 任务表：优先级/代码落点/依赖/状态/证据回写 + ### 未决项
## 接口与共享机制       # 契约表 + 异常矩阵 + 发布顺序×回滚点 + 评审门
## 验证命令            # 验收命令与预期
```

机器断言：文件名 = `plan_id`；`status` 固定枚举；`superseded` 要求 `superseded_by`；任务 ID
唯一且依赖图无环；任务状态固定枚举 `☐ 未开始 / ◐ 进行中 / ☑ 已完成 / ⚠ 阻塞 / — 本期不做`
（裸字形 ☐/◐/☑/⚠/— 与全称均可，裸「—」按本期不做计，自由文本不合法）；
`### 未决项` 中阻塞行未关闭则阻止 `status: approved`；三个必需小节存在。

进展回写纪律：任务完成后**只**编辑它的 状态 与 证据回写 两列——最小 diff；绝不重写已完成
的任务行，绝不用自由文本状态散文替换表格。会话死亡恢复协议读取这张表，从工作区重新推导
每个任务的状态。

## 升格与登记

- **issue → feature 升格**：中/大问题经用户确认后升格为批次，在 `docs/issues/README.md` 的
  升级通道处置，并在**两处**登记：原 issue 记录的状态节写「已升格并入 `<批次目录>`」，
  批次 README 的「元信息」节写「升格来源：ISS-YYYY-MM-DD-slug（原由）」。升格即留痕，不靠记忆。
- **批次完成**：结论入 `CHANGELOG.md` 与 episode，批次目录删除（git 历史即归档）。

证据列的形态要求（C23，2026-10-23 起）：☑ 已完成的行必须留下可复核载体；**四类载体的定义单点在
`skills/agentflow/references/document-chain.md` 的门 8**，本文件只引用不复述——复述就会长出第二个真源。
