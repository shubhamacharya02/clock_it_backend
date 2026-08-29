import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from app.models.product_variant import ProductVariant

class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    name: str = Field(..., max_length=255, nullable=False)
    brand: str = Field(..., max_length=255, index=True, nullable=False)
    category: str = Field(..., max_length=255, index=True, nullable=False)
    description: Optional[str] = Field(None)
    metadata_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    is_active: bool = Field(default=True, nullable=False)

    variants: List["ProductVariant"] = Relationship(back_populates="product", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
