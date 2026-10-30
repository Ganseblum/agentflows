# Evidence log: `--top N` for sales summary

Baseline (before changes): `python3 -m unittest discover -s tests -v` -> Ran 1 test, OK (0.033s), exit 0.

## Run 1 - focused tests, red (before implementation)

Command:

```sh
python3 -m unittest discover -s tests -p 'test_sales.py' -v
```

Result: `Ran 6 tests ... FAILED (failures=4)`, exit 1. Raw failures:

- `test_malformed_amount_exits_2_with_stderr`: `AssertionError: 1 != 2 : Traceback ... ValueError: could not convert string to float: 'abc'` (uncaught ValueError, exit 1).
- `test_top_breaks_ties_by_region_name`: `AssertionError: 2 != 0 : usage: sales.py [-h] csv_path / sales.py: error: unrecognized arguments: --top 1`.
- `test_top_larger_than_region_count_prints_all_by_total`: same `unrecognized arguments: --top 10`.
- `test_top_orders_by_total_descending_and_truncates`: same `unrecognized arguments: --top 2`.
- `test_top_below_one_exits_2_with_stderr` passed accidentally: argparse already exits 2 for the *unrecognized* `--top`, so this run does not yet prove the option exists; runs 2-3 do.

This is a valid target failure: 4 new tests fail on the missing `--top` option / uncaught `ValueError`, not on fixtures or imports.

## Run 2 - focused tests, green (after implementation)

Command:

```sh
python3 -m unittest discover -s tests -p 'test_sales.py' -v
```

Result: all 6 tests `ok`, `Ran 6 tests in 0.243s`, `OK`, exit 0.

Implementation (minimal, `sales.py` only): `--top N` int option; `summarize` converts each `amount` inside `try/except (TypeError, ValueError)` and raises a readable `ValueError`; `main` rejects `N < 1` and a bad amount through `parser.error(...)` (exit 2, message on stderr), and selects `sorted(..., key=(-total, region))[:N]` only when `--top` is given; the no-flag branch keeps the old `sorted(totals.items())` region-name order and the same `<region>\t<total:.2f>` formatting.

## Run 3 - full regression

Command:

```sh
python3 -m unittest discover -s tests -v
```

Result: all 6 tests `ok`, `Ran 6 tests in 0.294s`, `OK`, exit 0 (baseline before the change was 1 test, OK).

## Run 4 - manual CLI end-to-end (the real user path)

Commands (CSV supplied via process substitution; no fixture files left behind):

```sh
python3 sales.py <(printf 'region,amount\nnorth,10\nsouth,5\nnorth,2.5\neast,30\nwest,1\n')
python3 sales.py <(printf 'region,amount\nnorth,10\nsouth,5\nnorth,2.5\neast,30\nwest,1\n') --top 2
err=$(python3 sales.py <(printf 'region,amount\nnorth,1\n') --top 0 2>&1 >/dev/null); echo "exit=$?"; echo "stderr=$err"
err=$(python3 sales.py .tmp-sales-bad.csv 2>&1 >/dev/null); echo "exit=$?"; echo "stderr=$err"   # bad fixture: "region,amount\nnorth,10\nsouth,abc\n", removed afterwards
```

Raw result:

```text
--- no flag ---
east	30.00
north	12.50
south	5.00
west	1.00
exit=0
--- --top 2 ---
east	30.00
north	12.50
exit=0
--- --top 0 (stderr captured) ---
exit=2
stderr=usage: sales.py [-h] [--top N] csv_path
sales.py: error: --top must be at least 1
--- bad amount (stderr captured) ---
exit=2
stderr=usage: sales.py [-h] [--top N] csv_path
sales.py: error: invalid amount for region 'south': 'abc'
```

## Final change scope

`git status --short`: `M sales.py`, `M tests/test_sales.py`, untracked artifacts `EVIDENCE.md`, `PLAN.md`, `RESULT.md`, `TIMING.start`, `TIMING.end`, `review.diff`. No other source or test file touched; no git commit made.

## Review-fix round (2026-10-29): discriminating fixtures and raw evidence

Both P1 findings from the independent review are addressed here. Runs 1-4 above used the old
`east/north/south/west` fixture, whose name order (east < north < south < west) happened to match
its total order (30 > 12.5 > 5 > 1), so its no-flag assertion could not tell region-name sorting
from total-descending sorting. The fixtures and runs below replace that evidence.

### Fixture now used

`sales.csv` (in a scratch directory outside the repo):

```text
region,amount
zeta,60
alpha,1
mid,10
zeta,40
```

Totals: `zeta` 100 (60 + 40), `mid` 10, `alpha` 1. Region-name ascending is `alpha < mid < zeta`,
the exact reverse of total descending (`zeta > mid > alpha`). `sales-bad.csv` is the same file
with `alpha,1` replaced by `alpha,abc`.

The tie case uses `zeta,10 / alpha,10 / mid,3`: total descending with ties broken by name is
`alpha, zeta, mid`, which matches neither plain name order (`alpha, mid, zeta`) nor CSV order
(`zeta, alpha, mid`).

### Raw test run (working tree)

Command:

```sh
python3 -m unittest discover -s tests -v
```

Raw output:

```text
test_groups_sorted_by_region (test_sales.SalesCliTests) ... ok
test_malformed_amount_exits_2_with_stderr (test_sales.SalesCliTests) ... ok
test_top_below_one_exits_2_with_stderr (test_sales.SalesCliTests) ... ok
test_top_breaks_ties_by_region_name (test_sales.SalesCliTests) ... ok
test_top_larger_than_region_count_prints_all_by_total (test_sales.SalesCliTests) ... ok
test_top_orders_by_total_descending_and_truncates (test_sales.SalesCliTests) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.238s

OK
```

Exit code: 0.

### Raw CLI runs on the discriminating fixture

Run from the repo root; fixture paths point at a scratch directory outside the repo (removed
after the runs). stdout and stderr were captured separately; empty sections are shown empty.

```text
=== no --top ===
$ python3 sales.py ../manual-evidence/sales.csv
--- stdout ---
alpha	1.00
mid	10.00
zeta	100.00
--- stderr ---
--- exit ---
0
=== --top 1 ===
$ python3 sales.py ../manual-evidence/sales.csv --top 1
--- stdout ---
zeta	100.00
--- stderr ---
--- exit ---
0
=== --top 0 ===
$ python3 sales.py ../manual-evidence/sales.csv --top 0
--- stdout ---
--- stderr ---
usage: sales.py [-h] [--top N] csv_path
sales.py: error: --top must be at least 1
--- exit ---
2
=== malformed amount ===
$ python3 sales.py ../manual-evidence/sales-bad.csv
--- stdout ---
--- stderr ---
usage: sales.py [-h] [--top N] csv_path
sales.py: error: invalid amount for region 'alpha': 'abc'
--- exit ---
2
```

The no-flag output is name-ascending (`alpha` before `zeta`), while `--top 1` prints only `zeta`.
`--top 0` prints nothing on stdout and exits 2 with a non-empty stderr message; the malformed
amount behaves the same, with no traceback.

### Discrimination check on disposable copies

To show the new fixtures fail under a wrong implementation, two mutations were applied to
throwaway copies under `/tmp/agentflow-experiment-2026-10-29/` (the working tree was not
modified):

- Mutation A - the no-flag branch sorts by total descending instead of by region name:
  `test_top_orders_by_total_descending_and_truncates` failed with
  `['zeta\t100.00', 'mid\t10.00', 'alpha\t1.00'] != ['alpha\t1.00', 'mid\t10.00', 'zeta\t100.00']`;
  the other 5 tests stayed `ok` (`Ran 6 tests`, `FAILED (failures=1)`, exit 1).
- Mutation B - `--top` breaks ties by region name descending instead of ascending:
  `test_top_breaks_ties_by_region_name` failed with `['zeta\t10.00'] != ['alpha\t10.00']`;
  the other 5 tests stayed `ok` (`Ran 6 tests`, `FAILED (failures=1)`, exit 1).

Each mutation is caught by the test that targets it, so the fixtures distinguish name-ascending
from total-descending ordering and ascending from descending tie-breaks. Mutation copies were
removed after the check.

