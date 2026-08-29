import uuid
from decimal import Decimal
from typing import List, Tuple
from fastapi import status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem, CartStatus
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.inventory import Inventory
from app.services.product_service import product_service
from app.schemas.cart import CartItemResponse, CartResponse
from app.main import AppException

class CartService:
    async def get_or_create_active_cart(self, user_id: uuid.UUID, db: AsyncSession) -> Cart:
        """Fetches current active cart for user; auto-initializes new active cart if none exists."""
        stmt = select(Cart).where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE)
        result = await db.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=user_id, status=CartStatus.ACTIVE)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
        return cart

    async def get_cart_with_items(self, user_id: uuid.UUID, db: AsyncSession) -> CartResponse:
        """Fetches active cart and builds complete CartResponse with Decimal subtotal calculations."""
        cart = await self.get_or_create_active_cart(user_id, db)

        stmt = (
            select(CartItem, ProductVariant, Product, Inventory)
            .join(ProductVariant, CartItem.variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
            .join(Inventory, ProductVariant.id == Inventory.variant_id)
            .where(CartItem.cart_id == cart.id)
        )
        result = await db.execute(stmt)
        rows = result.all()

        item_responses: List[CartItemResponse] = []
        grand_total = Decimal("0.00")

        for item, variant, product, inventory in rows:
            line_subtotal = variant.price * Decimal(item.quantity)
            grand_total += line_subtotal

            item_responses.append(
                CartItemResponse(
                    id=item.id,
                    cart_id=item.cart_id,
                    variant_id=variant.id,
                    sku=variant.sku,
                    product_name=product.name,
                    brand=product.brand,
                    size=variant.size,
                    size_unit=variant.size_unit,
                    unit_price=variant.price,
                    quantity=item.quantity,
                    line_subtotal=line_subtotal,
                    available_quantity=inventory.available_quantity,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                )
            )

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            status=cart.status,
            items=item_responses,
            grand_total=grand_total,
            created_at=cart.created_at,
            updated_at=cart.updated_at
        )

    async def add_item_to_cart(
        self,
        user_id: uuid.UUID,
        variant_id: uuid.UUID,
        quantity: int,
        db: AsyncSession
    ) -> CartResponse:
        """Adds a SKU variant to active cart. Handles UNIQUE(cart_id, variant_id) by updating quantity."""
        if quantity <= 0:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_QUANTITY",
                message="Cart item quantity must be an integer >= 1."
            )

        # 1. Fetch variant & inventory details
        variant, product, inventory = await product_service.get_product_variant_by_id(variant_id, db)

        if not variant.is_active:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="VARIANT_INACTIVE",
                message=f"Product variant SKU '{variant.sku}' is inactive."
            )

        cart = await self.get_or_create_active_cart(user_id, db)

        # 2. Check if item already exists in cart (UNIQUE constraint handling)
        stmt = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id)
        result = await db.execute(stmt)
        existing_item = result.scalar_one_or_none()

        target_quantity = quantity if not existing_item else (existing_item.quantity + quantity)

        if inventory.available_quantity < target_quantity:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_STOCK",
                message=f"Requested quantity ({target_quantity}) exceeds available stock ({inventory.available_quantity}).",
                details=[{
                    "field": "variant_id",
                    "value": str(variant_id),
                    "issue": f"Available stock is {inventory.available_quantity}."
                }]
            )

        if existing_item:
            existing_item.quantity = target_quantity
        else:
            new_item = CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity)
            db.add(new_item)

        await db.commit()
        return await self.get_cart_with_items(user_id, db)

    async def update_cart_item_quantity(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        quantity: int,
        db: AsyncSession
    ) -> CartResponse:
        """Updates item quantity in cart. Enforces 404 user ownership rules."""
        if quantity <= 0:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_QUANTITY",
                message="Cart item quantity must be an integer >= 1."
            )

        cart = await self.get_or_create_active_cart(user_id, db)

        stmt = select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="RESOURCE_NOT_FOUND",
                message="Resource not found"
            )

        # Check inventory availability
        variant, product, inventory = await product_service.get_product_variant_by_id(item.variant_id, db)

        if inventory.available_quantity < quantity:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_STOCK",
                message=f"Requested quantity ({quantity}) exceeds available stock ({inventory.available_quantity}).",
                details=[{
                    "field": "variant_id",
                    "value": str(item.variant_id),
                    "issue": f"Available stock is {inventory.available_quantity}."
                }]
            )

        item.quantity = quantity
        await db.commit()
        return await self.get_cart_with_items(user_id, db)

    async def remove_cart_item(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        db: AsyncSession
    ) -> CartResponse:
        """Deletes a cart item from user's active cart. Enforces 404 user ownership rules."""
        cart = await self.get_or_create_active_cart(user_id, db)

        stmt = select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="RESOURCE_NOT_FOUND",
                message="Resource not found"
            )

        await db.delete(item)
        await db.commit()
        return await self.get_cart_with_items(user_id, db)

cart_service = CartService()
