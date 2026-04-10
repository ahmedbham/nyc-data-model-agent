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
4. A valid Azure AI Foundry project endpoint and model deployment if you want a full end-to-end test.

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

Expected behavior:

- If the local server is up and your Foundry settings are valid, the agent should respond with a structured summary.
- If the server is up but the Foundry project or model settings are placeholders, the endpoint will respond but Azure will return a configuration error such as `ResourceNotFound`.

## Next Steps To Complete The Setup

1. Replace the placeholder `.env` values with a real Foundry project endpoint and model deployment.
2. Add a simple validation step for generated SQL so the demo can show approval and dev-only execution gates.
3. Add a Power BI model or report over the target schema to complete the business-facing end of the demo.
4. Add deployment instructions for publishing the agent as a real hosted agent in Azure AI Foundry.

## Demo Data Loader Assets

- [app/load_demo_source_data.py](app/load_demo_source_data.py)
- [sql/create_demo_source_schema.sql](sql/create_demo_source_schema.sql)
- [data/sample/facilities.csv](data/sample/facilities.csv)
- [data/sample/departments.csv](data/sample/departments.csv)
- [data/sample/patients.csv](data/sample/patients.csv)
- [data/sample/encounters.csv](data/sample/encounters.csv)
- [data/sample/diagnoses.csv](data/sample/diagnoses.csv)

## Key Files

- [app/main.py](app/main.py)
- [app/load_demo_source_data.py](app/load_demo_source_data.py)
- [docs/demo-prd.md](docs/demo-prd.md)
- [docs/source-catalog.md](docs/source-catalog.md)
- [docs/metric-catalog.md](docs/metric-catalog.md)
- [data/profiles/source_profiles.json](data/profiles/source_profiles.json)
- [prompts/eda-output-template.md](prompts/eda-output-template.md)
- [prompts/model-output-template.md](prompts/model-output-template.md)
- [prompts/sql-output-template.md](prompts/sql-output-template.md)
- [sql/create_demo_source_schema.sql](sql/create_demo_source_schema.sql)
- [sql/create_demo_target_model.sql](sql/create_demo_target_model.sql)
- [agent.yaml](agent.yaml)
