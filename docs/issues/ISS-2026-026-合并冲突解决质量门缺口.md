---
bug_id: ISS-2026-026
title: 多分支合并解冲突无质量门——只查冲突标记的自检漏掉相邻行重复，重复函数声明进入交付
status: verified
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: infinite-canvas
files:
  - skills/agentflow/SKILL.md
  - skills/agentflow/references/roles.md
  - skills/agentflow/references/contracts.md
  - infinite-canvas@53bff1e:AGENTS.md
  - infinite-canvas@7af6cf5:server/internal/config/config.go
affected_slices:
  - merge-integration
  - review-gate
  - skill-trigger-criteria
  - supervisor-discipline
class_id: merge-integration-quality-gate
occurrence: "1"
recorded_at: 2026-09-20T00:00:00Z
updated_at: 2026-09-20T06:00:00Z
source_revision: 5da90f2ec08111386045c3b26c5e8badce053f7b
agentflow_version: 0.8.1
regression_status: pass
reviewer: agentflow:evaluator
review_decision: approved
closure_criteria: S1 五条条款 grep 各计 1(branch integration and conflict resolution / branch merge with conflict resolution / 任务本身是分支合并/解冲突 / clearing conflict markers is not a check / iteration default, not an exemption);S2 步骤 10 行原序+硬边界 3/14 行号+skills/docs 面版本字面量零命中;S3 tracked 改动面 vs 5da90f2 = 四候选文件 + AGENTS.md(已归因并行 linter 段),untracked = 已申报外来集(document-chain.md、docs/product/、tools/lab/doc_chain.py)+ 本环自有记录,超出该枚举集即 FAIL;S4 validate.py all 9×PASS EXIT=0 与 isolation.py check-diff blocked:[] EXIT=0 复现;S5 0.8.1 安装快照 step 6 同文计 1、质量句计 0。转 verified 前提:用户批准晋升、版本 bump 至 0.8.2、.zcode 活路径与源树一致。
fix_revision: agentflow 0.8.2
---

## 现象

2026-09-19 上午，在 `infinite-canvas` 仓库的 linked worktree `infinite-canvas-base`（分支
`codex/server-structure`）执行多分支合并解冲突。合并任务全程未启用 agentflow、未派发任何角色。

reflog 可证的提交序列（证据：`.git/worktrees/infinite-canvas-base/logs/HEAD`；提交对象由独立
分析员以 `git cat-file` 松散对象核验）：

```
83aa1fa → 479a70c    fix-payment-order-lifecycle（fast-forward）
479a70c → 52c5634    merge feature-sso-cookie-domain
52c5634 → 7af6cf5    merge feature-blog
7af6cf5 → 619ae69    amend 修复
```

用户复盘材料另称：共 6 个分支、其中后两条在 reflog 中无痕迹；合并结果与目标仓库 351 个文件
逐字节一致。此两点为**用户报告、未复现**，本记录不作为已核验事实。

缺陷本体（复盘材料 + 独立分析员核验）：解冲突时 Edit 边界误判，`server/internal/config/config.go`
中 `func (c *Config) validate() error {` 声明行相邻重复进入交付；交付前自检仅 grep 冲突标记
（`^<<<<<<<` / `^>>>>>>>`），按定义抓不住相邻行重复；用户验收时执行 `go build` 才抓出，修复后
amend 为 `619ae69`。

决定性证据（supervisor 已跑，逐字）：

```
$ git show 7af6cf5:server/internal/config/config.go | grep -c "func (c \*Config) validate() error {"
2
$ git show 619ae69:server/internal/config/config.go | grep -c "func (c \*Config) validate() error {"
1
```

`git worktree list` 显示 `infinite-canvas-base` 位于 `619ae69 [codex/server-structure]`；该
worktree 的 `git status --porcelain` 输出为空（工作树干净）。

反模式：以「清冲突标记」冒充验收。`grep` 无冲突标记只证明标记字样不在场，不能证明解冲突内容
正确——它对相邻行重复这一缺陷类没有判别力。本仓库 reviewer 契约（agents/reviewer.md）的口径
是 `Treat a claimed check you cannot see raw output for as not run.`；同理，一个即使跑了也
抓不住目标缺陷类的检查，不构成对合并产物的验收。

## 根因

归因 `workflow_policy`：条款缺口，不是执行者无视已有禁令。先例 ISS-2026-007（git 集成的
授权侧缺口，0.4.2 修复）同构——那次缺的是「集成要不要授权」，这次缺的是「集成产物如何验收」。
provenance `agentflow`：缺口落点是 agentflow 独立于会话的工件面（skill description、路由表、
硬边界 3）。

边界先说清（已覆盖面不得记成缺口）：

- 授权维度完整：0.4.2 修复的硬边界 3 在本次事件中按预期生效——合并本身是用户要求的，无越权。
  本次缺口不在授权侧。
- 质量维度在 skill 已激活时有文本覆盖：第 8 步评审门（含 supervisor 亲写不可豁免）与第 6 步
  整体检查都在。缺的不是「零质量条款」，而是下面四点精确缺口。

缺口面四点：

1. **触发判据枚举不含合并/集成形态——失败是识别/归类失败，不是零判据。**
   `skills/agentflow/SKILL.md:3` description 枚举（0.8.1 原文，单行引文）：

   ```
   Use for cross-layer features, architecture changes, parallel investigation, delegated implementation, automated testing of user-visible features, document-chain delivery (proposal/spec/design/plan for a feature), or work that benefits from an explicit review gate; skip trivial single-step work where delegation would add overhead.
   ```

   无 branch integration / conflict resolution / merge 字样。兜底短语 "work that benefits
   from an explicit review gate" 字面上可罩住改变用户可见行为的合并，但没有把合并形态显式
   枚举，识别就靠执行者自行归类——本次未归类成功。用户级清单同样无此形态：
   `/Users/lihanghang1/.zcode/AGENTS.md`（:49-58「Agentflow 的使用时机」主动启用清单，各条目
   首词逐字）为 `跨层功能`、`架构改动`、`可并行的调查或委派实现`、`需要独立评审门的改动`、
   `Bug`、`规划任务`——无合并、解冲突、integration 字样；该文件不在本仓库，绝对路径仅在此
   行内代码引注。`skills/agentflow/references/roles.md:10-21` 路由表十行的 Task shape 列
   （逐字，Roles 列略）：

   ```
   Single-layer small fix, clear reproduction
   Frontend or backend implementation with a bounded scope
   Cross-layer feature, contract change, migration
   Planning request, no code yet
   Automated testing of a user-visible feature (user asked, or the plan carries a test-design task)
   Test run produced failures or coverage gaps
   Material, uncertain, recurring, or cross-layer bug
   Small bug with a verified reproduction
   Review of documents authored under another system's rules
   Plugin/role-instruction improvement
   ```

   无一行对应 merge / branch integration / conflict resolution 任务形态。

2. **merge 只有授权维度，无质量句。** `skills/agentflow/references/contracts.md:13` 硬边界 3
   （0.8.1 原文，单行引文）：

   ```
   3. No push, deploy, publish, remote deletion, or third-party messaging without authorization already present in the conversation. Integrating others' work or rewriting history is the same class of act and needs per-instance authorization — `git merge`, `rebase`, `cherry-pick`, or pulling remote changes into a shared branch is a user decision (which method, which side of a conflict), not a step to complete a rejected push. The default on a rejected push is a read-only report: `git fetch` plus `log`/`diff` showing the added commits, the changed files, and the overlap; the user then chooses the integration method.
   ```

   全文管授权（集成方式、冲突采纳侧归用户），无一句涉及合并产物的验收。质量侧已有的文本与
   缺的条款要分开：第 6 步（`skills/agentflow/SKILL.md:122`）要求
   `runs the checks that establish the whole feature works`；第 8 步
   （`skills/agentflow/SKILL.md:124`）要求 `after material changes, assign an independent
   reviewer` 且 supervisor 亲写时 `this gate is mandatory and cannot be waived`。缺的是：
   把「亲解代码冲突的合并提交」显式指认为 material change 的条款、合并专属检查清单、以及
   「只查冲突标记」的显式反模式。没有这三样，第 6 步的整体检查在合并场景被执行者降格成了
   清标记，本次即如此。

3. **评审门无激活外兜底。** 第 8 步全部纪律位于 `skills/agentflow/SKILL.md:115-126` 的
   workflow 内，skill 未加载时结构上不可能生效——本次合并任务未启用 agentflow，第 6/8 步的
   文本从未进入执行上下文。agentflow 侧可修的只是触发判据（让合并形态被识别进来）；skill
   之外的最小兜底属宿主 AGENTS.md，是用户侧动作，不在 agentflow 候选内。

4. **与宿主「不构建」规则未调和，构成负向抑制（归因类 context，修复在宿主侧，不在本候选）。**
   宿主仓库规则原文 `infinite-canvas@53bff1e:AGENTS.md`：

   > 每次写完代码,不需要检查语法，不需要执行构建，用户会自己做。

   （:23）

   > 发版本流程中不要执行编译、测试或构建，除非用户明确要求。

   （:90）

   :3 优先级条款规定「开发时优先遵循本文件」；:110 已有定向 must-run 例外先例（MySQL 迁移）。
   该规则与合并场景无例外衔接：合并解冲突后的产物验收恰恰需要构建类检查，规则文本把「不构建」
   写成默认，负向抑制了交付前运行 `go build` 的倾向。agentflow 侧对应张力：第 5 步
   （`skills/agentflow/SKILL.md:121`）要求 worker `follow repository rules, run relevant
   checks`，但没有裁决句说明仓库规则禁止构建时检查义务如何落——候选修复以裁决句处理，宿主
   规则本身的例外衔接留给宿主侧。

直接责任层归位：supervisor 亲解冲突时的 Edit 边界误判与仅清标记的弱自检是事件的直接执行层
原因；宿主规则的负向抑制是 context 层因素。两层都不进 agentflow 证据簇的反事实主张——
agentflow 侧的反事实主张（合并形态被触发判据识别、走第 6/8 步则该缺陷会在交付前被整体检查或
评审门拦下）是假设，预防效果待 0.8.2 落地后对照验证，不得写「已防住」。

## 问题代码

缺陷声明行（交付版本 `infinite-canvas@7af6cf5:server/internal/config/config.go` 中出现
2 次，相邻重复；修复提交 `619ae69` 中 1 次）：

```go
// infinite-canvas@7af6cf5:server/internal/config/config.go
func (c *Config) validate() error {
```

完整文件不在此复现；在场性与修复以「决定性证据」的 `grep -c` 计数（2 → 1）为准。
agentflow 侧的缺口落点是条款文本（见根因各引文），不是本仓库代码缺陷。

## 修复

状态：**已发布（agentflow 0.8.2：用户批准晋升后版本已 bump——五 manifest + packaging/runtime
重建 + CHANGELOG 条目，validate.py all 复跑 9×PASS EXIT=0；frontmatter `status: verified`，
`fix_revision: agentflow 0.8.2`）**。以下条款已全部落地（原候选计划改完成时态）；预防效果
待对照验证，不写「已防住」。宿主 installed 快照重装为用户侧待办（已知残余，见「## 审查」）。

- `skills/agentflow/SKILL.md` description 枚举已补
  `branch integration and conflict resolution`，让合并形态可被识别；
- `skills/agentflow/SKILL.md` 第 6 步 Integrate 已扩写合并质量门：触发条件（亲解代码冲突的
  合并提交按 material change 对待）、确定性检查及原始输出要求、「清冲突标记不是检查」的
  反模式、以及宿主规则不构成豁免的裁决句（裁决第 5 步
  `follow repository rules, run relevant checks` 与宿主「不构建」规则的张力）；
- `skills/agentflow/references/roles.md` 路由表已补一行（中文镜像 `agentflows@0.8.2:docs/agent-roles.md` 当时已同步；该镜像已于 2026-10-12 精简批删除，角色面收敛为 `agents/*.md` 与 `skills/agentflow/references/roles.md` 两处）；
- `skills/agentflow/references/contracts.md` 硬边界 3 末尾已接质量句：授权≠验证，合并产物仍按
  material change 进评审门，清标记不是检查；
- episode/decision record 增加合并类固定字段属 gate 变更
  （`skills/improve/references/episode.schema.json` 在保护面内），只标记给人审，不进本候选。

规则文本变更，无自动化行为回归面；`regression_status` 按评审口径由 `not-run` 改为 `pass`
（pass 口径与 ISS-2026-007 先例一致，见「## 审查」）。closure_criteria 已由评审人指定
（S1–S5 与三项转 verified 前提），按实际执行结果核对通过。

## 变更记录

- 2026-09-20 00:00 · 建档（open）· 证据：reflog 合并序列与 `git show | grep -c` 计数 2→1
  证实重复声明在场与修复；缺口面四点，归因 workflow_policy；0.8.2 候选修复计划中，未落地。
- 2026-09-20 12:10 · 候选落地 · 四文件条款改动已实施（skills/agentflow/SKILL.md description
  枚举补 branch integration and conflict resolution、第 6 步 Integrate 合并质量门、
  skills/agentflow/references/roles.md 与 agentflows@0.8.2:docs/agent-roles.md 路由行（该镜像文件已删，见上）、
  skills/agentflow/references/contracts.md 硬边界 3 质量句）；validate.py all 9×PASS EXIT=0、
  isolation.py check-diff blocked:[] EXIT=0；status 转 fixed-pending-review；candidate record
  `improvements/candidates/0.8.2.json` 已建（改进三件套已随 2026-10-12 瘦身批停用删除，git 历史可回溯）。
- 2026-09-20 12:40 · 独立评审通过 · S3 检查发现两处额外外来项（tracked AGENTS.md +14 行
  document-chain linter 段、untracked tools/lab/doc_chain.py，mtime 2026-09-20 12:00/12:04），
  按内容/mtime/门面三重证据归因并行会话，与四候选文件及本 bug 缺口面零交集；门检在共存态
  复跑全绿；评审最终 approved。
- 2026-09-20 14:00 · 晋升落账 · 用户批准后 0.8.2 bump+runtime 重建+validate 全绿，记录转
  verified，台账 consolidated_in 0.8.2；宿主快照重装待用户应用内操作（已知残余）。

## 审查

已验证（`status: verified`，`fix_revision: agentflow 0.8.2`）。评审链：`agentflow:evaluator`
两轮评审均 `approved`；指定检查 S1–S5 由 supervisor 逐字执行并回传原始输出：

- S1 五条款 grep 各计 1：`branch integration and conflict resolution` /
  `branch merge with conflict resolution` / `任务本身是分支合并/解冲突` /
  `clearing conflict markers is not a check` / `iteration default, not an exemption`；
- S2 工作流步骤 10 行原序命中，硬边界 3（contracts.md:13）/14（contracts.md:24）行号命中，
  skills/docs 面版本字面量零命中；
- S3 tracked 改动面 vs 5da90f2 = 四候选文件 + AGENTS.md（已归因并行 linter 段），untracked =
  已申报外来集（document-chain.md、docs/product/、tools/lab/doc_chain.py）+ 本环自有记录，
  未超出枚举集；
- S4 `python3 tools/lab/validate.py all` 9×PASS EXIT=0；`tools/lab/isolation.py check-diff`
  输出 `blocked:[]` EXIT=0；
- S5 0.8.1 安装快照 step 6 同文计 1、质量句计 0（快照仍为修复前文本，与已知残余一致）。

closure_criteria 三前提全部满足：用户批准晋升（原文「可以,然后处理冲突记得有记录
不要解决完了也没回溯问题」）；版本 bump 至 0.8.2（五 manifest + packaging/runtime 重建 +
CHANGELOG 条目，validate.py all 复跑 9×PASS EXIT=0）；`.zcode/skills/agentflow` 符号链接
活路径与源树 SKILL.md / contracts.md / roles.md 三 diff 无输出、退出码 0。

已知残余（与 ISS-2026-007 先例 C5 残余口径一致）：宿主 installed 快照仍 0.8.1——
`python3 tools/lab/validate.py installed` 逐字输出：

```
FAIL installed (1 error(s)): ~/.zcode/cli/plugins/cache/agentflow-local/agentflow: no snapshot for source version 0.8.2; installed versions: 0.8.1. Refresh the marketplace and reinstall — source edits do not reach the installed copy, so role behavior still comes from the stale snapshot.
```

等用户在 ZCode 应用内刷新 marketplace 并重装后消除。预防效果待对照验证（measurement: none，
无 instrumented merge/integration 用例）；`regression_status: pass` 口径同先例：指定检查
已运行且输出符合预期，不是行为服从的自动化证明——失效检测器为再犯加 recurrence/improve 环。
