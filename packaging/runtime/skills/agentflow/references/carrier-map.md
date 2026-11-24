# 载体归属表 — 每条跨载体规则的唯一权威载体

> **加载者**：`skills/agentflow/SKILL.md` 按需包「载体归属」行；改任何跨载体规则之前先查这张表。
> 用途：回答「这条规则以哪份文件为准，其它地方出现时应该是指针还是副本」。
> 这张表不是第二条规则正文：它只登记归属，不复述条款内容。

## 1. 归属表

| 规则 | 权威载体 | 锚点 | 副本处置 |
| --- | --- | --- | --- |
| 十步主工作流与每步义务 | `skills/agentflow/SKILL.md` | ## 运行工作流 | 其它载体只引用步骤号，不重述该步动作 |
| 十四条硬边界 | `skills/agentflow/references/contracts.md` | ## 硬边界 | SKILL 与各角色文件只按编号引用，不复述条款正文 |
| 评审能力分级 L0/L1/L2 与三条不变式 | `skills/agentflow/references/contracts.md` | ## 评审能力分级 | SKILL 第 8 步只写「先探测并记录 `review_tier`」，档位定义不出现第二遍 |
| 简报与 worker 结果字段 | `skills/agentflow/references/contracts.md` | ## Worker 任务简报 与 ## Worker 结果 | 角色文件写「按契约的哪些字段产出」，不另立字段表 |
| 定位即预算（读取定位与上限） | `skills/agentflow/SKILL.md` | ## 评审简报的定位义务 | `contracts.md` 只留一条判据与指针，详细口径不复制第二份 |
| 调度判断词（小改动 / risky work / 相同原因，材料判据引用文档链） | `skills/agentflow/SKILL.md` | ## 判断词的可判定定义 | `skills/agentflow/references/roles.md` 与契约只指向这三条，不各写一套阈值 |
| 角色路由与工作链默认入口 | [角色路由](roles.md) | 工作链、阶段与角色 | 主技能与角色索引按需导航；写范围以角色文件和具体简报为准 |
| 文档阶段骨架、唯一材料档位与计划状态 | [文档交付链](document-chain.md) | 文档档位、阶段评审、计划状态 | 项目自有载体按阶段映射；角色、模板引用同一判据 |
| 测试计划与运行记录形态、bug 状态联动 | `skills/agentflow/references/test-records.md` | ## 契约 与 ## Bug 回归用例与状态联动 | SKILL 的自动化测试节只指路径，不重复联动表 |
| 开工预检、选测、证据复用与失败分流 | `skills/agentflow/references/execution.md` | ## 环境预检与选测 与 ## 三种结论分开 | 契约与 SKILL 只引用该节。可复跑启动步骤落工程基线或目标仓运行手册，批次计划引用，执行记录写实际结果 |
| 开工提问（六要素、红线、证据层级、任务简报） | `skills/agentflow/references/intake.md` | ## 六要素 | SKILL 的 Intake 步骤只写指针；角色文件不复述六要素，验收层级以本文件与 `test-records.md` 为准；宿主全局块不再复制六要素，由项目规则与 skill 承载 |
| 设计压测（设计树、前沿、逐轮推荐、收尾门） | `skills/agentflow/references/grilling.md` | ## 设计树与前沿 | SKILL 的架构门与 `technical-director.md` 只写指针；`design/be` §1.2.9 与 `design/fe` §1.2.9 是它的**固定落点**（内嵌核对表，确保每次设计都过一遍前沿，不再依赖「模型自己想起来读」） |
| 首次接入细则（脚本先行、六问、接入约定、基线对齐） | `skills/agentflow/references/init.md` | ## 0. 脚本先行，AI 只填项目事实 | SKILL 的 Init 节只留三条不变式与本文件指针；接入约定正文以 `templates/hub/repo-rules.md` 为准、工程基线以 `templates/engineering/baseline.md` 为准 |
| 证据工具 seal / verify / run 的接口 | `skills/agentflow/references/workflow-tool.md` | ## 命令 | 批次 `testing/` 写用法实例，不重定义命令语义 |
| 埋点评审清单 | `skills/agentflow/references/telemetry.md` | ## 评审检查清单 | SKILL 的埋点节明写「本文不复述那十条」，只指路径 |
| 设计图画法（三层选图、事件号、怎么读、九列表） | `skills/design-diagram/SKILL.md` | ## 三条铁律 | **要哪些图**仍归文档链（形态判据不在此复述）；本 skill 只定画成什么样算合格。时间序/状态/ER 的骨架在 `skills/design-diagram/templates/`，报错处置在 `references/gate-findings.md`，`skills/agentflow/SKILL.md` 的入口表只留指针 |
| 评审与测试的成本分档（S/M/L 判据与配套默认纪律） | `skills/agentflow/references/execution.md` | ## 评审与测试的成本分档（按改动量定证据深度，不按轮次惯性） | SKILL 只引用风险分档与适用的预览、用户验收要求；小 UI 可用真实页面预览，不另造原型正文或分档阈值 |
| 外部文档二次评审的桥工作流（快照、`source_revision`、`provenance` 分流、记录契约） | `skills/agentflow/references/repo-audit.md` | ## 外部文档二次评审（另一套规则下产出的文档） | SKILL 的该节只留触发条件、两个升级回路与指针；四步流程不出现第二份 |
| 仓库整体审核档位与铁律 | `skills/agentflow/references/repo-audit.md` | ## 铁律 | SKILL 审核节只留指针，档位与铁律以 repo-audit.md 为准，不抄铁律正文 |
| 检索纪律（存在性结论不用裸 grep、先打印命中原文再判 PASS/FAIL） | `skills/agentflow/references/repo-audit.md` | ## 铁律 | SKILL 的 Init 节已指针化（指向 repo-rules 模板第 4 节与本铁律清单）；`templates/hub/repo-rules.md` 第 4 节是写进目标仓的安装态固定块（同步机制随版本标记重跑 Init 刷新）；全局块不再复制检索纪律，避免与项目规则重复 |
| 宿主托管块协议（dry-run、只改块内、三项校验） | `skills/agentflow/references/hosts.md` | ## 托管块协议 与 ## 版本与漂移 | SKILL 的宿主级接入节只保留三条硬约束与指针 |
| 合并收口纪律（material 合并的构建/测试/对账义务） | `skills/agentflow/SKILL.md` | ## 运行工作流 | 与 `skills/agentflow/templates/host/global-rules.md` §3/§5/§6 是同一组规则的宿主级安装态副本：SKILL 第 6 步是权威正文，模板承载跨会话安装态，同步机制 = bump 插件版本后重跑 Host Init（见 `skills/agentflow/references/hosts.md`「版本与漂移」节），不靠人工逐句比对 |
| 宿主级全局规则正文（跨仓纪律的文本） | `skills/agentflow/templates/host/global-rules.md` | `<!-- agentflow:begin v{{version}} -->` | 目标仓的托管块是该文件的安装态副本：改模板必须同时 bump 插件版本并重跑 Host Init，**不靠「改一处就改另一处」的人工记忆**。与 `templates/hub/repo-rules.md` 的关系**不是同一份内容的两份拷贝**（前者管宿主全部工作区，后者管单个目标仓的实例与槽位），重叠条款已于 2026-11-04 指针化，2026-11-10 进一步收窄：global-rules 只保留跨仓 6 条（分支、落点、合并/推送授权、证据、合并收口、评审 revision），通用行为纪律（先问再假设、检索、工具重试）由项目规则与 skill 承载；repo-rules 只留本仓可执行形态并指向本文件的 §1/§3/§4 |
| 表达与沉淀纪律（白话优先、反复提醒要落成条款） | `AGENTS.md` | ## 表达与沉淀纪律 | 文档链「表达纪律」只说明单源、证据与当前/历史区分 |
| 首次接入（Init）六问与三句约束条款 | `skills/agentflow/SKILL.md` | ## 首次接入（Init） | `skills/agentflow/templates/hub/repo-rules.md` 是必产出载体：固定块写死判据，槽位由 Init 填充，不另立第二份接入清单 |
| 缺陷记录契约与状态机 | `skills/agentflow/templates/issue/issue-template.md` | `open → fixed-pending-review → verified` | 字段口径以模板为准；如需机器校验，目标仓自行配置，不随本插件强制 |
| 文档与实施评审入口、结果与能力分级 | [委派契约](contracts.md) | 按对象核对入口、评审结果、评审能力分级 | 角色引用统一 YAML；工具按 `review_type` 渲染入口 |
| 实验、快照与不可逆 git 操作的保全纪律 | `AGENTS.md` | ## 实验与恢复 | `skills/agentflow/references/execution.md` 只写执行侧的证据要求，不重抄快照生命周期 |
| 本仓记录根、命名与落点 | `AGENTS.md` | ## 在本仓库工作 | 各目录 README 写本域的形态细节，顶层归属只在 AGENTS |
| 本仓计划形态与人工核对（看板、任务枚举、分支策略） | `docs/features/README.md` | ## 计划形态 | `skills/agentflow/templates/feature/plan/execution.md` 是可复制骨架，不另写一份断言表 |
| 安全工程与审计底线（SEC-01~SEC-10） | `skills/agentflow/references/standards/security.md` | ## 0. 适用范围与何时必查 | `review-checklists.md` 与 `reviewer.md` 指针化引用，不复述条款正文 |
| API 规范与接口契约底线（API-01~API-08） | `skills/agentflow/references/standards/api-docs.md` | ## 0. 适用范围与何时必查 | `backend-engineer.md` 与 `design/be` 模板指针化引用 |
| Git 提交与变更记录规范（GIT-01~GIT-07） | `skills/agentflow/references/standards/git-commits.md` | ## 1. 提交信息结构标准（GIT-01） | 宿主全局规则与工程基线指针化引用，不复述格式语法 |
| 视觉方向与首屏层级（FE-12） | `skills/agentflow/references/standards/frontend.md` | ## 11. 视觉方向与首屏层级（FE-12） | `spec/ui` 写结论，评审清单只引用编号；不另立视觉规范文件 |
| 设计稿还原与走查（FE-13） | `skills/agentflow/references/standards/frontend.md` | ## 12. 设计稿还原与走查（FE-13） | `design/ui` 登记设计源与证据，模板只引用编号；不复制截图流程 |
| 根因门（缺陷与异常行为） | `skills/agentflow/references/execution.md` | ## 根因门（缺陷与异常行为） | `bug-investigator` 只补输出纪律，不另写第二套根因定义 |
| 修复后沉淀（防再发） | `skills/agentflow/references/issue-tracking.md` | ## 3. 修复后沉淀（防再发） | 缺陷修复收口引用本节；不新开平行记忆文件 |
| 浏览器执行纪律（不可信页面、黑盒、证据） | `skills/agentflow/references/execution.md` | ## 执行路线与数据 | `verification-grading.md` 只定证据层级，不复制操作纪律 |
| 只读调研（非审核） | `skills/agentflow/references/repo-audit.md` | ## 只读调研（非审核） | SKILL 的审核节与角色路由只指路径，不复述调研步骤 |
| 方案发散（进入设计前） | `skills/agentflow/references/intake.md` | ## 方案发散（进入设计前） | proposal / design 模板只留「决策与备选」节，不复制发散规则 |
| PR / MR 标题、正文、拆分与合并边界（GIT-07） | `skills/agentflow/references/standards/git-commits.md` | ## 7. PR / MR 标题、正文与合并边界（GIT-07） | Plan Architect 在执行计划登记拆分结果；宿主全局块与 CI/CD 模板只引用授权边界 |
| 工程门禁盘点（已有只验证、缺失才接入） | `skills/agentflow/references/init.md` | ## 1.5 工程门禁盘点（前端项目必做） | `templates/engineering/baseline.md` 的「工程门禁现状」表是落点；不另立接入清单 |

## 2. 表自身的规则

- **一行一条规则**：同一规则需要两个物理载体（如上表的宿主全局规则正文，安装态无法指针化）时，在「副本处置」列写明同步机制是什么（版本号、重建脚本或人工重跑），不写「记得同步」。
- 新增或移动权威载体时，同批改这张表，不留「写完即过期」的空白。
- 锚点写成文件里真实存在的标题字面量或标记注释；写不出锚点的行等于没写。
