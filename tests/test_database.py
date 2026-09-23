import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from database import forecasts_for_date, forecasts_for_region, list_regions, upsert_forecasts


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_upsert_does_not_duplicate_rows(self) -> None:
        upsert_forecasts([("臺北市", "2026-04-14", 20, 30)], self.db_path)
        upsert_forecasts([("臺北市", "2026-04-14", 21, 31)], self.db_path)
        frame = forecasts_for_region("臺北市", self.db_path)
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["mint"], 21)
        self.assertEqual(frame.iloc[0]["maxt"], 31)

    def test_query_is_parameterized(self) -> None:
        upsert_forecasts([("臺北市", "2026-04-14", 20, 30)], self.db_path)
        attack = "臺北市' OR 1=1 --"
        self.assertTrue(forecasts_for_region(attack, self.db_path).empty)
        self.assertEqual(list_regions(self.db_path), ["臺北市"])

    def test_query_for_date(self) -> None:
        upsert_forecasts([
            ("臺北市", "2026-04-14", 20, 30),
            ("高雄市", "2026-04-14", 25, 32),
        ], self.db_path)
        self.assertEqual(len(forecasts_for_date("2026-04-14", self.db_path)), 2)

    def test_database_check_rejects_invalid_range(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with closing(sqlite3.connect(self.db_path)) as connection:
                with connection:
                    from database import SCHEMA
                    connection.execute(SCHEMA)
                    connection.execute(
                        "INSERT INTO TemperatureForecasts "
                        "(regionName, dataDate, mint, maxt) VALUES (?, ?, ?, ?)",
                        ("臺北市", "2026-04-14", 35, 20),
                    )


if __name__ == "__main__":
    unittest.main()
