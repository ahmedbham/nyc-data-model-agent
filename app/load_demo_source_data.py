import csv
import logging
import os
import struct
import time
from datetime import date
from pathlib import Path

import pyodbc
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(override=False)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo_data_loader")

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT_DIR / "sql" / "create_demo_source_schema.sql"
SAMPLE_DIR = ROOT_DIR / "data" / "sample"
SQL_COPT_SS_ACCESS_TOKEN = 1256

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
MODERN_SQL_SERVER_DRIVERS = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]
TRANSIENT_CONNECTION_ERROR_CODES = ["08001", "HYT00", "HYT01"]


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is required.")
    return value


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


def _resolve_sql_driver(configured_driver: str, auth_mode: str) -> str:
    installed_drivers = list(pyodbc.drivers())
    if configured_driver in installed_drivers:
        return configured_driver

    for candidate in MODERN_SQL_SERVER_DRIVERS:
        if candidate in installed_drivers:
            logger.warning(
                "Configured Azure SQL driver '%s' was not found. Using installed driver '%s' instead.",
                configured_driver,
                candidate,
            )
            return candidate

    installed_driver_list = ", ".join(installed_drivers) if installed_drivers else "none"
    if auth_mode == "access-token":
        raise RuntimeError(
            "No supported SQL Server ODBC driver was found for Azure SQL token authentication. "
            f"Configured driver: '{configured_driver}'. Installed drivers: {installed_driver_list}. "
            "Install Microsoft ODBC Driver 18 for SQL Server, or switch to password auth with a compatible driver."
        )

    raise RuntimeError(
        "No supported SQL Server ODBC driver was found. "
        f"Configured driver: '{configured_driver}'. Installed drivers: {installed_driver_list}. "
        "Install Microsoft ODBC Driver 18 for SQL Server or set AZURE_SQL_DRIVER to a compatible installed driver."
    )


def _is_transient_connection_error(error: pyodbc.Error) -> bool:
    for arg in error.args:
        text = str(arg)
        if any(code in text for code in TRANSIENT_CONNECTION_ERROR_CODES):
            return True
        if "Login timeout expired" in text:
            return True
        if "Unable to complete login process due to delay in login response" in text:
            return True
    return False


def _build_connection() -> pyodbc.Connection:
    server = _require_env("AZURE_SQL_SERVER")
    database = _require_env("AZURE_SQL_DATABASE")
    configured_driver = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    auth_mode = os.getenv("AZURE_SQL_AUTH_MODE", "access-token").strip().lower()
    driver = _resolve_sql_driver(configured_driver, auth_mode)
    connection_timeout = int(os.getenv("AZURE_SQL_CONNECTION_TIMEOUT", "60"))
    max_attempts = int(os.getenv("AZURE_SQL_CONNECT_RETRIES", "3"))

    base_connection_string = (
        f"Driver={{{driver}}};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        f"Connection Timeout={connection_timeout};"
    )

    if auth_mode == "password":
        username = _require_env("AZURE_SQL_USERNAME")
        password = _require_env("AZURE_SQL_PASSWORD")
        logger.info("Connecting to Azure SQL with SQL authentication.")

        for attempt in range(1, max_attempts + 1):
            try:
                return pyodbc.connect(
                    base_connection_string + f"Uid={username};Pwd={password};",
                    autocommit=False,
                )
            except pyodbc.Error as error:
                if attempt == max_attempts or not _is_transient_connection_error(error):
                    raise
                wait_seconds = min(5 * attempt, 15)
                logger.warning(
                    "Azure SQL connection attempt %s of %s failed with a transient error. Retrying in %s seconds.",
                    attempt,
                    max_attempts,
                    wait_seconds,
                )
                time.sleep(wait_seconds)

    if auth_mode != "access-token":
        raise ValueError("AZURE_SQL_AUTH_MODE must be either 'access-token' or 'password'.")

    logger.info("Connecting to Azure SQL with Microsoft Entra token authentication.")
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)

    for attempt in range(1, max_attempts + 1):
        token = credential.get_token("https://database.windows.net/.default").token
        token_bytes = token.encode("utf-16-le")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        try:
            return pyodbc.connect(
                base_connection_string,
                attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct},
                autocommit=False,
            )
        except pyodbc.Error as error:
            if attempt == max_attempts or not _is_transient_connection_error(error):
                raise
            wait_seconds = min(5 * attempt, 15)
            logger.warning(
                "Azure SQL connection attempt %s of %s failed with a transient error. Retrying in %s seconds.",
                attempt,
                max_attempts,
                wait_seconds,
            )
            time.sleep(wait_seconds)

    raise RuntimeError("Azure SQL connection retries were exhausted before a connection could be established.")


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
    connection = _build_connection()
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