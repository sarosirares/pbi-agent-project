import json

from database_query_models import (
    DatabaseQueryColumnReference,
    DatabaseQueryPlan,
)
from database_semantic_context import (
    build_database_semantic_context,
)
from database_query_validator import validate_database_query_plan
from database_question_context import DatabaseQuestionContext
from database_schema_context import DatabaseSchemaContext
from llm_client import VLLMClient


QUERY_PLANNING_PROMPT = """
You create a structured read-only database query plan.

You receive:
- the user's question;
- detailed metadata for a small set of candidate database tables selected
  by trusted Python code.

Rules:
- Treat the supplied tables as candidates. They are not all required.
- Use only tables and columns that exist in the supplied context.
- Never invent schema names, table names, or column names.
- The only allowed operation is "select".
- Prefer a single table whenever it is sufficient for the request.
- Use multiple tables only when the requested result genuinely requires
  information stored across them.
- SEMANTIC CONTEXT may contain approved relationships between tables.
- Multi-table plans may use only those approved relationships.
- Never invent a join condition.
- Every selected table must contribute to the requested result or be
  necessary to connect other selected tables.
- The selected tables and joins must form one connected join tree.
- Only INNER JOIN is currently supported.
- For a single-table plan:
  joins = []
  requires_join = false.
- For a multi-table plan:
  requires_join = true.
- Use columns, aggregations, filters, grouping, sorting, and join columns
  only from selected tables.
- Do not generate SQL.
- Do not claim that row data has been inspected.

Semantic result naming rules:
- Always provide semantic_table_name.
- semantic_table_name names the result dataset when it is represented
  in a Power BI semantic model.
- Choose a concise and meaningful name based on the user's request and
  the meaning of the query result.
- Prefer English PascalCase names such as:
  StudentSummary, StudentsByGender, EnrollmentByYear.
- Do not use generic technical names such as:
  AgentReportData, QueryResult, ResultData, Data.
- Do not simply copy the source database table name unless that name is
  genuinely the best description of the result.
- The name must start with a letter and contain only letters and digits.

Join rules:
- Each join must use exactly this structure:
  {
    "join_type": "inner",
    "left_column": {
      "schema_name": "...",
      "table_name": "...",
      "column_name": "..."
    },
    "right_column": {
      "schema_name": "...",
      "table_name": "...",
      "column_name": "..."
    }
  }
- Both columns must match one approved relationship from SEMANTIC CONTEXT.
- The relationship may be used in either direction.
- Do not create duplicate joins.

Column rules:
- Use "columns" for non-aggregated values that must appear in the result.
- If aggregations are present, every item in "columns" must also appear
  in "group_by".
- Do not include unnecessary columns.

Aggregation rules:
- Supported functions are:
  count, count_distinct, sum, avg, min, max.
- For COUNT(*) use:
  "function": "count",
  "column": null.
- If the user asks how many distinct or unique values exist in a column,
  use "count_distinct" with that column.
- A COUNT DISTINCT request must not be implemented by selecting the
  column and grouping by it.
- For a scalar COUNT DISTINCT result, use:
  columns = [],
  group_by = [],
  and one "count_distinct" aggregation.
- Use GROUP BY only when the user wants a separate aggregated result for
  each category, such as "number of students by gender".
- GROUP BY must always be accompanied by at least one aggregation.
- SUM and AVG may only use numeric columns.
- Give every aggregation a short unique output_name.
- An aggregation may optionally have a condition.
- A conditional aggregation applies its aggregation only to rows that
  satisfy that condition.
- Use conditional aggregations when the requested metric contains a
  subset such as:
  values above a threshold,
  rows with a particular status,
  rows belonging to a particular category,
  or another condition supported by the filter operators.
- The condition uses exactly the same structure and operators as a
  normal filter.
- A condition on an aggregation does not filter the entire query result.
  It only affects that aggregation.

Derived metric rules:
- Use "derived_metrics" when the requested result is calculated from
  aggregation outputs rather than directly from a database column.
- The currently supported derived metric operation is "ratio".
- A ratio references two aggregation output_name values:
  numerator and denominator.
- Use scale = 1 for a plain ratio.
- Use scale = 100 when the user asks for a percentage or percent rate.
- Do not use AVG as a substitute for a ratio unless the user's request
  actually asks for an arithmetic average.
- Do not return only the numerator when the user asks for a rate,
  percentage, proportion, or share.
- Do not invent a business condition for the numerator. The condition
  must be supported by the user's request or supplied context.
- Give every derived metric a short unique output_name.

Filter rules:
- Supported operators are:
  eq, ne, gt, gte, lt, lte, in,
  contains, starts_with, ends_with,
  is_null, is_not_null.
- Every filter must contain a nested "column" object.
- Never place schema_name, table_name, or column_name directly inside
  the filter object.
- Use exactly this structure for each filter:
  {
    "column": {
      "schema_name": "dbo",
      "table_name": "ExampleTable",
      "column_name": "ExampleColumn"
    },
    "operator": "eq",
    "value": "ExampleValue"
  }
- Use null as the filter value only for is_null and is_not_null.
- Use "in" when one column may match any of several explicit values.
- For "in", value must be a non-empty JSON array.
- Do not represent alternatives on the same column as multiple eq
  filters, because multiple filters are combined with AND.
- contains, starts_with and ends_with are only for string columns.
- Multiple filters are combined with AND.

Sort rules:
- Sort only by real database columns supplied in the context.
- Supported directions are "asc" and "desc".

Limit rules:
- limit must be between 1 and 1000.
- Use 100 when the user does not request a specific result limit.
- For aggregate-only queries such as COUNT(*), keep limit at 100.

Return only valid JSON.
Do not add markdown fences or explanations.

Return exactly this structure:

{
  "operation": "select",
  "semantic_table_name": "StudentSummary",
  "tables": [
    {
      "schema_name": "...",
      "table_name": "..."
    }
  ],
  "joins": [],
  "columns": [],
  "aggregations": [
    {
      "function": "count",
      "column": null,
      "output_name": "total_count",
      "condition": null
    },
    {
      "function": "count",
      "column": null,
      "output_name": "matching_count",
      "condition": {
        "column": {
          "schema_name": "...",
          "table_name": "...",
          "column_name": "..."
        },
        "operator": "gte",
        "value": 10
      }
    }
  ],
  "derived_metrics": [
    {
      "operation": "ratio",
      "numerator": "matching_count",
      "denominator": "total_count",
      "scale": 100,
      "output_name": "matching_percentage"
    }
  ],
  "group_by": [],
  "filters": [],
  "sort": [],
  "limit": 100,
  "requires_join": false
}
"""


class DatabaseQueryPlanner:
    def __init__(
        self,
        llm: VLLMClient | None = None,
    ) -> None:
        self.llm = llm or VLLMClient()

    def plan(
        self,
        question: str,
        question_context: DatabaseQuestionContext,
        schema_context: DatabaseSchemaContext,
    ) -> DatabaseQueryPlan:
        clean_question = question.strip()

        if not clean_question:
            raise ValueError("Question must not be empty.")

        if question_context.mode != "tables":
            raise ValueError(
                "Database query planning requires detailed table context."
            )

        if not question_context.tables:
            raise ValueError(
                "Database query planning received no detailed tables."
            )

        context_payload = {
            "database_name": question_context.database_name,
            "tables": [
                table.model_dump()
                for table in question_context.tables
            ],
        }

        context_json = json.dumps(
            context_payload,
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
                    "content": QUERY_PLANNING_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"QUESTION:\n{clean_question}\n\n"
                        f"DATABASE SCHEMA CONTEXT:\n"
                        f"{context_json}\n\n"
                        f"SEMANTIC CONTEXT:\n"
                        f"{semantic_context_json}"
                    ),
                },
            ],
            max_tokens=2048,
            temperature=0.0,
            enable_thinking=False,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned no database query plan."
            )

        parsed_result = _parse_json(content)

        plan = DatabaseQueryPlan.model_validate(
            parsed_result
        )

        validate_database_query_plan(
            plan=plan,
            schema_context=schema_context,
        )

        _validate_plan_against_question_context(
            plan=plan,
            question_context=question_context,
        )

        return plan


def _validate_plan_against_question_context(
    plan: DatabaseQueryPlan,
    question_context: DatabaseQuestionContext,
) -> None:
    allowed_tables = {
        (table.schema_name, table.name)
        for table in question_context.tables
    }

    for table_reference in plan.tables:
        key = (
            table_reference.schema_name,
            table_reference.table_name,
        )

        if key not in allowed_tables:
            raise ValueError(
                "Database query plan used a table outside "
                "the selected question context."
            )

    allowed_columns = {
        (
            table.schema_name,
            table.name,
            column.name,
        )
        for table in question_context.tables
        for column in table.columns
    }

    referenced_columns: list[
        DatabaseQueryColumnReference
    ] = [
        *plan.columns,
        *plan.group_by,
        *[
            aggregation.column
            for aggregation in plan.aggregations
            if aggregation.column is not None
        ],
        *[
            aggregation.condition.column
            for aggregation in plan.aggregations
            if aggregation.condition is not None
        ],
        *[
            query_filter.column
            for query_filter in plan.filters
        ],
        *[
            query_sort.column
            for query_sort in plan.sort
        ],
    ]

    for column_reference in referenced_columns:
        key = (
            column_reference.schema_name,
            column_reference.table_name,
            column_reference.column_name,
        )

        if key not in allowed_columns:
            raise ValueError(
                "Database query plan used a column outside "
                "the selected question context."
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