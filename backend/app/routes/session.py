from fastapi import APIRouter

from app.models.session_model import SessionCreate
from app.services.session_manager import SessionManager

router = APIRouter()


@router.post("/create")
def create_session(
    payload: SessionCreate
):
    return SessionManager.create_session(
        payload.name
    )


@router.get("/list")
def list_sessions():
    return SessionManager.list_sessions()