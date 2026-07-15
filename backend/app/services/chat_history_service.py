import json
from pathlib import Path

from app.config import SESSION_DIR


class ChatHistoryService:

    @staticmethod
    def get_chat_file(session_id):

        return (
            SESSION_DIR
            / session_id
            / "chat_history.json"
        )

    @staticmethod
    def save_message(
        session_id,
        role,
        content
    ):

        chat_file = (
            ChatHistoryService.get_chat_file(
                session_id
            )
        )

        history = []

        if chat_file.exists():

            with open(
                chat_file,
                "r",
                encoding="utf-8"
            ) as f:

                history = json.load(f)

        history.append({
            "role": role,
            "content": content
        })

        with open(
            chat_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                indent=4
            )

    @staticmethod
    def get_history(
        session_id
    ):

        chat_file = (
            ChatHistoryService.get_chat_file(
                session_id
            )
        )

        if not chat_file.exists():
            return []

        with open(
            chat_file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)