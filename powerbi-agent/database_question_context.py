from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from database_schema_context import (
    DatabaseSchemaContext,
    DatabaseTable,
)
from database_schema_selector import DatabaseSchemaSelection


class DatabaseCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_name: str = Field(min_length=1)
    table_name: str = Field(min_length=1)
    column_count: int = Field(ge=0)


class DatabaseQuestionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database_name: str = Field(min_length=1)
    mode: Literal["catalog", "tables"]
    table_count: int = Field(ge=0)
    catalog: list[DatabaseCatalogEntry]
    tables: list[DatabaseTable]


def build_database_question_context(
    schema_context: DatabaseSchemaContext,
    selection: DatabaseSchemaSelection,
) -> DatabaseQuestionContext:
    available_tables = {
        (table.schema_name, table.name): table
        for table in schema_context.tables
    }

    if selection.mode == "catalog":
        catalog = [
            DatabaseCatalogEntry(
                schema_name=table.schema_name,
                table_name=table.name,
                column_count=len(table.columns),
            )
            for table in schema_context.tables
        ]

        return DatabaseQuestionContext(
            database_name=schema_context.database_name,
            mode="catalog",
            table_count=len(schema_context.tables),
            catalog=catalog,
            tables=[],
        )

    selected_tables: list[DatabaseTable] = []

    for reference in selection.tables:
        key = (
            reference.schema_name,
            reference.table_name,
        )

        table = available_tables.get(key)

        if table is None:
            raise ValueError(
                "Database question context received an unknown table: "
                f"{reference.schema_name}.{reference.table_name}"
            )

        selected_tables.append(table)

    return DatabaseQuestionContext(
        database_name=schema_context.database_name,
        mode="tables",
        table_count=len(schema_context.tables),
        catalog=[],
        tables=selected_tables,
    )