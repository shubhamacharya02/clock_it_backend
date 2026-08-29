from decimal import Decimal

def test_decimal_pricing_math_precision():
    unit_price = Decimal("54.00")
    quantity = 3
    line_subtotal = unit_price * Decimal(quantity)

    assert line_subtotal == Decimal("162.00")
    assert isinstance(line_subtotal, Decimal)

def test_cart_grand_total_calculation():
    item1_subtotal = Decimal("54.00") * Decimal(2)  # 108.00
    item2_subtotal = Decimal("85.00") * Decimal(1)  # 85.00

    grand_total = item1_subtotal + item2_subtotal
    assert grand_total == Decimal("193.00")
    assert isinstance(grand_total, Decimal)
