# 关闭证据门 — 测试与验证方案（design/qa）

## 1. 前置门禁与环境

- 解释器：仓内 `.venv/bin/python`（无则 `python3`）；依赖见 `requirements-dev.txt`。
- 前置：无外部服务、无数据库、无宿主交互；所有用例在临时目录或仓内只读执行。
- 门变更授权：用户 2026-10-28 选择「允许改受保护门」；独立评审未跑，不得据此宣告批次完成。

## 2. 模块 × 验证类型矩阵

| 模块 | 单元（unittest） | 契约扫描（validate.py） | 文档链（doc_chain） |
| --- | --- | --- | --- |
| M01 文档同步 | — | — | `grep` 旧表述零命中 |
| M02 流转记录 | T03-05 | `validate.py artifacts` | — |
| M03 回归 | T03-01 至 T03-04、T03-06、T03-07 | `validate.py all` | 本批次 `doc_chain.py` |

## 3. 核心流程测试设计

| 用例 | 输入 | 期望 |
| --- | --- | --- |
| T03-01 | verified，缺 `closure_criteria` | 错误命中 `closure_criteria` |
| T03-02 | verified，缺 `reviewer`/`review_decision`/`regression_status` | 三个字段分别被点名 |
| T03-03 | verified，`review_decision=changes_requested` 或 `regression_status=not-run` | 对应字段报错 |
| T03-04 | rejected，缺 `rejection_reason` | 错误命中 `rejection_reason` |
| T03-05 | fixed-pending-review，正文缺 `## 变更记录` | 错误命中 `变更记录` |
| T03-06 | verified 合法正例（四项齐全且 approved/pass） | 无错误 |
| T03-07 | fixed-pending-review，正文含 `## 变更记录` | 无错误 |

## 4. 边界与异常覆盖

| 边界 | 覆盖 |
| --- | --- |
| `fixed-pending-review` 缺审查字段 | 不做必填（允许退回 open），由存量 5 条 PASS 证明 |
| `fix_revision` 缺失 | 不强制；proposal Q-01 |
| `rejected` 放进归档 | 既有布局检查覆盖，本批不加用例 |
| 归档目录内记录 | 同一 `validate_bug_markdown` 编译；当前 0 条 rejected |

## 5. Bug 回归用例设计

本批修的是门自身的缺口，回归即 §3 的 T03-01 至 T03-07；schema 条件的负例在修改前应**已红**（证明条件存在），`## 变更记录` 的负例在修改前应**静默通过**（证明缺口存在），修改后必须报错。

## 6. 测试准备

- 数据：全部为内联 fixture，不读真实记录；`validate.py artifacts` 对仓内 66 条记录做只读扫描。
- Mock：无。

## 7. 验证命令

| 命令 | 覆盖什么 | 命令依据 |
| --- | --- | --- |
| `.venv/bin/python -m unittest tests.test_gate_schema` | 负例与正例 | `tests/test_gate_schema.py` |
| `.venv/bin/python tools/lab/doc_chain.py docs/features/feature-2026-10-28-关闭证据门` | 本批次文档链 C1–C26 | `AGENTS.md` 文档链节 |
| `.venv/bin/python tools/lab/validate.py artifacts` | 存量 66 条记录零误伤 | `tools/lab/validate.py` 子项 |
| `.venv/bin/python tools/lab/validate.py all` | 全量门（含 tests 与 lint） | `AGENTS.md` 接受产物前 |

## 8. 发布判断条件

- 五条负例必红（T03-01 至 T03-05）、两条正例必绿（T03-06、T03-07）、存量零误伤、文档链全绿；原始输出入 `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md`。
- 独立评审通过前不得发布；本批不 bump 版本、不写 CHANGELOG、不推送、不重装宿主。

## 9. 自检清单

- ☑ 每条新门都有负例，负例文案可定位字段。
- ☑ 正例与存量数据证明零误伤。
- ☑ 命令可复制执行，依据指向仓内文件。
- ☑ 未声称未运行的检查为通过。
