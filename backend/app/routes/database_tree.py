from fastapi import APIRouter

from app.services.database_tree_service import (
    DatabaseTreeService
)

router = APIRouter()


@router.get("/{session_id}")
def get_database_tree(
    session_id: str
):

    return DatabaseTreeService.get_tree(
        session_id
    )