import re
import json
import html
import httpx
from bs4 import BeautifulSoup
from fastapi import status
from app.core.exceptions import AppException

def _clean_text_string(text: str) -> str:
    """Cleans HTML entities, unicode fractions, and messy formatting from text."""
    if not text:
        return ""
    text = html.unescape(text)
    text = text.replace('¼', '0.25').replace('½', '0.5').replace('¾', '0.75').replace('⅓', '0.33').replace('⅔', '0.66')
    text = re.sub(r'\(\s*\((.*?)\)\s*\)', r'(\1)', text)
    return text.strip()

def _extract_instructions_from_json_ld(raw_insts) -> list[str]:
    """Recursively extracts cooking step text strings from JSON-LD HowToSection / HowToStep items."""
    formatted_insts = []
    if not raw_insts:
        return formatted_insts

    if isinstance(raw_insts, list):
        for item in raw_insts:
            formatted_insts.extend(_extract_instructions_from_json_ld(item))
    elif isinstance(raw_insts, dict):
        if raw_insts.get("@type") == "HowToSection" and "itemListElement" in raw_insts:
            formatted_insts.extend(_extract_instructions_from_json_ld(raw_insts["itemListElement"]))
        else:
            text_val = raw_insts.get("text") or raw_insts.get("name")
            if text_val and text_val not in ("Preparation", "How to make", "Instructions"):
                formatted_insts.append(_clean_text_string(str(text_val)))
    elif isinstance(raw_insts, str):
        cleaned = _clean_text_string(raw_insts)
        if cleaned:
            formatted_insts.append(cleaned)

    return formatted_insts

async def fetch_webpage_content(url: str) -> str:
    """
    Fetches HTML from target URL.
    1. Extracts schema.org JSON-LD Recipe structured data when present.
    2. Fallbacks to cleaned HTML body text stripping nav/scripts/styles.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise AppException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="URL_FETCH_FAILED",
                    message=f"Failed to fetch content from URL. Website returned HTTP {response.status_code}."
                )
            html_content = response.text
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="URL_FETCH_FAILED",
            message="Target website URL is unreachable or timed out.",
            details=[{"error": str(exc)}]
        )

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract schema.org JSON-LD Recipe structured data
        recipe_data = None
        for s in soup.find_all("script", type="application/ld+json"):
            if not s.string:
                continue
            try:
                data = json.loads(s.string)
                items = data.get("@graph", [data]) if isinstance(data, dict) else (data if isinstance(data, list) else [data])
                for item in items:
                    if isinstance(item, dict) and item.get("@type") == "Recipe":
                        recipe_data = item
                        break
                if recipe_data:
                    break
            except Exception:
                pass

        if recipe_data:
            name = _clean_text_string(recipe_data.get("name", "Web Recipe"))
            desc = _clean_text_string(recipe_data.get("description", ""))
            prep = _clean_text_string(str(recipe_data.get("prepTime", "")))
            cook = _clean_text_string(str(recipe_data.get("cookTime", "")))
            yield_servings = _clean_text_string(str(recipe_data.get("recipeYield", "")))

            raw_ings = recipe_data.get("recipeIngredient", [])
            ingredients_text = "\n".join([f"- {_clean_text_string(str(ing))}" for ing in raw_ings])

            raw_insts = recipe_data.get("recipeInstructions", [])
            extracted_steps = _extract_instructions_from_json_ld(raw_insts)
            instructions_text = "\n".join([f"- {step}" for step in extracted_steps])

            return f"""Recipe Title: {name}
Description: {desc}
Prep Time: {prep}
Cook Time: {cook}
Servings: {yield_servings}

Ingredients:
{ingredients_text}

Instructions:
{instructions_text}"""

        # 2. Fallback to clean HTML body text
        for tag in soup(["script", "style", "header", "footer", "nav", "noscript", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        if not text or len(text) < 50:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="URL_FETCH_FAILED",
                message="Extracted webpage text content is empty or insufficient."
            )
        return _clean_text_string(text[:15000])

    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="URL_FETCH_FAILED",
            message="Failed to parse webpage HTML content.",
            details=[{"error": str(exc)}]
        )
