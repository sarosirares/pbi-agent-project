const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat-button");
const chatMessages = document.getElementById("chat-messages");
const statusMessage = document.getElementById("status-message");
const sessionList = document.getElementById("session-list");

const sessionStorageKey = "powerbi_agent_session_id";

let sessionId = sessionStorage.getItem(sessionStorageKey);

const NEW_CHAT_REQUEST_KEY = "__new_chat__";
const pendingChatRequests = new Map();

const reportReviewStatuses = new Map();


function removeEmptyState() {
    const emptyState = document.getElementById("empty-state");

    if (emptyState) {
        emptyState.remove();
    }
}


function showEmptyState() {
    chatMessages.innerHTML = `
        <div id="empty-state">
            <h2>Incepe o conversatie</h2>
            <p>
                Descrie raportul Power BI de care ai nevoie
                sau pune o intrebare.
            </p>
        </div>
    `;
}


function renderMarkdown(content) {
    const html = marked.parse(
        content,
        {
            gfm: true,
            breaks: true,
        },
    );

    return DOMPurify.sanitize(
        html,
        {
            USE_PROFILES: {
                html: true,
            },
        },
    );
}


function addMessage(role, content) {
    removeEmptyState();

    const messageElement = document.createElement("div");

    messageElement.classList.add(
        "message",
        role === "user"
            ? "message-user"
            : "message-assistant",
    );

    if (role === "assistant") {
        messageElement.innerHTML = renderMarkdown(content);
    } else {
        messageElement.textContent = content;
    }

    chatMessages.appendChild(messageElement);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeReportReviewState() {
    const state = document.getElementById(
        "report-review-state"
    );

    if (state) {
        state.remove();
    }
}


function renderReportReviewState(status) {
    removeReportReviewState();

    if (sessionId) {
        if (
            status === "pending"
            || status === "generating"
            || status === "rejecting"
        ) {
            reportReviewStatuses.set(
                sessionId,
                status,
            );
        } else {
            reportReviewStatuses.delete(
                sessionId
            );
        }
    }

    updateActiveRequestState();

    if (
        status !== "pending"
        && status !== "generating"
        && status !== "rejecting"
    ) {
        return;
    }

    const state = document.createElement("div");

    state.id = "report-review-state";
    state.className = "report-review-state";

    if (status !== "pending") {
        const message = document.createElement("div");

        message.className = "report-review-status";

        message.textContent = (
            status === "generating"
                ? "Se genereaza raportul aprobat..."
                : "Se respinge interogarea..."
        );

        state.appendChild(message);
    }

    const actions = document.createElement("div");

    actions.className = "report-review-actions";

    const approveButton = document.createElement("button");

    approveButton.type = "button";
    approveButton.className = "report-review-approve";
    approveButton.textContent = "Aproba";

    const rejectButton = document.createElement("button");

    rejectButton.type = "button";
    rejectButton.className = "report-review-reject";
    rejectButton.textContent = "Respinge";

    const disabled = status !== "pending";

    approveButton.disabled = disabled;
    rejectButton.disabled = disabled;

    approveButton.addEventListener(
        "click",
        () => reviewReport("approve"),
    );

    rejectButton.addEventListener(
        "click",
        () => reviewReport("reject"),
    );

    actions.appendChild(approveButton);
    actions.appendChild(rejectButton);

    state.appendChild(actions);
    chatMessages.appendChild(state);

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


function getActiveRequestKey() {
    return sessionId ?? NEW_CHAT_REQUEST_KEY;
}


function updateActiveRequestState() {
    const requestKey = getActiveRequestKey();

    const isChatPending = pendingChatRequests.has(
        requestKey
    );

    const reviewStatus = sessionId
        ? reportReviewStatuses.get(sessionId)
        : null;

    const isReportBusy = (
        reviewStatus === "generating"
        || reviewStatus === "rejecting"
    );

    const isBusy = (
        isChatPending
        || isReportBusy
    );

    sendButton.disabled = isBusy;
    messageInput.disabled = isBusy;

    if (isChatPending) {
        statusMessage.textContent =
            "Agentul genereaza raspunsul...";
    } else {
        statusMessage.textContent = "";
    }
}


async function reviewReport(action) {
    if (!sessionId) {
        return;
    }

    const reviewSessionId = sessionId;

    renderReportReviewState(
        action === "approve"
            ? "generating"
            : "rejecting"
    );

    try {
        const response = await fetch(
            `/reports/${encodeURIComponent(reviewSessionId)}/review`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    action: action,
                }),
            },
        );

        if (!response.ok) {
            throw new Error(
                await readErrorResponse(response)
            );
        }

        await response.json();

        if (sessionId === reviewSessionId) {
            await loadConversation();
        }

        await loadSessions();
    } catch (error) {
        if (sessionId === reviewSessionId) {
            await loadConversation();

            statusMessage.textContent =
                `Eroare: ${error.message}`;
        }
    } finally {
        if (sessionId === reviewSessionId) {
            messageInput.focus();
        }
    }
}


async function readErrorResponse(response) {
    try {
        const data = await response.json();

        if (data.detail) {
            return data.detail;
        }
    } catch {
        return `HTTP ${response.status}`;
    }

    return `HTTP ${response.status}`;
}


async function loadSessions() {
    try {
        const response = await fetch("/sessions");

        if (!response.ok) {
            throw new Error(
                await readErrorResponse(response)
            );
        }

        const data = await response.json();

        sessionList.innerHTML = "";

        for (const session of data.sessions) {
            const button = document.createElement("button");

            button.type = "button";
            button.className = "session-item";
            button.textContent = session.title;

            if (session.session_id === sessionId) {
                button.classList.add("active");
            }

            button.addEventListener(
                "click",
                async () => {
                    sessionId = session.session_id;

                    sessionStorage.setItem(
                        sessionStorageKey,
                        sessionId,
                    );

                    await loadConversation();
                    await loadSessions();
                },
            );

            sessionList.appendChild(button);
        }
    } catch (error) {
        statusMessage.textContent =
            `Nu s-au putut incarca sesiunile: ${error.message}`;
    }
}


async function loadConversation() {
    const requestedSessionId = sessionId;

    statusMessage.textContent = "";
    removeReportReviewState();

    if (!requestedSessionId) {
        chatMessages.innerHTML = "";

        const pendingMessage = pendingChatRequests.get(
            NEW_CHAT_REQUEST_KEY
        );

        if (pendingMessage) {
            addMessage(
                "user",
                pendingMessage,
            );
        } else {
            showEmptyState();
        }

        updateActiveRequestState();
        return;
    }

    try {
        const response = await fetch(
            `/sessions/${
                encodeURIComponent(
                    requestedSessionId
                )
            }/messages`
        );

        if (sessionId !== requestedSessionId) {
            return;
        }

        if (response.status === 404) {
            sessionStorage.removeItem(
                sessionStorageKey
            );

            sessionId = null;

            showEmptyState();
            updateActiveRequestState();

            return;
        }

        if (!response.ok) {
            throw new Error(
                await readErrorResponse(response)
            );
        }

        const data = await response.json();

        if (sessionId !== requestedSessionId) {
            return;
        }

        chatMessages.innerHTML = "";

        for (const message of data.messages) {
            addMessage(
                message.role,
                message.content,
            );
        }

        const pendingMessage = pendingChatRequests.get(
            requestedSessionId
        );

        if (pendingMessage) {
            addMessage(
                "user",
                pendingMessage,
            );
        }

        if (
            data.messages.length === 0
            && !pendingMessage
        ) {
            showEmptyState();
        }

        renderReportReviewState(
            data.report_review_status
        );

    } catch (error) {
        if (sessionId === requestedSessionId) {
            updateActiveRequestState();

            statusMessage.textContent =
                `Nu s-a putut incarca conversatia: ${error.message}`;
        }
    }
}


async function sendMessage(
    message,
    requestSessionId,
) {
    const response = await fetch(
        "/chat",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message: message,
                session_id: requestSessionId,
            }),
        },
    );

    if (!response.ok) {
        throw new Error(
            await readErrorResponse(response)
        );
    }

    return response.json();
}


chatForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const message =
            messageInput.value.trim();

        if (!message) {
            return;
        }

        const requestSessionId =
            sessionId;

        const requestKey = (
            requestSessionId
            ?? NEW_CHAT_REQUEST_KEY
        );

        if (
            pendingChatRequests.has(
                requestKey
            )
        ) {
            return;
        }

        pendingChatRequests.set(
            requestKey,
            message,
        );

        addMessage(
            "user",
            message,
        );

        messageInput.value = "";

        updateActiveRequestState();

        let errorMessage = null;

        try {
            const response =
                await sendMessage(
                    message,
                    requestSessionId,
                );

            pendingChatRequests.delete(
                requestKey
            );

            if (
                requestSessionId === null
            ) {
                if (sessionId === null) {
                    sessionId =
                        response.session_id;

                    sessionStorage.setItem(
                        sessionStorageKey,
                        sessionId,
                    );

                    await loadConversation();
                }
            } else if (
                sessionId
                === requestSessionId
            ) {
                await loadConversation();
            }

            await loadSessions();
        } catch (error) {
            pendingChatRequests.delete(
                requestKey
            );

            errorMessage =
                `Eroare: ${error.message}`;
        } finally {
            const requestIsStillVisible = (
                sessionId
                === requestSessionId
                || (
                    requestSessionId
                    === null
                    && sessionId === null
                )
            );

            updateActiveRequestState();

            if (
                errorMessage
                && requestIsStillVisible
            ) {
                statusMessage.textContent =
                    errorMessage;
            }

            if (!messageInput.disabled) {
                messageInput.focus();
            }
        }
    },
);


newChatButton.addEventListener(
    "click",
    async () => {
        sessionId = null;

        sessionStorage.removeItem(
            sessionStorageKey
        );

        await loadConversation();
        await loadSessions();

        messageInput.focus();
    },
);


messageInput.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Enter"
            && !event.shiftKey
        ) {
            event.preventDefault();
            chatForm.requestSubmit();
        }
    },
);


async function initialize() {
    await loadConversation();
    await loadSessions();
}


initialize();