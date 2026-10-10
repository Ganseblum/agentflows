# <项目名> 工作流与文档中枢（`<project>-workflow-ai`）
> <一句话：本目录是 <项目> 的文档与记录中枢——需求全生命周期（`features/`）、缺陷与事项（`issues/`）、发布验收（`releases/`）与唯一文档索引（`index.md`）。全部纯 Markdown，中文单份。>

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `features/` | 需求全生命周期：`feature-<日期>-<主题>/`（proposal → spec → design → plan → 回写）；feature 的 README 是唯一入口 |
| `issues/` | 缺陷与事项流：开放条目平铺 + `归档/`；小修在条目内解决，中/大问题经用户确认后升格为 Feature |
| `releases/` | 发布验收记录：`todo.md`（待办）、`pending-test.md`（待验收） |
| `index.md` | 唯一文档索引 |

## 约定

- 内容统一 `.md` 后缀；中文单份、不中英混排；文档间互链用相对路径并带 `.md` 后缀。
- 新增、移动或删除文档必须同步维护 `index.md`；新 feature 目录与结构变更先经用户确认，Agent 不得自动建目录。
- feature 文档链走 proposal → spec → design → plan 的阶段门；评审类门禁只由独立评审勾选，进度板与实际产物保持一致。
- 可复制骨架：feature 模板、issue 骨架与 releases 双文件随接入约定就位后从模板复制填写。
