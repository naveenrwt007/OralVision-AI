import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------
# Directory paths
# ---------------------------------

CORE_DIR = Path(__file__).resolve().parent
APP_DIR = CORE_DIR.parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent


# Explicitly load backend/.env
ENV_FILE = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)


# ---------------------------------
# MongoDB configuration
# ---------------------------------

MONGODB_URL = os.getenv("MONGODB_URL")

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "oralscan_ai",
)

if not MONGODB_URL:
    raise RuntimeError(
        f"MONGODB_URL is missing. Check this file: {ENV_FILE}"
    )


# ---------------------------------
# Model path
# ---------------------------------

MODEL_PATH = (
    BACKEND_DIR
    / "models"
    / "efficientnet_b0_oral_cancer.pth"
)


# ---------------------------------
# Storage directories
# ---------------------------------

UPLOAD_DIR = BACKEND_DIR / "uploads"
OUTPUT_DIR = BACKEND_DIR / "outputs"

REPORT_DIR = BACKEND_DIR / "generated_reports"
REPORT_METADATA_DIR = BACKEND_DIR / "report_metadata"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_METADATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------
# API configuration
# ---------------------------------

REPORT_BASE_URL = os.getenv(
    "REPORT_BASE_URL",
    "http://127.0.0.1:8000",
)


# ---------------------------------
# Image configuration
# ---------------------------------

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

MAX_FILE_SIZE_MB = 10
IMAGE_SIZE = 224


# ---------------------------------
# Medical disclaimer
# ---------------------------------

MEDICAL_DISCLAIMER = (
    "This AI system provides preliminary screening support only. "
    "It does not diagnose oral cancer. A qualified dentist, doctor, "
    "or oral oncologist must perform clinical examination and biopsy "
    "when required."
)