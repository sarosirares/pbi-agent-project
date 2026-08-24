import json
from typing import Any

from llm_client import VLLMClient
from pbir_example_catalog import (
    discover_pbir_examples,
)
from report_plan import ReportPlan
from semantic_model_context import SemanticModelContext


REPORT_PLANNING_PROMPT = """
You are planning a Power BI report.

Your job is to transform the user's request into a semantic report plan.

Rules:
- Use only tables, columns, and measures that exist in the provided semantic model context.
- Do not invent tables, columns, or measures.
- Do not generate PBIR, TMDL, DAX, JSON schemas, file paths, or internal Power BI IDs.
- Use only visual types listed in SUPPORTED VISUAL TYPES.
- The visual type must exactly match one of the supplied strings.
- Do not invent aliases, synonyms, or alternative names for visual types.
- Prefer the smallest report structure that fully satisfies the user's request.
- Do not add extra pages or visuals unless they are necessary to satisfy the user's request.
- A visual can have any semantic bindings that are useful for that visual.
- Do not use "filter" as a visual binding role.
- Request-level data filters are already applied to the data used by the
  semantic model and must not be recreated as PBIR visual filters.
- Each binding must have a short semantic role such as:
  value, category, axis, legend, tooltip, rows, columns, or another appropriate role.
- For a column that needs aggregation, use one of:
  sum, average, count, distinct_count, min, max.
- If a column should not be aggregated, use null.
- For an existing measure, use kind="measure" and aggregation=null.
- Explain the purpose of every page and visual briefly.
- Give every page a concise, descriptive name based on its actual content.
- Do not use generic page names such as "Page 1", "Pagina 1", "New Page", or similar placeholder names unless the user explicitly requested that exact name.
- If the user explicitly provides a report title, page name, or visual title, preserve that text exactly, including spacing and capitalization. Do not rewrite, translate, prettify, or normalize an explicitly requested name.
- Return only one valid JSON object.
- Do not add Markdown fences or explanations outside the JSON.

The JSON must have this structure:

{
  "title": "...",
  "summary": "...",
  "pages": [
    {
      "name": "...",
      "purpose": "...",
      "visuals": [
        {
          "type": "...",
          "title": "...",
          "purpose": "...",
          "bindings": [
            {
              "role": "...",
              "field": {
                "table": "...",
                "name": "...",
                "kind": "column or measure",
                "aggregation": "sum, average, count, distinct_count, min, max, or null"
              }
            }
          ]
        }
      ]
    }
  ]
}
"""

REPORT_PLAN_REPAIR_PROMPT = """
You repair an invalid semantic Power BI report plan.

You receive:
- the original user request;
- the semantic model context;
- the supported visual types;
- the complete invalid ReportPlan;
- deterministic validation errors produced by Python.

Rules:
- Treat the supplied validation errors as authoritative.
- Fix every supplied validation error.
- Preserve the user's original report intent.
- Preserve valid pages, visuals, fields, titles, and bindings unless they
  must change to fix a validation error.
- Do not remove requested report content merely to avoid an error.
- Use only tables, columns, and measures from the supplied semantic model.
- Use only visual types from SUPPORTED VISUAL TYPES.
- Do not generate PBIR, TMDL, DAX, file paths, IDs, or implementation details.
- Return the COMPLETE corrected ReportPlan.
- Return only one valid JSON object.
- Do not add Markdown fences or explanations outside the JSON.
"""


class ReportPlanner:
    def __init__(
        self,
        llm: VLLMClient | None = None,
    ) -> None:
        self.llm = llm or VLLMClient()

    def create_plan(
    self,
    message: str,
    semantic_context: SemanticModelContext,
    ) -> ReportPlan:
        """Create a semantic report plan from a user request."""
        clean_message = message.strip()

        if not clean_message:
            raise ValueError(
                "The report request cannot be empty."
            )

        semantic_context_json = (
            semantic_context.model_dump_json(
                indent=2
            )
        )

        visual_catalog = (
            discover_pbir_examples()
        )

        supported_visual_types = sorted(
            visual_catalog.keys()
        )

        if not supported_visual_types:
            raise RuntimeError(
                "No validated PBIR visual examples "
                "are available."
            )

        supported_visual_types_json = (
            json.dumps(
                supported_visual_types,
                ensure_ascii=False,
            )
        )

        messages = [
            {
                "role": "system",
                "content": REPORT_PLANNING_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "SUPPORTED VISUAL TYPES:\n"
                    f"{supported_visual_types_json}\n\n"
                    "SEMANTIC MODEL CONTEXT:\n"
                    f"{semantic_context_json}\n\n"
                    "USER REQUEST:\n"
                    f"{clean_message}"
                ),
            },
        ]

        response = self.llm.chat(
            messages=messages,
            max_tokens=1500,
            temperature=0.0,
            enable_thinking=False,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned no report plan."
            )

        parsed_plan = self._parse_json(
            content
        )

        return ReportPlan.model_validate(
            parsed_plan
        )

    def repair_plan(
        self,
        message: str,
        semantic_context: SemanticModelContext,
        invalid_plan: ReportPlan,
        validation_errors: list[str],
    ) -> ReportPlan:
        """Repair a semantically invalid report plan."""
        clean_message = message.strip()

        if not clean_message:
            raise ValueError(
                "The report request cannot be empty."
            )

        if not validation_errors:
            raise ValueError(
                "validation_errors must not be empty."
            )

        visual_catalog = (
            discover_pbir_examples()
        )

        supported_visual_types = sorted(
            visual_catalog.keys()
        )

        if not supported_visual_types:
            raise RuntimeError(
                "No validated PBIR visual examples "
                "are available."
            )

        semantic_context_json = (
            semantic_context.model_dump_json(
                indent=2
            )
        )

        invalid_plan_json = json.dumps(
            invalid_plan.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        validation_errors_json = json.dumps(
            validation_errors,
            ensure_ascii=False,
            indent=2,
        )

        supported_visual_types_json = (
            json.dumps(
                supported_visual_types,
                ensure_ascii=False,
            )
        )

        messages = [
            {
                "role": "system",
                "content": (
                    REPORT_PLANNING_PROMPT
                    + "\n\n"
                    + REPORT_PLAN_REPAIR_PROMPT
                ),
            },
            {
                "role": "user",
                "content": (
                    "SUPPORTED VISUAL TYPES:\n"
                    f"{supported_visual_types_json}\n\n"
                    "SEMANTIC MODEL CONTEXT:\n"
                    f"{semantic_context_json}\n\n"
                    "ORIGINAL USER REQUEST:\n"
                    f"{clean_message}\n\n"
                    "INVALID REPORT PLAN:\n"
                    f"{invalid_plan_json}\n\n"
                    "VALIDATION ERRORS:\n"
                    f"{validation_errors_json}"
                ),
            },
        ]

        response = self.llm.chat(
            messages=messages,
            max_tokens=1500,
            temperature=0.0,
            enable_thinking=False,
        )

        content = response.choices[
            0
        ].message.content

        if not content:
            raise RuntimeError(
                "The model returned no repaired "
                "report plan."
            )

        parsed_plan = self._parse_json(
            content
        )

        return ReportPlan.model_validate(
            parsed_plan
        )

    @staticmethod
    def _parse_json(
        content: str,
    ) -> dict[str, Any]:
        clean_content = content.strip()

        if clean_content.startswith("```"):
            lines = clean_content.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            clean_content = "\n".join(lines).strip()

        return json.loads(clean_content)