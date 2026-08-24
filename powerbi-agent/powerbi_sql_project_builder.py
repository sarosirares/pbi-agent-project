import shutil
from dataclasses import dataclass
from pathlib import Path

from database_query_models import DatabaseQueryPlan
from database_schema_context import DatabaseSchemaContext
from semantic_model_sql_table import (
    SemanticModelSqlTableSpec,
    build_semantic_model_sql_table_spec,
    clear_semantic_model_local_cache,
    write_sql_backed_semantic_table,
)


@dataclass(frozen=True)
class PowerBISqlProjectBuildResult:
    project_path: Path
    report_path: Path
    semantic_model_path: Path
    pbip_path: Path
    semantic_table: SemanticModelSqlTableSpec


def build_powerbi_sql_project(
    template_path: str | Path,
    output_path: str | Path,
    plan: DatabaseQueryPlan,
    schema_context: DatabaseSchemaContext,
    server: str,
    database: str,
    semantic_table_name: str | None = None,
) -> PowerBISqlProjectBuildResult:
    template_folder = Path(
        template_path
    ).resolve()

    output_folder = Path(
        output_path
    ).resolve()

    if not template_folder.is_dir():
        raise FileNotFoundError(
            "Power BI template not found: "
            f"{template_folder}"
        )

    if output_folder == template_folder:
        raise ValueError(
            "Output path must be different "
            "from the template path."
        )

    resolved_semantic_table_name = (
        semantic_table_name
        or plan.semantic_table_name
    )

    if not resolved_semantic_table_name:
        raise ValueError(
            "Database query plan contains no "
            "semantic table name."
        )

    semantic_table = (
        build_semantic_model_sql_table_spec(
            plan=plan,
            schema_context=schema_context,
            table_name=(
                resolved_semantic_table_name
            ),
        )
    )

    if output_folder.exists():
        shutil.rmtree(
            output_folder
        )

    output_folder.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copytree(
        template_folder,
        output_folder,
    )

    report_folder = _find_single_folder(
        project_path=output_folder,
        suffix=".Report",
    )

    semantic_model_folder = _find_single_folder(
        project_path=output_folder,
        suffix=".SemanticModel",
    )

    pbip_file = _find_single_pbip(
        output_folder
    )

    write_sql_backed_semantic_table(
        semantic_model_path=semantic_model_folder,
        spec=semantic_table,
        server=server,
        database=database,
    )

    clear_semantic_model_local_cache(
        semantic_model_folder
    )

    return PowerBISqlProjectBuildResult(
        project_path=output_folder,
        report_path=report_folder,
        semantic_model_path=semantic_model_folder,
        pbip_path=pbip_file,
        semantic_table=semantic_table,
    )


def _find_single_folder(
    project_path: Path,
    suffix: str,
) -> Path:
    folders = [
        child
        for child in project_path.iterdir()
        if (
            child.is_dir()
            and child.name.endswith(suffix)
        )
    ]

    if len(folders) != 1:
        raise RuntimeError(
            f"Expected exactly one '{suffix}' folder, "
            f"found {len(folders)}."
        )

    return folders[0]


def _find_single_pbip(
    project_path: Path,
) -> Path:
    pbip_files = list(
        project_path.glob("*.pbip")
    )

    if len(pbip_files) != 1:
        raise RuntimeError(
            "Expected exactly one .pbip file, "
            f"found {len(pbip_files)}."
        )

    return pbip_files[0]