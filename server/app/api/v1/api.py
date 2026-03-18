from fastapi import APIRouter

from app.api.v1.endpoints import account, category, auth, user

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
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)
api_router.include_router(
    user.router,
    prefix="/me",
    tags=["me"]
)