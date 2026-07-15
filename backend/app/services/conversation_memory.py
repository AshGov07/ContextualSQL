from app.services.chat_history_service import (
    ChatHistoryService
)

class ConversationMemory:

    @staticmethod
    def get_context(
        session_id,
        limit=10
    ):

        history = (
            ChatHistoryService
            .get_history(session_id)
        )

        history = history[-limit:]

        return "\n".join(
            [
                f"{msg['role']}: {msg['content']}"
                for msg in history
            ]
        )