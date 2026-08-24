from pathlib import PurePosixPath

from pbir_change_models import PBIRChangeSet
from pbir_project_context import PBIRProjectContext


PAGES_METADATA_PATH = PurePosixPath(
    "Report/definition/pages/pages.json"
)


def validate_pbir_change_set_structure(
    change_set: PBIRChangeSet,
    project_context: PBIRProjectContext,
) -> list[str]:
    """Validate structural consistency of proposed PBIR changes."""
    errors: list[str] = []

    existing_paths = {
        PurePosixPath(file.path)
        for file in project_context.files
    }

    operation_paths: set[PurePosixPath] = set()

    created_page_ids: set[str] = set()
    created_visual_ids: set[str] = set()

    pages_metadata_operation = None

    for operation in change_set.operations:
        path = PurePosixPath(
            operation.path.replace("\\", "/")
        )

        if path in operation_paths:
            errors.append(
                f"Duplicate operation path: '{operation.path}'."
            )
            continue

        operation_paths.add(path)

        if operation.operation == "create":
            if path in existing_paths:
                errors.append(
                    f"Create operation targets an existing file: "
                    f"'{operation.path}'."
                )

        if operation.operation == "update":
            if path not in existing_paths:
                errors.append(
                    f"Update operation targets a file that "
                    f"does not exist: '{operation.path}'."
                )

        if path == PAGES_METADATA_PATH:
            pages_metadata_operation = operation
            continue

        _validate_page_file(
            operation=operation,
            path=path,
            created_page_ids=created_page_ids,
            errors=errors,
        )

        _validate_visual_file(
            operation=operation,
            path=path,
            created_visual_ids=created_visual_ids,
            errors=errors,
        )

    _validate_pages_metadata(
        pages_metadata_operation=pages_metadata_operation,
        created_page_ids=created_page_ids,
        project_context=project_context,
        errors=errors,
    )

    return errors


def _validate_page_file(
    operation,
    path: PurePosixPath,
    created_page_ids: set[str],
    errors: list[str],
) -> None:
    """Validate a page.json operation."""
    parts = path.parts

    if (
        len(parts) != 5
        or parts[:3] != (
            "Report",
            "definition",
            "pages",
        )
        or parts[-1] != "page.json"
    ):
        return

    page_id = parts[3]

    content_name = operation.content.get(
        "name"
    )

    if content_name != page_id:
        errors.append(
            f"Page ID mismatch for '{path}': "
            f"path uses '{page_id}' but content name is "
            f"'{content_name}'."
        )

    if "visualContainers" in operation.content:
        errors.append(
            f"page.json must not embed visual definitions: "
            f"'{path}'."
        )

    if operation.operation == "create":
        created_page_ids.add(
            page_id
        )


def _validate_visual_file(
    operation,
    path: PurePosixPath,
    created_visual_ids: set[str],
    errors: list[str],
) -> None:
    """Validate a visual.json operation."""
    parts = path.parts

    if (
        len(parts) != 7
        or parts[:3] != (
            "Report",
            "definition",
            "pages",
        )
        or parts[4] != "visuals"
        or parts[-1] != "visual.json"
    ):
        return

    visual_id = parts[5]

    content_name = operation.content.get(
        "name"
    )

    if content_name != visual_id:
        errors.append(
            f"Visual ID mismatch for '{path}': "
            f"path uses '{visual_id}' but content name is "
            f"'{content_name}'."
        )

    if visual_id in created_visual_ids:
        errors.append(
            f"Duplicate visual ID: '{visual_id}'."
        )

    visual_content = operation.content.get(
        "visual"
    )

    if isinstance(visual_content, dict):
        if "title" in visual_content:
            errors.append(
                f"Unsupported PBIR property 'visual.title' "
                f"in '{path}'."
            )

    if operation.operation == "create":
        created_visual_ids.add(
            visual_id
        )


def _validate_pages_metadata(
    pages_metadata_operation,
    created_page_ids: set[str],
    project_context: PBIRProjectContext,
    errors: list[str],
) -> None:
    """Validate pages.json against existing and newly created pages."""
    if not created_page_ids:
        return

    if pages_metadata_operation is None:
        errors.append(
            "A new page was created but pages.json "
            "was not updated."
        )
        return

    page_order = pages_metadata_operation.content.get(
        "pageOrder"
    )

    if not isinstance(page_order, list):
        errors.append(
            "pages.json must contain a pageOrder list."
        )
        return

    for page_id in created_page_ids:
        if page_id not in page_order:
            errors.append(
                f"New page '{page_id}' is missing "
                "from pages.json pageOrder."
            )

    existing_page_ids = _get_existing_page_ids(
        project_context
    )

    for page_id in existing_page_ids:
        if page_id not in page_order:
            errors.append(
                f"Existing page '{page_id}' was removed "
                "from pages.json pageOrder."
            )


def _get_existing_page_ids(
    project_context: PBIRProjectContext,
) -> set[str]:
    """Extract existing page IDs from page.json paths."""
    page_ids: set[str] = set()

    for file in project_context.files:
        path = PurePosixPath(
            file.path
        )

        parts = path.parts

        if (
            len(parts) == 5
            and parts[:3] == (
                "Report",
                "definition",
                "pages",
            )
            and parts[-1] == "page.json"
        ):
            page_ids.add(
                parts[3]
            )

    return page_ids