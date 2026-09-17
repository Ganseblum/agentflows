---
bug_id: BUG-20260917-01
title: 推送被拒后未经授权自行 rebase 集成远端提交——集成操作不在授权边界清单内
status: open
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
updated_at: 2026-09-17T00:00:00Z
source_revision: 8665ca3
agentflow_version: 0.4.0
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

待落地（属 improve 环范围，规则改动**尚未实施**，本记录因此保持 `open`，不写 `fix_revision`）：

- `skills/agentflow/references/contracts.md`：Hard boundaries 第 3 条扩写，覆盖合并 / 变基 /
  跨分支摘取提交（merge / rebase / cherry-pick）——凡集成他人改动或改写历史的操作都需要用户
  当次授权。
- `skills/agentflow/SKILL.md`：「Preserve control and traceability」增加一条：推送被拒或需要集成
  远端改动时，先只读汇报重叠面，由用户选择集成方式，不得自行合成。

对照证据（已获用户授权、已在 fork 侧落地同义约束），原文 `infinite-canvas@a14cfa1:AGENTS.md`：

> **合并与集成必须取得明确授权，不许自动做。** 未经用户明确要求，不得执行 `git merge`、
> `git pull`（非 `--rebase` 的合并式拉取）、把 `main` / `upstream/main` 或任何分支合并进当前分支、
> 跨分支 `git cherry-pick`，也不得为了「顺便同步一下」自行集成其它分支。需要集成时先说明
> 「要合并哪个分支、目标分支是什么、为什么必须合并、预期影响」，得到当次确认后再执行。

> **推送被拒需要先集成远程改动时，同样先问。** 先只做只读的 `git fetch` / `git log` / `git diff`
> 把「远程多了哪些提交、改了哪些文件、与本地的重叠在哪」讲清楚，再让用户选择 `merge` 还是 `rebase`；
> 不要自行选一种方式直接把远程改动合成进来。

## 变更记录

- 2026-09-17 00:00 · 建档（open）· 依据用户纠正、推送被拒与 rebase 集成的事实链条，以及 fork 侧
  已落地的同义约束；Agentflow 侧条款改动尚未实施。
