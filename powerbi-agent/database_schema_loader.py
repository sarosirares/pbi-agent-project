from collections import defaultdict
from typing import Any

from database_connection import connect_to_database
from database_schema_context import (
    DatabaseColumn,
    DatabaseForeignKey,
    DatabaseForeignKeyColumn,
    DatabaseKey,
    DatabaseSchemaContext,
    DatabaseTable,
)


TableKey = tuple[str, str]


def load_database_schema_context() -> DatabaseSchemaContext:
    """Load SQL Server metadata without reading user table data."""
    connection = connect_to_database()

    try:
        database_name = _load_database_name(connection)
        table_data = _load_tables_and_columns(connection)
        primary_keys = _load_key_constraints(
            connection,
            constraint_type="PK",
        )
        unique_constraints = _load_key_constraints(
            connection,
            constraint_type="UQ",
        )
        foreign_keys = _load_foreign_keys(connection)

        tables: list[DatabaseTable] = []

        for table_key in sorted(table_data):
            schema_name, table_name = table_key

            tables.append(
                DatabaseTable(
                    schema_name=schema_name,
                    name=table_name,
                    columns=table_data[table_key],
                    primary_key=primary_keys.get(table_key),
                    unique_constraints=unique_constraints.get(
                        table_key,
                        [],
                    ),
                    foreign_keys=foreign_keys.get(
                        table_key,
                        [],
                    ),
                )
            )

        return DatabaseSchemaContext(
            database_name=database_name,
            tables=tables,
        )

    finally:
        connection.close()


def _load_database_name(connection: Any) -> str:
    cursor = connection.cursor()
    cursor.execute("SELECT DB_NAME();")

    row = cursor.fetchone()

    if row is None or not isinstance(row[0], str):
        raise RuntimeError(
            "Could not determine the current database name."
        )

    return row[0]


def _load_tables_and_columns(
    connection: Any,
) -> dict[TableKey, list[DatabaseColumn]]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            s.name AS schema_name,
            t.name AS table_name,
            c.column_id,
            c.name AS column_name,
            ty.name AS data_type,
            CASE
                WHEN ty.name IN ('nchar', 'nvarchar')
                     AND c.max_length > 0
                    THEN c.max_length / 2
                ELSE c.max_length
            END AS max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            c.is_identity
        FROM sys.tables AS t
        INNER JOIN sys.schemas AS s
            ON t.schema_id = s.schema_id
        INNER JOIN sys.columns AS c
            ON t.object_id = c.object_id
        INNER JOIN sys.types AS ty
            ON c.user_type_id = ty.user_type_id
        WHERE t.is_ms_shipped = 0
        ORDER BY
            s.name,
            t.name,
            c.column_id;
        """
    )

    tables: dict[
        TableKey,
        list[DatabaseColumn],
    ] = defaultdict(list)

    for row in cursor.fetchall():
        table_key = (
            str(row.schema_name),
            str(row.table_name),
        )

        tables[table_key].append(
            DatabaseColumn(
                name=str(row.column_name),
                ordinal_position=int(row.column_id),
                data_type=str(row.data_type),
                max_length=(
                    int(row.max_length)
                    if row.max_length is not None
                    else None
                ),
                precision=(
                    int(row.precision)
                    if row.precision is not None
                    else None
                ),
                scale=(
                    int(row.scale)
                    if row.scale is not None
                    else None
                ),
                is_nullable=bool(row.is_nullable),
                is_identity=bool(row.is_identity),
            )
        )

    return dict(tables)


def _load_key_constraints(
    connection: Any,
    constraint_type: str,
) -> dict[TableKey, Any]:
    if constraint_type not in {"PK", "UQ"}:
        raise ValueError(
            f"Unsupported constraint type: {constraint_type}"
        )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            s.name AS schema_name,
            t.name AS table_name,
            kc.name AS constraint_name,
            ic.key_ordinal,
            c.name AS column_name
        FROM sys.key_constraints AS kc
        INNER JOIN sys.tables AS t
            ON kc.parent_object_id = t.object_id
        INNER JOIN sys.schemas AS s
            ON t.schema_id = s.schema_id
        INNER JOIN sys.index_columns AS ic
            ON kc.parent_object_id = ic.object_id
            AND kc.unique_index_id = ic.index_id
        INNER JOIN sys.columns AS c
            ON ic.object_id = c.object_id
            AND ic.column_id = c.column_id
        WHERE kc.type = ?
        ORDER BY
            s.name,
            t.name,
            kc.name,
            ic.key_ordinal;
        """,
        constraint_type,
    )

    grouped: dict[
        tuple[str, str, str],
        list[str],
    ] = defaultdict(list)

    for row in cursor.fetchall():
        key = (
            str(row.schema_name),
            str(row.table_name),
            str(row.constraint_name),
        )

        grouped[key].append(
            str(row.column_name)
        )

    if constraint_type == "PK":
        result: dict[TableKey, DatabaseKey] = {}

        for (
            schema_name,
            table_name,
            constraint_name,
        ), columns in grouped.items():
            result[(schema_name, table_name)] = DatabaseKey(
                name=constraint_name,
                columns=columns,
            )

        return result

    unique_result: dict[
        TableKey,
        list[DatabaseKey],
    ] = defaultdict(list)

    for (
        schema_name,
        table_name,
        constraint_name,
    ), columns in grouped.items():
        unique_result[
            (schema_name, table_name)
        ].append(
            DatabaseKey(
                name=constraint_name,
                columns=columns,
            )
        )

    return dict(unique_result)


def _load_foreign_keys(
    connection: Any,
) -> dict[TableKey, list[DatabaseForeignKey]]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            parent_schema.name AS schema_name,
            parent_table.name AS table_name,
            fk.name AS constraint_name,
            fkc.constraint_column_id,
            parent_column.name AS column_name,
            referenced_schema.name AS referenced_schema_name,
            referenced_table.name AS referenced_table_name,
            referenced_column.name AS referenced_column_name
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc
            ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables AS parent_table
            ON fk.parent_object_id = parent_table.object_id
        INNER JOIN sys.schemas AS parent_schema
            ON parent_table.schema_id = parent_schema.schema_id
        INNER JOIN sys.columns AS parent_column
            ON fkc.parent_object_id = parent_column.object_id
            AND fkc.parent_column_id = parent_column.column_id
        INNER JOIN sys.tables AS referenced_table
            ON fk.referenced_object_id =
               referenced_table.object_id
        INNER JOIN sys.schemas AS referenced_schema
            ON referenced_table.schema_id =
               referenced_schema.schema_id
        INNER JOIN sys.columns AS referenced_column
            ON fkc.referenced_object_id =
               referenced_column.object_id
            AND fkc.referenced_column_id =
               referenced_column.column_id
        ORDER BY
            parent_schema.name,
            parent_table.name,
            fk.name,
            fkc.constraint_column_id;
        """
    )

    grouped: dict[
        tuple[str, str, str, str, str],
        list[DatabaseForeignKeyColumn],
    ] = defaultdict(list)

    for row in cursor.fetchall():
        key = (
            str(row.schema_name),
            str(row.table_name),
            str(row.constraint_name),
            str(row.referenced_schema_name),
            str(row.referenced_table_name),
        )

        grouped[key].append(
            DatabaseForeignKeyColumn(
                column=str(row.column_name),
                referenced_column=str(
                    row.referenced_column_name
                ),
            )
        )

    result: dict[
        TableKey,
        list[DatabaseForeignKey],
    ] = defaultdict(list)

    for (
        schema_name,
        table_name,
        constraint_name,
        referenced_schema,
        referenced_table,
    ), columns in grouped.items():
        result[(schema_name, table_name)].append(
            DatabaseForeignKey(
                name=constraint_name,
                referenced_schema=referenced_schema,
                referenced_table=referenced_table,
                columns=columns,
            )
        )

    return dict(result)