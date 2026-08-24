from pydantic import BaseModel, ConfigDict, Field


class DatabaseColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    ordinal_position: int = Field(ge=1)
    data_type: str = Field(min_length=1)
    max_length: int | None = None
    precision: int | None = None
    scale: int | None = None
    is_nullable: bool
    is_identity: bool


class DatabaseKey(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    columns: list[str]


class DatabaseForeignKeyColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: str = Field(min_length=1)
    referenced_column: str = Field(min_length=1)


class DatabaseForeignKey(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    referenced_schema: str = Field(min_length=1)
    referenced_table: str = Field(min_length=1)
    columns: list[DatabaseForeignKeyColumn]


class DatabaseTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_name: str = Field(min_length=1)
    name: str = Field(min_length=1)
    columns: list[DatabaseColumn]
    primary_key: DatabaseKey | None = None
    unique_constraints: list[DatabaseKey]
    foreign_keys: list[DatabaseForeignKey]


class DatabaseSchemaContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database_name: str = Field(min_length=1)
    tables: list[DatabaseTable]