import pytest
import uuid
from decimal import Decimal
from app.schemas.cart import CartItemResponse, CartResponse
from app.models.cart import CartStatus

def test_cart_response_formatting():
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    variant_id = uuid.uuid4()

    item = CartItemResponse(
        id=uuid.uuid4(),
        cart_id=cart_id,
        variant_id=variant_id,
        sku="SKU-AMUL-1L",
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
        id=cart_id,
        user_id=user_id,
        status=CartStatus.ACTIVE,
        items=[item],
        grand_total=Decimal("108.00"),
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )

    assert cart.grand_total == Decimal("108.00")
    assert cart.items[0].line_subtotal == Decimal("108.00")
