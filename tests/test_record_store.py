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


if __name__ == "__main__":
    unittest.main()
