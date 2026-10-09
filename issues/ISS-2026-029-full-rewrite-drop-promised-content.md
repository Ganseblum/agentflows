---
bug_id: ISS-2026-029
title: 整文件重写丢失已承诺内容——图目录承诺的图未兑现、执行通道节与自测 C6 夹具在重写中蒸发
status: verified
severity: P2
error_kind: other
attribution: context
provenance: agentflow
project: agentflows
files:
  - tools/lab/doc_chain.py
  - aiwork-workflow-ai@worktree-2026-09-20:docs/features/feature-2026-09-18-定时任务/design/fe/定时任务-前端技术方案.md
affected_slices:
  - rewrite-discipline
  - self-test-discrimination
class_id: full-rewrite-drop-promised-content
occurrence: "1"
recorded_at: 2026-09-20T06:00:00Z
updated_at: 2026-09-20T07:05:00Z
source_revision: agentflows@5da90f2
agentflow_version: 0.8.2
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: doc_chain 自测 18/18（含图覆盖判别 case 02/08/09/10/11/12/18）；真实链 doc_chain PASS exit 0；validate.py all → 9×PASS
fix_revision: agentflow 0.8.3
---

## 现象

为对齐沙箱熔断设计基准做整文件重写时，三处已存在且已承诺的内容被静默丢弃：

1. `design/fe` 重写稿的图目录仍列出图 1（页面流转 flowchart）/图 5（弹窗状态机）/
   图 6（开关时序），正文却只有一张时序图——linter 真实链复跑以 C8 FAIL 抓出；
2. `design/be` 重写稿丢失"执行通道与注入段/无人值守执法面"整节（首版已有）；
3. `doc_chain.py` 自测从 6 例扩到 16 例时**丢失原 C6 判别夹具**（fe 缺异常矩阵变体），
   被独立评审 round-2 点名（该轮未给编号），补 C6 后 16→17；第 18 例（HTML 原型满足
   C7 的判别夹具）是 episode 落账后随 C7 原型形态扩展另行新增，与 C6 无关。

## 根因

attribution=context（执行层流程草率）：三次大改均采用**整文件覆盖**而非增量修改，
重写前没有建立"现存内容/已承诺内容清单→逐项兑现"对照；当时无任何机器检查覆盖
"图目录承诺 vs 图实际存在"，自测判别矩阵未做逐检查映射评审。

## 问题代码

修复前自测（6 例版→16 例版过渡）缺失 C6 用例——修复前 `self_test()` 无任何变体移除
fe 异常矩阵表；修复前 linter 无 C8 图覆盖检查（重写丢图在首版 linter 下不会失败）。

## 修复

1. linter 新增/强化图覆盖：C4（be 需含 alt 时序+flowchart+ER/状态图，数据模型图可落
   spec）、C8（fe 需 flowchart+sequence+state）、C7（线框或 prototype HTML 二选一），
   自测 18 例含"重写丢图必须失败"判别；
2. 丢失内容全部补回（图 1/5/6、执行通道节、C6 夹具），由真实链 PASS 与 18/18 自测钉住；
3. 流程约束：整文件重写前先列出"已承诺内容清单"，重写后逐项对照（本轮起执行，并已
   写入 document-chain.md 图目录纪律——图目录所列必须逐张兑现）。

外部引用现状片段（丢失图补回后，节选自引用文件）：

> aiwork-workflow-ai@worktree-2026-09-20:docs/features/feature-2026-09-18-定时任务/design/fe/定时任务-前端技术方案.md 图目录
>
> | 图 5 | 状态机 | 弹窗一次创建会话的解析/预检/提交流转 |
> | 图 6 | 时序图 | 启停开关乐观更新失败怎么回滚 |

**回归证据**：linter 18/18（含 case 02/08/09/10/11/12/18 对图覆盖与线框的判别）；
真实链 PASS；评审员 round-2 以 C6 夹具缺失为由 changes_requested、补齐后 approved。

## 变更记录

- 2026-09-20 初版立账。

## 审查

- [x] 三处丢失内容已补回并被机器检查钉住
- [x] linter 判别力经独立评审逐夹具核对（round-3 AC1 approved）
- [x] 独立评审核对通过（agentflow:reviewer approved，2026-09-20 终裁）
