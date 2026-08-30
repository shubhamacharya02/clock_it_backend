import uuid
from typing import Optional, List, Dict, Any
from fastapi import status
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe, SourceType, RecipeStatus
from app.models.recipe_ingredient import RecipeIngredient
from app.services.storage_service import storage_service
from app.integrations.webpage_fetcher import fetch_webpage_content
from app.integrations.youtube_transcript import fetch_youtube_transcript
from app.ai.workflows.recipe_graph import recipe_graph
from app.core.exceptions import AppException

class RecipeService:
    async def get_recipe_by_id(self, user_id: uuid.UUID, recipe_id: uuid.UUID, db: AsyncSession) -> Recipe:
        """Fetches recipe by ID, enforcing strict 404 user resource ownership isolation."""
        result = await db.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id))
        recipe = result.scalar_one_or_none()

        if not recipe or recipe.user_id != user_id:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="RESOURCE_NOT_FOUND",
                message="Resource not found"
            )
        return recipe

    async def _execute_and_persist_recipe(
        self,
        user_id: uuid.UUID,
        title: str,
        source_type: SourceType,
        source_url: Optional[str],
        storage_path: Optional[str],
        raw_content: Optional[str],
        graph_input: Dict[str, Any],
        db: AsyncSession
    ) -> Recipe:
        """Executes LangGraph workflow and persists Recipe & RecipeIngredients to PostgreSQL."""
        recipe = Recipe(
            user_id=user_id,
            title=title,
            source_type=source_type,
            source_url=source_url,
            storage_path=storage_path,
            raw_content=raw_content[:2000] if raw_content else None,
            status=RecipeStatus.PROCESSING
        )
        db.add(recipe)
        await db.commit()
        await db.refresh(recipe)

        try:
            # Run LangGraph recipe workflow
            graph_output = await recipe_graph.ainvoke(graph_input)
            extracted = graph_output.get("extracted_recipe")
            if extracted and extracted.title and not title:
                recipe.title = extracted.title

            ingredients_data = graph_output.get("processed_ingredients", [])

            for ing_data in ingredients_data:
                db_ing = RecipeIngredient(
                    recipe_id=recipe.id,
                    raw_name=ing_data.get("raw_name") or "Ingredient",
                    canonical_name=(ing_data.get("canonical_name") or "ingredient").lower().strip(),
                    quantity=ing_data.get("quantity"),
                    unit=ing_data.get("unit"),
                    confidence=float(ing_data.get("confidence", 1.0) or 1.0),
                    requires_confirmation=bool(ing_data.get("requires_confirmation", False)),
                    is_user_modified=False
                )
                db.add(db_ing)

            recipe.status = RecipeStatus.COMPLETED
            await db.commit()
            await db.refresh(recipe)

            # Reload with ingredients relation
            result = await db.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe.id))
            return result.scalar_one()

        except Exception as exc:
            import logging
            logging.getLogger("uvicorn.error").error("Recipe AI processing failed: %s", exc, exc_info=True)
            recipe.status = RecipeStatus.FAILED
            await db.commit()
            if isinstance(exc, AppException):
                raise exc
            raise AppException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                code="LLM_STRUCTURE_ERROR",
                message="Recipe AI processing encountered a structural extraction error.",
                details=[{"error": str(exc)}]
            )

    async def process_image_recipe(
        self,
        user_id: uuid.UUID,
        file_bytes: bytes,
        content_type: str,
        db: AsyncSession
    ) -> Recipe:
        """Handles image and camera photo upload ingestion."""
        recipe_id = uuid.uuid4()
        ext = content_type.split("/")[-1] if "/" in content_type else "jpg"
        
        # Upload to Supabase Storage
        storage_path = storage_service.upload_recipe_image(
            user_id=user_id,
            recipe_id=recipe_id,
            file_bytes=file_bytes,
            content_type=content_type,
            file_extension=ext
        )

        graph_input = {
            "input_type": "image",
            "raw_content": f"Image recipe media upload: {storage_path}",
            "is_vision": True,
            "image_bytes": file_bytes,
            "mime_type": content_type,
            "extracted_recipe": None,
            "processed_ingredients": []
        }

        return await self._execute_and_persist_recipe(
            user_id=user_id,
            title="Image Recipe",
            source_type=SourceType.IMAGE,
            source_url=None,
            storage_path=storage_path,
            raw_content="[Binary Image Media]",
            graph_input=graph_input,
            db=db
        )

    async def process_text_recipe(
        self,
        user_id: uuid.UUID,
        title: Optional[str],
        text_content: str,
        db: AsyncSession
    ) -> Recipe:
        """Handles raw text recipe ingestion."""
        graph_input = {
            "input_type": "text",
            "raw_content": text_content,
            "is_vision": False,
            "image_bytes": None,
            "mime_type": "text/plain",
            "extracted_recipe": None,
            "processed_ingredients": []
        }

        return await self._execute_and_persist_recipe(
            user_id=user_id,
            title=title or "Text Recipe",
            source_type=SourceType.TEXT,
            source_url=None,
            storage_path=None,
            raw_content=text_content,
            graph_input=graph_input,
            db=db
        )

    async def process_url_recipe(
        self,
        user_id: uuid.UUID,
        url: str,
        db: AsyncSession
    ) -> Recipe:
        """Handles recipe webpage URL ingestion."""
        clean_text = await fetch_webpage_content(url)

        graph_input = {
            "input_type": "url",
            "raw_content": clean_text,
            "is_vision": False,
            "image_bytes": None,
            "mime_type": "text/plain",
            "extracted_recipe": None,
            "processed_ingredients": []
        }

        return await self._execute_and_persist_recipe(
            user_id=user_id,
            title="Webpage Recipe",
            source_type=SourceType.URL,
            source_url=url,
            storage_path=None,
            raw_content=clean_text,
            graph_input=graph_input,
            db=db
        )

    async def process_video_recipe(
        self,
        user_id: uuid.UUID,
        video_url: str,
        db: AsyncSession
    ) -> Recipe:
        """Handles YouTube video transcript recipe ingestion."""
        transcript = fetch_youtube_transcript(video_url)

        graph_input = {
            "input_type": "video",
            "raw_content": transcript,
            "is_vision": False,
            "image_bytes": None,
            "mime_type": "text/plain",
            "extracted_recipe": None,
            "processed_ingredients": []
        }

        return await self._execute_and_persist_recipe(
            user_id=user_id,
            title="YouTube Recipe",
            source_type=SourceType.VIDEO,
            source_url=video_url,
            storage_path=None,
            raw_content=transcript,
            graph_input=graph_input,
            db=db
        )

    async def update_recipe_ingredients(
        self,
        user_id: uuid.UUID,
        recipe_id: uuid.UUID,
        updates: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Recipe:
        """Updates recipe ingredients when modified by the user."""
        recipe = await self.get_recipe_by_id(user_id, recipe_id, db)

        for update in updates:
            ing_id = update.get("id")
            result = await db.execute(select(RecipeIngredient).where(RecipeIngredient.id == ing_id, RecipeIngredient.recipe_id == recipe_id))
            ing = result.scalar_one_or_none()
            if ing:
                if "raw_name" in update and update["raw_name"] is not None:
                    ing.raw_name = update["raw_name"]
                if "canonical_name" in update and update["canonical_name"] is not None:
                    ing.canonical_name = update["canonical_name"].lower().strip()
                if "quantity" in update:
                    ing.quantity = update["quantity"]
                if "unit" in update:
                    ing.unit = update["unit"]
                ing.is_user_modified = True
                ing.requires_confirmation = False

        await db.commit()
        await db.refresh(recipe)
        return recipe

recipe_service = RecipeService()
