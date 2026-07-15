import uuid
import json
from pathlib import Path

from app.config import SESSION_DIR


class SessionManager:

    @staticmethod
    def create_session(name: str):

        session_id = str(uuid.uuid4())

        session_folder = SESSION_DIR / session_id
        session_folder.mkdir(exist_ok=True)

        metadata = {
            "session_id": session_id,
            "name": name
        }

        with open(
            session_folder / "metadata.json",
            "w"
        ) as f:
            json.dump(metadata, f, indent=4)

        return metadata

    @staticmethod
    def list_sessions():

        sessions = []

        for folder in SESSION_DIR.iterdir():

            if folder.is_dir():

                meta_file = folder / "metadata.json"

                if meta_file.exists():

                    with open(meta_file) as f:
                        sessions.append(json.load(f))

        return sessions