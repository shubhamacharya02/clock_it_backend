import json
from typing import List, Dict, Any
from fastapi import status
from app.ai.llm import get_recipe_llm
from app.ai.schemas.alternative_output import RankedAlternativeResponse
from app.ai.prompts.alternative_prompts import ALTERNATIVE_RANKING_PROMPT
from app.core.exceptions import AppException

def rank_alternatives_chain(canonical_name: str, candidates: List[Dict[str, Any]]) -> RankedAlternativeResponse:
    """
    LangChain alternative ranking chain using ChatPromptTemplate and structured output.
    Ranks pre-filtered in-stock candidates and generates 1-sentence rationale.
    """
    candidates_json = json.dumps(candidates, indent=2)

    try:
        llm = get_recipe_llm()
        chain = ALTERNATIVE_RANKING_PROMPT | llm.with_structured_output(RankedAlternativeResponse)
        
        result: RankedAlternativeResponse = chain.invoke({
            "canonical_name": canonical_name,
            "candidates_json": candidates_json
        })
        
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
