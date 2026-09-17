---
bug_id: BUG-20260917-03
title: 凭会话记忆回答「现在有什么高优任务」——状态类结论未经仓库事实校准
status: open
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
updated_at: 2026-09-17T00:00:00Z
source_revision: 8665ca3
agentflow_version: 0.4.0
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

待落地（属 improve 环范围，规则改动**尚未实施**，本记录保持 `open`，不写 `fix_revision`）：

- `skills/agentflow/SKILL.md` 的 Intake（或 supervisor 职责段落）补一条：仓库状态类结论必须先
  `git fetch` 并读 `log` / `status` 校准，结论中给出证据命令与输出；不得以会话记忆代替仓库事实。

## 变更记录

- 2026-09-17 00:00 · 建档（open）· 依据用户询问与事后 `git log --all` 核查暴露的状态认知过期。
