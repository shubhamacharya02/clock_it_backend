from typing import Optional, List
from pydantic import BaseModel, Field, model_validator

class ExtractedIngredient(BaseModel):
    raw_name: str = Field(..., description="Exact raw text name of ingredient")
    canonical_name: str = Field(..., description="Standardized lowercase snake_case canonical ingredient key")
    quantity: Optional[float] = Field(None, description="Numeric quantity as float")
    unit: Optional[str] = Field(None, description="Measurement unit")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Certainty score")

    @model_validator(mode="before")
    def resolve_ingredient_fields(cls, values):
        if isinstance(values, dict):
            raw = values.get("raw_name") or values.get("item") or values.get("name") or values.get("ingredient") or values.get("canonical_name") or "Ingredient"
            canon = values.get("canonical_name") or str(raw).lower().replace(" ", "_").strip()
            values["raw_name"] = str(raw)
            values["canonical_name"] = str(canon).lower().strip()
        return values

class ExtractedRecipe(BaseModel):
    title: str = Field(..., description="Extracted recipe title")
    description: Optional[str] = Field(None, description="Detailed 2-3 sentence overview of dish")
    prep_time: Optional[str] = Field("15 mins", description="Preparation time")
    cook_time: Optional[str] = Field("25 mins", description="Cooking time")
    servings: Optional[int] = Field(4, description="Servings count")
    equipment_needed: List[str] = Field(default_factory=list, description="Key cookware and tools")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step cooking instructions")
    serving_suggestions: Optional[str] = Field(None, description="Garnishing & serving suggestions")
    ingredients: List[ExtractedIngredient] = Field(default_factory=list, description="List of ingredients")

    @model_validator(mode="before")
    def resolve_recipe_fields(cls, values):
        if isinstance(values, dict):
            if not values.get("title"):
                values["title"] = values.get("recipe_title") or values.get("name") or "Recipe Guide"
            if not values.get("equipment_needed"):
                values["equipment_needed"] = values.get("equipment") or values.get("tools") or []

            raw_insts = values.get("instructions") or values.get("steps") or values.get("directions") or []
            clean_insts = []
            if isinstance(raw_insts, list):
                for item in raw_insts:
                    if isinstance(item, dict):
                        text = item.get("description") or item.get("text") or item.get("step") or str(item)
                        clean_insts.append(str(text))
                    else:
                        clean_insts.append(str(item))
            values["instructions"] = clean_insts

            raw_ings = values.get("ingredients") or values.get("recipe_ingredients") or values.get("ingredient_list") or []
            values["ingredients"] = raw_ings
        return values
