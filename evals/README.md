# Evaluation workspace

`public/` contains fourteen offline regression cases (`AF-001`–`AF-014`) with sanitized inputs
under `public/inputs/`. They test workflow decisions and permission boundaries, not model
quality. Private holdout cases must live outside this project and outside candidate
worktrees.

The whole suite is part of the release gate declared in
[`protected-paths.txt`](../protected-paths.txt): a candidate may not edit a case, its input, or the
acceptance criteria it is measured against.

Validate the suite with the deterministic checker, then use the baseline/candidate runner:

```sh
python3 tools/lab/validate.py evals
python3 tools/lab/eval_runner.py run --help
python3 tools/lab/eval_runner.py compare --help
```

See [public/README.md](public/README.md) and [../tools/lab/README.md](../tools/lab/README.md)
for the case contract and the host adapter protocol.
