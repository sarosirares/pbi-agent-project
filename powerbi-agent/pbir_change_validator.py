from pathlib import PurePosixPath

from pbir_change_models import PBIRChangeSet


ALLOWED_ROOT = PurePosixPath("Report/definition")


def validate_pbir_change_set_security(
    change_set: PBIRChangeSet,
) -> list[str]:
    """Validate whether proposed PBIR file operations are safe."""
    errors: list[str] = []

    for operation in change_set.operations:
        raw_path = operation.path.strip()

        if not raw_path:
            errors.append(
                "Operation path cannot be empty."
            )
            continue

        normalized_path = PurePosixPath(
            raw_path.replace("\\", "/")
        )

        if normalized_path.is_absolute():
            errors.append(
                f"Absolute path is not allowed: "
                f"'{operation.path}'."
            )
            continue

        if ".." in normalized_path.parts:
            errors.append(
                f"Path traversal is not allowed: "
                f"'{operation.path}'."
            )
            continue

        try:
            normalized_path.relative_to(
                ALLOWED_ROOT
            )
        except ValueError:
            errors.append(
                f"Path is outside the allowed PBIR area: "
                f"'{operation.path}'."
            )
            continue

        if normalized_path.suffix.casefold() != ".json":
            errors.append(
                f"Only JSON files are allowed: "
                f"'{operation.path}'."
            )

    return errors