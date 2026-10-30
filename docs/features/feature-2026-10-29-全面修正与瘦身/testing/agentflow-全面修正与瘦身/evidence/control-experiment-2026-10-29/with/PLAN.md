# Plan: add `--top N` to the sales summary CLI

- Goal: add optional `--top N` printing the N regions with the largest total (total desc, ties region name asc); without the flag output stays region-name-ascending; `N < 1` and malformed `amount` each exit 2 with a non-empty stderr message.
- Acceptance: new tests in `tests/test_sales.py` cover top ordering + tie-break, no-flag unchanged, `--top` larger than region count, `N < 1` (0 and -1), malformed amount; the existing test stays green.
- Change surface: `sales.py` (argument parsing, amount parsing error path, output ordering) and `tests/test_sales.py` only; no refactoring of unrelated code.
- Commands: `python3 -m unittest tests.test_sales -v` (focused, red first then green) and `python3 -m unittest discover -s tests` (full regression).
