from fastapi import APIRouter

from app.api.v1.endpoints import accounts

api_router = APIRouter()

api_router.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["accounts"],
)