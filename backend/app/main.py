from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.history import router as history_router
from app.api.patients import router as patients_router
from app.api.report import router as report_router
from app.api.screening import router as screening_router
from app.api.search import router as search_router

from app.core.config import OUTPUT_DIR, REPORT_DIR
from app.core.database import check_database_connection
from app.core.startup import create_default_admin
from app.services.model_loader import DEVICE, MODEL


app = FastAPI(
    title="OralVision API",
    description=(
        "AI-assisted preliminary oral cancer "
        "screening API using EfficientNet-B0 "
        "and Grad-CAM."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://oral-vision-ai-cwkl.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/outputs",
    StaticFiles(directory=str(OUTPUT_DIR)),
    name="outputs",
)

app.mount(
    "/reports",
    StaticFiles(directory=str(REPORT_DIR)),
    name="reports",
)


app.include_router(auth_router)
app.include_router(screening_router)
app.include_router(report_router)
app.include_router(dashboard_router)
app.include_router(patients_router)
app.include_router(search_router)
app.include_router(history_router)


@app.get("/")
def root():
    return {
        "message": "OralVision API is running.",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    database_connected = await check_database_connection()

    return {
        "status": "healthy",
        "model_loaded": MODEL is not None,
        "device": str(DEVICE),
        "database_connected": database_connected,
    }

@app.on_event("startup")
async def startup():

    await create_default_admin()