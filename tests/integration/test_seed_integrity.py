import pytest
from scripts.seed_database import generate_100_products

def test_seed_catalog_dataset_integrity():
    catalog = generate_100_products()

    assert len(catalog) == 100, f"Expected 100 products, got {len(catalog)}"

    total_variants = sum(len(p["variants"]) for p in catalog)
    assert total_variants == 200, f"Expected 200 variants, got {total_variants}"

    brands = set(p["brand"] for p in catalog)
    assert len(brands) == 15, f"Expected 15 brands, got {len(brands)}"

    categories = set(p["category"] for p in catalog)
    assert len(categories) == 10, f"Expected 10 categories, got {len(categories)}"

    # Check edge cases fixtures
    amul_paneer = next(p for p in catalog if p["name"] == "Malai Paneer" and p["brand"] == "Amul")
    assert all(v["stock"] == 0 for v in amul_paneer["variants"]), "Amul Paneer must be out of stock"

    tofu = next(p for p in catalog if p["name"] == "Firm Organic Tofu" and p["brand"] == "Urban Platter")
    assert "paneer" in tofu["metadata"]["alternatives_for"], "Tofu must be marked as alternative for paneer"
    assert any(v["stock"] > 0 for v in tofu["variants"]), "Tofu variants must be in stock"
