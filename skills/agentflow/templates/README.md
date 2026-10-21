# templates — 文档链模板（先抄模板，再填占位符）

> 固定标题字面量：模板章节不得改名或删除；不适用的节写 `N/A: 原因`。目标仓已有模板体系时用其的，本目录是下限。
> 写前自查（术语与指称）：按「换 > 释 > 删」处理；**代号裸用**（代号只在定义处出现，正文以「白话（代号）」或「代号（白话）」成对伴随）与**模式词分域**（标识符留在代码、SQL、日志语境，正文用业务白话）两条形态同受约束；判据见 [`document-chain.md` 表达纪律节](../references/document-chain.md)。
> 命名与目录形态：骨架按链契约的角色目录组织——`spec/be/backend.md` ↔ `design/be/backend.md`、`spec/fe/frontend.md` ↔ `design/fe/frontend.md`、`spec/qa/acceptance.md` ↔ `design/qa/testing.md`、`spec/ui/visual.md` ↔ `design/ui/visual.md` 镜像；单文档阶段 `proposal/proposal.md`、`plan/execution.md`。复制时保持目录与文件名。
> 三条跨阶段贯通项（复制骨架时不要漏）：**线框/原型** `prototype/index.html`（提案与设计都指向它，浏览器直开）；**视觉来源** `spec/ui` §2.1 → `design/ui` §0.1（组件库/主题机制/token 源文件给 `path:line`，A 复用 / B 移植 / C 冷启动 三档，禁凭空造色值）；**埋点** 三处口径——`proposal/proposal.md` §6.2 决策 → `spec/fe/frontend.md` §4 口径 → `design/fe/frontend.md` §1.7 事件契约，验收在 `spec/qa` 与 `design/qa`（评审清单与隐私红线见 [`telemetry.md`](../references/telemetry.md)）。

| 模板 | 用法（复制到 feature 目录的对应路径） |
| --- | --- |
| [feature/README.md](feature/README.md) | 批次入口：元信息 + 推进进度（阶段门）+ 当前步骤 + 模块总览 + 分支基线与落库映射 |
| [feature/proposal/proposal.md](feature/proposal/proposal.md) | 需求提案（单文档阶段，`proposal/proposal.md`） |
| [feature/spec/be/backend.md](feature/spec/be/backend.md) · [fe](feature/spec/fe/frontend.md) · [qa](feature/spec/qa/acceptance.md) · [ui](feature/spec/ui/visual.md) | 各角色规格（`spec/<角色>/`） |
| [feature/design/be/backend.md](feature/design/be/backend.md) · [fe](feature/design/fe/frontend.md) · [qa](feature/design/qa/testing.md) · [ui](feature/design/ui/visual.md) | 各角色技术方案（`design/<角色>/`） |
| [feature/plan/execution.md](feature/plan/execution.md) | 执行契约（单文件；目标仓有自己的计划约定时用其约定） |
| [feature/prototype/index.html](feature/prototype/index.html) · [README](feature/prototype/README.md) | 可直开线框/原型骨架：复制到 `<feature 目录>/prototype/index.html`，浏览器双击即见结构稿；四态可切换、页签自动生成、零依赖 |
| [decision/decision-record.md](decision/decision-record.md) · [decision-brief.md](decision/decision-brief.md) | 决策记录八列表（拍板口逐条占行，C16 机器可判）与决策简报骨架（出处/选项/影响/关闭条件）：记录落 `docs/PENDING-DECISIONS.md` 等拍板口，检查由 `validate.py decision_gate` 承载 |
| [testing/plan.md](testing/plan.md) · [testing/run.md](testing/run.md) | 测试用例库 / 执行记录骨架（frontmatter 信封固定字段）：复制到 `docs/features/<批次>/testing/<project>-<feature>/plan-<YYYY-MM-DD>-<NNN>.md` 与 `run-<YYYY-MM-DD>-<NNN>.md` |
| [hub/README.md](hub/README.md) · [index.md](hub/index.md) · [issues-README.md](hub/issues-README.md) | 文档枢纽仓骨架（`<project>-workflow-ai/` 的 README、index、issues 看板） |
| [issue/issue-template.md](issue/issue-template.md) | ISS 记录骨架（frontmatter 全字段 + 固定章节的契约形态）：复制到 `issues/ISS-<YYYY>-<NNN>-<slug>.md` |
| [releases/todo.md](releases/todo.md) · [releases/pending-test.md](releases/pending-test.md) | 发布待办 / 待验收双文件骨架：复制到 `releases/`（这两个文件就是发布侧的现行载体） |


## 可选层（语料中出现的扩展，按需启用）

- `api/`：接口文档（研发提交 QA 用；§0 文档粒度约定 + §7 提交前自检清单）。
- `复盘.md`：feature 收口后的复盘（喂改进环的证据来源）。
- `code-gap-matrix`：文档 vs 代码现状完成度矩阵（在既有代码上落地的 feature 强烈建议）。
- 超大 feature 的模块化拆分：一模块一套 proposal/spec/design/plan 四件套 + 总控 spec。
