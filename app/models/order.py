import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import NUMERIC

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product_variant import ProductVariant

class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(..., foreign_key="users.id", index=True, nullable=False)
    order_number: str = Field(..., max_length=100, unique=True, index=True, nullable=False)
    total_amount: Decimal = Field(..., sa_column=Column(NUMERIC(10, 2), nullable=False))
    status: OrderStatus = Field(default=OrderStatus.CONFIRMED, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional["User"] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    order_id: uuid.UUID = Field(..., foreign_key="orders.id", index=True, nullable=False)
    variant_id: uuid.UUID = Field(..., foreign_key="product_variants.id", nullable=False)
    product_name_snapshot: str = Field(..., max_length=255, nullable=False)
    brand_snapshot: str = Field(..., max_length=255, nullable=False)
    size_snapshot: Decimal = Field(..., sa_column=Column(NUMERIC(10, 2), nullable=False))
    unit_snapshot: str = Field(..., max_length=50, nullable=False)
    unit_price_snapshot: Decimal = Field(..., sa_column=Column(NUMERIC(10, 2), nullable=False))
    quantity: int = Field(..., gt=0, nullable=False)
    line_total: Decimal = Field(..., sa_column=Column(NUMERIC(10, 2), nullable=False))

    order: Optional["Order"] = Relationship(back_populates="items")
    variant: Optional["ProductVariant"] = Relationship()
