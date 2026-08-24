from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DatabaseQueryTableReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_name: str = Field(min_length=1)
    table_name: str = Field(min_length=1)


class DatabaseQueryColumnReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_name: str = Field(min_length=1)
    table_name: str = Field(min_length=1)
    column_name: str = Field(min_length=1)


class DatabaseQueryJoin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    join_type: Literal["inner"]
    left_column: DatabaseQueryColumnReference
    right_column: DatabaseQueryColumnReference


class DatabaseQueryFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: DatabaseQueryColumnReference
    operator: Literal[
        "eq",
        "ne",
        "gt",
        "gte",
        "lt",
        "lte",
        "in",
        "contains",
        "starts_with",
        "ends_with",
        "is_null",
        "is_not_null",
    ]
    value: (
        str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | None
    ) = None


class DatabaseQueryAggregation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    function: Literal[
        "count",
        "count_distinct",
        "sum",
        "avg",
        "min",
        "max",
    ]
    column: DatabaseQueryColumnReference | None = None
    output_name: str = Field(min_length=1)
    condition: DatabaseQueryFilter | None = None


class DatabaseQueryDerivedMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["ratio"]
    numerator: str = Field(min_length=1)
    denominator: str = Field(min_length=1)
    scale: float = Field(default=1.0, gt=0)
    output_name: str = Field(min_length=1)


class DatabaseQuerySort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: DatabaseQueryColumnReference
    direction: Literal["asc", "desc"]


class DatabaseQueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["select"]

    semantic_table_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
    )

    tables: list[DatabaseQueryTableReference] = Field(
        min_length=1,
        max_length=8,
    )

    joins: list[DatabaseQueryJoin] = Field(
        default_factory=list,
        max_length=7,
    )

    columns: list[DatabaseQueryColumnReference] = Field(
        default_factory=list,
    )

    aggregations: list[DatabaseQueryAggregation] = Field(
        default_factory=list,
    )

    derived_metrics: list[DatabaseQueryDerivedMetric] = Field(
        default_factory=list,
    )

    group_by: list[DatabaseQueryColumnReference] = Field(
        default_factory=list,
    )

    filters: list[DatabaseQueryFilter] = Field(
        default_factory=list,
    )

    sort: list[DatabaseQuerySort] = Field(
        default_factory=list,
    )

    limit: int | None = Field(
        default=100,
        ge=1,
        le=1000,
    )

    requires_join: bool