import os
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from app.core.config import settings

def get_recipe_llm() -> Any:
    """
    Returns LLM instance for structured text parsing.
    Supports both Google AI Studio API Key (GEMINI_API_KEY / GOOGLE_API_KEY)
    and GCP Vertex AI Credentials (VERTEX_PROJECT_ID).
    """
    api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if api_key:
        model_name = settings.VERTEX_MODEL_NAME.replace("-002", "").replace("-001", "")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.0,
            max_output_tokens=2048,
        )

    return ChatVertexAI(
        model_name=settings.VERTEX_MODEL_NAME,
        project=settings.VERTEX_PROJECT_ID,
        location=settings.VERTEX_LOCATION,
        temperature=0.0,
        max_output_tokens=2048,
    )

def get_vision_llm() -> Any:
    """
    Returns multimodal LLM instance for recipe image and camera parsing.
    """
    api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if api_key:
        model_name = settings.VERTEX_VISION_MODEL_NAME.replace("-002", "").replace("-001", "")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.0,
            max_output_tokens=2048,
        )

    return ChatVertexAI(
        model_name=settings.VERTEX_VISION_MODEL_NAME,
        project=settings.VERTEX_PROJECT_ID,
        location=settings.VERTEX_LOCATION,
        temperature=0.0,
        max_output_tokens=2048,
    )
