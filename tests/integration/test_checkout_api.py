import pytest
import uuid
from decimal import Decimal
from app.schemas.order import OrderItemResponse, OrderResponse
from app.models.order import OrderStatus

def test_order_response_snapshot_formatting():
    order_id = uuid.uuid4()
    user_id = uuid.uuid4()
    variant_id = uuid.uuid4()

    item_snap = OrderItemResponse(
        id=uuid.uuid4(),
        order_id=order_id,
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
        id=order_id,
        user_id=user_id,
        order_number="ORD-8A3B2F1C",
        total_amount=Decimal("108.00"),
        status=OrderStatus.CONFIRMED,
        items=[item_snap],
        created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00"
    )

    assert order.order_number == "ORD-8A3B2F1C"
    assert order.total_amount == Decimal("108.00")
    assert order.items[0].product_name_snapshot == "Taaza Toned Milk"
    assert order.items[0].unit_price_snapshot == Decimal("54.00")
    assert order.items[0].line_total == Decimal("108.00")
