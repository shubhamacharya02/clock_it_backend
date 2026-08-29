from pathlib import Path
from functools import lru_cache

BASE_PROMPTS_DIR = Path(__file__).parent

@lru_cache(maxsize=32)
def load_prompt(category: str, filename: str) -> str:
    """Loads external prompt template text file from disk."""
    file_path = BASE_PROMPTS_DIR / category / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt template file not found: {file_path}")
    return file_path.read_text(encoding="utf-8").strip()
