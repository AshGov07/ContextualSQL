from fastapi import APIRouter

from app.services.schema_service import (
    SchemaService
)

router = APIRouter()


@router.get("/{session_id}")
def get_schema(
    session_id: str
):

    return SchemaService.get_schema(
        session_id
    )