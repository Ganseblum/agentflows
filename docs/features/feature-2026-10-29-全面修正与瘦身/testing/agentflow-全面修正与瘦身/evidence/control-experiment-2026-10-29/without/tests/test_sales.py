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

    def test_top_selects_largest_totals_descending(self):
        result = self.run_cli(
            "region,amount\nnorth,10\nsouth,5\neast,30\nwest,20\n",
            "--top",
            "2",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["east\t30.00", "west\t20.00"])

    def test_top_breaks_ties_by_region_name(self):
        result = self.run_cli(
            "region,amount\nzeta,7\nalpha,3\nbeta,7\n",
            "--top",
            "3",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["beta\t7.00", "zeta\t7.00", "alpha\t3.00"],
        )

    def test_top_larger_than_region_count_prints_all(self):
        result = self.run_cli("region,amount\nnorth,10\nsouth,5\n", "--top", "5")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["north\t10.00", "south\t5.00"])

    def test_top_below_one_exits_two_with_error(self):
        result = self.run_cli("region,amount\nnorth,10\n", "--top", "0")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.strip())

    def test_malformed_amount_exits_two_with_error(self):
        result = self.run_cli("region,amount\nnorth,not-a-number\n")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.strip())
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
