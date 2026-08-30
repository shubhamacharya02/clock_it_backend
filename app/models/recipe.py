import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.recipe_ingredient import RecipeIngredient

class SourceType(str, Enum):
    IMAGE = "image"
    CAMERA = "camera"
    TEXT = "text"
    URL = "url"
    VIDEO = "video"

class RecipeStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(..., foreign_key="users.id", index=True, nullable=False)
    title: str = Field(..., max_length=255, nullable=False)
    source_type: SourceType = Field(
        ...,
        sa_column=Column(String(), nullable=False)
    )
    source_url: Optional[str] = Field(None, max_length=1024)
    storage_path: Optional[str] = Field(None, max_length=1024)
    raw_content: Optional[str] = Field(None)
    status: RecipeStatus = Field(
        default=RecipeStatus.PROCESSING,
        sa_column=Column(String(), nullable=False, default=RecipeStatus.PROCESSING.value)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional["User"] = Relationship(back_populates="recipes")
    ingredients: List["RecipeIngredient"] = Relationship(back_populates="recipe", sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"})
