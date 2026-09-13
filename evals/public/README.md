# Public evaluation cases

These ten cases are the first offline regression slice for Agentflow's role and boundary
contracts. They test workflow decisions and permissions, not model quality. Each case is
paired with a sanitized input under `inputs/` and has `holdout: false`.

The cases deliberately include both small tasks that should not be over-delegated and
material tasks that must pass through architecture or independent review gates.

Run:

```sh
python3 tools/lab/validate.py evals
```
