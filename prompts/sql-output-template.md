# SQL Output Template

Use this template when the user asks for DDL, DML, transformation SQL, or executable starter SQL for the demo target model.

Output contract:
- Use the exact markdown H2 section headings below.
- Keep the sections in the exact order shown below.
- Do not rename the headings.
- Always include fenced sql code blocks for DDL, transformation SQL, and validation queries.

## SQL Objective
- One short paragraph on what the SQL will create or populate.

## Approval Gate
- State that the SQL is for a dev-only environment and requires human approval before execution.
- Tell the user to validate the SQL with `python app/validate_generated_sql.py --sql-file <path-to-sql> --target-environment dev --approved-by <name>` before any execution step.

## Target Objects
- List the tables, views, or helper objects being created or populated.

## DDL
```sql
-- Azure SQL compatible DDL goes here
```

## Transformation SQL
```sql
-- Azure SQL compatible DML or transformation SQL goes here
```

## Validation Queries
```sql
-- Basic row-count or metric validation queries go here
```

## Validation Gate
- Summarize the validation expectation: dev-only target, named approver required, and no execution until the validation step passes.

## Execution Notes
- State assumptions, ordering, dependencies, and anything intentionally left for later hardening.

Formatting rules:
- Generate Azure SQL compatible syntax only.
- Use fenced sql code blocks.
- Separate object creation from data population and validation.