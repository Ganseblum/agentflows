---
class_id: invented-interface-ids-and-adjudication-pointer-noise
title: 逐行裁决指针噪音——「契约以谁为准」等权威声明逐行重复（用户明确反馈过的形态复发）
status: consolidated
consolidated_in: 0.8.4
first_record: BUG-20260920-06
occurrences:
  - BUG-20260920-06
  - BUG-20260921-03
recorded_at: 2026-09-21T14:32:00+08:00
updated_at: 2026-09-21T14:32:00+08:00
---

## 类模式

接口清单表逐行携带内容相同的裁决/权威指针（「契约以谁为准」列 15 行同值），迫使读者重复
阅读同一裁决；用户在 EP-20260920-003 明确反馈「逐行指针×16 是噪音——应为路径直写+裁决
规则声明一次」。

## 归纳内容

BUG-20260920-06 已把「禁自造接口编号与逐行裁决指针」写入 `document-chain.md`（主线与克制：
adjudication rules stated once, never repeated per row）。

## 升级记录（2026-09-21，BUG-20260921-03）

条款已在 source 的前提下，同一形态仍在 0.8.3 运行的首次真实文档链中复发（design/be §1.4.1
15 行同值列）。根因升级：**方法条款与目标仓模板结构正面冲突时无显式裁决装置**——模板表头
自带该列，brief 要求照抄模板含表头，评审按模板合规判合格，冲突被静默解决在模板一侧。修复
方向不是重申条款，而是新增「方法质量条款 > 目标仓模板结构，冲突时声明结构性裁剪」的裁决
规则（BUG-20260921-03）。
