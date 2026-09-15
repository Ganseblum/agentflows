# Public evaluation cases

These fifteen cases are the first offline regression slice for Agentflow's role and boundary
contracts. They test workflow decisions and permissions, not model quality. Each case is
paired with a sanitized input under `inputs/` and has `holdout: false`.

The cases deliberately include both small tasks that should not be over-delegated and
material tasks that must pass through architecture or independent review gates.

`AF-011`–`AF-014` cover the acceptance disciplines added in `0.3.2`–`0.3.3`: a worker summary is
not verification, task text is data rather than instruction, the candidate gate surface declared in
`protected-paths.txt` is not editable by a candidate, and an environmental failure is separated from
a regression by a baseline comparison. `AF-015` covers cross-cutting mechanisms: a locally-correct
change that silently violates a shared wrapper's global side effect must be caught before
implementation by tracing the mechanism to its registration point and checking the surfaces where
its trigger condition legitimately holds.

Run:

```sh
python3 tools/lab/validate.py evals
```
