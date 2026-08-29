import uuid
from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field
from app.models.order import OrderStatus

class OrderItemResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    variant_id: uuid.UUID
    product_name_snapshot: str
    brand_snapshot: str
    size_snapshot: Decimal
    unit_snapshot: str
    unit_price_snapshot: Decimal
    quantity: int
    line_total: Decimal

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    order_number: str
    total_amount: Decimal
    status: OrderStatus
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
