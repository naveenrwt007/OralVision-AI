from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


ALLOWED_GENDERS = {
    "Male",
    "Female",
    "Other",
    "Prefer not to say",
}


class PatientBase(BaseModel):
    patient_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Naveen Singh Rawat"],
    )

    age: int = Field(
        ...,
        ge=1,
        le=120,
        examples=[22],
    )

    gender: str = Field(
        ...,
        min_length=1,
        max_length=30,
        examples=["Male"],
    )

    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        examples=["9876543210"],
    )

    email: Optional[EmailStr] = Field(
        default=None,
        examples=["naveen@example.com"],
    )

    referred_by: Optional[str] = Field(
        default=None,
        max_length=100,
        examples=["Self"],
    )

    doctor_name: Optional[str] = Field(
        default=None,
        max_length=100,
        examples=["Dr. Sharma"],
    )

    hospital_name: Optional[str] = Field(
        default=None,
        max_length=150,
        examples=["OralScan Clinic"],
    )

    @field_validator(
        "patient_name",
        "gender",
        "referred_by",
        "doctor_name",
        "hospital_name",
        mode="before",
    )
    @classmethod
    def strip_text_fields(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("patient_name")
    @classmethod
    def validate_patient_name(cls, value: str) -> str:
        if not value.replace(" ", "").replace(".", "").isalpha():
            raise ValueError(
                "Patient name must contain only letters, spaces, and periods."
            )
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        normalized = value.strip().title()

        if normalized not in ALLOWED_GENDERS:
            raise ValueError(
                "Gender must be Male, Female, Other, or Prefer not to say."
            )

        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        cleaned = (
            value.strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if cleaned.startswith("+"):
            digits = cleaned[1:]
        else:
            digits = cleaned

        if not digits.isdigit():
            raise ValueError(
                "Phone number must contain only digits and an optional leading +."
            )

        if not 10 <= len(digits) <= 15:
            raise ValueError(
                "Phone number must contain between 10 and 15 digits."
            )

        return cleaned


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    patient_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    age: Optional[int] = Field(
        default=None,
        ge=1,
        le=120,
    )

    gender: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
    )

    email: Optional[EmailStr] = None

    referred_by: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    doctor_name: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    hospital_name: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    @field_validator(
        "patient_name",
        "gender",
        "referred_by",
        "doctor_name",
        "hospital_name",
        mode="before",
    )
    @classmethod
    def strip_text_fields(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("patient_name")
    @classmethod
    def validate_patient_name(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        if not value.replace(" ", "").replace(".", "").isalpha():
            raise ValueError(
                "Patient name must contain only letters, spaces, and periods."
            )

        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip().title()

        if normalized not in ALLOWED_GENDERS:
            raise ValueError(
                "Gender must be Male, Female, Other, or Prefer not to say."
            )

        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        cleaned = (
            value.strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if cleaned.startswith("+"):
            digits = cleaned[1:]
        else:
            digits = cleaned

        if not digits.isdigit():
            raise ValueError(
                "Phone number must contain only digits and an optional leading +."
            )

        if not 10 <= len(digits) <= 15:
            raise ValueError(
                "Phone number must contain between 10 and 15 digits."
            )

        return cleaned

    model_config = ConfigDict(
        extra="forbid",
    )


class PatientResponse(PatientBase):
    id: str

    total_reports: int = Field(default=0, ge=0)
    total_screenings: int = Field(default=0, ge=0)

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )