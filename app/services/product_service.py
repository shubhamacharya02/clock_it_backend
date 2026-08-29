import uuid
from typing import List, Dict, Tuple, Optional
from fastapi import status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.recipe import Recipe
from app.services.recipe_service import recipe_service
from app.schemas.product import (
    VariantMatchResponse,
    ProductMatchResponse,
    IngredientProductMatchResponse,
    RecipeProductDiscoveryResponse
)
from app.main import AppException

class ProductService:
    async def get_product_variant_by_id(self, variant_id: uuid.UUID, db: AsyncSession) -> Tuple[ProductVariant, Product, Inventory]:
        """Fetches product variant, product, and inventory by variant ID."""
        stmt = (
            select(ProductVariant, Product, Inventory)
            .join(Product, ProductVariant.product_id == Product.id)
            .join(Inventory, ProductVariant.id == Inventory.variant_id)
            .where(ProductVariant.id == variant_id, ProductVariant.is_active == True, Product.is_active == True)
        )
        result = await db.execute(stmt)
        row = result.first()

        if not row:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="VARIANT_NOT_FOUND",
                message=f"Product variant '{variant_id}' was not found in the catalog."
            )
        return row[0], row[1], row[2]

    async def match_products_for_canonical_name(self, canonical_name: str, db: AsyncSession) -> List[ProductMatchResponse]:
        """
        Executes deterministic PostgreSQL JSONB containment query for canonical ingredient matching.
        Surfaces all in-stock variants across all brands and package sizes.
        """
        stmt = (
            select(Product, ProductVariant, Inventory)
            .join(ProductVariant, Product.id == ProductVariant.product_id)
            .join(Inventory, ProductVariant.id == Inventory.variant_id)
            .where(
                Product.is_active == True,
                ProductVariant.is_active == True,
                Inventory.available_quantity > 0,
                Product.metadata_json["canonical_ingredients"].contains([canonical_name])
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        products_map: Dict[uuid.UUID, Dict] = {}

        for product, variant, inventory in rows:
            if product.id not in products_map:
                products_map[product.id] = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "brand": product.brand,
                    "category": product.category,
                    "description": product.description,
                    "variants": []
                }

            products_map[product.id]["variants"].append(
                VariantMatchResponse(
                    variant_id=variant.id,
                    sku=variant.sku,
                    size=variant.size,
                    size_unit=variant.size_unit,
                    price=variant.price,
                    available_quantity=inventory.available_quantity
                )
            )

        return [ProductMatchResponse(**data) for data in products_map.values()]

    async def discover_products_for_recipe(
        self,
        user_id: uuid.UUID,
        recipe_id: uuid.UUID,
        db: AsyncSession
    ) -> RecipeProductDiscoveryResponse:
        """
        Discovers matching products for all ingredients in a recipe.
        Enforces 404 user resource ownership isolation via recipe_service.
        """
        recipe: Recipe = await recipe_service.get_recipe_by_id(user_id=user_id, recipe_id=recipe_id, db=db)

        ingredient_responses: List[IngredientProductMatchResponse] = []

        for ing in recipe.ingredients:
            matched_products = await self.match_products_for_canonical_name(ing.canonical_name, db)
            has_stock = len(matched_products) > 0

            ingredient_responses.append(
                IngredientProductMatchResponse(
                    ingredient_id=ing.id,
                    raw_name=ing.raw_name,
                    canonical_name=ing.canonical_name,
                    status="MATCHED" if has_stock else "OUT_OF_STOCK",
                    requires_confirmation=ing.requires_confirmation,
                    matched_products=matched_products
                )
            )

        return RecipeProductDiscoveryResponse(
            recipe_id=recipe.id,
            ingredients=ingredient_responses
        )

product_service = ProductService()
