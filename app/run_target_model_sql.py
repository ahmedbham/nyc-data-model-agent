import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from sql_connection import build_connection

load_dotenv(override=False)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("target_model_runner")

ROOT_DIR = Path(__file__).resolve().parent.parent
TARGET_MODEL_FILE = ROOT_DIR / "sql" / "create_demo_target_model.sql"
RESET_ORDER = [
    "fact_encounter_outcomes",
    "dim_diagnosis",
    "dim_department",
    "dim_facility",
    "dim_patient",
    "dim_age_group",
    "dim_date"
]


def _split_batches(sql_text: str) -> list[str]:
    batches: list[str] = []
    buffer: list[str] = []
    for line in sql_text.splitlines():
        if line.strip().upper() == "GO":
            batch = "\n".join(buffer).strip()
            if batch:
                batches.append(batch)
            buffer = []
            continue
        buffer.append(line)

    batch = "\n".join(buffer).strip()
    if batch:
        batches.append(batch)
    return batches


def _format_cell(value) -> str:
    return "NULL" if value is None else str(value)


def _print_result_set(cursor, result_set_index: int) -> None:
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    logger.info("Validation result set %s", result_set_index)
    print(" | ".join(columns))
    print("-+-".join("-" * len(column) for column in columns))
    for row in rows:
        print(" | ".join(_format_cell(value) for value in row))
    if not rows:
        print("<no rows>")


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SELECT 1 FROM sys.tables WHERE name = ? AND schema_id = SCHEMA_ID('dbo')", table_name)
    return cursor.fetchone() is not None


def _existing_target_tables(cursor) -> list[str]:
    return [table_name for table_name in RESET_ORDER if _table_exists(cursor, table_name)]


def _reset_target_tables(cursor) -> None:
    for table_name in RESET_ORDER:
        if _table_exists(cursor, table_name):
            cursor.execute(f"DROP TABLE dbo.{table_name}")
            logger.info("Dropped existing target table %s.", table_name)


def _summarize_batch(batch: str) -> str:
    lines = [line.strip() for line in batch.splitlines() if line.strip()]
    return " ".join(lines[:3])[:240]


def _run_batches(cursor, sql_text: str) -> int:
    result_set_count = 0
    for batch_number, batch in enumerate(_split_batches(sql_text), start=1):
        try:
            cursor.execute(batch)
        except Exception as error:
            logger.error("Execution failed in batch %s: %s", batch_number, _summarize_batch(batch))
            raise RuntimeError(f"Target-model SQL failed in batch {batch_number}.") from error
        while True:
            if cursor.description:
                result_set_count += 1
                _print_result_set(cursor, result_set_count)
            if not cursor.nextset():
                break
    return result_set_count


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute the demo target-model SQL and print validation query results.")
    parser.add_argument(
        "--sql-file",
        type=Path,
        default=TARGET_MODEL_FILE,
        help="Path to the target model SQL file.",
    )
    parser.add_argument(
        "--reset-target",
        action="store_true",
        help="Drop existing demo target tables before execution. Useful for repeatable live demos.",
    )
    return parser


def main() -> None:
    args = _build_argument_parser().parse_args()
    if not args.sql_file.exists():
        raise FileNotFoundError(f"Target model SQL file not found: {args.sql_file}")

    sql_text = args.sql_file.read_text(encoding="utf-8")
    connection = build_connection()
    try:
        cursor = connection.cursor()
        logger.info("Executing target model SQL from %s", args.sql_file)
        if args.reset_target:
            _reset_target_tables(cursor)
        else:
            existing_tables = _existing_target_tables(cursor)
            if existing_tables:
                existing_table_list = ", ".join(existing_tables)
                raise RuntimeError(
                    "Target tables already exist and this SQL file is not idempotent. "
                    f"Existing tables: {existing_table_list}. Re-run with --reset-target or make the SQL idempotent."
                )

        result_set_count = _run_batches(cursor, sql_text)
        connection.commit()
        logger.info("Target model SQL execution completed successfully.")
        logger.info("Printed %s validation result set(s).", result_set_count)
    except Exception:
        connection.rollback()
        logger.exception("Target model SQL execution failed.")
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()