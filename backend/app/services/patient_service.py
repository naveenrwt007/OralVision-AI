from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.core.database import patients_collection
from app.models.patient import (
    patient_document,
    serialize_patient,
    serialize_patients,
    valid_object_id,
)
from app.schemas.patient import PatientCreate, PatientUpdate


async def create_patient_record(
    payload: PatientCreate,
) -> dict:
    patient_data = payload.model_dump()
    document = patient_document(patient_data)

    result = await patients_collection.insert_one(document)

    created_patient = await patients_collection.find_one(
        {"_id": result.inserted_id}
    )

    return serialize_patient(created_patient)


async def list_patient_records(
    search: str | None = None,
    limit: int = 50,
    skip: int = 0,
) -> list[dict]:
    query: dict = {}

    if search:
        search_pattern = {
            "$regex": search,
            "$options": "i",
        }

        query = {
            "$or": [
                {"patient_name": search_pattern},
                {"phone": search_pattern},
                {"email": search_pattern},
                {"doctor_name": search_pattern},
                {"hospital_name": search_pattern},
            ]
        }

    cursor = (
        patients_collection
        .find(query)
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    patients = await cursor.to_list(length=limit)

    return serialize_patients(patients)


async def get_patient_by_id(
    patient_id: str,
) -> dict | None:
    if not valid_object_id(patient_id):
        return None

    patient = await patients_collection.find_one(
        {"_id": ObjectId(patient_id)}
    )

    return serialize_patient(patient)


async def update_patient_record(
    patient_id: str,
    payload: PatientUpdate,
) -> dict | None:
    if not valid_object_id(patient_id):
        return None

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not update_data:
        return await get_patient_by_id(patient_id)

    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await patients_collection.update_one(
        {"_id": ObjectId(patient_id)},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_patient = await patients_collection.find_one(
        {"_id": ObjectId(patient_id)}
    )

    return serialize_patient(updated_patient)


async def delete_patient_record(
    patient_id: str,
) -> bool:
    if not valid_object_id(patient_id):
        return False

    result = await patients_collection.delete_one(
        {"_id": ObjectId(patient_id)}
    )

    return result.deleted_count == 1


async def increment_patient_screening_count(
    patient_id: str,
) -> bool:
    if not valid_object_id(patient_id):
        return False

    result = await patients_collection.update_one(
        {"_id": ObjectId(patient_id)},
        {
            "$inc": {"total_screenings": 1},
            "$set": {
                "updated_at": datetime.now(timezone.utc)
            },
        },
    )

    return result.matched_count == 1


async def increment_patient_report_count(
    patient_id: str,
) -> bool:
    if not valid_object_id(patient_id):
        return False

    result = await patients_collection.update_one(
        {"_id": ObjectId(patient_id)},
        {
            "$inc": {"total_reports": 1},
            "$set": {
                "updated_at": datetime.now(timezone.utc)
            },
        },
    )

    return result.matched_count == 1


async def create_patient_indexes() -> None:
    await patients_collection.create_index(
        [("patient_name", ASCENDING)]
    )

    await patients_collection.create_index(
        [("phone", ASCENDING)]
    )

    await patients_collection.create_index(
        [("email", ASCENDING)]
    )

    await patients_collection.create_index(
        [("created_at", DESCENDING)]
    )