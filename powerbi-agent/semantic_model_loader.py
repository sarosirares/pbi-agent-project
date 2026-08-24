from pathlib import Path

from semantic_model_context import (
    SemanticColumn,
    SemanticMeasure,
    SemanticModelContext,
    SemanticTable,
)


def load_semantic_model_context(
    semantic_model_path: str | Path,
) -> SemanticModelContext:
    """Load the semantic schema from a TMDL semantic model folder."""
    model_path = Path(semantic_model_path)

    tables_path = (
        model_path
        / "definition"
        / "tables"
    )

    if not tables_path.is_dir():
        raise FileNotFoundError(
            f"TMDL tables directory not found: {tables_path}"
        )

    table_files = sorted(
        tables_path.glob("*.tmdl")
    )

    if not table_files:
        raise FileNotFoundError(
            f"No TMDL table files found in: {tables_path}"
        )

    tables = [
        _parse_table_file(table_file)
        for table_file in table_files
    ]

    return SemanticModelContext(
        tables=tables
    )


def _parse_table_file(
    table_file: Path,
) -> SemanticTable:
    """Extract table, column, and measure metadata from one TMDL file."""
    lines = table_file.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    table_line_index = _find_table_declaration(
        lines,
        table_file,
    )

    table_name = _parse_object_name(
        lines[table_line_index].strip(),
        object_type="table",
    )

    child_indent = _find_direct_child_indent(
        lines,
        table_line_index,
        table_file,
    )

    columns: list[SemanticColumn] = []
    measures: list[SemanticMeasure] = []

    index = table_line_index + 1

    while index < len(lines):
        line = lines[index]

        if (
            not line.strip()
            or _indent_width(line) != child_indent
        ):
            index += 1
            continue

        stripped_line = line.strip()

        if stripped_line.startswith("column "):
            block_end = _find_object_block_end(
                lines,
                start_index=index + 1,
                object_indent=child_indent,
            )

            properties = _read_object_properties(
                lines,
                start_index=index + 1,
                end_index=block_end,
                object_indent=child_indent,
            )

            column_name = _parse_object_name(
                stripped_line,
                object_type="column",
            )

            data_type = properties.get("datatype")

            summarization = properties.get(
                "summarizeby"
            )

            if (
                summarization is not None
                and summarization.casefold() == "none"
            ):
                summarization = None

            columns.append(
                SemanticColumn(
                    name=column_name,
                    data_type=data_type,
                    default_summarization=summarization,
                )
            )

            index = block_end
            continue

        if stripped_line.startswith("measure "):
            measure_name = _parse_object_name(
                stripped_line,
                object_type="measure",
            )

            measures.append(
                SemanticMeasure(
                    name=measure_name
                )
            )

        index += 1

    return SemanticTable(
        name=table_name,
        columns=columns,
        measures=measures,
    )


def _find_table_declaration(
    lines: list[str],
    table_file: Path,
) -> int:
    """Find the top-level table declaration."""
    for index, line in enumerate(lines):
        if (
            _indent_width(line) == 0
            and line.strip().startswith("table ")
        ):
            return index

    raise ValueError(
        f"No table declaration found in: {table_file}"
    )


def _find_direct_child_indent(
    lines: list[str],
    table_line_index: int,
    table_file: Path,
) -> int:
    """Find the indentation level used by direct table children."""
    indentation_levels: list[int] = []

    for line in lines[table_line_index + 1:]:
        stripped_line = line.strip()

        if (
            not stripped_line
            or stripped_line.startswith("///")
        ):
            continue

        indentation = _indent_width(line)

        if indentation > 0:
            indentation_levels.append(
                indentation
            )

    if not indentation_levels:
        raise ValueError(
            f"Table has no content: {table_file}"
        )

    return min(indentation_levels)


def _find_object_block_end(
    lines: list[str],
    start_index: int,
    object_indent: int,
) -> int:
    """Find where the current TMDL object block ends."""
    index = start_index

    while index < len(lines):
        line = lines[index]

        if not line.strip():
            index += 1
            continue

        if _indent_width(line) <= object_indent:
            break

        index += 1

    return index


def _read_object_properties(
    lines: list[str],
    start_index: int,
    end_index: int,
    object_indent: int,
) -> dict[str, str]:
    """Read direct properties from a TMDL object block."""
    property_lines = [
        line
        for line in lines[start_index:end_index]
        if (
            line.strip()
            and _indent_width(line) > object_indent
        )
    ]

    if not property_lines:
        return {}

    property_indent = min(
        _indent_width(line)
        for line in property_lines
    )

    properties: dict[str, str] = {}

    for line in property_lines:
        if _indent_width(line) != property_indent:
            continue

        stripped_line = line.strip()

        if ":" not in stripped_line:
            continue

        key, value = stripped_line.split(
            ":",
            maxsplit=1,
        )

        properties[key.strip().casefold()] = (
            value.strip()
        )

    return properties


def _parse_object_name(
    declaration: str,
    object_type: str,
) -> str:
    """Extract an object name from a TMDL declaration."""
    prefix = f"{object_type} "

    if not declaration.startswith(prefix):
        raise ValueError(
            f"Invalid {object_type} declaration: "
            f"{declaration}"
        )

    remainder = declaration[
        len(prefix):
    ].lstrip()

    if remainder.startswith("'"):
        return _parse_quoted_name(
            remainder
        )

    name = remainder.split(
        "=",
        maxsplit=1,
    )[0].strip()

    if not name:
        raise ValueError(
            f"Missing {object_type} name: "
            f"{declaration}"
        )

    return name


def _parse_quoted_name(
    text: str,
) -> str:
    """Parse a single-quoted TMDL identifier."""
    characters: list[str] = []
    index = 1

    while index < len(text):
        character = text[index]

        if character == "'":
            if (
                index + 1 < len(text)
                and text[index + 1] == "'"
            ):
                characters.append("'")
                index += 2
                continue

            return "".join(characters)

        characters.append(character)
        index += 1

    raise ValueError(
        f"Unterminated quoted TMDL name: {text}"
    )


def _indent_width(
    line: str,
) -> int:
    """Return the visual width of the leading indentation."""
    leading_whitespace = (
        line[:len(line) - len(line.lstrip())]
    )

    return len(
        leading_whitespace.expandtabs(4)
    )