---
bug_id: BUG-20260914-001
title: Claude Code rejects Draft 2020-12 schema declarations passed to --json-schema
status: fixed-pending-review
severity: high
error_kind: host-compat
attribution: tool_or_host
project: agentflows
files:
  - tools/lab/host_adapter.py
  - schemas/adapter-case-result.schema.json
affected_slices:
  - host-adapter
  - evaluation-harness
recorded_at: 2026-09-14T12:04:08Z
updated_at: 2026-09-14T12:40:00Z
source_revision: f2ea05c
agentflow_version: 0.3.1
regression_status: pass
---

## Symptom

第一次 AF-001 smoke 在约 1 秒内失败，模型调用根本没发生。`host_adapter.py --host claude`
退出码 1，stderr 原文：

```
host adapter: Error: --json-schema is not a valid JSON Schema: no schema with key or ref "https://json-schema.org/draft/2020-12/schema"
```

复现（确定性）：

1. 用 `eval_runner.build_request` 构造 AF-001 单用例请求，管道传给 `host_adapter.py --host claude`。
2. schema 文件保持原样（携带 `$schema` 和 `$id` 元声明）。
3. 约 1 秒内 claude 退出码 1，报上述 meta-schema 错误。

## Problem code

修复前 `run_claude` 把 schema 文件原文直接传给宿主：

```python
# tools/lab/host_adapter.py (before fix)
def run_claude(request, prompt, workspace, schema, timeout):
    schema_text = schema.read_text(encoding="utf-8")   # 原文含 $schema/$id
    command = [
        "claude", "--print", ...,
        "--json-schema", schema_text,   # Claude Code 2.1.268 在此拒绝加载
        ...
    ]
```

问题文件：`tools/lab/host_adapter.py`（run_claude）、`schemas/adapter-case-result.schema.json`（携带 Draft 2020-12 元声明）。

## Root cause

Claude Code 2.1.268 的 `--json-schema` 校验器不解析 Draft 2020-12 的 meta-schema URI，
adapter 又把 schema 文档原样透传，没有为宿主做投影。schema 本身合法，坏在传输方式——
属于宿主兼容问题（host-compat），不是 schema 或宿主的单独过错。

## Fix

`tools/lab/host_adapter.py` 新增 `host_output_schema()`，调用 Claude 前剥离 `$schema`/`$id`：

```python
def host_output_schema(schema: Path) -> str:
    """Return the case-result schema without meta-schema declarations some hosts reject."""
    document = json.loads(schema.read_text(encoding="utf-8"))
    for key in ("$schema", "$id"):
        document.pop(key, None)
    return json.dumps(document, separators=(",", ":"))
```

schema 主体保持不变，仍完整约束结构化输出；Codex 路径继续用原文件。

## Regression check

- 通过：修复后 AF-001 smoke 完整跑通（约 212 秒），返回 schema 合法结果，未出现上一台机器的 502。
  命令：`python3 tools/lab/host_adapter.py --host claude < agentflow-lab/request-af001.json`

## Notes

- 状态保持 `fixed-pending-review`：修复经过 smoke 验证，但尚无独立 Reviewer 批准，按规则不得写 verified。
- 已记入 `docs/host-platform-facts.md`（Claude Code C1）。
- 修复尚未提交（working tree），提交后更新 `source_revision`。
