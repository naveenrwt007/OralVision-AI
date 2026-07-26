from fastapi import APIRouter

from app.services.dashboard_service import (
    get_dashboard_statistics,
)


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/stats",
    summary="Get dashboard and analytics statistics",
)
async def dashboard_stats():
    return await get_dashboard_statistics()