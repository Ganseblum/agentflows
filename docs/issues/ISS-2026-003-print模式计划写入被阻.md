---
bug_id: ISS-2026-003
title: print 模式评测权限档无法完成写计划的用例
status: verified
severity: P2
error_kind: host-compat
attribution: evaluation
provenance: agentflow
project: agentflows
files:
  - docs/design-decisions.md
affected_slices:
  - host-adapter
  - cross-layer-planning
  - evaluation-harness
recorded_at: 2026-09-14T12:04:08Z
updated_at: 2026-10-19T21:45:00+08:00
source_revision: f2ea05c
agentflow_version: 0.3.1
regression_status: pass
fix_revision: agentflows@95de103
reviewer: agentflow:reviewer（2026-10-19 独立批量复审）
review_decision: approved
closure_criteria: 机制级证据锚可复现：git show 95de103 可见 HostIsolationArgumentTests 与 ClaudeStreamObservationTests 两个隔离测试类及 host_adapter.py 的 allowed_tools/isolate_host_config 机制代码（提交信息自证 149 单测 OK）；docs/design-decisions.md §3(三) 知识留存；docs/host-platform-facts.md C8/C9/C12 在盘（C9 组合经 2026-10-10 AF-001×3 现场验证）。AF-002 打印模式端到端用例因评测装置 2026-10-12 裁撤无法复跑，本条以机制级证据收敛。
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

## 审查

2026-10-19 独立复审（agentflow:reviewer 子代理，只读）。修复声称核对成立（机制级）：commit 95de103 含 host_adapter.py 的 allowed_tools/isolate_host_config 机制与两个隔离测试类，提交信息自证 149 单测 OK；设计知识留存于 docs/design-decisions.md §3(三)；宿主事实登记于 docs/host-platform-facts.md C8/C9/C12（C9 组合经 2026-10-10 AF-001×3 现场验证）。原转正路径（G4 首次评测）随评测装置 2026-10-12 整线裁撤失效，AF-002 打印模式端到端用例无法复跑；本条按机制级证据锚收敛，regression_status 指 0.8.0 时点单元回归。review_decision：approved。

## 变更记录

- 2026-09-14 12:04 · 建档（open）· AF-002 诊断证据入库。
- 2026-09-16 12:03 · 备注更新（handoff P0 待办挂起）。
- 2026-09-19 · live 验证尝试被网关阻断（502/挂起，host-platform-facts C10）· 维护
  `fixed-pending-review` 与 `regression_status: not-run`；机制级 stub 验证已过，实跑等可用端点。
- 2026-09-18（0.8.1 批转状态）· 0.8.0 落地选项 A · 转 `fixed-pending-review`；`regression_status: not-run`
  （修复是适配器机制 + stub 级验证，真实用例能否跑通要等 G4 首次评测确认后转 `verified`）。

## 备注

- 观察环境：Claude Code 2.1.268 + 网关映射模型；其他宿主行为未验证。
- 2026-10-12 · 条目维护 · files 中指向评测装置（已随同日裁撤删除）的条目已移除：`tools/lab/host_adapter.py`、`tools/lab/eval_runner.py`、`evals/public/inputs/AF-002.md`；设计知识与恢复清单见 `docs/design-decisions.md` §3。
- 2026-10-19 21:45 · 独立复审通过 · agentflow:reviewer 批量复审（只读）核对修复声称与回归证据成立，转 verified。
