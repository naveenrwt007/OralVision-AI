from pydantic import BaseModel


class ReportResponse(BaseModel):
    report_id: str
    generated_at: str
    filename: str
    url: str
    download_url: str
    verification_url: str


class ReportVerificationResponse(BaseModel):
    valid: bool
    report_id: str
    generated_at: str
    prediction: str | None = None
    confidence_percent: float | None = None
    patient_name: str | None = None
    message: str