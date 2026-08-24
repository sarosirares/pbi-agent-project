from pydantic import BaseModel, ConfigDict

from database_query_answerer import DatabaseQueryAnswerer
from database_query_executor import (
    DatabaseQueryResult,
    execute_database_query,
)
from database_query_models import DatabaseQueryPlan
from database_query_planner import DatabaseQueryPlanner
from database_question_context import (
    build_database_question_context,
)
from database_schema_context import DatabaseSchemaContext
from database_schema_loader import (
    load_database_schema_context,
)
from database_schema_selector import DatabaseSchemaSelector
from llm_client import VLLMClient


class DatabaseQueryPlanningResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: DatabaseQueryPlan
    schema_context: DatabaseSchemaContext


class DatabaseQueryServiceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: DatabaseQueryPlan
    result: DatabaseQueryResult


class DatabaseQueryService:
    def __init__(
        self,
        llm: VLLMClient | None = None,
        selector: DatabaseSchemaSelector | None = None,
        planner: DatabaseQueryPlanner | None = None,
        answerer: DatabaseQueryAnswerer | None = None,
    ) -> None:
        shared_llm = llm or VLLMClient()

        self.selector = (
            selector
            or DatabaseSchemaSelector(
                llm=shared_llm
            )
        )

        self.planner = (
            planner
            or DatabaseQueryPlanner(
                llm=shared_llm
            )
        )

        self.answerer = (
            answerer
            or DatabaseQueryAnswerer(
                llm=shared_llm
            )
        )

    def plan(
        self,
        question: str,
    ) -> DatabaseQueryPlanningResult:
        clean_question = question.strip()

        if not clean_question:
            raise ValueError(
                "Question must not be empty."
            )

        schema_context = (
            load_database_schema_context()
        )

        selection = self.selector.select(
            question=clean_question,
            schema_context=schema_context,
        )

        if selection.mode != "tables":
            raise ValueError(
                "Database data query requires "
                "table selection mode."
            )

        question_context = (
            build_database_question_context(
                schema_context=schema_context,
                selection=selection,
            )
        )

        plan = self.planner.plan(
            question=clean_question,
            question_context=question_context,
            schema_context=schema_context,
        )

        return DatabaseQueryPlanningResult(
            plan=plan,
            schema_context=schema_context,
        )

    def execute(
        self,
        question: str,
    ) -> DatabaseQueryServiceResult:
        planning = self.plan(
            question
        )

        result = execute_database_query(
            plan=planning.plan,
            schema_context=planning.schema_context,
        )

        return DatabaseQueryServiceResult(
            plan=planning.plan,
            result=result,
        )

    def answer(
        self,
        question: str,
    ) -> str:
        execution = self.execute(
            question
        )

        return self.answerer.answer(
            question=question,
            plan=execution.plan,
            result=execution.result,
        )