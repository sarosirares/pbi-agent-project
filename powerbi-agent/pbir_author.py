import json
from typing import Any

from llm_client import VLLMClient
from pbir_change_models import PBIRChangeSet


PBIR_AUTHORING_PROMPT = """
You are authoring a Power BI report in PBIR format.

You receive:
- a validated semantic ReportPlan;
- the real semantic model context;
- valid PBIR examples for relevant visual types;
- relevant JSON files from the current Power BI report;
- an optional reusable_blank_page describing a verified empty page.

Your task is to produce a PBIRChangeSet for the supplied ReportPlan.

Page strategy:
- If reusable_blank_page is not null, reuse that page for the FIRST
  ReportPlan page.
- Reusing the blank page means:
  - use an "update" operation for its existing page.json;
  - preserve its existing internal page ID and "name" exactly;
  - set its displayName exactly to the first ReportPlan page name;
  - preserve its existing $schema, displayOption, width, height, and
    other valid page metadata unless a change is required;
  - create the first ReportPlan page visuals under that existing page ID;
  - do NOT create a replacement page for the first ReportPlan page.
- If the ReportPlan contains additional pages after the reused first
  page, create those additional pages normally.
- If reusable_blank_page is null, create new pages normally.
- Do not modify unrelated existing pages or visuals.

Rules:
- Every authored page displayName must exactly match the corresponding
  ReportPlan page name. Do not rewrite, translate, prettify, or normalize it.
- Do not modify the semantic model.
- Use only tables, columns, and measures from the provided semantic model.
- Follow the provided PBIR examples as structural references.
- Follow the provided PBIR file structure exactly.
- Do not invent PBIR properties or structures that are not demonstrated
  by the supplied valid examples or current report context.
- A page.json file must not contain visual definitions.
- Every visual must be created as a separate visual.json file under
  Report/definition/pages/<page_id>/visuals/<visual_id>/visual.json.
- Adapt the examples to the fields, aggregations, and purposes described
  by the ReportPlan.
- ReportPlan visual titles represent semantic intent only.
- Do not add a "title" property directly under the "visual" object.
- Only emit custom title configuration when the supplied valid PBIR
  examples explicitly demonstrate the correct PBIR structure for it.
- Do not reuse existing visual internal IDs.
- Do not reuse an existing page ID except for the page explicitly
  supplied as reusable_blank_page.
- Keep all internal IDs consistent between file paths and JSON content.
- Create reasonable positions and sizes for the visuals.
- Update pages.json when newly created pages must be added to pageOrder.
- Do not add a new page ID to pages.json for a reused blank page.
- Preserve all existing page IDs already present in pageOrder.
- Only create or update JSON files under Report/definition/.
- Use forward slashes in all paths.
- Include only files that actually need to be created or updated.
- For an "update" operation, content must contain the COMPLETE resulting
  JSON document, not a partial patch.
- Return only one valid JSON object.
- Do not include Markdown fences or explanations outside the JSON.

The output must have this structure:

{
  "summary": "...",
  "operations": [
    {
      "operation": "create or update",
      "path": "Report/definition/...",
      "content": {}
    }
  ]
}
"""


PBIR_REPAIR_PROMPT = """
You are repairing a proposed Power BI PBIRChangeSet.

You receive:
- the original PBIR authoring context;
- the invalid PBIRChangeSet;
- deterministic validation errors produced by Python.

Your task is to return a COMPLETE corrected PBIRChangeSet.

Rules:
- Treat the supplied validation errors as authoritative.
- Fix every supplied validation error.
- Preserve the original ReportPlan intent.
- Preserve required pages and visuals; do not remove required report
  content merely to avoid a validation error.
- Preserve proposed new page and visual IDs unless an error specifically
  requires changing them.
- Preserve all existing report content.
- Respect the reusable_blank_page strategy from the original authoring
  context. If a reusable blank page is provided, the first ReportPlan
  page must update and reuse it instead of creating a replacement page.
- Do not modify the semantic model.
- Use only tables, columns, and measures from the provided semantic model.
- Follow the supplied valid PBIR examples and current report context.
- Do not invent PBIR properties or structures that are not demonstrated
  by the supplied valid examples or current report context.
- Do not add a "title" property directly under the "visual" object.
- Only create or update JSON files under Report/definition/.
- Use forward slashes in all paths.
- For an "update" operation, content must contain the COMPLETE resulting
  JSON document, not a partial patch.
- Return the COMPLETE repaired PBIRChangeSet, not only the changed
  operation.
- Return only one valid JSON object.
- Do not include Markdown fences or explanations outside the JSON.

The output must have this structure:

{
  "summary": "...",
  "operations": [
    {
      "operation": "create or update",
      "path": "Report/definition/...",
      "content": {}
    }
  ]
}
"""


class PBIRAuthor:
    def __init__(
        self,
        llm: VLLMClient | None = None,
    ) -> None:
        self.llm = llm or VLLMClient()

    def create_change_set(
        self,
        authoring_context: dict[str, Any],
    ) -> PBIRChangeSet:
        """Generate proposed PBIR changes without applying them."""
        context_json = json.dumps(
            authoring_context,
            indent=2,
            ensure_ascii=False,
        )

        messages = [
            {
                "role": "system",
                "content": PBIR_AUTHORING_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "PBIR AUTHORING CONTEXT:\n"
                    f"{context_json}"
                ),
            },
        ]

        response = self.llm.chat(
            messages=messages,
            max_tokens=10000,
            temperature=0.0,
            enable_thinking=False,
            timeout_seconds=300.0,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned no PBIR change set."
            )

        parsed_change_set = self._parse_json(
            content
        )

        return PBIRChangeSet.model_validate(
            parsed_change_set
        )

    def repair_change_set(
        self,
        authoring_context: dict[str, Any],
        invalid_change_set: PBIRChangeSet,
        validation_errors: list[str],
    ) -> PBIRChangeSet:
        """Repair an invalid PBIR change set using validator feedback."""
        if not validation_errors:
            raise ValueError(
                "validation_errors must not be empty."
            )

        repair_context = {
            "authoring_context": authoring_context,
            "invalid_change_set": (
                invalid_change_set.model_dump()
            ),
            "validation_errors": validation_errors,
        }

        repair_context_json = json.dumps(
            repair_context,
            indent=2,
            ensure_ascii=False,
        )

        messages = [
            {
                "role": "system",
                "content": PBIR_REPAIR_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "PBIR REPAIR CONTEXT:\n"
                    f"{repair_context_json}"
                ),
            },
        ]

        response = self.llm.chat(
            messages=messages,
            max_tokens=10000,
            temperature=0.0,
            enable_thinking=False,
            timeout_seconds=300.0,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned no repaired "
                "PBIR change set."
            )

        parsed_change_set = self._parse_json(
            content
        )

        return PBIRChangeSet.model_validate(
            parsed_change_set
        )

    @staticmethod
    def _parse_json(
        content: str,
    ) -> dict[str, Any]:
        """Parse the JSON object returned by the model."""
        clean_content = content.strip()

        if clean_content.startswith("```"):
            lines = clean_content.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            clean_content = "\n".join(
                lines
            ).strip()

        return json.loads(
            clean_content
        )