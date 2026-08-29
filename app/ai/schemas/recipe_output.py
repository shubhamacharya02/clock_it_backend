from typing import Optional, List
from pydantic import BaseModel, Field

class ExtractedIngredient(BaseModel):
    raw_name: str = Field(..., description="Exact raw text name of ingredient as written in input source")
    canonical_name: str = Field(..., description="Standardized lowercase snake_case canonical ingredient key (e.g. milk, wheat_flour)")
    quantity: Optional[float] = Field(None, description="Numeric quantity if specified, else None")
    unit: Optional[str] = Field(None, description="Measurement unit if specified, else None")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Certainty score between 0.0 and 1.0")

class ExtractedRecipe(BaseModel):
    title: str = Field(..., description="Extracted recipe title")
    servings: Optional[int] = Field(None, description="Number of servings if specified")
    ingredients: List[ExtractedIngredient] = Field(default_factory=list, description="List of extracted recipe ingredients")
