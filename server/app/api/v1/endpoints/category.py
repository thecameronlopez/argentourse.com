from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from sqlalchemy.orm import Session

from app.api.deps import get_current_user
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
    current_user: User = Depends(get_current_user)
):
    return CategoryService.create(
        db=db,
        user_id=current_user.id,
        data=payload
    )
    
    
@router.get("/", response_model=list[CategoryRead])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CategoryService.list(
        db=db,
        user_id=current_user.id
    )
    

@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = CategoryService.get(
        db=db,
        user_id=current_user.id,
        category_id=category_id
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = CategoryService.update(
        db=db,
        user_id=current_user.id,
        category_id=category_id,
        data=payload
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = CategoryService.delete(
        db=db,
        user_id=current_user.id,
        category_id=category_id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)