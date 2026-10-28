---
bug_id: ISS-2026-10-23-非法disposition取值
title: 非法的 disposition 取值必须被记录契约拒绝
status: open
disposition: wontfix
severity: P3
error_kind: other
attribution: product_code
provenance: external
project: example-project
files:
  - examples/invalid/bug-record-disposition-unknown.md
recorded_at: 2026-10-23T00:15:00+08:00
---

## 现象

本记录把 `disposition` 写成 `wontfix`，而契约只承认 `deferred` 与 `not-doing`。

## 根因

用于演示归属字段的取值闭集：允许自由字符串会让「不做」出现四种写法，C18 的归属判定随之失效。
校验器必须拒绝本记录——这是刻意的非法示例，不是待修的缺陷。
