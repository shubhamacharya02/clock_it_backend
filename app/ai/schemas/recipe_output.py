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
    description: Optional[str] = Field("A beloved classic dish known for its rich harmony of aromatic spices and velvety textures. This recipe balances deeply infused flavors with simple, accessible cooking techniques.", description="Rich 2-3 sentence overview of dish and flavor profile")
    prep_time: Optional[str] = Field("15 mins", description="Estimated preparation time")
    cook_time: Optional[str] = Field("25 mins", description="Estimated cooking time")
    servings: Optional[int] = Field(4, description="Servings count")
    equipment_needed: List[str] = Field(default_factory=lambda: ["Heavy skillet / kadai", "Wooden stirring spatula", "Sharp chef's knife", "Prep bowls"], description="Key cookware and kitchen prep tools")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step detailed cooking instructions")
    serving_suggestions: Optional[str] = Field("Serve piping hot alongside steamed Basmati rice, butter garlic naan, or fresh tandoori roti. Garnish with a swirl of fresh cream or lemon wedges for bright contrast.", description="Garnishing & serving suggestions")
    ingredients: List[ExtractedIngredient] = Field(default_factory=list, description="List of extracted recipe ingredients")
