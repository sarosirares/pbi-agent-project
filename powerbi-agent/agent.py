import json
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
from urllib.parse import quote

from conversation_store import SQLiteConversationStore
from database_query_service import DatabaseQueryService
from database_question_service import DatabaseQuestionService
from intent_classifier import IntentClassifier
from intent_models import IntentResult
from llm_client import VLLMClient
from report_generation_service import (
    generate_powerbi_project,
)
from pbir_project_context import (
    load_pbir_project_context,
)
from powerbi_sql_project_builder import (
    build_powerbi_sql_project,
)
from project_inspection_context import (
    build_project_inspection_context,
)
from semantic_model_loader import (
    load_semantic_model_context,
)


SYSTEM_PROMPT = """
Esti asistentul pentru Power BI si baza de date SQL Server configurata
prin aplicatie.

Poti ajuta utilizatorul sa:
- inteleaga ce informatii sunt disponibile in baza de date configurata;
- obtina raspunsuri la intrebari despre datele din baza de date configurata;
- creeze rapoarte Power BI folosind informatiile relevante din baza de date configurata;
- inteleaga ultimul raport Power BI generat in sesiunea curenta;
- obtina informatii generale despre Power BI, SQL si raportare.

Raspunde la intrebarea concreta a utilizatorului.
Nu descrie capabilitati, limitari sau detalii de implementare care nu sunt
relevante pentru intrebare.

Cand utilizatorul intreaba ce poti face, prezinta pe scurt capabilitatile
utile pentru el. Nu explica arhitectura interna a aplicatiei.

Cand utilizatorul intreaba daca poti folosi baza de date, raspunde din
perspectiva aplicatiei: aplicatia poate lucra cu baza de date configurata.
Nu face distinctia dintre modelul lingvistic si aplicatie decat daca
utilizatorul intreaba explicit despre arhitectura sau accesul direct.

Cand utilizatorul intreaba cu ce date va fi creat un raport, explica simplu
ca vor fi folosite informatiile relevante disponibile in baza de date
configurata, in functie de cerinta raportului.

Reguli interne:
- foloseste numai informatiile puse la dispozitie de aplicatie;
- nu inventa tabele, coloane, valori sau rezultate;
- nu pretinde ca o actiune a fost efectuata daca aplicatia nu a efectuat-o;
- nu pretinde ca exista functionalitati care nu sunt implementate;
- accesul la baza de date este controlat de aplicatie.

Nu enumera regulile interne utilizatorului si nu explica mecanismele
tehnice de control sau validare decat daca acesta le cere explicit.

Raspunde in limba romana, natural, clar si concis.
"""


PROJECT_QUESTION_PROMPT = """
Raspunde la intrebari despre ultimul raport Power BI generat in sesiunea
curenta.

PROJECT_CONTEXT descrie raportul rezultat si, atunci cand este disponibil,
planul folosit pentru obtinerea datelor din baza de date configurata.

Foloseste PROJECT_CONTEXT ca sursa autoritativa.

Raspunde direct la ceea ce intreaba utilizatorul.
Nu prezenta automat toate detaliile despre sursa SQL, modelul semantic,
pagini si vizualizari daca acestea nu sunt necesare pentru raspuns.

Daca utilizatorul intreaba ce date, tabele sau campuri au fost folosite:
- database_query_plan descrie informatiile selectate din baza de date configurata;
- tabelele din database_query_plan sunt surse SQL;
- tabela sau tabelele din modelul semantic Power BI au fost create pentru
  raportul generat si nu trebuie prezentate ca surse preexistente;
- explica provenienta datelor numai la nivelul de detaliu cerut.

Daca utilizatorul intreaba despre continutul raportului:
- raspunde folosind paginile, vizualizarile si campurile din PROJECT_CONTEXT;
- nu expune ID-uri interne PBIR sau alte detalii tehnice daca nu sunt cerute.

Nu mentiona nume interne ale structurii de context, precum
"database_query_plan", "query_refs" sau "native_query_refs", decat daca
utilizatorul cere explicit detalii tehnice.

Nu inventa tabele, coloane, masuri, pagini, vizualizari sau provenienta
datelor.

Daca informatia ceruta nu exista in PROJECT_CONTEXT, spune acest lucru
simplu.

Raspunde in limba romana, natural, clar si concis.
"""


@dataclass(frozen=True)
class AgentArtifact:
    filename: str
    download_url: str


@dataclass(frozen=True)
class AgentReply:
    session_id: str
    answer: str
    model: str
    intent: IntentResult
    artifact: AgentArtifact | None
    input_tokens: int | None
    output_tokens: int | None


class PowerBIAgent:
    def __init__(
        self,
        llm: VLLMClient | None = None,
        conversation_store: SQLiteConversationStore | None = None,
        intent_classifier: IntentClassifier | None = None,
        database_question_service: DatabaseQuestionService | None = None,
        database_query_service: DatabaseQueryService | None = None,
        max_history_messages: int = 10,
        artifacts_dir: str | Path | None = None,
    ) -> None:
        if max_history_messages <= 0:
            raise ValueError(
                "max_history_messages must be greater than zero."
            )

        self.llm = llm or VLLMClient()

        self.conversation_store = (
            conversation_store
            or SQLiteConversationStore()
        )

        self.intent_classifier = (
            intent_classifier
            or IntentClassifier(
                llm=self.llm
            )
        )

        self.database_question_service = (
            database_question_service
            or DatabaseQuestionService(
                llm=self.llm
            )
        )

        self.database_query_service = (
            database_query_service
            or DatabaseQueryService(
                llm=self.llm
            )
        )

        self.max_history_messages = (
            max_history_messages
        )

        self.artifacts_dir = Path(
            artifacts_dir
            or (
                Path(__file__).resolve().parent
                / "artifacts"
            )
        ).resolve()

    def respond(
        self,
        message: str,
        session_id: str | None = None,
    ) -> AgentReply:
        clean_message = message.strip()

        if not clean_message:
            raise ValueError(
                "The message cannot be empty."
            )

        resolved_session_id = (
            session_id
            or str(uuid4())
        )

        history = (
            self.conversation_store.get_history(
                session_id=resolved_session_id,
                limit=self.max_history_messages,
            )
        )

        intent_result = (
            self.intent_classifier.classify(
                message=clean_message,
                history=history,
            )
        )

        if intent_result.intent == "report_request":
            return self._generate_report(
                message=clean_message,
                session_id=resolved_session_id,
                intent_result=intent_result,
            )

        if intent_result.intent == "project_question":
            return self._answer_project_question(
                message=clean_message,
                session_id=resolved_session_id,
                intent_result=intent_result,
                history=history,
            )

        if intent_result.intent == "database_question":
            return self._answer_database_question(
                message=clean_message,
                session_id=resolved_session_id,
                intent_result=intent_result,
            )

        if intent_result.intent == "database_query":
            return self._answer_database_query(
                message=clean_message,
                session_id=resolved_session_id,
                intent_result=intent_result,
            )

        if intent_result.intent == "report_follow_up":
            return self._follow_up_report(
                message=clean_message,
                session_id=resolved_session_id,
                intent_result=intent_result,
            )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *history,
            {
                "role": "user",
                "content": clean_message,
            },
        ]

        response = self.llm.chat(
            messages=messages,
            max_tokens=512,
            temperature=0.0,
            enable_thinking=False,
        )

        answer = (
            response.choices[0].message.content
        )

        if not answer:
            raise RuntimeError(
                "The model returned no text response."
            )

        self.conversation_store.save_exchange(
            session_id=resolved_session_id,
            user_message=clean_message,
            assistant_message=answer,
        )

        return AgentReply(
            session_id=resolved_session_id,
            answer=answer,
            model=self.llm.model_name,
            intent=intent_result,
            artifact=None,
            input_tokens=(
                response.usage.prompt_tokens
                if response.usage
                else None
            ),
            output_tokens=(
                response.usage.completion_tokens
                if response.usage
                else None
            ),
        )

    def _answer_database_question(
        self,
        message: str,
        session_id: str,
        intent_result: IntentResult,
    ) -> AgentReply:
        resolved_message = (
            intent_result.resolved_message
            or message
        )

        answer = self.database_question_service.answer(
            resolved_message
        )

        self.conversation_store.save_exchange(
            session_id=session_id,
            user_message=message,
            assistant_message=answer,
        )

        return AgentReply(
            session_id=session_id,
            answer=answer,
            model=self.llm.model_name,
            intent=intent_result,
            artifact=None,
            input_tokens=None,
            output_tokens=None,
        )


    def _answer_database_query(
        self,
        message: str,
        session_id: str,
        intent_result: IntentResult,
    ) -> AgentReply:
        resolved_message = (
            intent_result.resolved_message
            or message
        )

        answer = self.database_query_service.answer(
            resolved_message
        )

        self.conversation_store.save_exchange(
            session_id=session_id,
            user_message=message,
            assistant_message=answer,
        )

        return AgentReply(
            session_id=session_id,
            answer=answer,
            model=self.llm.model_name,
            intent=intent_result,
            artifact=None,
            input_tokens=None,
            output_tokens=None,
        )


    def _answer_project_question(
        self,
        message: str,
        session_id: str,
        intent_result: IntentResult,
        history: list[dict[str, str]],
    ) -> AgentReply:
        session_artifacts_dir = (
            self.artifacts_dir
            / session_id
        )

        latest_report_context_path = (
            session_artifacts_dir
            / "latest_report_context.json"
        )

        if not latest_report_context_path.is_file():
            answer = (
                "Nu exista inca un raport Power BI "
                "generat in aceasta sesiune."
            )

            self.conversation_store.save_exchange(
                session_id=session_id,
                user_message=message,
                assistant_message=answer,
            )

            return AgentReply(
                session_id=session_id,
                answer=answer,
                model=self.llm.model_name,
                intent=intent_result,
                artifact=None,
                input_tokens=None,
                output_tokens=None,
            )

        latest_report_context = json.loads(
            latest_report_context_path.read_text(
                encoding="utf-8"
            )
        )

        project_directory = (
            latest_report_context.get(
                "project_directory"
            )
        )

        if not isinstance(
            project_directory,
            str,
        ) or not project_directory:
            raise RuntimeError(
                "Latest report context contains "
                "no project directory."
            )

        generated_project_path = (
            session_artifacts_dir
            / project_directory
        )

        semantic_model_candidates = list(
            generated_project_path.glob(
                "*.SemanticModel"
            )
        )

        report_candidates = list(
            generated_project_path.glob(
                "*.Report"
            )
        )

        if len(semantic_model_candidates) != 1:
            raise RuntimeError(
                "Expected exactly one semantic model "
                "in the latest generated project."
            )

        if len(report_candidates) != 1:
            raise RuntimeError(
                "Expected exactly one report "
                "in the latest generated project."
            )

        semantic_context = (
            load_semantic_model_context(
                semantic_model_candidates[0]
            )
        )

        project_context = (
            load_pbir_project_context(
                report_candidates[0]
            )
        )

        inspection_context = (
            build_project_inspection_context(
                semantic_context=semantic_context,
                project_context=project_context,
            )
        )

        database_query_plan = (
            latest_report_context.get(
                "database_query_plan"
            )
        )

        if isinstance(
            database_query_plan,
            dict,
        ):
            inspection_context[
                "database_query_plan"
            ] = database_query_plan

        inspection_context_json = (
            json.dumps(
                inspection_context,
                indent=2,
                ensure_ascii=False,
            )
        )

        messages = [
            {
                "role": "system",
                "content": (
                    PROJECT_QUESTION_PROMPT
                    + "\n\nPROJECT_CONTEXT:\n"
                    + inspection_context_json
                ),
            },
            *history,
            {
                "role": "user",
                "content": message,
            },
        ]

        response = self.llm.chat(
            messages=messages,
            max_tokens=4096,
            temperature=0.0,
            enable_thinking=False,
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        if not answer:
            raise RuntimeError(
                "The model returned no project answer."
            )

        self.conversation_store.save_exchange(
            session_id=session_id,
            user_message=message,
            assistant_message=answer,
        )

        return AgentReply(
            session_id=session_id,
            answer=answer,
            model=self.llm.model_name,
            intent=intent_result,
            artifact=None,
            input_tokens=(
                response.usage.prompt_tokens
                if response.usage
                else None
            ),
            output_tokens=(
                response.usage.completion_tokens
                if response.usage
                else None
            ),
        )

    def _follow_up_report(
        self,
        message: str,
        session_id: str,
        intent_result: IntentResult,
    ) -> AgentReply:
        session_artifacts_dir = (
            self.artifacts_dir
            / session_id
        )

        latest_report_context_path = (
            session_artifacts_dir
            / "latest_report_context.json"
        )

        if not latest_report_context_path.is_file():
            answer = (
                "Nu exista inca un raport Power BI "
                "generat in aceasta sesiune pe care "
                "sa il pot modifica."
            )

            self.conversation_store.save_exchange(
                session_id=session_id,
                user_message=message,
                assistant_message=answer,
            )

            return AgentReply(
                session_id=session_id,
                answer=answer,
                model=self.llm.model_name,
                intent=intent_result,
                artifact=None,
                input_tokens=None,
                output_tokens=None,
            )

        latest_report_context = json.loads(
            latest_report_context_path.read_text(
                encoding="utf-8"
            )
        )

        original_request = (
            latest_report_context.get(
                "report_request"
            )
        )

        if not isinstance(
            original_request,
            str,
        ) or not original_request.strip():
            raise RuntimeError(
                "Latest report context contains "
                "no original report request."
            )

        stored_follow_ups = (
            latest_report_context.get(
                "report_follow_ups",
                [],
            )
        )

        if not isinstance(
            stored_follow_ups,
            list,
        ) or not all(
            isinstance(item, str)
            for item in stored_follow_ups
        ):
            raise RuntimeError(
                "Latest report context contains "
                "invalid report follow-up history."
            )

        current_database_query_plan = (
            latest_report_context.get(
                "database_query_plan"
            )
        )

        if not isinstance(
            current_database_query_plan,
            dict,
        ):
            raise RuntimeError(
                "Latest report context contains "
                "no current database query plan."
            )

        current_report_plan = (
            latest_report_context.get(
                "report_plan"
            )
        )

        if not isinstance(
            current_report_plan,
            dict,
        ):
            raise RuntimeError(
                "Latest report context contains "
                "no current report plan."
            )

        updated_follow_ups = [
            *stored_follow_ups,
            message,
        ]

        current_database_query_plan_json = (
            json.dumps(
                current_database_query_plan,
                indent=2,
                ensure_ascii=False,
            )
        )

        current_report_plan_json = (
            json.dumps(
                current_report_plan,
                indent=2,
                ensure_ascii=False,
            )
        )

        effective_request = (
            "ORIGINAL REPORT REQUEST:\n"
            f"{original_request}\n\n"
            "CURRENT DATABASE QUERY PLAN:\n"
            f"{current_database_query_plan_json}\n\n"
            "CURRENT REPORT PLAN:\n"
            f"{current_report_plan_json}\n\n"
            "NEW FOLLOW-UP REQUEST:\n"
            f"{message}\n\n"
            "REVISION RULES:\n"
            "- The current database query plan and "
            "current report plan describe the existing "
            "report and are the authoritative starting "
            "point for this revision.\n"
            "- Apply only the new follow-up request.\n"
            "- Preserve every part of the current report "
            "that the new follow-up does not explicitly "
            "ask to change.\n"
            "- If the follow-up changes presentation "
            "only, preserve the current database query "
            "semantics.\n"
            "- If the follow-up changes the required "
            "data, make the smallest necessary change "
            "to the database query while preserving "
            "unaffected columns, aggregations, grouping, "
            "filters, sorting, pages, and visuals.\n"
            "- Do not redesign or simplify the existing "
            "report unless the new follow-up explicitly "
            "requires it."
        )

        return self._generate_report(
            message=message,
            session_id=session_id,
            intent_result=intent_result,
            pipeline_request=effective_request,
            original_report_request=original_request,
            report_follow_ups=updated_follow_ups,
        )

    def _generate_report(
        self,
        message: str,
        session_id: str,
        intent_result: IntentResult,
        *,
        pipeline_request: str | None = None,
        original_report_request: str | None = None,
        report_follow_ups: list[str] | None = None,
    ) -> AgentReply:
        effective_request = (
            pipeline_request
            or message
        )
        server = os.getenv(
            "SQLSERVER_SERVER"
        )

        if not server:
            raise RuntimeError(
                "SQLSERVER_SERVER is not configured."
            )

        database = os.getenv(
            "SQLSERVER_DATABASE"
        )

        if not database:
            raise RuntimeError(
                "SQLSERVER_DATABASE is not configured."
            )

        template_path = (
            Path(__file__).resolve().parent
            / "templates"
            / "blank_powerbi_project"
        )

        if not template_path.is_dir():
            raise RuntimeError(
                "Blank Power BI template was not found: "
                f"{template_path}"
            )

        session_artifacts_dir = (
            self.artifacts_dir
            / session_id
        )

        planning = (
            self.database_query_service.plan(
                effective_request
            )
        )

        report_data_plan = (
            planning.plan.model_copy(
                update={
                    "limit": None,
                }
            )
        )

        data_project = (
            build_powerbi_sql_project(
                template_path=template_path,
                output_path=(
                    session_artifacts_dir
                    / "src"
                ),
                plan=report_data_plan,
                schema_context=(
                    planning.schema_context
                ),
                server=server,
                database=database,
            )
        )

        result = generate_powerbi_project(
            user_request=effective_request,
            semantic_model_path=(
                data_project.semantic_model_path
            ),
            report_path=(
                data_project.report_path
            ),
            output_root=(
                session_artifacts_dir
            ),
            llm=self.llm,
            max_repairs=1,
        )

        if result.cli_exit_code != 0:
            raise RuntimeError(
                "Generated Power BI project failed "
                "PBIR CLI validation.\n"
                f"STDOUT:\n{result.cli_stdout}\n"
                f"STDERR:\n{result.cli_stderr}"
            )

        latest_report_context = {
            "project_directory": (
                result.project_path.name
            ),
            "report_request": (
                original_report_request
                or message
            ),
            "report_follow_ups": (
                report_follow_ups
                or []
            ),
            "database_query_plan": (
                report_data_plan.model_dump()
            ),
            "report_plan": (
                result.plan.model_dump()
            ),
        }

        latest_report_context_path = (
            session_artifacts_dir
            / "latest_report_context.json"
        )

        latest_report_context_path.write_text(
            json.dumps(
                latest_report_context,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        encoded_filename = quote(
            result.zip_path.name
        )

        artifact = AgentArtifact(
            filename=result.zip_path.name,
            download_url=(
                f"/artifacts/{session_id}/"
                f"{encoded_filename}"
            ),
        )

        answer = (
            "Raportul Power BI a fost generat "
            "si validat.\n\n"
            f"[Descarca proiectul Power BI (ZIP)]"
            f"({artifact.download_url})"
        )

        self.conversation_store.save_exchange(
            session_id=session_id,
            user_message=message,
            assistant_message=answer,
        )

        return AgentReply(
            session_id=session_id,
            answer=answer,
            model=self.llm.model_name,
            intent=intent_result,
            artifact=artifact,
            input_tokens=None,
            output_tokens=None,
        )

    def list_sessions(
        self,
        limit: int = 50,
    ) -> list[dict[str, str]]:
        return (
            self.conversation_store.list_sessions(
                limit=limit,
            )
        )

    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[dict[str, int | str]] | None:
        return (
            self.conversation_store.get_session_messages(
                session_id=session_id,
                limit=limit,
            )
        )

    def delete_session(
        self,
        session_id: str,
    ) -> bool:
        return (
            self.conversation_store.delete_session(
                session_id
            )
        )