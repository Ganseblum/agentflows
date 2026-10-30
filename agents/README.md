# agents — 角色定义（交付面）

本目录是 Agentflow 的**角色定义面**：每个 `.md` 是一个角色的系统提示词档案，宿主（ZCode /
Claude Code / Codex）从已安装的插件快照加载它们。改这里的源文件不等于改宿主跑的内容——
重装插件后才生效，漂移检查用 `python3 tools/lab/validate.py installed`。

**本文件是目录入口索引；角色文件无需、也不得有同名 frontmatter `name` 之外的形态分歧
（docs 门逐个断言 `name` = 文件名，README 为放行例外）。**

## 工作链（任务怎么落到角色）

选角色先认链，再读对应的实际角色文件。详细职责不在路由里复制；执行方法集中在
[执行与验证](../skills/agentflow/references/execution.md)。遗留补测复用测试链，不另建角色或第七条链。

五条链——实现、缺陷、测试、规划、独立评审——的默认序列、默认可省步骤，以及那一步
**不可省**（跳过即改变结论效力），单点定义在
[`../skills/agentflow/references/roles.md`](../skills/agentflow/references/roles.md) 的工作链节；
本文件不再复制那张表。2026-10-22 的走查发现这张表在两个文件里各写一份且列数已经分歧（这里三列、
那里四列），而「同一结论双源并存、不声明取舍」正是本仓自己列为出现即缺陷的反模式。

## 角色清单（10）

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

## 调度要点

- 角色是**能力不是阶段**：只上那些能降低风险或允许有效并行的角色（纯前端小修不需要后端）。
- 并行只并行「写范围互不重叠」的实现；两个写入者共用同一仓库时还要各用分支或 worktree。
- `maxTurns` 按意图元数据对待（声明未验证）；生效约束是各角色提示词里的预算纪律
  （最后一轮留给结果，目标未成返回 `partial`）。
- 只观察到宿主强制 `tools` 白名单（ZCode 实测）；`disallowedTools` 在 Qoder 等宿主未验证强制，不得当作隔离保证。各角色的写范围见其文件内的
  `## 产物归属` 矩阵，文档链各阶段谁产出见
  [`../skills/agentflow/references/roles.md`](../skills/agentflow/references/roles.md) 的「阶段 × 角色速查」表。
