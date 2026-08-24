from typing import Any

from pydantic import BaseModel, ConfigDict

from database_connection import connect_to_database
from database_query_models import DatabaseQueryPlan
from database_query_renderer import render_database_query
from database_schema_context import DatabaseSchemaContext


class DatabaseQueryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[str]
    rows: list[list[Any]]
    row_count: int


def execute_database_query(
    plan: DatabaseQueryPlan,
    schema_context: DatabaseSchemaContext,
) -> DatabaseQueryResult:
    if plan.limit is None:
        raise ValueError(
            "Direct database query execution "
            "requires a result limit."
        )
    
    rendered_query = render_database_query(
        plan=plan,
        schema_context=schema_context,
    )

    _validate_executable_sql(
        rendered_query.sql
    )

    connection = connect_to_database()

    try:
        cursor = connection.cursor()

        try:
            cursor.execute(
                rendered_query.sql,
                *rendered_query.parameters,
            )

            if cursor.description is None:
                raise RuntimeError(
                    "Database query returned no result set."
                )

            columns = [
                column[0]
                for column in cursor.description
            ]

            fetched_rows = cursor.fetchall()

            rows = [
                list(row)
                for row in fetched_rows
            ]

            if (
                not plan.aggregations
                and len(rows) > plan.limit
            ):
                raise RuntimeError(
                    "Database query returned more rows "
                    "than the validated plan limit."
                )

            return DatabaseQueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
            )

        finally:
            cursor.close()

    finally:
        connection.close()


def _validate_executable_sql(
    sql: str,
) -> None:
    normalized_sql = sql.lstrip().upper()

    if not normalized_sql.startswith("SELECT "):
        raise ValueError(
            "Database query executor accepts SELECT only."
        )