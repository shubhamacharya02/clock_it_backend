import re
import json
import base64
from typing import Optional
from fastapi import status
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.llm import get_recipe_llm, get_vision_llm
from app.ai.schemas.recipe_output import ExtractedRecipe
from app.ai.prompts.recipe_prompts import RECIPE_EXTRACTION_PROMPT
from app.core.exceptions import AppException

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
    except Exception:
        pass

    # 2. Dual-mode fallback: Raw completion + robust JSON extraction
    try:
        llm = get_recipe_llm()
        raw_res = (RECIPE_EXTRACTION_PROMPT | llm).invoke({
            "input_type": input_type,
            "raw_content": raw_content
        })
        text = raw_res.content if hasattr(raw_res, "content") else str(raw_res)
        
        match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        json_str = match.group(1) if match else text[text.find("{"):text.rfind("}")+1]
        
        parsed = ExtractedRecipe.model_validate_json(json_str)
        if parsed and isinstance(parsed, ExtractedRecipe) and parsed.ingredients:
            return parsed
    except Exception:
        pass

    raise AppException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        code="LLM_STRUCTURE_ERROR",
        message="AI model produced null or invalid recipe structure."
    )
