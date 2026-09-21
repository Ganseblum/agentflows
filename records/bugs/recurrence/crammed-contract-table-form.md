---
class_id: crammed-contract-table-form
title: 契约字段表杂糅——字段/类型/必填/说明挤在一格（用户明确反馈过的形态复发）
status: consolidated
consolidated_in: 0.8.4
first_record: BUG-20260920-07
occurrences:
  - BUG-20260920-07
  - BUG-20260921-04
recorded_at: 2026-09-21T14:34:00+08:00
updated_at: 2026-09-21T14:34:00+08:00
---

## 类模式

契约表把多个字段的名称/类型/必填/说明压进同一单元格（首现形态 `name(string/Y)` 一格挤），
用户在 EP-20260920-003 明确要求「字段/类型/必填/说明拆列或代码块+注释」。

## 归纳内容

BUG-20260920-07 已把拆列形态教进 `document-chain-templates.md`（design 模板契约表范式）。

## 升级记录（2026-09-21，BUG-20260921-04）

模板修复后的首次真实文档链出现**新机制变体**：supervisor 为通过 linter C4（检查「存在含
『请求字段/响应字段』表头的契约表」）补写的字段级总表，满足存在性检查但请求/响应各为一格
塞 10-13 字段——机器门验收存在性、用户标准是形态，缝隙处 Goodhart。另 design/fe §1.2 七列
宽表复发（形态约束只在 be 模板，fe/qa 无同等条款）。修复：document-chain.md 明确「通过存在
性检查≠满足形态标准」+ 模板 fe/qa 侧补形态约束（BUG-20260921-04）。
