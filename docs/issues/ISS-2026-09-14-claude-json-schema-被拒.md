---
bug_id: ISS-2026-09-14-claude-json-schema-被拒
title: Claude Code 的 --json-schema 拒绝携带 Draft 2020-12 元声明的 schema
status: verified
severity: P1
error_kind: host-compat
attribution: tool_or_host
provenance: agentflow
project: agentflows
files:
  - docs/design-decisions.md
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
closure_criteria: 评审人指定检查符合预期：`python3 tools/lab/validate.py all` 退出码 0（8/8 PASS）；`host_adapter.host_output_schema` 投影检查退出码 0，输出不含 `$schema`/`$id` 且逐键等于原文档剥键结果；`run_claude` 传投影文本、`run_codex` 传原文件；宿主级接受度由 `docs/host-platform-facts.md` C1 行已录 smoke 承担。
fix_revision: agentflow 0.3.2
---

## 现象

第一次 AF-001 smoke 在约 1 秒内失败，模型调用根本没发生。`host_adapter.py --host claude`
退出码 1，stderr 原文：

```
host adapter: Error: --json-schema is not a valid JSON Schema: no schema with key or ref "https://json-schema.org/draft/2020-12/schema"
```

复现（确定性）：

1. 用 `eval_runner.build_request` 构造 AF-001 单用例请求，管道传给 `host_adapter.py --host claude`。
2. schema 文件保持原样（携带 `$schema` 和 `$id` 元声明）。
3. 约 1 秒内 claude 退出码 1，报上述 meta-schema 错误。

## 问题代码

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

问题文件：`tools/lab/host_adapter.py`（run_claude）与对照 schema（均随 2026-10-12 评测装置裁撤删除，
证据见 `agentflows@cc03012` 的对照 schema（「adapter case result」契约）；携带 Draft 2020-12 元声明）。

## 根因

Claude Code 2.1.268 的 `--json-schema` 校验器不解析 Draft 2020-12 的 meta-schema URI，
adapter 又把 schema 文档原样透传，没有为宿主做投影。schema 本身合法，坏在传输方式——
属于宿主兼容问题（host-compat），不是 schema 或宿主的单独过错。

## 修复

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

## 回归检查

- 通过：修复后 AF-001 smoke 完整跑通（约 212 秒），返回 schema 合法结果，未出现上一台机器的 502。
  命令：`python3 tools/lab/host_adapter.py --host claude < agentflow-lab/request-af001.json`

## 备注

- 状态保持 `fixed-pending-review`：修复经过 smoke 验证，但尚无独立 Reviewer 批准，按规则不得写 verified。
- 已记入 `docs/host-platform-facts.md`（Claude Code C1）。
- 修复尚未提交（working tree），提交后更新 `source_revision`。

## 更正（2026-09-14）

记录创建时的“修复尚未提交”是当时的时间点证据。后续修复已在提交 `77e1577` 落地，
并已由当前工作树保留；`source_revision: f2ea05c` 仍表示问题发现时的源版本，不表示修复
仍未提交。状态继续保持 `fixed-pending-review`，直到独立 Reviewer 批准。

## 审查

评审人 `agentflow:reviewer`（独立评审角色）于 2026-09-17 对本批 8 条 `fixed-pending-review`
记录做批量评审。本条指定检查 C0（全量确定性检查）与 C1（schema 投影检查），由 supervisor
执行并回传原始输出；结论 `approved`，本记录转 `verified`，`fix_revision` 据实回填为
agentflow 0.3.2。

决定性证据（supervisor 回传，逐字输出）：

C0 —— `python3 tools/lab/validate.py all`：

```
8/8 PASS, exit 0
```

C1 —— 投影检查（`python3` 调 `host_adapter.host_output_schema`，入参
`agentflows@cc03012` 的对照 schema）输出，退出码 0：

```
OK host_output_schema: only $schema/$id stripped, body intact
```

宿主级接受度按评审人提案由 `docs/host-platform-facts.md` C1 行已录 smoke 承担。

## 变更记录

- 2026-09-17 · 独立评审通过 · agentflow:reviewer 批量评审指定检查（C0–C8），supervisor 执行并回传原始输出，转 verified。
- 2026-10-12 · 条目维护 · files 中指向评测装置（已随同日裁撤删除）的条目已移除：`tools/lab/host_adapter.py`、`（已删的对照 schema，见正文：adapter case result 契约）`；设计知识与恢复清单见 `docs/design-decisions.md` §3。
