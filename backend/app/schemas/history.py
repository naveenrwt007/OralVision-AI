from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScreeningHistoryCreate(BaseModel):
    patient_id: str
    prediction: str
    confidence: float = Field(ge=0, le=1)
    confidence_percent: float = Field(ge=0, le=100)
    confidence_level: str

    probabilities: dict[str, float]
    image_quality: dict[str, Any] | None = None

    uploaded_image_url: str | None = None
    gradcam_url: str | None = None

    notes: str | None = None


class ScreeningHistoryResponse(ScreeningHistoryCreate):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientHistoryResponse(BaseModel):
    patient: dict[str, Any]
    screenings: list[dict[str, Any]]
    reports: list[dict[str, Any]]

    total_screenings: int
    total_reports: int