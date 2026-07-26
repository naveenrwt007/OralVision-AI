from typing import Dict, List

from pydantic import BaseModel


class ImageQualityResponse(BaseModel):
    status: str
    width: int
    height: int
    blur_score: float
    issues: List[str]


class GradCAMResponse(BaseModel):
    filename: str
    path: str
    url: str


class ScreeningResponse(BaseModel):
    prediction: str
    confidence: float
    confidence_percent: float
    confidence_level: str
    probabilities: Dict[str, float]
    message: str
    disclaimer: str
    image_quality: ImageQualityResponse
    gradcam: GradCAMResponse


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str