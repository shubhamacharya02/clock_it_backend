import uuid
import pytest
from unittest.mock import MagicMock
from app.services.storage_service import StorageService
from app.main import AppException

def test_storage_validation_empty_file():
    service = StorageService(client=MagicMock())
    with pytest.raises(AppException) as exc_info:
        service.validate_file(b"", "image/jpeg")
    assert exc_info.value.code == "INVALID_IMAGE_PAYLOAD"
    assert exc_info.value.status_code == 400

def test_storage_validation_invalid_mime():
    service = StorageService(client=MagicMock())
    with pytest.raises(AppException) as exc_info:
        service.validate_file(b"dummy_bytes", "application/pdf")
    assert exc_info.value.code == "INVALID_FILE_TYPE"
    assert exc_info.value.status_code == 400

def test_storage_validation_file_too_large():
    service = StorageService(client=MagicMock())
    large_bytes = b"x" * (10 * 1024 * 1024 + 1)
    with pytest.raises(AppException) as exc_info:
        service.validate_file(large_bytes, "image/jpeg")
    assert exc_info.value.code == "FILE_TOO_LARGE"
    assert exc_info.value.status_code == 400

def test_safe_storage_path_formatting():
    mock_client = MagicMock()
    mock_client.storage.list_buckets.return_value = []
    service = StorageService(client=mock_client)

    user_id = uuid.uuid4()
    recipe_id = uuid.uuid4()
    path = service.upload_recipe_image(user_id, recipe_id, b"valid_image_content", "image/png", "png")

    assert path == f"users/{user_id}/recipes/{recipe_id}.png"

def test_storage_upload_failure_502():
    mock_client = MagicMock()
    mock_client.storage.list_buckets.return_value = []
    mock_client.storage.from_().upload.side_effect = Exception("Supabase Storage Error")
    
    service = StorageService(client=mock_client)

    user_id = uuid.uuid4()
    recipe_id = uuid.uuid4()

    with pytest.raises(AppException) as exc_info:
        service.upload_recipe_image(user_id, recipe_id, b"image_data", "image/jpeg", "jpg")

    assert exc_info.value.status_code == 502
    assert exc_info.value.code == "STORAGE_UPLOAD_FAILED"
