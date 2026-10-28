# 关闭证据门 — 验收标准（spec/qa）

## 0. 来源对齐缺口（GAP）

### 0.1 GAP 台账

| 编号 | 缺口 | 来源 | 状态 |
| --- | --- | --- | --- |
| GAP-01 | `docs/issues/README.md` 声称 schema 不按状态强制，与 0.13.0 起实际行为相反 | 阅读 `docs/issues/README.md` 与 `schemas/bug-record.schema.json` 对照 | 已由 M01 承接 |
| GAP-02 | 非 open 记录的 `## 变更记录` 只有散文要求，机器不查 | `tools/lab/gate/records.py` 现状 | 已由 M02 承接 |
| GAP-03 | schema 条件只钉了一个负例（缺 closure_criteria） | `tests/test_gate_schema.py` 现状 | 已由 M03 承接 |

无未关闭阻塞项。

## 1. 目标范围与不做

- 覆盖：契约文档同步、非 open 流转记录检查、schema 条件的完整负例回归。
- 不做：改 schema、`fix_revision` 强制、`verified` 归档、历史记录回改、版本号与发布动作。

## 2. 边界与异常覆盖

| 边界 | 期望 | 覆盖方式 |
| --- | --- | --- |
| verified 缺 `closure_criteria` | FAIL，点名字段 | 负例 T03-01 |
| verified 缺 `reviewer` / `review_decision` / `regression_status` | FAIL，分别点名 | 负例 T03-02 |
| verified 的 `review_decision=changes_requested` | FAIL | 负例 T03-03 |
| verified 的 `regression_status=not-run` | FAIL | 负例 T03-03 |
| rejected 缺 `rejection_reason` | FAIL | 负例 T03-04 |
| 非 open 缺 `## 变更记录` | FAIL，固定文案 | 负例 T03-05 |
| verified 合法正例 | PASS | 正例 T03-06 |
| 既有 66 条记录 | 全部 PASS | `validate.py artifacts` |
| `fixed-pending-review` | 不新增标题必填，保持可退回 open | 存量 5 条 PASS |

## 3. 模块验收点

### M01 契约文档同步

- `docs/issues/README.md` 不再出现「当前 schema 尚不按状态强制该字段」；新增状态条件矩阵，写明 verified 四项与 approved/pass、rejected 拒绝原因、非 open `## 变更记录`。
- 模板的条件字段一览与 README 一致。
- 判据：`grep -c "尚不按状态强制" docs/issues/README.md` 为 0；README 命中「变更记录」「approved」「pass」。

### M02 流转记录门

- `status != open` 的正文必须含 `## 变更记录`。
- 判据：`validate_bug_markdown` 对缺该节的记录返回固定文案错误。

### M03 回归与证据

- schema 条件与新增标题检查各有负例；正例通过；三道门原始输出入 `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md`。
- 判据：`unittest` 全绿；`doc_chain.py` 全绿；`validate.py all` 与基线一致。

## 4. AC×用例覆盖映射

| AC | 用例 | 判据 |
| --- | --- | --- |
| G1-AC-01 | T04-01 | 旧表述零命中；README 含状态条件矩阵 |
| G1-AC-02 | T04-01 | 模板与 README 的条件字段一致 |
| G2-AC-01 | T03-05 | 非 open 缺 `## 变更记录` → 错误含 `变更记录` |
| G3-AC-01 | T03-01、T03-02 | verified 缺四项任一项 → 错误逐字段点名 |
| G3-AC-02 | T03-03 | changes_requested / not-run → 错误含对应字段 |
| G3-AC-03 | T03-04、T03-06 | rejected 缺理由报错；合法 verified 无错误 |
| G3-AC-04 | T04-02 | 存量 66 条记录 PASS；原始输出入 `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md` |

## 5. 发布要求与结论

- 本批不改 manifest 版本、不写 CHANGELOG、不推送、不重装宿主；版本与发布由集成会话统一处理（避免与在途批次争用 0.21.0）。
- 独立评审未跑，不得宣告批次完成；验收结论以 `plan/PLAN-CLOSE-001.md` 与 `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md` 为准。
