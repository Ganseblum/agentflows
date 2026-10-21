# agents — 角色定义（交付面）

本目录是 Agentflow 的**角色定义面**：每个 `.md` 是一个角色的系统提示词档案，宿主（ZCode /
Claude Code / Codex）从已安装的插件快照加载它们。改这里的源文件不等于改宿主跑的内容——
重装插件后才生效，漂移检查用 `python3 tools/lab/validate.py installed`。

**本文件是目录入口索引；角色文件无需、也不得有同名 frontmatter `name` 之外的形态分歧
（docs 门逐个断言 `name` = 文件名，README 为放行例外）。**

## 工作链（任务怎么落到角色）

选角色分两步：**先认链**，再从链里取角色。链是默认入口，画像是难 case 的备用深度；两者同一批
角色，不是两套角色。链外没有第七种入口。

| 链 | 默认序列 | 不可省的一步 |
| --- | --- | --- |
| 实现 | 工程师（frontend / backend，按层选一或并行）→ Reviewer | 独立评审门（作者不验证自己的改动） |
| 缺陷 | Bug investigator → Bug fixer → Reviewer → Bug recorder | Fixer 不得关闭自己的修复 |
| 测试 | Test planner → Test executor | Executor 不改被测对象 |
| 规划 | Technical director → Plan architect | 计划只由 Plan architect 写 |
| 改进 | Feedback analyst → Candidate engineer → Evaluator → Release governor | 候选不自评、不自放行 |
| 独立评审 | Reviewer（单点） | 评审期间不编辑、不运行受候选控制的命令 |

完整链路契约与角色画像见 [`../skills/agentflow/references/roles.md`](../skills/agentflow/references/roles.md)。

## 角色清单（14）

| 文件 | 一句话职责 | 工具面 |
| --- | --- | --- |
| `backend-engineer.md` | 有界后端范围实现：API、持久化、授权、迁移 | 读写 |
| `frontend-engineer.md` | 有界前端范围实现：UI 状态、样式、类型契约 | 读写 |
| `bug-investigator.md` | 缺陷调查：范围定性、可复现步骤、诊断（不改码） | 只读 |
| `bug-fixer.md` | 已诊断缺陷的单点修复 + 回归覆盖 | 读写 |
| `bug-recorder.md` | 把诊断与验证结果固化为可追溯记录 | 写记录 |
| `reviewer.md` | 独立评审 material 改动（作者不是验证者） | 只读 |
| `technical-director.md` | 跨层架构 / 接口 / 安全边界等难回退决策 | 只读 |
| `plan-architect.md` | 把各角色发现转成带状态与证据回写的执行计划 | 写计划 |
| `test-planner.md` | 为用户可见功能设计可执行测试计划 | 写计划 |
| `test-executor.md` | 对目标环境执行测试计划（脚本自动化优先） | 写执行记录（禁 Edit） |
| `feedback-analyst.md` | 归一化改进反馈的证据、聚类失败、归因 | 只读 |
| `candidate-engineer.md` | 实现单个有界的改进候选（不自评） | 读写 |
| `evaluator.md` | 只读对照候选与冻结基线的结果记录 | 只读 |
| `release-governor.md` | 晋升 / 修订 / 拒绝 / 回退决策 | 只读 |

## 调度要点

- 角色是**能力不是阶段**：只上那些能降低风险或允许有效并行的角色（纯前端小修不需要后端）。
- 并行只并行「写范围互不重叠」的实现；两个写入者共用同一仓库时还要各用分支或 worktree。
- `maxTurns` 按意图元数据对待（声明未验证）；生效约束是各角色提示词里的预算纪律
  （最后一轮留给结果，目标未成返回 `partial`）。
- 每个角色的 `tools` / `disallowedTools` 由宿主白名单强制；角色与门的写范围互证见
  [`../skills/agentflow/references/roles.md`](../skills/agentflow/references/roles.md) 的产物归属表。
