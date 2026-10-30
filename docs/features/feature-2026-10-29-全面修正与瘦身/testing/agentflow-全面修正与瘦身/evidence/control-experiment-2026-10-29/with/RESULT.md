# Result: `--top N` for the sales summary CLI

## Changed files

- `sales.py` — added the `--top N` option (`type=int`, metavar `N`); rejects `N < 1` via `parser.error` (exit 2, stderr message); parses each `amount` inside `try/except (TypeError, ValueError)` and turns a malformed value into a readable `ValueError` that `main` reports through `parser.error` (exit 2, stderr message, no traceback); with `--top` the rows are `sorted(..., key=(-total, region))[:N]`, without it the old region-name ordering is untouched; output still `<region>\t<total with 2 decimals>`.
- `tests/test_sales.py` — 5 new regression tests: top ordering + truncation (and no-flag order assertion), tie-break by region name, `--top` larger than region count, `N < 1` (0 and -1), malformed amount. The existing test is unchanged.
- Process artifacts only: `PLAN.md`, `EVIDENCE.md`, `RESULT.md`, `TIMING.start`, `TIMING.end`. No other file touched; no git commit made.

## Test runs

Unit-test runs (4):

1. Baseline, `python3 -m unittest discover -s tests -v` — 1 test, OK, exit 0.
2. Red, `python3 -m unittest discover -s tests -p 'test_sales.py' -v` — 6 tests, 4 failures, exit 1 (missing `--top`; malformed amount gave exit 1 with a `ValueError` traceback). Raw output in `EVIDENCE.md` run 1.
3. Focused green, same command — 6 tests, OK, exit 0.
4. Full regression, `python3 -m unittest discover -s tests -v` — 6 tests, OK, exit 0.

Plus manual CLI end-to-end invocations (no flag, `--top 2`, `--top 0`, bad amount) whose exact stdout/stderr/exit codes are in `EVIDENCE.md` run 4.

## Failure / rework rounds

One round: the intended test-first red (4 failures) → minimal implementation → focused green. No implementation-caused regression and no second fix round. Caveat recorded honestly: `test_top_below_one_exits_2_with_stderr` passed even in the red run because argparse already exits 2 for an *unrecognized* argument; it was re-verified green after implementation, when the option is actually parsed.

## Acceptance check

- `--top N` prints the N largest-total regions, total descending, ties region ascending — covered by tests and the manual `--top 2` run.
- Without `--top` output is unchanged — existing test plus an explicit no-flag assertion in the new ordering test plus the manual run.
- `N < 1` exits 2 with a non-empty stderr message — tests with 0 and -1, manual `--top 0`.
- Malformed `amount` exits 2 with a non-empty stderr message and no traceback — test and manual run.
- Output format preserved as `<region>\t<total with 2 decimals>` — every successful-path assertion compares exact lines.
- Regression tests added for the new behavior and both error paths — yes, 5 tests.

## Remaining risks

- Ties are decided by exact float equality of the totals; two totals that differ only by float rounding but format to the same 2-decimal value are still ordered by their actual totals. The task does not define this case, so it is not special-cased.
- Bad data aborts before any row is printed (the totals are built first), so no partial table is emitted; this is asserted by the tests but not a stated task requirement.
- In-process callers of `main()` get `SystemExit(2)` for `N < 1` and a bad amount instead of a returned `2`; the accepted behavior is the CLI exit code, which is verified by subprocess tests and manual runs.
- A CSV missing the `region`/`amount` columns still raises an uncaught `KeyError`; not part of the stated scope.
- Pre-existing float accumulation precision is unchanged.
- `--help` text was not otherwise documented; the option appears there automatically.

## Why I judge this complete

All 6 tests pass in both the focused and full runs, including the untouched baseline test; the manual CLI reproduces the required output formats, the descending/tie ordering and both exit-2 error paths; and the diff is limited to `sales.py` and `tests/test_sales.py` with no unrelated refactor.

## 评审修复轮

针对独立评审的两条 P1，本轮只改测试夹具与证据，`sales.py` 实现未动。

- **P1 #1 夹具判别力**：`tests/test_sales.py` 的 `--top` 用例改用 `zeta,60 / alpha,1 / mid,10 / zeta,40`（总额 zeta 100 > mid 10 > alpha 1，与区域名升序 alpha < mid < zeta 恰好相反）。断言：无 `--top` 时输出 `alpha, mid, zeta`（名序，alpha 在 zeta 前）；`--top 1` 只输出 `zeta`；`--top 2` 输出 `zeta, mid`。并列用例改用 `zeta,10 / alpha,10 / mid,3`，期望 `alpha, zeta, mid`，既不等于纯名序（alpha, mid, zeta），也不等于 CSV 顺序（zeta, alpha, mid）。用例总数仍为 6。
- **P1 #2 证据**：重跑 `python3 -m unittest discover -s tests -v`，把逐条 `... ok` 行与 `Ran 6 tests` / `OK` 的原始输出贴进 `EVIDENCE.md`；并用上述判别性 fixture 贴出无 `--top`、`--top 1`、`--top 0`、非法金额四组的原始 stdout/stderr/exit。另在仓库外的一次性副本上做了两次变异检查（无 `--top` 改为按总额降序、并列改为按名降序），两次都被对应用例判红，工作树未做变异。

测试运行次数：工作树完整套件 3 次——改夹具前基线（6/6 通过）、改夹具后（6/6 通过）、最终确认（6/6 通过，原文见 `EVIDENCE.md` 评审修复轮一节）；另加一次性副本变异运行 2 次（各 6 条用例、各 1 条预期失败）。

修复轮次：1 轮。夹具与证据一次改到位，无需二次返工；未提交 git。
