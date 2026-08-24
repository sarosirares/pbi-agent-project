import json
from pathlib import Path

from pbir_change_models import PBIRChangeSet


def apply_pbir_change_set(
    change_set: PBIRChangeSet,
    report_path: str | Path,
) -> None:
    """Apply a validated PBIR change set to a report folder."""
    report_folder = Path(report_path).resolve()

    if not report_folder.is_dir():
        raise FileNotFoundError(
            f"Report folder not found: {report_folder}"
        )

    for operation in change_set.operations:
        target_path = _resolve_target_path(
            report_folder=report_folder,
            logical_path=operation.path,
        )

        if operation.operation == "create":
            if target_path.exists():
                raise FileExistsError(
                    f"Create target already exists: "
                    f"{target_path}"
                )

            target_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        elif operation.operation == "update":
            if not target_path.is_file():
                raise FileNotFoundError(
                    f"Update target does not exist: "
                    f"{target_path}"
                )

        with target_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            json.dump(
                operation.content,
                file,
                indent=2,
                ensure_ascii=False,
            )

            file.write("\n")


def _resolve_target_path(
    report_folder: Path,
    logical_path: str,
) -> Path:
    """Map a PBIR logical path to the physical report copy."""
    normalized_path = logical_path.replace(
        "\\",
        "/",
    )

    parts = Path(
        normalized_path
    ).parts

    if (
        not parts
        or parts[0] != "Report"
    ):
        raise ValueError(
            f"Invalid PBIR logical path: "
            f"'{logical_path}'."
        )

    relative_parts = parts[1:]

    target_path = (
        report_folder.joinpath(
            *relative_parts
        ).resolve()
    )

    try:
        target_path.relative_to(
            report_folder
        )
    except ValueError as error:
        raise ValueError(
            f"PBIR path escapes the report folder: "
            f"'{logical_path}'."
        ) from error

    return target_path