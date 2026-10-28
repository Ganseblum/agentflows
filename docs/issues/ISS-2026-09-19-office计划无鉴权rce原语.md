---
bug_id: ISS-2026-09-19-office计划无鉴权rce原语
title: 契约二无认证且 Runtime 接受外部传入工作区路径——构成内网 RCE 原语
status: open
disposition: deferred
updated_at: 2026-10-23T00:18:22+08:00
severity: P2
error_kind: missing-constraint
attribution: product_code
class_id: external-plan-missing-failure-branches
occurrence: 5
provenance: external
project: infinite-canvas
files:
  - reviews/infinite-canvas-office-agent-plan/archive/2026-09-19-001/第六期-AI办公助理Agent产品线.md
recorded_at: 2026-09-19T14:21:06Z
source_revision: infinite-canvas@1343820
agentflow_version: 0.8.0
---

## 现象

安全维度。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）三处叠加：

> 职责边界：只做协议翻译与 agent 生命周期管理；**鉴权、配额、计费、业务规则一律不进 Node**。

> `POST /v1/runs`：入参 session 工作区路径、消息内容、agent 配置（system_prompt/model/tools/skills）、附件清单

> office-agent 只在内网，不经 nginx 暴露。

契约二完全无认证设计，且 Runtime 接受调用方传入的工作区路径。「鉴权不进 Node」+ compose 内网互通意味着：任何能触达 office-agent 端口的容器（含未来新增服务、被攻破的兄弟容器）都可以传任意路径起一个带 Read/Write/Bash 的 agent——一个内网 RCE 原语。

## 影响

沙箱阶段一「容器即边界」的隔离声明被契约二开洞；内网横向移动后可直接接管 agent 执行环境。

## 根因

「职责边界不进 Node」被当成边界设计本身；未推演「无认证 + 内网互通 + 接受外部路径」三条件叠加后的攻击面。

## 备注

修复方向：契约二共享密钥/来源校验；工作区路径改由 Runtime 按 sessionId 在服务端推导（不收客户端路径）；网络策略隔离 office-agent。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-2026-09-19-001 finding F6，状态 open。

- 2026-10-23 00:18 · 归属登记 · 补 `disposition: deferred`：该条属被评审项目（见 frontmatter `project`），本仓不承接；C18 归属检查要求显式声明，来源见 `docs/features/feature-2026-10-22-追溯闭环与证据在场/plan/PLAN-TRACE-001.md` T07。
