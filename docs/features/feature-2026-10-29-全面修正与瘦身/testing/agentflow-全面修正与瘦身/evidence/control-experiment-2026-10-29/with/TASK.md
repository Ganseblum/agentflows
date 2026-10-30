# Task: add `--top N` to the sales summary CLI

The CLI currently groups sales by region and prints every region, sorted by region name.

Add an optional `--top N` option:
- With `--top N`, print only the N regions with the largest total amount, ordered by total descending; ties are broken by region name ascending.
- Without `--top`, behavior must not change.
- `N < 1` must exit with code 2 and a non-empty error message on stderr.
- A malformed `amount` value must exit with code 2 and a non-empty error message on stderr (it currently raises an uncaught ValueError).
- Keep the existing output format exactly (`<region>\t<total with 2 decimals>`).
- Add regression tests for the new behavior and the two error paths.
