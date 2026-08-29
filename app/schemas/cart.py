import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.cart import CartStatus

class CartItemAddRequest(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(..., gt=0, description="Quantity must be integer >= 1")

class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity must be integer >= 1")

class CartItemResponse(BaseModel):
    id: uuid.UUID
    cart_id: uuid.UUID
    variant_id: uuid.UUID
    sku: str
    product_name: str
    brand: str
    size: Decimal
    size_unit: str
    unit_price: Decimal
    quantity: int
    line_subtotal: Decimal
    available_quantity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: CartStatus
    items: List[CartItemResponse] = []
    grand_total: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
