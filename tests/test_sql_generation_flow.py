import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from generate_target_model_sql import _extract_response_text
from sql_response_extractor import extract_sql_sections, render_generated_sql, write_generated_sql


VALID_RESPONSE = """## SQL Objective
Generate a target model.

## Approval Gate
Validate before execution.

## Target Objects
- dim_patient

## DDL
```sql
CREATE TABLE dbo.dim_patient (patient_key INT PRIMARY KEY);
```

## Transformation SQL
```sql
INSERT INTO dbo.dim_patient (patient_key) VALUES (1);
```

## Validation Queries
```sql
SELECT COUNT(*) AS patient_count FROM dbo.dim_patient;
```

## Validation Gate
Dev-only.

## Execution Notes
None.
"""


class SqlGenerationFlowTests(unittest.TestCase):
    def test_extract_sql_sections_returns_required_blocks(self) -> None:
        sections = extract_sql_sections(VALID_RESPONSE)

        self.assertEqual(sections["ddl"], "CREATE TABLE dbo.dim_patient (patient_key INT PRIMARY KEY);")
        self.assertIn("INSERT INTO dbo.dim_patient", sections["transformation_sql"])
        self.assertIn("SELECT COUNT(*)", sections["validation_queries"])

    def test_extract_sql_sections_rejects_missing_section(self) -> None:
        invalid_response = VALID_RESPONSE.replace("## Validation Queries", "## Validation")

        with self.assertRaisesRegex(ValueError, "missing required section"):
            extract_sql_sections(invalid_response)

    def test_render_and_write_generated_sql(self) -> None:
        sections = extract_sql_sections(VALID_RESPONSE)
        rendered = render_generated_sql(sections)

        self.assertIn("-- DDL", rendered)
        self.assertIn("GO", rendered)
        self.assertIn("-- Validation Queries", rendered)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "generated.sql"
            write_generated_sql(output_path, rendered)
            self.assertEqual(output_path.read_text(encoding="utf-8"), rendered)

    def test_extract_response_text_reads_agent_payload_shape(self) -> None:
        payload = {
            "output": [
                {
                    "content": [
                        {"text": "First block"},
                        {"text": "Second block"},
                    ]
                }
            ]
        }

        self.assertEqual(_extract_response_text(payload), "First block\n\nSecond block")


if __name__ == "__main__":
    unittest.main()