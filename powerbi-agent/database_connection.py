import os

import pyodbc
from dotenv import load_dotenv


load_dotenv()


def connect_to_database() -> pyodbc.Connection:
    """Create a SQL Server connection from environment configuration."""
    server = _required_env("SQLSERVER_SERVER")
    database = _required_env("SQLSERVER_DATABASE")

    driver = os.getenv(
        "SQLSERVER_DRIVER",
        "ODBC Driver 18 for SQL Server",
    )

    trusted_connection = os.getenv(
        "SQLSERVER_TRUSTED_CONNECTION",
        "yes",
    ).strip().lower()

    encrypt = os.getenv(
        "SQLSERVER_ENCRYPT",
        "yes",
    )

    trust_server_certificate = os.getenv(
        "SQLSERVER_TRUST_SERVER_CERTIFICATE",
        "yes",
    )

    if trusted_connection in {
        "yes",
        "true",
        "1",
    }:
        authentication = "Trusted_Connection=yes;"
    else:
        username = _required_env(
            "SQLSERVER_USERNAME"
        )
        password = _required_env(
            "SQLSERVER_PASSWORD"
        )

        authentication = (
            f"UID={_odbc_value(username)};"
            f"PWD={_odbc_value(password)};"
        )

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"{authentication}"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_server_certificate};"
        "APP=PowerBIAgent;"
    )

    return pyodbc.connect(
        connection_string,
        timeout=5,
    )


def _required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' is not configured."
        )

    return value


def _odbc_value(value: str) -> str:
    """Escape an ODBC connection string value."""
    return "{" + value.replace("}", "}}") + "}"