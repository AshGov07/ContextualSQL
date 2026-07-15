from fastapi import HTTPException
from pathlib import Path
import shutil

from app.config import SESSION_DIR


class FileManager:

    @staticmethod
    def save_file(session_id, file):

        session_folder = SESSION_DIR / session_id

        if not session_folder.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        upload_folder = session_folder / "uploads"

        upload_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = upload_folder / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        return str(file_path)