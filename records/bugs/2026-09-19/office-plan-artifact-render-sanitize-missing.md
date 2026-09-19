---
bug_id: BUG-20260919-007
title: Artifact/markdown 预览渲染无净化策略——模型生成内容构成存储型 XSS 面
status: open
severity: P2
error_kind: missing-constraint
attribution: product_code
provenance: external
project: infinite-canvas
files:
  - records/reviews/infinite-canvas-office-agent-plan/archive/2026-09-19-001/第六期-AI办公助理Agent产品线.md
recorded_at: 2026-09-19T14:21:06Z
source_revision: infinite-canvas@1343820
agentflow_version: 0.8.0
---

## 现象

安全维度（注入面）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）对渲染只有功能性描述：

> 预览由 Go 提供只读接口，前端渲染 markdown/代码高亮；下载走 storage 签名 URL。

> 对话流组件：文本增量渲染（markdown + 代码高亮 + katex 公式预留）…

Agent 产出物是模型生成内容（可被提示注入操纵），前端将 markdown/html 渲染进用户浏览器是存储型 XSS 面；计划对净化策略（sanitize allowlist、html 类型是否禁渲染等）只字未提。安全节的「存储侧标记 + admin 可见」不解决渲染层问题。

## 影响

被注入的 artifact 可在查看者浏览器执行脚本；多用户预览/下载链路放大影响面。

## 根因

仅从功能视角描述渲染链路；未把「Agent 产出物是不可信输入（可被提示注入操纵）」带入渲染技术选型。

## 备注

修复方向：渲染层净化策略（sanitize 白名单；html 类型 artifact 默认不渲染或走白名单）写入计划并进 M2 验收。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F7，状态 open。
