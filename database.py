"""SQLite 氣溫預報資料存取層。"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path

import pandas as pd


DEFAULT_DB_PATH = Path(__file__).with_name("data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    mint REAL NOT NULL,
    maxt REAL NOT NULL,
    updatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (mint <= maxt),
    UNIQUE (regionName, dataDate)
);
"""

UPSERT = """
INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
VALUES (?, ?, ?, ?)
ON CONFLICT(regionName, dataDate) DO UPDATE SET
    mint = excluded.mint,
    maxt = excluded.maxt,
    updatedAt = CURRENT_TIMESTAMP;
"""


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """建立啟用欄位名稱存取的 SQLite 連線。"""
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with closing(connect(db_path)) as connection:
        with connection:
            connection.execute(SCHEMA)


def upsert_forecasts(
    rows: Iterable[tuple[str, str, float, float]],
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """新增或更新預報，回傳本次送入的有效紀錄數。"""
    clean_rows = [
        (str(region), str(date), float(mint), float(maxt))
        for region, date, mint, maxt in rows
        if region and date and float(mint) <= float(maxt)
    ]
    if not clean_rows:
        return 0
    initialize_database(db_path)
    with closing(connect(db_path)) as connection:
        with connection:
            connection.executemany(UPSERT, clean_rows)
    return len(clean_rows)


def list_regions(db_path: str | Path = DEFAULT_DB_PATH) -> list[str]:
    initialize_database(db_path)
    with closing(connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName"
        ).fetchall()
    return [str(row["regionName"]) for row in rows]


def list_dates(db_path: str | Path = DEFAULT_DB_PATH) -> list[str]:
    initialize_database(db_path)
    with closing(connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate"
        ).fetchall()
    return [str(row["dataDate"]) for row in rows]


def forecasts_for_region(
    region: str, db_path: str | Path = DEFAULT_DB_PATH
) -> pd.DataFrame:
    initialize_database(db_path)
    with closing(connect(db_path)) as connection:
        return pd.read_sql_query(
            """
            SELECT dataDate, mint, maxt
            FROM TemperatureForecasts
            WHERE regionName = ?
            ORDER BY dataDate
            """,
            connection,
            params=(region,),
        )


def forecasts_for_date(
    data_date: str, db_path: str | Path = DEFAULT_DB_PATH
) -> pd.DataFrame:
    initialize_database(db_path)
    with closing(connect(db_path)) as connection:
        return pd.read_sql_query(
            """
            SELECT regionName, dataDate, mint, maxt
            FROM TemperatureForecasts
            WHERE dataDate = ?
            ORDER BY regionName
            """,
            connection,
            params=(data_date,),
        )


def last_updated(db_path: str | Path = DEFAULT_DB_PATH) -> str | None:
    initialize_database(db_path)
    with closing(connect(db_path)) as connection:
        row = connection.execute(
            "SELECT MAX(updatedAt) AS updatedAt FROM TemperatureForecasts"
        ).fetchone()
    return str(row["updatedAt"]) if row and row["updatedAt"] else None
