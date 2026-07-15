from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from app.services.settings_service import SettingsService

router = APIRouter()

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

@router.get("")
def get_settings():
    return SettingsService.get_masked_settings()

@router.post("")
def update_settings(payload: SettingsUpdateRequest):
    updated = SettingsService.save_settings(payload.settings)
    return SettingsService.get_masked_settings()
