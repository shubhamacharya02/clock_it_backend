from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from app.ai.chains.alternative_ranking import rank_alternatives_chain
from app.ai.schemas.alternative_output import RankedAlternativeResponse

class AlternativeState(TypedDict):
    canonical_name: str
    prefiltered_candidates: List[Dict[str, Any]]
    ranked_response: Optional[RankedAlternativeResponse]

def prepare_candidates_node(state: AlternativeState) -> AlternativeState:
    """Prepares in-stock candidates for LLM ranking."""
    return state

def rank_alternatives_node(state: AlternativeState) -> AlternativeState:
    """Invokes LLM ranking chain on pre-filtered in-stock candidates."""
    if not state["prefiltered_candidates"]:
        state["ranked_response"] = RankedAlternativeResponse(canonical_name=state["canonical_name"], alternatives=[])
        return state

    ranked = rank_alternatives_chain(
        canonical_name=state["canonical_name"],
        candidates=state["prefiltered_candidates"]
    )
    state["ranked_response"] = ranked
    return state

# Build LangGraph alternative workflow
workflow = StateGraph(AlternativeState)
workflow.add_node("prepare_candidates", prepare_candidates_node)
workflow.add_node("rank_alternatives", rank_alternatives_node)

workflow.set_entry_point("prepare_candidates")
workflow.add_edge("prepare_candidates", "rank_alternatives")
workflow.add_edge("rank_alternatives", END)

alternative_graph = workflow.compile()
