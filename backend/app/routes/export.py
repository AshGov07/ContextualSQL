from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

import pandas as pd

from app.config import BASE_DIR

router = APIRouter()

EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


class ExportRequest(BaseModel):
    rows: List[dict]


@router.post("/csv")
def export_csv(data: ExportRequest):

    df = pd.DataFrame(data.rows)

    file_path = EXPORT_DIR / "result.csv"

    df.to_csv(file_path, index=False)

    return FileResponse(
        str(file_path),
        filename="result.csv",
        media_type="text/csv"
    )


@router.post("/excel")
def export_excel(data: ExportRequest):

    df = pd.DataFrame(data.rows)

    file_path = EXPORT_DIR / "result.xlsx"

    df.to_excel(file_path, index=False)

    return FileResponse(
        str(file_path),
        filename="result.xlsx",
        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )