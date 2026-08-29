from typing import List
from pydantic import BaseModel, Field

class RankedAlternativeItem(BaseModel):
    variant_id: str = Field(..., description="Variant ID string matching input candidate")
    rank: int = Field(..., description="Culinary suitability rank (1 = best substitute)")
    alternative_reason: str = Field(..., description="1-sentence rationale explaining why this is a good culinary substitute")

class RankedAlternativeResponse(BaseModel):
    canonical_name: str = Field(..., description="Primary out-of-stock canonical ingredient key")
    alternatives: List[RankedAlternativeItem] = Field(default_factory=list, description="Ranked list of in-stock alternatives")
