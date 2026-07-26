import json
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from pymongo import DESCENDING

from app.core.config import REPORT_METADATA_DIR
from app.core.database import (
    patients_collection,
    reports_collection,
    screenings_collection,
)
from app.models.patient import valid_object_id
from app.schemas.report import (
    ReportResponse,
    ReportVerificationResponse,
)
from app.services.report_generator import generate_screening_report


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
)


def _as_dict(value) -> dict:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    raise ValueError(
        "Report generator returned an unsupported response type."
    )


def _serialize_report(report: dict) -> dict:
    item = report.copy()

    object_id = item.pop("_id", None)
    if object_id is not None:
        item["id"] = str(object_id)

    patient_id = item.get("patient_id")
    if isinstance(patient_id, ObjectId):
        item["patient_id"] = str(patient_id)

    screening_id = item.get("screening_id")
    if isinstance(screening_id, ObjectId):
        item["screening_id"] = str(screening_id)

    return item


@router.get("")
async def list_reports(
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    query: dict = {}

    if search and search.strip():
        pattern = search.strip()

        query = {
            "$or": [
                {
                    "report_id": {
                        "$regex": pattern,
                        "$options": "i",
                    }
                },
                {
                    "patient_name": {
                        "$regex": pattern,
                        "$options": "i",
                    }
                },
                {
                    "prediction": {
                        "$regex": pattern,
                        "$options": "i",
                    }
                },
            ]
        }

        if valid_object_id(pattern):
            query["$or"].append(
                {"patient_id": ObjectId(pattern)}
            )

    cursor = (
        reports_collection
        .find(query)
        .sort("created_at", DESCENDING)
        .limit(limit)
    )

    reports = await cursor.to_list(length=limit)

    return {
        "reports": [
            _serialize_report(report)
            for report in reports
        ],
        "count": len(reports),
    }


@router.post(
    "/generate",
    response_model=ReportResponse,
)
async def generate_report(
    file: UploadFile = File(...),
    screening_result: str = Form(...),
    patient_name: str = Form(...),
    patient_age: str = Form(""),
    patient_gender: str = Form(""),
    patient_phone: str = Form(""),
    patient_id: str = Form(...),
    referred_by: str = Form(""),
    doctor_name: str = Form(""),
    hospital_name: str = Form("OralScan AI"),
):
    try:
        if not valid_object_id(patient_id):
            raise HTTPException(
                status_code=400,
                detail="A valid patient_id is required.",
            )

        patient_object_id = ObjectId(patient_id)

        patient_record = await patients_collection.find_one(
            {"_id": patient_object_id}
        )

        if patient_record is None:
            raise HTTPException(
                status_code=404,
                detail="Patient record was not found.",
            )

        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded image is empty.",
            )

        try:
            parsed_result = json.loads(screening_result)
        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=400,
                detail="Invalid screening-result JSON.",
            ) from error

        patient = {
            "name": patient_name,
            "age": patient_age,
            "gender": patient_gender,
            "phone": patient_phone,
            "patient_id": patient_id,
            "referred_by": referred_by,
        }

        generated = generate_screening_report(
            patient=patient,
            screening_result=parsed_result,
            original_image_bytes=image_bytes,
            doctor_name=doctor_name,
            hospital_name=hospital_name,
        )

        generated_data = _as_dict(generated)

        report_id = generated_data.get("report_id")
        if not report_id:
            raise ValueError(
                "Generated report does not contain report_id."
            )

        now = datetime.now(timezone.utc)

        # Link the report to the most recent screening for this patient.
        latest_screening = await screenings_collection.find_one(
            {"patient_id": patient_object_id},
            sort=[("created_at", DESCENDING)],
        )

        screening_object_id = (
            latest_screening.get("_id")
            if latest_screening
            else None
        )

        report_document = {
            "report_id": report_id,
            "patient_id": patient_object_id,
            "screening_id": screening_object_id,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "patient_phone": patient_phone,
            "referred_by": referred_by or None,
            "doctor_name": doctor_name or None,
            "hospital_name": hospital_name or "OralScan AI",
            "prediction": parsed_result.get("prediction"),
            "confidence": parsed_result.get("confidence"),
            "confidence_percent": parsed_result.get(
                "confidence_percent"
            ),
            "download_url": generated_data.get("download_url"),
            "verification_url": generated_data.get(
                "verification_url"
            ),
            "generated_at": generated_data.get(
                "generated_at",
                now,
            ),
            "created_at": now,
            "updated_at": now,
        }

        existing_report = await reports_collection.find_one(
            {"report_id": report_id}
        )

        if existing_report is None:
            await reports_collection.insert_one(
                report_document
            )

            await patients_collection.update_one(
                {"_id": patient_object_id},
                {
                    "$inc": {"total_reports": 1},
                    "$set": {"updated_at": now},
                },
            )

        if screening_object_id is not None:
            await screenings_collection.update_one(
                {"_id": screening_object_id},
                {
                    "$set": {
                        "report_id": report_id,
                        "report_download_url": (
                            generated_data.get("download_url")
                        ),
                        "updated_at": now,
                    }
                },
            )

        return generated_data

    except HTTPException:
        raise

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {error}",
        ) from error


@router.get(
    "/{report_id}/verify",
    response_model=ReportVerificationResponse,
)
def verify_report(
    report_id: str,
):
    safe_report_id = Path(report_id).name.upper()

    metadata_path = (
        REPORT_METADATA_DIR
        / f"{safe_report_id}.json"
    )

    if not metadata_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report ID was not found.",
        )

    try:
        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        patient = metadata.get("patient", {})

        return {
            "valid": True,
            "report_id": metadata["report_id"],
            "generated_at": metadata["generated_at"],
            "prediction": metadata.get("prediction"),
            "confidence_percent": metadata.get(
                "confidence_percent"
            ),
            "patient_name": patient.get("name"),
            "message": (
                "This OralScan AI report exists and "
                "its report ID is valid."
            ),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "The report metadata could not be read."
            ),
        ) from error