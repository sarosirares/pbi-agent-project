from typing import Any

from pbir_project_context import (
    PBIRProjectContext,
)
from semantic_model_context import (
    SemanticModelContext,
)


def build_project_inspection_context(
    semantic_context: SemanticModelContext,
    project_context: PBIRProjectContext,
) -> dict[str, Any]:
    """Build a concise read-only description of a Power BI project."""
    pages_by_id: dict[
        str,
        dict[str, Any],
    ] = {}

    page_order: list[str] = []

    for pbir_file in project_context.files:
        path = pbir_file.path
        content = pbir_file.content

        if (
            path
            == "Report/definition/pages/pages.json"
        ):
            raw_page_order = (
                content.get(
                    "pageOrder"
                )
            )

            if isinstance(
                raw_page_order,
                list,
            ):
                page_order = [
                    str(page_id)
                    for page_id
                    in raw_page_order
                ]

            continue

        parts = path.split("/")

        if (
            len(parts) == 5
            and parts[:3]
            == [
                "Report",
                "definition",
                "pages",
            ]
            and parts[-1]
            == "page.json"
        ):
            page_id = parts[3]

            display_name = (
                content.get(
                    "displayName"
                )
            )

            pages_by_id[
                page_id
            ] = {
                "id": page_id,
                "display_name": (
                    display_name
                    if isinstance(
                        display_name,
                        str,
                    )
                    else page_id
                ),
                "visuals": [],
            }

    for pbir_file in project_context.files:
        path = pbir_file.path
        parts = path.split("/")

        if not (
            len(parts) == 7
            and parts[:3]
            == [
                "Report",
                "definition",
                "pages",
            ]
            and parts[4]
            == "visuals"
            and parts[-1]
            == "visual.json"
        ):
            continue

        page_id = parts[3]
        visual_id = parts[5]

        page = pages_by_id.setdefault(
            page_id,
            {
                "id": page_id,
                "display_name": page_id,
                "visuals": [],
            },
        )

        content = pbir_file.content

        visual_content = (
            content.get(
                "visual"
            )
        )

        visual_type = None

        if isinstance(
            visual_content,
            dict,
        ):
            raw_visual_type = (
                visual_content.get(
                    "visualType"
                )
            )

            if isinstance(
                raw_visual_type,
                str,
            ):
                visual_type = (
                    raw_visual_type
                )

        page["visuals"].append(
            {
                "id": visual_id,
                "visual_type": visual_type,
                "fields": (
                    _collect_field_references(
                        content
                    )
                ),
                "query_refs": (
                    _collect_string_values(
                        content,
                        "queryRef",
                    )
                ),
                "native_query_refs": (
                    _collect_string_values(
                        content,
                        "nativeQueryRef",
                    )
                ),
                "position": (
                    content.get(
                        "position"
                    )
                ),
            }
        )

    ordered_page_ids = [
        page_id
        for page_id in page_order
        if page_id in pages_by_id
    ]

    ordered_page_ids.extend(
        page_id
        for page_id in pages_by_id
        if page_id
        not in ordered_page_ids
    )

    pages = [
        pages_by_id[
            page_id
        ]
        for page_id
        in ordered_page_ids
    ]

    return {
        "semantic_model": (
            semantic_context
            .model_dump()
        ),
        "report": {
            "pages": pages,
        },
    }


def _collect_field_references(
    value: Any,
) -> list[dict[str, str]]:
    references: list[
        dict[str, str]
    ] = []

    seen: set[
        tuple[str, str, str]
    ] = set()

    def visit(
        node: Any,
    ) -> None:
        if isinstance(
            node,
            dict,
        ):
            for (
                pbir_key,
                field_kind,
            ) in (
                (
                    "Column",
                    "column",
                ),
                (
                    "Measure",
                    "measure",
                ),
            ):
                field = (
                    node.get(
                        pbir_key
                    )
                )

                if not isinstance(
                    field,
                    dict,
                ):
                    continue

                expression = (
                    field.get(
                        "Expression"
                    )
                )

                property_name = (
                    field.get(
                        "Property"
                    )
                )

                if not isinstance(
                    expression,
                    dict,
                ):
                    continue

                source_ref = (
                    expression.get(
                        "SourceRef"
                    )
                )

                if not isinstance(
                    source_ref,
                    dict,
                ):
                    continue

                table_name = (
                    source_ref.get(
                        "Entity"
                    )
                )

                if not (
                    isinstance(
                        table_name,
                        str,
                    )
                    and isinstance(
                        property_name,
                        str,
                    )
                ):
                    continue

                key = (
                    field_kind,
                    table_name,
                    property_name,
                )

                if key in seen:
                    continue

                seen.add(
                    key
                )

                references.append(
                    {
                        "kind": (
                            field_kind
                        ),
                        "table": (
                            table_name
                        ),
                        "name": (
                            property_name
                        ),
                    }
                )

            for child in (
                node.values()
            ):
                visit(
                    child
                )

            return

        if isinstance(
            node,
            list,
        ):
            for child in node:
                visit(
                    child
                )

    visit(
        value
    )

    return references


def _collect_string_values(
    value: Any,
    key_name: str,
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()

    def visit(
        node: Any,
    ) -> None:
        if isinstance(
            node,
            dict,
        ):
            raw_value = (
                node.get(
                    key_name
                )
            )

            if (
                isinstance(
                    raw_value,
                    str,
                )
                and raw_value
                not in seen
            ):
                seen.add(
                    raw_value
                )

                values.append(
                    raw_value
                )

            for child in (
                node.values()
            ):
                visit(
                    child
                )

            return

        if isinstance(
            node,
            list,
        ):
            for child in node:
                visit(
                    child
                )

    visit(
        value
    )

    return values