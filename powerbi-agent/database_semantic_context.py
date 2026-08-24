from database_schema_context import DatabaseSchemaContext


ColumnKey = tuple[str, str, str]
DatabaseRelationship = tuple[ColumnKey, ColumnKey]


DEMO_RELATIONSHIPS: tuple[
    DatabaseRelationship,
    ...,
] = (
    (
        (
            "dbo",
            "StudentProgramGradebook",
            "StudentProgramId",
        ),
        (
            "dbo",
            "StudentProgram",
            "Id",
        ),
    ),
    (
        (
            "dbo",
            "StudentProgramGradebook",
            "EducationPlanStructureId",
        ),
        (
            "dbo",
            "EducationPlanStructure",
            "StructureId",
        ),
    ),
    (
        (
            "dbo",
            "EducationPlanStructure",
            "DisciplineId",
        ),
        (
            "dbo",
            "EducationPlanDiscipline",
            "DisciplineId",
        ),
    ),
    (
        (
            "dbo",
            "StudentProgram",
            "SpecializationId",
        ),
        (
            "dbo",
            "Unit",
            "UnitId",
        ),
    ),
    (
        (
            "dbo",
            "StudentProgram",
            "StudentId",
        ),
        (
            "dbo",
            "UniversityParticipant",
            "Id",
        ),
    ),
)


def get_allowed_database_relationships(
    schema_context: DatabaseSchemaContext,
) -> list[DatabaseRelationship]:
    available_columns = {
        (
            table.schema_name,
            table.name,
            column.name,
        )
        for table in schema_context.tables
        for column in table.columns
    }

    return [
        relationship
        for relationship in DEMO_RELATIONSHIPS
        if (
            relationship[0] in available_columns
            and relationship[1] in available_columns
        )
    ]


def build_database_semantic_context(
    schema_context: DatabaseSchemaContext,
) -> list[dict[str, object]]:
    available_columns = {
        (
            table.schema_name,
            table.name,
            column.name,
        )
        for table in schema_context.tables
        for column in table.columns
    }

    entries: list[dict[str, object]] = []

    grade_column = (
        "dbo",
        "StudentProgramGradebook",
        "ExamGrade",
    )

    if grade_column in available_columns:
        entries.append(
            {
                "scope": "demo",
                "concept": "student academic promotion",
                "terms": [
                    "promovare",
                    "promovat",
                    "nepromovat",
                    "rata de promovare",
                ],
                "source": {
                    "schema_name": "dbo",
                    "table_name": "StudentProgramGradebook",
                    "column_name": "ExamGrade",
                },
                "meaning": (
                    "For the current synthetic academic demo, "
                    "ExamGrade is treated as the final numeric grade."
                ),
                "rules": [
                    {
                        "meaning": "promoted",
                        "operator": "gte",
                        "value": 5,
                    },
                    {
                        "meaning": "not_promoted",
                        "operator": "lt",
                        "value": 5,
                    },
                ],
                "notes": [
                    (
                        "Final grade >= 5 as promoted is confirmed "
                        "business logic."
                    ),
                    (
                        "Using StudentProgramGradebook.ExamGrade as "
                        "the final grade is a demo assumption."
                    ),
                ],
            }
        )

    study_program_name = (
        "dbo",
        "Unit",
        "Name",
    )

    specialization_id = (
        "dbo",
        "StudentProgram",
        "SpecializationId",
    )

    if (
        study_program_name in available_columns
        and specialization_id in available_columns
    ):
        entries.append(
            {
                "scope": "demo",
                "concept": "study program",
                "terms": [
                    "program de studiu",
                    "program",
                    "specializare",
                ],
                "source": {
                    "schema_name": "dbo",
                    "table_name": "Unit",
                    "column_name": "Name",
                },
                "meaning": (
                    "For the current synthetic academic demo, "
                    "Unit.Name is used as the human-readable "
                    "study program name."
                ),
                "notes": [
                    (
                        "StudentProgram.SpecializationId is "
                        "treated as a technical identifier."
                    ),
                    (
                        "When a human-readable study program "
                        "label is requested, use Unit.Name."
                    ),
                    (
                        "The relationship from SpecializationId "
                        "to UnitId is a demo assumption."
                    ),
                ],
            }
        )

    relationships = get_allowed_database_relationships(
        schema_context
    )

    if relationships:
        entries.append(
            {
                "scope": "demo",
                "concept": "academic relationships",
                "status": "TEST_INFERRED_RELATION",
                "relationships": [
                    {
                        "left": {
                            "schema_name": left[0],
                            "table_name": left[1],
                            "column_name": left[2],
                        },
                        "right": {
                            "schema_name": right[0],
                            "table_name": right[1],
                            "column_name": right[2],
                        },
                    }
                    for left, right in relationships
                ],
                "notes": [
                    (
                        "These relationships are approved only for "
                        "the synthetic academic demo."
                    ),
                    (
                        "They must not be presented as confirmed "
                        "SQL Server foreign keys."
                    ),
                ],
            }
        )

    return entries