from pydantic import BaseModel, ConfigDict

from database_query_models import (
    DatabaseQueryAggregation,
    DatabaseQueryColumnReference,
    DatabaseQueryFilter,
    DatabaseQueryPlan,
)
from database_query_validator import validate_database_query_plan
from database_schema_context import DatabaseSchemaContext


QueryParameter = str | int | float | bool


class RenderedDatabaseQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sql: str
    parameters: list[QueryParameter]


def render_database_query(
    plan: DatabaseQueryPlan,
    schema_context: DatabaseSchemaContext,
) -> RenderedDatabaseQuery:
    validate_database_query_plan(
        plan=plan,
        schema_context=schema_context,
    )

    select_expressions: list[str] = []
    parameters: list[QueryParameter] = []

    for column in plan.columns:
        select_expressions.append(
            _render_column(column)
        )

    aggregation_expressions: dict[str, str] = {}
    aggregation_parameters: dict[
        str,
        list[QueryParameter],
    ] = {}

    for aggregation in plan.aggregations:
        expression, expression_parameters = (
            _render_aggregation(
                aggregation
            )
        )

        aggregation_expressions[
            aggregation.output_name
        ] = expression

        aggregation_parameters[
            aggregation.output_name
        ] = expression_parameters

        select_expressions.append(
            f"{expression} AS "
            f"{_quote_identifier(aggregation.output_name)}"
        )

        parameters.extend(
            expression_parameters
        )

    for derived_metric in plan.derived_metrics:
        numerator_expression = (
            aggregation_expressions[
                derived_metric.numerator
            ]
        )

        denominator_expression = (
            aggregation_expressions[
                derived_metric.denominator
            ]
        )

        expression = (
            "("
            f"CAST(({numerator_expression}) AS float) "
            "/ NULLIF("
            f"CAST(({denominator_expression}) AS float), "
            "0.0)"
            ")"
        )

        if derived_metric.scale != 1.0:
            expression = (
                f"({expression} * "
                f"{float(derived_metric.scale)})"
            )

        select_expressions.append(
            f"{expression} AS "
            f"{_quote_identifier(derived_metric.output_name)}"
        )

        parameters.extend(
            aggregation_parameters[
                derived_metric.numerator
            ]
        )

        parameters.extend(
            aggregation_parameters[
                derived_metric.denominator
            ]
        )

    if not select_expressions:
        raise ValueError(
            "Database query renderer received "
            "no select expressions."
        )

    select_line = "SELECT"

    if plan.limit is not None:
        select_line = (
            f"SELECT TOP ({plan.limit})"
        )

    sql_lines = [
        select_line,
        "    " + ",\n    ".join(select_expressions),
        *_render_from_clause(plan),
    ]

    where_expressions: list[str] = []

    for query_filter in plan.filters:
        expression, filter_parameters = (
            _render_filter_condition(
                query_filter
            )
        )

        where_expressions.append(expression)
        parameters.extend(filter_parameters)

    if where_expressions:
        sql_lines.append("WHERE")
        sql_lines.append(
            "    "
            + "\n    AND ".join(where_expressions)
        )

    if plan.group_by:
        group_by_sql = ",\n    ".join(
            _render_column(column)
            for column in plan.group_by
        )

        sql_lines.append("GROUP BY")
        sql_lines.append(
            f"    {group_by_sql}"
        )

    if plan.sort:
        sort_sql = ",\n    ".join(
            (
                f"{_render_column(query_sort.column)} "
                f"{query_sort.direction.upper()}"
            )
            for query_sort in plan.sort
        )

        sql_lines.append("ORDER BY")
        sql_lines.append(
            f"    {sort_sql}"
        )

    sql = "\n".join(sql_lines) + ";"

    return RenderedDatabaseQuery(
        sql=sql,
        parameters=parameters,
    )


def _render_from_clause(
    plan: DatabaseQueryPlan,
) -> list[str]:
    base_table = plan.tables[0]

    lines = [
        (
            "FROM "
            f"{_quote_identifier(base_table.schema_name)}."
            f"{_quote_identifier(base_table.table_name)}"
        )
    ]

    if not plan.joins:
        return lines

    joined_tables = {
        (
            base_table.schema_name,
            base_table.table_name,
        )
    }

    pending_joins = list(plan.joins)

    while pending_joins:
        progress = False

        for join in list(pending_joins):
            left_table = (
                join.left_column.schema_name,
                join.left_column.table_name,
            )

            right_table = (
                join.right_column.schema_name,
                join.right_column.table_name,
            )

            if (
                left_table in joined_tables
                and right_table not in joined_tables
            ):
                new_table = right_table

            elif (
                right_table in joined_tables
                and left_table not in joined_tables
            ):
                new_table = left_table

            else:
                continue

            table_sql = (
                f"{_quote_identifier(new_table[0])}."
                f"{_quote_identifier(new_table[1])}"
            )

            lines.append(
                "INNER JOIN "
                f"{table_sql} "
                "ON "
                f"{_render_column(join.left_column)} "
                "= "
                f"{_render_column(join.right_column)}"
            )

            joined_tables.add(
                new_table
            )

            pending_joins.remove(join)
            progress = True

        if not progress:
            raise ValueError(
                "Unable to render a connected join tree."
            )

    return lines


def _render_aggregation(
    aggregation: DatabaseQueryAggregation,
) -> tuple[str, list[QueryParameter]]:
    condition_sql: str | None = None
    condition_parameters: list[
        QueryParameter
    ] = []

    if aggregation.condition is not None:
        (
            condition_sql,
            condition_parameters,
        ) = _render_filter_condition(
            aggregation.condition
        )

    if aggregation.column is None:
        if condition_sql is None:
            return "COUNT(*)", []

        return (
            "SUM(CASE WHEN "
            f"{condition_sql} "
            "THEN 1 ELSE 0 END)",
            condition_parameters,
        )

    column_sql = _render_column(
        aggregation.column
    )

    if condition_sql is None:
        if aggregation.function == "count":
            expression = f"COUNT({column_sql})"

        elif aggregation.function == "count_distinct":
            expression = (
                f"COUNT(DISTINCT {column_sql})"
            )

        elif aggregation.function == "sum":
            expression = f"SUM({column_sql})"

        elif aggregation.function == "avg":
            expression = (
                f"AVG(CAST({column_sql} AS float))"
            )

        elif aggregation.function == "min":
            expression = f"MIN({column_sql})"

        elif aggregation.function == "max":
            expression = f"MAX({column_sql})"

        else:
            raise ValueError(
                "Unsupported aggregation function."
            )

        return expression, []

    conditional_column = (
        "CASE WHEN "
        f"{condition_sql} "
        f"THEN {column_sql} ELSE NULL END"
    )

    if aggregation.function == "count":
        expression = (
            f"COUNT({conditional_column})"
        )

    elif aggregation.function == "count_distinct":
        expression = (
            "COUNT(DISTINCT "
            f"{conditional_column})"
        )

    elif aggregation.function == "sum":
        expression = (
            f"SUM({conditional_column})"
        )

    elif aggregation.function == "avg":
        expression = (
            "AVG(CAST("
            f"{conditional_column} "
            "AS float))"
        )

    elif aggregation.function == "min":
        expression = (
            f"MIN({conditional_column})"
        )

    elif aggregation.function == "max":
        expression = (
            f"MAX({conditional_column})"
        )

    else:
        raise ValueError(
            "Unsupported aggregation function."
        )

    return expression, condition_parameters


def _render_filter_condition(
    query_filter: DatabaseQueryFilter,
) -> tuple[str, list[QueryParameter]]:
    column_sql = _render_column(
        query_filter.column
    )

    if query_filter.operator == "is_null":
        return f"{column_sql} IS NULL", []

    if query_filter.operator == "is_not_null":
        return f"{column_sql} IS NOT NULL", []

    if query_filter.operator == "in":
        if (
            not isinstance(query_filter.value, list)
            or not query_filter.value
        ):
            raise ValueError(
                "IN filter requires a non-empty list."
            )

        placeholders = ", ".join(
            "?"
            for _ in query_filter.value
        )

        return (
            f"{column_sql} IN ({placeholders})",
            list(query_filter.value),
        )

    if query_filter.value is None:
        raise ValueError(
            "Filter value must not be null."
        )

    if query_filter.operator == "eq":
        expression = f"{column_sql} = ?"
        parameter = query_filter.value

    elif query_filter.operator == "ne":
        expression = f"{column_sql} <> ?"
        parameter = query_filter.value

    elif query_filter.operator == "gt":
        expression = f"{column_sql} > ?"
        parameter = query_filter.value

    elif query_filter.operator == "gte":
        expression = f"{column_sql} >= ?"
        parameter = query_filter.value

    elif query_filter.operator == "lt":
        expression = f"{column_sql} < ?"
        parameter = query_filter.value

    elif query_filter.operator == "lte":
        expression = f"{column_sql} <= ?"
        parameter = query_filter.value

    elif query_filter.operator == "contains":
        expression = (
            f"{column_sql} LIKE ? ESCAPE '\\'"
        )
        parameter = (
            "%"
            + _escape_like_value(
                str(query_filter.value)
            )
            + "%"
        )

    elif query_filter.operator == "starts_with":
        expression = (
            f"{column_sql} LIKE ? ESCAPE '\\'"
        )
        parameter = (
            _escape_like_value(
                str(query_filter.value)
            )
            + "%"
        )

    elif query_filter.operator == "ends_with":
        expression = (
            f"{column_sql} LIKE ? ESCAPE '\\'"
        )
        parameter = (
            "%"
            + _escape_like_value(
                str(query_filter.value)
            )
        )

    else:
        raise ValueError(
            "Unsupported filter operator."
        )

    return expression, [parameter]


def _render_column(
    column: DatabaseQueryColumnReference,
) -> str:
    return (
        f"{_quote_identifier(column.schema_name)}."
        f"{_quote_identifier(column.table_name)}."
        f"{_quote_identifier(column.column_name)}"
    )


def _quote_identifier(
    value: str,
) -> str:
    escaped = value.replace(
        "]",
        "]]",
    )

    return f"[{escaped}]"


def _escape_like_value(
    value: str,
) -> str:
    return (
        value
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("[", "\\[")
    )