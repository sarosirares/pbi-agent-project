import sqlite3
from pathlib import Path


class SQLiteConversationStore:
    def __init__(
        self,
        database_path: str | Path | None = None,
    ) -> None:
        if database_path is None:
            database_path = (
                Path(__file__).resolve().parent
                / "data"
                / "conversations.db"
            )

        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        # Return rows that can be accessed by column name.
        connection.row_factory = sqlite3.Row

        # Foreign keys must be enabled for every SQLite connection.
        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:

            # WAL improves SQLite behavior when reads and writes overlap.
            connection.execute("PRAGMA journal_mode = WAL")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL
                        CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id)
                        REFERENCES sessions(session_id)
                        ON DELETE CASCADE
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_messages_session_id
                ON messages(session_id, message_id)
                """
            )

    def get_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        with self._connect() as connection:
            # Read the newest messages first so LIMIT keeps the most
            # recent context instead of the oldest messages.
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY message_id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        # Restore chronological order before sending history to the LLM.
        return [
            {
                "role": row["role"],
                "content": row["content"],
            }
            for row in reversed(rows)
        ]

    def save_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        # Create a new session or mark an existing one as recently used.
        clean_session_id = session_id.strip()
        clean_user_message = user_message.strip()
        clean_assistant_message = assistant_message.strip()

        if not clean_session_id:
            raise ValueError(
                "session_id cannot be empty."
            )

        if not clean_user_message:
            raise ValueError(
                "user_message cannot be empty."
            )

        if not clean_assistant_message:
            raise ValueError(
                "assistant_message cannot be empty."
            )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (session_id)
                VALUES (?)
                ON CONFLICT(session_id)
                DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP
                """,
                (clean_session_id,),
            )

            connection.executemany(
                """
                INSERT INTO messages (
                    session_id,
                    role,
                    content
                )
                VALUES (?, ?, ?)
                """,
                [
                    (
                        clean_session_id,
                        "user",
                        clean_user_message,
                    ),
                    (
                        clean_session_id,
                        "assistant",
                        clean_assistant_message,
                    ),
                ],
            )

    def list_sessions(
        self,
        limit: int = 50,
    ) -> list[dict[str, str]]:
        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )
        
        # Use the first user message as a temporary conversation title.
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    s.session_id,
                    s.created_at,
                    s.updated_at,
                    COALESCE(
                        (
                            SELECT m.content
                            FROM messages AS m
                            WHERE
                                m.session_id = s.session_id
                                AND m.role = 'user'
                            ORDER BY m.message_id ASC
                            LIMIT 1
                        ),
                        ''
                    ) AS first_message
                FROM sessions AS s
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        sessions = []

        for row in rows:
            first_message = row["first_message"].strip()

            if len(first_message) > 60:
                first_message = (
                    first_message[:57] + "..."
                )

            sessions.append(
                {
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "title": (
                        first_message
                        or "Conversatie fara titlu"
                    ),
                }
            )

        return sessions
            
    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[dict[str, int | str]] | None:
        clean_session_id = session_id.strip()

        if not clean_session_id:
            return None

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        # Distinguish a missing session from an existing empty session.
        with self._connect() as connection:
            session_exists = connection.execute(
                """
                SELECT 1
                FROM sessions
                WHERE session_id = ?
                """,
                (clean_session_id,),
            ).fetchone()

            if session_exists is None:
                return None

            rows = connection.execute(
                """
                SELECT
                    message_id,
                    role,
                    content,
                    created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY message_id ASC
                LIMIT ?
                """,
                (clean_session_id, limit),
            ).fetchall()

        return [
            {
                "message_id": row["message_id"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


    def delete_session(
        self,
        session_id: str,
    ) -> bool:
        clean_session_id = session_id.strip()

        if not clean_session_id:
            return False

        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM sessions
                WHERE session_id = ?
                """,
                (clean_session_id,),
            )

        return cursor.rowcount > 0