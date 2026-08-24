import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PBIRJsonFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    content: dict[str, Any]


class PBIRProjectContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[PBIRJsonFile] = Field(min_length=1)


def load_pbir_project_context(
    report_path: str | Path,
) -> PBIRProjectContext:
    """Load JSON files from a Power BI report definition."""
    report_folder = Path(report_path)

    definition_path = (
        report_folder
        / "definition"
    )

    if not definition_path.is_dir():
        raise FileNotFoundError(
            f"PBIR definition directory not found: "
            f"{definition_path}"
        )

    json_files = sorted(
        definition_path.rglob("*.json")
    )

    if not json_files:
        raise FileNotFoundError(
            f"No PBIR JSON files found in: "
            f"{definition_path}"
        )

    files: list[PBIRJsonFile] = []

    for json_file in json_files:
        with json_file.open(
            "r",
            encoding="utf-8-sig",
        ) as file:
            content = json.load(file)

        if not isinstance(content, dict):
            raise ValueError(
                f"PBIR file must contain a JSON object: "
                f"{json_file}"
            )

        relative_path = (
            json_file
            .relative_to(report_folder)
            .as_posix()
        )

        logical_path = (
            f"Report/{relative_path}"
        )

        files.append(
            PBIRJsonFile(
                path=logical_path,
                content=content,
            )
        )

    return PBIRProjectContext(
        files=files
    )