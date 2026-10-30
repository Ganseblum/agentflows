# 同题对照实验原始件（2026-10-29）

结论与口径见 `docs/evaluations/AGENTFLOW-CONTROL-EXPERIMENT-2026-10-29.md`。本目录是从
`/tmp/agentflow-experiment-2026-10-29` 归档的两组工作副本（`.git` 与评审用的 `review.diff` 未收）：

- `without/` — 普通执行组；`with/` — 按 Agentflow 方法执行组（含 `PLAN.md`、`EVIDENCE.md`、`RESULT.md`、`TIMING.start/end`）。
- `hidden_test.py` — 判定用的隐藏验收测试（4 例），两组完成后各跑一次，均 4/4 通过。

复现：把 `hidden_test.py` 与任一目录放在同一父目录下，执行
`python3 hidden_test.py <该目录路径>`；墙钟与命令次数见各目录的 `TIMING.*` 与 `RESULT.md`。
归档原因：`/tmp` 现场不随提交留存，而报告里的数字必须可复核（C23 证据载体纪律）。
