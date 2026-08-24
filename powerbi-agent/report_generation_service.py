import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from llm_client import VLLMClient
from pbir_author import PBIRAuthor
from pbir_authoring_context import (
    build_pbir_authoring_context,
)
from pbir_authoring_orchestrator import (
    generate_validated_pbir_change_set,
)
from pbir_change_applier import (
    apply_pbir_change_set,
)
from pbir_change_models import PBIRChangeSet
from pbir_project_context import (
    load_pbir_project_context,
)
from report_plan import ReportPlan
from report_planner import ReportPlanner
from semantic_model_loader import (
    load_semantic_model_context,
)
from semantic_model_validator import (
    validate_report_plan_semantics,
)


@dataclass(frozen=True)
class ReportGenerationResult:
    plan: ReportPlan
    change_set: PBIRChangeSet
    project_path: Path
    report_path: Path
    pbip_path: Path
    zip_path: Path
    repair_count: int
    unavailable_schemas: list[str]
    cli_exit_code: int
    cli_stdout: str
    cli_stderr: str


def generate_powerbi_project(
    user_request: str,
    semantic_model_path: str | Path,
    report_path: str | Path,
    output_root: str | Path,
    llm: VLLMClient | None = None,
    max_repairs: int = 1,
) -> ReportGenerationResult:
    """Generate a validated Power BI project copy from a user request."""
    clean_request = user_request.strip()

    if not clean_request:
        raise ValueError(
            "The report request cannot be empty."
        )

    semantic_model_folder = Path(
        semantic_model_path
    ).resolve()

    report_folder = Path(
        report_path
    ).resolve()

    output_folder = Path(
        output_root
    ).resolve()

    if not semantic_model_folder.is_dir():
        raise FileNotFoundError(
            "Semantic model folder not found: "
            f"{semantic_model_folder}"
        )

    if not report_folder.is_dir():
        raise FileNotFoundError(
            f"Report folder not found: {report_folder}"
        )

    if max_repairs < 0:
        raise ValueError(
            "max_repairs must be greater than or equal to 0."
        )

    project_root = report_folder.parent

    try:
        output_folder.relative_to(
            project_root
        )
    except ValueError:
        pass
    else:
        raise ValueError(
            "output_root must not be inside the source "
            "Power BI project folder."
        )

    cli_path = shutil.which(
        "powerbi-report-author"
    )

    if cli_path is None:
        raise RuntimeError(
            "powerbi-report-author CLI was not found."
        )

    semantic_context = load_semantic_model_context(
        semantic_model_folder
    )

    project_context = load_pbir_project_context(
        report_folder
    )

    shared_llm = llm or VLLMClient()

    planner = ReportPlanner(
        llm=shared_llm
    )

    plan = planner.create_plan(
        message=clean_request,
        semantic_context=semantic_context,
    )

    semantic_errors = validate_report_plan_semantics(
        plan,
        semantic_context,
    )

    if semantic_errors:
        plan = planner.repair_plan(
            message=clean_request,
            semantic_context=semantic_context,
            invalid_plan=plan,
            validation_errors=semantic_errors,
        )

        semantic_errors = (
            validate_report_plan_semantics(
                plan,
                semantic_context,
            )
        )

    if semantic_errors:
        formatted_errors = "\n".join(
            f"- {error}"
            for error in semantic_errors
        )

        raise RuntimeError(
            "Report plan failed semantic validation "
            "after one repair attempt:\n"
            f"{formatted_errors}"
        )

    authoring_context = build_pbir_authoring_context(
        plan=plan,
        semantic_context=semantic_context,
        project_context=project_context,
    )

    author = PBIRAuthor(
        llm=shared_llm
    )

    authoring_result = (
        generate_validated_pbir_change_set(
            authoring_context=authoring_context,
            project_context=project_context,
            author=author,
            max_repairs=max_repairs,
        )
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    project_copy = (
        output_folder
        / f"{project_root.name}_generated"
    )

    if project_copy.exists():
        shutil.rmtree(
            project_copy
        )

    shutil.copytree(
        project_root,
        project_copy,
    )

    report_copy = (
        project_copy
        / report_folder.name
    )

    apply_pbir_change_set(
        change_set=authoring_result.change_set,
        report_path=report_copy,
    )

    validation_result = subprocess.run(
        [
            cli_path,
            "validate",
            str(report_copy),
            "--pretty",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    pbip_files = list(
        project_copy.glob("*.pbip")
    )

    if len(pbip_files) != 1:
        raise RuntimeError(
            "Expected exactly one .pbip file "
            "in generated project, found "
            f"{len(pbip_files)}."
        )

    archive_base = (
        output_folder
        / project_copy.name
    )

    zip_path = Path(
        f"{archive_base}.zip"
    )

    if zip_path.exists():
        zip_path.unlink()

    created_archive = shutil.make_archive(
        base_name=str(archive_base),
        format="zip",
        root_dir=output_folder,
        base_dir=project_copy.name,
    )

    zip_path = Path(
        created_archive
    ).resolve()

    if not zip_path.is_file():
        raise RuntimeError(
            "Generated Power BI ZIP archive was not created."
        )

    return ReportGenerationResult(
        plan=plan,
        change_set=authoring_result.change_set,
        project_path=project_copy,
        report_path=report_copy,
        pbip_path=pbip_files[0],
        zip_path=zip_path,
        repair_count=authoring_result.repair_count,
        unavailable_schemas=(
            authoring_result.unavailable_schemas
        ),
        cli_exit_code=validation_result.returncode,
        cli_stdout=validation_result.stdout,
        cli_stderr=validation_result.stderr,
    )