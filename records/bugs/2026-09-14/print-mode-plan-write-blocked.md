---
bug_id: BUG-20260914-003
title: print 模式评测权限档无法完成写计划的用例
status: fixed-pending-review
severity: P2
error_kind: host-compat
attribution: evaluation
provenance: agentflow
project: agentflows
files:
  - tools/lab/host_adapter.py
  - tools/lab/eval_runner.py
  - evals/public/inputs/AF-002.md
affected_slices:
  - host-adapter
  - cross-layer-planning
  - evaluation-harness
recorded_at: 2026-09-14T12:04:08Z
updated_at: 2026-09-18T16:02:00Z
source_revision: f2ea05c
agentflow_version: 0.3.1
regression_status: not-run
fix_revision: agentflows@95de103
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
# tools/lab/host_adapter.py (0.3.1)
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

已按当年预案的选项 A 落地（0.8.0，commit `95de103`）：

- 请求级 `allowed_tools`（claude 侧拼接为 `--allowed-tools`，逐工具显式预批）+
  `isolate_host_config`（`--strict-mcp-config` + 一次性 `CLAUDE_CONFIG_DIR`），
  不再让 `acceptEdits` 的隐式拦截充当权限语义；
- `eval_runner.py run` 新增 `--allowed-tools` / `--isolate-host-config` 透传，
  两者写入 `observed_context`（`allowed_tools` / `mcp_isolated`），codex 传了即 fail-closed；
- stub 回归：`HostIsolationArgumentTests`、`ClaudeStreamObservationTests`
  （`tests/test_lab_contracts.py`）；契约面：`evals/business/README.md`、
  `tools/lab/adapter-protocol.md`、`docs/host-platform-facts.md` C9。

决策依据（当年待补项）已闭合：print 模式权限行为即 `docs/host-platform-facts.md` C8
（文件访问按 cwd + `--add-dir` 划界、denial 不进审批计数），flag 组合的实跑行为登记为 C9，
待首次真实评测核实。

## 变更记录

- 2026-09-14 12:04 · 建档（open）· AF-002 诊断证据入库。
- 2026-09-16 12:03 · 备注更新（handoff P0 待办挂起）。
- 2026-09-18（0.8.1 批转状态）· 0.8.0 落地选项 A · 转 `fixed-pending-review`；`regression_status: not-run`
  （修复是适配器机制 + stub 级验证，真实用例能否跑通要等 G4 首次评测确认后转 `verified`）。

## 备注

- 观察环境：Claude Code 2.1.268 + 网关映射模型；其他宿主行为未验证。
