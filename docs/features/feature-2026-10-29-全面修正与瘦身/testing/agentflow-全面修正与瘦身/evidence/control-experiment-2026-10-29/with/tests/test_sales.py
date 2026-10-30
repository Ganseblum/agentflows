import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SalesCliTests(unittest.TestCase):
    def run_cli(self, csv_text, *args):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sales.csv"
            path.write_text(csv_text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(ROOT / "sales.py"), str(path), *args],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_groups_sorted_by_region(self):
        result = self.run_cli("region,amount\nnorth,10\nsouth,5\nnorth,2.5\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["north\t12.50", "south\t5.00"])

    def test_top_orders_by_total_descending_and_truncates(self):
        # Region-name order (alpha < mid < zeta) is the reverse of total order
        # (zeta 100 > mid 10 > alpha 1), so a name-sorted fallback cannot pass.
        csv_text = "region,amount\nzeta,60\nalpha,1\nmid,10\nzeta,40\n"
        top_one = self.run_cli(csv_text, "--top", "1")
        self.assertEqual(top_one.returncode, 0, top_one.stderr)
        self.assertEqual(top_one.stdout.splitlines(), ["zeta\t100.00"])
        top_two = self.run_cli(csv_text, "--top", "2")
        self.assertEqual(top_two.returncode, 0, top_two.stderr)
        self.assertEqual(top_two.stdout.splitlines(), ["zeta\t100.00", "mid\t10.00"])
        # Without --top the pre-existing region-name order is unchanged.
        plain = self.run_cli(csv_text)
        self.assertEqual(plain.returncode, 0, plain.stderr)
        self.assertEqual(
            plain.stdout.splitlines(),
            ["alpha\t1.00", "mid\t10.00", "zeta\t100.00"],
        )

    def test_top_breaks_ties_by_region_name(self):
        # zeta ties alpha at 10 but is listed first; a name-descending tie-break
        # or a plain name sort would order these rows differently.
        csv_text = "region,amount\nzeta,10\nalpha,10\nmid,3\n"
        first = self.run_cli(csv_text, "--top", "1")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout.splitlines(), ["alpha\t10.00"])
        all_rows = self.run_cli(csv_text, "--top", "3")
        self.assertEqual(all_rows.returncode, 0, all_rows.stderr)
        self.assertEqual(
            all_rows.stdout.splitlines(),
            ["alpha\t10.00", "zeta\t10.00", "mid\t3.00"],
        )

    def test_top_larger_than_region_count_prints_all_by_total(self):
        result = self.run_cli("region,amount\nnorth,1\nsouth,9\n", "--top", "10")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["south\t9.00", "north\t1.00"])

    def test_top_below_one_exits_2_with_stderr(self):
        for value in ("0", "-1"):
            with self.subTest(top=value):
                result = self.run_cli("region,amount\nnorth,1\n", "--top", value)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotEqual(result.stderr.strip(), "")
                self.assertEqual(result.stdout, "")

    def test_malformed_amount_exits_2_with_stderr(self):
        result = self.run_cli("region,amount\nnorth,10\nsouth,abc\n")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotEqual(result.stderr.strip(), "")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
