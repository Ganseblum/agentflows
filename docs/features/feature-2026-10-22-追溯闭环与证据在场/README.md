# feature-2026-10-22-追溯闭环与证据在场 — 让新门第一次照到活文件

> 段落映射：逐段声明落点（下表）。落点非空且非「—」的段落可缺目录；其余段落齐全。
> 轻量降档：未启用。
> 落点形态：普通业务仓（`docs/features/`），本仓即为该形态。
> 本批次启用两项标记（声明行形态，2026-10-29 起由防摘除断言核验）：
>
> agentflow 目标承接
>
> agentflow 决策归属
>
> 目标承接表进入 C22 检查；开放记录归属进入 C18 检查。结构模板标记未启用：本批无前端轨，C11 的 design/fe 固定章节不适用。

## 元信息

- 需求原文/页面链接：2026-10-22 用户原话，逐字保留于 `proposal/proposal.md` 文档信息节；主实施仓：
  本仓（agentflows）；相关系统/仓库：无；UI 轨：未启用；埋点：N/A（本批不产出用户可见行为，
  无事件新增或变更）；最后更新时间：2026-10-23
- 升格来源：无。由 2026-10-22 对本仓规范面与记录面的三轮质量走查直接立项；走查发现逐条登记在
  `spec/qa/acceptance.md` §0 的缺口台账。
- 状态：链已成文并执行中。唯一权威状态源是 `plan/PLAN-TRACE-001.md` 的任务看板；本 README 只作批次入口索引。

## 段落映射

| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 需求提案（含范围决策表与待冻结问题台账 Q-01 至 Q-03） |
| spec | `spec/be/`、`spec/qa/` | 工程需求（M-A 至 M-F 模块清单与字段口径）与验收标准（判据预先写定）；本批无前端范围，不建 spec/fe |
| design | `design/be/`、`design/qa/` | 工具链技术方案（C22/C23 判据、异常矩阵、影响面与回滚）与验证方案（变异语料与用例库）；不建 design/fe |
| plan | `plan/PLAN-TRACE-001.md` | 执行计划（任务看板 + 状态与证据回写） |
| testing | `testing/agentflows-gate-evidence/` | 门基线输出与整门变异报告的落盘处（本批补上的证据载体） |
| reviews | `reviews/` | 独立评审记录落点（门变更须经独立评审） |

## 推进进度

> 规则：完成即将行首 ☐ 改 ☑；不适用改 ☑ 并写 (N/A: 原因)；评审类门禁只能由独立评审勾选。

### 1. Proposal [PM]
☑ 主稿已成文（`proposal/proposal.md`），目标 G1–G5 与范围决策表齐备

### 2. Spec [按角色]
☑ spec/be 已成文（`spec/be/backend.md`），含 Proposal 反审 checklist，阻塞项已关闭
☑ spec/qa 已成文（`spec/qa/acceptance.md`），验收点与判据预先写定

### 3. 需求评审 [门禁]
☐ 待独立评审勾选（评审记录落 `reviews/`）

### 4. Design [按角色]
☑ design/be 已成文（`design/be/backend.md`）
☑ design/qa 已成文（`design/qa/testing.md`）

### 5. 技术方案评审 [门禁]
☐ 待独立评审勾选；前置为需求评审门

### 6. Plan [执行契约]
☑ 已成文并开始执行（`plan/PLAN-TRACE-001.md`）

### 7. 实施与验证 / 8. 收口
◐ 实施进行中；收口待独立评审、episode 落盘与版本发布记录

## 目标承接表

> 本表是 C22 的载体：每个目标必须同时给出 spec 承接（模块与验收点）与 plan 任务行，状态列与
> 计划看板一致。表由 `python3 tools/lab/doc_chain.py docs/features/feature-2026-10-22-追溯闭环与证据在场`
> 机器校验（2026-10-22 门变更，经用户授权）。

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 目标承接可机判 | `proposal/proposal.md` §1.2 | M-A（`spec/be/backend.md` §5）与 G1-AC-01 至 G1-AC-05（`spec/qa/acceptance.md` §4） | T02、T03、T05 | ☑ 已完成 |
| G2 任务证据可在盘 | `proposal/proposal.md` §1.2 | M-B（`spec/be/backend.md` §5）与 G2-AC-01 至 G2-AC-04（`spec/qa/acceptance.md` §4） | T01、T04、T05、T10 | ☑ 已完成 |
| G3 决策门照到活文件 | `proposal/proposal.md` §1.2 | M-C（`spec/be/backend.md` §5）与 G3-AC-01 至 G3-AC-04（`spec/qa/acceptance.md` §4） | T06、T07、T08 | ☑ 已完成 |
| G4 规范文本自洽 | `proposal/proposal.md` §1.2 | M-D（`spec/be/backend.md` §5）与 G4-AC-01 至 G4-AC-03（`spec/qa/acceptance.md` §4） | T09 | ☑ 已完成 |
| G5 发布可核 | `proposal/proposal.md` §1.2 | M-E 证据落盘与 M-F 发布（`spec/be/backend.md` §5）与 G5-AC-01 至 G5-AC-03（`spec/qa/acceptance.md` §4） | T10、T11、T12 | ☑ 已完成 |

## 开放记录承接（C18）

| 记录编号 | 任务号 | 说明 |
| --- | --- | --- |
| ISS-2026-10-23-变异存活项长期无逐项处置 | — | 本批实跑整门变异时确认的存量疑点（6 个存活项无逐项归宿）。修复要把存活变成有归宿的语料或豁免，属下一批范围；此处按 C18 显式承接并声明本批不做 |
| — | T07 | 本批不承接外部项目记录。`docs/issues/` 下 16 条 `status: open` 记录全部是 2026-09-19 对另一项目方案文档的评审发现（`provenance: external`），归属该项目；本批把 C18 要求的显式豁免通道（`disposition` 字段）补进记录契约后，它们逐条登记为 `deferred`，不再靠「没打标所以不红」悬空 |

## 模块进度总览

| 模块 | 负责面 | 状态 | 做到哪 | 还差什么 |
| --- | --- | --- | --- | --- |
| M-A C22 目标承接闭环 | 后端 | ☑ | `tools/lab/docchain/checks.py` 的 `goal_traceability_findings()` 落地（经薄启动器 `tools/lab/doc_chain.py` 调用），自测夹具 86–92/97，仓扫与目录模式共用实现 | 无 |
| M-B C23 证据在场 | 后端 | ☑ | `evidence_presence_findings()` 与四类载体识别落地，夹具 93–96，plan 扫描改递归 | 无 |
| M-C 决策门落地 | 后端 | ☑ | `disposition` 进契约与正反例；16 条 open 记录登记 deferred；拍板口八列化并打标，C16/C17/C18 首次照到活文件 | 无 |
| M-D 文本与双源收口 | 文档 | ☑ | 八条缺陷逐条闭合（含实现中新发现的三条，立为 `docs/issues/ISS-2026-10-23-元信息同行声明默认落点基准被误判.md` 等） | 无 |
| M-E 证据落盘 | 测试 | ☑ | 门基线已落 `testing/agentflows-gate-evidence/evidence/baseline-96e0383.md`；整门变异第一轮 49 杀死/6 存活/1 无效 | 无（存活项处置已转 `docs/issues/ISS-2026-10-23-变异存活项长期无逐项处置.md`） |
| M-F 发布 | 后端 | ◐ | 发布动作已随 `861b6ef` 完成：五份 manifest、CHANGELOG 0.13.0 条目、episode、`index.md` 与 `docs/releases/` 回写 | T11 第三轮独立评审；`validate.py all` 全绿原始输出留档 |

## 当前步骤

实现与自检已闭（T01–T10）：两条新门落地并有判别夹具、契约与活文件采用面都已打通、文本缺陷逐条收口、门基线与变异报告落盘。
两项新门（C22 目标承接、C23 证据在场）的实现与夹具排在 T02 至 T05，决策门落地排在 T06 至 T08，
余下 T11（第三轮独立评审）与 T12（补 `validate.py all` 全绿原始输出留档）；发布动作已于 `861b6ef` 完成。权威进度以 `plan/PLAN-TRACE-001.md` 的任务看板为准。

## 当前实施仓与分支基线

实施直接在 `main` 执行（无独立分支）；开工基线为 `96e0383`。按仓库规则：未提交、未推送、未发布，
除非用户当次指示。门变更授权：用户的逐字指令是「按照你说的提一个feature，然后开始修复完善并发版升级」；具体范围（C22、C23、
`disposition`、门清单同步、本地 bump）由 2026-10-22 会话内问答选定，选项说明文本由作者撰写。终审由独立评审与用户保留。
