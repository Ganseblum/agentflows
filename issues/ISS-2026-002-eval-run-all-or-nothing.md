---
bug_id: ISS-2026-002
title: 单次调用超时即中断整个评测运行，且无诊断信息
status: verified
severity: P2
error_kind: missing-constraint
attribution: product_code
provenance: agentflow
project: agentflows
files:
  - tools/lab/host_adapter.py
affected_slices:
  - host-adapter
  - evaluation-harness
recorded_at: 2026-09-14T12:04:08Z
updated_at: 2026-09-17T16:00:00Z
source_revision: f2ea05c
agentflow_version: 0.3.1
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: 评审人指定检查符合预期：`python3 tools/lab/host_adapter.py --host claude --progress <jsonl>` 输入含不支持 permissions_profile 的 public 请求时退出码 1；progress.jsonl 恰两行（`start` 与 `failed`，case_id 均 `PROGRESS-CHECK`，`failed` 行含 `elapsed_ms` 与 `error`）；stderr 出现 host adapter 前缀的逐调用失败行（PROGRESS-CHECK repetition 1 failed）；全程无宿主进程。
fix_revision: agentflow 0.3.2
---

## 现象

第一次完整 10 用例 baseline 在约 26 分钟后中止，`baseline-run.log` 只有：

```
adapter exited with 1
host adapter: claude timed out after 900 seconds
```

没有任何用例级记录、部分结果或进度信息——整个 run 作废，无法定位是哪个用例、第几次重复超时。

复现（确定性）：

1. `eval_runner.py run` 对 claude adapter，`--timeout-seconds 900`，公开 suite。
2. 让一个用例（24 分钟的跨层用例 AF-002）超时。
3. adapter 退出码 1，无用例级输出，无部分结果文件。

## 问题代码

修复前 `host_adapter.py` 把所有结果攒在内存里、最后一次性打印，失败只剩一个退出码：

```python
# tools/lab/host_adapter.py (before fix)
for case in cases:
    for repetition in range(1, request["repeat_count"] + 1):
        result = run_claude(...)          # 任何一次超时 → 整个 run 丢弃
        repetitions.append(result)
    results.append(...)
print(json.dumps({... "case_results": results}))   # 只在全部成功后输出一次
```

## 根因

adapter 设计里没有任何每次调用的进度记录和部分结果落盘——失败处理只有最终退出码。
这属于当时设计缺少约束（missing-constraint）：没有人规定"单次失败必须可归因"。

## 修复

`host_adapter.py` 新增 `--progress <jsonl>` 与逐调用 stderr 状态行：

```python
write_progress(progress_path, {"event": "start", "case_id": case["case_id"], "repetition": repetition})
try:
    result = run_claude(...)
except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
    write_progress(progress_path, {"event": "failed", "case_id": case["case_id"],
                                   "repetition": repetition, "error": str(exc)})
    raise
write_progress(progress_path, {"event": "completed", ..., "accepted": result.get("accepted")})
```

纯诊断性质，不改变评测语义，`eval_runner.py` 不消费它。

## 回归检查

- 通过：带 `--progress` 重跑，`baseline-progress.jsonl` 精确记录每次调用，定位到 AF-002 repetition 1 在 900 秒超时。

## 备注

- 超时的 run 仍会丢弃内存中结果，只有诊断存活；部分结果持久化/断点续跑未实现（已知边界）。
- AF-002 本身仍超默认 900 秒上限，相关权限问题另见 ISS-2026-003。

## 审查

评审人 `agentflow:reviewer` 于 2026-09-17 批量评审本批 8 条 `fixed-pending-review` 记录。
本条指定检查 C0（全量确定性检查）与 C2（progress 诊断路径注入），由 supervisor 执行并
回传原始输出；结论 `approved`，本记录转 `verified`，`fix_revision` 据实回填为
agentflow 0.3.2。C2 首次执行因 supervisor 转录漏一行而失败，属执行者差错，更正后重跑
通过——如实记录，以下为重跑的逐字输出。

决定性证据（supervisor 回传，逐字输出）：

C0 —— `python3 tools/lab/validate.py all`：

```
8/8 PASS, exit 0
```

C2 —— `python3 tools/lab/host_adapter.py --host claude --progress <jsonl>`，输入为含不支持
permissions_profile 的 public 请求：退出码 1，全程无宿主进程。progress.jsonl 恰两行：

```
{"event": "start", "case_id": "PROGRESS-CHECK", "repetition": 1}
{"event": "failed", "case_id": "PROGRESS-CHECK", "repetition": 1, "elapsed_ms": 1, "error": "unsupported claude permissions_profile: 'definitely-unsupported-profile'"}
```

stderr 含逐调用失败行：

```
host adapter: PROGRESS-CHECK repetition 1 failed: ...
```

## 变更记录

- 2026-09-17 · 独立评审通过 · agentflow:reviewer 批量评审指定检查（C0–C8），supervisor 执行并回传原始输出，转 verified。
