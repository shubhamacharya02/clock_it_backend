import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product_variant import ProductVariant

class CartStatus(str, Enum):
    ACTIVE = "active"
    CONVERTED = "converted"
    ABANDONED = "abandoned"

class Cart(SQLModel, table=True):
    __tablename__ = "carts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(..., foreign_key="users.id", index=True, nullable=False)
    status: CartStatus = Field(default=CartStatus.ACTIVE, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional["User"] = Relationship(back_populates="carts")
    items: List["CartItem"] = Relationship(back_populates="cart", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id", name="uq_cart_items_cart_variant"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    cart_id: uuid.UUID = Field(..., foreign_key="carts.id", index=True, nullable=False)
    variant_id: uuid.UUID = Field(..., foreign_key="product_variants.id", index=True, nullable=False)
    quantity: int = Field(default=1, gt=0, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    cart: Optional["Cart"] = Relationship(back_populates="items")
    variant: Optional["ProductVariant"] = Relationship()
