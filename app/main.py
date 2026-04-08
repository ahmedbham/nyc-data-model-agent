import asyncio
import logging
import os
from pathlib import Path

from agent_framework import Agent
from agent_framework.azure import AzureAIClient
from azure.ai.agentserver.agentframework import from_agent_framework
from azure.identity.aio import DefaultAzureCredential, ManagedIdentityCredential
from dotenv import load_dotenv

load_dotenv(override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hospital_data_model_agent")

ROOT_DIR = Path(__file__).resolve().parent.parent
_client: AzureAIClient | None = None


def _read_text_from_env_path(env_name: str) -> str:
    raw_path = os.getenv(env_name)
    if not raw_path:
        raise ValueError(f"{env_name} environment variable is required.")

    file_path = ROOT_DIR / raw_path
    if not file_path.exists():
        raise FileNotFoundError(f"Referenced demo asset was not found: {file_path}")

    return file_path.read_text(encoding="utf-8")


def _build_credential():
    if os.getenv("IDENTITY_ENDPOINT") or os.getenv("MSI_ENDPOINT"):
        logger.info("Using ManagedIdentityCredential for hosted execution.")
        return ManagedIdentityCredential()

    logger.info("Using DefaultAzureCredential for local execution.")
    return DefaultAzureCredential()


def _build_instructions() -> str:
    prd = _read_text_from_env_path("DEMO_PRD_PATH")
    source_catalog = _read_text_from_env_path("DEMO_SOURCE_CATALOG_PATH")
    metric_catalog = _read_text_from_env_path("DEMO_METRIC_CATALOG_PATH")
    source_profiles = _read_text_from_env_path("DEMO_PROFILE_PATH")

    return f"""
You are a hospital data product copilot for a Microsoft product demo.

Your scope is limited to the first three use cases:
1. Autonomous data exploration.
2. Target data model and supporting data flows.
3. SQL and model generation.

Follow these rules:
- Treat all data as synthetic demo data.
- Stay within the PRD, source catalog, metric catalog, and profiling context provided below.
- When asked for exploration, summarize relevant tables, keys, candidate joins, and data quality findings.
- When asked for modeling, propose a dimensional model with explicit grain, facts, dimensions, and transformation flow.
- When asked for SQL, generate Azure SQL compatible DDL and DML for a dev-only environment.
- Before suggesting execution of generated SQL, remind the user that model approval is required.
- Keep responses concise, structured, and implementation-oriented.

## Demo PRD
{prd}

## Source Catalog
{source_catalog}

## Metric Catalog
{metric_catalog}

## Source Profiles
{source_profiles}
""".strip()


def create_agent() -> Agent:
    project_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    model_deployment_name = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME")
    agent_name = os.getenv("AGENT_NAME", "hospital-data-model-agent")

    if not project_endpoint:
        raise ValueError("FOUNDRY_PROJECT_ENDPOINT environment variable is required.")
    if not model_deployment_name:
        raise ValueError("FOUNDRY_MODEL_DEPLOYMENT_NAME environment variable is required.")

    global _client
    _client = AzureAIClient(
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment_name,
        credential=_build_credential(),
    )

    return _client.as_agent(
        name=agent_name,
        description="Hospital data product copilot for exploration, modeling, and SQL generation demos.",
        instructions=_build_instructions(),
    )


async def main() -> None:
    agent = create_agent()
    logger.info("Starting agent server for %s", agent.name)
    await from_agent_framework(agent).run_async()


if __name__ == "__main__":
    asyncio.run(main())
