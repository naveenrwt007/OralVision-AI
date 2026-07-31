from datetime import datetime, timezone
from typing import Any
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

def patient_access_query(
    current_user: dict[str, Any],
) -> dict:
    user_role = str(
        current_user.get("role", "")
    ).strip().lower()

    user_id = str(
        current_user.get("_id", "")
    )

    # Admin can access all patients
    if user_role == "admin":
        return {}

    # Doctor/technician can access only their own patients
    return {
        "created_by": user_id
    }

async def create_patient_record(
    payload: PatientCreate,
    current_user: dict[str, Any],
) -> dict:
    patient_data = payload.model_dump()

    patient_data["created_by"] = str(
        current_user.get("_id", "")
    )

    patient_data["created_by_name"] = (
        current_user.get("name")
        or current_user.get("full_name")
        or "Unknown User"
    )

    patient_data["created_by_email"] = (
        current_user.get("email", "")
    )

    patient_data["created_by_role"] = str(
        current_user.get("role", "")
    ).strip().lower()

    document = patient_document(patient_data)

    result = await patients_collection.insert_one(
        document
    )

    created_patient = await patients_collection.find_one(
        {"_id": result.inserted_id}
    )

    await patients_collection.create_index(
        [
            ("created_by", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    return serialize_patient(created_patient)


async def list_patient_records(
    current_user: dict[str, Any],
    search: str | None = None,
    limit: int = 50,
    skip: int = 0,
) -> list[dict]:
    query = patient_access_query(current_user)

    if search:
        search_pattern = {
            "$regex": search,
            "$options": "i",
        }

        search_query = {
            "$or": [
                {"patient_name": search_pattern},
                {"phone": search_pattern},
                {"email": search_pattern},
                {"doctor_name": search_pattern},
                {"hospital_name": search_pattern},
            ]
        }

        if query:
            query = {
                "$and": [
                    query,
                    search_query,
                ]
            }
        else:
            query = search_query

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
    current_user: dict[str, Any],
) -> dict | None:
    if not valid_object_id(patient_id):
        return None

    query = {
        "_id": ObjectId(patient_id),
        **patient_access_query(current_user),
    }

    patient = await patients_collection.find_one(query)

    return serialize_patient(patient)


async def update_patient_record(
    patient_id: str,
    payload: PatientUpdate,
    current_user: dict[str, Any],
) -> dict | None:
    if not valid_object_id(patient_id):
        return None

    query = {
        "_id": ObjectId(patient_id),
        **patient_access_query(current_user),
    }

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not update_data:
        return await get_patient_by_id(
            patient_id,
            current_user,
        )

    # Ownership fields cannot be changed
    update_data.pop("created_by", None)
    update_data.pop("created_by_role", None)
    update_data.pop("created_by_email", None)
    update_data.pop("created_by_name", None)

    update_data["updated_at"] = datetime.now(
        timezone.utc
    )

    result = await patients_collection.update_one(
        query,
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_patient = await patients_collection.find_one(
        query
    )

    return serialize_patient(updated_patient)


async def update_patient_record(
    patient_id: str,
    payload: PatientUpdate,
    current_user: dict[str, Any],
) -> dict | None:
    if not valid_object_id(patient_id):
        return None

    query = {
        "_id": ObjectId(patient_id),
        **patient_access_query(current_user),
    }

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not update_data:
        return await get_patient_by_id(
            patient_id,
            current_user,
        )

    # Ownership fields cannot be changed
    update_data.pop("created_by", None)
    update_data.pop("created_by_role", None)
    update_data.pop("created_by_email", None)
    update_data.pop("created_by_name", None)

    update_data["updated_at"] = datetime.now(
        timezone.utc
    )

    result = await patients_collection.update_one(
        query,
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_patient = await patients_collection.find_one(
        query
    )

    return serialize_patient(updated_patient)


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