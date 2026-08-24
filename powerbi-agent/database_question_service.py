from database_question_answerer import DatabaseQuestionAnswerer
from database_question_context import (
    build_database_question_context,
)
from database_schema_loader import (
    load_database_schema_context,
)
from database_schema_selector import DatabaseSchemaSelector
from llm_client import VLLMClient


class DatabaseQuestionService:
    def __init__(
        self,
        llm: VLLMClient | None = None,
        selector: DatabaseSchemaSelector | None = None,
        answerer: DatabaseQuestionAnswerer | None = None,
    ) -> None:
        self.selector = (
            selector
            or DatabaseSchemaSelector(llm=llm)
        )
        self.answerer = (
            answerer
            or DatabaseQuestionAnswerer(llm=llm)
        )

    def answer(self, question: str) -> str:
        clean_question = question.strip()

        if not clean_question:
            raise ValueError("Question must not be empty.")

        schema_context = load_database_schema_context()

        selection = self.selector.select(
            question=clean_question,
            schema_context=schema_context,
        )

        question_context = build_database_question_context(
            schema_context=schema_context,
            selection=selection,
        )

        return self.answerer.answer(
            question=clean_question,
            question_context=question_context,
        )