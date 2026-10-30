import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(sys.argv[1])

class HiddenTests(unittest.TestCase):
    def run_cli(self, csv_text, *args):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sales.csv"
            path.write_text(csv_text, encoding="utf-8")
            return subprocess.run([sys.executable, str(ROOT / "sales.py"), str(path), *args], capture_output=True, text=True, check=False)

    def test_no_top_unchanged(self):
        r = self.run_cli("region,amount\nnorth,10\nsouth,5\nnorth,2.5\n")
        self.assertEqual((r.returncode, r.stdout.splitlines()), (0, ["north\t12.50", "south\t5.00"]))

    def test_top_desc_with_name_tiebreak(self):
        r = self.run_cli("region,amount\nb,10\na,10\nc,1\n", "--top", "2")
        self.assertEqual((r.returncode, r.stdout.splitlines()), (0, ["a\t10.00", "b\t10.00"]))

    def test_top_rejects_zero(self):
        r = self.run_cli("region,amount\na,1\n", "--top", "0")
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.strip())

    def test_malformed_amount_is_clean_error(self):
        r = self.run_cli("region,amount\na,oops\n")
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.strip())
        self.assertNotIn("Traceback", r.stderr)

if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
