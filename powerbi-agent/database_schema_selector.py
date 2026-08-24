import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from database_schema_context import DatabaseSchemaContext
from llm_client import VLLMClient

from database_semantic_context import (
    build_database_semantic_context,
)


SELECTION_PROMPT = """
You select relevant SQL Server tables for the user's current task.

The task may be:
- inspecting database structure or metadata;
- answering a question that requires database data;
- identifying data needed for a Power BI report.

You receive:
- the user's request;
- a compact catalog of the available database tables.

Rules:
- Use only tables that exist in the supplied catalog.
- Never invent schema names or table names.
- Use mode "catalog" only when the user is asking for a general database
  overview, table count, or list of tables.
- Use mode "tables" when the task requires selecting specific database
  tables, including data questions and Power BI report requests.
- In mode "tables", select at most 8 relevant tables.
- Prefer the smallest set of tables that is sufficient for the task.
- If one table is sufficient, select only that table.
- Select multiple tables when the requested result genuinely requires
  information stored across related tables.
- SEMANTIC CONTEXT may contain approved relationships between tables.
- When multiple tables are required, select only the minimum connected
  set of tables needed for the task using those approved relationships.
- Do not assume or invent relationships that are not present in
  SEMANTIC CONTEXT.
- Do not select additional tables only because their names contain words
  related to the user's request.
- Return only valid JSON.
- Do not add markdown fences or explanations outside the JSON.
- Use exactly one of these structures:

{
  "mode": "catalog",
  "tables": []
}

or:

{
  "mode": "tables",
  "tables": [
    {
      "schema_name": "...",
      "table_name": "..."
    }
  ]
}
"""


class DatabaseTableReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_name: str = Field(min_length=1)
    table_name: str = Field(min_length=1)


class DatabaseSchemaSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["catalog", "tables"]
    tables: list[DatabaseTableReference]


class DatabaseSchemaSelector:
    def __init__(
        self,
        llm: VLLMClient | None = None,
    ) -> None:
        self.llm = llm or VLLMClient()

    def select(
        self,
        question: str,
        schema_context: DatabaseSchemaContext,
    ) -> DatabaseSchemaSelection:
        clean_question = question.strip()

        if not clean_question:
            raise ValueError("Question must not be empty.")

        catalog = [
            {
                "schema_name": table.schema_name,
                "table_name": table.name,
                "column_count": len(table.columns),
            }
            for table in schema_context.tables
        ]

        catalog_json = json.dumps(
            catalog,
            ensure_ascii=False,
        )

        semantic_context = (
            build_database_semantic_context(
                schema_context
            )
        )

        semantic_context_json = json.dumps(
            semantic_context,
            ensure_ascii=False,
        )

        response = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": SELECTION_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"QUESTION:\n{clean_question}\n\n"
                        f"DATABASE: "
                        f"{schema_context.database_name}\n\n"
                        f"TABLE CATALOG:\n{catalog_json}\n\n"
                        f"SEMANTIC CONTEXT:\n"
                        f"{semantic_context_json}"
                    ),
                },
            ],
            max_tokens=512,
            temperature=0.0,
            enable_thinking=False,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned no database schema selection."
            )

        parsed_result = _parse_json(content)

        selection = DatabaseSchemaSelection.model_validate(
            parsed_result
        )

        _validate_selection(
            selection=selection,
            schema_context=schema_context,
        )

        return selection


def _validate_selection(
    selection: DatabaseSchemaSelection,
    schema_context: DatabaseSchemaContext,
) -> None:
    available_tables = {
        (table.schema_name, table.name)
        for table in schema_context.tables
    }

    if selection.mode == "catalog":
        if selection.tables:
            raise ValueError(
                "Catalog mode must not select individual tables."
            )

        return

    if not selection.tables:
        raise ValueError(
            "Tables mode requires at least one selected table."
        )

    if len(selection.tables) > 8:
        raise ValueError(
            "The schema selector returned more than 8 tables."
        )

    for table in selection.tables:
        key = (
            table.schema_name,
            table.table_name,
        )

        if key not in available_tables:
            raise ValueError(
                "The schema selector returned an unknown table: "
                f"{table.schema_name}.{table.table_name}"
            )


def _parse_json(
    content: str,
) -> dict[str, object]:
    clean_content = content.strip()

    if clean_content.startswith("```"):
        lines = clean_content.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        clean_content = "\n".join(lines).strip()

    parsed = json.loads(clean_content)

    if not isinstance(parsed, dict):
        raise ValueError(
            "The model response must be a JSON object."
        )

    return parsed