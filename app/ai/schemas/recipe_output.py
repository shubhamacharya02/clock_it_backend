from typing import Optional, List
from pydantic import BaseModel, Field

class ExtractedIngredient(BaseModel):
    raw_name: str = Field(..., description="Exact raw text name of ingredient")
    canonical_name: str = Field(..., description="Standardized lowercase snake_case canonical ingredient key")
    quantity: Optional[float] = Field(None, description="Numeric quantity as float")
    unit: Optional[str] = Field(None, description="Measurement unit")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Certainty score")

class ExtractedRecipe(BaseModel):
    title: str = Field(..., description="Extracted recipe title")
    description: Optional[str] = Field(None, description="Detailed 2-3 sentence overview of dish and flavor profile")
    prep_time: Optional[str] = Field("15 mins", description="Preparation time")
    cook_time: Optional[str] = Field("25 mins", description="Cooking time")
    servings: Optional[int] = Field(4, description="Servings count")
    equipment_needed: List[str] = Field(default_factory=list, description="Key cookware and tools")
    instructions: List[str] = Field(default_factory=list, description="List of plain string cooking steps. Do NOT output objects or key-value pairs.")
    serving_suggestions: Optional[str] = Field(None, description="Garnishing & serving suggestions")
    ingredients: List[ExtractedIngredient] = Field(default_factory=list, description="List of ingredients")
