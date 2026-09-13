# Policy example

`candidate-record.json` and the two evaluation-result fixtures demonstrate the deterministic
policy boundary. They are deliberately not a release approval: the policy output still
requires human approval before any installation pointer changes.

```sh
python3 tools/lab/eval_runner.py compare \
  --baseline examples/evaluation-results/baseline.json \
  --candidate examples/evaluation-results/candidate.json

python3 tools/lab/policy.py \
  --candidate-record examples/policy/candidate-record.json \
  --baseline-result examples/evaluation-results/baseline.json \
  --candidate-result examples/evaluation-results/candidate.json
```
