from bson import ObjectId

from app.core.database import (
    patients_collection,
    reports_collection,
    screenings_collection,
)
from app.models.patient import serialize_patients


def serialize_mongo(document):
    """
    Convert every ObjectId inside a MongoDB document into strings.
    """

    if isinstance(document, ObjectId):
        return str(document)

    if isinstance(document, dict):
        return {
            key: serialize_mongo(value)
            for key, value in document.items()
        }

    if isinstance(document, list):
        return [
            serialize_mongo(item)
            for item in document
        ]

    return document


async def global_search_records(query: str):
    regex = {
        "$regex": query,
        "$options": "i",
    }

    # -------------------------
    # Patients
    # -------------------------
    patient_cursor = (
        patients_collection.find(
            {
                "$or": [
                    {"patient_name": regex},
                    {"phone": regex},
                    {"email": regex},
                    {"doctor_name": regex},
                    {"hospital_name": regex},
                ]
            }
        )
        .limit(20)
    )

    patients = await patient_cursor.to_list(length=20)

    # -------------------------
    # Reports
    # -------------------------
    report_cursor = (
        reports_collection.find(
            {
                "$or": [
                    {"report_id": regex},
                    {"patient_name": regex},
                    {"prediction": regex},
                ]
            }
        )
        .limit(20)
    )

    reports = await report_cursor.to_list(length=20)

    # -------------------------
    # Screenings
    # -------------------------
    screening_cursor = (
        screenings_collection.find(
            {
                "$or": [
                    {"prediction": regex},
                    {"patient_name": regex},
                ]
            }
        )
        .limit(20)
    )

    screenings = await screening_cursor.to_list(length=20)

    # Serialize all MongoDB documents
    reports = [
        serialize_mongo(report)
        for report in reports
    ]

    screenings = [
        serialize_mongo(screening)
        for screening in screenings
    ]

    return {
        "patients": serialize_patients(patients),
        "reports": reports,
        "screenings": screenings,
        "total_results": (
            len(patients)
            + len(reports)
            + len(screenings)
        ),
    }