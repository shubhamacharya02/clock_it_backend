from app.ai.schemas.recipe_output import ExtractedRecipe, ExtractedIngredient
from app.ai.workflows.recipe_graph import normalize_canonical_name

def test_pydantic_structured_output_schema():
    ingredient = ExtractedIngredient(
        raw_name="2 cups organic fresh farm milk",
        canonical_name="toned milk",
        quantity=2.0,
        unit="cups",
        confidence=0.95
    )
    assert ingredient.raw_name == "2 cups organic fresh farm milk"
    assert ingredient.canonical_name == "toned milk"

    recipe = ExtractedRecipe(
        title="Homemade Kheer",
        servings=4,
        ingredients=[ingredient]
    )
    assert recipe.title == "Homemade Kheer"
    assert len(recipe.ingredients) == 1

def test_canonical_normalization():
    assert normalize_canonical_name("atta") == "wheat_flour"
    assert normalize_canonical_name("whole wheat flour") == "wheat_flour"
    assert normalize_canonical_name("fresh organic farm milk") == "milk"
    assert normalize_canonical_name("toned milk") == "milk"
    assert normalize_canonical_name("almond milk") == "almond_milk"
    assert normalize_canonical_name("fresh paneer") == "paneer"
    assert normalize_canonical_name("tofu") == "tofu"
