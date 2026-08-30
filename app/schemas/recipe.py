import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, model_validator
from app.models.recipe import SourceType, RecipeStatus

class RecipeTextRequest(BaseModel):
    title: Optional[str] = Field("Untitled Recipe", max_length=255)
    text: str = Field(..., min_length=2, description="Raw recipe text content or dish search query")

class RecipeURLRequest(BaseModel):
    url: Optional[str] = Field(None, description="Recipe webpage URL")
    video_url: Optional[str] = Field(None, description="Alternative URL key")

    @model_validator(mode="after")
    def resolve_url(self):
        target = self.url or self.video_url
        if not target:
            raise ValueError("url field is required.")
        self.url = target
        return self

class RecipeVideoRequest(BaseModel):
    video_url: Optional[str] = Field(None, description="YouTube video URL")
    url: Optional[str] = Field(None, description="Alternative URL key")

    @model_validator(mode="after")
    def resolve_video_url(self):
        target = self.video_url or self.url
        if not target:
            raise ValueError("video_url or url field is required.")
        self.video_url = target
        return self

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
    description: Optional[str] = "Butter Chicken is a beloved classic known for its rich harmony of aromatic spices and velvety textures. This recipe balances deeply infused flavors with simple, accessible cooking techniques."
    prep_time: Optional[str] = "15 mins"
    cook_time: Optional[str] = "25 mins"
    servings: Optional[int] = 4
    equipment_needed: List[str] = Field(default_factory=lambda: ["Heavy skillet / kadai", "Wooden stirring spatula", "Sharp chef's knife", "Prep bowls"])
    instructions: List[str] = Field(default_factory=lambda: [
        "Heat cooking oil or ghee over medium flame until shimmering. Drop in whole aromatics like cumin seeds and bay leaves, allowing them to crackle for about 30 seconds.",
        "Introduce finely minced onions, sautéing patiently until they reach a deep golden brown shade. Stir in ginger-garlic paste and fresh tomato puree, cooking until oil begins to separate around pan edges.",
        "Add ground coriander, turmeric, and chili powders, stirring continuously on low flame. Fold in boneless chicken, coating every piece thoroughly with the masala base.",
        "Cover skillet with a tight lid and allow chicken to simmer gently over low heat. Finish with a pinch of garam masala, heavy cream, and freshly chopped cilantro right before serving."
    ])
    serving_suggestions: Optional[str] = "Serve piping hot alongside steamed Basmati rice, butter garlic naan, or fresh tandoori roti. Garnish with a swirl of fresh cream or lemon wedges for bright contrast."
    source_type: SourceType
    source_url: Optional[str] = None
    storage_path: Optional[str] = None
    status: RecipeStatus
    ingredients: List[RecipeIngredientResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
