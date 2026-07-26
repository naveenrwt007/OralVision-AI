from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def patient_document(
    patient_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Prepare a new patient document before inserting it into MongoDB.
    """

    current_time = datetime.now(timezone.utc)

    return {
        **patient_data,
        "total_reports": 0,
        "total_screenings": 0,
        "created_at": current_time,
        "updated_at": current_time,
    }


def serialize_patient(
    patient: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Convert a MongoDB patient document into an API-friendly dictionary.
    """

    if patient is None:
        return None

    serialized_patient = patient.copy()

    object_id = serialized_patient.pop("_id", None)

    if object_id is not None:
        serialized_patient["id"] = str(object_id)

    serialized_patient.setdefault("total_reports", 0)
    serialized_patient.setdefault("total_screenings", 0)

    return serialized_patient


def serialize_patients(
    patients: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Serialize a list of MongoDB patient documents.
    """

    return [
        serialized
        for patient in patients
        if (serialized := serialize_patient(patient)) is not None
    ]


def valid_object_id(value: str) -> bool:
    """
    Check whether a string is a valid MongoDB ObjectId.
    """

    return ObjectId.is_valid(value)