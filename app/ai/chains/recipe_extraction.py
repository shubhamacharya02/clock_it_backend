import re
import json
import base64
import logging
from typing import Optional
from fastapi import status
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.llm import get_recipe_llm, get_vision_llm
from app.ai.schemas.recipe_output import ExtractedRecipe
from app.ai.prompts.recipe_prompts import RECIPE_EXTRACTION_PROMPT
from app.core.exceptions import AppException

logger = logging.getLogger("uvicorn.error")

def extract_recipe_chain(
    input_type: str,
    raw_content: str,
    is_vision: bool = False,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg"
) -> ExtractedRecipe:
    """
    Dual-mode recipe extraction chain.
    1. Tries structured output (Function Calling) first.
    2. Fallbacks to raw LLM completion + Markdown JSON extraction for long transcripts/webpages.
    """
    # 1. Try structured function calling output
    try:
        if is_vision and image_bytes:
            llm = get_vision_llm()
            structured_llm = llm.with_structured_output(ExtractedRecipe)
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            formatted_messages = RECIPE_EXTRACTION_PROMPT.format_messages(
                input_type=input_type,
                raw_content=raw_content
            )
            
            system_msg = formatted_messages[0]
            human_msg_content = [
                {"type": "text", "text": formatted_messages[1].content},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}
                }
            ]
            messages = [system_msg, HumanMessage(content=human_msg_content)]
            result = structured_llm.invoke(messages)
        else:
            llm = get_recipe_llm()
            structured_llm = RECIPE_EXTRACTION_PROMPT | llm.with_structured_output(ExtractedRecipe)
            result = structured_llm.invoke({
                "input_type": input_type,
                "raw_content": raw_content
            })

        if result and isinstance(result, ExtractedRecipe) and result.ingredients:
            return result
    except Exception as exc:
        logger.warning("Structured Function Calling extraction failed: %s", exc)

    # 2. Dual-mode fallback: Raw completion + robust JSON extraction
    try:
        llm = get_recipe_llm()
        raw_res = (RECIPE_EXTRACTION_PROMPT | llm).invoke({
            "input_type": input_type,
            "raw_content": raw_content
        })
        text = raw_res.content if hasattr(raw_res, "content") else str(raw_res)
        
        match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if match:
            json_str = match.group(1)
        else:
            start = text.find("{")
            end = text.rfind("}")
            json_str = text[start:end+1] if start != -1 and end != -1 else ""

        if json_str:
            parsed = ExtractedRecipe.model_validate_json(json_str)
            if parsed and isinstance(parsed, ExtractedRecipe) and parsed.ingredients:
                return parsed
    except Exception as exc:
        logger.error("Raw LLM JSON fallback extraction failed: %s", exc, exc_info=True)

    raise AppException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        code="LLM_STRUCTURE_ERROR",
        message="AI model produced null or invalid recipe structure."
    )
