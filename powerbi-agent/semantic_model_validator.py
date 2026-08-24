from report_plan import ReportPlan
from semantic_model_context import SemanticModelContext


def validate_report_plan_semantics(
    plan: ReportPlan,
    semantic_context: SemanticModelContext,
) -> list[str]:
    """Validate report field references against the semantic model."""
    errors: list[str] = []

    tables_by_name = {
        table.name.casefold(): table
        for table in semantic_context.tables
    }

    for page in plan.pages:
        for visual in page.visuals:
            for binding in visual.bindings:
                field = binding.field

                location = (
                    f"Page '{page.name}', "
                    f"visual '{visual.title}', "
                    f"binding '{binding.role}'"
                )

                if binding.role.casefold() == "filter":
                    errors.append(
                        f"{location}: visual binding role "
                        "'filter' is not supported. "
                        "Request-level data filters must "
                        "be applied in the database query plan."
                    )
                    continue

                table = tables_by_name.get(
                    field.table.casefold()
                )

                if table is None:
                    errors.append(
                        f"{location}: table "
                        f"'{field.table}' does not exist."
                    )
                    continue

                if field.kind == "column":
                    column_names = {
                        column.name.casefold()
                        for column in table.columns
                    }

                    if field.name.casefold() not in column_names:
                        errors.append(
                            f"{location}: column "
                            f"'{field.table}.{field.name}' "
                            f"does not exist."
                        )

                elif field.kind == "measure":
                    measure_names = {
                        measure.name.casefold()
                        for measure in table.measures
                    }

                    if field.name.casefold() not in measure_names:
                        errors.append(
                            f"{location}: measure "
                            f"'{field.table}.{field.name}' "
                            f"does not exist."
                        )

                    if field.aggregation is not None:
                        errors.append(
                            f"{location}: measure "
                            f"'{field.table}.{field.name}' "
                            "must not have an aggregation."
                        )

    return errors