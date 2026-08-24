import json
from pathlib import Path
from typing import Any

from report_plan import ReportPlan


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_EXAMPLES_DIR = BASE_DIR / "pbir_examples"


def discover_pbir_examples(
    examples_dir: str | Path = DEFAULT_EXAMPLES_DIR,
) -> dict[str, Path]:
    """Discover available PBIR visual examples."""
    root = Path(examples_dir)

    if not root.is_dir():
        raise FileNotFoundError(
            f"PBIR examples directory not found: {root}"
        )

    examples: dict[str, Path] = {}

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue

        visual_file = child / "visual.json"

        if visual_file.is_file():
            examples[child.name] = visual_file

    return examples


def load_relevant_pbir_examples(
    plan: ReportPlan,
    examples_dir: str | Path = DEFAULT_EXAMPLES_DIR,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load only PBIR examples relevant to a report plan."""
    catalog = discover_pbir_examples(
        examples_dir
    )

    requested_types = {
        visual.type
        for page in plan.pages
        for visual in page.visuals
    }

    examples: dict[str, dict[str, Any]] = {}
    missing_types: list[str] = []

    for visual_type in sorted(requested_types):
        example_path = catalog.get(
            visual_type
        )

        if example_path is None:
            missing_types.append(
                visual_type
            )
            continue

        with example_path.open(
            "r",
            encoding="utf-8-sig",
        ) as file:
            content = json.load(file)

        if not isinstance(content, dict):
            raise ValueError(
                f"PBIR example must contain a JSON object: "
                f"{example_path}"
            )

        examples[visual_type] = content

    return examples, missing_types