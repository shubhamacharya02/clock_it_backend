import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.recipe import Recipe

class RecipeIngredient(SQLModel, table=True):
    __tablename__ = "recipe_ingredients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    recipe_id: uuid.UUID = Field(..., foreign_key="recipes.id", index=True, nullable=False)
    raw_name: str = Field(..., max_length=255, nullable=False)
    canonical_name: str = Field(..., max_length=255, index=True, nullable=False)
    quantity: Optional[float] = Field(None)
    unit: Optional[str] = Field(None, max_length=50)
    confidence: float = Field(..., ge=0.0, le=1.0, nullable=False)
    requires_confirmation: bool = Field(default=False, nullable=False)
    is_user_modified: bool = Field(default=False, nullable=False)

    recipe: Optional["Recipe"] = Relationship(back_populates="ingredients")
