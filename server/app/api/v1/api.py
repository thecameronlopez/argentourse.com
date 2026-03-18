from fastapi import APIRouter

from server.app.api.v1.endpoints import account, category

api_router = APIRouter()

api_router.include_router(
    account.router,
    prefix="/accounts",
    tags=["accounts"],
)
api_router.include_router(
    category.router,
    prefix="/categories",
    tags=["categories"]
)