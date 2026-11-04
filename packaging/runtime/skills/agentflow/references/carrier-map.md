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
| 判断词的可判定定义（小改动 / risky work / 相同原因） | `skills/agentflow/SKILL.md` | ## 判断词的可判定定义 | `skills/agentflow/references/roles.md` 与契约只指向这三条，不各写一套阈值 |
| 角色路由与工作链默认入口 | `skills/agentflow/references/roles.md` | ## 工作链 | SKILL 不复述路由表；角色文件不重复「何时选我」的整段 |
| 文档链阶段骨架、档位判据与阶段评审语义 | `skills/agentflow/references/document-chain.md` | ## 门 | 门 1–10 只定义语义；主契约不复制细则 |
| 测试计划与运行记录形态、bug 状态联动 | `skills/agentflow/references/test-records.md` | ## 契约 与 ## Bug 回归用例与状态联动 | SKILL 的自动化测试节只指路径，不重复联动表 |
| 开工预检、选测、证据复用与失败分流 | `skills/agentflow/references/execution.md` | ## 环境预检与选测 与 ## 三种结论分开 | 契约与 SKILL 只引用该节，不再列一份测试纪律 |
| 开工提问（六要素、红线、证据层级、任务简报） | `skills/agentflow/references/intake.md` | ## 六要素 | SKILL 的 Intake 步骤只写指针；角色文件不复述六要素，验收层级以本文件与 `test-records.md` 为准；`templates/host/global-rules.md` §7 是不可指针化的安装态副本，改模板后 bump 版本并重跑 Host Init |
| 设计压测（设计树、前沿、逐轮推荐、收尾门） | `skills/agentflow/references/grilling.md` | ## 设计树与前沿 | SKILL 的架构门与 `technical-director.md` 只写指针；`design/be` §1.2.9 与 `design/fe` §1.2.9 是它的**固定落点**（内嵌核对表，确保每次设计都过一遍前沿，不再依赖「模型自己想起来读」） |
| 首次接入细则（脚本先行、六问、接入约定、基线对齐） | `skills/agentflow/references/init.md` | ## 0. 脚本先行，AI 只填项目事实 | SKILL 的 Init 节只留三条不变式与本文件指针；接入约定正文以 `templates/hub/repo-rules.md` 为准、工程基线以 `templates/engineering/baseline.md` 为准 |
| 证据工具 seal / verify / run 的接口 | `skills/agentflow/references/workflow-tool.md` | ## 命令 | 批次 `testing/` 写用法实例，不重定义命令语义 |
| 埋点评审清单 | `skills/agentflow/references/telemetry.md` | ## 评审检查清单 | SKILL 的埋点节明写「本文不复述那十条」，只指路径 |
| 设计图画法（三层选图、事件号、怎么读、九列表） | `skills/design-diagram/SKILL.md` | ## 三条铁律 | **要哪些图**仍归文档链（形态判据不在此复述）；本 skill 只定画成什么样算合格。时间序/状态/ER 的骨架在 `skills/design-diagram/templates/`，报错处置在 `references/gate-findings.md`，`skills/agentflow/SKILL.md` 的入口表只留指针 |
| 评审与测试的成本分档（S/M/L 判据与配套默认纪律） | `skills/agentflow/references/execution.md` | ## 评审与测试的成本分档（按改动量定成本，不按轮次惯性） | SKILL 的分档节只留两条不可让渡（原型前置、收口用户验收）与指针，不复制分档表 |
| 外部文档二次评审的桥工作流（快照、`source_revision`、`provenance` 分流、记录契约） | `skills/agentflow/references/repo-audit.md` | ## 外部文档二次评审（另一套规则下产出的文档） | SKILL 的该节只留触发条件、两个升级回路与指针；四步流程不出现第二份 |
| 仓库整体审核档位与铁律 | `skills/agentflow/references/repo-audit.md` | ## 铁律 | SKILL 审核节只留指针，档位与铁律以 repo-audit.md 为准，不抄铁律正文 |
| 检索纪律（存在性结论不用裸 grep、先打印命中原文再判 PASS/FAIL） | `skills/agentflow/references/repo-audit.md` | ## 铁律 | SKILL 的 Init 节已指针化（指向 repo-rules 模板第 4 节与本铁律清单）；`templates/hub/repo-rules.md` 第 4 节是写进目标仓的安装态固定块（同步机制随版本标记重跑 Init 刷新），`templates/host/global-rules.md` 第 11 节同理 |
| 宿主托管块协议（dry-run、只改块内、三项校验） | `skills/agentflow/references/hosts.md` | ## 托管块协议 与 ## 版本与漂移 | SKILL 的宿主级接入节只保留三条硬约束与指针 |
| 合并收口纪律（material 合并的构建/测试/对账义务） | `skills/agentflow/SKILL.md` | ## 运行工作流 | 与 `skills/agentflow/templates/host/global-rules.md` §3/§5/§6 是同一组规则的宿主级安装态副本：SKILL 第 6 步是权威正文，模板承载跨会话安装态，同步机制 = bump 插件版本后重跑 Host Init（见 `skills/agentflow/references/hosts.md`「版本与漂移」节），不靠人工逐句比对 |
| 宿主级全局规则正文（跨仓纪律的文本） | `skills/agentflow/templates/host/global-rules.md` | `<!-- agentflow:begin v{{version}} -->` | 目标仓的托管块是该文件的安装态副本：改模板必须同时 bump 插件版本并重跑 Host Init，**不靠「改一处就改另一处」的人工记忆**。与 `templates/hub/repo-rules.md` 的关系**不是同一份内容的两份拷贝**（前者管宿主全部工作区，后者管单个目标仓的实例与槽位），重叠的 3 处条款已于 2026-11-04 指针化：repo-rules 只留本仓可执行形态并指向本文件的 §1/§3/§4/§11，宿主未接入（无托管块）时 repo-rules 自身即为完整要求 |
| 表达与沉淀纪律（白话优先、反复提醒要落成条款） | `AGENTS.md` | ## 表达与沉淀纪律 | 链契约的表达节只补「代号裸用 / 模式词分域」两种文档链形态的判据 |
| 首次接入（Init）六问与三句约束条款 | `skills/agentflow/SKILL.md` | ## 首次接入（Init） | `skills/agentflow/templates/hub/repo-rules.md` 是必产出载体：固定块写死判据，槽位由 Init 填充，不另立第二份接入清单 |
| 缺陷记录契约与状态机 | `skills/agentflow/templates/issue/issue-template.md` | `open → fixed-pending-review → verified` | 字段口径以模板为准；如需机器校验，目标仓自行配置，不随本插件强制 |
| 评审记录契约（含 `review_tier` / `dispatch_errors`） | `skills/agentflow/references/contracts.md` | ## 评审能力分级 | 链契约与 SKILL 只写「按评审契约落记录」，不复制字段表 |
| 实验、快照与不可逆 git 操作的保全纪律 | `AGENTS.md` | ## 实验与恢复 | `skills/agentflow/references/execution.md` 只写执行侧的证据要求，不重抄快照生命周期 |
| 本仓记录根、命名与落点 | `AGENTS.md` | ## 在本仓库工作 | 各目录 README 写本域的形态细节，顶层归属只在 AGENTS |
| 计划形态与机器断言（看板、任务枚举、分支策略） | `docs/features/README.md` | ## 计划形态 | `skills/agentflow/templates/feature/plan/execution.md` 是可复制骨架，不另写一份断言表 |

## 2. 表自身的规则

- **一行一条规则**：同一规则需要两个物理载体（如上表的宿主全局规则正文，安装态无法指针化）时，在「副本处置」列写明同步机制是什么（版本号、重建脚本或人工重跑），不写「记得同步」。
- 新增或移动权威载体时，同批改这张表，不留「写完即过期」的空白。
- 锚点写成文件里真实存在的标题字面量或标记注释；写不出锚点的行等于没写。
