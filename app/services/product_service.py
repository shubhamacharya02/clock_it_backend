import uuid
from typing import List, Dict, Tuple, Optional, Any
from fastapi import status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.recipe import Recipe
from app.services.recipe_service import recipe_service
from app.ai.workflows.alternative_graph import alternative_graph
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
        Executes deterministic PostgreSQL JSONB containment query for primary canonical ingredient matching.
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
                    available_quantity=inventory.available_quantity,
                    is_alternative=False,
                    alternative_reason=None
                )
            )

        return [ProductMatchResponse(**data) for data in products_map.values()]

    async def find_alternative_candidates_for_canonical_name(self, canonical_name: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Queries database for in-stock products where metadata_json->'alternatives_for' contains canonical_name.
        Filters candidates deterministically BEFORE passing to LLM ranking.
        """
        stmt = (
            select(Product, ProductVariant, Inventory)
            .join(ProductVariant, Product.id == ProductVariant.product_id)
            .join(Inventory, ProductVariant.id == Inventory.variant_id)
            .where(
                Product.is_active == True,
                ProductVariant.is_active == True,
                Inventory.available_quantity > 0,
                Product.metadata_json["alternatives_for"].contains([canonical_name])
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        candidates: List[Dict[str, Any]] = []
        for product, variant, inventory in rows:
            candidates.append({
                "product_id": str(product.id),
                "variant_id": str(variant.id),
                "product_name": product.name,
                "brand": product.brand,
                "category": product.category,
                "size": float(variant.size),
                "size_unit": variant.size_unit,
                "price": float(variant.price),
                "sku": variant.sku,
                "available_quantity": inventory.available_quantity,
                "product_obj": product,
                "variant_obj": variant,
                "inventory_obj": inventory
            })
        return candidates

    async def discover_products_for_recipe(
        self,
        user_id: uuid.UUID,
        recipe_id: uuid.UUID,
        db: AsyncSession
    ) -> RecipeProductDiscoveryResponse:
        """
        Discovers matching products for all ingredients in a recipe.
        STRICT GATEKEEPER: Alternative recommendation flow triggers ONLY IF zero primary variants are in stock.
        Enforces 404 user resource ownership isolation via recipe_service.
        """
        recipe: Recipe = await recipe_service.get_recipe_by_id(user_id=user_id, recipe_id=recipe_id, db=db)

        ingredient_responses: List[IngredientProductMatchResponse] = []

        for ing in recipe.ingredients:
            # 1. Primary Deterministic Matching Query
            matched_products = await self.match_products_for_canonical_name(ing.canonical_name, db)

            if len(matched_products) > 0:
                # Primary product variants ARE in stock -> Return primary match. Alternative flow NOT triggered.
                ingredient_responses.append(
                    IngredientProductMatchResponse(
                        ingredient_id=ing.id,
                        raw_name=ing.raw_name,
                        canonical_name=ing.canonical_name,
                        status="MATCHED",
                        requires_confirmation=ing.requires_confirmation,
                        matched_products=matched_products
                    )
                )
            else:
                # 2. STRICT GATEKEEPER: Primary in-stock count is 0 -> Trigger Alternative Flow
                candidates = await self.find_alternative_candidates_for_canonical_name(ing.canonical_name, db)

                if len(candidates) == 0:
                    # Zero alternatives in stock -> Expected business state (HTTP 200)
                    ingredient_responses.append(
                        IngredientProductMatchResponse(
                            ingredient_id=ing.id,
                            raw_name=ing.raw_name,
                            canonical_name=ing.canonical_name,
                            status="OUT_OF_STOCK_NO_ALTERNATIVES",
                            requires_confirmation=ing.requires_confirmation,
                            matched_products=[]
                        )
                    )
                else:
                    # In-stock alternative candidates exist -> Pass to LLM for ranking & 1-sentence rationale
                    candidates_payload = [
                        {
                            "variant_id": c["variant_id"],
                            "product_name": c["product_name"],
                            "brand": c["brand"],
                            "size": c["size"],
                            "size_unit": c["size_unit"],
                            "price": c["price"]
                        }
                        for c in candidates
                    ]

                    graph_input = {
                        "canonical_name": ing.canonical_name,
                        "prefiltered_candidates": candidates_payload,
                        "ranked_response": None
                    }

                    graph_output = await alternative_graph.ainvoke(graph_input)
                    ranked_resp = graph_output.get("ranked_response")

                    # Map LLM rank & rationale back to candidates
                    reasons_map = {}
                    if ranked_resp and ranked_resp.alternatives:
                        for alt in ranked_resp.alternatives:
                            reasons_map[alt.variant_id] = alt.alternative_reason

                    products_map: Dict[uuid.UUID, Dict] = {}

                    for c in candidates:
                        p_obj: Product = c["product_obj"]
                        v_obj: ProductVariant = c["variant_obj"]
                        i_obj: Inventory = c["inventory_obj"]

                        if p_obj.id not in products_map:
                            products_map[p_obj.id] = {
                                "product_id": p_obj.id,
                                "product_name": p_obj.name,
                                "brand": p_obj.brand,
                                "category": p_obj.category,
                                "description": p_obj.description,
                                "variants": []
                            }

                        reason = reasons_map.get(str(v_obj.id), f"Culinary alternative for {ing.canonical_name}")

                        products_map[p_obj.id]["variants"].append(
                            VariantMatchResponse(
                                variant_id=v_obj.id,
                                sku=v_obj.sku,
                                size=v_obj.size,
                                size_unit=v_obj.size_unit,
                                price=v_obj.price,
                                available_quantity=i_obj.available_quantity,
                                is_alternative=True,
                                alternative_reason=reason
                            )
                        )

                    alt_products = [ProductMatchResponse(**data) for data in products_map.values()]

                    ingredient_responses.append(
                        IngredientProductMatchResponse(
                            ingredient_id=ing.id,
                            raw_name=ing.raw_name,
                            canonical_name=ing.canonical_name,
                            status="ALTERNATIVE_RECOMMENDED",
                            requires_confirmation=ing.requires_confirmation,
                            matched_products=alt_products
                        )
                    )

        return RecipeProductDiscoveryResponse(
            recipe_id=recipe.id,
            ingredients=ingredient_responses
        )

product_service = ProductService()
