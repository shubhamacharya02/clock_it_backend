from langchain_core.prompts import ChatPromptTemplate

ALTERNATIVE_RANKING_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an intelligent grocery recommendation assistant.

Given a missing canonical ingredient and a list of pre-filtered in-stock candidate products, rank the candidates by suitability as a direct substitute.

For each candidate, produce a 1-sentence concise, human-readable rationale explaining why it is a suitable alternative (e.g., 'Tofu provides a comparable texture and high protein content to cottage cheese in savory curries.')."""
    ),
    (
        "human",
        """Target Canonical Ingredient: {canonical_name}

Candidate In-Stock Products:
{candidates_json}

Rank these candidates and provide 1-sentence rationales."""
    )
])
