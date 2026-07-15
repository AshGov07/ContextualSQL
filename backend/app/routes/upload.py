from fastapi import APIRouter, UploadFile, File, Header, Query
from fastapi.responses import JSONResponse

from app.services.file_manager import FileManager
from app.services.upload_processor import UploadProcessor
from app.services.schema_embedding_service import (
    SchemaEmbeddingService
)

router = APIRouter()



@router.post("/{session_id}")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...)
):

    file_path = FileManager.save_file(
        session_id,
        file
    )

    UploadProcessor.process_file(
        session_id,
        file_path
    )

    SchemaEmbeddingService.build_vector_store(
        session_id
    )

    return {
        "message": "uploaded",
        "file": file.filename
    }


@router.post("/sync/{session_id}")
def sync_database(
    session_id: str,
    offset: int = Query(0),
    limit: int = Query(50),
    force_provider: str = Query(None),
    x_gemini_key: str = Header(None)
):
    try:
        result = SchemaEmbeddingService.build_vector_store(
            session_id,
            offset=offset,
            limit=limit,
            temp_gemini_key=x_gemini_key,
            force_provider=force_provider
        )
        return {
            "status": "success",
            "processed": result["processed"],
            "total": result["total"],
            "offset": result["offset"]
        }
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
            from app.services.schema_service import SchemaService
            try:
                total_tables = len(SchemaService.get_schema(session_id))
            except:
                total_tables = 0
            return JSONResponse(
                status_code=429,
                content={
                    "status": "rate_limit_exceeded",
                    "offset": offset,
                    "total": total_tables,
                    "message": "Gemini API rate limit exceeded."
                }
            )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": err_msg
            }
        )


    