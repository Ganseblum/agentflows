---
bug_id: ISS-2026-014
title: 覆盖对照表两处自评与正文自相矛盾（AskUserQuestion 标✅覆盖、checkpoint 标✅等效替代）
status: open
disposition: deferred
updated_at: 2026-10-23T00:18:22+08:00
severity: P2
error_kind: logic-error
attribution: product_code
provenance: external
project: infinite-canvas
files:
  - reviews/infinite-canvas-office-agent-plan/archive/2026-09-19-001/第六期-AI办公助理Agent产品线.md
recorded_at: 2026-09-19T14:21:06Z
source_revision: infinite-canvas@1343820
agentflow_version: 0.8.0
---

## 现象

必查维度（对照表诚实性）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）WorkBuddy 对照表写：

> TodoWrite/AskUserQuestion/ExitPlanMode 工具集 | M2 SDK 内置工具 | ✅ 覆盖（AskUserQuestion 见差距说明）

而差距说明正文自认：

> 结构化提问（clarification/AskUserQuestion）…只做了事件预留

同一行内「✅ 覆盖」与「只做了事件预留」矛盾。另一处：

> checkpoint 会话连续性 | resume-per-turn + transcript 落盘 | ✅ 等效替代（无 UI 级回滚，后续期再评估）

checkpoint 的定义性能力就是回滚，自注「无 UI 级回滚」再标「✅ 等效替代」是夸大。

## 影响

覆盖结论被高估；依赖对照表做范围决策（如砍掉 clarification 优先级）会得出错误结论。

## 根因

对照表为作者自评且未受独立核对；括号内注记（见差距说明/无 UI 级回滚）已与判定矛盾，但未上翻修正结论符号。

## 备注

修复方向：AskUserQuestion 行改 ⏸/预留并消除与差距说明的矛盾；checkpoint 行降为「核心覆盖（无回滚）」。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F5，状态 open。

- 2026-10-23 00:18 · 归属登记 · 补 `disposition: deferred`：该条属被评审项目（见 frontmatter `project`），本仓不承接；C18 归属检查要求显式声明，来源见 `docs/features/feature-2026-10-22-追溯闭环与证据在场/plan/PLAN-TRACE-001.md` T07。
