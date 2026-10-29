# 发布待办

> 在途批次索引与决策性记录。已完成条目见 git 历史与 `../../CHANGELOG.md`；
> 待用户拍板的事项见 `../PENDING-DECISIONS.md`；待人工验收见 `pending-test.md`。

## 批次索引

| # | 变更 | 状态 | 备注 |
| --- | --- | --- | --- |
| 1 | 质量提升批（feature-2026-10-13：门禁拆分 / 变异测试 / 计数脚本 / 角色场景 / 文档链） | 已完成（T10 本期不做） | T01–T09 已闭（T04 于 2026-10-20 全量实跑 28/28 达成、G5 通过）。门变更均经独立评审 approved。2026-10-23 追溯闭环批为本批补上 T01/T04 的仓内证据载体并回写了 `spec/qa` 的验收点状态列 |
| 2 | 追溯闭环与证据在场批（feature-2026-10-22：文档链新增 C22 目标承接闭环与 C23 证据在场、记录契约补 `disposition`、拍板口八列化、八条文本缺陷收口） | 已随 0.13.0 发布；T11 第三轮独立复核待跑 | 门变更经用户 2026-10-22 当次授权；第二轮 20 条已在 `ff13912` 修完（看板 T11 ◐）；发布动作见 `861b6ef`，T12 缺「`validate.py all` 全绿原始输出」留档（看板 T12 ◐） |
| 3 | 宿主接入批 2026-10-24：Host Init（`skills/agentflow/references/hosts.md`、`skills/agentflow/templates/host/`、SKILL 宿主级接入节）、0.14.0 版本 bump | 已随 0.14.0 发布，现由 0.15.0 取代 | 真实宿主写入与加载验证仍待用户，见 `pending-test.md` 第 4 行 |
| 4 | 测试链路 Ego Light 批 2026-10-25（分支 `feature-2026-10-24-gate-tune-and-refactor` 已并入 main）：QA 方法切换、`doc_chain` 拆包、README 四问导航、episodes 按月归档、0.15.0 版本 bump | 已发布并已装入宿主（`validate.py installed` PASS） | 端到端 Ego Light 实跑与 bug 回归链走查待用户，见 `pending-test.md` 第 5 行；本批未建 `docs/features/` 批次目录，记录存于 `CHANGELOG.md` 与 git 历史 |
| 5 | 总体评审吸收与修复批（feature-2026-10-25：2026-10-25 会话总体评审结论入仓——问题清单、四维评分与理由、26 项修复任务） | 立项：提案与计划已成文，`status: proposed` | 五项待拍板（Q-01 门工具交付路线 / Q-02 文档链默认档 / Q-03 改进环处置 / Q-04 记录面删减 / Q-05 必读面瘦身）见批次提案 §六；受保护路径任务 12 项需逐项授权。2026-10-29：Q-01 经实测已由 2026-10-26 的安装面修复落地（`packaging/build_runtime.py:37-40` 的 `RUNTIME_SUBTREES` 已含 `tools/lab/doc_chain.py` 与 `docchain/`），不再当未决项；收敛类任务 T13/T14/T24 与 §六 Q 项并入 `feature-2026-10-29-全面修正与瘦身`，其余任务留本批 |
| 6 | L3 工作流增强批（feature-2026-10-26：十四项吸收 / 执行协议与证据工具 / 轻量档 / pre-push 门禁修正） | 已随 0.19.1 发布；0.19.3 已推送 origin/main（`272add3`）并装入 ZCode 与 Codex（installed PASS） | 门变更经独立评审；pre-push 四轮评审后 approved（`d231bcb`）。见批次 `plan/PLAN-L3-001.md` |
| 7 | 评测整改批（feature-2026-10-28：整改状态列 / 评审能力分级 L0–L2 / 表达面收敛 / 本地 `.venv` 门基线 / 改进环首份真实记录），版本号已并入 0.22.0（已发布） | 已并入 `main`（合并提交 `26988a4`），随 0.22.0 推送 `origin/main` 并装入双端（2026-10-28 `validate.py installed` PASS） | 合并后 `validate.py all` 11/11 PASS、unittest 172 OK（当日时点值；现行值以 `validate.py --list` 与 `-m unittest discover -s tests` 实跑为准）；生成树已重建；待验收项见 `pending-test.md` 第 6 行。见批次 `plan/PLAN-EVAL-001.md` |
| 8 | 表达面与角色治理批（feature-2026-10-28：载体归属表 / 同步义务退场 / `document-chain` 拆分 / FE-BE 裁决 / 实现角色深度对齐），尚无版本变更 | 立项与范围冻结（T01–T08 全部 ☐ 未开始）；文档已并入 `main`（`26988a4`），不含实现改动 | 本批交付物是「范围 + 判据 + 裁决规则」；实施需另一次授权。评审档位 L0，恢复委派能力后须补独立复核。2026-10-29：八项任务全部并入 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md`，原计划置 `superseded`（`superseded_by: PLAN-FIX-001`），本行不再作为进度权威。见批次 `plan/PLAN-GOV-001.md` |
| 9 | 评审欠账清偿批（feature-2026-10-28：两批 L0 欠账补独立评审 / `review_tier` 伪降级记录侧校验 / 五条待评审缺陷逐条清偿），尚无版本变更 | 立项与范围冻结（T01–T08 全部 ☐ 未开始）；文档已并入 `main`（合并提交 `94e8eed`，保留比分支更新的在途修订），随 0.22.0 推送 | 委派能力 2026-10-28 实测已恢复，本批按 L1 档立项；T04 触碰 `schemas/` 与 `tools/lab/`，属门变更须逐项授权——2026-10-29 该两项由 `docs/features/feature-2026-10-29-全面修正与瘦身` 的 T14 与 T09 承接执行（同一授权口径），T02/T03/T05–T07 仍留本批。见批次 `plan/PLAN-DEBT-001.md` |
| 10 | 工程基线吸收批（feature-2026-10-28：工程基线模板与 Init 六项 / 后端数据与配置核对 / 原型可点性 / 测试设计三维 / 前端实现纪律），版本 0.22.0（已发布） | 实施与确定性门完成；原四项独立评审通过，**FE 增量的独立评审未运行**（用户 2026-10-28 拒绝派发子代理，按未评审记录）；已并入 `main`（`d5b52ce` + `256ea64`），已推送 `origin/main` 并装入双端（0.22.0） | 0.21.0 从未发布，其内容随 0.22.0 一并发布并装入双端。见批次 `plan/PLAN-BASE-001.md` |
| 11 | 关闭证据门批（feature-2026-10-28：verified/rejected 按状态强制关闭证据 / 非 open 必须有 `## 变更记录` / 负例回归钉住），无独立版本号（计入 0.22.0） | 实施与确定性门完成；首轮独立评审 changes_requested 的 4 项已修复，修复轮按 L0 自审，**两个评审门（需求评审门 + 技术方案评审门）待跑**；2026-10-28 由 worktree 的工作树改动直接并入 `main`（开发分支无提交），随 0.22.0 推送 `origin/main` 并装入双端 | 属门变更：`tools/lab/gate/records.py`、`tools/lab/gate/examples.py`、`tools/lab/mutate.py`、`tests/test_gate_schema.py` 均在 `protected-paths.txt` 内，经用户 2026-10-28 授权并入；未新增测试文件，`EXPECTED_TEST_FILES` 与保护清单无需增补。见批次 `plan/PLAN-CLOSE-001.md` 与 `reviews/agentflow-关闭证据门/review-2026-10-28-001.md` |
| 12 | 全面修正与瘦身批（feature-2026-10-29-全面修正与瘦身：议程归并 / 拍板口归口 / 四组门判据 / 必读面收敛 / 证据件与重复导航删除），尚无版本变更 | 进行中：文档链五段成文且链 linter 绿（T01 ☑），实施任务 T02 起推进；门变更四条经用户 2026-10-29 授权（`schemas/`、`tools/lab/`、`tests/` 逐文件在保护清单内）；经授权不提交、不推送、不重装 | 状态以 `plan/PLAN-FIX-001.md` 为准 |

已完成批次：产品链修复轮（REV-2026-10-19-003 approved，2026-10-19）、全仓中文化、youc 吸收批、结构文档、端点复测与试水、2026-10-22 文档面收尾批——详见 `CHANGELOG.md` 与 git 历史。

## 决策性记录

- **吸收 youc 模式**（2026-10-10 用户指示）：实例化本文件与 `pending-test.md`；建立
  `../PENDING-DECISIONS.md` 单点拍板清单；`AGENTS.md` 增「表达与沉淀纪律」；`SKILL` 增
  「首次接入（Init）」；「单真源 + 生成视图」推迟为设计项（原待拍板第 8 条：拍板为试点
  「结构文档目录树生成」；未开工，试点载体所在的手写目录树已随 2026-10-13 校正批删除——重启需另行立项）。
- **中文化口径**（用户指示「能改的都改」）：含受保护面；受保护改动的授权依据见相应提交信息与
  `CHANGELOG`，回溯评审登记为 `../PENDING-DECISIONS.md` 第 4 条。

## 零散微项

- **写范围执法器（G08 / 2026-10-26 审核 P2）登记为「已知人工步骤，不自动接入」**：
  `skills/agentflow/scripts/check-write-scope.sh` 只在 Supervisor 接受产物时手动运行
  （硬边界 14），未接入 pre-push 或 CI。原因：`check-write-scope.sh:18-22` 自身要求
  「委派时已 dirty 的路径需在阅读报告时人工扣除」，误报面（dirty 树上的无关变更）尚未评估，
  贸然接入会阻断合法推送。等价于把 G08 从 P1 降为「已声明未缓释」。接入与否待用户拍板
  （见 `../PENDING-DECISIONS.md`；若改接入，pre-push.sh / CI 改动 + 误报面评估属门变更，需授权）。
- 历史微项（计划看板回写、`--case-ids` 复核、`check-write-scope.sh`「.」缺陷、
  schema description 汉化、`index-template.md` 去重、`host_adapter` 隔离认证、公开切片授权）
  均已在 2026-10-09–2026-10-22 期间关闭，证据见 `CHANGELOG.md` 与 git 历史。
