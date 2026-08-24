from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


FieldKind = Literal[
    "column",
    "measure",
]

AggregationType = Literal[
    "sum",
    "average",
    "count",
    "distinct_count",
    "min",
    "max",
]


class SemanticFieldReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: FieldKind
    aggregation: AggregationType | None = None


class VisualBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=1, max_length=100)
    field: SemanticFieldReference


class VisualPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    purpose: str = Field(min_length=1, max_length=500)
    bindings: list[VisualBinding] = Field(min_length=1)


class PagePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    purpose: str = Field(min_length=1, max_length=500)
    visuals: list[VisualPlan] = Field(min_length=1)


class ReportPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=1000)
    pages: list[PagePlan] = Field(min_length=1)