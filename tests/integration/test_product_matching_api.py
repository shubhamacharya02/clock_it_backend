import pytest
import uuid
from decimal import Decimal
from app.schemas.product import VariantMatchResponse, ProductMatchResponse, RecipeProductDiscoveryResponse

def test_product_matching_dto_structure():
    variant = VariantMatchResponse(
        variant_id=uuid.uuid4(),
        sku="SKU-AMUL-1L",
        size=Decimal("1000.00"),
        size_unit="ml",
        price=Decimal("54.00"),
        available_quantity=15
    )

    product = ProductMatchResponse(
        product_id=uuid.uuid4(),
        product_name="Taaza Toned Milk",
        brand="Amul",
        category="Dairy",
        variants=[variant]
    )

    assert product.brand == "Amul"
    assert product.variants[0].price == Decimal("54.00")
    assert product.variants[0].size == Decimal("1000.00")

def test_product_discovery_response_serialization():
    recipe_id = uuid.uuid4()
    discovery = RecipeProductDiscoveryResponse(
        recipe_id=recipe_id,
        ingredients=[]
    )
    assert discovery.recipe_id == recipe_id
    assert discovery.ingredients == []
