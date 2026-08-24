from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PBIRChangeOperationType = Literal[
    "create",
    "update",
]


class PBIRFileChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: PBIRChangeOperationType
    path: str = Field(min_length=1)
    content: dict[str, Any]


class PBIRChangeSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1000)
    operations: list[PBIRFileChange] = Field(min_length=1)