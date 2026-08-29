# Document 11: Supabase Storage Architecture

## 1. Storage Access Model & Bucket Policy
The system relies exclusively on **Supabase Storage** for persisting uploaded recipe images and camera snapshots.

- **Bucket Name**: `recipe-media`
- **Access Policy**: Private storage access preferred. The canonical application reference is the internal Supabase storage path. Public URLs are **NOT** required, and the bucket is not made public merely to support Vertex AI.
- **Allowed Declared MIME Types**: `image/jpeg`, `image/png`, `image/webp`
- **Maximum File Size**: `10 MB` (10,485,760 bytes)

---

## 2. Object Path Naming & Security Hierarchy
To enforce user isolation, prevent path traversal attacks, and eliminate collision risks from arbitrary client filenames, all files are assigned a safe server-generated path based on `user_id`, `recipe_id`, and the validated extension:

```
recipe-media/
└── users/
    └── {user_id}/
        └── recipes/
            └── {recipe_id}.{extension}
```

Example Canonical Path:
`users/123e4567-e89b-12d3-a456-426614174000/recipes/8f3b2e1a-4c9d-4e5f-b6a7-8c9d0e1f2a3b.jpg`

- **Database Reference**: PostgreSQL stores this exact string (`storage_path`) in `recipes.storage_path` as the database source of truth.

---

## 3. Storage Service Implementation Specification

```python
# app/services/storage_service.py
import uuid
from typing import BinaryIO
from supabase import create_client, Client
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket = "recipe-media"
        self.max_bytes = 10 * 1024 * 1024 # 10 MB

    async def upload_recipe_image(self, user_id: uuid.UUID, recipe_id: uuid.UUID, file: UploadFile) -> str:
        # 1. Validate declared Content-Type header
        allowed_mime_map = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp"
        }
        mime_type = file.content_type
        if mime_type not in allowed_mime_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{mime_type}'. Allowed MIME types: {list(allowed_mime_map.keys())}"
            )

        # 2. Enforce 10MB limit via bounded stream reading (avoids reading unbounded payloads into memory)
        content_bytes = bytearray()
        chunk_size = 1024 * 1024 # 1 MB chunks
        
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            content_bytes.extend(chunk)
            if len(content_bytes) > self.max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File payload size exceeds maximum limit of 10 MB"
                )

        if len(content_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image payload provided"
            )

        # 3. Derive safe destination storage path using server-generated IDs
        extension = allowed_mime_map[mime_type]
        storage_path = f"users/{user_id}/recipes/{recipe_id}.{extension}"

        # 4. Upload file to Supabase Storage
        try:
            res = self.client.storage.from_(self.bucket).upload(
                path=storage_path,
                file=bytes(content_bytes),
                file_options={"content-type": mime_type, "upsert": "true"}
            )
            # Return canonical storage path reference (Source of Truth for PostgreSQL)
            return storage_path
        except Exception as e:
            # Storage failure returns standardized 502 Bad Gateway response
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Supabase Storage Upload Failed: {str(e)}"
            )
```

---

## 4. Single Source Constraint & Failure Policy
- **Sole Object Store**: Supabase Storage is the single configured object store.
- **No Local Filesystem Fallback**: If Supabase credentials are missing or the API call fails, the system MUST NOT write files to `/tmp` or local disk.
- **No AWS S3 / GCP GCS Fallback**: Alternative cloud providers or CDNs are prohibited.
- **Error Behavior**: Storage API downtime or upload failures report a standardized `HTTP 502 Bad Gateway` error to the client, preventing corrupt or orphaned recipe entries.
