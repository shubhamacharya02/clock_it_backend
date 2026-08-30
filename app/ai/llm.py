from langchain_google_vertexai import ChatVertexAI
from app.core.config import settings

def get_recipe_llm() -> ChatVertexAI:
    """Returns sub-second ChatVertexAI LLM for structured text parsing."""
    return ChatVertexAI(
        model_name=settings.VERTEX_MODEL_NAME,
        project=settings.VERTEX_PROJECT_ID,
        location=settings.VERTEX_LOCATION,
        temperature=0.0,
        max_output_tokens=8192,
    )

def get_vision_llm() -> ChatVertexAI:
    """Returns multimodal ChatVertexAI LLM for recipe image and camera parsing."""
    return ChatVertexAI(
        model_name=settings.VERTEX_VISION_MODEL_NAME,
        project=settings.VERTEX_PROJECT_ID,
        location=settings.VERTEX_LOCATION,
        temperature=0.0,
        max_output_tokens=8192,
    )
