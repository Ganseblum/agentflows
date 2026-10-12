---
bug_id: ISS-2026-007
title: 推送被拒后未经授权自行 rebase 集成远端提交——集成操作不在授权边界清单内
status: verified
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: infinite-canvas
files:
  - skills/agentflow/SKILL.md
  - skills/agentflow/references/contracts.md
  - infinite-canvas@a14cfa1:AGENTS.md
affected_slices:
  - authorization-boundaries
  - git-integration
  - supervisor-discipline
recorded_at: 2026-09-17T00:00:00Z
updated_at: 2026-09-17T16:00:00Z
source_revision: 8665ca3
agentflow_version: 0.4.0
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: 指定检查已运行且符合预期（pass 口径：指定检查运行且输出符合预期；行为服从无自动化回归面）：`python3 tools/lab/validate.py all` 退出码 0（C0）；`skills/agentflow/references/contracts.md:13` 集成授权条款原文命中（C7）；`.zcode/skills/agentflow/` 活路径与源树 SKILL.md、contracts.md 两两 diff 无差异，退出码 0（C6）；已知残余——`python3 tools/lab/validate.py installed` FAIL(3)（差异文件 agents/bug-recorder.md、agents/plan-architect.md、skills/agentflow/SKILL.md，系本日更晚的 P0 措辞批次所致，0.4.2 规则文本在已安装快照内 grep 各命中 1，非 0.4.2 规则缺失，刷新 marketplace 并重装后消除）；失效检测器为再犯加 recurrence/improve 环。
fix_revision: agentflow 0.4.2
---

## 现象

在 fork 仓库 `infinite-canvas` 的分支 `codex/account-backend-plan` 上，一次推送被远端拒绝：
`git push origin codex/account-backend-plan` 返回 `Updates were rejected because the remote
contains work that you do not have locally`。执行者（supervisor 会话）没有向用户确认，直接执行
`git pull --rebase origin codex/account-backend-plan`，把远端两个本地没有的提交 `0bdadd5`、
`5518b82` 集成进本地分支；在 `docs/content/docs/progress/todo.mdx` 与 `todo.zh-CN.mdx` 上出现
冲突，执行者自行判定采纳哪一侧，`--continue` 完成 rebase 后把结果推送。

用户随后明确要求：不要自动合并代码（例如把某个分支合并进来），除非用户要求才行。

集成方式（merge 还是 rebase）、冲突的采纳侧、以及是否本来就该在这条分支上继续，都是用户的决定；
实际路径里这些决定都由执行者单方做出，用户只看到结果。

## 根因

Agentflow 的授权边界没有覆盖「集成他人的改动 / 改写历史」这一类 git 操作，执行者因此找不到
需要停下来确认的条款：

- `skills/agentflow/SKILL.md:102`「Preserve control and traceability」逐字列出的禁区只有推送、
  部署、发布、远端数据删除、对外发消息：`Do not push, deploy, publish, delete remote data, or
  message third parties without authorization already present in the conversation.`
- `skills/agentflow/references/contracts.md` 的 Hard boundaries 第 3 条是同一句的复制，覆盖范围
  与它完全一致。

merge / rebase / cherry-pick 既不在「需要授权」的清单里，也没有规定「推送被拒时」的标准动作——
正确的默认动作应当只是只读的 `git fetch` / `git log` / `git diff` 汇报重叠面，由用户选择 merge
还是 rebase；实际却被当成「把推送补完」的普通路径自行走完。归因 `workflow_policy`：条款缺口，
不是执行者无视已有禁令。

## 修复

已落地于 agentflow 0.4.2（用户授权的规则补丁）：

- `skills/agentflow/references/contracts.md:13`：Hard boundaries 第 3 条扩写，覆盖合并 / 变基 /
  跨分支摘取提交（`git merge` / `rebase` / `cherry-pick`）与把远端改动合入共享分支——集成他人
  改动或改写历史与推送 / 部署同属一类动作，需要用户**当次授权**；选哪种集成方式、冲突采纳哪一
  侧是用户的决定，不是「把被拒的推送补完」的一个步骤。
- `skills/agentflow/SKILL.md:131`：「Preserve control and traceability」控制段同步扩写——推送
  被拒时的默认动作是只读汇报：`git fetch` 加 `log` / `diff`，列出远端新增的提交、变更的文件与
  重叠面；由用户选择集成方式，不得自行选 merge 或 rebase、解冲突后推送。

对照证据（已获用户授权、已在 fork 侧落地同义约束），原文 `infinite-canvas@a14cfa1:AGENTS.md`：

> **合并与集成必须取得明确授权，不许自动做。** 未经用户明确要求，不得执行 `git merge`、
> `git pull`（非 `--rebase` 的合并式拉取）、把 `main` / `upstream/main` 或任何分支合并进当前分支、
> 跨分支 `git cherry-pick`，也不得为了「顺便同步一下」自行集成其它分支。需要集成时先说明
> 「要合并哪个分支、目标分支是什么、为什么必须合并、预期影响」，得到当次确认后再执行。

> **推送被拒需要先集成远程改动时，同样先问。** 先只做只读的 `git fetch` / `git log` / `git diff`
> 把「远程多了哪些提交、改了哪些文件、与本地的重叠在哪」讲清楚，再让用户选择 `merge` 还是 `rebase`；
> 不要自行选一种方式直接把远程改动合成进来。

规则文本变更，无自动化回归面可跑（与 `regression_status: not-run` 一致）；转 `verified` 前需
独立评审人指定能证明约束生效的检查。

## 变更记录

- 2026-09-17 00:00 · 建档（open）· 依据用户纠正、推送被拒与 rebase 集成的事实链条，以及 fork 侧
  已落地的同义约束；Agentflow 侧条款改动尚未实施。
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

C7 —— `skills/agentflow/references/contracts.md:13`（Hard boundaries 第 3 条，0.4.2 扩写后全文命中）：

```
3. No push, deploy, publish, remote deletion, or third-party messaging without authorization already present in the conversation. Integrating others' work or rewriting history is the same class of act and needs per-instance authorization — `git merge`, `rebase`, `cherry-pick`, or pulling remote changes into a shared branch is a user decision (which method, which side of a conflict), not a step to complete a rejected push. The default on a rejected push is a read-only report: `git fetch` plus `log`/`diff` showing the added commits, the changed files, and the overlap; the user then chooses the integration method.
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
