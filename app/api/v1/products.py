import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.product_service import product_service
from app.schemas.product import RecipeProductDiscoveryResponse, VariantMatchResponse, ProductMatchResponse

router = APIRouter(tags=["Products"])

@router.post("/recipes/{recipe_id}/products", response_model=RecipeProductDiscoveryResponse)
async def discover_recipe_products(
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await product_service.discover_products_for_recipe(
        user_id=current_user.id,
        recipe_id=recipe_id,
        db=db
    )

@router.get("/products/{variant_id}", response_model=ProductMatchResponse)
async def get_product_variant(
    variant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    variant, product, inventory = await product_service.get_product_variant_by_id(variant_id, db)
    return ProductMatchResponse(
        product_id=product.id,
        product_name=product.name,
        brand=product.brand,
        category=product.category,
        description=product.description,
        variants=[
            VariantMatchResponse(
                variant_id=variant.id,
                sku=variant.sku,
                size=variant.size,
                size_unit=variant.size_unit,
                price=variant.price,
                available_quantity=inventory.available_quantity
            )
        ]
    )
