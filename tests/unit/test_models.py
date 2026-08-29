import uuid
from decimal import Decimal
from app.models.user import User
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.cart import Cart, CartItem, CartStatus
from app.models.order import Order, OrderItem, OrderStatus

def test_sqlmodel_entities_instantiation():
    user_id = uuid.uuid4()
    user = User(id=user_id, email="test@example.com", hashed_password="hashed_pwd", full_name="Test User")
    assert user.email == "test@example.com"
    assert user.is_active is True

    product_id = uuid.uuid4()
    product = Product(
        id=product_id,
        name="Taaza Toned Milk",
        brand="Amul",
        category="Dairy",
        metadata_json={"canonical_ingredients": ["milk"], "product_type": "dairy", "sub_type": "cow_milk", "alternatives_for": []}
    )
    assert product.brand == "Amul"
    assert product.metadata_json["canonical_ingredients"] == ["milk"]

    variant_id = uuid.uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="SKU-AMUL-MILK-1L",
        size=Decimal("1000.00"),
        size_unit="ml",
        price=Decimal("54.00")
    )
    assert variant.price == Decimal("54.00")
    assert variant.size == Decimal("1000.00")

    inventory = Inventory(variant_id=variant_id, available_quantity=15)
    assert inventory.available_quantity == 15

    cart = Cart(user_id=user_id, status=CartStatus.ACTIVE)
    assert cart.status == CartStatus.ACTIVE

    cart_item = CartItem(cart_id=cart.id, variant_id=variant_id, quantity=2)
    assert cart_item.quantity == 2

    order = Order(user_id=user_id, order_number="ORD-123456", total_amount=Decimal("108.00"), status=OrderStatus.CONFIRMED)
    assert order.total_amount == Decimal("108.00")

    order_item = OrderItem(
        order_id=order.id,
        variant_id=variant_id,
        product_name_snapshot=product.name,
        brand_snapshot=product.brand,
        size_snapshot=variant.size,
        unit_snapshot=variant.size_unit,
        unit_price_snapshot=variant.price,
        quantity=2,
        line_total=Decimal("108.00")
    )
    assert order_item.line_total == Decimal("108.00")
