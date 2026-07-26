from datetime import datetime, timezone
from typing import Any


def screening_document(
    screening_data: dict[str, Any],
) -> dict[str, Any]:
    return {
        **screening_data,
        "created_at": datetime.now(timezone.utc),
    }


def serialize_screening(
    screening: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if screening is None:
        return None

    serialized = screening.copy()

    object_id = serialized.pop("_id", None)

    if object_id is not None:
        serialized["id"] = str(object_id)

    patient_id = serialized.get("patient_id")

    if patient_id is not None:
        serialized["patient_id"] = str(patient_id)

    return serialized


def serialize_screenings(
    screenings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        serialized
        for item in screenings
        if (serialized := serialize_screening(item)) is not None
    ]