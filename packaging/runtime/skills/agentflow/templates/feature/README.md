# `feature-<日期>-<主题>` Feature 总览
<一句话：本 README 是当前 Feature 的唯一入口；推荐阅读顺序 proposal/需求提案 → spec/{be,fe,qa} → design/{be,fe,qa} → plan/execution>
> 段落映射：逐段声明落点（下表），落点指向本目录之外的活文档时写对方路径；落点非空且非「—」的段落可缺目录，其余段落齐全。
> 轻量降档：只在「元信息」的段落映射表里声明降档范围，不再另立标记行。
> 落点形态：<文档枢纽仓（`<repo>/<name>-workflow-ai/`）｜普通业务仓（`docs/features/`）> 二选一，随接入约定。
## 元信息
- 需求原文/页面链接：<路径或链接>；主实施仓：<仓>；相关系统/仓库：<仓>；UI 轨：<已启用（spec/ui/visual.md + design/ui/visual.md）｜未启用>；最后更新时间：<日期>
- 落点基准：<任务表代码落点相对 <主实施仓根（默认）｜<name>-workflow-ai/｜本批次目录>>——不声明时按主实施仓根解析，跨基准书写的路径一律写全前缀
- 视觉基线：<A 复用本仓既有基线（<组件/主题/token 源文件 path>）｜B 移植自 <仓/页面>｜C 冷启动新建基线 v1｜`N/A: 无 UI 改动`>
- 原型：<形态 A（目标仓已维护原型库：批次 `prototype/index.html` 只做入口页）｜形态 B（确无原型库：批次 `prototype/index.html` 即正文）｜`N/A: 无用户界面`｜`N/A: 复用 <页面> 既有结构（仅限完全复用且无界面改动）`>——判据与入口页/依赖闭包要求见 `templates/feature/prototype/README.md`
- 原型基线：<原型正文 `path@revision`（可解析的提交号；形态 A 与入口页登记的一致，跨仓写 `<repo>@<revision>:<path>`）；目标页面实现 `path:line@revision`；若沿用上一版，再列上游 feature 的 `prototype/index.html@revision`；全新页面写「新建」；无 UI 写 `N/A: 原因`>
- 埋点：<本期新增 n 个事件（design/fe §1.7）｜复用既有事件 <事件名>｜`N/A: 理由`>
## 段落映射
| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 或指向本目录之外的活文档 |
| spec | `spec/{be,fe,qa}/` | 不适用写「—」 |
| design | `design/{be,fe,qa}/` | 不适用写「—」 |
| plan | `plan/execution.md` | 目标仓有自己的计划约定时指向它 |
## 推进进度
> 规则：完成即将行首 ☐ 改 ☑；不适用改 ☑ 并写 (N/A: 原因)；评审类门禁只能由独立评审勾选。
### 1. Proposal [PM]  <填：☐/☑ 主稿、业务补充（按需）>
### 2. Spec [按角色]  <填：BE/FE/QA/UI 各条；勾选=起稿并完成反审登记，≠阶段完成>
### 3. 需求评审 [门禁]  <填：☐ 待独立评审；阻塞项全关后勾选>
### 4. Design [按角色] <填：BE/FE/QA/UI 各条（草案标注）>
### 5. 技术方案评审 [门禁] <填：☐；前置=需求评审门>
### 6. Plan [执行契约] <填：☐/☑ plan/execution.md 起稿>
### 7. 实施与验证 / 8. 收口 <填：逐条；实施后按任务回写证据>
## 当前步骤 <填：1–3 行：下一步、阻塞项；由 agentflow 文档链生成时注明>
## 模块进度总览 <填：| 模块 | 负责人 | 状态(☐◐☑⚠—) | 做到哪 | 还差什么 |>
## 当前实施仓与分支基线（指针）/ ## 代码修改落库映射 <填：分支基线只写指针指向 `plan/execution.md`「分支策略」节基线表（该表是唯一权威，此处不维护第二份）；落库映射开工后回写 commit/分支>
本 feature 文档链由 agentflow 文档链方法生成（<日期>）
