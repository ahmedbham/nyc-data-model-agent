# Azure AI Foundry Deployment Runbook

## Purpose

This runbook describes how to publish the hospital data model agent as a real hosted agent in Azure AI Foundry using the existing [agent.yaml](agent.yaml), Python app entrypoint, and container image workflow.

## Deployment Shape

- Agent type: hosted
- Protocol: `responses` `v1`
- Runtime port: `8088`
- Agent definition source: [agent.yaml](agent.yaml)
- Application entrypoint: [app/main.py](app/main.py)

## Prerequisites

1. An Azure AI Foundry project endpoint.
2. A model deployment in that Foundry project for `FOUNDRY_MODEL_DEPLOYMENT_NAME`.
3. An Azure Container Registry available for the hosted image.
4. Azure CLI authenticated to the target tenant and subscription.
5. Ongoing access to the environment variables required by [agent.yaml](agent.yaml).

Recommended references:

- https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents?view=foundry
- https://learn.microsoft.com/azure/ai-foundry/agents/concepts/runtime-components?view=foundry
- https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents

## Required Runtime Configuration

The hosted agent expects these environment variables at deployment time:

- `FOUNDRY_PROJECT_ENDPOINT`
- `FOUNDRY_MODEL_DEPLOYMENT_NAME`
- `AGENT_NAME`
- `DEMO_PRD_PATH`
- `DEMO_SOURCE_CATALOG_PATH`
- `DEMO_METRIC_CATALOG_PATH`
- `DEMO_PROFILE_PATH`

Recommended values for this repo:

- `AGENT_NAME=hospital-data-model-agent`
- `DEMO_PRD_PATH=docs/demo-prd.md`
- `DEMO_SOURCE_CATALOG_PATH=docs/source-catalog.md`
- `DEMO_METRIC_CATALOG_PATH=docs/metric-catalog.md`
- `DEMO_PROFILE_PATH=data/profiles/source_profiles.json`

The repo now includes a Foundry workspace scaffold at [.foundry/agent-metadata.yaml](.foundry/agent-metadata.yaml). It captures the current project endpoint, agent name, ACR login server, and a starter smoke-test case for the `dev` environment.

## Pre-Deployment Verification

Before publishing, verify locally:

1. Install dependencies.
2. Confirm `.env` contains working Foundry values.
3. Start the app locally:

```powershell
.\.venv\Scripts\python.exe app/main.py
```

4. Send a smoke test to the local endpoint:

```powershell
$response = Invoke-WebRequest -Uri http://127.0.0.1:8088/responses -Method POST -ContentType 'application/json' -Body '{"input":"Summarize the demo source tables for readmission analytics.","stream":false}' -UseBasicParsing
($response.Content | ConvertFrom-Json).output[0].content[0].text
```

Do not deploy until the local smoke test succeeds.

## Build Container Image

Cloud build through ACR Tasks is the safest default for this repo because it avoids local Docker variability.

Choose an image tag using a timestamp, for example `20260410-1830`.

Example ACR cloud build:

```powershell
az acr build --registry <acr-name> --image hospital-data-model-agent:20260410-1830 --platform linux/amd64 --file Dockerfile .
```

Expected output:

- A Linux container image published to `<acr-name>.azurecr.io/hospital-data-model-agent:<timestamp>`

## Create Or Update The Hosted Agent

Use Azure AI Foundry with the hosted-agent definition in [agent.yaml](agent.yaml). The deployment payload should match this repo’s runtime shape:

- `kind=hosted`
- `image=<acr-name>.azurecr.io/hospital-data-model-agent:<timestamp>`
- `container_protocol_versions=[{"protocol":"responses","version":"v1"}]`
- environment variables populated with the values listed above

Recommended resource sizing for the demo:

- CPU: `1`
- Memory: `2Gi`

When creating or updating the hosted agent in Foundry, make sure the agent name matches `AGENT_NAME` unless you intentionally want a different deployed name.

## Start And Verify The Container

After the hosted agent definition is saved:

1. Start the container in Foundry.
2. Wait until the container status is `Running`.
3. Run a smoke test in the Foundry playground or through the deployed endpoint.

Suggested smoke test prompt:

```text
Provide an exploratory analysis of the source data for readmission analytics using the EDA template.
```

Expected result:

- The hosted agent responds with the structured EDA headings from the repo prompt templates.

## Deployment Checklist

- The image was built for `linux/amd64`.
- The deployed image tag is timestamped rather than `latest`.
- All environment variables from [agent.yaml](agent.yaml) are populated.
- The Foundry project contains the specified model deployment.
- The container reaches `Running` state.
- A smoke test succeeds in the hosted environment.

## Post-Deployment Demo Flow

Once deployed, the live demo sequence should be:

1. Ask the hosted agent for EDA or modeling output.
2. Validate and approve generated SQL.
3. Run the Azure SQL source and target model scripts.
4. Refresh the Power BI report.
5. Return to the hosted agent for follow-up analysis.

## Troubleshooting Notes

- If the hosted agent starts but does not respond correctly, verify every required environment variable from [agent.yaml](agent.yaml).
- If the container fails on startup, first confirm the image contains the repo files referenced by the prompt asset paths.
- If deployment succeeds but responses fail at runtime, verify the Foundry project endpoint and model deployment name.
- If the agent works locally but not when deployed, compare local `.env` values to the Foundry hosted environment variable configuration.