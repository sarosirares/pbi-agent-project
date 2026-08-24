import json

from database_query_models import DatabaseQueryPlan
from database_query_executor import DatabaseQueryResult
from llm_client import VLLMClient


DATABASE_QUERY_ANSWER_PROMPT = """
You answer the user's question using the supplied validated database
query plan and query result.

Rules:
- Use only information supported by the supplied plan and result.
- Use the plan only to understand the scope and meaning of the result.
- Never invent rows, values, columns, counts, or relationships.
- Do not claim that information exists if it is not present in the result.
- If the result contains no data rows, say so clearly.
- If the result is an aggregate such as COUNT, SUM, AVG, MIN, or MAX,
  report the returned aggregate value accurately.
- Answer the user's question directly.
- For a simple scalar result, prefer a short direct sentence containing
  the value instead of introducing the query execution process.
- Do not routinely use phrases such as "according to the executed query"
  or describe how the query was executed.
- Mention the scope or source of the result only when it is useful for
  answering accurately or avoiding an unsupported generalization.
- Do not generalize a result from one selected table into a claim about
  the entire database unless the plan and result justify that conclusion.
- Do not generate SQL.
- Do not describe internal implementation details unless the user asks.
- Answer in the same language as the user's question.
- Be concise and specific.
"""


class DatabaseQueryAnswerer:
    def __init__(
        self,
        llm: VLLMClient | None = None,
    ) -> None:
        self.llm = llm or VLLMClient()

    def answer(
        self,
        question: str,
        plan: DatabaseQueryPlan,
        result: DatabaseQueryResult,
    ) -> str:
        clean_question = question.strip()

        if not clean_question:
            raise ValueError(
                "Question must not be empty."
            )

        payload = {
            "plan": plan.model_dump(
                mode="json"
            ),
            "result": result.model_dump(
                mode="json"
            ),
        }

        payload_json = json.dumps(
            payload,
            ensure_ascii=False,
        )

        response = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": DATABASE_QUERY_ANSWER_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"QUESTION:\n{clean_question}\n\n"
                        f"VALIDATED QUERY RESULT:\n"
                        f"{payload_json}"
                    ),
                },
            ],
            max_tokens=1024,
            temperature=0.0,
            enable_thinking=False,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned no database query answer."
            )

        return content.strip()