const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat-button");
const chatMessages = document.getElementById("chat-messages");
const statusMessage = document.getElementById("status-message");
const sessionList = document.getElementById("session-list");

const sessionStorageKey = "powerbi_agent_session_id";

let sessionId = sessionStorage.getItem(sessionStorageKey);


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


function setLoading(isLoading) {
    sendButton.disabled = isLoading;
    messageInput.disabled = isLoading;

    statusMessage.textContent = isLoading
        ? "Agentul genereaza raspunsul..."
        : "";
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
    if (!sessionId) {
        showEmptyState();
        return;
    }

    try {
        const response = await fetch(
            `/sessions/${encodeURIComponent(sessionId)}/messages`
        );

        if (response.status === 404) {
            sessionStorage.removeItem(sessionStorageKey);            
            sessionId = null;
            showEmptyState();
            return;
        }

        if (!response.ok) {
            throw new Error(
                await readErrorResponse(response)
            );
        }

        const data = await response.json();

        chatMessages.innerHTML = "";

        for (const message of data.messages) {
            addMessage(
                message.role,
                message.content,
            );
        }

        if (data.messages.length === 0) {
            showEmptyState();
        }
    } catch (error) {
        statusMessage.textContent =
            `Nu s-a putut incarca conversatia: ${error.message}`;
    }
}


async function sendMessage(message) {
    const response = await fetch(
        "/chat",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
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

        const message = messageInput.value.trim();

        if (!message) {
            return;
        }

        addMessage("user", message);

        messageInput.value = "";
        setLoading(true);

        try {
            const response = await sendMessage(message);

            if (!sessionId) {
                sessionId = response.session_id;

                sessionStorage.setItem(
                    sessionStorageKey,
                    sessionId,
                );
            }

            addMessage(
                "assistant",
                response.answer,
            );

            await loadSessions();
        } catch (error) {
            statusMessage.textContent =
                `Eroare: ${error.message}`;
        } finally {
            setLoading(false);
            messageInput.focus();
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

        statusMessage.textContent = "";

        showEmptyState();

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