import uuid
from typing import Optional
from fastapi import status
from supabase import create_client, Client
from app.core.config import settings
from app.core.exceptions import AppException

class StorageService:
    BUCKET_NAME = "recipe-media"
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(self, client: Optional[Client] = None):
        if client:
            self.client = client
        else:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def ensure_bucket_exists(self) -> None:
        """Ensures the private recipe-media bucket exists in Supabase Storage."""
        try:
            buckets = self.client.storage.list_buckets()
            bucket_names = [b.name for b in buckets] if buckets else []
            if self.BUCKET_NAME not in bucket_names:
                self.client.storage.create_bucket(self.BUCKET_NAME, options={"public": False})
        except Exception:
            # Ignore bucket creation errors if already present or restricted permissions
            pass

    def validate_file(self, file_bytes: bytes, content_type: str) -> None:
        """Validates MIME type, non-empty payload, and maximum 10MB size limit."""
        if not file_bytes or len(file_bytes) == 0:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_IMAGE_PAYLOAD",
                message="Image file payload is empty."
            )

        if content_type.lower() not in self.ALLOWED_MIME_TYPES:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_FILE_TYPE",
                message=f"Unsupported file type '{content_type}'. Allowed types: jpeg, png, webp."
            )

        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="FILE_TOO_LARGE",
                message=f"File size exceeds maximum allowed limit of 10MB."
            )

    def upload_recipe_image(
        self,
        user_id: uuid.UUID,
        recipe_id: uuid.UUID,
        file_bytes: bytes,
        content_type: str,
        file_extension: str = "jpg"
    ) -> str:
        """
        Validates and uploads a recipe image file to Supabase Storage.
        Returns the safe canonical storage_path: users/{user_id}/recipes/{recipe_id}.{ext}
        """
        self.validate_file(file_bytes, content_type)
        self.ensure_bucket_exists()

        ext = file_extension.lstrip(".").lower()
        if not ext or ext not in {"jpg", "jpeg", "png", "webp"}:
            ext = "jpg"

        storage_path = f"users/{user_id}/recipes/{recipe_id}.{ext}"

        try:
            # Upload file bytes to private bucket
            res = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            return storage_path
        except Exception as exc:
            raise AppException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                code="STORAGE_UPLOAD_FAILED",
                message="Failed to upload recipe media to Supabase Storage object store.",
                details=[{"error": str(exc)}]
            )

    def delete_recipe_image(self, storage_path: str) -> None:
        """Deletes a recipe image from Supabase Storage."""
        try:
            self.client.storage.from_(self.BUCKET_NAME).remove([storage_path])
        except Exception:
            pass

storage_service = StorageService()
