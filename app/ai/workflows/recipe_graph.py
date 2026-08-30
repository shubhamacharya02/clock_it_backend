import re
from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from app.ai.chains.recipe_extraction import extract_recipe_chain
from app.ai.schemas.recipe_output import ExtractedRecipe, ExtractedIngredient
from app.core.config import settings

class RecipeState(TypedDict):
    input_type: str
    raw_content: str
    is_vision: bool
    image_bytes: Optional[bytes]
    mime_type: str
    extracted_recipe: Optional[ExtractedRecipe]
    processed_ingredients: List[Dict[str, Any]]

def prepare_input_node(state: RecipeState) -> RecipeState:
    return state

def extract_recipe_node(state: RecipeState) -> RecipeState:
    """
    Extracts structured recipe from input using LangChain extract_recipe_chain.
    Does NOT return mock/fallback data; propagates real LLM output directly.
    """
    extracted = extract_recipe_chain(
        input_type=state['input_type'],
        raw_content=state['raw_content'],
        is_vision=state['is_vision'],
        image_bytes=state['image_bytes'],
        mime_type=state['mime_type']
    )

    state['extracted_recipe'] = extracted
    return state

def normalize_canonical_name(name: str) -> str:
    text = name.lower().strip()
    strip_words = ['organic', 'fresh', 'farm', 'picked', 'pure', 'natural', 'chopped', 'boiled', 'diced', 'sliced', 'ground']
    for word in strip_words:
        text = re.sub(rf'{word}', '', text)

    text_clean = text.strip()
    if 'atta' in text_clean or 'wheat flour' in text_clean:
        return 'wheat_flour'
    if 'almond milk' in text_clean:
        return 'almond_milk'
    if 'soy milk' in text_clean:
        return 'soy_milk'
    if 'oat milk' in text_clean:
        return 'oat_milk'
    if 'toned milk' in text_clean or 'cow milk' in text_clean or 'milk' in text_clean:
        return 'milk'
    if 'paneer' in text_clean or 'cottage cheese' in text_clean:
        return 'paneer'
    if 'tofu' in text_clean:
        return 'tofu'

    clean_str = re.sub(r'[^\w\s]', '', text_clean)
    snake_str = re.sub(r'\s+', '_', clean_str).strip('_')
    return snake_str if snake_str else 'unknown_ingredient'

def normalize_and_evaluate_node(state: RecipeState) -> RecipeState:
    extracted = state['extracted_recipe']
    processed = []
    threshold = settings.CONFIDENCE_THRESHOLD

    if extracted and extracted.ingredients:
        for ing in extracted.ingredients:
            canonical = normalize_canonical_name(ing.canonical_name or ing.raw_name)
            confidence = float(ing.confidence)
            requires_confirmation = confidence < threshold

            processed.append({
                'raw_name': ing.raw_name,
                'canonical_name': canonical,
                'quantity': ing.quantity,
                'unit': ing.unit,
                confidence: confidence,
                requires_confirmation: requires_confirmation
            })

    state['processed_ingredients'] = processed
    return state

workflow = StateGraph(RecipeState)
workflow.add_node('prepare_input', prepare_input_node)
workflow.add_node('extract_recipe', extract_recipe_node)
workflow.add_node('normalize_and_evaluate', normalize_and_evaluate_node)

workflow.set_entry_point('prepare_input')
workflow.add_edge('prepare_input', 'extract_recipe')
workflow.add_edge('extract_recipe', 'normalize_and_evaluate')
workflow.add_edge('normalize_and_evaluate', END)

recipe_graph = workflow.compile()
