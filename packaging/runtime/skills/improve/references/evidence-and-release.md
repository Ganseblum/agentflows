# 证据与发布规则

## 证据层级

优先采用外部可观察的信号，而不是 Agent 的自我评估：

1. 用户验收、拒绝、纠正或回滚；
2. 确定性测试与验收检查；
3. 带文件级证据的独立 reviewer 决策；
4. 任务完成、工具错误、重试、时延与成本；
5. 执行 Agent 自己的摘要。

正、负 episode 都要保留。不要让工作流只训练在失败上，或只训练在到达完成态的任务上。

episode 应记录这样的逻辑形态。`revision`、`run`、`claims` 与 `evidence` 让结果可被独立核对；`complete` 的运行不得仅凭 agent 摘要推断：

```json
{
  "schema_version": 1,
  "episode_id": "stable-id",
  "revision": {"source": "git:<revision>", "base": "git:<parent>"},
  "run": {"run_id": "run-id", "started_at": "2026-09-18T00:00:00Z", "ended_at": "2026-09-18T00:01:00Z", "status": "complete"},
  "claims": [{"claim_id": "C-1", "claim": "the stated outcome", "status": "verified", "check": "command or reviewer", "evidence_ref": "E-1"}],
  "evidence": [{"evidence_id": "E-1", "kind": "test", "ref": "path:line or command output"}],
  "source_type": "user_feedback | acceptance | test | review | incident | rollback",
  "objective": "what the task was expected to achieve",
  "outcome": "accepted | rejected | partial | failed | unknown",
  "signals": [],
  "feedback_summary": "sanitized factual summary",
  "agentflow_version": "0.2.0",
  "host": "codex | claude-code | zcode | other",
  "provenance": {"carrier": "<session carrier>", "sanitized": true},
  "redactions": [],
  "review_roundtrips": []
}
```

机器可读契约是 [episode.schema.json](episode.schema.json)。

引用来源证据要使用稳定引用。不要存密钥、原始凭证或不必要的完整转录。

## 失败归因

在提出改动之前，对每个 material 失败分类：

- `workflow_policy`：角色选择、委派、门、重试或决策规则；
- `role_prompt`：某个专家误解了自己的职责；
- `context`：所需的项目或任务信息缺失；
- `tool_or_host`：宿主工具、沙箱、权限或集成失败；
- `model_limit`：所选模型无法可靠完成该任务；
- `product_code`：仓库自身有缺陷；
- `evaluation`：评分标准、fixture 或判定器无效；
- `unknown`：证据不足。

通常只有前两类可以正当支撑修改 Agentflow 指令。context 失败可以支撑新的接案检查。其它类别要在各自的边界内修复。

## 发布记录

完成后的发布门产出一条这样的记录。下面的例子是一次**方法级晋升**（`measurement: none`）：它通过
`release-record.schema.json` 校验，也是当前装置状态下唯一可用的晋升形态——评测套件、runner 与
对照结果契约已随 2026-10-12 裁撤，所以不再有 `baseline_results` / `candidate_results` 可填
（两者仅在 `measurement: complete` 时必填）。

```json
{
  "schema_version": 1,
  "candidate": {
    "schema_version": 1,
    "candidate_version": "0.3.0-rc.1",
    "parent_version": "0.2.0",
    "source_revision": "git:<frozen parent revision>",
    "artifact_digest": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "hypothesis": "one falsifiable improvement claim",
    "evidence_ids": ["EP-20260101-001"],
    "changed_components": ["agents/reviewer.md"],
    "risk_class": "low",
    "primary_metrics": ["review first-pass rate (declared intent, not instrumented)"],
    "guardrails": ["no protected slice regresses"],
    "rejection_criteria": ["any guardrail fails"],
    "protected_slices": ["role-selection"]
  },
  "measurement": {
    "status": "none",
    "basis": "human review: release governor approved 2026-01-01, evidence EP-20260101-001"
  },
  "evaluation_result": "neutral",
  "decision": "promote",
  "approvals": [
    {
      "actor": "agentflow:release-governor",
      "decision": "approved",
      "evidence_ref": "review round EP-20260101-001 / review_roundtrips[0]",
      "recorded_at": "2026-01-01T00:00:00Z"
    }
  ],
  "rollout": {"mode": "human-gated"},
  "rollback_to": "0.2.0"
}
```

`evaluation_result` 是**证据等级**字段，不是晋升许可证：它照实记录该候选相对基线的判定，没有
仪器化度量时通常记为 `neutral`（方法级改动没有对照面），而晋升许可来自下面这条规则。当
`measurement: none` 时，晋升的正确性由人工评审承载，`evaluation_result` 不再被要求为 `better`。

候选预声明用 [candidate.schema.json](candidate.schema.json)，完成后的门用
[release-record.schema.json](release-record.schema.json)（以上两份契约文件仍在）。
**冻结用例与对照结果的原契约（`eval-case.schema.json`、`comparison.schema.json`）已随
2026-10-12 评测装置裁撤删除**——本轮及以后的方法级改动一律 `measurement: none`；恢复仪器化时
按 `docs/design-decisions.md` §3 的重建清单一并恢复契约
（届时 `baseline_results` / `candidate_results` 再次成为 `measurement: complete` 的必填项，
晋升也重新要求 `evaluation_result: better`）。

把记录绑定到确切的源码与评测 revision 以及不可变的产物摘要。不要复用另一个候选的结果。受保护切片独立评测；聚合改进不能掩盖被声明切片里的回归。

## 评测隔离（恢复仪器化后适用）

评测套件与隔离 runner 已随 2026-10-12 装置裁撤，本节条款当前无对照面可挂载——留存为恢复
仪器化时的施工要求（重建清单见 `docs/design-decisions.md` §3）。
恢复后：

- 在实现候选之前定义评分标准与阈值。
- 让 holdout 答案对 candidate engineer 不可得。
- 不要让同一处改动同时修改 Agentflow 行为与评判它的门。
- 用相同的宿主、模型、权限、fixture 与重复次数比较 baseline 与候选。
- 按任务切片评测，使平均值无法掩盖关键回归。
- 把 evaluator 分歧与小样本当作不确定性，而不是候选的成功。

推荐的主指标是任务验收率、评审一次通过率、纠正次数与逃逸缺陷。护栏包括权限违规、关键回归、成本、时延、工具失败与不必要的委派。

## 发布门

发布门由一条可执行的晋升规则判定，`measurement` 决定它走哪一支：

- **`measurement: complete`（有仪器化度量时）**：`promote` 要求 `evaluation_result: better`，
  且记录同时带 `baseline_results` 与 `candidate_results` 两份对照结果。
- **`measurement: none`（方法级改动，当前装置状态下的唯一形态）**：没有可产生 `better` 的
  对照面，因此 `promote` 要求 `measurement.basis` 写为**人工评审**（human review）并附评审引用——
  `approvals` 中至少一条 `decision: approved` 带非空 `evidence_ref`，指向触发该候选的评审
  轮次或事故记录。此时 `evaluation_result` 照实记（没有对照面通常为 `neutral`），不伪装成已
  验证的改进。

两支共同仍要求：

- 候选修复了关键缺陷，或（仅 complete 支）已声明的主指标改善；
- 没有受保护任务切片或安全/权限护栏越过其阈值回归；
- 必需的确定性检查通过；
- 独立评审完成（none 支即以人工评审承载）；
- 其风险等级允许所选发布模式；
- 回滚目标可用且已验证；
- 必需的人工批准已记录。

**`measurement: none` 时禁止 `promote` 配 `evaluation_result: better`**：那是把无人对照的推断
记成已验证的改进，本环最不该犯的错。这一条与 [release-record.schema.json](release-record.schema.json)
的 `allOf` 分支、`skills/improve/SKILL.md` 的「度量范围与晋升规则」段逐字一致。

提示词措辞与角色描述在流程被证明之后可以取得 canary 资格。权限、工具、hook、MCP、evaluator 规则、发布规则与自动阈值保持人工把门。**注意当前装置下 canary 与 automatic 均不可达**（2026-10-26 审核 G07）：无自动监控/回滚执行面，且 `automatic` 要求 `evaluation_result: better` 而 `measurement: none` 结构上禁止它——详见 `SKILL.md` 的晋级模式注。

## 版本与回滚

源码存于 Git，发布不可变的语义化版本。晋级通过改变指向某个已评测版本的安装或发布指针完成。回滚通过重新指向记录的父版本或回滚版本完成；不要就地修复线上的安装。

发布记录保持只增不改。之后的更正新建一条记录，而不是改写更早决策的证据。
