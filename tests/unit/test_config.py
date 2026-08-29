import pytest
from app.core.config import settings

def test_settings_load():
    assert settings.APP_NAME == "AI Recipe-to-Commerce Backend"
    assert settings.JWT_EXPIRATION_SECONDS == 3600
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.CONFIDENCE_THRESHOLD == 0.70
    assert settings.VERTEX_MODEL_NAME == "gemini-1.5-flash"
    assert settings.VERTEX_VISION_MODEL_NAME == "gemini-1.5-pro"
