from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.history import (
    PatientHistoryResponse,
    ScreeningHistoryCreate,
    ScreeningHistoryResponse,
)
from app.services.screening_history_service import (
    delete_screening_history,
    get_patient_complete_history,
    get_patient_screenings,
    get_screening_by_id,
    save_screening_history,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Screening History"],
)


@router.post(
    "/screenings/history",
    response_model=ScreeningHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_screening_history(
    payload: ScreeningHistoryCreate,
):
    screening = await save_screening_history(payload)

    if screening is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found or patient ID is invalid.",
        )

    return screening


@router.get(
    "/screenings/history/{screening_id}",
    response_model=ScreeningHistoryResponse,
)
async def read_screening_history(screening_id: str):
    screening = await get_screening_by_id(screening_id)

    if screening is None:
        raise HTTPException(
            status_code=404,
            detail="Screening record not found.",
        )

    return screening


@router.get(
    "/patients/{patient_id}/screenings",
    response_model=list[ScreeningHistoryResponse],
)
async def read_patient_screenings(
    patient_id: str,
    limit: int = Query(default=100, ge=1, le=500),
):
    screenings = await get_patient_screenings(
        patient_id=patient_id,
        limit=limit,
    )

    if screenings is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found or patient ID is invalid.",
        )

    return screenings


@router.get(
    "/patients/{patient_id}/history",
    response_model=PatientHistoryResponse,
)
async def read_patient_history(patient_id: str):
    history = await get_patient_complete_history(patient_id)

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found or patient ID is invalid.",
        )

    return history


@router.delete("/screenings/history/{screening_id}")
async def remove_screening_history(screening_id: str):
    deleted = await delete_screening_history(screening_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Screening record not found.",
        )

    return {
        "message": "Screening history deleted successfully.",
        "screening_id": screening_id,
    }