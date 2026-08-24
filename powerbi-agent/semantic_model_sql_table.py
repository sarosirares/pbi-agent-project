import json
import math
import re
import unicodedata
import uuid
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from database_query_models import (
    DatabaseQueryColumnReference,
    DatabaseQueryPlan,
)
from database_query_renderer import (
    QueryParameter,
    render_database_query,
)
from database_schema_context import (
    DatabaseColumn,
    DatabaseSchemaContext,
)


SQL_TO_TMDL_TYPE = {
    "bigint": "int64",
    "int": "int64",
    "smallint": "int64",
    "tinyint": "int64",
    "bit": "boolean",
    "decimal": "decimal",
    "numeric": "decimal",
    "money": "decimal",
    "smallmoney": "decimal",
    "float": "double",
    "real": "double",
    "date": "dateTime",
    "datetime": "dateTime",
    "datetime2": "dateTime",
    "smalldatetime": "dateTime",
    "char": "string",
    "varchar": "string",
    "nchar": "string",
    "nvarchar": "string",
    "text": "string",
    "ntext": "string",
    "uniqueidentifier": "string",
}


class SemanticModelSqlColumnSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    source_column: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    summarize_by: str = Field(min_length=1)


class SemanticModelSqlTableSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_name: str = Field(min_length=1)
    sql: str = Field(min_length=1)

    parameters: list[QueryParameter] = Field(
        default_factory=list,
    )

    columns: list[SemanticModelSqlColumnSpec] = Field(
        min_length=1,
    )


def is_supported_sql_data_type(
    data_type: str,
) -> bool:
    return data_type.casefold() in SQL_TO_TMDL_TYPE


def normalize_semantic_table_name(
    value: str,
) -> str:
    clean_value = value.strip()

    if not clean_value:
        raise ValueError(
            "Semantic table name must not be empty."
        )

    ascii_value = (
        unicodedata.normalize(
            "NFKD",
            clean_value,
        )
        .encode(
            "ascii",
            "ignore",
        )
        .decode("ascii")
    )

    tokens = re.findall(
        r"[A-Za-z0-9]+",
        ascii_value,
    )

    if not tokens:
        raise ValueError(
            "Semantic table name contains "
            "no usable characters."
        )

    normalized_name = "".join(
        token[:1].upper()
        + token[1:]
        for token in tokens
    )

    if normalized_name[0].isdigit():
        normalized_name = (
            "Report"
            + normalized_name
        )

    normalized_name = (
        normalized_name[:64]
    )

    if not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9]*",
        normalized_name,
    ):
        raise ValueError(
            "Semantic table name could not "
            "be normalized safely."
        )

    return normalized_name


def build_semantic_model_sql_table_spec(
    plan: DatabaseQueryPlan,
    schema_context: DatabaseSchemaContext,
    table_name: str,
) -> SemanticModelSqlTableSpec:
    clean_table_name = (
        normalize_semantic_table_name(
            table_name
        )
    )

    semantic_query_plan = plan

    if (
        plan.limit is None
        and plan.sort
    ):
        semantic_query_plan = (
            plan.model_copy(
                update={
                    "sort": [],
                }
            )
        )

    rendered_query = render_database_query(
        plan=semantic_query_plan,
        schema_context=schema_context,
    )

    output_names = [
        column.column_name
        for column in plan.columns
    ] + [
        aggregation.output_name
        for aggregation in plan.aggregations
    ]

    normalized_output_names = [
        name.casefold()
        for name in output_names
    ]

    if len(set(normalized_output_names)) != len(
        normalized_output_names
    ):
        raise ValueError(
            "Database query plan contains duplicate output names."
        )

    column_specs: list[
        SemanticModelSqlColumnSpec
    ] = []

    outer_select_expressions: list[str] = []

    for index, column_reference in enumerate(
        plan.columns,
        start=1,
    ):
        database_column = _find_database_column(
            schema_context=schema_context,
            column_reference=column_reference,
        )

        data_type = _map_sql_type_to_tmdl(
            database_column.data_type
        )

        source_column = f"AgentField{index}"

        column_specs.append(
            SemanticModelSqlColumnSpec(
                name=column_reference.column_name,
                source_column=source_column,
                data_type=data_type,
                summarize_by="none",
            )
        )

        outer_select_expressions.append(
            (
                f"[AgentQuery]."
                f"{_quote_sql_identifier(column_reference.column_name)} "
                f"AS {_quote_sql_identifier(source_column)}"
            )
        )

    for index, aggregation in enumerate(
        plan.aggregations,
        start=1,
    ):
        if aggregation.function in {
            "count",
            "count_distinct",
        }:
            data_type = "int64"

        else:
            if aggregation.column is None:
                raise ValueError(
                    "This aggregation requires "
                    "a source column."
                )

            database_column = (
                _find_database_column(
                    schema_context=schema_context,
                    column_reference=(
                        aggregation.column
                    ),
                )
            )

            data_type = (
                _map_sql_type_to_tmdl(
                    database_column.data_type
                )
            )

        summarize_by = (
            "sum"
            if data_type in {
                "int64",
                "decimal",
                "double",
            }
            else "none"
        )

        source_column = f"AgentMetric{index}"

        column_specs.append(
            SemanticModelSqlColumnSpec(
                name=aggregation.output_name,
                source_column=source_column,
                data_type=data_type,
                summarize_by=summarize_by,
            )
        )

        outer_select_expressions.append(
            (
                f"[AgentQuery]."
                f"{_quote_sql_identifier(aggregation.output_name)} "
                f"AS {_quote_sql_identifier(source_column)}"
            )
        )

    inner_sql = rendered_query.sql.strip()

    if inner_sql.endswith(";"):
        inner_sql = inner_sql[:-1].rstrip()

    indented_inner_sql = "\n".join(
        f"    {line}"
        for line in inner_sql.splitlines()
    )

    sql = (
        "SELECT\n"
        "    "
        + ",\n    ".join(
            outer_select_expressions
        )
        + "\nFROM (\n"
        + indented_inner_sql
        + "\n) AS [AgentQuery];"
    )

    if rendered_query.parameters:
        sql = _replace_qmark_parameters_with_named(
            sql=sql,
            parameter_count=len(
                rendered_query.parameters
            ),
        )

    return SemanticModelSqlTableSpec(
        table_name=clean_table_name,
        sql=sql,
        parameters=rendered_query.parameters,
        columns=column_specs,
    )


def write_sql_backed_semantic_table(
    semantic_model_path: str | Path,
    spec: SemanticModelSqlTableSpec,
    server: str,
    database: str,
) -> Path:
    semantic_model_folder = Path(
        semantic_model_path
    ).resolve()

    if not semantic_model_folder.is_dir():
        raise FileNotFoundError(
            "Semantic model folder not found: "
            f"{semantic_model_folder}"
        )

    tables_folder = (
        semantic_model_folder
        / "definition"
        / "tables"
    )

    model_file = (
        semantic_model_folder
        / "definition"
        / "model.tmdl"
    )

    if not model_file.is_file():
        raise FileNotFoundError(
            f"model.tmdl not found: {model_file}"
        )

    tables_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    table_file = (
        tables_folder
        / f"{spec.table_name}.tmdl"
    )

    if table_file.exists():
        raise FileExistsError(
            "Semantic table file already exists: "
            f"{table_file}"
        )

    table_tmdl = _build_table_tmdl(
        spec=spec,
        server=server,
        database=database,
    )

    table_file.write_text(
        table_tmdl,
        encoding="utf-8",
    )

    try:
        _add_table_reference_to_model(
            model_file=model_file,
            table_name=spec.table_name,
        )
    except Exception:
        table_file.unlink(
            missing_ok=True
        )
        raise

    return table_file


def clear_semantic_model_local_cache(
    semantic_model_path: str | Path,
) -> None:
    semantic_model_folder = Path(
        semantic_model_path
    ).resolve()

    cache_file = (
        semantic_model_folder
        / ".pbi"
        / "cache.abf"
    )

    if cache_file.is_file():
        cache_file.unlink()


def _find_database_column(
    schema_context: DatabaseSchemaContext,
    column_reference: DatabaseQueryColumnReference,
) -> DatabaseColumn:
    for table in schema_context.tables:
        if (
            table.schema_name
            == column_reference.schema_name
            and table.name
            == column_reference.table_name
        ):
            for column in table.columns:
                if (
                    column.name
                    == column_reference.column_name
                ):
                    return column

            break

    raise ValueError(
        "Database query plan contains an unknown column: "
        f"{column_reference.schema_name}."
        f"{column_reference.table_name}."
        f"{column_reference.column_name}"
    )


def _map_sql_type_to_tmdl(
    data_type: str,
) -> str:
    mapped_type = SQL_TO_TMDL_TYPE.get(
        data_type.casefold()
    )

    if mapped_type is None:
        raise ValueError(
            "Unsupported SQL data type for semantic model: "
            f"{data_type}"
        )

    return mapped_type


def _build_table_tmdl(
    spec: SemanticModelSqlTableSpec,
    server: str,
    database: str,
) -> str:
    lines = [
        f"table {spec.table_name}",
        f"\tlineageTag: {uuid.uuid4()}",
        "",
    ]

    for column in spec.columns:
        lines.extend(
            [
                (
                    "\tcolumn "
                    f"{_quote_tmdl_identifier(column.name)}"
                ),
                f"\t\tdataType: {column.data_type}",
                f"\t\tlineageTag: {uuid.uuid4()}",
                (
                    "\t\tsummarizeBy: "
                    f"{column.summarize_by}"
                ),
                (
                    "\t\tsourceColumn: "
                    f"{column.source_column}"
                ),
                "",
                (
                    "\t\tannotation "
                    "SummarizationSetBy = Automatic"
                ),
                "",
            ]
        )

    m_server = _escape_m_text(
        server
    )

    m_database = _escape_m_text(
        database
    )

    m_sql = _escape_m_text(
        spec.sql
    )

    if spec.parameters:
        m_parameters = (
            _build_m_parameter_record(
                spec.parameters
            )
        )

        source_lines = [
            "\t\t\t\tlet",
            (
                "\t\t\t\t    Source = "
                f'Sql.Database("{m_server}", '
                f'"{m_database}"),'
            ),
            (
                "\t\t\t\t    Result = "
                "Value.NativeQuery("
            ),
            "\t\t\t\t        Source,",
            (
                "\t\t\t\t        "
                f'"{m_sql}",'
            ),
            (
                "\t\t\t\t        "
                f"{m_parameters}"
            ),
            "\t\t\t\t    )",
            "\t\t\t\tin",
            "\t\t\t\t    Result",
        ]

    else:
        source_lines = [
            "\t\t\t\tlet",
            (
                "\t\t\t\t    Source = "
                f'Sql.Database("{m_server}", '
                f'"{m_database}", '
                f'[Query = "{m_sql}"])'
            ),
            "\t\t\t\tin",
            "\t\t\t\t    Source",
        ]

    lines.extend(
        [
            (
                f"\tpartition "
                f"{spec.table_name} = m"
            ),
            "\t\tmode: import",
            "\t\tsource =",
            *source_lines,
            "",
            "\tannotation PBI_ResultType = Table",
            "",
        ]
    )

    return "\n".join(lines)


def _add_table_reference_to_model(
    model_file: Path,
    table_name: str,
) -> None:
    text = model_file.read_text(
        encoding="utf-8-sig"
    )

    existing_ref = re.search(
        (
            rf"^ref table "
            rf"{re.escape(table_name)}"
            rf"\s*$"
        ),
        text,
        flags=re.MULTILINE,
    )

    if existing_ref is not None:
        raise RuntimeError(
            "Semantic table reference already exists."
        )

    query_order_match = re.search(
        (
            r"^annotation PBI_QueryOrder = "
            r"(?P<value>\[.*\])\s*$"
        ),
        text,
        flags=re.MULTILINE,
    )

    if query_order_match is None:
        reference_match = re.search(
            r"^ref \w+\b.*$",
            text,
            flags=re.MULTILINE,
        )

        if reference_match is None:
            raise RuntimeError(
                "No model reference location was found."
            )

        query_order_annotation = (
            "annotation PBI_QueryOrder = "
            + json.dumps(
                [table_name],
                ensure_ascii=False,
            )
            + "\n\n"
        )

        text = (
            text[:reference_match.start()]
            + query_order_annotation
            + text[reference_match.start():]
        )

    else:
        query_order = json.loads(
            query_order_match.group(
                "value"
            )
        )

        if table_name in query_order:
            raise RuntimeError(
                "Semantic table already exists "
                "in PBI_QueryOrder."
            )

        query_order.append(
            table_name
        )

        query_order_replacement = (
            "annotation PBI_QueryOrder = "
            + json.dumps(
                query_order,
                ensure_ascii=False,
            )
        )

        text = (
            text[:query_order_match.start()]
            + query_order_replacement
            + text[query_order_match.end():]
        )

    culture_match = re.search(
        r"^ref cultureInfo\b.*$",
        text,
        flags=re.MULTILINE,
    )

    if culture_match is None:
        raise RuntimeError(
            "Culture reference was not found."
        )

    text = (
        text[:culture_match.start()]
        + f"ref table {table_name}\n\n"
        + text[culture_match.start():]
    )

    model_file.write_text(
        text,
        encoding="utf-8",
    )


def _quote_sql_identifier(
    value: str,
) -> str:
    escaped = value.replace(
        "]",
        "]]",
    )

    return f"[{escaped}]"


def _quote_tmdl_identifier(
    value: str,
) -> str:
    escaped = value.replace(
        "'",
        "''",
    )

    return f"'{escaped}'"


def _escape_m_text(
    value: str,
) -> str:
    normalized = (
        value
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    return (
        normalized
        .replace("#", "#(#)")
        .replace('"', '""')
        .replace("\n", "#(lf)")
    )


def _replace_qmark_parameters_with_named(
    sql: str,
    parameter_count: int,
) -> str:
    placeholder_count = sql.count("?")

    if placeholder_count != parameter_count:
        raise ValueError(
            "SQL parameter placeholder count "
            "does not match parameter count."
        )

    named_sql = sql

    for index in range(
        1,
        parameter_count + 1,
    ):
        named_sql = named_sql.replace(
            "?",
            f"@p{index}",
            1,
        )

    return named_sql


def _build_m_parameter_record(
    parameters: list[QueryParameter],
) -> str:
    rendered_parameters = [
        (
            f"p{index} = "
            f"{_render_m_parameter_value(parameter)}"
        )
        for index, parameter in enumerate(
            parameters,
            start=1,
        )
    ]

    return (
        "["
        + ", ".join(rendered_parameters)
        + "]"
    )


def _render_m_parameter_value(
    value: QueryParameter,
) -> str:
    if isinstance(value, bool):
        return (
            "true"
            if value
            else "false"
        )

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(
                "Non-finite numeric query "
                "parameters are not supported."
            )

        return repr(value)

    if isinstance(value, str):
        escaped_value = _escape_m_text(
            value
        )

        return f'"{escaped_value}"'

    raise TypeError(
        "Unsupported query parameter type: "
        f"{type(value).__name__}"
    )