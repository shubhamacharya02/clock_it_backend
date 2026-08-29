import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.recipe_service import recipe_service
from app.schemas.recipe import (
    RecipeTextRequest,
    RecipeURLRequest,
    RecipeVideoRequest,
    IngredientUpdatesPayload,
    RecipeResponse
)

router = APIRouter(prefix="/recipes", tags=["Recipes"])

@router.post("/process-image", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def process_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"
    return await recipe_service.process_image_recipe(
        user_id=current_user.id,
        file_bytes=file_bytes,
        content_type=content_type,
        db=db
    )

@router.post("/process-text", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def process_text(
    payload: RecipeTextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await recipe_service.process_text_recipe(
        user_id=current_user.id,
        title=payload.title,
        text_content=payload.text,
        db=db
    )

@router.post("/process-url", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def process_url(
    payload: RecipeURLRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await recipe_service.process_url_recipe(
        user_id=current_user.id,
        url=payload.url,
        db=db
    )

@router.post("/process-video", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def process_video(
    payload: RecipeVideoRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await recipe_service.process_video_recipe(
        user_id=current_user.id,
        video_url=payload.video_url,
        db=db
    )

@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await recipe_service.get_recipe_by_id(
        user_id=current_user.id,
        recipe_id=recipe_id,
        db=db
    )

@router.patch("/{recipe_id}/ingredients", response_model=RecipeResponse)
async def update_recipe_ingredients(
    recipe_id: uuid.UUID,
    payload: IngredientUpdatesPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updates_dict = [item.model_dump() for item in payload.ingredients]
    return await recipe_service.update_recipe_ingredients(
        user_id=current_user.id,
        recipe_id=recipe_id,
        updates=updates_dict,
        db=db
    )
