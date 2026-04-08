# Hospital Data Model Agent Demo

This repository contains an initial Microsoft-first demo scaffold for the first three business use cases in [prompts/use-case-1-requirements.md](prompts/use-case-1-requirements.md):

1. Autonomous data exploration.
2. Target data model and supporting data flows.
3. SQL and model generation.

The implementation is designed as a Foundry-hosted Python agent service with local demo assets that provide:

- A sample product requirements document.
- A sample source schema and metric catalog.
- Synthetic hospital source data.
- SQL to create the demo source schema.

## Demo Story

The demo focuses on inpatient readmission and length-of-stay analytics for a synthetic three-facility hospital system. The agent is intended to accept a PRD plus source context, reason over the first three use cases, and produce:

- Exploratory data analysis guidance.
- A proposed target dimensional model and data flow.
- Initial DDL and transformation SQL for a dev environment.

## Project Layout

- `app/` - Foundry-hosted agent service code.
- `docs/` - Demo PRD, source catalog, and metric catalog.
- `data/` - Synthetic source data and profiling metadata.
- `sql/` - Source schema setup SQL and starter target model SQL.
- `.vscode/` - Local run and debug configuration.

## Local Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.template` to `.env` and fill in your Foundry settings.
4. Authenticate with Azure CLI if using `DefaultAzureCredential` locally.
5. Run `python app/main.py`.

## Pinned Packages

This scaffold pins preview packages to reduce SDK drift:

- `agent-framework-core==1.0.0rc3`
- `agent-framework-azure-ai==1.0.0rc3`
- `azure-ai-agentserver-agentframework==1.0.0b16`
- `azure-ai-agentserver-core==1.0.0b16`

## Current Scope

This is an implementation starter for a demo, not a production-ready hospital platform. The current scaffold intentionally assumes:

- Synthetic non-PHI data.
- Dev-only SQL execution.
- Human approval before any generated write operation is promoted.
- One analytics scenario rather than a multi-domain rollout.
