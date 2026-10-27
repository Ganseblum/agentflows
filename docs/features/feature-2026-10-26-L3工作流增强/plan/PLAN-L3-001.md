---
plan_id: PLAN-L3-001
plan_version: 0.1.0
status: approved
objective: 实施十四项L3吸收建议，集中执行规则与证据工具，按风险裁剪文档并保持回归和安装生成树可用
recorded_at: 2026-10-26T15:15:28.124Z
updated_at: 2026-10-27T11:26:13+08:00
---

# L3 工作流增强执行计划

> 执行负责人按用户已明确的十四项实施授权批准本执行契约。候选文件已准备，接受状态以实际检查及任务证据为准；独立评审未被材料存在或自查替代。

输入为本批提案、规格及设计：`proposal/proposal.md`、`spec/be/backend.md`、`spec/qa/acceptance.md`、`design/be/backend.md`、`design/qa/testing.md`。实现前须关闭本批 README 的需求评审和技术方案评审；计划批准及执行状态由执行负责人回写。

## 分支策略

| 仓库 | 基线提交 | 工作分支 | 写入与集成约束 |
| --- | --- | --- | --- |
| agentflows | `50cf8ad324c850a4cfeedbba55c6cedc310d336f` | `codex/l3-workflow-enhancement` | 主工作树为隔离检出；方法文档实现使用独立工作树。按文件范围交付和审查差异，不直接合并、提交、推送或重装。 |
| 一次性验证项目 | 从上述受信检出复制 | 不创建发布分支 | 故障注入和变异仅在 `/tmp` 副本；不得用 checkout、restore 或 clean 撤销真实树上的工作。 |

落点基准为本仓根目录。用户已要求全部补齐、增强及合理结构改造；此授权不包含发布、远端写入、宿主安装或全局指令写入。受保护面只按本批明确设计修改，实际差异仍须独立评审。

## 进展概览

总任务 8 项；状态与原始证据只在下表维护，本文不另复制计数。

| 阅读视角 | 当前材料 | 后续范围 | 可验证的交付效果 |
| --- | --- | --- | --- |
| 使用者 | 执行协议、六组提示词和分档入口 | 本地候选可审查；宿主升级另行进行 | 行为先测试、既有选择复用、复杂任务保留设计与评审 |
| 实现者 | 单一证据工具与模板已实现 | 无本批未完成代码任务 | 输入绑定、报告核对、依赖、补测与托管保护均有回归 |
| 交付验证 | 原始检查、测试记录与独立批准 | 仅最终记录一致性核对 | 源面/生成树一致，真实runner与关键反例可复跑 |

本地候选实现已获独立批准。主要边界为实际宿主未安装、平台兼容未跨机运行、方法疗效未测量；不将这些边界写成已验证。本批尚未提交，证据不能靠尚不存在的Git历史恢复，因此保留本批材料供审查，待进入Git历史后再按既有归档规则处理。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 角色 | 关联 design | 可验证交付效果 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | 采集基线，设计CLI冒烟与关键失败用例，先运行目标失败检查 | P0 | `docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/baseline.txt`；待核实（本任务创建）`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/plan-2026-10-26-001.md`；待核实（本任务先写目标测试）`tests/test_workflow.py` | — | 测试设计者、执行负责人 | 技术方案 §3–5；验证方案 §关键负例 | 用例关联验收；目标检查因能力缺失而失败，缺依赖或零用例不算有效失败 | ☑ 已完成 | `docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/baseline.txt`、`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/target-red.txt`；真实准备30项目标检查，入口未实现时失败，基线问题未被算成通过 |
| T02 | 实现单一证据工具及纯函数模块 | P0 | 待核实（本任务创建）`skills/agentflow/scripts/workflow.py`、`skills/agentflow/scripts/workflow_lib/` | T01 | 工具实现者 | 技术方案 §2–6 | seal、verify、run、inventory及单文件托管命令符合字段、路径、退出码和原始证据契约 | ☑ 已完成 | `skills/agentflow/scripts/workflow.py`、`skills/agentflow/scripts/workflow_lib/snapshots.py`、`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/review-002-requested-target.txt`；绑定、报告、依赖、补测及托管路径均通过独立复核 |
| T03 | 集中执行协议，缩短入口并消除角色与指南的同义重复 | P1 | 待核实（本任务创建）`skills/agentflow/references/execution.md`；`skills/agentflow/SKILL.md`、`skills/agentflow/references/contracts.md`、`skills/agentflow/references/test-records.md`、`skills/agentflow/references/roles.md`、`docs/quickstart.md`、`docs/system-guide.md` | T01 | 方法实现者 | 技术方案 §2、§6 | 八项方法增强有单一权威，六组提示词可使用；保留角色及独立评审，不引入第二状态系统 | ☑ 已完成 | `skills/agentflow/references/execution.md`、`docs/quickstart.md`、`docs/features/feature-2026-10-26-L3工作流增强/reviews/review-2026-10-27-002.md`；方法单一权威，六组入口提示词与角色指针已核对 |
| T04 | 落实可判定轻量档与完整档，更新模板并保留高风险边界 | P1 | `skills/agentflow/references/document-chain.md`、`skills/agentflow/templates/feature/README.md`、`skills/agentflow/templates/feature/plan/execution.md`、`skills/agentflow/templates/testing/plan.md`、`skills/agentflow/templates/testing/run.md`、`skills/agentflow/references/hosts.md` | T03 | 方法实现者 | 技术方案 §2、§6；验证方案 §关键负例 | 轻量采用README单文件：六条适用性与依据、需求验收、带代码落点的实施证据、风险恢复；risky或明确整套文档请求仍走完整链 | ☑ 已完成 | `skills/agentflow/templates/feature/lightweight.md`、`skills/agentflow/references/document-chain.md`、`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/review-002-requested-target.txt`；完整档保留，轻量冲突声明反例通过 |
| T05 | 完成回归、文档分档判定及门登记，并修复已观察的四项ruff问题 | P0 | 待核实（最终登记）`tests/test_workflow.py`；`tests/test_doc_chain.py`、`tools/lab/docchain/checks.py`、`tools/lab/docchain/selftest.py`、`tools/lab/gate/common.py`、`tools/lab/gate/checks.py`、`tools/lab/docchain/cli.py`、`tools/lab/gate/manifests.py`、`protected-paths.txt` | T02、T03、T04 | 测试与门维护者 | 技术方案 §3–6 | 原生报告、漂移、路径、依赖、轻量误降档及托管负例均被钉住；新测试同步声明和保护；不减少旧测试或放宽原门换绿 | ☑ 已完成 | `tests/test_workflow.py`、`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/repair-check-01-all.txt`、`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/review-mutations.txt`；全套门与58项目标回归通过，四组指定变异被捕获 |
| T06 | 按用例库真实运行CLI的成功与失败路径，复核覆盖 | P0 | `skills/agentflow/scripts/workflow.py`；待核实（本任务创建）`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/cli-e2e.txt` | T02、T03、T04、T05 | 测试执行者 | 技术方案 §4–5；验证方案 §3–17 | 一次性项目真实runner先失败后通过；空/旧/重复/跳过报告、漂移、依赖及托管冲突按设计拒绝；逐用例保留实际输出与退出码 | ☑ 已完成 | `docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/run-2026-10-27-001.md`、`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/native-e2e-review-002/commands.txt`；10组用例及源码/生成树真实Node Red→Green |
| T07 | 对冻结差异执行独立评审，限定修复后复审 | P0 | 待核实（本任务创建）`docs/features/feature-2026-10-26-L3工作流增强/reviews/review-2026-10-26-001.md`；必要的修复仅限已评差异 | T06 | 独立评审者、相应修复者 | 技术方案 §7–8 | 需求、设计、实际差异和端到端证据一致；作者不批准自己实现；未获批准不称完成 | ☑ 已完成 | `docs/features/feature-2026-10-26-L3工作流增强/reviews/review-2026-10-27-001.md`、`docs/features/feature-2026-10-26-L3工作流增强/reviews/review-2026-10-27-002.md`；首轮changes_requested，限定修复后独立approved，不倒填事前批准 |
| T08 | 本地版本收口、重建生成树，完成最终证据和决策记录 | P0 | `plugin.json`、`marketplace.json`、`.zcode-plugin/plugin.json`、`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`CHANGELOG.md`、`packaging/runtime/`、`index.md`；待核实（写前确认编号）`episodes/2026-10-26/EP-20261026-001.json` | T07 | 执行负责人 | 技术方案 §7；验证方案 §覆盖复核 | 五份版本一致、生成树可运行同一CLI、全套检查及本批文档链通过；episode记录评审各轮及未验证边界，不提交、发布或重装 | ☑ 已完成 | `packaging/runtime/plugin.json`、`docs/features/feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/evidence/repair-check-04-generated.txt`、`episodes/2026-10-27/EP-20261027-001.json`；本地版本与生成树一致；未提交、发布或重装 |

测试先行不形成依赖环：任务 T01 先提供最小用例设计与失败测试；任务 T05 对完整回归及门登记作最终验收。因此测试文件可以在任务 T02 的实现之前编写，任务 T05 并不因文件已经出现而置为完成。执行负责人是任务状态与证据列的唯一写入者。

### 未决项

无阻塞性产品未决项。十四项吸收及合理去重已有明确授权，不再次登记同一授权问题。

尚未生成的文件已经在代码落点列标为待核实；创建后以真实路径替换待核实说明，不以空目录或占位文档计为完成。评审记录及episode写入前检查当天编号，存在同名文件时使用下一编号而不覆盖。

## 接口与共享机制

| 机制 | 注册点或权威位置 | 实施约束 |
| --- | --- | --- |
| 执行入口 | 新 `skills/agentflow/scripts/workflow.py` 及 `workflow_lib/` | 只执行精确argv；计划JSON仅作证据，不批准计划、不回写任务或Bug状态 |
| 记录与角色 | `skills/agentflow/references/contracts.md`、`skills/agentflow/references/test-records.md`、`agents/test-planner.md`、`agents/test-executor.md`、`agents/reviewer.md` | 原状态枚举与独立性保留，角色不因文本去重合并 |
| 文档档位 | `skills/agentflow/references/document-chain.md`、`tools/lab/docchain/checks.py` | 轻量仅限六条条件均为是且有依据；完整文档请求和risky边界不可降档；存量记录不追改 |
| 测试及保护集合 | `tools/lab/gate/common.py` 的 `EXPECTED_TEST_FILES`、`REQUIRED_PROTECTED_PATHS`；`protected-paths.txt` | 新测试和承重执行工具进入相应声明；禁止弱化旧检查以接受本批 |
| 摘要及授权对象 | 技术方案 §3–4；`tools/lab/artifact_digest.py` 的已有路径与执行位约定 | 授权基线与最终执行快照分开；合法允许范围改动可验证，计划及越界变化拒绝 |
| 托管块 | `skills/agentflow/references/hosts.md` | 备份、块外保留、幂等和加载证明继续适用；仅增强写前预览绑定 |
| 安装生成树 | `packaging/build_runtime.py` 的 `RUNTIME_DIRECTORIES`、`RUNTIME_SUBTREES`；`tools/lab/gate/manifests.py` | 整树交付现有scripts路径，重建后逐字节检查；从生成树真实调用，不把源码可用当安装可用 |

执行工具没有框架拦截器、页面路由或服务端中间件；其共享入口是CLI、文件与子进程。外部平台、网络发送、UI和数据库均为 N/A：本批没有这些能力。

### 关键路径步骤

| 顺序 | 参与方 | 操作与依据 | 失败出口 |
| --- | --- | --- | --- |
| 1 | 任务负责人及既有计划 | 固定行为验收、精确命令和允许写范围；技术方案 §3 | 未决语义或必要授权缺失只阻止依赖步骤 |
| 2 | 证据工具 | seal绑定计划与授权基线，输出指纹 | 路径或输入非法退出2 |
| 3 | 实现者及证据工具 | 允许路径实现后verify检查计划、HEAD和越界变化 | 漂移或越界退出3，不执行命令 |
| 4 | 证据工具及原生runner | 固定最终执行快照，运行精确argv，收集新报告 | 局部失败隔离依赖；共同预检失败阻止依赖者 |
| 5 | 证据工具 | 核对前后快照、具名用例和原始输出 | 失效报告不计通过，coverage保持待复核 |
| 6 | 记录者与独立评审者 | 结果回写既有记录，复核断言和遗漏 | 未通过必需检查或独立评审不接受 |

### 异常矩阵

| 路径与失败模式 | 检测 | 处理 | 重试方、次数及退避 | 幂等前提 | 可观察结果 |
| --- | --- | --- | --- | --- | --- |
| 封存或运行：计划、HEAD或越界源变化 | 指纹与文件差集 | 拒绝旧对象 | 执行负责人核实后重新封存1次；无自动重试或退避 | 封存与检查只读，不重复有副作用命令 | 退出3并点名变化 |
| 测试：空、旧、重复、跳过、缺失或损坏报告 | 本次报告与精确用例映射 | 不计通过 | 实现者修正后在新证据目录执行1次；无自动重试 | 原始输出保留，旧报告不复用 | 失败或未验证及具体原因 |
| 运行：命令超时 | 显式有界timeout | 终止任务并阻止依赖，独立节点继续 | 不自动重试；环境恢复后由执行负责人新发一次运行，无退避 | 不确定副作用先核实 | 超时原因、实际输出及剩余节点 |
| 依赖：共享预检失败 | depends_on | 全部真实依赖停止，无依赖任务继续 | 环境维护者修复后重新执行1次；不盲目循环 | 同一预检使用同一输入 | 阻塞引用共同前置，不伪装通过 |
| 运行：测试期间输入改变 | 前后最终快照 | 本次证据失效并停止后续命令 | 核实并稳定输入后新运行1次；无自动退避 | 输入稳定，原始证据不改写 | 退出3及变化列表 |
| 托管：手改、预览过期或模式变化 | 原字节与执行位摘要 | 拒绝覆盖并保留用户内容 | 用户差异明确后由操作者新预览1次；无自动重试 | 写前目标仍匹配原预览 | 具体目标与冲突 |
| 托管：替换或读回失败 | 文件错误及写后摘要 | 报告实际写入和备份；不覆盖随后新改动 | 不自动重试；仅当前内容等于刚写入内容时允许受控恢复 | 备份为普通文件且恢复对象未被他人改变 | 实际路径、残留状态及恢复信息 |
| 回调失败 | N/A：CLI同步命令，无异步平台回调 | 不新增回调协议 | N/A：无回调重试 | N/A | 不宣称外部任务已完成 |

### 发布顺序与回滚点

| 顺序 | 本地动作 | 回滚或恢复点 |
| --- | --- | --- |
| 1 | 记录基线、测试用例与目标失败 | 保留基线与已发生输出，未开始的实现不称完成 |
| 2 | 工具与方法分别实现后核对实际差异 | 只移除或恢复本批明确改动；不重置真实树或丢弃用户工作 |
| 3 | CLI、托管与文档分档反例验证后独立评审 | 失败限定修复并新一轮复审，历史证据保留 |
| 4 | 本地版本与生成树同步，最终完整检查 | 源面与生成树成组恢复到已验证内容，重跑相同检查确认恢复 |

实际提交、推送、发布和宿主重装不在本计划内。没有数据迁移或跨部署单元发布，无不可逆迁移步骤。

### 评审门

| 门 | 时机 | 通过条件 |
| --- | --- | --- |
| 需求与技术方案 | 实现前 | 本批 README 对应检查关闭，验收及字段/失败语义一致 |
| 计划批准 | 分派实现前 | 由执行负责人显式将proposed置approved并追加变更记录，不由计划作者代批 |
| 实现与门变更 | 原生CLI与失败路径已经执行后 | 独立评审冻结差异、原始检查及用户路径；限定修复后复审 |
| 本地收口 | 生成树重建后 | 实际文件完整门与文档链通过，计划及目标表状态按证据聚合 |

## 验证命令

下列命令从本仓根执行；解释器必须装有 `requirements-dev.txt` 中的固定依赖。每条命令的逐字输出、退出码和实际版本落本批 `testing/agentflow-workflow/evidence/`，不是仅留临时目录。

| 命令或检查 | 覆盖与预期 | 对应验收 |
| --- | --- | --- |
| `python3 tools/lab/validate.py all` | 实际文件全套检查；初始结果保留，完成时全部通过；缺依赖不伪装绿色 | G4-AC-01 |
| `python3 -m unittest discover -s tests -p test_workflow.py` | 目标测试先因能力未实现而失败，再运行到通过；注册前可聚焦执行，注册后纳入all | G2-AC-01、G2-AC-02、G2-AC-03、G2-AC-04 |
| `python3 -m unittest discover -s tests` | 原回归与新增回归均通过，不减少测试、不使用skip换绿 | G4-AC-01 |
| `python3 tools/lab/doc_chain.py docs/features/feature-2026-10-26-L3工作流增强` | 本批完整链通过；轻量正反例另在一次性副本验证 | G3-AC-01、G3-AC-02 |
| `python3 tools/lab/doc_chain.py --self-test` | 原判别夹具与新档位反例通过，无缩水或无效统计 | G3-AC-01、G4-AC-01 |
| `python3 skills/agentflow/scripts/workflow.py --help` | 实现后显示六个子命令及输入边界，不触发执行 | G2-AC-01 |
| 按测试计划smoke用例执行 `seal → verify → run` 及托管命令 | `/tmp` 项目真实runner先目标失败后通过；精确输入、退出码和逐用例结果对应 | G2-AC-01、G2-AC-02、G2-AC-03、G2-AC-04 |
| `python3 packaging/build_runtime.py` | 重建现有安装面，不安装宿主 | G4-AC-01 |
| `python3 packaging/runtime/skills/agentflow/scripts/workflow.py --help` 并从生成树重跑同组CLI冒烟 | 生成树能执行同一工具，实际结果与源面一致 | G4-AC-01 |
| `python3 tools/lab/validate.py manifests` | 五份版本及源面/生成树一致 | G4-AC-01 |

有用户可观察命令行能力，故测试用例库由任务 T01 明确设计，任务 T06 按其smoke和失败矩阵执行；原始结果是实现评审的输入。无UI线框或埋点任务：本批没有图形界面和网络事件。宿主实际加载、Windows/Linux及外部平台未运行时保留未验证，不以本机CLI结果替代。

## 残余风险

| 风险 | 触发信号 | 处置与责任 |
| --- | --- | --- |
| 同权限进程伪造报告或原始测试断言无效 | 用例报告虽匹配但断言或真实入口缺失 | 独立评审复核测试与公开入口；工具不宣称沙箱或安全隔离 |
| 托管检查与替换之间的并发竞争 | 其他进程同时写同一目标 | 操作者串行管理同一文件；拒绝可观察漂移，保留备份，不宣称跨文件事务或恶意并发原子锁 |
| 轻量条件误判导致设计缺失 | 未决行为、跨层契约或risky触发项被遗漏 | 执行负责人升级完整档；判别负例由独立评审核对 |
| 文本已改但实际宿主仍用旧快照 | 源面与当前安装摘要不同 | 本批仅验证本地生成树；需要实际重装与新会话验证时另按授权执行，不先称宿主已生效 |

## 变更记录

- 2026-10-26T15:15:28.124Z · 创建proposed计划；八项任务保持未开始，基线文件存在未被当作目标失败或完成证据。

## 实施范围补充

以下是同一目标必需的实际落点补充，不改写已完成任务定义：

- T03/T04：`AGENTS.md` 的分档入口；角色文件的执行协议指针；`skills/agentflow/templates/feature/lightweight.md` 的单文件材料；`skills/agentflow/references/workflow-tool.md` 的CLI字段权威，以及测试请求/补测映射JSON模板。运行规则不在指南中再复制。
- T05：`tools/lab/validate.py` 把新运行工具纳入静态检查；`tools/lab/docchain/constants.py` 登记轻量检查；`tools/lab/gate/workspace.py` 按既有evidence/scratch目录契约接受其内部原生runner子目录，任意其他testing目录仍拒绝。两项嵌套布局回归先失败再修复，不靠移除原始证据转绿。
- T06：真实Node测试已在源码及生成树运行；具体日志保留在本批evidence原生运行目录，后续执行记录逐用例引用。
- T08：本地候选版本与生成树准备是可审查差异的一部分；正式接受及最终结束仍依赖T07，不把准备阶段当成已发布或已安装。

- 2026-10-27T10:51:41+08:00 · 执行负责人批准执行契约并记载实际候选准备；未倒填需求或设计的独立批准。最终独立评审逐项核对实际差异及已发生时序。

## 实际交付与过程偏差

- 实际交付日为2026-10-27：T06原规划的单文件日志由 `testing/agentflow-workflow/run-2026-10-27-001.md` 与 `evidence/native-e2e-review-002/` 承载；T07评审为 `reviews/review-2026-10-27-001.md` 和 `reviews/review-2026-10-27-002.md`；T08使用 `episodes/2026-10-27/EP-20261027-001.json`。不为匹配预估日期补造历史记录。
- 候选准备早于正式计划批准及独立需求/设计评审，这是本批实际顺序偏差。终审检查了提案、验收、设计和实际实现；完成后关闭检查项，不倒写成事前获批。首轮发现两项P1及一项P2，限定修复后第二轮批准。
- T01初始入口缺失记录不单独证明行为Red；有效失败以真实Node断言及后续修复反例为准，见测试执行记录。测试与门未通过删除用例或摘标记换绿。
- T03列出的contracts与T05列出的既有test_doc_chain无需修改，沿用原契约；T04新增轻量模板的实际位置已在范围补充声明。仅状态和证据列回写，不追改任务定义。
- 2026-10-27T11:26:13+08:00 · 本地实现、独立复审及逐项证据完成；随后只做收尾记录复核和最终实际文件全套检查，不扩展代码范围。
