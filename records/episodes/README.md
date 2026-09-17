# Episodes

任务级证据的最小落盘：一条 episode = 一次任务的最终决策记录的持久化形态（目标、结论、
claims、评审决策、成本）。写在会话结束**之前**——对话历史一旦消失，episode 就不可恢复，
而「没有投诉不等于成功」的前提是证据先活下来。

## 布局与契约

```text
records/episodes/
  2026-09-16/
    EP-20260916-001.json        # 文件名 = episode_id（校验器强制，全局唯一）
  README.md
```

契约**复用** improve 环的既有
[`skills/improve/references/episode.schema.json`](../../skills/improve/references/episode.schema.json)
（在保护门内），不另设平行载体。字段速览：`schema_version=1`、`episode_id`、`source_type`
（user_feedback / acceptance / test / review / incident / rollback）、`objective`、`outcome`
（accepted / rejected / partial / failed / unknown）、`signals[]`（kind + value +
evidence_ref）、`feedback_summary`、`agentflow_version`、`host`、`provenance`、`redactions`。

要点：

- **谁写**：supervisor 在会话收口时写（final decision record 的落盘动作，不需要新角色）。
- **何时写**：结果可能喂给改进环的任务都写；outcome 用 worker result 同一语义——预算耗尽
  是 `partial`，永不 `complete`。
- **脱敏**：`redactions` 声明已脱敏的内容；凭证与私人对话内容不进 episode。
- **provenance**：`carrier`（会话载体）与 `sanitized`（是否已脱敏）两键必填，schema 强制
  `additionalProperties: false`——多余键会被拒。
- **校验**：`python3 tools/lab/validate.py artifacts` 强制 schema、文件名 = episode_id、
  id 全局唯一。

## 与其他记录的关系

bug 记录（`records/bugs/`）承载**缺陷**证据；episode 承载**任务级**证据——正常完成的任务、
被门拦下的任务、成本与摩擦，都是 improve 环的输入。两者共同构成 feedback-analyst 的证据池。

回溯：

```sh
python3 tools/lab/validate.py artifacts                 # 编译门
jq -r '[.occurred_at, .episode_id, .source_type, .outcome] | @tsv' records/episodes/*/*.json | sort
```
