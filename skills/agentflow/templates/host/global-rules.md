# Agentflow 全局规则

<!--
  这是宿主级全局规则的正文字面量。安装时整块替换进宿主自己的指令文件，
  只把 {{version}} 换成当前插件版本；不要改正文措辞，改这里再重新安装。
  安装协议与宿主矩阵见 ../../references/hosts.md。
  本文件与 SKILL.md 的「集成」节是同一组规则的两种载体：改一处必须同步另一处。
-->

<!-- agentflow:begin v{{version}} -->

## Agentflow 全局规则（托管块，勿手改）

适用范围：本宿主的所有工作区。仓库级约定（检查命令、文档落点、分支前缀实例）由各仓 `AGENTS.md` 的「Agentflow 接入约定」节定义，不在这里重复。

### 1. 写操作前先确认分支

任何写操作之前——编辑文件、`git merge`、`git rebase`、`git commit`、`git push`、`git cherry-pick`——先运行 `git rev-parse --abbrev-ref HEAD` 确认当前分支。一次任务中切换过分支（合并、切分支排查、切换工作分支）后，后续每次写操作前重新确认。不得"先改后查"；发现已经先改后查，立即停下报告，不继续提交或推送。

### 2. 分支前缀与改动落点

仓库使用 `feature-*` / `release_sim_*` / `release_pre_*` / `release_prod_*` 前缀时：

- 允许：`feature-*` → `release_sim_*` / `release_pre_*` / `release_prod_*`；主干（`master` / `main`）→ `feature-*`。
- 禁止：任何 `release_*` → `feature-*`。
- 代码改动只落 `feature-*`。`release_*` 上只允许就地解决冲突，且不得借解冲突夹带其它改动；落在 `release_*` 上的其它写操作，先停下来向用户确认。
- 四类前缀之外的仓库按该仓自身规则执行。

### 3. 合并与推送是两次独立授权

解冲突不等于授权合并；合并不等于授权推送。未经当次明确要求，不执行 `git merge`、合并式 `git pull`、跨分支 `cherry-pick`、推送、发布或删除远端数据。推送被拒时先用只读的 `fetch` / `log` / `diff` 说清重叠面，由用户选择集成方式。

### 4. 证据

摘要不是验证；只有复现出来的确定性检查才算通过。无法复现或环境缺失的检查记为**未运行**，绝不计为通过。关于工具或宿主行为的断言，先做最小实验并保留退出码与逐字输出；做不到就标注为未验证。

### 5. 合并收口

- 手工解过冲突的合并按 **material 改动**对待：解决冲突就是在写代码，独立评审门适用；报完成前运行仓库的构建检查与**每个受影响单元的测试套件**，并留存原始输出。
- 测试失败不得用跳过 pretest、`--ignore-scripts`、只跑子集或缩小 glob 的方式换成绿色：要么修，要么把红作为阻塞升级给用户，并保留原始输出。
- 合并一个**曾被回滚**的分支时，先用 `git log --grep='This reverts commit' --oneline` 找到回滚提交，再用 `git show --name-status <revert>` 取文件清单逐项对账，逐文件确认合并结果。
- 评审 diff 必须包含源分支一侧：源分支还在时用 `source_branch..merge_result`；源分支已删除时用 `merge_result^2..merge_result`。只给 `merge_result^1..merge_result`（第一父提交基线）的评审看不见「源分支有、合并结果没有」的漏项。

### 6. 评审绑定 revision

独立评审针对确切的 `reviewed_revision`。revision 变化后重新开门，旧批准不得沿用到新提交；拿不到评审就如实记为未评审，不写成"已批准"。

<!-- agentflow:end -->
