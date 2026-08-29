import json
from typing import List, Dict, Any
from fastapi import status
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.llm import get_recipe_llm
from app.ai.schemas.alternative_output import RankedAlternativeResponse
from app.prompts.prompt_loader import load_prompt
from app.core.exceptions import AppException

def rank_alternatives_chain(canonical_name: str, candidates: List[Dict[str, Any]]) -> RankedAlternativeResponse:
    """
    LangChain alternative ranking chain.
    Ranks pre-filtered in-stock candidates and generates 1-sentence rationale.
    """
    system_prompt = load_prompt("alternative_ranking", "system.txt")
    human_prompt_template = load_prompt("alternative_ranking", "human.txt")
    
    candidates_json = json.dumps(candidates, indent=2)
    human_text = human_prompt_template.format(canonical_name=canonical_name, candidates_json=candidates_json)

    try:
        llm = get_recipe_llm()
        structured_llm = llm.with_structured_output(RankedAlternativeResponse)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_text)
        ]
        result: RankedAlternativeResponse = structured_llm.invoke(messages)
        if not result or not isinstance(result, RankedAlternativeResponse):
            raise ValueError("Alternative output returned null or invalid object.")
        return result
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="LLM_STRUCTURE_ERROR",
            message="AI model produced structurally invalid alternative ranking output.",
            details=[{"error": str(exc)}]
        )
