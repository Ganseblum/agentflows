---
bug_id: BUG-20260917-03
title: 凭会话记忆回答「现在有什么高优任务」——状态类结论未经仓库事实校准
status: verified
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: infinite-canvas
files:
  - skills/agentflow/SKILL.md
  - skills/agentflow/references/contracts.md
affected_slices:
  - intake
  - status-reporting
  - evidence-discipline
recorded_at: 2026-09-17T00:00:00Z
updated_at: 2026-09-17T16:00:00Z
source_revision: 8665ca3
agentflow_version: 0.4.0
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: 指定检查已运行且符合预期（pass 口径：指定检查运行且输出符合预期；行为服从无自动化回归面）：`python3 tools/lab/validate.py all` 退出码 0（C0）；`skills/agentflow/SKILL.md:81` 状态校准条款原文命中（C7）；`.zcode/skills/agentflow/` 活路径与源树 SKILL.md、contracts.md 两两 diff 无差异，退出码 0（C6）；已知残余——`python3 tools/lab/validate.py installed` FAIL(3)（差异文件 agents/bug-recorder.md、agents/plan-architect.md、skills/agentflow/SKILL.md，系本日更晚的 P0 措辞批次所致，0.4.2 规则文本在已安装快照内 grep 各命中 1，非 0.4.2 规则缺失，刷新 marketplace 并重装后消除）；失效检测器为再犯加 recurrence/improve 环。
fix_revision: agentflow 0.4.2
---

## 现象

用户询问「现在有什么高优任务」时，执行者凭会话记忆给出待办清单，把已经完成的项列为待办：
`我的规划/` 第三 / 四 / 五期实现、WebDAV 文档清理、`vercel.json` 删除。实际上该分支在那之后
已推进 10 个提交并推送（自 `6130cd1` 起），上述多项已经完成。执行者事后核查 `git log --all`
时才发现自己的状态认知已经过期，并向用户更正。

问题不在于答案「不够新」，而在于执行者给出的是状态类结论，却没有任何一步去读仓库的真实历史：
如果用户不追问，这份过期清单就会被当作当前任务面继续使用。

## 根因

`skills/agentflow/SKILL.md:78` 的 Intake 步骤要求检查仓库指令、当前 diff、相关架构与测试，
但：

- 没有要求「给出仓库状态类结论之前先 `git fetch` 并读取真实历史」——Intake 的证据要求停在
  「开始工作时读一次」，没有覆盖「对外输出状态判断」这一动作；
- 没有要求状态类结论附带可复核的命令与输出——会话记忆因此被直接当作仓库事实使用。

同一份 `skills/agentflow/references/contracts.md` 的 Hard boundaries 已经为相邻的断言立了证据
要求：工具 / 框架行为断言必须有最小实验证据（exit code 与逐字输出），「不存在」类断言必须直接
读权威 sink。仓库状态断言是同一族、更常用的断言，却没有对应条款；当另一会话继续推进分支时，
记忆里的待办清单立即过期，而回答过程中没有任何环节会暴露这一点。归因 `workflow_policy`。

## 修复

已落地于 agentflow 0.4.2（用户授权的规则补丁）：

- `skills/agentflow/SKILL.md:81`（Intake 步骤）补状态校准：仓库状态类结论（什么已完成、接下来
  是什么）必须先用 `git fetch` 加 `log` / `status` 对照仓库实况再给出，并携带证据命令；会话
  记忆不是仓库事实——另一写入者一推送，它就过期。

规则文本变更，无自动化回归面可跑（与 `regression_status: not-run` 一致）；转 `verified` 前需
独立评审人指定能证明约束生效的检查。

## 变更记录

- 2026-09-17 00:00 · 建档（open）· 依据用户询问与事后 `git log --all` 核查暴露的状态认知过期。
- 2026-09-17 · 修复落地 · 规则改动已实施（SKILL/contracts 三处补丁，版本 0.4.2）；待独立评审（规则文本变更，无自动化检测面可跑；validate.py all 仅验证记录结构完整。转 verified 前需评审人指定能证明约束生效的检查。）
- 2026-09-17 · 记录更正 · 「## 修复」段由「待落地」改写为已落地事实（0.4.2 已实施），与 frontmatter 的 fixed-pending-review / fix_revision 对齐。
- 2026-09-17 · 独立评审通过 · agentflow:reviewer 批量评审指定检查（C0–C8），supervisor 执行并回传原始输出，转 verified。
- 2026-09-17 · 措辞澄清（评审发现）· 0.4.2 批次三条记录合计命名落点为 4 处（contracts.md:13 + SKILL.md:81/:84/:131），既有「三处补丁」行按建档时口径保留不改写。

## 审查

评审人 `agentflow:reviewer` 于 2026-09-17 批量评审本批 8 条 `fixed-pending-review` 记录。
本条指定检查 C0（全量确定性检查）、C7（0.4.2 条款原文命中）与 C6（活路径与源树一致性），
由 supervisor 执行并回传原始输出；结论 `approved`，本记录转 `verified`。规则文本变更没有
自动化行为回归面：`regression_status` 按评审口径由 `not-run` 改为 `pass`，pass 的含义是
指定检查已运行且输出符合预期，不是行为服从的自动化证明——失效检测器为再犯加
recurrence/improve 环。

决定性证据（supervisor 回传，逐字输出）：

C0 —— `python3 tools/lab/validate.py all`：

```
8/8 PASS, exit 0
```

C7 —— `skills/agentflow/SKILL.md:81`（Intake 步骤，0.4.2 扩写段原文命中）：

```
When you report repository **status** — what is done, what is next, what is high priority — calibrate against the repository's real history first (`git fetch` plus `log`/`status`), never against session memory, and carry the evidence command with the conclusion. A status claim is a repository-fact claim: session memory goes stale the moment another writer pushes, and nothing in the answer would reveal it.
```

C6 —— `.zcode/skills/agentflow/` 活路径与源树两两 diff（`diff .zcode/skills/agentflow/SKILL.md skills/agentflow/SKILL.md` 与 `diff .zcode/skills/agentflow/references/contracts.md skills/agentflow/references/contracts.md`）均无输出，退出码 0。

C5 残余 —— `python3 tools/lab/validate.py installed` FAIL(3)，差异文件为
`agents/bug-recorder.md`、`agents/plan-architect.md`、`skills/agentflow/SKILL.md`，系本日
更晚的 P0 措辞批次（绑定清单与「交 supervisor 校验」措辞）导致，非 0.4.2 规则缺失。
补充证据确认 0.4.2 规则文本在已安装快照（host 实际加载的 plugin cache）内存在：

```
$ grep -c "per-instance authorization" /Users/lihanghang1/.zcode/cli/plugins/cache/agentflow-local/agentflow/0.6.0/skills/agentflow/references/contracts.md
1
$ grep -c "parallel writers get separate branches or worktrees" /Users/lihanghang1/.zcode/cli/plugins/cache/agentflow-local/agentflow/0.6.0/skills/agentflow/SKILL.md
1
```

刷新 marketplace 并重装后该残余消除；作为已知残余风险如实记录在案。
