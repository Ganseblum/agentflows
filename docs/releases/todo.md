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
| 5 | 总体评审吸收与修复批（feature-2026-10-25：2026-10-25 会话总体评审结论入仓——问题清单、四维评分与理由、26 项修复任务） | 立项：提案与计划已成文，`status: proposed` | 五项待拍板（Q-01 门工具交付路线 / Q-02 文档链默认档 / Q-03 改进环处置 / Q-04 记录面删减 / Q-05 必读面瘦身）见批次提案 §六；受保护路径任务 12 项需逐项授权 |
| 6 | L3 工作流增强批（feature-2026-10-26：十四项吸收 / 执行协议与证据工具 / 轻量档 / pre-push 门禁修正） | 已随 0.19.1 推送 origin/main 并装入 ZCode 与 Codex（installed PASS） | 门变更经独立评审；pre-push 四轮评审后 approved（`d231bcb`）。见批次 `plan/PLAN-L3-001.md` |

已完成批次：产品链修复轮（REV-20261019-003 approved，2026-10-19）、全仓中文化、youc 吸收批、结构文档、端点复测与试水、2026-10-22 文档面收尾批——详见 `CHANGELOG.md` 与 git 历史。

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
