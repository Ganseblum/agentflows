# templates — 文档链模板（先抄模板，再填占位符）

> 固定标题字面量：模板章节不得改名或删除；不适用的节写 `N/A: 原因`。目标仓已有模板体系时用其的，本目录是下限。
> 写前自查（术语与指称）：按「换 > 释 > 删」处理；**代号裸用**（代号只在定义处出现，正文以「白话（代号）」或「代号（白话）」成对伴随）与**模式词分域**（标识符留在代码、SQL、日志语境，正文用业务白话）两条形态同受约束；判据见 [`document-chain.md` 表达纪律节](../references/document-chain.md)。

| 模板 | 用法 |
| --- | --- |
| [feature/README.md](feature/README.md) | 批次入口：元信息 + 推进进度 + 当前步骤 + 模块总览 + 分支基线与落库映射 |
| [feature/proposal.md](feature/proposal.md) | 需求提案 |
| [feature/spec/fe.md](feature/spec/fe.md) · [be](feature/spec/be.md) · [qa](feature/spec/qa.md) · [ui](feature/spec/ui.md) | 各角色规格 |
| [feature/design/fe.md](feature/design/fe.md) · [be](feature/design/be.md) · [qa](feature/design/qa.md) · [ui](feature/design/ui.md) | 各角色技术方案 |
| [feature/plan/be.md](feature/plan/be.md) · [fe](feature/plan/fe.md) · [qa](feature/plan/qa.md) | 各角色实施计划 |

## 可选层（语料中出现的扩展，按需启用）

- `api/`：接口文档（研发提交 QA 用；§0 文档粒度约定 + §7 提交前自检清单）。
- `复盘.md`：feature 收口后的复盘（喂改进环的证据来源）。
- `code-gap-matrix`：文档 vs 代码现状完成度矩阵（在既有代码上落地的 feature 强烈建议）。
- 超大 feature 的模块化拆分：一模块一套 proposal/spec/design/plan 四件套 + 总控 spec。
