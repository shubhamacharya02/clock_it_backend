import uuid
from datetime import datetime
from decimal import Decimal
from typing import List
from fastapi import status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem, CartStatus
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderItemResponse, OrderResponse
from app.main import AppException

class OrderService:
    async def get_order_by_id(self, user_id: uuid.UUID, order_id: uuid.UUID, db: AsyncSession) -> OrderResponse:
        """Fetches an order by ID, enforcing 404 user resource ownership isolation."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
        )
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order or order.user_id != user_id:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="RESOURCE_NOT_FOUND",
                message="Resource not found"
            )

        stmt_items = (
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
        )
        items_result = await db.execute(stmt_items)
        items = items_result.scalars().all()

        item_responses = [OrderItemResponse.model_validate(item) for item in items]

        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            order_number=order.order_number,
            total_amount=order.total_amount,
            status=order.status,
            items=item_responses,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

    async def list_user_orders(self, user_id: uuid.UUID, db: AsyncSession) -> List[OrderResponse]:
        """Lists all completed orders for the authenticated user."""
        stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        result = await db.execute(stmt)
        orders = result.scalars().all()

        order_responses: List[OrderResponse] = []
        for order in orders:
            stmt_items = select(OrderItem).where(OrderItem.order_id == order.id)
            items_result = await db.execute(stmt_items)
            items = items_result.scalars().all()
            item_responses = [OrderItemResponse.model_validate(item) for item in items]

            order_responses.append(
                OrderResponse(
                    id=order.id,
                    user_id=order.user_id,
                    order_number=order.order_number,
                    total_amount=order.total_amount,
                    status=order.status,
                    items=item_responses,
                    created_at=order.created_at,
                    updated_at=order.updated_at
                )
            )

        return order_responses

    async def checkout_active_cart(self, user_id: uuid.UUID, db: AsyncSession) -> OrderResponse:
        """
        Executes atomic checkout transaction using row locking (SELECT ... FOR UPDATE) on Cart, CartItems, and Inventory.
        Re-validates stock, deducts inventory, builds immutable OrderItem snapshots, converts cart, and commits.
        Returns 201 Created.
        """
        try:
            # 1. Lock active cart row
            stmt_cart = (
                select(Cart)
                .where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE)
                .with_for_update()
            )
            result_cart = await db.execute(stmt_cart)
            cart = result_cart.scalar_one_or_none()

            if not cart:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code="EMPTY_CART",
                    message="Active cart is empty. Cannot checkout an empty cart."
                )

            # 2. Lock cart items
            stmt_items = (
                select(CartItem)
                .where(CartItem.cart_id == cart.id)
                .with_for_update()
            )
            result_items = await db.execute(stmt_items)
            cart_items = result_items.scalars().all()

            if not cart_items or len(cart_items) == 0:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code="EMPTY_CART",
                    message="Active cart is empty. Cannot checkout an empty cart."
                )

            # 3. Lock inventory, validate stock, read variant/product snapshots
            order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            total_amount = Decimal("0.00")
            order_items_to_create: List[OrderItem] = []

            for item in cart_items:
                # Lock inventory row
                stmt_inv = (
                    select(Inventory)
                    .where(Inventory.variant_id == item.variant_id)
                    .with_for_update()
                )
                res_inv = await db.execute(stmt_inv)
                inventory = res_inv.scalar_one_or_none()

                if not inventory or inventory.available_quantity < item.quantity:
                    await db.rollback()
                    avail_qty = inventory.available_quantity if inventory else 0
                    raise AppException(
                        status_code=status.HTTP_409_CONFLICT,
                        code="INSUFFICIENT_STOCK",
                        message=f"Insufficient inventory for checkout.",
                        details=[{
                            "field": "variant_id",
                            "value": str(item.variant_id),
                            "issue": f"Requested quantity ({item.quantity}) exceeds available stock ({avail_qty})."
                        }]
                    )

                # Fetch variant and product for authoritative snapshot details
                stmt_var = (
                    select(ProductVariant, Product)
                    .join(Product, ProductVariant.product_id == Product.id)
                    .where(ProductVariant.id == item.variant_id)
                    .with_for_update()
                )
                res_var = await db.execute(stmt_var)
                variant_row = res_var.first()
                if not variant_row:
                    await db.rollback()
                    raise AppException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        code="VARIANT_INACTIVE",
                        message="One or more cart items reference invalid product variants."
                    )

                variant, product = variant_row[0], variant_row[1]

                # Deduct inventory stock
                inventory.available_quantity -= item.quantity
                inventory.updated_at = datetime.utcnow()

                # Calculate Decimal pricing math
                line_total = variant.price * Decimal(item.quantity)
                total_amount += line_total

                # Create OrderItem snapshot
                order_item_snap = OrderItem(
                    variant_id=variant.id,
                    product_name_snapshot=product.name,
                    brand_snapshot=product.brand,
                    size_snapshot=variant.size,
                    unit_snapshot=variant.size_unit,
                    unit_price_snapshot=variant.price,
                    quantity=item.quantity,
                    line_total=line_total
                )
                order_items_to_create.append(order_item_snap)

            # 4. Create Order row
            order = Order(
                user_id=user_id,
                order_number=order_number,
                total_amount=total_amount,
                status=OrderStatus.CONFIRMED
            )
            db.add(order)
            await db.flush()  # Assign order.id

            for item_snap in order_items_to_create:
                item_snap.order_id = order.id
                db.add(item_snap)

            # 5. Convert cart status
            cart.status = CartStatus.CONVERTED
            cart.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(order)

            return await self.get_order_by_id(user_id=user_id, order_id=order.id, db=db)

        except AppException:
            await db.rollback()
            raise
        except Exception as exc:
            await db.rollback()
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="DATABASE_TRANSACTION_ERROR",
                message="An error occurred during database transaction checkout execution.",
                details=[{"error": str(exc)}]
            )

order_service = OrderService()
