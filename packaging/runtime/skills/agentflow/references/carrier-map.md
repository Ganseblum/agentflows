# 载体归属表 — 每条跨载体规则的唯一权威载体

> 用途：回答「这条规则以哪份文件为准，其它地方出现时应该是指针还是副本」。
> 这张表不是第二条规则正文：它只登记归属，不复述条款内容。
> 机器核验：`python3 tools/lab/validate.py docs`（`gate/docs.py` 的 `validate_carrier_map`）
> 逐行断言权威路径存在、锚点在该文件里命中、`agentflow:<role>` 指针可解析、副本处置列非空。
> 立表来源：2026-10-29 全面修正与瘦身批 T07（承接 2026-10-28 治理批 T01 的载体归属表），
> 起因是 2026-10-28 评测报告 §二 B4「同一规则维护 2–3 份，且用『改一处就改另一处』的纪律对冲重复」。

## 1. 归属表

| 规则 | 权威载体 | 锚点 | 副本处置 |
| --- | --- | --- | --- |
| 十步主工作流与每步义务 | `skills/agentflow/SKILL.md` | ## 运行工作流 | 其它载体只引用步骤号，不重述该步动作 |
| 十四条硬边界 | `skills/agentflow/references/contracts.md` | ## 硬边界 | SKILL 与各角色文件只按编号引用，不复述条款正文 |
| 评审能力分级 L0/L1/L2 与三条不变式 | `skills/agentflow/references/contracts.md` | ## 评审能力分级 | SKILL 第 8 步只写「先探测并记录 `review_tier`」，档位定义不出现第二遍 |
| 简报与 worker 结果字段 | `skills/agentflow/references/contracts.md` | ## Worker 任务简报 与 ## Worker 结果 | 角色文件写「按契约的哪些字段产出」，不另立字段表 |
| 判断词的可判定定义（小改动 / risky work / 相同原因） | `skills/agentflow/SKILL.md` | ## 判断词的可判定定义 | `skills/agentflow/references/roles.md` 与契约只指向这三条，不各写一套阈值 |
| 角色路由与工作链默认入口 | `skills/agentflow/references/roles.md` | ## 工作链 | SKILL 不复述路由表；角色文件不重复「何时选我」的整段 |
| 文档链阶段骨架、档位判据与阶段门 | `skills/agentflow/references/document-chain.md` | ## 门 与 ## 质量密度下限（机器检查） | 判据正文只在这一份里；细则拆分（原治理批 T04）本批未实施，登记为计划 ☐ 任务，不在表里指向尚不存在的文件 |
| 文档链 C 判据的逐条口径（执行体一侧） | `tools/lab/docchain/checks.py` | def batch_traceability_findings | 人读口径同上，不复述代码；`tools/lab/` 不随插件全量交付，只发链检查器（`packaging/build_runtime.py` 的 `RUNTIME_SUBTREES`） |
| 测试计划与运行记录形态、bug 状态联动 | `skills/agentflow/references/test-records.md` | ## 契约 与 ## Bug 回归用例与状态联动 | SKILL 的自动化测试节只指路径，不重复联动表 |
| 开工预检、选测、证据复用与失败分流 | `skills/agentflow/references/execution.md` | ## 环境预检与选测 与 ## 三种结论分开 | 契约与 SKILL 只引用该节，不再列一份测试纪律 |
| 证据工具 seal / verify / run 的接口 | `skills/agentflow/references/workflow-tool.md` | ## 命令 | 批次 `testing/` 写用法实例，不重定义命令语义 |
| 埋点评审清单 | `skills/agentflow/references/telemetry.md` | ## 评审门检查清单 | SKILL 的埋点节明写「本文不复述那十条」，只指路径 |
| 仓库整体审核档位与铁律 | `skills/agentflow/references/repo-audit.md` | ## 铁律 | SKILL 的审核节只列七种档位名称与入口，不抄铁律正文 |
| 宿主托管块协议（dry-run、只改块内、三项校验） | `skills/agentflow/references/hosts.md` | ## 托管块协议 与 ## 版本与漂移 | SKILL 的宿主级接入节只保留三条硬约束与指针 |
| 宿主级全局规则正文（跨仓纪律的文本） | `skills/agentflow/templates/host/global-rules.md` | `<!-- agentflow:begin v{{version}} -->` | 目标仓的托管块是该文件的安装态副本：改模板必须同时 bump 插件版本并重跑 Host Init，**不靠「改一处就改另一处」的人工记忆**（同一内容有两个物理载体且无法指针化，同步机制是版本号，见 `skills/agentflow/references/hosts.md` 的漂移判定） |
| 本仓质量门命令与接受产物前置 | `AGENTS.md` | ## 接受任何产物之前 | `tools/lab/README.md` 写各门项职责，不重复命令清单；README 与 index 不复述门项数 |
| 本仓记录根、命名与落点 | `AGENTS.md` | ## 在本仓库工作 | `docs/issues/README.md`、`docs/features/README.md` 等各写本域的形态细节，顶层归属只在 AGENTS |
| 计划形态与机器断言（看板、任务枚举、分支策略） | `docs/features/README.md` | ## 计划形态 | `skills/agentflow/templates/feature/plan/execution.md` 是可复制骨架，不另写一份断言表 |
| 缺陷记录契约与状态机 | `schemas/bug-record.schema.json` | `regression_status` | `skills/agentflow/templates/issue/issue-template.md` 是填写式镜像，字段口径以 schema 为准 |
| 评审记录契约（含 `review_tier` / `dispatch_errors`） | `schemas/review.schema.json` | `伪降级护栏` | 链契约与 SKILL 只写「按评审契约落记录」，不复制字段表 |
| 实验、快照与不可逆 git 操作的保全纪律 | `AGENTS.md` | ## 实验与恢复 | `skills/agentflow/references/execution.md` 只写执行侧的证据要求，不重抄快照生命周期 |
| 表达与沉淀纪律（白话优先、反复提醒要落成条款） | `AGENTS.md` | ## 表达与沉淀纪律 | 链契约的表达节只补「代号裸用 / 模式词分域」两种文档链形态的判据 |
| 首次接入（Init）六问与三句门条款 | `skills/agentflow/SKILL.md` | ## 首次接入（Init） | `skills/agentflow/templates/hub/repo-rules.md` 是必产出载体：固定块写死判据，槽位由 Init 填充，不另立第二份接入清单 |

## 2. 表自身的规则

- **一行一条规则**：同一规则需要两个物理载体（如上表的宿主全局规则正文，安装态无法指针化）时，
  在「副本处置」列写明同步机制是什么（版本号、重建脚本或人工重跑），不写「记得同步」。
- 新增或移动权威载体时，同批改这张表；`validate.py docs` 会逐行核验，**表滞后即红**，
  不留「写完即过期」的空白（这正是 2026-10-29 实测的第 F1/F4 类形态）。
- 锚点写成文件里真实存在的标题字面量或标记注释；写不出锚点的行等于没写——检查器会按
  「锚点未命中」判红，而不是放过。
- 判据的机器执行体（`tools/lab/docchain/`、`tools/lab/gate/`）不进这张表：它是实现，不是载体。
