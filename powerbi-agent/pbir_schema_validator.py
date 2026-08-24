import json
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.exceptions import (
    NoSuchResource,
    Unresolvable,
)

from pbir_change_models import PBIRChangeSet


ALLOWED_SCHEMA_HOST = "developer.microsoft.com"
ALLOWED_SCHEMA_PATH_PREFIX = (
    "/json-schemas/fabric/"
)


def validate_pbir_change_set_schemas(
    change_set: PBIRChangeSet,
) -> tuple[list[str], list[str]]:
    """
    Validate PBIR JSON documents against their declared schemas.

    Returns:
        A tuple containing:
        - validation errors;
        - schemas that could not be validated because they were unavailable.
    """
    errors: list[str] = []
    unavailable_schemas: list[str] = []

    registry = Registry(
        retrieve=_retrieve_schema_resource
    )

    for operation in change_set.operations:
        schema_uri = operation.content.get(
            "$schema"
        )

        if not isinstance(schema_uri, str):
            errors.append(
                f"Missing or invalid $schema in "
                f"'{operation.path}'."
            )
            continue

        if not _is_allowed_schema_uri(
            schema_uri
        ):
            errors.append(
                f"Unsupported schema URI in "
                f"'{operation.path}': "
                f"'{schema_uri}'."
            )
            continue

        try:
            root_resource = (
                _retrieve_schema_resource(
                    schema_uri
                )
            )

            operation_registry = (
                registry.with_resource(
                    schema_uri,
                    root_resource,
                )
            )

            validator = Draft7Validator(
                root_resource.contents,
                registry=operation_registry,
            )

            validation_errors = sorted(
                validator.iter_errors(
                    operation.content
                ),
                key=lambda error: list(
                    error.absolute_path
                ),
            )

        except HTTPError as error:
            if error.code == 404:
                unavailable_schemas.append(
                    f"{operation.path}: "
                    f"schema is not published or reachable: "
                    f"{schema_uri}"
                )
            else:
                errors.append(
                    f"Could not load PBIR schema for "
                    f"'{operation.path}': {error}"
                )

            continue

        except (
            URLError,
            OSError,
            NoSuchResource,
            Unresolvable,
        ) as error:
            unavailable_schemas.append(
                f"{operation.path}: "
                f"schema could not be resolved: {error}"
            )
            continue

        for validation_error in validation_errors:
            json_path = _format_json_path(
                validation_error.absolute_path
            )

            errors.append(
                f"{operation.path} at "
                f"{json_path}: "
                f"{validation_error.message}"
            )

    return errors, unavailable_schemas


@lru_cache(maxsize=128)
def _retrieve_schema_resource(
    uri: str,
) -> Resource:
    """Download and cache an allowed Microsoft PBIR schema."""
    if not _is_allowed_schema_uri(uri):
        raise NoSuchResource(
            ref=uri
        )

    with urlopen(
        uri,
        timeout=15,
    ) as response:
        schema = json.load(
            response
        )

    if not isinstance(schema, dict):
        raise ValueError(
            f"Schema must be a JSON object: {uri}"
        )

    return Resource.from_contents(
        schema
    )


def _is_allowed_schema_uri(
    uri: str,
) -> bool:
    """Allow schema retrieval only from the Microsoft PBIR schema area."""
    parsed_uri = urlsplit(
        uri
    )

    return (
        parsed_uri.scheme == "https"
        and parsed_uri.hostname
        == ALLOWED_SCHEMA_HOST
        and parsed_uri.path.startswith(
            ALLOWED_SCHEMA_PATH_PREFIX
        )
    )


def _format_json_path(
    path,
) -> str:
    """Format a jsonschema error path for readable output."""
    result = "$"

    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"

    return result