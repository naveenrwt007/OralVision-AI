from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from app.services.patient_service import (
    create_patient_record,
    delete_patient_record,
    get_patient_by_id,
    list_patient_records,
    update_patient_record,
)

router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"],
)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(payload: PatientCreate):
    patient = await create_patient_record(payload)

    if not patient:
        raise HTTPException(
            status_code=500,
            detail="Unable to create patient.",
        )

    return patient


@router.get(
    "",
    response_model=list[PatientResponse],
)
async def get_patients(
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
):
    return await list_patient_records(
        search=search,
        limit=limit,
        skip=skip,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
async def get_patient(patient_id: str):
    patient = await get_patient_by_id(patient_id)

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found.",
        )

    return patient


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
)
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
):
    patient = await update_patient_record(
        patient_id,
        payload,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found.",
        )

    return patient


@router.delete(
    "/{patient_id}",
)
async def delete_patient(patient_id: str):
    deleted = await delete_patient_record(patient_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Patient not found.",
        )

    return {
        "message": "Patient deleted successfully.",
        "patient_id": patient_id,
    }