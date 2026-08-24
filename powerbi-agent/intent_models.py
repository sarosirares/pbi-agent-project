from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


IntentType = Literal[
    "general_question",
    "project_question",
    "database_question",
    "database_query",
    "report_request",
    "report_follow_up",
    "unclear",
]


class IntentResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    intent: IntentType

    summary: str = Field(
        min_length=1,
        max_length=500,
    )

    resolved_message: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )

    requires_database_schema: bool
    requires_report_generation: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )