from pathlib import PurePosixPath
from typing import Any

from pbir_example_catalog import (
    load_relevant_pbir_examples,
)
from pbir_project_context import PBIRProjectContext
from report_plan import ReportPlan
from semantic_model_context import SemanticModelContext


PBIR_FILE_STRUCTURE = {
    "page": {
        "path_pattern": (
            "Report/definition/pages/"
            "<page_id>/page.json"
        ),
        "rules": [
            "page.json contains page metadata only.",
            "Do not embed visual definitions inside page.json.",
        ],
    },
    "visual": {
        "path_pattern": (
            "Report/definition/pages/"
            "<page_id>/visuals/"
            "<visual_id>/visual.json"
        ),
        "rules": [
            "Each visual must be stored in its own visual.json file.",
            "The visual JSON name must match <visual_id>.",
        ],
    },
    "pages_metadata": {
        "path": (
            "Report/definition/pages/pages.json"
        ),
        "rules": [
            "Preserve all existing page IDs in pageOrder.",
            "Add newly created page IDs to pageOrder.",
            (
                "When a reusable blank page is used, keep its "
                "existing page ID instead of adding a replacement "
                "page ID for that ReportPlan page."
            ),
        ],
    },
}


def build_pbir_authoring_context(
    plan: ReportPlan,
    semantic_context: SemanticModelContext,
    project_context: PBIRProjectContext,
) -> dict[str, Any]:
    """Build the minimal context needed for PBIR authoring."""
    examples, missing_example_types = (
        load_relevant_pbir_examples(plan)
    )

    if missing_example_types:
        raise ValueError(
            "No validated PBIR example is available "
            "for visual type(s): "
            + ", ".join(
                sorted(missing_example_types)
            )
        )

    relevant_project_files = [
        pbir_file
        for pbir_file in project_context.files
        if _is_relevant_project_file(
            pbir_file.path
        )
    ]

    reusable_blank_page = (
        _find_reusable_blank_page(
            project_context
        )
    )

    return {
        "report_plan": plan.model_dump(),
        "semantic_model": semantic_context.model_dump(),
        "pbir_file_structure": PBIR_FILE_STRUCTURE,
        "pbir_examples": examples,
        "missing_example_types": missing_example_types,
        "reusable_blank_page": reusable_blank_page,
        "current_report_files": [
            pbir_file.model_dump()
            for pbir_file in relevant_project_files
        ],
    }


def _find_reusable_blank_page(
    project_context: PBIRProjectContext,
) -> dict[str, Any] | None:
    """Find the single blank page from a blank Power BI template."""
    page_files = [
        pbir_file
        for pbir_file in project_context.files
        if (
            pbir_file.path.startswith(
                "Report/definition/pages/"
            )
            and pbir_file.path.endswith(
                "/page.json"
            )
        )
    ]

    if len(page_files) != 1:
        return None

    page_file = page_files[0]

    page_path = PurePosixPath(
        page_file.path
    )

    parts = page_path.parts

    if (
        len(parts) != 5
        or parts[:3] != (
            "Report",
            "definition",
            "pages",
        )
    ):
        return None

    page_id = parts[3]

    visual_prefix = (
        f"Report/definition/pages/"
        f"{page_id}/visuals/"
    )

    has_visuals = any(
        pbir_file.path.startswith(
            visual_prefix
        )
        and pbir_file.path.endswith(
            "/visual.json"
        )
        for pbir_file in project_context.files
    )

    if has_visuals:
        return None

    pages_metadata_file = next(
        (
            pbir_file
            for pbir_file in project_context.files
            if pbir_file.path
            == "Report/definition/pages/pages.json"
        ),
        None,
    )

    if pages_metadata_file is None:
        return None

    page_order = (
        pages_metadata_file.content.get(
            "pageOrder"
        )
    )

    active_page_name = (
        pages_metadata_file.content.get(
            "activePageName"
        )
    )

    if page_order != [page_id]:
        return None

    if active_page_name != page_id:
        return None

    return {
        "page_id": page_id,
        "page_path": page_file.path,
        "page_content": page_file.content,
    }


def _is_relevant_project_file(
    path: str,
) -> bool:
    """Select structural PBIR files needed for report authoring."""
    if path == "Report/definition/report.json":
        return True

    if path == "Report/definition/pages/pages.json":
        return True

    if (
        path.startswith(
            "Report/definition/pages/"
        )
        and path.endswith("/page.json")
    ):
        return True

    return False