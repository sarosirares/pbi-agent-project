from pydantic import BaseModel, ConfigDict, Field


class SemanticColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    data_type: str | None = None
    default_summarization: str | None = None


class SemanticMeasure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)


class SemanticTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    columns: list[SemanticColumn] = Field(default_factory=list)
    measures: list[SemanticMeasure] = Field(default_factory=list)


class SemanticModelContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tables: list[SemanticTable] = Field(min_length=1)