from typing import Literal
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import PowerBIAgent


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

ARTIFACTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


app = FastAPI(
    title="Power BI AI Agent API",
    version="0.6.0",
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

agent = PowerBIAgent(
    artifacts_dir=ARTIFACTS_DIR,
)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
    )
    session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class IntentResponse(BaseModel):
    intent: str
    summary: str
    requires_database_schema: bool
    requires_report_generation: bool
    confidence: float


class ArtifactResponse(BaseModel):
    filename: str
    download_url: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    model: str
    classification: IntentResponse
    artifact: ArtifactResponse | None = None
    report_review_status: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ReportReviewRequest(BaseModel):
    action: Literal["approve", "reject"]


class ReportReviewResponse(BaseModel):
    session_id: str
    answer: str
    artifact: ArtifactResponse | None = None
    report_review_status: str | None = None


class SessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str


class SessionsResponse(BaseModel):
    sessions: list[SessionSummary]


class SessionMessage(BaseModel):
    message_id: int
    role: str
    content: str
    created_at: str


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: list[SessionMessage]
    report_review_status: str | None = None


@app.get(
    "/",
    include_in_schema=False,
)
def frontend() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html"
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get("/artifacts/{filename}")
def download_artifact(
    filename: str,
) -> FileResponse:
    candidate_name = Path(filename)

    if (
        candidate_name.name != filename
        or candidate_name.suffix.lower()
        != ".zip"
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact filename.",
        )

    artifacts_root = (
        ARTIFACTS_DIR.resolve()
    )

    artifact_path = (
        ARTIFACTS_DIR
        / filename
    ).resolve()

    if artifact_path.parent != artifacts_root:
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact path.",
        )

    if not artifact_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    return FileResponse(
        path=artifact_path,
        media_type="application/zip",
        filename=filename,
    )


@app.get(
    "/artifacts/{session_id}/{filename}"
)
def download_session_artifact(
    session_id: str,
    filename: str,
) -> FileResponse:
    session_component = Path(
        session_id
    )

    filename_component = Path(
        filename
    )

    if (
        session_component.name != session_id
        or session_id in {".", ".."}
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact session.",
        )

    if (
        filename_component.name != filename
        or filename_component.suffix.lower()
        != ".zip"
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact filename.",
        )

    artifacts_root = (
        ARTIFACTS_DIR.resolve()
    )

    session_directory = (
        ARTIFACTS_DIR
        / session_id
    ).resolve()

    if session_directory.parent != artifacts_root:
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact session path.",
        )

    artifact_path = (
        session_directory
        / filename
    ).resolve()

    if artifact_path.parent != session_directory:
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact path.",
        )

    if not artifact_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    return FileResponse(
        path=artifact_path,
        media_type="application/zip",
        filename=filename,
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
) -> ChatResponse:
    try:
        reply = agent.respond(
            message=request.message,
            session_id=request.session_id,
        )

        artifact_response = None

        if reply.artifact is not None:
            artifact_response = (
                ArtifactResponse(
                    filename=(
                        reply.artifact.filename
                    ),
                    download_url=(
                        reply.artifact.download_url
                    ),
                )
            )

        return ChatResponse(
            session_id=reply.session_id,
            answer=reply.answer,
            model=reply.model,
            classification=IntentResponse(
                intent=reply.intent.intent,
                summary=reply.intent.summary,
                requires_database_schema=(
                    reply.intent
                    .requires_database_schema
                ),
                requires_report_generation=(
                    reply.intent
                    .requires_report_generation
                ),
                confidence=(
                    reply.intent.confidence
                ),
            ),
            artifact=artifact_response,
            report_review_status=(
                agent.get_report_review_status(
                    reply.session_id
                )
            ),
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Agent request failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@app.post(
    "/reports/{session_id}/review",
    response_model=ReportReviewResponse,
)
def review_report(
    session_id: str,
    request: ReportReviewRequest,
) -> ReportReviewResponse:
    try:
        if request.action == "approve":
            reply = agent.approve_pending_report(
                session_id
            )
        else:
            reply = agent.reject_pending_report(
                session_id
            )

        artifact_response = None

        if reply.artifact is not None:
            artifact_response = ArtifactResponse(
                filename=reply.artifact.filename,
                download_url=(
                    reply.artifact.download_url
                ),
            )

        return ReportReviewResponse(
            session_id=reply.session_id,
            answer=reply.answer,
            artifact=artifact_response,
            report_review_status=(
                agent.get_report_review_status(
                    reply.session_id
                )
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        agent.restore_pending_report_review(
            session_id
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Report review failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@app.get(
    "/sessions",
    response_model=SessionsResponse,
)
def list_sessions(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
) -> SessionsResponse:
    sessions = agent.list_sessions(
        limit=limit,
    )

    return SessionsResponse(
        sessions=[
            SessionSummary(**session)
            for session in sessions
        ],
    )


@app.get(
    "/sessions/{session_id}/messages",
    response_model=SessionMessagesResponse,
)
def get_session_messages(
    session_id: str,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> SessionMessagesResponse:
    messages = (
        agent.get_session_messages(
            session_id=session_id,
            limit=limit,
        )
    )

    if messages is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation session not found."
            ),
        )

    return SessionMessagesResponse(
        session_id=session_id,
        messages=[
            SessionMessage(**message)
            for message in messages
        ],
        report_review_status=(
            agent.get_report_review_status(
                session_id
            )
        ),
    )


@app.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
) -> dict[str, str]:
    deleted = agent.delete_session(
        session_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation session not found."
            ),
        )

    return {
        "status": "deleted",
        "session_id": session_id,
    }