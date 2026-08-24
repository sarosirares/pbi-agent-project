from database_query_models import (
    DatabaseQueryColumnReference,
    DatabaseQueryPlan,
)
from database_semantic_context import (
    get_allowed_database_relationships,
)
from database_schema_context import (
    DatabaseSchemaContext,
    DatabaseTable,
)


def validate_database_query_plan(
    plan: DatabaseQueryPlan,
    schema_context: DatabaseSchemaContext,
) -> None:
    available_tables = {
        (table.schema_name, table.name): table
        for table in schema_context.tables
    }

    selected_table_keys = {
        (
            table.schema_name,
            table.table_name,
        )
        for table in plan.tables
    }

    if len(selected_table_keys) != len(plan.tables):
        raise ValueError(
            "Database query plan contains duplicate tables."
        )

    for table_reference in plan.tables:
        key = (
            table_reference.schema_name,
            table_reference.table_name,
        )

        if key not in available_tables:
            raise ValueError(
                "Database query plan contains an unknown table: "
                f"{table_reference.schema_name}."
                f"{table_reference.table_name}"
            )

    referenced_columns = [
        *plan.columns,
        *plan.group_by,
        *[
            join.left_column
            for join in plan.joins
        ],
        *[
            join.right_column
            for join in plan.joins
        ],
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
        _validate_column_reference(
            column_reference=column_reference,
            selected_table_keys=selected_table_keys,
            available_tables=available_tables,
        )

    aggregation_output_names: set[str] = set()

    for aggregation in plan.aggregations:
        if aggregation.output_name in aggregation_output_names:
            raise ValueError(
                "Database query plan contains duplicate "
                "aggregation output names."
            )

        aggregation_output_names.add(
            aggregation.output_name
        )

        if (
            aggregation.column is None
            and aggregation.function != "count"
        ):
            raise ValueError(
                "Only count aggregation may omit a column."
            )

        if aggregation.column is not None:
            column = _get_database_column(
                column_reference=aggregation.column,
                available_tables=available_tables,
            )

            if aggregation.function in {
                "sum",
                "avg",
            }:
                if not _is_numeric_type(
                    column.data_type
                ):
                    raise ValueError(
                        "SUM and AVG require a numeric column."
                    )

    filters_to_validate = [
        *plan.filters,
        *[
            aggregation.condition
            for aggregation in plan.aggregations
            if aggregation.condition is not None
        ],
    ]

    for query_filter in filters_to_validate:
        if query_filter.operator in {
            "is_null",
            "is_not_null",
        }:
            if query_filter.value is not None:
                raise ValueError(
                    "Null-check filters must not have a value."
                )

        elif query_filter.operator == "in":
            if (
                not isinstance(query_filter.value, list)
                or not query_filter.value
            ):
                raise ValueError(
                    "IN filters require a non-empty list."
                )

        else:
            if query_filter.value is None:
                raise ValueError(
                    "This filter operator requires a value."
                )

            if isinstance(query_filter.value, list):
                raise ValueError(
                    "Only IN filters may use a list value."
                )

        if query_filter.operator in {
            "contains",
            "starts_with",
            "ends_with",
        }:
            column = _get_database_column(
                column_reference=query_filter.column,
                available_tables=available_tables,
            )

            if not _is_string_type(
                column.data_type
            ):
                raise ValueError(
                    "Text filter operators require "
                    "a string column."
                )

    derived_output_names: set[str] = set()

    for derived_metric in plan.derived_metrics:
        normalized_output_name = (
            derived_metric.output_name.casefold()
        )

        existing_output_names = {
            name.casefold()
            for name in aggregation_output_names
        } | derived_output_names

        if normalized_output_name in existing_output_names:
            raise ValueError(
                "Database query plan contains duplicate "
                "metric output names."
            )

        derived_output_names.add(
            normalized_output_name
        )

        if (
            derived_metric.numerator
            not in aggregation_output_names
        ):
            raise ValueError(
                "Derived metric numerator must reference "
                "an aggregation output name."
            )

        if (
            derived_metric.denominator
            not in aggregation_output_names
        ):
            raise ValueError(
                "Derived metric denominator must reference "
                "an aggregation output name."
            )

    if plan.derived_metrics and not plan.aggregations:
        raise ValueError(
            "Derived metrics require aggregations."
        )

    selected_columns = {
        (
            column.schema_name,
            column.table_name,
            column.column_name,
        )
        for column in plan.columns
    }

    group_by_columns = {
        (
            column.schema_name,
            column.table_name,
            column.column_name,
        )
        for column in plan.group_by
    }

    if plan.group_by and not plan.aggregations:
        raise ValueError(
            "GROUP BY requires at least one aggregation."
        )

    if plan.aggregations:
        if not selected_columns.issubset(
            group_by_columns
        ):
            raise ValueError(
                "Non-aggregated selected columns must "
                "appear in GROUP BY."
            )

        if not group_by_columns.issubset(
            selected_columns
        ):
            raise ValueError(
                "GROUP BY columns must also be selected."
            )

    if plan.aggregations:
        for query_sort in plan.sort:
            sort_key = (
                query_sort.column.schema_name,
                query_sort.column.table_name,
                query_sort.column.column_name,
            )

            if sort_key not in group_by_columns:
                raise ValueError(
                    "Aggregated queries may only sort "
                    "by GROUP BY columns."
                )

    if not plan.columns and not plan.aggregations:
        raise ValueError(
            "Database query plan must select at least "
            "one column or aggregation."
        )

    _validate_joins(
        plan=plan,
        schema_context=schema_context,
    )


def _validate_joins(
    plan: DatabaseQueryPlan,
    schema_context: DatabaseSchemaContext,
) -> None:
    selected_table_keys = {
        (
            table.schema_name,
            table.table_name,
        )
        for table in plan.tables
    }

    if len(plan.tables) == 1:
        if plan.joins:
            raise ValueError(
                "Single-table queries must not contain joins."
            )

        if plan.requires_join:
            raise ValueError(
                "Single-table queries must set "
                "requires_join to false."
            )

        return

    if not plan.requires_join:
        raise ValueError(
            "Multi-table queries must set "
            "requires_join to true."
        )

    if len(plan.joins) != len(plan.tables) - 1:
        raise ValueError(
            "The current join model requires exactly "
            "one fewer join than selected tables."
        )

    allowed_relationships = {
        frozenset(
            (
                left,
                right,
            )
        )
        for left, right
        in get_allowed_database_relationships(
            schema_context
        )
    }

    seen_relationships: set[
        frozenset[tuple[str, str, str]]
    ] = set()

    graph: dict[
        tuple[str, str],
        set[tuple[str, str]],
    ] = {
        table_key: set()
        for table_key in selected_table_keys
    }

    for join in plan.joins:
        left_key = (
            join.left_column.schema_name,
            join.left_column.table_name,
            join.left_column.column_name,
        )

        right_key = (
            join.right_column.schema_name,
            join.right_column.table_name,
            join.right_column.column_name,
        )

        left_table_key = left_key[:2]
        right_table_key = right_key[:2]

        if left_table_key == right_table_key:
            raise ValueError(
                "A join must connect two different tables."
            )

        if (
            left_table_key not in selected_table_keys
            or right_table_key not in selected_table_keys
        ):
            raise ValueError(
                "Join columns must belong to selected tables."
            )

        relationship_key = frozenset(
            (
                left_key,
                right_key,
            )
        )

        if relationship_key not in allowed_relationships:
            raise ValueError(
                "Database query plan contains a join "
                "that is not in the approved "
                "relationship catalog."
            )

        if relationship_key in seen_relationships:
            raise ValueError(
                "Database query plan contains a duplicate join."
            )

        seen_relationships.add(
            relationship_key
        )

        graph[left_table_key].add(
            right_table_key
        )

        graph[right_table_key].add(
            left_table_key
        )

    start_table = next(
        iter(selected_table_keys)
    )

    visited: set[tuple[str, str]] = set()
    pending = [start_table]

    while pending:
        current = pending.pop()

        if current in visited:
            continue

        visited.add(current)

        pending.extend(
            graph[current] - visited
        )

    if visited != selected_table_keys:
        raise ValueError(
            "Selected tables must form one connected "
            "join graph."
        )


def _validate_column_reference(
    column_reference: DatabaseQueryColumnReference,
    selected_table_keys: set[tuple[str, str]],
    available_tables: dict[
        tuple[str, str],
        DatabaseTable,
    ],
) -> None:
    table_key = (
        column_reference.schema_name,
        column_reference.table_name,
    )

    if table_key not in selected_table_keys:
        raise ValueError(
            "Database query plan references a column from "
            "a table that was not selected: "
            f"{column_reference.schema_name}."
            f"{column_reference.table_name}."
            f"{column_reference.column_name}"
        )

    table = available_tables[table_key]

    available_columns = {
        column.name
        for column in table.columns
    }

    if column_reference.column_name not in available_columns:
        raise ValueError(
            "Database query plan contains an unknown column: "
            f"{column_reference.schema_name}."
            f"{column_reference.table_name}."
            f"{column_reference.column_name}"
        )


def _get_database_column(
    column_reference: DatabaseQueryColumnReference,
    available_tables: dict[
        tuple[str, str],
        DatabaseTable,
    ],
):
    table_key = (
        column_reference.schema_name,
        column_reference.table_name,
    )

    table = available_tables[table_key]

    for column in table.columns:
        if column.name == column_reference.column_name:
            return column

    raise ValueError(
        "Database query plan contains an unknown column."
    )


def _is_numeric_type(
    data_type: str,
) -> bool:
    return data_type.lower() in {
        "bigint",
        "int",
        "smallint",
        "tinyint",
        "decimal",
        "numeric",
        "money",
        "smallmoney",
        "float",
        "real",
    }


def _is_string_type(
    data_type: str,
) -> bool:
    return data_type.lower() in {
        "char",
        "varchar",
        "nchar",
        "nvarchar",
    }