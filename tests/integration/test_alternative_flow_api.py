import pytest
import uuid
from decimal import Decimal
from app.schemas.product import VariantMatchResponse, IngredientProductMatchResponse

def test_alternative_match_response_flagging():
    variant = VariantMatchResponse(
        variant_id=uuid.uuid4(),
        sku="SKU-TOFU-250G",
        size=Decimal("250.00"),
        size_unit="g",
        price=Decimal("85.00"),
        available_quantity=10,
        is_alternative=True,
        alternative_reason="Tofu provides a firm texture, making it an excellent culinary substitute for paneer."
    )
    assert variant.is_alternative is True
    assert "substitute for paneer" in variant.alternative_reason

def test_out_of_stock_no_alternatives_status():
    ingredient_match = IngredientProductMatchResponse(
        ingredient_id=uuid.uuid4(),
        raw_name="exotic truffle oil",
        canonical_name="truffle_oil",
        status="OUT_OF_STOCK_NO_ALTERNATIVES",
        requires_confirmation=False,
        matched_products=[]
    )
    assert ingredient_match.status == "OUT_OF_STOCK_NO_ALTERNATIVES"
    assert len(ingredient_match.matched_products) == 0
