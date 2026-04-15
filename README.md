# Hospital Data Model Agent Demo

## What Is Being Developed So Far

This repository contains the initial implementation scaffold for a Microsoft-first demo covering the first three prioritized use cases in [prompts/use-case-1-requirements.md](prompts/use-case-1-requirements.md):

1. Autonomous data exploration.
2. Target data model and supporting data flows.
3. SQL and model generation.

The current implementation is a Foundry-hosted Python agent starter for a hospital analytics demo focused on inpatient readmission and length-of-stay reporting. The repo currently includes:

- A hosted agent entrypoint in [app/main.py](app/main.py).
- A demo PRD in [docs/demo-prd.md](docs/demo-prd.md).
- A source catalog in [docs/source-catalog.md](docs/source-catalog.md).
- A metric catalog in [docs/metric-catalog.md](docs/metric-catalog.md).
- Synthetic sample source data in [data/sample/patients.csv](data/sample/patients.csv), [data/sample/encounters.csv](data/sample/encounters.csv), [data/sample/diagnoses.csv](data/sample/diagnoses.csv), [data/sample/departments.csv](data/sample/departments.csv), and [data/sample/facilities.csv](data/sample/facilities.csv).
- Source profiling metadata in [data/profiles/source_profiles.json](data/profiles/source_profiles.json).
- Demo source and target SQL in [sql/create_demo_source_schema.sql](sql/create_demo_source_schema.sql) and [sql/create_demo_target_model.sql](sql/create_demo_target_model.sql).
- Foundry deployment metadata in [agent.yaml](agent.yaml).
- Local debug and run configuration in [.vscode/launch.json](.vscode/launch.json) and [.vscode/tasks.json](.vscode/tasks.json).

The current agent loads the demo PRD, source catalog, metric catalog, profiling metadata, and structured output templates into its instructions so it can act as a hospital data product copilot for the demo scenario.

Current assumptions:

- Synthetic non-PHI data only.
- Azure SQL-compatible SQL generation.
- Dev-only execution for generated SQL.
- Human approval between model design and SQL execution.
- One focused hospital analytics scenario rather than a multi-domain rollout.

## How To Run A Local Test

### Prerequisites

1. Python virtual environment support.
2. Azure CLI installed if you want to authenticate locally with Azure credentials.
3. ODBC Driver 18 for SQL Server installed if you want to load the synthetic CSVs into Azure SQL Database.
4. A valid Microsoft Foundry project endpoint and model deployment if you want a full end-to-end test.

### Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Copy [.env.template](.env.template) to `.env` and populate the required values:

- `FOUNDRY_PROJECT_ENDPOINT`
- `FOUNDRY_MODEL_DEPLOYMENT_NAME`
- `AGENT_NAME`
- `DEMO_PRD_PATH`
- `DEMO_SOURCE_CATALOG_PATH`
- `DEMO_METRIC_CATALOG_PATH`
- `DEMO_PROFILE_PATH`
- `AZURE_SQL_SERVER`
- `AZURE_SQL_DATABASE`
- `AZURE_SQL_DRIVER`
- `AZURE_SQL_AUTH_MODE`
- `AZURE_SQL_CONNECTION_TIMEOUT`
- `AZURE_SQL_CONNECT_RETRIES`

Optional for SQL authentication mode:

- `AZURE_SQL_USERNAME`
- `AZURE_SQL_PASSWORD`

Optional for Microsoft Entra interactive browser fallback:

- `AZURE_SQL_ENABLE_INTERACTIVE_AUTH=true`

4. If testing against a real Foundry resource, sign in with Azure CLI:

```powershell
az login
```

If you plan to use Microsoft Entra authentication for Azure SQL, make sure the database has an Entra admin configured and that your signed-in principal has access to the target database.

### Load The Demo Source Data Into Azure SQL

The repo now includes a bootstrap loader that creates the demo source tables if they do not already exist, clears any previously loaded demo rows, and reloads the CSV files from [data/sample/patients.csv](data/sample/patients.csv), [data/sample/encounters.csv](data/sample/encounters.csv), [data/sample/diagnoses.csv](data/sample/diagnoses.csv), [data/sample/departments.csv](data/sample/departments.csv), and [data/sample/facilities.csv](data/sample/facilities.csv).

Run it with Microsoft Entra authentication:

```powershell
.\.venv\Scripts\python.exe app/load_demo_source_data.py
```

If your Azure SQL Database uses SQL authentication instead, set `AZURE_SQL_AUTH_MODE=password` and populate `AZURE_SQL_USERNAME` and `AZURE_SQL_PASSWORD` in `.env` before running the same command.

Troubleshooting:

- If the loader fails with `Data source name not found` or reports that no supported SQL Server ODBC driver is installed, install Microsoft ODBC Driver 18 for SQL Server on the machine running the script. The legacy Windows `SQL Server` ODBC driver is usually not sufficient for Azure SQL token authentication.
- If the loader fails with `Login timeout expired` or `Unable to complete login process due to delay in login response`, increase `AZURE_SQL_CONNECTION_TIMEOUT` and rerun. This is common when Azure SQL needs extra time to resume or when server-side login processing is slow.

Expected behavior:

- The script executes [sql/create_demo_source_schema.sql](sql/create_demo_source_schema.sql) if the source tables do not exist yet.
- Existing demo rows are removed in child-to-parent order so the load is rerunnable.
- The script logs row counts for each loaded table and finishes with a success message.

### Start The Agent Locally

Run the hosted agent service:

```powershell
.\.venv\Scripts\python.exe app/main.py
```

This should start a local HTTP service on port `8088` through the Foundry hosting adapter.

### Send A Local Test Request

In a second terminal, send a simple request to the hosted endpoint:

```powershell
$response = Invoke-WebRequest -Uri http://127.0.0.1:8088/responses -Method POST -ContentType 'application/json' -Body '{"input":"Summarize the demo source tables for readmission analytics.","stream":false}' -UseBasicParsing
($response.Content | ConvertFrom-Json).output[0].content[0].text
```

For a reusable end-to-end demo request covering EDA, target modeling, and starter SQL generation, use:

```powershell
$prompt = @'
Using the inpatient readmission analytics demo context, complete this request in three phases: EDA, target modeling, and starter SQL generation.

Phase requirements:
1. First produce the EDA output using the exact section headings and order from the repo's EDA output template.
2. Then produce the target model output using the exact section headings and order from the repo's model output template.
3. Then produce Azure SQL starter SQL using the exact section headings and order from the repo's SQL output template.

Business objective:
Create an analytics-ready dimensional model for 30-day readmission and length-of-stay reporting that supports both dashboarding and self-service analysis.

Source tables:
- patients
- encounters
- diagnoses
- departments
- facilities

Required joins:
- patients.patient_id = encounters.patient_id
- encounters.encounter_id = diagnoses.encounter_id
- departments.department_id = encounters.department_id
- facilities.facility_id = encounters.facility_id

Metrics to support:
- readmission_rate_30d
- average_length_of_stay
- encounter_count
- discharge_count
- readmission_count_30d

Business rules:
- Only inpatient encounters are in scope.
- Readmission matching uses patient identity and a subsequent inpatient admission within 30 days of discharge.
- Primary diagnosis comes from the diagnosis row where is_primary = 1.
- Age group is derived from patient birth date as of admit date.

Modeling expectations:
- Propose a dimensional model with explicit fact grain.
- Keep fact tables and dimensions separate.
- Include metric-to-model mapping.
- Include a source-to-target transformation flow.
- Call out assumptions and tradeoffs, especially around readmission logic, diagnosis handling, and age grouping.
- Keep the design compatible with Azure SQL Database.

SQL expectations:
- Generate Azure SQL compatible DDL, transformation SQL, and validation queries.
- Keep SQL dev-only.
- Do not include server-level administration statements, EXEC or EXECUTE, or system-database switching.
- Include SELECT-based validation queries.
- State clearly that human approval is required before execution.
- Include the validation command the user must run before execution.

Output expectations:
- Keep each phase clearly separated.
- Do not skip open gaps or design decisions.
- Do not execute anything.
'@

$body = @{ input = $prompt; stream = $false } | ConvertTo-Json -Compress
$response = Invoke-WebRequest -Uri http://127.0.0.1:8088/responses -Method POST -ContentType 'application/json' -Body $body -UseBasicParsing
($response.Content | ConvertFrom-Json).output[0].content[0].text
```

Expected behavior:

- If the local server is up and your Foundry settings are valid, the agent should respond with a structured summary.
- If the server is up but the Foundry project or model settings are placeholders, the endpoint will respond but Azure will return a configuration error such as `ResourceNotFound`.

## Next Steps To Complete The Setup

1. Replace the placeholder `.env` values with a real Foundry project endpoint and model deployment.

## Foundry Deployment

Deployment instructions for publishing this repo as a hosted agent in Microsoft Foundry are documented in [docs/foundry-deployment.md](docs/foundry-deployment.md).

The deployment runbook covers:

- local pre-deployment verification
- ACR image build guidance
- hosted agent configuration based on [agent.yaml](agent.yaml)
- container startup and smoke-test validation
- post-deployment demo flow

## Demo Data Loader Assets

- [app/load_demo_source_data.py](app/load_demo_source_data.py)
- [sql/create_demo_source_schema.sql](sql/create_demo_source_schema.sql)
- [data/sample/facilities.csv](data/sample/facilities.csv)
- [data/sample/departments.csv](data/sample/departments.csv)
- [data/sample/patients.csv](data/sample/patients.csv)
- [data/sample/encounters.csv](data/sample/encounters.csv)
- [data/sample/diagnoses.csv](data/sample/diagnoses.csv)

## SQL Validation Gate

The repo now includes a lightweight SQL validator at [app/validate_generated_sql.py](app/validate_generated_sql.py). Use it after the agent produces SQL and before any execution step.

Example without approval, showing the gate is still closed:

```powershell
.\.venv\Scripts\python.exe app/validate_generated_sql.py --sql-file sql/create_demo_target_model.sql --target-environment dev
```

Example with a named approver, allowing dev-only execution:

```powershell
.\.venv\Scripts\python.exe app/validate_generated_sql.py --sql-file sql/create_demo_target_model.sql --target-environment dev --approved-by demo-owner
```

Expected behavior:

- The validator fails if the target environment is not `dev`.
- The validator fails if no approver is supplied.
- The validator blocks clearly unsafe server-level statements and warns on risky table-reset patterns.
- The validator exits successfully only when the dev-only and approval gates are satisfied.

## Target Model Execution

The repo now includes an execution utility at [app/run_target_model_sql.py](app/run_target_model_sql.py). It runs [sql/create_demo_target_model.sql](sql/create_demo_target_model.sql) against Azure SQL Database and prints the validation query result sets at the end of the script.

First validate the SQL and capture approval:

```powershell
.\.venv\Scripts\python.exe app/validate_generated_sql.py --sql-file sql/create_demo_target_model.sql --target-environment dev --approved-by demo-owner
```

Then execute the target model script:

```powershell
.\.venv\Scripts\python.exe app/run_target_model_sql.py
```

For repeat demos where the target tables already exist, use:

```powershell
.\.venv\Scripts\python.exe app/run_target_model_sql.py --reset-target
```

Expected behavior:

- The script connects using the same Azure SQL auth settings as the source-data loader.
- By default the script prefers non-interactive credentials such as Azure CLI. Set `AZURE_SQL_ENABLE_INTERACTIVE_AUTH=true` only if you explicitly want browser-based fallback.
- The script executes the target model DDL, population SQL, and built-in validation queries.
- The script prints each validation result set directly to the terminal for demo-friendly verification.

## Power BI Demo Layer

The repo includes Power BI guidance for the business-facing end of the demo.

Use these artifacts together:

- Report specification: [docs/powerbi-report-spec.md](docs/powerbi-report-spec.md)
- Semantic model mapping: [powerbi/starter-semantic-model.md](powerbi/starter-semantic-model.md)

Recommended setup flow:

1. Run the source-data loader and target-model execution scripts so Azure SQL contains the populated target schema.
2. In Power BI Desktop, connect to the Azure SQL Database in import mode.
3. Import `fact_encounter_outcomes`, `dim_patient`, `dim_facility`, `dim_department`, and `dim_diagnosis`.
4. Apply the relationships and starter DAX measures from [powerbi/starter-semantic-model.md](powerbi/starter-semantic-model.md).
5. Build the report pages and visuals described in [docs/powerbi-report-spec.md](docs/powerbi-report-spec.md).
6. Refresh the report after rerunning the target-model script during the live demo.

Expected outcome:

- KPI cards for readmission rate, average length of stay, and encounter count.
- Drill-down analysis by facility, department, diagnosis, and age group.
- A report layer that matches the validation results printed by [app/run_target_model_sql.py](app/run_target_model_sql.py).

## Key Files

- [app/main.py](app/main.py)
- [app/load_demo_source_data.py](app/load_demo_source_data.py)
- [app/run_target_model_sql.py](app/run_target_model_sql.py)
- [app/sql_connection.py](app/sql_connection.py)
- [app/validate_generated_sql.py](app/validate_generated_sql.py)
- [docs/demo-prd.md](docs/demo-prd.md)
- [docs/foundry-deployment.md](docs/foundry-deployment.md)
- [docs/source-catalog.md](docs/source-catalog.md)
- [docs/metric-catalog.md](docs/metric-catalog.md)
- [docs/powerbi-report-spec.md](docs/powerbi-report-spec.md)
- [data/profiles/source_profiles.json](data/profiles/source_profiles.json)
- [powerbi/starter-semantic-model.md](powerbi/starter-semantic-model.md)
- [prompts/eda-output-template.md](prompts/eda-output-template.md)
- [prompts/model-output-template.md](prompts/model-output-template.md)
- [prompts/sql-output-template.md](prompts/sql-output-template.md)
- [sql/create_demo_source_schema.sql](sql/create_demo_source_schema.sql)
- [sql/create_demo_target_model.sql](sql/create_demo_target_model.sql)
- [agent.yaml](agent.yaml)
