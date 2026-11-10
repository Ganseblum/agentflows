---
plan_id: PLAN-2026-11-05-AUDIT-FIXES
plan_version: 1.0.0
status: approved
objective: 修复 G01–G16，交付 0.41.0 源码、可复核回归及三端本地安装与 ZCode 全局既有块同步证据
recorded_at: 2026-11-05T10:48:14Z
updated_at: 2026-11-05T12:37:41Z
---

# 审计修复执行计划

## 输入与边界

| 输入 | 确切版本或证据 |
| --- | --- |
| 批次规则与已定选择 | [批次 README](../README.md)；本次工作区版本由主审在 T01 冻结原始 bytes；未提供该未提交文件的独立 revision，不编造 |
| 已接受审计 | [原报告](/Users/lihanghang1/.zcode/v2/artifacts/agentflows-design-audit-20261105-174945/AGENTFLOW-设计与可用性评估-2026-11-05.md:45) G01–G16；source_version=0.40.0，recorded_at=2026-11-05T18:14:03+08:00，source_revision 见分支表；保留修前日志及原评分 |
| 用户批准的实施方案 | [会话方案](/Users/lihanghang1/Desktop/TestProject/agentflows/.zcode/plans/plan-sess_3265d419-ff8c-444f-8a16-471640ff8138.md)；ExitPlanMode 已获用户明确批准；其中开工前 main 状态是历史事实，当前以主审分支确认及下表为准 |
| 方法参考 | `skills/agentflow/references/contracts.md`、`skills/agentflow/references/test-records.md`；宿主本角色加载插件快照 0.36.0。审计指名的失效门及矛盾规则是整改对象，不据此恢复旧 schema/大门禁 |
| 本轮证据 E | `/Users/lihanghang1/.zcode/v2/artifacts/agentflows-fixes-20261105-184849`；候选输出、修前/修后逐字输出、退出码及各轮快照保留于此，run 绑定精确路径与版本 |

不恢复已退役的大门禁、schema、运行时或常驻服务；不增加角色；no commit/merge/push/remote release。只改 `/Users/lihanghang1/.zcode/AGENTS.md` 中现有 Agentflow 块，块外逐字保留；不修改其他宿主全局文件。新增源码入口只限本计划列出的共享模块和一个跨工具回归入口，不另立记录根或文档类型。

## 分支策略

| 仓库/工作区 | 分支 | 基线 | 确认依据及用途 |
| --- | --- | --- | --- |
| `/Users/lihanghang1/Desktop/TestProject/agentflows` | `feature-audit-fixes-0.41.0` | `511b9ef7b66a4b23cb859345d1810981aa083f5b` | 主审在本次指派前已查分支；该确认供无 Bash 的计划角色使用；后续写入仍由执行者先查当前分支 |
| E 下 `candidate-init`、`candidate-review`、`candidate-execution`、`candidate-generator`、`candidate-docs` | 依次为 `feature-audit-fixes-init-0.41.0`、`feature-audit-fixes-review-0.41.0`、`feature-audit-fixes-execution-0.41.0`、`feature-audit-fixes-generator-0.41.0`、`feature-audit-fixes-docs-0.41.0` | 同上，由主审复核各工作区实际 HEAD | 五个独立候选，一处一写者；共享接口先定，调用方后集成 |

落点基准为主仓根；E 及其子目录均按上文绝对路径展开。候选代码绝不靠 merge/cherry-pick 集成：主审先保全主树未提交内容，再按逐文件显式复制清单增量集成，复跑检查后才接受；重叠文件串行处理，不整树覆盖。不运行 `git restore`、`reset --hard` 或真实树故障注入。

## 进展概览

完成 10 / 进行中 0 / 阻塞 2 / 未开始 0；统计范围为 T01–T12 的接受状态，候选已开工不计已接受。

| 范围 | 业务侧解读 | 技术侧解读 | 交付效果 |
| --- | --- | --- | --- |
| 工具可靠性 | 初始化不丢规则，审的就是声明对象，超时后没有晚写 | G01–G05/G08/G12；安全文件写、冻结 bytes、进程组清理、安装内容核验 | 同一修前反例修后通过，错误路径明确拒绝 |
| 使用规则 | 小事少写材料，行为变更仍有独立判断，验收只维护一份 | G06/G07/G09–G11/G13–G15；风险路由、授权、用例与图例收敛 | 实际生成/调用与权威规则一致 |
| 交付与效果 | 三端装对，并如实知道哪些效果已测到 | G16；49 项既有自测、四类受控任务、安装/加载分开 | 有原始记录；未实测子项保持未验证，不外推普遍提效 |

我们在哪：实现修复、独审和三端载荷同步已完成；T09剩余浏览器变体及T11部分新会话加载缺证据，整体partial。下一步：只在相关确认/环境恢复后补测，保留已完成结果。阻塞风险：环境或加载证据缺失、同因两次失败、源码与已定规则冲突均须具名上报；只阻塞相关依赖，不把摘要当验证。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 主审冻结输入并批准本计划；明确 G01–G16 与各候选精确写范围 | P0 | `docs/features/feature-2026-11-05-审计修复/plan/PLAN-2026-11-05-AUDIT-FIXES.md` |  | ☑ 已完成 | file/manual：本轮用户批准方案；主审已批准proposed计划，context.json与本计划变更记录绑定基线。 |
| T02 | 指派 test-planner 编写用例库，冻结 smoke、反例、四类项目与替身表面 | P0 | `docs/features/feature-2026-11-05-审计修复/testing/agentflows-audit-fixes/plan-2026-11-05-001.md` | T01 | ☑ 已完成 | file：25例用例v2已读并接受；四张事前冻结任务卡 representative-task-cards.md；用例已转active。 |
| T03 | init 候选先完成共享源码对齐清单，再修 G01/G02/G03/G08 | P0 | `skills/agentflow/scripts/init_workspace.py`；`skills/agentflow/scripts/workflow_lib/managed.py`；`skills/agentflow/scripts/workflow_lib/snapshots.py` | T02 | ☑ 已完成 | file/manual：init-evidence/supervisor-red-driver.log为有效修前红；supervisor-main-selftest.log 20/20；完整CLI29回归保全/冲突/Claude项通过。 |
| T04 | review 候选修 G04/G10：严格 review_bundle、冻结读取及真实受评任务子集 | P0 | `skills/agentflow/scripts/workflow_lib/review_bundle.py`；`skills/agentflow/scripts/review_snapshot.py`；`skills/agentflow/scripts/gen_review_brief.py` | T02 | ☑ 已完成 | file/manual：review-evidence/supervisor-baseline-driver.log有效OLD/NEW红；两个supervisor-main日志22/22+15/15；task-map闭包回归通过。 |
| T05 | execution 候选修 G05：POSIX 进程组统一有界清理 | P0 | `skills/agentflow/scripts/workflow_lib/execution.py` | T02 | ☑ 已完成 | file/manual：有效E8红与7项生命周期绿；首轮评审ps失败已补修，同一review-ps-replay修后无晚写；完整增量回归另见run。 |
| T06 | generator 候选修 G02/G09/G13：显式档位/轨道、路径安全、只生成所需材料 | P1 | `skills/agentflow/scripts/new_feature.py` | T03, T07 | ☑ 已完成 | file/manual：generator-evidence/supervisor-main-self-test.log 22/22；slug-boundaries.json；四类旧新版立项1/10文件对照。 |
| T07 | docs 候选按 W07 精确集收敛 G06/G07/G09/G10/G11/G13/G14/G15 | P0 | `skills/agentflow/SKILL.md`；`skills/agentflow/references/document-chain.md`；`skills/design-diagram/SKILL.md`；其余见 W07 | T02 | ☑ 已完成 | file/manual：54文件范围对账与refs通过；首轮独审消费者问题已聚焦修入，语义独审接受仍在T10，不提前记approved。 |
| T08 | 主审或显式 worker 修 G12：唯一安装库、既有 CLI/升级脚本及维护薄入口 | P0 | `skills/agentflow/scripts/workflow_lib/installation.py`；`skills/agentflow/scripts/workflow_lib/cli.py`；`skills/agentflow/scripts/upgrade-codex.sh`；`skills/agentflow/scripts/upgrade-zcode.sh`；`packaging/build_runtime.py` | T03, T07 | ☑ 已完成 | file/manual：install-verifier-checks-02.json六边界；真实两端dry-run；安装mock拒绝；review-timeout-replay修后分类JSON，最终真实安装在T11。 |
| T09 | test-executor 执行全量回归与四类受控任务，主审复跑接受；覆盖 G01–G16 | P0 | `skills/agentflow/scripts/test_tools_regressions.py`；`docs/features/feature-2026-11-05-审计修复/testing/agentflows-audit-fixes/run-2026-11-05-001.md`；E 原始证据 | T02, T03, T04, T05, T06, T07, T08 | ⚠ 阻塞 | file/api/browser：七组96/96、跨工具31/31、补充17/17已运行；首轮browser顺序样本保留。run2中TC23/24/25扩展变体未运行，原space25消失，新建替代空间问题未获明确答复。 |
| T10 | 非作者独立 reviewer 评审冻结实现与 G01–G16 关闭依据 | P0 | E 下 `review-evidence/`；本计划关联任务证据 | T09 | ☑ 已完成 | file/manual：REVIEW-TOOLS-041与REVIEW-DOCS-041各snapshot-2均approved/complete，首轮三项工具/三项规则finding均cost_replay关闭；review-decisions.json及两轮原始输出保留。 |
| T11 | 主审升 0.41.0、更新 CHANGELOG/索引、build、三端本地安装与 ZCode 既有全局块 | P0 | `./plugin.json`；`./marketplace.json`；`.zcode-plugin/plugin.json`；`.claude-plugin/plugin.json`；`.codex-plugin/plugin.json`；`.qoder-plugin/plugin.json`；`./CHANGELOG.md`；`./index.md`；`packaging/runtime/`；`/Users/lihanghang1/.zcode/AGENTS.md` | T10 | ⚠ 阻塞 | file/manual：0.41.0源/生成树/三端各102文件一致，ZCode全局内外逐字校验和新会话复述通过；Codex加载探针因usage limit退出1，Qoder仅磁盘安装未取得新会话加载证据，不宣称三端均已生效。 |
| T12 | 主审收集最终 delta 独审、逐 G 验收及完整交付结论 | P0 | 本计划；`docs/features/feature-2026-11-05-审计修复/testing/agentflows-audit-fixes/run-2026-11-05-001.md`；`docs/host-platform-facts.md`；E 原始证据 | T11 | ☑ 已完成 | file/manual：decision.md与run2逐项收口，G01–G15已修且验证，G16部分；已审工具/规则未漂移，后续仅索引/事实/验收记录；整批partial，明确剩余动作，不自动提交合并推送。 |

W07 为以下逐文件集合；候选之外的索引和批次登记由主审串行维护，未列文件先报范围变更，禁止 worker 扩写。

| 子集 | 精确文件 |
| --- | --- |
| 规则入口 | `skills/agentflow/SKILL.md`；`skills/agentflow-intake/SKILL.md`；`skills/agentflow-grilling/SKILL.md`；`skills/agentflow/references/document-chain.md`；`skills/agentflow/references/contracts.md`；`skills/agentflow/references/execution.md`；`skills/agentflow/references/intake.md`；`skills/agentflow/references/roles.md` |
| 测试与宿主 | `skills/agentflow/references/test-records.md`；`skills/agentflow/references/testcases.md`；`skills/agentflow/references/carrier-map.md`；`skills/agentflow/references/hosts.md`；`skills/agentflow/references/init.md`；`skills/agentflow/references/workflow-tool.md`；`skills/agentflow/templates/host/global-rules.md` |
| 工程与图 | `skills/agentflow/references/standards/server-side.md`；`skills/agentflow/references/standards/data-model.md`；`skills/agentflow/references/standards/frontend.md`；`skills/design-diagram/SKILL.md`；`skills/design-diagram/templates/sequence.md`；`skills/design-diagram/templates/state.md` |
| 角色消费点 | `agents/plan-architect.md`；`agents/reviewer.md`；`agents/test-planner.md`；`agents/test-executor.md`；`agents/backend-engineer.md`；`agents/frontend-engineer.md`；`agents/bug-fixer.md`；`agents/bug-investigator.md`；`agents/bug-recorder.md` |
| 模板消费点 | `skills/agentflow/templates/feature/README.md`；`skills/agentflow/templates/feature/lightweight.md`；`skills/agentflow/templates/feature/plan/execution.md`；`skills/agentflow/templates/feature/spec/qa/acceptance.md`；`skills/agentflow/templates/feature/design/qa/testing.md`；`skills/agentflow/templates/testing/plan.md`；`skills/agentflow/templates/testing/run.md`；`skills/agentflow/templates/testing/testcases.yaml.example`；`skills/agentflow/templates/issue/issue-template.md` |
| 人读说明 | `./README.md`；`docs/quickstart.md`；`docs/system-guide.md`；`docs/features/README.md`；`skills/agentflow/templates/README.md`；`skills/agentflow/templates/host/README.md` |

执行期间仅主审回写任务状态/证据及同步概览计数，最小 diff，不重写已完成任务行；修订方案另增版本并刷新主审供给的 UTC 时间。任务表不授予 worker 任何记录写入权，逐条记录路径仍由主审指派。原型/线框 N/A：本插件无新增产品 UI，不生成 design/fe 线框任务；埋点实现/验收 N/A：事件集合为空，无新增采集或事件契约。临时 UI 演练由 T02/T09 承接 browser 验收。

### 未决项

无阻塞性产品决策待拍板。测试入口、安装登记实际路径和加载可用性由 T02/T08/T11 取证，不是默认通过；事实查不到即在对应任务标阻塞并报告最小解锁条件。G16 业务效果未验证，不把计划或受控样本当成实测结论。

## 接口与共享机制

| 机制/权威 | 注册点与消费者 | 本批契约 |
| --- | --- | --- |
| bytes 托管块与单文件写 | `workflow_lib/managed.py:_replacement/preview_managed/apply_managed`；现注册 `workflow_lib/cli.py:11,78–88`；T03 接入 `init_workspace.py:build_plan/apply_plan` | 公共纯 bytes 定位/替换，扫描全部标记后只改唯一自有块，foreign/用户字节保留；单文件写沿用预期状态、临时写、备份、读回；不承诺多文件事务 |
| 路径边界 | `workflow_lib/snapshots.py:no_symlinks/relative_name/project_path`；T03/T06/T08 接入 init、立项、安装写入点 | 验证 slug/date 及全部输入输出和祖先，拒绝用户可控 symlink/junction；既有受信系统目录别名例外不扩大；完整预检先于写，manifest 最后安全写 |
| 冻结评审 | 新 `workflow_lib/review_bundle.py`，T04 在 `review_snapshot.py:make_snapshot/verify_snapshot` 与 `gen_review_brief.py:build_brief` 注册调用 | 同一严格解析器校验唯一条目、计数、相对路径/外部命名空间、size/hash；正文和 delta 从快照或固定 commit 原始 bytes 读，不回退工作树；状态仅验证受评任务及真实前置，沿用原 ID |
| 执行清理 | `workflow_lib/execution.py:_command` 的 `start_new_session` 注册点（基线 66–75 行）及 `_stop` 的全部退出调用点 | POSIX 整组 TERM→有界宽限→KILL→确认无存活同组进程，不以父进程 wait 成功替代；非 POSIX 无等效能力显式不支持，不只杀父进程后报成功 |
| 安装核验 | 新 `workflow_lib/installation.py`；T08 注册到既有 `workflow_lib/cli.py:parser/main`、两个 upgrade shell、`packaging/build_runtime.py:main` | 唯一实现 `install-verify`、`upgrade-codex`、`upgrade-zcode`；维护面薄入口；固定期望树，逐文件核验且源前后一致；本批强制 local，无隐式市场重绑/联网发布 |
| 风险、用例、状态权威 | `references/document-chain.md` 六风险路由；主 SKILL/roles/生成器/角色/模板逐消费点引用；测试语义只在 Markdown 用例库（light 为 README）；状态只在本计划 | 用户要求全材料、跨层/公开契约、权限、持久化、共享时序、不可逆任一命中即 full；静态琐碎自检，行为变更独审；YAML 只存执行参数/引用，统一 automated，run 绑定计划版本，不复制 AC/步骤/预期 |
| 隐式行为空集及覆盖 | 本批无产品路由守卫、HTTP 拦截器、会话订阅、中间件、遥测注册；现有文件/进程/加载机制由上列注册点覆盖 | T02 以入口×空/已有/漂移/冲突/重复/并发/超时/缺依赖列检查或明确未测；无异步业务回调，不默默省略完成信号失败路径 |

表内 `workflow_lib/` 均位于 `skills/agentflow/scripts/`，`references/` 位于 `skills/agentflow/`；新注册点是 to-be，接受时由主审附最终 path:line。五链路的步骤表为设计基准。

## 关键链路与异常矩阵

### 1. init / 立项（T03、T06）

| 步骤 | 调用与产物 |
| --- | --- |
| 1 | 写码前 T03 从 managed/snapshots 真实源码逐分支列 replicate / omit-with-reason / defer；未决偏离先交主审。固定源版本、目标根、hosts、既有 manifest 和目标 bytes |
| 2 | 验证名称/日期/所有路径、所有权及完整期望文件集；Claude-only 同时规划 AGENTS 依赖；dry-run 不写；new_feature 必选 --tier，full 必显式 --tracks，qa 默认，--prototype 可选，light 只 README |
| 3 | 按唯一自有 bytes 块构造全量计划；旧 Cursor/Claude 格式仅做可证明归属的迁移；冲突保留旧 owner/hash，缩小 hosts 不卸载旧所有权 |
| 4 | 完整预检后逐文件安全写，manifest 最后更新；随后 --check 读取完整期望集。重复执行保持一个自有块，用户前后哨兵及块外 bytes 相等 |

| 失败/检测 | 处理 | 重试方/次数/退避 | 幂等前提 | 用户结果 | 日志 |
| --- | --- | --- | --- | --- | --- |
| 调度超时/I/O 失败，写入或读回未完成 | 停后续写，列实际已写/未写及备份；manifest 不报完整成功 | 自动无/0/无；主审核清状态后新运行1次/无自动退避 | 逐文件预期摘要匹配，不覆盖后续用户修改 | 非零/partial，保留可恢复状态 | argv、退出码、逐文件动作/摘要/备份 |
| 重复/foreign 共存或残缺/重复自有标记 | 唯一自有块同 bytes 不写；歧义拒绝，不删附录 | 无/0/无 | 唯一归属、输入不漂移 | 幂等成功或明确 conflict 非零 | 标记位置、归属、前后哨兵比对 |
| 越界/symlink、冲突资产或缺 AGENTS 依赖 | 写前拒绝危险路径；冲突保留完整所有权，check 持续非零；依赖缺失拒绝假绿 | 主审显式解决后新运行1次/无自动退避 | 授权根安全、归属明确、旧期望集合未缩小 | 非零，仓外哨兵不变 | 全期望集、旧/新 hash、冲突清单、外部落点读回 |
| 异步回调 | N/A：同步 CLI；最终 manifest/退出码是完成信号，写失败按首行 | 无/0/无 | N/A：无业务回调 | 不出现回调成功断言 | 最终 check 与退出码 |

### 2. 冻结评审（T04、T10、T12）

| 步骤 | 调用与产物 |
| --- | --- |
| 1 | 主审列精确受评对象/任务 ID，冻结快照或可解析固定 commit；外部对象进入稳定命名空间，不按 basename 覆盖 |
| 2 | review_bundle 严格核对清单格式、条目/计数/路径/size/hash；commit 从该对象取 bytes，快照从该目录取 bytes；不依赖工作树仍存在 |
| 3 | gen_review_brief 从同一冻结对象构造内联正文/delta；带 review_scope、reviewed_revision、inline_objects、stop_rule、output_budget，检查输出附 exit |
| 4 | 独立 reviewer 读冻结对象与原生证据；e2e 在收口前已通过。批准绑定该对象；之后变化重新冻结并做 delta 复核 |

| 失败/检测 | 处理 | 重试方/次数/退避 | 幂等前提 | 用户结果 | 日志 |
| --- | --- | --- | --- | --- | --- |
| git/读取超时或对象不可用 | 不读工作树替补，不出可供批准的简报 | 自动无/0/无；主审修环境后新运行1次/无自动退避 | 原对象可读且校验一致 | blocked/非零 | 对象标识、argv、stderr、exit |
| 重放旧快照，工作树已 NEW/已删除 | 只内联 OLD 冻结 bytes；损坏则拒绝 | 无/0/无 | 快照/commit 完整且不可混源 | 同一对象可重复生成；不虚称审了 NEW | 内联原文、来源路径、冻结摘要 |
| 清单缩减/重复/碰撞/篡改或受评前置未终态 | 严格拒绝；后继评审/收口待办不作为自指前置 | 主审修清单/范围后新运行1次/无自动退避 | 完整冻结集与原计划 ID/依赖一致 | 非零或 blocked，不批准 | 冲突条目、计数、具体任务及校验错误 |
| reviewer/完成信号失败或缺独审 | 保留派发原始错误；自检与独审/批准分列，L0 上限 partial | 无自动重派/0/无；能力恢复另行派发 | 新简报绑定有效冻结对象 | 未评审/partial | review_tier、错误、原结论及新对象锚点 |

### 3. 执行清理（T05、T09）

| 步骤 | 调用与产物 |
| --- | --- |
| 1 | workflow seal→verify 固定计划、用例、argv、cwd、timeout_seconds 和原生报告；POSIX 新 session/组启动，记录 PGID |
| 2 | 监测超时/输出超限/异常/父进程先退后的遗留同组进程；统一进入清理，不因父已退出提前返回 |
| 3 | 整组 TERM，宽限至多 0.2s；仍存活则整组 KILL，再至多 1s 确认无存活同组进程，确保旧 E8 的 1s 晚写前收净；期限内不能确认即 cleanup-incomplete，不报清理成功 |
| 4 | 回收父进程后再解析本轮原生报告；验证延迟哨兵路径及组状态，返回后继续观察超过夹具晚写期限，无 SURVIVED_TIMEOUT |

| 失败/检测 | 处理 | 重试方/次数/退避 | 幂等前提 | 用户结果 | 日志 |
| --- | --- | --- | --- | --- | --- |
| 超时/超限/父先退但子忽略 TERM | 整组 TERM，0.2s 宽限后 KILL，1s 内确认；任务失败，清理不全单独报告 | 无任务自动重跑/0/无 | 清理信号可重复；不假定业务命令可重放 | 非零，禁止依赖任务继续；无晚写才算清理通过 | PGID、信号/期限、存活检查、stdout/stderr、哨兵读回 |
| 重复运行/输出落点已存在 | 拒绝覆盖既有证据，使用新轮次 | 主审复位后新运行1次/无自动退避 | fixture/副作用状态已复位且新证据路径 | 不重复未知副作用 | evidence-exists、落点、运行指纹 |
| plan 漂移/权限不足/非 POSIX 无等效保证 | 漂移在执行前拒绝；清理权限失败报 cleanup-incomplete；不支持的平台明确拒绝 | 无/0/无 | 输入重新封存、平台保证成立才可启动 | refused/blocked，不静默只杀父进程 | error_kind、平台、权限错误、实际剩余状态 |
| 原生报告迟到/丢失/格式错/用例不全 | 不把命令 exit0 当用例通过；保留失败轮 | 主审修数据/报告来源后新运行1次/无自动退避 | 报告绑定当前运行，非旧缓存 | fail/blocked | 原始报告、用例差异、exit、指纹 |

保证范围是同一 POSIX 进程组；不声称能清理主动 setsid 逃逸的进程。T02 明确该边界并避免将不支持的命令记为受保护路径。

### 4. 分档 / 用例（T02、T06、T07、T09）

| 步骤 | 调用与产物 |
| --- | --- |
| 1 | 逐任务应用 README 已定六风险规则；文档档位与独审需要分别判断，作者身份不改变阈值；必要授权等待明确答复 |
| 2 | 显式 --tier 立项；light 只生成含必要用例节的 README；full 按显式 tracks 生成并默认 qa，原型仅明确启用时生成 |
| 3 | Markdown 用例库唯一保存 TC/AC 映射、步骤/预期；YAML 仅引用及执行参数；run 固定 test_version、target 对象、原生报告 |
| 4 | 对静态小修、单层 UI、跨层表单/API、重复提交四类最小项目跑旧/新版受控样本；记录首次成功、人工恢复次数、耗时/成本与缺陷，不外推普遍提效 |

| 失败/检测 | 处理 | 重试方/次数/退避 | 幂等前提 | 用户结果 | 日志 |
| --- | --- | --- | --- | --- | --- |
| 演练超时/预算耗尽/缺 browser | 停依赖场景，保留已发生证据，UI 不用 API 替代 | 无自动重复/0/无 | 新轮次明确复位/可重放 | partial/未验证 | 阶段、停止原因、已跑/未跑用例 |
| 重复立项/重复提交 | 既有产物不覆盖；重复提交按 T02 冻结断言验证副作用次数 | 主审复位后新运行1次/无自动退避 | 相同任务输入、隔离项目、可观测副作用落点 | 明确拒绝或可证幂等，不假绿 | 文件集、实际副作用落点、逐次结果 |
| 缺 tier/tracks、非法日期/slug、规则冲突或 YAML 复制验收 | 参数/路径在写前拒绝；规则矛盾退回，删副本须保留权威语义 | 修输入后主审新运行1次/无自动退避 | 唯一权威和明确档位 | 非零或退回，不猜设计/授权 | 生成计划/文件数、权威引用、原文命中及计数 |
| 异步回调/原生运行结果缺失 | 产品业务回调 N/A；run/报告不全不得记 pass | 无/0/无 | 本轮原生报告与计划版本一致 | not-run/blocked | 缺失 TC、实际层级、报告路径 |

### 5. 三端安装 / 全局加载（T08、T11、T12）

| 步骤 | 调用与产物 |
| --- | --- |
| 1 | 主审读取 ZCode/Codex 实际本地市场源、Qoder 本地缓存/登记及三端旧版本；确认指向本仓；冻结源面、登记/缓存和全局原文备份 |
| 2 | 六份源 manifest 升 0.41.0、CHANGELOG/索引同步；build_runtime 生成；冻结不可变 expected runtime 与 Codex source 期望，不从安装后的源重算期望 |
| 3 | 按下表逐端本地安装；workflow.py 的 install-verify 比较完整运行面集合、类型、bytes、版本、执行位；升级前后源摘要必须相同 |
| 4 | 只对 ZCode 已有块 managed-preview→授权范围内 apply，核对旧状态/备份、块外 bytes、块内渲染模板；缺块/歧义拒绝，本批不追加新块 |
| 5 | 三端分别新会话探针核实实际加载的角色/规则版本，ZCode 逐字复述全局块首行；磁盘一致与加载分别报告。T12 独立 delta 复核全部最终对象及证据 |

| 失败/检测 | 处理 | 重试方/次数/退避 | 幂等前提 | 用户结果 | 日志 |
| --- | --- | --- | --- | --- | --- |
| CLI 超时/非零、登记或写入中断 | 不标安装成功，列实际变更；核清后按该步回滚点恢复 | 自动无/0/无；主审修因后1次/无自动退避 | 原登记/缓存备份存在，未被并发修改 | 非零/partial | argv、stdout/stderr、exit、前后状态、备份 |
| 重装同版本/CLI exit0 留旧缓存 | 全量核验，STALE_SENTINEL/缺项/多项/模式错均非零 | 无自动再安装/0/无 | 期望已冻结，缓存实际普通文件集可读 | 一致才报磁盘成功 | 文件集合、类型、size/hash、执行位、版本差异 |
| 源漂移/源非本仓/目标链接/全局块漂移 | 拒绝旧预览和安装结果；禁止重绑市场/覆盖用户后改内容 | 主审核清后新预览/运行1次/无自动退避 | 同一授权源和预期目标状态 | refused，块外不变 | realpath/祖先、源指纹、预期/实际摘要 |
| 新会话/加载探针失败或不可调用 | 不强退用户会话；磁盘成功仍单列加载未验证，保留备份 | 主审获可用会话后探针1次/无自动退避 | 真正新会话，不读旧上下文作证明 | blocked/partial，不能说已生效 | 宿主原始回复、版本/首行、失败原因 |

## 验证替身与发布顺序

| 验证装置 | 必须具备的表面与错误路径 |
| --- | --- |
| 文件/冻结 fixture | 用户块前后附录含非 UTF-8/不同换行/尾空白；foreign 块、唯一/重复/残缺自有块；Claude-only 缺依赖；manifest owner/hash/完整期望集；symlink 祖先及外部哨兵；OLD 快照/NEW 工作树、删除、commit、仓外同名、坏 size/hash/计数。HTTP 端点 N/A：文件/CLI 表面 |
| 执行 fixture | 真实 workflow seal/verify/run；task argv/cwd/timeout_seconds、用例与原生报告；父先退、子忽略 TERM、延迟写哨兵、正常完成、超限、异常、报告迟到/缺失；固定观察窗口长于夹具晚写期限 |
| 安装 CLI stub | 覆盖 T08 实际消费的 marketplace 查询及 add/update argv；stdout/stderr/exit、源指向、登记与缓存副作用；正确安装、exit0+STALE_SENTINEL、缺/多文件、同版本改 bytes、执行位错、源漂移、超时/非零。端点 N/A：命令行；隔离 HOME/PATH，绝不碰真实缓存 |
| 四类受控项目 | T02 在实施前冻结同一份任务输入、真实临时页面/API/字段与 fixture、错误分支及复位方法；UI 真实 browser 走通，API 仅支撑下层断言。旧/新版环境和样本一致；不把 stub 结果当真实宿主安装或业务收益 |

所有端到端检查先于 T10 评审关闭；安装后的最终入口/加载证据先于 T12 关闭。以下是本地发布顺序，每步成功才进入依赖步骤；没有远端发布动作。

| 顺序 | 动作/验收点 | 配对回滚点 |
| --- | --- | --- |
| R0 | 冻结源、主树未提交内容、旧生成树、三端登记/缓存、ZCode 全局文件；备份可读且普通文件 | 尚无安装变更；只保留证据，不清理未知文件 |
| R1 | T10 后 bump 六份 manifest、CHANGELOG/索引，build 并冻结 expected 树，验证 runtime equality | 按 R0 逐文件对照恢复本轮内容/旧生成树；先确认未覆盖其他写入，不用 git restore |
| R2 | ZCode 既有 local 市场升级，逐文件核验 | 恢复该端 R0 登记与旧缓存/旧启用版本，不改变市场来源 |
| R3 | Codex 既有 local 市场升级，按 --codex-source 核验 | 恢复该端 R0 登记与旧缓存/旧启用版本，不改其全局 AGENTS |
| R4 | Qoder 按已核实格式更新本地缓存/登记，逐文件核验 | 恢复该端 R0 缓存/登记与旧启用版本；不猜新登记格式或借机远端安装 |
| R5 | ZCode 既有全局块预览/备份/apply，块外相等、块内等于 0.41.0 渲染模板 | 仅在目标仍等于本轮写后状态时用普通文件备份安全还原；漂移则停下，不覆盖用户后改内容 |
| R6 | 三端新会话加载、smoke、最终 delta 独审及逐 G 验收 | 任一失败保留备份与失败证据，按受影响端 R2/R3/R4/R5 回退；无须回退其他已证独立端；完成前不清旧版本 |

## 验证命令

由主审/获工具的执行者运行，计划角色没有 Bash，不把下列待执行命令写成已通过。设置 `SRC=/Users/lihanghang1/Desktop/TestProject/agentflows`、`S=$SRC/skills/agentflow/scripts`、`E` 为上文路径；市场名、CACHE、EXPECTED_*、CASE_ROOT/REQUEST/SEALED/FINGERPRINT 由对应任务从实际登记或冻结文件赋值，不猜测。每条留完整 stdout/stderr/exit，不用屏蔽输出换绿。

| 命令/操作 | 预期结果与依据 |
| --- | --- |
| `git -C "$SRC" rev-parse --abbrev-ref HEAD`；`git -C "$SRC" diff --name-only --no-renames 511b9ef7b66a4b23cb859345d1810981aa083f5b`；`git -C "$SRC" ls-files --others --exclude-standard` | 主审复核分支与实际写范围，含未跟踪文件；逐候选同查。标准：git；不接受只报文件摘要 |
| `for n in check_ac_clarity check_skill_refs gen_review_brief init_workspace new_feature record_findings review_snapshot; do python3 "$S/$n.py" --self-test || exit; done` | 49 既有断言逐项保留、全部通过，另列本轮新增；失败不得删/跳用例。标准：七个既有 --self-test |
| `python3 "$S/test_tools_regressions.py"` | T09 唯一新增标准库入口；串联已审反例和邻接回归，故障注入只在一次性副本，逐项打印断言与 exit；标准入口待 Coding：T09 |
| `python3 -m compileall "$SRC/skills" "$SRC/packaging/build_runtime.py"`；`for f in "$S"/*.sh; do printf '%s\n' "$f"; bash -n "$f" || exit; done` | Python/Shell 语法全过；JSON 六源 manifest、运行请求及原生结果解析由 T09 同时检查。标准：解释器/现有文件集 |
| `python3 "$S/check_skill_refs.py" --root "$SRC"`；T07 权威/消费者人工语义核对 | 引用真实可达；残留门/冲突规则检索先打印原文和计数，排除引用旧错例/否定式表述再判定；不存在的检查不报机器通过。标准：check_skill_refs；人工确认：G06/G07/G09–G15 |
| `python3 "$S/init_workspace.py" "$CASE_ROOT" --hosts claude --dry-run`；实跑后同目标 `--check` | Claude 引用必存在；按 T02 smoke 补跑附录/foreign/冲突/越界用例。标准：init CLI；演练目录由 T02 固定 |
| `python3 "$S/new_feature.py" --hub "$CASE_HUB" --slug audit-smoke --date 2026-11-05 --tier light`；另一空副本用 `--tier full --tracks be` | light 仅 README，full 仅启用轨道且 qa 默认；缺 tier、full 缺 tracks、遍历/坏日期必须非零；--prototype 单测另列。参数契约待 Coding：T06 |
| `python3 "$S/workflow.py" seal --root "$CASE_ROOT" --input "$REQUEST" --output "$SEALED"`；同指纹 `verify`、`run --phase red`、范围内实现后 `run --phase green` | T09 依次补全各子命令 --root/--sealed/--fingerprint 和每轮新 --output；有效 red→green，计划漂移拒绝；原生用例结果绑定本轮，退出成功不代替覆盖。标准：既有 workflow CLI，具体输入由 T02/run 冻结 |
| `python3 "$SRC/packaging/build_runtime.py"`；`python3 "$S/workflow.py" install-verify --expected-tree "$EXPECTED_RUNTIME" --installed "$SRC/packaging/runtime"` | 源面→runtime 运行面逐文件一致；expected 在升级前固定。核验入口待 Coding：T08 |
| `python3 "$S/workflow.py" upgrade-zcode --repo "$SRC" --marketplace "$ZCODE_MARKETPLACE" --plugin agentflow --mode local --dry-run`；Codex 同形 `upgrade-codex`；通过后去 --dry-run 实跑 | 确认现有 local 源为本仓，无自动推送/市场重绑；接受 --mode auto/local/remote，但本批只执行 local。入口待 Coding：T08；维护 shell 只转调同库 |
| `python3 "$S/workflow.py" install-verify --expected-tree "$EXPECTED_RUNTIME" --installed "$ZCODE_CACHE"`；Qoder 换实际 cache；Codex 用 `--expected-tree "$EXPECTED_CODEX_SOURCE" --installed "$CODEX_CACHE" --codex-source` | 三端完整集合/类型/bytes/版本/执行位一致，stub 假安装非零；Qoder 更新按 T11 已核实本地缓存/登记逐步留原始操作。入口待 Coding：T08 |
| `python3 "$SRC/packaging/build_runtime.py" --verify-installed "$CODEX_CACHE" --expected-tree "$EXPECTED_CODEX_SOURCE" --codex-source` | 维护薄入口与 workflow 核验同结论，不复制实现。入口待 Coding：T08 |
| `python3 "$S/workflow.py" managed-preview --target /Users/lihanghang1/.zcode/AGENTS.md --content "$GLOBAL_BODY" --output "$GLOBAL_PREVIEW" --begin-marker "$OLD_BEGIN" --end-marker '<!-- agentflow:end -->' --new-begin-marker '<!-- agentflow:begin v0.41.0 -->'`；随后 `managed-apply --preview "$GLOBAL_PREVIEW" --fingerprint "$GLOBAL_FINGERPRINT"` | 仅既有块，应用前摘要重检；T11 保留备份并分别逐字比较块外/渲染块内；新会话复述首行。标准：既有 managed CLI 与 hosts 协议 |
| 执行 [测试计划](../testing/agentflows-audit-fixes/plan-2026-11-05-001.md) 的 smoke 集及全部必需 e2e | T02 注册 INIT/FREEZE/CLEANUP/TIER/INSTALL 五链 smoke，并明确脚本/入口/断言；UI 场景 browser 原始证据，其他 CLI 用户路径 manual+file；run 绑定计划版本。未跑不得 pass，e2e 不接受 api/file 关闭 |

## 变更记录

2026-11-05T10:48:14Z · Plan Architect 创建 v1.0.0 proposed，全部接受状态未开始；时间由主审供给。主审批准时另记审批及刷新 updated_at；本文件不自行批准。最终验收逐 G 报已验证/缺证据/外部阻塞，G16 缺实测仍未验证，成本/耗时拿不到写 not reported，缺业务对照保留 measurement: none。

2026-11-05T11:55:51Z · 主审接受计划与用例、回写已复验实现T01–T08；T09/T10仍进行中，T11/T12待办。首轮工具/规则独审changes_requested保留，聚焦修复后绑定新快照复审。

2026-11-05T12:37:41Z · 最终收口：10任务已完成，2任务按具体浏览器/加载限制阻塞；实现与独审完成不代替父目标完整验收，结论partial，剩余动作见decision.md。
