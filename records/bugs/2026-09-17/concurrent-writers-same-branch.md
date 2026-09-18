---
bug_id: BUG-20260917-02
title: 同一分支被两个执行者并发写入——写入隔离约束没有延伸到 git 层
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
  - parallel-writes
  - branch-isolation
  - delegation-briefs
recorded_at: 2026-09-17T00:00:00Z
updated_at: 2026-09-17T16:00:00Z
source_revision: 8665ca3
agentflow_version: 0.4.0
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: 指定检查已运行且符合预期（pass 口径：指定检查运行且输出符合预期；行为服从无自动化回归面）：`python3 tools/lab/validate.py all` 退出码 0（C0）；`skills/agentflow/SKILL.md:84` git 层写入隔离条款原文命中（C7）；`.zcode/skills/agentflow/` 活路径与源树 SKILL.md、contracts.md 两两 diff 无差异，退出码 0（C6）；已知残余——`python3 tools/lab/validate.py installed` FAIL(3)（差异文件 agents/bug-recorder.md、agents/plan-architect.md、skills/agentflow/SKILL.md，系本日更晚的 P0 措辞批次所致，0.4.2 规则文本在已安装快照内 grep 各命中 1，非 0.4.2 规则缺失，刷新 marketplace 并重装后消除）；失效检测器为再犯加 recurrence/improve 环。
fix_revision: agentflow 0.4.2
---

## 现象

同一分支被两个执行者同时写入，写入在 git 层相撞：

- fork 仓库 `infinite-canvas` 的分支 `codex/account-backend-plan` 上，另一会话新增并推送了
  10 个提交（含 `6130cd1`、`5a48913`、`32057f0`、`50da5d0`、`eb30e48`、`caf63bf` 等）；本会话
  在此期间仍在本地累积自己的提交，双方的推送在远端相撞，触发「推送被拒 → 要求集成」（见同目录
  `records/bugs/2026-09-17/unauthorized-git-integration-after-push-rejected.md`）。
- 同一批文件被两侧并发修改并在集成时产生冲突：`docs/content/docs/progress/todo.mdx`、
  `我的规划/Fork同步与部署约定.md`。
- 同一模式在 agentflow 仓库本身复现：本会话需要修改 `skills/agentflow/references/contracts.md`
  时，发现该文件正被另一个会话修改（工作区未提交），无法安全编辑，只能停下并上报。

## 根因

Agentflow 已经规定「并行写入必须落在互不重叠的文件上」（`skills/agentflow/SKILL.md:81` 的委派
步骤，以及 `skills/agentflow/references/contracts.md` 中 disjoint file scopes 的段落），但这
条约束止步于文件路径，没有延伸到 git 层：

- 没有要求并行写入落在独立分支或独立工作区——提交、rebase、push 是共享的可变状态，两个
  执行者各自看来都只在写自己的文件范围，却在同一分支上叠加提交；
- 没有规定「同一分支同一时刻只允许一个执行者写入」；
- 没有跨会话 / 跨执行者的分支占用声明与交接规则——发现目标文件已被另一写入者占用时（本仓的
  `skills/agentflow/references/contracts.md` 就是实例），没有规定默认动作（停止并上报、等待，
  还是另建分支）。

这条文件级约束的隐含前提是「单个 supervisor 统一分配 write_scope」；一旦两个会话共享同一仓库与
分支，前提失效，而规则没有给出替代机制，也没有任何环节要求写入者在动手前声明自己占用了哪个
分支。归因 `workflow_policy`。

## 修复

已落地于 agentflow 0.4.2（用户授权的规则补丁）：

- `skills/agentflow/SKILL.md:84`（委派步骤）补 git 层写入隔离，把原本止步于文件路径的
  「互不重叠的文件」约束延伸到 git 层：互不重叠的文件不足以隔离提交 / rebase / 推送——提交与
  推送是共享可变状态；并行写入者各用独立分支或 worktree，同一分支同一时刻只有一个写入者。
- 写入者发现目标已被占用（其他会话的未提交编辑、分支上的新提交）时停止并上报，而不是交错写入。

规则文本变更，无自动化回归面可跑（与 `regression_status: not-run` 一致）；转 `verified` 前需
独立评审人指定能证明约束生效的检查。

## 变更记录

- 2026-09-17 00:00 · 建档（open）· 依据双写提交序列、冲突文件清单，以及本仓
  `skills/agentflow/references/contracts.md` 被并发占用的现状。
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

C7 —— `skills/agentflow/SKILL.md:84`（委派步骤，0.4.2 扩写段原文命中）：

```
**Disjoint files are not enough once two writers share a repository**: commits, rebases, and pushes are shared mutable state, so parallel writers get separate branches or worktrees, one writer holds a branch at a time, and a writer that finds its target file or branch already occupied by another writer (uncommitted edits from another session, a branch with new commits) stops and reports instead of interleaving.
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
