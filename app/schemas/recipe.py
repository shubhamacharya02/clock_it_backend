import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from app.models.recipe import SourceType, RecipeStatus

class RecipeTextRequest(BaseModel):
    title: Optional[str] = Field("Untitled Recipe", max_length=255)
    text: str = Field(..., min_length=10, description="Raw recipe text content")

class RecipeURLRequest(BaseModel):
    url: str = Field(..., description="Recipe webpage URL")

class RecipeVideoRequest(BaseModel):
    video_url: str = Field(..., description="YouTube video URL")

class IngredientUpdateRequest(BaseModel):
    id: uuid.UUID
    raw_name: Optional[str] = None
    canonical_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None

class IngredientUpdatesPayload(BaseModel):
    ingredients: List[IngredientUpdateRequest]

class RecipeIngredientResponse(BaseModel):
    id: uuid.UUID
    raw_name: str
    canonical_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    confidence: float
    requires_confirmation: bool
    is_user_modified: bool

    class Config:
        from_attributes = True

class RecipeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    source_type: SourceType
    source_url: Optional[str] = None
    storage_path: Optional[str] = None
    status: RecipeStatus
    ingredients: List[RecipeIngredientResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
