from collections import Counter
from pathlib import PurePosixPath

from pbir_change_models import PBIRChangeSet
from report_plan import ReportPlan


def validate_pbir_change_set_plan(
    change_set: PBIRChangeSet,
    plan: ReportPlan,
    reusable_blank_page_id: str | None = None,
) -> list[str]:
    """Validate that authored pages match the ReportPlan."""
    errors: list[str] = []

    expected_page_names = [
        page.name
        for page in plan.pages
    ]

    authored_page_names: list[str] = []

    reused_blank_page = False

    for operation in change_set.operations:
        path = PurePosixPath(
            operation.path.replace("\\", "/")
        )

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
            continue

        display_name = operation.content.get(
            "displayName"
        )

        if not isinstance(display_name, str):
            authored_page_names.append(
                "<missing displayName>"
            )
        else:
            authored_page_names.append(
                display_name
            )

        page_id = parts[3]

        if (
            reusable_blank_page_id is not None
            and page_id
            == reusable_blank_page_id
        ):
            if operation.operation != "update":
                errors.append(
                    "The reusable blank page must be "
                    "modified with an update operation."
                )
            else:
                reused_blank_page = True

    if Counter(authored_page_names) != Counter(
        expected_page_names
    ):
        errors.append(
            "Authored page display names must match "
            "ReportPlan page names exactly. "
            f"Expected {expected_page_names!r}, "
            f"got {authored_page_names!r}."
        )

    if (
        reusable_blank_page_id is not None
        and not reused_blank_page
    ):
        errors.append(
            "The first ReportPlan page must reuse the "
            f"verified blank page "
            f"'{reusable_blank_page_id}'."
        )

    return errors