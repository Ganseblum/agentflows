# templates — 按任务选择材料

> 先按[文档档位](../references/document-chain.md#文档档位)选择轻量或完整模板。完整链固定标题不得改名或删除，不适用节写 `N/A: 原因`；轻量使用单份 README 的四个固定章节。目标仓已有体系时复用，不另建重复正文。
> 写前自查（术语与指称）：按「换 > 释 > 删」处理；**代号裸用**（代号只在定义处出现，正文以「白话（代号）」或「代号（白话）」成对伴随）与**模式词分域**（标识符留在代码、SQL、日志语境，正文用业务白话）两条形态同受约束；判据见 [`document-chain.md` 表达纪律节](../references/document-chain.md)。
> 命名与目录形态：骨架按链契约的角色目录组织——`spec/be/backend.md` ↔ `design/be/backend.md`、`spec/fe/frontend.md` ↔ `design/fe/frontend.md`、`spec/qa/acceptance.md` ↔ `design/qa/testing.md`、`spec/ui/visual.md` ↔ `design/ui/visual.md` 镜像；proposal 使用 `proposal/proposal.md`。计划按使用位置选择：目标仓使用自身约定；没有约定时复制 `plan/execution.md`。Agentflow 仓库的批次记录使用 `plan/<plan_id>.md` 混合契约。复制时保持对应形态的文件名与信封。
> 三条跨阶段贯通项（复制骨架时不要漏）：**产品原型**（目标仓已维护原型库 → 必须形态 A：正文在库内、批次 `prototype/index.html` 只做入口页；确无原型库 → 形态 B：批次内可编辑 HTML 是正文。两种形态都沿用项目真实视觉基线，跨批次登记上游路径与 revision，截图可由 HTML 导出）；**视觉来源** `spec/ui` §2.1 → `design/ui` §0.1（组件库/主题机制/token 源文件给 `path:line`，A 复用 / B 移植 / C 冷启动三档，禁凭空造色值）；**埋点** 三处口径——`proposal/proposal.md` §6.2 决策 → `spec/fe/frontend.md` §4 口径 → `design/fe/frontend.md` §1.7 事件契约，验收在 `spec/qa` 与 `design/qa`（评审清单与隐私红线见 [`telemetry.md`](../references/telemetry.md)）。

| 模板 | 用法（复制到 feature 目录的对应路径） |
| --- | --- |
| [feature/lightweight.md](feature/lightweight.md) | 满足六条适用判据的任务：复制为 feature README，集中需求、实施证据与恢复；不能用轻量省略评审或验证 |
| [feature/README.md](feature/README.md) | 批次入口：元信息 + 推进进度（阶段门）+ 当前步骤 + 模块总览 + 分支基线与落库映射 |
| [feature/proposal/proposal.md](feature/proposal/proposal.md) | 需求提案（单文档阶段，`proposal/proposal.md`） |
| [feature/spec/be/backend.md](feature/spec/be/backend.md) · [fe](feature/spec/fe/frontend.md) · [qa](feature/spec/qa/acceptance.md) · [ui](feature/spec/ui/visual.md) | 各角色规格（`spec/<角色>/`） |
| [feature/spec/checklist.md](feature/spec/checklist.md) | Spec 待确认问题唯一登记表（`spec/checklist.md`，`Q-01/Q-02`…；阻塞阶段、来源、答案与关闭条件集中维护） |
| [feature/design/be/backend.md](feature/design/be/backend.md) · [fe](feature/design/fe/frontend.md) · [qa](feature/design/qa/testing.md) · [ui](feature/design/ui/visual.md) | 各角色技术方案（`design/<角色>/`） |
| [feature/plan/execution.md](feature/plan/execution.md) | 执行契约（单文件；目标仓有自己的计划约定时用其约定） |
| [feature/prototype/index.html](feature/prototype/index.html) · [README](feature/prototype/README.md) | 双形态可直开原型骨架：形态 A 只留入口页链接块（删 sections，指到库内正文 + `path@revision`），形态 B 复制到 `<feature 目录>/prototype/index.html` 按真实视觉基线改造；四态可切换、页签自动生成、零依赖 |
| [decision/decision-record.md](decision/decision-record.md) · [decision-brief.md](decision/decision-brief.md) | 决策记录九列表（八个决策字段 + 生命周期状态列；拍板口逐条占行，C16 机器可判）与决策简报骨架（出处/选项/影响/关闭条件）：记录落 `docs/PENDING-DECISIONS.md` 等拍板口，检查由 `validate.py decision_gate` 承载 |
| [testing/plan.md](testing/plan.md) · [testing/run.md](testing/run.md) | 测试用例库 / 执行记录骨架（frontmatter 信封固定字段）：复制到 `docs/features/<批次>/testing/<project>-<feature>/plan-<YYYY-MM-DD>-<NNN>.md` 与 `run-<YYYY-MM-DD>-<NNN>.md` |
| [host/README.md](host/README.md) · [host/global-rules.md](host/global-rules.md) | 宿主级全局规则（跨仓）：托管块正文 + 操作清单（协议权威是 [`references/hosts.md`](../references/hosts.md)）。只在用户明确确认后写入宿主全局指令文件，不随仓库 Init 自动写 |
| [engineering/baseline.md](engineering/baseline.md) | 目标仓工程基线骨架：技术栈与运行环境、目录与文件职责、命名与类型、禁止的平行方案、新增模块必做清单、测试栈、质量门顺序、配置与边界、规范入口与规则写法。已有工程规范时只登记入口，没有时与用户确认后落一份最小基线 |
| [hub/README.md](hub/README.md) · [index.md](hub/index.md) · [issues-README.md](hub/issues-README.md) | 文档枢纽仓骨架（`<project>-workflow-ai/` 的 README、index、issues 看板） |
| [hub/repo-rules.md](hub/repo-rules.md) | 目标仓 `AGENTS.md`「Agentflow 接入约定」节骨架（固定硬判据 + 仓事实槽位 + begin / end 版本标记）：Init 的必产出，重跑只替换标记内内容 |
| [issue/issue-template.md](issue/issue-template.md) | ISS 记录骨架（frontmatter 全字段 + 固定章节的契约形态）：复制到 `issues/ISS-<YYYY-MM-DD>-<slug>.md` |
| [releases/todo.md](releases/todo.md) · [releases/pending-test.md](releases/pending-test.md) | 发布待办 / 待验收双文件骨架：复制到 `releases/`（这两个文件就是发布侧的现行载体） |


## 可选层（语料中出现的扩展，按需启用）

- `api/`：接口文档（研发提交 QA 用；§0 文档粒度约定 + §7 提交前自检清单）。
- `复盘.md`：feature 收口后的复盘（方法复盘与后续证据池的来源）。
- `code-gap-matrix`：文档 vs 代码现状完成度矩阵（在既有代码上落地的 feature 强烈建议）。
- 超大 feature 的模块化拆分：一模块一套 proposal/spec/design/plan 四件套 + 总控 spec。

## 执行证据工具输入

[执行请求](testing/execution-request.json)与[补测映射](testing/backfill-map.json)是字段示例，复制后按实际项目替换并完整分类输入；不直接代表现有项目。字段和命令见[工具用法](../references/workflow-tool.md)。
