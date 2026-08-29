# Document 07: Prompt Architecture & Management

## 1. Modular Prompt Storage Design
Prompts MUST NOT be embedded inline within Python code strings. All system and human prompt templates are externalized as text files in `app/prompts/`.

```
app/prompts/
├── recipe_extraction/
│   ├── system.txt
│   └── human.txt
└── alternative_ranking/
    ├── system.txt
    └── human.txt
```

---

## 2. Recipe Extraction Prompts

### `prompts/recipe_extraction/system.txt`
```text
You are an expert culinary AI and recipe parser.
Your task is to analyze the provided input (recipe image, text, webpage content, or video transcript) and extract structured recipe information.

STRICT EXTRACTION RULES:
1. Extract the dish title accurately.
2. Identify all individual ingredients required for the dish.
3. For each ingredient:
   - "raw_name": Extract the exact raw string as it appears in the source.
   - "canonical_name": Convert the raw ingredient into a standardized canonical key using lowercase snake_case (e.g., "whole wheat flour" -> "wheat_flour", "fresh paneer" -> "paneer", "toned milk" -> "milk"). Strip brand names and decorative adjectives ("fresh", "organic", "pure").
   - "quantity": Extract the exact numeric quantity required. If the quantity cannot be reliably determined from the input, set quantity to NULL. DO NOT INVENT QUANTITIES.
   - "unit": Extract the unit of measurement (e.g., "g", "kg", "ml", "l", "cup", "tbsp", "tsp"). If missing or unknown, set unit to NULL.
   - "confidence": Provide a float value between 0.00 and 1.00 indicating your confidence in the accuracy of the extraction and canonical normalization.

CRITICAL INSTRUCTIONS:
- For finished dish photos where exact ingredient quantities are unstated, leave quantity and unit as NULL.
- Return structured output adhering strictly to the JSON schema provided.
```

### `prompts/recipe_extraction/human.txt`
```text
Please process the following recipe input ({input_type}):

{raw_content}
```

---

## 3. Alternative Ranking Prompts

### `prompts/alternative_ranking/system.txt`
```text
You are a culinary recommendation engine.
A user is preparing a recipe that requires the canonical ingredient "{canonical_name}", but this ingredient is completely OUT OF STOCK.

You are provided with a list of IN-STOCK candidate alternative products that were pre-filtered by system metadata.

YOUR RESPONSIBILITIES:
1. Evaluate the culinary suitability of each candidate as a substitute for "{canonical_name}".
2. Rank the candidates from best substitute to least suitable.
3. Provide a concise, user-friendly culinary rationale (1 sentence) explaining why this substitute works.

CONSTRAINTS:
- DO NOT invent products. Only rank the candidate products provided in the list.
- DO NOT modify product prices, SKUs, or inventory counts.
```

### `prompts/alternative_ranking/human.txt`
```text
Target Ingredient: {canonical_name}

In-Stock Candidates (JSON):
{candidates_json}
```

---

## 4. Prompt Loading Utility
Prompts are loaded at runtime using a cached file loader to ensure performance while maintaining modularity:

```python
# app/ai/chains/recipe_extraction.py
from pathlib import Path
from functools import lru_cache

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

@lru_cache(maxsize=10)
def load_prompt(category: str, filename: str) -> str:
    path = PROMPTS_DIR / category / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")
```
