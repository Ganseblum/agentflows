# Improvement artifacts

improve 环的交接落盘面：一条候选改进从假设到发布裁决的四类 JSON 工件。工具产出工具写、人裁决
supervisor 写——evaluation result 与 comparison 由冻结的 runner 原样写出，candidate record 与
release record 由 supervisor 依裁决写出；evaluator 只读。文件名即身份：candidate record 的
stem 必须等于 `candidate_version`，evaluation result 的 stem 必须等于 `result_id`；comparison
与 release record 没有自有 id，其身份是它们声明的结果对。

## 布局与契约

```text
records/improvement/
  candidates/   <candidate_version>.json   # 预先声明的候选（假设、证据、守门与拒绝标准）
  evaluations/  <result_id>.json           # 冻结 runner 产出的基线/候选评测结果
  comparisons/  <slug>.json                # runner compare 的输出：结果对 + 上下文 + 八指标 deltas
  releases/     <slug>.json                # 发布裁决：内嵌 candidate、结果对、审批、回滚目标
  README.md
```

组织规则（一句话，防止后人当分裂缺陷重报）：**schema 的 2+2 分布是规则产物**——
`schemas/` 是确定性工具输出契约（evaluation-result、adapter-case-result、comparison），
`skills/improve/references/` 是 improve 环规则手册契约（candidate、eval-case、episode、
release-record、business-case）；工具产出归工具契约，人的裁决物归规则手册，不合并。

## 每类工件的契约

- **candidates/**：`skills/improve/references/candidate.schema.json`（`schema_version=1`、
  `candidate_version` 语义版本、`evidence_ids`、`risk_class`、`guardrails`、
  `rejection_criteria` 等）。文件名 = `candidate_version`，子树内唯一。`evidence_ids` 按
  前缀条件解析：`EP-*` 必须命中 `records/episodes/` 现存 episode_id，`BUG-*` 必须命中
  `records/bugs/` 现存 bug_id，其他形态不查。
- **evaluations/**：`schemas/evaluation-result.schema.json`，并复用评测不变量
  （`suite_case_count` = case 数、`repeat_count` = 每例重复数、`observed_context` 与声明一致）。
  文件名 = `result_id`，子树内唯一。
- **comparisons/**：`schemas/comparison.schema.json`——runner `compare` 的原样输出：
  `baseline_result_id` / `candidate_result_id`、七字段执行上下文、八指标 `deltas`（可为负）、
  两份 summary。同一结果对只允许出现一次。
- **releases/**：`skills/improve/references/release-record.schema.json`。内嵌 `candidate`
  对象必须与 `candidates/` 下对应文件 JSON 全等（按内嵌 `candidate_version` 定位，必须存在）；
  `baseline_results.result_id` / `candidate_results.result_id` 必须解析到 `evaluations/` 现存
  记录；必须存在一条 comparison 与其结果对相同。`rollback_to` 指向发布指针，不做跨文档解析。

## 交叉校验

`python3 tools/lab/validate.py artifacts` 除逐文件 schema 外，还编译跨文档声明：comparison
引用的两个 result 必须存在且 `source_kind` 分别为 baseline/candidate、七字段上下文彼此一致
且等于 comparison.context；release 的内嵌 candidate 与结果对声明必须落到现存文件；candidate
的 `EP-*`/`BUG-*` 证据必须命中现存记录。校验不过即编译错误——无效记录不得被下一个角色引用。

回溯：

```sh
python3 tools/lab/validate.py artifacts                 # 编译门
jq -r '[.baseline_result_id, .candidate_result_id] | @tsv' records/improvement/comparisons/*.json
jq -r '[.decision, .candidate.candidate_version] | @tsv' records/improvement/releases/*.json
```
