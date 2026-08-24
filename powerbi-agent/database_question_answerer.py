import json

from database_question_context import DatabaseQuestionContext
from llm_client import VLLMClient


DATABASE_QUESTION_PROMPT = """
You answer questions about a SQL Server database schema.

You receive:
- the user's question;
- a database schema context produced by trusted Python code.

The context contains metadata only. It does not contain table row data.

Rules:
- Answer only from the supplied database schema context.
- Never invent tables, columns, keys, relationships, or data values.
- Do not claim that a relationship exists unless it is explicitly present
  in the supplied metadata.
- Do not infer the contents of table rows from table or column names.
- If the supplied metadata is insufficient to answer the question, say so
  clearly.
- Distinguish between primary keys, unique constraints, and foreign keys.
- A table name or column name may suggest a purpose, but this is not proof
  of the actual data stored there.
- Do not generate or execute SQL.
- Do not claim that you inspected table data.
- Answer in the same language as the user's question.
- Be concise but sufficiently specific.
"""


class DatabaseQuestionAnswerer:
    def __init__(
        self,
        llm: VLLMClient | None = None,
    ) -> None:
        self.llm = llm or VLLMClient()

    def answer(
        self,
        question: str,
        question_context: DatabaseQuestionContext,
    ) -> str:
        clean_question = question.strip()

        if not clean_question:
            raise ValueError("Question must not be empty.")

        context_json = json.dumps(
            question_context.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        response = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": DATABASE_QUESTION_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"QUESTION:\n{clean_question}\n\n"
                        f"DATABASE SCHEMA CONTEXT:\n"
                        f"{context_json}"
                    ),
                },
            ],
            max_tokens=2048,
            temperature=0.0,
            enable_thinking=False,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned no database question answer."
            )

        return content.strip()