# Runtime packaging

`marketplace.json` points ZCode at `packaging/runtime`, not the repository root. That
directory is generated. It is not the source of truth.

```sh
python3 packaging/build_runtime.py
```

The copy includes `agents/`, `skills/`, `schemas/`, the five manifests, host plugin
wrappers, and `protected-paths.txt`. It excludes `records/`, `tests/`, `tools/`, `docs/`,
`evals/`, `mock/`, and `examples/`.

Refresh the local marketplace and reinstall after generating. `python3 tools/lab/validate.py
installed` still compares those runtime files against the repository root, not against this
directory. Claude `--plugin-dir .` and Codex continue to use the source tree.

Relative links from skills into `records/` only resolve in a source checkout.
