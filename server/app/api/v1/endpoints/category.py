from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from sqlalchemy.orm import Session

from app.api.deps import current_user, require_csrf
from app.core.db import get_db
from app.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.base_service import BaseService
from app.models import User, Category

router = APIRouter()


class CategoryService(BaseService[Category, CategoryCreate, CategoryUpdate]):
    model = Category
    

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    return CategoryService.create(
        db=db,
        user_id=current_user.id,
        data=payload
    )
    
    
@router.get("/", response_model=list[CategoryRead])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user)
):
    return CategoryService.list(
        db=db,
        user_id=current_user.id
    )
    

@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user)
):
    return CategoryService.get(
        db=db,
        user_id=current_user.id,
        item_id=category_id
    )


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    return CategoryService.update(
        db=db,
        user_id=current_user.id,
        item_id=category_id,
        data=payload
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user),
    _: None = Depends(require_csrf)
):
    CategoryService.delete(
        db=db,
        user_id=current_user.id,
        item_id=category_id
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)