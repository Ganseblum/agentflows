# Episodes

任务级证据的最小落盘：一条 episode = 一次任务的最终决策记录的持久化形态（目标、结论、
claims、评审决策、成本）。写在会话结束**之前**——对话历史一旦消失，episode 就不可恢复，
而「没有投诉不等于成功」的前提是证据先活下来。

## 布局与契约

```text
episodes/
  2026-09-16/
    EP-20260916-001.json        # 文件名 = episode_id（校验器强制，全局唯一）
  README.md
```

契约**复用** improve 环的既有
[`skills/improve/references/episode.schema.json`](../skills/improve/references/episode.schema.json)
（在保护门内），不另设平行载体。字段速览：`schema_version=1`、`episode_id`、`source_type`（user_feedback / acceptance / test / review / incident / rollback）、`revision`（source/base）、`run`（run_id/时间/状态）、`claims`（每条带可执行 check）、`evidence`（稳定引用）、`objective`、`outcome`
（accepted / rejected / partial / failed / unknown）、`signals[]`（kind + value +
evidence_ref）、`review_roundtrips[]`（0.7.2 引入、0.8.0 起必填：每轮独立评审一行——`at` / `reviewer` /
`decision`（approved / changes_requested / blocked）/ `finding` / `resolution` /
`evidence_ref`；含未通过的轮次与分歧如何收场，中途评审分歧由此可审计）、
`feedback_summary`、`agentflow_version`、`host`、`provenance`、`redactions`。

要点：

- **谁写**：supervisor 在会话收口时写（final decision record 的落盘动作，不需要新角色）。
- **何时写**：0.7.2 起 material 改动（开过独立评审门的）一律写，不再限于「可能喂给改进环」
  的任务；评审每一轮（含 `changes_requested` 与分歧收场）落 `review_roundtrips`。outcome 用
  worker result 同一语义——预算耗尽是 `partial`，永不 `complete`。`review_roundtrips` 自
  0.8.0 起 schema 必填：没开过评审门的任务写 `[]`；早于该字段的历史 episode 以 `[]` 回填，
  并在 `signals[]` 加一条 `review_roundtrips_backfill` 说明「未捕获」与「没有评审」的区别，
  不虚构当时没有结构化记录的轮次。
- **负向 episode 必须收录（0.8.0 约定，针对生存者偏差）**：`outcome: rejected / partial /
  failed` 的任务与 `accepted` 一样是一等证据。独立评审 `changes_requested` 后放弃或返工的
  任务、被门拦下的候选、预算耗尽的中断，都要落 episode；只挑成功任务落盘会让改进环把
  「没做坏过」误读成「不会做坏」。supervisor 收口自检：这批任务里有没有一条没写、正因为它
  失败了？
- **脱敏**：`redactions` 声明已脱敏的内容；凭证与私人对话内容不进 episode。
- **provenance**：`carrier`（会话载体）与 `sanitized`（是否已脱敏）两键必填，schema 强制
  `additionalProperties: false`——多余键会被拒。
- **校验**：`python3 tools/lab/validate.py artifacts` 强制 schema、文件名 = episode_id、
  id 全局唯一。

## 与其他记录的关系

bug 记录（`issues/`）承载**缺陷**证据；episode 承载**任务级**证据——正常完成的任务、
被门拦下的任务、成本与摩擦，都是 improve 环的输入。两者共同构成 feedback-analyst 的证据池。

回溯：

```sh
python3 tools/lab/validate.py artifacts                 # 编译门
jq -r '[.occurred_at, .episode_id, .source_type, .outcome] | @tsv' episodes/归档/*/*/*.json episodes/2*/2*/*.json | sort
```

## 存档策略（归档）

episode 是任务级证据的最小落盘，会随时间累积。为保持 `episodes/` 顶层只放「当期」目录、
又不丢历史，采用与 `docs/issues/归档/` 一致的口径：

- 目录按**月份**归档到 `episodes/归档/<YYYY-MM>/`，整月目录原样搬入（目录名保留原 `YYYY-MM-DD`，
  不重命名，文件名仍 = episode_id，唯一性不变）。
- 仅搬**整月目录**；`README.md` 始终留在 `episodes/` 顶层，不进归档。
- 归档是纯移动，不删内容、不重写证据；被挡在门外的候选、预算耗尽的中断等负向 episode
  也一并保留（见上「负向 episode 必须收录」）。
- 归档后 `episodes/*/*.json` 的回溯命令会继续命中归档目录，无需改脚本。
- 触发时机：每月初把上月（及更早）的目录归档一次；当前月的目录留在顶层为「当期」。

> 注意：live record 门（`validate_workspace_artifacts`）只认 `episodes/` 直接下的 `*.json`，
> 不会下钻 `episodes/归档/`，因此归档后的目录不再计入门扫描——这正是「历史移出当期面」的预期，
> 不视为记录丢失。
