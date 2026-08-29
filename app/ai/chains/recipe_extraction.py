import base64
from typing import Optional
from fastapi import status
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.llm import get_recipe_llm, get_vision_llm
from app.ai.schemas.recipe_output import ExtractedRecipe
from app.prompts.prompt_loader import load_prompt
from app.main import AppException

def extract_recipe_chain(
    input_type: str,
    raw_content: str,
    is_vision: bool = False,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg"
) -> ExtractedRecipe:
    """
    LangChain recipe extraction chain using structured output validation.
    Returns ExtractedRecipe Pydantic schema or raises 502 LLM_STRUCTURE_ERROR.
    """
    system_prompt = load_prompt("recipe_extraction", "system.txt")
    human_prompt_template = load_prompt("recipe_extraction", "human.txt")
    human_text = human_prompt_template.format(input_type=input_type, raw_content=raw_content)

    try:
        if is_vision and image_bytes:
            llm = get_vision_llm()
            structured_llm = llm.with_structured_output(ExtractedRecipe)
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=[
                        {"type": "text", "text": human_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}
                        }
                    ]
                )
            ]
        else:
            llm = get_recipe_llm()
            structured_llm = llm.with_structured_output(ExtractedRecipe)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_text)
            ]

        result: ExtractedRecipe = structured_llm.invoke(messages)
        if not result or not isinstance(result, ExtractedRecipe):
            raise ValueError("Structured output returned null or invalid object.")
        return result

    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="LLM_STRUCTURE_ERROR",
            message="AI model produced structurally invalid or unparseable recipe output.",
            details=[{"error": str(exc)}]
        )
