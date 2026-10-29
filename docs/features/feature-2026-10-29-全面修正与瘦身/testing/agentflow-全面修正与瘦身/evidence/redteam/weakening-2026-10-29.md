# 新判据的反证记录（2026-10-29，一次性副本实跑）

故障注入与判据削弱一律在 `cp`/`rsync` 出的副本上进行，不在工作树（`AGENTS.md`「实验与恢复」）。
副本方法：`rsync -a`（排除 `.venv`、缓存与 `.workbuddy`）到 `/tmp/af-redteam*`，再把仓内 `.venv` 软链接进去。

| 编号 | 削弱动作 | 期望 | 实跑观察（逐字摘录） | 判定 |
| --- | --- | --- | --- | --- |
| A | 删掉 `docs/PENDING-DECISIONS.md` 的独立声明行（表格里仍提及该词） | 判红，且不得被散文提及糊过去 | `FAIL decision_gate (1 error(s))` —「C18 decision-marker: docs/PENDING-DECISIONS.md 只在散文中提及该词，没有独立声明行——检查器按声明行认它」 | 通过。首轮此条曾为 `PASS`（断言只按子串认标记），已改判据为「声明行」后复跑转红 |
| B | 删掉 `validate_episode_document` 里的 `validate_episode_references` 调用点 | 逐函数用例仍可绿，**接线用例必须转红** | `Ran 9 tests … FAILED (failures=1)` | 通过。补接线用例之前这条是 `Ran 8 tests … OK`——即「判据在、接线没了」无人可抓，故新增 `test_the_artifacts_path_trips_on_a_stale_episode_pointer` |
| C | 删掉 `validate_review_markdown` 里的 `review_tier_findings` 调用点（schema 的 `allOf` 保留） | 仍判红（schema 层守住） | `Ran 7 tests … OK`；另在副本上伪造 `review_tier: L0` 无 `dispatch_errors` 的记录，`validate.py artifacts` →「$: missing required property 'dispatch_errors'」 | 通过：这一层由 schema 兜住 |
| E | 只删 schema 的 `allOf`（校验器调用保留） | 仍判红（校验器层守住） | 副本上 `validate.py artifacts` 对伪降级记录 →「伪降级：review_tier 声明 L0 却没有 dispatch_errors」 | 通过：两层各自独立成立 |
| F | 同时删掉 `allOf` 与校验器调用 | 接线用例必须转红（证明它不是空测） | `Ran 7 tests … FAILED (failures=1, errors=1)` | 通过 |
| D | 关掉 `repo_policy_findings` 里的 `pending_ledger_findings` 接线 | 自测转红 | `FAIL C18-01 …`、`FAIL C18-08 …`、`130/132 self-test cases pass` | 通过 |

## 反证自身踩到的一次「假反证」

首轮反证 A 得到的是 `PASS decision_gate`，当时结论写成「新断言无效」。复核后确认原因不成立：
被删的是独立声明行，而 `docs/PENDING-DECISIONS.md` 第 25 条的现状核验列里恰好有一句
「已把 `agentflow 决策记录` 标记单独成行」——子串检查仍为真，所以门根本没进入「标记消失」分支。
这条区分很重要：**判据没被削弱，是被测形态选错了**。修复方式不是换反证目标，而是把判据改成
按声明行识别（散文提及不算声明），改后 A 立刻转红。相关口径见
`docs/issues/ISS-2026-10-29-拍板口改写中两处自述超出事实.md`。

## 遗留（未反证项，如实登记）

- 字形映射单源（门④）的反证未做：它的回归信号来自 `validate.py tests` 与 `doc_chain` 判据本身
  （两处消费方读同一份定义，任何一侧改写枚举都会被现有用例抓到），本轮未额外构造削弱实验。
- `carrier-map` 的地板值 `MIN_CARRIER_ROWS = 12` 未做「表被删到只剩一行」的独立反证，
  由 `test_gate_records.py` 之外的逐行存在性断言覆盖；已作为评审提问项交给独立评审。
