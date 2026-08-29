import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.product_variant import ProductVariant

class Inventory(SQLModel, table=True):
    __tablename__ = "inventory"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    variant_id: uuid.UUID = Field(..., foreign_key="product_variants.id", unique=True, index=True, nullable=False)
    available_quantity: int = Field(default=0, ge=0, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    variant: Optional["ProductVariant"] = Relationship(back_populates="inventory")
