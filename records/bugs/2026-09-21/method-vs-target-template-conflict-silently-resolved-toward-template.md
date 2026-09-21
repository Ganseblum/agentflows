---
bug_id: BUG-20260921-03
title: 方法条款与目标仓模板冲突无显式裁决装置——「契约以谁为准」逐行指针在条款已存在的情况下复发（BUG-20260920-06 升级）
status: fixed-pending-review
regression_status: not-run
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/references/document-chain.md
recorded_at: 2026-09-21T14:24:00+08:00
source_revision: agentflow@7a235b5 (0.8.3+方法整合候选)
agentflow_version: 0.8.3
---

## 现象

aiwork 定时任务文档链 design/be §1.4.1 接口清单表带「契约以谁为准」列，15 行取值完全相同（`nexus-v1.yaml（§1.4.5）`/「同上」）。用户上轮已明确反馈过该形态（EP-20260920-003：「『契约以谁为准』逐行指针×16 是噪音——应为路径直写+裁决规则声明一次」），且现行方法 `document-chain.md` **已有条款**："adjudication/authority rules are stated once, never repeated per row"。

条款存在、复发仍发生：目标仓模板 `templates/feature/design/be` §1.4.1 表头**自带该列**，brief 要求「严格照抄模板章节结构，含各表头」，评审按「模板合规」检查反而视该列为合格。两条规范正面冲突，被静默解决在最不符合用户意图的一侧。

## 根因

方法（质量条款优先、裁决声明一次）与目标仓模板（结构逐列保留）发生冲突时，**没有显式裁决规则**。方法同时主张「目标仓有自己的模板系统就保留它」，两条主张的交叠区无优先级排序；brief 作者与评审人都各自默认了模板一侧。

## 修复

`document-chain.md` 新增冲突裁决条款：**方法质量条款优先于目标仓模板的结构性要求**——当模板要求与质量条款冲突（逐行裁决指针、逐行重复的权威声明等），保留模板骨架、按质量条款收拢（该列改一句表头注或删除），并在文档头以一句「结构性裁剪声明」留痕（先例：plan/qa 模板 §3 的结构性裁剪声明）。

regression_status=not-run：条款变更，无 instrumented 用例；对照面=下次文档链的 §1.4.1 形态。
