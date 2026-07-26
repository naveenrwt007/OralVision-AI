from bson import ObjectId
from pymongo import DESCENDING

from app.core.database import (
    patients_collection,
    reports_collection,
    screenings_collection,
)
from app.models.patient import (
    serialize_patient,
    valid_object_id,
)
from app.models.screening import (
    screening_document,
    serialize_screening,
)
from app.schemas.history import ScreeningHistoryCreate
from app.services.patient_service import (
    increment_patient_screening_count,
)


def serialize_mongo_value(value):
    """
    Recursively convert MongoDB ObjectId values into strings.
    Handles dictionaries, lists, tuples, and nested data.
    """
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, dict):
        return {
            key: serialize_mongo_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            serialize_mongo_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            serialize_mongo_value(item)
            for item in value
        ]

    return value


def serialize_screening_record(
    screening: dict | None,
) -> dict | None:
    if screening is None:
        return None

    serialized = screening.copy()

    object_id = serialized.pop("_id", None)

    if object_id is not None:
        serialized["id"] = str(object_id)

    return serialize_mongo_value(serialized)


def serialize_screening_records(
    screenings: list[dict],
) -> list[dict]:
    return [
        serialize_screening_record(screening)
        for screening in screenings
        if screening is not None
    ]


def serialize_report(
    report: dict | None,
) -> dict | None:
    if report is None:
        return None

    serialized = report.copy()

    object_id = serialized.pop("_id", None)

    if object_id is not None:
        serialized["id"] = str(object_id)

    return serialize_mongo_value(serialized)


async def save_screening_history(
    payload: ScreeningHistoryCreate,
) -> dict | None:
    if not valid_object_id(payload.patient_id):
        return None

    patient_object_id = ObjectId(payload.patient_id)

    patient_exists = await patients_collection.find_one(
        {"_id": patient_object_id}
    )

    if patient_exists is None:
        return None

    screening_data = payload.model_dump()
    screening_data["patient_id"] = patient_object_id

    document = screening_document(screening_data)

    result = await screenings_collection.insert_one(
        document
    )

    await increment_patient_screening_count(
        payload.patient_id
    )

    created_screening = (
        await screenings_collection.find_one(
            {"_id": result.inserted_id}
        )
    )

    return serialize_screening_record(
        created_screening
    )


async def get_screening_by_id(
    screening_id: str,
) -> dict | None:
    if not valid_object_id(screening_id):
        return None

    screening = await screenings_collection.find_one(
        {"_id": ObjectId(screening_id)}
    )

    return serialize_screening_record(
        screening
    )


async def get_patient_screenings(
    patient_id: str,
    limit: int = 100,
) -> list[dict] | None:
    if not valid_object_id(patient_id):
        return None

    patient_object_id = ObjectId(patient_id)

    patient_exists = await patients_collection.find_one(
        {"_id": patient_object_id}
    )

    if patient_exists is None:
        return None

    cursor = (
        screenings_collection
        .find({"patient_id": patient_object_id})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )

    screenings = await cursor.to_list(
        length=limit
    )

    return serialize_screening_records(
        screenings
    )


async def get_patient_complete_history(
    patient_id: str,
) -> dict | None:
    if not valid_object_id(patient_id):
        return None

    patient_object_id = ObjectId(patient_id)

    patient = await patients_collection.find_one(
        {"_id": patient_object_id}
    )

    if patient is None:
        return None

    screening_cursor = (
        screenings_collection
        .find({"patient_id": patient_object_id})
        .sort("created_at", DESCENDING)
    )

    screenings = await screening_cursor.to_list(
        length=500
    )

    report_cursor = (
        reports_collection
        .find({"patient_id": patient_object_id})
        .sort("created_at", DESCENDING)
    )

    reports = await report_cursor.to_list(
        length=500
    )

    serialized_patient = serialize_patient(
        patient
    )

    serialized_screenings = (
        serialize_screening_records(
            screenings
        )
    )

    serialized_reports = [
        serialize_report(report)
        for report in reports
        if report is not None
    ]

    return {
        "patient": serialize_mongo_value(
            serialized_patient
        ),
        "screenings": serialized_screenings,
        "reports": serialized_reports,
        "total_screenings": len(
            serialized_screenings
        ),
        "total_reports": len(
            serialized_reports
        ),
    }


async def delete_screening_history(
    screening_id: str,
) -> bool:
    if not valid_object_id(screening_id):
        return False

    screening_object_id = ObjectId(
        screening_id
    )

    screening = await screenings_collection.find_one(
        {"_id": screening_object_id}
    )

    if screening is None:
        return False

    result = await screenings_collection.delete_one(
        {"_id": screening_object_id}
    )

    if result.deleted_count != 1:
        return False

    patient_id = screening.get(
        "patient_id"
    )

    if patient_id:
        await patients_collection.update_one(
            {"_id": patient_id},
            {
                "$inc": {
                    "total_screenings": -1,
                }
            },
        )

    return True