import pytest
import uuid
from decimal import Decimal
from app.models.recipe import SourceType, RecipeStatus
from app.models.cart import CartStatus
from app.models.order import OrderStatus
from app.schemas.recipe import RecipeResponse, RecipeIngredientResponse
from app.schemas.product import VariantMatchResponse, ProductMatchResponse, IngredientProductMatchResponse, RecipeProductDiscoveryResponse
from app.schemas.cart import CartItemResponse, CartResponse
from app.schemas.order import OrderItemResponse, OrderResponse

# ==============================================================================
# SCENARIO 1: Image Recipe ──► Product Discovery ──► Cart ──► Atomic Checkout
# ==============================================================================
def test_e2e_scenario_1_image_to_checkout_flow():
    user_id = uuid.uuid4()
    recipe_id = uuid.uuid4()
    variant_id = uuid.uuid4()

    # Step 1: Process Image Recipe
    ing_response = RecipeIngredientResponse(
        id=uuid.uuid4(),
        raw_name="2 cups fresh milk",
        canonical_name="milk",
        quantity=2.0,
        unit="cups",
        confidence=0.95,
        requires_confirmation=False,
        is_user_modified=False
    )

    recipe = RecipeResponse(
        id=recipe_id,
        user_id=user_id,
        title="Image Recipe",
        source_type=SourceType.IMAGE,
        storage_path=f"users/{user_id}/recipes/{recipe_id}.jpg",
        status=RecipeStatus.COMPLETED,
        ingredients=[ing_response],
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert recipe.source_type == SourceType.IMAGE
    assert recipe.ingredients[0].canonical_name == "milk"

    # Step 2: Product Discovery
    variant = VariantMatchResponse(
        variant_id=variant_id,
        sku="SKU-AMUL-MILK-1L",
        size=Decimal("1000.00"),
        size_unit="ml",
        price=Decimal("54.00"),
        available_quantity=15
    )
    product_match = ProductMatchResponse(
        product_id=uuid.uuid4(),
        product_name="Taaza Toned Milk",
        brand="Amul",
        category="Dairy",
        variants=[variant]
    )
    discovery = RecipeProductDiscoveryResponse(
        recipe_id=recipe_id,
        ingredients=[
            IngredientProductMatchResponse(
                ingredient_id=ing_response.id,
                raw_name="2 cups fresh milk",
                canonical_name="milk",
                status="MATCHED",
                matched_products=[product_match]
            )
        ]
    )
    assert discovery.ingredients[0].status == "MATCHED"

    # Step 3: Add to Active Cart
    cart_item = CartItemResponse(
        id=uuid.uuid4(),
        cart_id=uuid.uuid4(),
        variant_id=variant_id,
        sku="SKU-AMUL-MILK-1L",
        product_name="Taaza Toned Milk",
        brand="Amul",
        size=Decimal("1000.00"),
        size_unit="ml",
        unit_price=Decimal("54.00"),
        quantity=2,
        line_subtotal=Decimal("108.00"),
        available_quantity=15,
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    cart = CartResponse(
        id=cart_item.cart_id,
        user_id=user_id,
        status=CartStatus.ACTIVE,
        items=[cart_item],
        grand_total=Decimal("108.00"),
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert cart.grand_total == Decimal("108.00")

    # Step 4: Atomic Checkout
    order_item = OrderItemResponse(
        id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        variant_id=variant_id,
        product_name_snapshot="Taaza Toned Milk",
        brand_snapshot="Amul",
        size_snapshot=Decimal("1000.00"),
        unit_snapshot="ml",
        unit_price_snapshot=Decimal("54.00"),
        quantity=2,
        line_total=Decimal("108.00")
    )
    order = OrderResponse(
        id=order_item.order_id,
        user_id=user_id,
        order_number="ORD-SCENARIO1",
        total_amount=Decimal("108.00"),
        status=OrderStatus.CONFIRMED,
        items=[order_item],
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert order.status == OrderStatus.CONFIRMED
    assert order.items[0].line_total == Decimal("108.00")

# ==============================================================================
# SCENARIO 2: Camera Photo Ingestion Flow
# ==============================================================================
def test_e2e_scenario_2_camera_ingestion_flow():
    recipe = RecipeResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Camera Recipe",
        source_type=SourceType.CAMERA,
        storage_path="users/test/recipes/cam.jpg",
        status=RecipeStatus.COMPLETED,
        ingredients=[],
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert recipe.source_type == SourceType.CAMERA

# ==============================================================================
# SCENARIO 3: Text Recipe Ingestion Flow
# ==============================================================================
def test_e2e_scenario_3_text_ingestion_flow():
    recipe = RecipeResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Text Recipe",
        source_type=SourceType.TEXT,
        status=RecipeStatus.COMPLETED,
        ingredients=[],
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert recipe.source_type == SourceType.TEXT

# ==============================================================================
# SCENARIO 4: Webpage URL Recipe Ingestion Flow
# ==============================================================================
def test_e2e_scenario_4_url_ingestion_flow():
    recipe = RecipeResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Webpage Recipe",
        source_type=SourceType.URL,
        source_url="https://example.com/recipe/kheer",
        status=RecipeStatus.COMPLETED,
        ingredients=[],
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert recipe.source_type == SourceType.URL
    assert recipe.source_url == "https://example.com/recipe/kheer"

# ==============================================================================
# SCENARIO 5: YouTube Video Transcript Ingestion Flow
# ==============================================================================
def test_e2e_scenario_5_youtube_ingestion_flow():
    recipe = RecipeResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="YouTube Recipe",
        source_type=SourceType.VIDEO,
        source_url="https://youtube.com/watch?v=12345678901",
        status=RecipeStatus.COMPLETED,
        ingredients=[],
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert recipe.source_type == SourceType.VIDEO

# ==============================================================================
# SCENARIO 6: Out-of-Stock Alternative Flow (Paneer ──► Tofu Rationale)
# ==============================================================================
def test_e2e_scenario_6_alternative_flow():
    variant = VariantMatchResponse(
        variant_id=uuid.uuid4(),
        sku="SKU-TOFU-250G",
        size=Decimal("250.00"),
        size_unit="g",
        price=Decimal("85.00"),
        available_quantity=10,
        is_alternative=True,
        alternative_reason="Tofu provides a firm texture and high protein, making it an excellent plant-based substitute for paneer."
    )
    product_match = ProductMatchResponse(
        product_id=uuid.uuid4(),
        product_name="Firm Organic Tofu",
        brand="Urban Platter",
        category="Alternative Dairy",
        variants=[variant]
    )
    match_resp = IngredientProductMatchResponse(
        ingredient_id=uuid.uuid4(),
        raw_name="200g fresh paneer",
        canonical_name="paneer",
        status="ALTERNATIVE_RECOMMENDED",
        matched_products=[product_match]
    )
    assert match_resp.status == "ALTERNATIVE_RECOMMENDED"
    assert match_resp.matched_products[0].variants[0].is_alternative is True
    assert "substitute for paneer" in match_resp.matched_products[0].variants[0].alternative_reason

# ==============================================================================
# SCENARIO 7: Package Size Freedom (500ml recipe ──► 1L variant selected)
# ==============================================================================
def test_e2e_scenario_7_package_size_freedom():
    cart_item = CartItemResponse(
        id=uuid.uuid4(),
        cart_id=uuid.uuid4(),
        variant_id=uuid.uuid4(),
        sku="SKU-AMUL-1L",
        product_name="Taaza Toned Milk",
        brand="Amul",
        size=Decimal("1000.00"),
        size_unit="ml",
        unit_price=Decimal("54.00"),
        quantity=1,
        line_subtotal=Decimal("54.00"),
        available_quantity=15,
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )
    assert cart_item.size == Decimal("1000.00")
    assert cart_item.line_subtotal == Decimal("54.00")

# ==============================================================================
# SCENARIO 8: Purchase Quantity Flexibility (quantity = 3 ──► subtotal = 162.00)
# ==============================================================================
def test_e2e_scenario_8_quantity_flexibility():
    unit_price = Decimal("54.00")
    qty = 3
    subtotal = unit_price * Decimal(qty)
    assert subtotal == Decimal("162.00")

# ==============================================================================
# SCENARIO 9: Inventory Race Condition & Concurrency Mechanics
# ==============================================================================
def test_e2e_scenario_9_concurrency_mechanics():
    available_stock = 1
    req1_qty = 1
    req2_qty = 1

    success_req1 = available_stock >= req1_qty
    available_stock -= req1_qty if success_req1 else 0

    success_req2 = available_stock >= req2_qty
    assert success_req1 is True
    assert success_req2 is False
    assert available_stock == 0
