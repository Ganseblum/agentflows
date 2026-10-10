# 宿主 adapter 协议

`eval_runner.py run` 向显式提供的 adapter 命令发送一个 JSON 请求。仓库内含 `host_adapter.py`，被
显式调用时会把该请求转换为 `codex exec` 或 `claude --print`。

Claude 路径可用 `--plugin-dir` 加载候选工作树。Codex CLI 路径对 `source_kind=candidate` 刻意
fail-closed，因为当前 CLI 不暴露任何按调用的本地 Plugin 源绑定；它不得在把结果标注为 candidate
的同时悄悄评测已安装的 baseline。
adapter 运行所请求的宿主/模型/权限配置，并在 stdout 上返回一个 JSON 对象：

```json
{
  "observed_context": {
    "host": "codex",
    "model": "example-model",
    "permissions_profile": "read-write-workspace",
    "fixture_revision": "fixture-001",
    "evidence_refs": ["adapter://codex/smoke-001"]
  },
  "case_results": [
    {
      "case_id": "AF-001",
      "slice": "role-selection",
      "holdout": false,
      "protected_guardrails": ["permission_violations", "escaped_defects"],
      "repetitions": [
        {
          "accepted": true,
          "first_pass_review": true,
          "correction_count": 0,
          "escaped_defects": 0,
          "permission_violations": 0,
          "unnecessary_delegation": false,
          "tool_failures": 0,
          "latency_ms": 1200,
          "evidence_refs": ["result://AF-001/1"]
        }
      ]
    }
  ]
}
```

runner 拥有执行身份，并在结果 manifest 中重复它。重复编号恰好是 1..repeat_count；被跳过或捏造的
重复无效，测量到的延迟由 adapter 在 schema 校验之前注入。业务用例的 `accepted` 与
`escaped_defects` 归 grader 所有，而不是宿主的声明。adapter 不能更改声明的宿主、模型、权限配置、
fixture 版本、套件版本或重复次数。只有当这些字段完全匹配时，Baseline 与 Candidate 的结果才可比。

### 隔离与观测通道（0.8.0）

两个可选的请求字段会改变 claude 的调用；两者在 codex 上都会被大声拒绝，而不是被忽略：

- `allowed_tools`（工具规格数组，不含逗号）：通过 `--allowed-tools` 精确预批准恰好需要的工具，
  而不是依赖 `acceptEdits`——print 模式会用权限拒绝覆盖它，而这些权限拒绝随后会伪装成工作流
  行为。
- `isolate_host_config`（布尔值）：为本次调用加上 `--strict-mcp-config` 与一个临时
  `CLAUDE_CONFIG_DIR`，使操作者的全局 MCP/slash 配置不会泄漏到运行中。权威的 baseline/candidate
  运行必须同时设置两者；`observed_context` 会记录 `allowed_tools` 与 `mcp_isolated`。

每次 claude 调用都以 `--output-format stream-json` 运行；adapter 会扫描出错的工具结果中的权限
拒绝标记，并把计数写入 `observed_permission_denials`（按每次重复，覆写模型在该键下自报的任何
内容）。这是一个启发式观测通道，而不是宿主契约；codex 没有该通道，因此键缺失意味着“未观测”，
绝不是 0。

当被测工作区（模型的 cwd）下存在任何 `*.seeds.json` 文件时，业务请求还会额外 fail-closed：构建
被测副本时排除 `evals/business/seeds/`。评分从受信任的 `repository_root` fixture 副本读取种子，
该副本必须仍然携带它们。

runner 还会发送 `holdout: false` 与精确的按用例重复次数。holdout 用例在到达 adapter 之前就被
拒绝。Adapter 响应必须恰好覆盖每个冻结用例一次，保留其 slice/guardrail 元数据，提供每一次重复，
并为每次重复与观测上下文返回至少一个证据引用。

使用 `eval_runner.py compare` 生成指标差值，然后用 `policy.py` 配合预先声明的候选记录。policy
结果是供人工发布门使用的证据；它不安装或发布任何东西。

候选的 `artifact_digest` 值由 `artifact_digest.py` 生成。摘要包含规范化后的相对路径、普通文件
mode 位、大小与内容哈希；`.git` 与 Python 缓存目录被排除，符号链接被拒绝，manifest 格式是
确定性的。

约束本协议的已观测宿主行为——schema 元声明拒绝、print 模式权限边界、配置继承、网关模型标签
完整性以及按用例延迟——连同其证据记录在 [宿主平台事实](../../docs/host-platform-facts.md)。请依据
真实运行更新该表，而不是凭记忆。

对于更长的运行，传入 `host_adapter.py --progress <path>` 可为每次调用追加一条诊断 JSONL 记录
（`start`、`completed`，或带耗时与错误的 `failed`）。进度记录仅是操作者诊断信息：它们不是
adapter 结果的一部分，不改变评测上下文，也从不被 `eval_runner.py` 消费。

某些宿主会拒绝 Draft 2020-12 的 `$schema`/`$id` 声明（位于 `--json-schema` 内部）。adapter 在调用
Claude 之前剥掉这两个键；schema 主体仍完整约束结构化输出，而 Codex 收到的是原始文件路径。
