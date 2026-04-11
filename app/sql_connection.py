import logging
import os
import struct
import time

import pyodbc
from azure.identity import AzureCliCredential, ChainedTokenCredential, InteractiveBrowserCredential, ManagedIdentityCredential
from dotenv import load_dotenv

load_dotenv(override=False)

logger = logging.getLogger("sql_connection")

SQL_COPT_SS_ACCESS_TOKEN = 1256
MODERN_SQL_SERVER_DRIVERS = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]
TRANSIENT_CONNECTION_ERROR_CODES = ["08001", "HYT00", "HYT01"]


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is required.")
    return value


def resolve_sql_driver(configured_driver: str, auth_mode: str) -> str:
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


def is_transient_connection_error(error: pyodbc.Error) -> bool:
    for arg in error.args:
        text = str(arg)
        if any(code in text for code in TRANSIENT_CONNECTION_ERROR_CODES):
            return True
        if "Login timeout expired" in text:
            return True
        if "Unable to complete login process due to delay in login response" in text:
            return True
    return False


def build_connection() -> pyodbc.Connection:
    server = require_env("AZURE_SQL_SERVER")
    database = require_env("AZURE_SQL_DATABASE")
    configured_driver = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    auth_mode = os.getenv("AZURE_SQL_AUTH_MODE", "access-token").strip().lower()
    allow_interactive_browser = os.getenv("AZURE_SQL_ENABLE_INTERACTIVE_AUTH", "false").strip().lower() == "true"
    driver = resolve_sql_driver(configured_driver, auth_mode)
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
        username = require_env("AZURE_SQL_USERNAME")
        password = require_env("AZURE_SQL_PASSWORD")
        logger.info("Connecting to Azure SQL with SQL authentication.")

        for attempt in range(1, max_attempts + 1):
            try:
                return pyodbc.connect(
                    base_connection_string + f"Uid={username};Pwd={password};",
                    autocommit=False,
                )
            except pyodbc.Error as error:
                if attempt == max_attempts or not is_transient_connection_error(error):
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
    if os.getenv("IDENTITY_ENDPOINT") or os.getenv("MSI_ENDPOINT"):
        credential = ManagedIdentityCredential()
    else:
        local_credentials = [AzureCliCredential()]
        if allow_interactive_browser:
            local_credentials.append(InteractiveBrowserCredential())
        credential = ChainedTokenCredential(*local_credentials)

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
            if attempt == max_attempts or not is_transient_connection_error(error):
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