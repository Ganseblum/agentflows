---
bug_id: ISS-2026-021
title: 四个关键机制压在未验证的 Claude Agent SDK 行为上，且无前置 spike（resume 验收排在 M2）
status: open
severity: P2
error_kind: other
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

必查维度（未验证依赖）。快照（原始地址 infinite-canvas@1343820:我的规划/第六期-AI办公助理Agent产品线.md）把上下文连续性、压缩、工具审批、沙箱四个关键机制全部押在 SDK 具体行为上：

> SDK 配置：`query()` + `resume` 续会话；`canUseTool` 钩子预留审批位

> 容器内用 SDK 自带 sandboxed bash（Linux bubblewrap）做文件系统/网络限制

评审证据基线明确标注：resume/fork/canUseTool 仅读过官方 overview 页，API 细节未核；经 LiteLLM 翻译路径后 resume 所依赖的 transcript/tool_use 块是否保真更属未知。计划没有任何前置 spike 验证任务——resume 首次被验收竟在 M2，而 M2 的全部设计（transcript 落盘、跨 run 续接）已压在它上面。

## 影响

若 resume/翻译路径行为与设想不符，M2 设计需要返工；bubblewrap 在 Docker 内嵌套运行的可行性本身待验证。

## 根因

证据基线中的「未验证」标注未被转译为计划内的显式验证任务；验收排期把假设的首次检验放在了依赖它的设计（M2）之后。

## 备注

修复方向：M1 增加 spike 验收条目（GLM 经 LiteLLM 直通端到端验证 resume 续接）；将 resume/fork/canUseTool/压缩/bubblewrap 标注为待验证假设。

## 变更记录

- 2026-09-19 14:21 · 立录 · REV-20260919-001 finding F12，状态 open。
