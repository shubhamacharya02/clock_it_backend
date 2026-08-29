import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import NUMERIC

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.inventory import Inventory

class ProductVariant(SQLModel, table=True):
    __tablename__ = "product_variants"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    product_id: uuid.UUID = Field(..., foreign_key="products.id", index=True, nullable=False)
    sku: str = Field(..., max_length=100, unique=True, index=True, nullable=False)
    size: Decimal = Field(..., sa_column=Column(NUMERIC(10, 2), nullable=False))
    size_unit: str = Field(..., max_length=50, nullable=False)
    price: Decimal = Field(..., sa_column=Column(NUMERIC(10, 2), nullable=False))
    is_active: bool = Field(default=True, nullable=False)

    product: Optional["Product"] = Relationship(back_populates="variants")
    inventory: Optional["Inventory"] = Relationship(back_populates="variant", sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"})
