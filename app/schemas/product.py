import uuid
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

class VariantMatchResponse(BaseModel):
    variant_id: uuid.UUID
    sku: str
    size: Decimal
    size_unit: str
    price: Decimal
    available_quantity: int
    is_alternative: bool = False
    alternative_reason: Optional[str] = None

    class Config:
        from_attributes = True

class ProductMatchResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    brand: str
    category: str
    description: Optional[str] = None
    variants: List[VariantMatchResponse] = []

    class Config:
        from_attributes = True

class IngredientProductMatchResponse(BaseModel):
    ingredient_id: uuid.UUID
    raw_name: str
    canonical_name: str
    status: str = Field(..., description="MATCHED, OUT_OF_STOCK_NO_ALTERNATIVES, or ALTERNATIVE_RECOMMENDED")
    requires_confirmation: bool = False
    matched_products: List[ProductMatchResponse] = []

class RecipeProductDiscoveryResponse(BaseModel):
    recipe_id: uuid.UUID
    ingredients: List[IngredientProductMatchResponse] = []
