import contextlib
import io
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_default_roots_are_the_five_live_roots(self):
        # 2026-10-12 slimming batch phases 3/4: issues/releases/features live under docs/
        # (the top-level plans/ root was dissolved into the feature batches), episodes and
        # reviews stay at the repository root — five live roots.
        self.assertEqual(
            [path.name for path in record_store.DEFAULT_ROOTS],
            ["issues", "releases", "features", "episodes", "reviews"],
        )
        self.assertEqual(
            [path.parent.name for path in record_store.DEFAULT_ROOTS][:3],
            ["docs", "docs", "docs"],
        )

    def test_docstring_and_cli_help_name_the_live_roots_that_are_indexed(self):
        # Item J: the module docstring listed retired roots (plans/, improvements/) and the CLI
        # help claimed six roots. Both must now match DEFAULT_ROOTS.
        doc = record_store.__doc__
        for root in record_store.DEFAULT_ROOTS:
            self.assertIn(root.relative_to(record_store.ROOT).as_posix(), doc)
        self.assertNotIn("improvements", doc)
        self.assertNotIn("plans/", doc)
        out = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["record_store.py", "--help"]),
            contextlib.redirect_stdout(out),
            self.assertRaises(SystemExit),
        ):
            record_store.main()
        self.assertIn("五个现行记录根", out.getvalue())

    def test_reindex_removes_rows_for_deleted_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            records = root / "records"
            records.mkdir()
            source = records / "gone.md"
            source.write_text("# Retired record\nA stale index row must not survive.\n", encoding="utf-8")
            db = root / "records.sqlite3"
            self.assertEqual(record_store.index(records, db), 1)
            self.assertTrue(record_store.query(db, "stale index row"))
            source.unlink()
            self.assertEqual(record_store.index(records, db), 0)
            self.assertEqual(record_store.query(db, "stale index row"), [])
            with sqlite3.connect(db) as connection:
                self.assertEqual(connection.execute("select count(*) from records").fetchone()[0], 0)
                self.assertEqual(connection.execute("select count(*) from records_fts").fetchone()[0], 0)

    def test_query_raises_ordinary_exception_not_system_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            records = root / "records"
            records.mkdir()
            (records / "one.md").write_text("# One\nbody\n", encoding="utf-8")
            db = root / "records.sqlite3"
            record_store.index(records, db)
            with self.assertRaises(record_store.RecordQueryError):
                record_store.query(db, '"unterminated')

    def test_multiple_live_roots_index_into_one_store(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            issues = root / "issues"
            episodes = root / "episodes"
            issues.mkdir()
            episodes.mkdir()
            (issues / "ISS-2026-01-02-alpha.md").write_text(
                "# Alpha issue\nA recall regression signal.\n", encoding="utf-8"
            )
            (episodes / "EP-2026-09-17-901.json").write_text(
                '{"objective":"recall regression episode"}', encoding="utf-8"
            )
            db = root / "records.sqlite3"
            self.assertEqual(record_store.index([issues, episodes], db), 2)
            paths = sorted(path for path, _ in record_store.query(db, "recall regression"))
            self.assertEqual(len(paths), 2)
            self.assertTrue(paths[0].endswith("episodes/EP-2026-09-17-901.json"), paths)
            self.assertTrue(paths[1].endswith("issues/ISS-2026-01-02-alpha.md"), paths)


if __name__ == "__main__":
    unittest.main()
