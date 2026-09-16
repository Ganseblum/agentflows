---
bug_id: BUG-20260914-003
title: print 模式评测权限档无法完成写计划的用例
status: open
severity: P2
error_kind: host-compat
attribution: evaluation
provenance: agentflow
project: agentflows
files:
  - tools/lab/host_adapter.py
  - evals/public/inputs/AF-002.md
affected_slices:
  - host-adapter
  - cross-layer-planning
  - evaluation-harness
recorded_at: 2026-09-14T12:04:08Z
updated_at: 2026-09-16T12:03:24Z
source_revision: f2ea05c
agentflow_version: 0.3.1
---

## 现象

AF-002 诊断运行中，plan-architect 子 Agent 的 Write 被宿主拒绝，Bash 校验命令未获批准。
最终 `accepted: false`、`tool_failures: 3`，单用例约 23.8 分钟 / $4.05。stream 证据原文：

```
Write tool result: plans/AF-002-activity-list.json classified as sensitive and not created
Bash result: validator command required approval and was not run
```

## 问题代码

```python
# tools/lab/host_adapter.py (current)
def permission_args(host: str, profile: str) -> list[str]:
    if host == "claude":
        if profile in {"workspace-write", "read-write-workspace"}:
            return ["--permission-mode", "acceptEdits"]   # print 模式仍拦敏感写/审批 Bash
```

## 根因

`read-write-workspace` 映射到 `--permission-mode acceptEdits`，而 Claude Code 2.1.268 在
`--print` 模式下仍拦截敏感路径写入和需要审批的 Bash。需要写计划的评测用例在该 profile
下测到的是宿主权限限制，不是工作流行为。

## 修复

未修复，方案决策中：

- 选项 A：对齐 profile 语义（如显式 `--allowed-tools`/`--permission-mode` 组合），让计划类用例可完成；
- 选项 B：声明计划类用例超出 print 模式评测范围，从 suite 中排除或标记。

决策依据待补：宿主在 print 模式下的完整权限矩阵（见 `docs/host-platform-facts.md` C2）。

## 备注

- 观察环境：Claude Code 2.1.268 + 网关映射模型；其他宿主行为未验证。
