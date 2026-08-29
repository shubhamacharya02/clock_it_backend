import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.cart_service import cart_service
from app.schemas.cart import CartItemAddRequest, CartItemUpdateRequest, CartResponse

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await cart_service.get_cart_with_items(user_id=current_user.id, db=db)

@router.post("/items", response_model=CartResponse)
async def add_cart_item(
    payload: CartItemAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await cart_service.add_item_to_cart(
        user_id=current_user.id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
        db=db
    )

@router.patch("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: uuid.UUID,
    payload: CartItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await cart_service.update_cart_item_quantity(
        user_id=current_user.id,
        item_id=item_id,
        quantity=payload.quantity,
        db=db
    )

@router.delete("/items/{item_id}", response_model=CartResponse)
async def delete_cart_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await cart_service.remove_cart_item(
        user_id=current_user.id,
        item_id=item_id,
        db=db
    )
