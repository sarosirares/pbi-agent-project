from dataclasses import dataclass
from typing import Any

from pbir_author import PBIRAuthor
from pbir_change_models import PBIRChangeSet
from pbir_change_validator import (
    validate_pbir_change_set_security,
)
from pbir_layout_validator import (
    validate_pbir_visual_layout,
)
from pbir_project_context import (
    PBIRProjectContext,
)
from pbir_plan_validator import (
    validate_pbir_change_set_plan,
)
from pbir_schema_validator import (
    validate_pbir_change_set_schemas,
)
from pbir_structure_validator import (
    validate_pbir_change_set_structure,
)
from report_plan import ReportPlan

@dataclass(frozen=True)
class PBIRAuthoringResult:
    change_set: PBIRChangeSet
    unavailable_schemas: list[str]
    repair_count: int


def generate_validated_pbir_change_set(
    authoring_context: dict[str, Any],
    project_context: PBIRProjectContext,
    author: PBIRAuthor | None = None,
    max_repairs: int = 1,
) -> PBIRAuthoringResult:
    """Generate, validate, and optionally repair a PBIR change set."""
    if max_repairs < 0:
        raise ValueError(
            "max_repairs must be greater than or equal to 0."
        )

    pbir_author = author or PBIRAuthor()

    change_set = pbir_author.create_change_set(
        authoring_context
    )

    repair_count = 0

    while True:
        (
            validation_errors,
            unavailable_schemas,
        ) = _validate_change_set(
            change_set=change_set,
            project_context=project_context,
            authoring_context=authoring_context,
        )

        if not validation_errors:
            return PBIRAuthoringResult(
                change_set=change_set,
                unavailable_schemas=unavailable_schemas,
                repair_count=repair_count,
            )

        if repair_count >= max_repairs:
            formatted_errors = "\n".join(
                f"- {error}"
                for error in validation_errors
            )

            raise RuntimeError(
                "PBIR change set remained invalid after "
                f"{repair_count} repair attempt(s):\n"
                f"{formatted_errors}"
            )

        change_set = pbir_author.repair_change_set(
            authoring_context=authoring_context,
            invalid_change_set=change_set,
            validation_errors=validation_errors,
        )

        repair_count += 1


def _validate_change_set(
    change_set: PBIRChangeSet,
    project_context: PBIRProjectContext,
    authoring_context: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Run deterministic validators for a proposed PBIR change set."""
    validation_errors: list[str] = []

    security_errors = (
        validate_pbir_change_set_security(
            change_set
        )
    )

    validation_errors.extend(
        f"Security validation: {error}"
        for error in security_errors
    )

    plan = ReportPlan.model_validate(
        authoring_context["report_plan"]
    )

    reusable_blank_page = (
        authoring_context.get(
            "reusable_blank_page"
        )
    )

    reusable_blank_page_id = None

    if isinstance(
        reusable_blank_page,
        dict,
    ):
        page_id = reusable_blank_page.get(
            "page_id"
        )

        if isinstance(page_id, str):
            reusable_blank_page_id = page_id

    plan_errors = (
        validate_pbir_change_set_plan(
            change_set=change_set,
            plan=plan,
            reusable_blank_page_id=(
                reusable_blank_page_id
            ),
        )
    )

    validation_errors.extend(
        f"Plan validation: {error}"
        for error in plan_errors
    )

    layout_errors = (
        validate_pbir_visual_layout(
            change_set
        )
    )

    validation_errors.extend(
        f"Layout validation: {error}"
        for error in layout_errors
    )

    structure_errors = (
        validate_pbir_change_set_structure(
            change_set=change_set,
            project_context=project_context,
        )
    )

    validation_errors.extend(
        f"Structure validation: {error}"
        for error in structure_errors
    )

    (
        schema_errors,
        unavailable_schemas,
    ) = validate_pbir_change_set_schemas(
        change_set
    )

    validation_errors.extend(
        f"Schema validation: {error}"
        for error in schema_errors
    )

    return (
        validation_errors,
        unavailable_schemas,
    )