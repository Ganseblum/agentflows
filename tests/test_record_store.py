import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "lab"))
import record_store


class RecordStoreTests(unittest.TestCase):
    def test_index_and_query_use_fts5_without_editing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            records = root / "records"
            records.mkdir()
            source = records / "episode.md"
            source.write_text("# Permission regression\nA reviewer found a permission boundary regression.\n", encoding="utf-8")
            db = root / "records.sqlite3"
            original = source.read_bytes()
            self.assertEqual(record_store.index(records, db), 1)
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(record_store.query(db, "permission regression"))
            with sqlite3.connect(db) as connection:
                self.assertEqual(connection.execute("select count(*) from records_fts").fetchone()[0], 1)

    def test_query_is_lexical_and_missing_terms_return_no_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            records = root / "records"
            records.mkdir()
            (records / "one.json").write_text('{"objective":"review evidence"}', encoding="utf-8")
            db = root / "records.sqlite3"
            record_store.index(records, db)
            self.assertEqual(record_store.query(db, "vector_database"), [])

    def test_default_roots_are_the_six_live_roots(self):
        # 2026-10 structural overhaul: the default corpus is the six live roots, not the
        # former single records/ tree.
        self.assertEqual(
            [path.name for path in record_store.DEFAULT_ROOTS],
            ["issues", "episodes", "plans", "improvements", "releases", "reviews"],
        )

    def test_multiple_live_roots_index_into_one_store(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            issues = root / "issues"
            episodes = root / "episodes"
            issues.mkdir()
            episodes.mkdir()
            (issues / "ISS-2026-001-alpha.md").write_text(
                "# Alpha issue\nA recall regression signal.\n", encoding="utf-8"
            )
            (episodes / "EP-20260917-901.json").write_text(
                '{"objective":"recall regression episode"}', encoding="utf-8"
            )
            db = root / "records.sqlite3"
            self.assertEqual(record_store.index([issues, episodes], db), 2)
            paths = sorted(path for path, _ in record_store.query(db, "recall regression"))
            self.assertEqual(len(paths), 2)
            self.assertTrue(paths[0].endswith("episodes/EP-20260917-901.json"), paths)
            self.assertTrue(paths[1].endswith("issues/ISS-2026-001-alpha.md"), paths)


if __name__ == "__main__":
    unittest.main()
