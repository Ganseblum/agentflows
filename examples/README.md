# Contract examples

`bug-records/`, `plans/`, and `test-records/` contain structurally valid, sanitized examples.
Files under `invalid/` are intentionally rejected: the validator checks both their JSON Schema
and the cross-document invariants that the schemas cannot express alone.

Run:

```sh
python3 tools/lab/validate.py examples
```
