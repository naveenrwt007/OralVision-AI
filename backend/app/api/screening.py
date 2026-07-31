from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.core.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_FILE_SIZE_MB,
)
from app.core.database import (
    patients_collection,
    screenings_collection,
)
from app.core.dependencies import get_current_technician
from app.models.patient import valid_object_id
from app.schemas.screening import ScreeningResponse
from app.services.image_quality import (
    assess_image_quality,
    validate_image_bytes,
)
from app.services.prediction import run_screening


router = APIRouter(
    prefix="/api/v1/screening",
    tags=["Screening"],
)


@router.post(
    "/predict",
    response_model=ScreeningResponse,
    status_code=status.HTTP_201_CREATED,
)
async def predict_oral_image(
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    current_user: dict[str, Any] = Depends(
        get_current_technician
    ),
):
    """
    Run AI-based oral screening and save the result.

    Allowed roles:
    - Admin
    - Doctor
    - Technician
    """

    filename = file.filename or "uploaded_image"
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. "
                "Upload JPG, JPEG, PNG, BMP, or WEBP."
            ),
        )

    if not valid_object_id(patient_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid patient_id is required.",
        )

    patient_object_id = ObjectId(patient_id)

    current_user_id = str(
        current_user.get("_id", "")
    )

    current_user_role = str(
        current_user.get("role", "")
    ).strip().lower()

    patient_query = {
        "_id": patient_object_id
    }

    if current_user_role != "admin":
        patient_query["created_by"] = current_user_id

    patient = await patients_collection.find_one(
        patient_query
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found.",
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is empty.",
        )

    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    if len(image_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE_MB} MB.",
        )

    try:
        image = validate_image_bytes(image_bytes)

        image_quality = assess_image_quality(image)

        screening_result = run_screening(image)

        screening_result["image_quality"] = image_quality

        now = datetime.now(timezone.utc)

        current_user_id = str(
            current_user.get("_id", "")
        )

        current_user_name = (
            current_user.get("name")
            or current_user.get("full_name")
            or "Unknown User"
        )

        current_user_email = current_user.get(
            "email",
            "",
        )

        current_user_role = str(
            current_user.get("role", "")
        ).strip().lower()

        patient_name = (
            patient.get("patient_name")
            or patient.get("name")
            or "Unknown Patient"
        )

        screening_document = {
            "patient_id": patient_object_id,
            "patient_name": patient_name,

            "owner_id": patient.get("created_by", current_user_id),
            "prediction": screening_result.get(
                "prediction"
            ),
            "confidence": screening_result.get(
                "confidence"
            ),
            "confidence_percent": screening_result.get(
                "confidence_percent"
            ),
            "confidence_level": screening_result.get(
                "confidence_level"
            ),
            "probabilities": screening_result.get(
                "probabilities",
                {},
            ),

            "image_quality": image_quality,
            "gradcam": screening_result.get("gradcam"),

            "message": screening_result.get("message"),
            "disclaimer": screening_result.get(
                "disclaimer"
            ),

            "original_filename": filename,

            "report_id": None,
            "report_download_url": None,

            "status": "active",
            "is_archived": False,

            "screened_by": current_user_id,
            "screened_by_name": current_user_name,
            "screened_by_email": current_user_email,
            "screened_by_role": current_user_role,

            "created_at": now,
            "updated_at": now,
        }

        insert_result = (
            await screenings_collection.insert_one(
                screening_document
            )
        )

        screening_id = str(
            insert_result.inserted_id
        )

        await patients_collection.update_one(
            patient_query,
            {
                "$inc": {
                    "total_screenings": 1,
                },
                "$set": {
                    "last_screening_at": now,
                    "updated_at": now,
                },
            },
        )

        screening_result["screening_id"] = (
            screening_id
        )

        screening_result["patient_id"] = patient_id
        screening_result["patient_name"] = patient_name

        screening_result["performed_by"] = {
            "id": current_user_id,
            "name": current_user_name,
            "email": current_user_email,
            "role": current_user_role,
        }

        screening_result["created_at"] = (
            now.isoformat()
        )

        return screening_result

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening failed: {error}",
        ) from error

    finally:
        await file.close()