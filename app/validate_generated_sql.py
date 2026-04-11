import argparse
import json
import re
import sys
from pathlib import Path


BLOCKING_PATTERNS = [
    (
        "forbidden_server_scope_statement",
        re.compile(r"\b(drop\s+database|create\s+login|alter\s+login|drop\s+login|sp_configure|xp_)\b", re.IGNORECASE),
        "Server-level or destructive administration statements are not allowed in the demo workflow.",
    ),
    (
        "forbidden_execution_statement",
        re.compile(r"\bexec(?:ute)?\b", re.IGNORECASE),
        "Dynamic or procedural execution statements are not allowed in the demo workflow.",
    ),
    (
        "forbidden_database_switch",
        re.compile(r"\buse\s+\[?(master|msdb|tempdb)\]?\b", re.IGNORECASE),
        "Switching to system databases is not allowed in the demo workflow.",
    ),
]

WARNING_PATTERNS = [
    (
        "destructive_table_reset",
        re.compile(r"\b(drop\s+table|truncate\s+table)\b", re.IGNORECASE),
        "The SQL contains table reset statements. Verify the script is safe for repeated dev-only execution.",
    ),
    (
        "delete_without_where",
        re.compile(r"\bdelete\s+from\b(?![^;]*\bwhere\b)", re.IGNORECASE | re.DOTALL),
        "The SQL contains a DELETE statement without a WHERE clause.",
    ),
]

STATEMENT_PATTERN = re.compile(r"[^;]+;?", re.DOTALL)
SELECT_PATTERN = re.compile(r"\bselect\b", re.IGNORECASE)


def _strip_sql_comments(sql_text: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.DOTALL)
    return re.sub(r"--.*?$", "", without_block_comments, flags=re.MULTILINE)


def _read_sql_text(sql_file: Path | None) -> str:
    if sql_file is None:
        return sys.stdin.read()

    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    return sql_file.read_text(encoding="utf-8")


def _split_statements(sql_text: str) -> list[str]:
    normalized = re.sub(r"(?im)^\s*GO\s*$", ";", sql_text)
    return [statement.strip() for statement in STATEMENT_PATTERN.findall(normalized) if statement.strip()]


def validate_sql(sql_text: str, target_environment: str, approved_by: str | None) -> dict:
    normalized_sql = _strip_sql_comments(sql_text)
    statements = _split_statements(normalized_sql)

    report = {
        "target_environment": target_environment,
        "approved_by": approved_by or "",
        "statement_count": len(statements),
        "blocking_findings": [],
        "warnings": [],
        "execution_allowed": False,
    }

    if target_environment.lower() != "dev":
        report["blocking_findings"].append(
            {
                "rule": "non_dev_environment",
                "message": "Generated SQL can only be approved for execution against a dev environment.",
            }
        )

    if not approved_by:
        report["blocking_findings"].append(
            {
                "rule": "missing_approval",
                "message": "Execution approval is required. Re-run with --approved-by to pass the approval gate.",
            }
        )

    if not statements:
        report["blocking_findings"].append(
            {
                "rule": "empty_sql",
                "message": "No SQL statements were found.",
            }
        )

    for rule_name, pattern, message in BLOCKING_PATTERNS:
        if pattern.search(normalized_sql):
            report["blocking_findings"].append({"rule": rule_name, "message": message})

    for rule_name, pattern, message in WARNING_PATTERNS:
        if pattern.search(normalized_sql):
            report["warnings"].append({"rule": rule_name, "message": message})

    if not SELECT_PATTERN.search(normalized_sql):
        report["warnings"].append(
            {
                "rule": "missing_validation_queries",
                "message": "No obvious validation query was detected. Add a SELECT-based validation query for demo verification.",
            }
        )

    report["execution_allowed"] = len(report["blocking_findings"]) == 0
    return report


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate generated SQL for the demo approval and dev-only execution gate.")
    parser.add_argument("--sql-file", type=Path, help="Path to a .sql file. If omitted, SQL is read from stdin.")
    parser.add_argument(
        "--target-environment",
        default="dev",
        help="Target execution environment. Only 'dev' passes the execution gate.",
    )
    parser.add_argument("--approved-by", help="Approver identity required to pass the execution gate.")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Choose human-readable or JSON output.",
    )
    return parser


def _print_text_report(report: dict) -> None:
    print("SQL Validation Report")
    print(f"Target environment: {report['target_environment']}")
    print(f"Approved by: {report['approved_by'] or 'not provided'}")
    print(f"Statement count: {report['statement_count']}")

    print("Blocking findings:")
    if report["blocking_findings"]:
        for finding in report["blocking_findings"]:
            print(f"- [{finding['rule']}] {finding['message']}")
    else:
        print("- none")

    print("Warnings:")
    if report["warnings"]:
        for warning in report["warnings"]:
            print(f"- [{warning['rule']}] {warning['message']}")
    else:
        print("- none")

    print(f"Execution allowed: {'yes' if report['execution_allowed'] else 'no'}")


def main() -> None:
    parser = _build_argument_parser()
    args = parser.parse_args()
    sql_text = _read_sql_text(args.sql_file)
    report = validate_sql(sql_text, args.target_environment, args.approved_by)

    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        _print_text_report(report)

    raise SystemExit(0 if report["execution_allowed"] else 1)


if __name__ == "__main__":
    main()