from fastapi import APIRouter, Query

from app.services.search_service import global_search_records

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search"],
)


@router.get("")
async def global_search(
    query: str = Query(
        ...,
        min_length=1,
        max_length=100,
    ),
):
    return await global_search_records(query)