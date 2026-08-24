from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any

from pbir_change_models import (
    PBIRChangeSet,
)


def validate_pbir_visual_layout(
    change_set: PBIRChangeSet,
) -> list[str]:
    errors: list[str] = []

    visuals_by_page: dict[
        str,
        list[tuple[str, dict[str, float]]],
    ] = defaultdict(list)

    for operation in change_set.operations:
        path = PurePosixPath(
            operation.path.replace("\\", "/")
        )

        parts = path.parts

        if (
            len(parts) != 7
            or parts[:3] != (
                "Report",
                "definition",
                "pages",
            )
            or parts[4] != "visuals"
            or parts[-1] != "visual.json"
        ):
            continue

        position = operation.content.get(
            "position"
        )

        if not isinstance(
            position,
            dict,
        ):
            continue

        rectangle = _read_rectangle(
            position
        )

        if rectangle is None:
            continue

        page_id = parts[3]
        visual_id = parts[5]

        visuals_by_page[
            page_id
        ].append(
            (
                visual_id,
                rectangle,
            )
        )

    for (
        page_id,
        visuals,
    ) in visuals_by_page.items():
        for index, (
            first_id,
            first_rectangle,
        ) in enumerate(visuals):
            for (
                second_id,
                second_rectangle,
            ) in visuals[
                index + 1:
            ]:
                if _rectangles_overlap(
                    first_rectangle,
                    second_rectangle,
                ):
                    errors.append(
                        "Visuals overlap on page "
                        f"'{page_id}': "
                        f"'{first_id}' and "
                        f"'{second_id}'."
                    )

    return errors


def _read_rectangle(
    position: dict[str, Any],
) -> dict[str, float] | None:
    required_names = (
        "x",
        "y",
        "width",
        "height",
    )

    values: dict[str, float] = {}

    for name in required_names:
        value = position.get(
            name
        )

        if not isinstance(
            value,
            (int, float),
        ):
            return None

        values[name] = float(
            value
        )

    if (
        values["width"] <= 0
        or values["height"] <= 0
    ):
        return None

    return values


def _rectangles_overlap(
    first: dict[str, float],
    second: dict[str, float],
) -> bool:
    first_right = (
        first["x"]
        + first["width"]
    )
    first_bottom = (
        first["y"]
        + first["height"]
    )

    second_right = (
        second["x"]
        + second["width"]
    )
    second_bottom = (
        second["y"]
        + second["height"]
    )

    return (
        first["x"] < second_right
        and first_right > second["x"]
        and first["y"] < second_bottom
        and first_bottom > second["y"]
    )