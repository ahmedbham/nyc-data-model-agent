import csv
import logging
import os
from datetime import date
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

from sql_connection import build_connection

load_dotenv(override=False)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo_data_loader")

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT_DIR / "sql" / "create_demo_source_schema.sql"
SAMPLE_DIR = ROOT_DIR / "data" / "sample"

TABLE_CONFIG = [
    {
        "name": "facilities",
        "file": SAMPLE_DIR / "facilities.csv",
        "columns": ["facility_id", "facility_name", "region"],
        "converters": [int, str, str],
    },
    {
        "name": "departments",
        "file": SAMPLE_DIR / "departments.csv",
        "columns": ["department_id", "facility_id", "department_name", "department_type", "bed_count"],
        "converters": [int, int, str, str, int],
    },
    {
        "name": "patients",
        "file": SAMPLE_DIR / "patients.csv",
        "columns": ["patient_id", "mrn", "birth_date", "gender", "insurance_type", "zip_code"],
        "converters": [str, str, lambda value: date.fromisoformat(value), str, str, str],
    },
    {
        "name": "encounters",
        "file": SAMPLE_DIR / "encounters.csv",
        "columns": [
            "encounter_id",
            "patient_id",
            "facility_id",
            "department_id",
            "admit_date",
            "discharge_date",
            "admission_type",
            "discharge_disposition",
        ],
        "converters": [str, str, int, int, lambda value: date.fromisoformat(value), lambda value: date.fromisoformat(value), str, str],
    },
    {
        "name": "diagnoses",
        "file": SAMPLE_DIR / "diagnoses.csv",
        "columns": ["encounter_id", "diagnosis_sequence", "icd10_code", "diagnosis_description", "is_primary"],
        "converters": [str, int, str, str, lambda value: bool(int(value))],
    },
]

PURGE_ORDER = ["diagnoses", "encounters", "patients", "departments", "facilities"]


def _read_sql_statements(file_path: Path) -> list[str]:
    if not file_path.exists():
        raise FileNotFoundError(f"Schema file not found: {file_path}")

    statements: list[str] = []
    buffer: list[str] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if line.strip().upper() == "GO":
            statement = "\n".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            continue
        buffer.append(line)

    statement = "\n".join(buffer).strip()
    if statement:
        statements.append(statement)

    return statements


def _table_exists(cursor: pyodbc.Cursor, table_name: str) -> bool:
    cursor.execute("SELECT 1 FROM sys.tables WHERE name = ? AND schema_id = SCHEMA_ID('dbo')", table_name)
    return cursor.fetchone() is not None


def _ensure_schema(cursor: pyodbc.Cursor) -> None:
    for statement in _read_sql_statements(SCHEMA_FILE):
        cursor.execute(statement)


def _purge_existing_rows(cursor: pyodbc.Cursor) -> None:
    for table_name in PURGE_ORDER:
        if _table_exists(cursor, table_name):
            cursor.execute(f"DELETE FROM dbo.{table_name}")


def _read_csv_rows(file_path: Path, columns: list[str], converters: list) -> list[tuple]:
    if not file_path.exists():
        raise FileNotFoundError(f"Sample file not found: {file_path}")

    rows: list[tuple] = []
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [column for column in columns if column not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"CSV file {file_path} is missing columns: {', '.join(missing_columns)}")

        for record in reader:
            rows.append(tuple(converter(record[column]) for column, converter in zip(columns, converters, strict=True)))

    return rows


def _load_table(cursor: pyodbc.Cursor, table_name: str, columns: list[str], rows: list[tuple]) -> None:
    if not rows:
        logger.warning("Skipping %s because no rows were found.", table_name)
        return

    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(columns)
    insert_sql = f"INSERT INTO dbo.{table_name} ({column_list}) VALUES ({placeholders})"
    cursor.fast_executemany = True
    cursor.executemany(insert_sql, rows)
    logger.info("Loaded %s rows into %s.", len(rows), table_name)


def main() -> None:
    connection = build_connection()
    try:
        cursor = connection.cursor()
        _ensure_schema(cursor)
        _purge_existing_rows(cursor)

        for table in TABLE_CONFIG:
            rows = _read_csv_rows(table["file"], table["columns"], table["converters"])
            _load_table(cursor, table["name"], table["columns"], rows)

        connection.commit()
        logger.info("Demo source data load completed successfully.")
    except Exception:
        connection.rollback()
        logger.exception("Demo source data load failed.")
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()