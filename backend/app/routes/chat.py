from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_history_service import (
    ChatHistoryService
)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/{session_id}")
def send_message(
    session_id: str,
    payload: ChatRequest
):

    ChatHistoryService.save_message(
        session_id,
        "user",
        payload.message
    )

    return {
        "message": "saved"
    }


@router.get("/{session_id}")
def get_history(
    session_id: str
):

    return ChatHistoryService.get_history(
        session_id
    )