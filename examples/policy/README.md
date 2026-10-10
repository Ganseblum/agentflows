# 策略示例

`candidate-record.json` 与两个评测结果 fixture 演示了确定性策略边界。
它们刻意不构成发布批准：在任何安装指针变更之前，策略输出仍需要人工批准。

```sh
python3 tools/lab/eval_runner.py compare \
  --baseline examples/evaluation-results/baseline.json \
  --candidate examples/evaluation-results/candidate.json

python3 tools/lab/policy.py \
  --candidate-record examples/policy/candidate-record.json \
  --baseline-result examples/evaluation-results/baseline.json \
  --candidate-result examples/evaluation-results/candidate.json
```
