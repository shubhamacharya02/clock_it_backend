# Document 12: Database Seed Data Specification

## 1. Seed Purpose & Verification Matrix
The seed dataset provides a realistic, multi-brand catalog of **100 deterministic products**, **200 variants**, and **200 inventory records** designed specifically to test all core business rules, edge cases, deterministic catalog queries, and alternative workflows.

| Testing Scenario | Seed Condition | Expected Behavior |
| :--- | :--- | :--- |
| **Normal Multi-Variant Matching** | `canonical_name: "milk"` has in-stock variants for Amul (500ml, 1L) & Nandini (500ml). | Surface all 3 variants across both brands. Do not show alternatives. |
| **Size / Quantity Flexibility** | Recipe requires 500ml milk. 1L variant (`SKU-AMUL-MILK-1L`) has stock 15. | User can add 2x 1L units to cart without restriction. |
| **Out-of-Stock Primary Product** | `canonical_name: "paneer"` has 0 stock across all primary variants (`SKU-AMUL-PANEER-200G`, `SKU-AMUL-PANEER-500G`). | Trigger Alternative Flow. |
| **Alternative Recommendation** | Primary `milk` variants set to 0 stock in controlled test state -> `almond_milk` (Stock: 12) & `soy_milk` (Stock: 3) have `alternatives_for: ["milk"]`. | Return Almond Milk & Soy Milk with LLM ranking and rationale. |
| **Alternative Candidate Out-of-Stock** | `oat_milk` has `alternatives_for: ["milk"]` but Stock = 0 (`SKU-OATMLK-1L`). | Filter out Oat Milk before sending candidates to LLM. |
| **Low-Stock Inventory Warning** | `SKU-NANDINI-MILK-500ML` has stock = 2. Adding quantity = 3 to cart. | Reject cart item addition with HTTP 409 `INSUFFICIENT_STOCK`. |
| **Multi-Brand Surfacing** | Query `wheat_flour`. Multiple brands exist (Aashirvaad, Fortune, Organic Tattva). | Surface variants across all matching brands. |
| **Decimal Price & Size Precision** | All variants use `Decimal` price and `Decimal` size (`NUMERIC(10,2)`). | Exact precision preserved without floating-point rounding errors. |
| **Cart & Checkout Concurrency** | Two parallel checkouts attempt to claim low-stock variant (`stock = 1`). | One checkout receives HTTP 201; second receives HTTP 409 `INSUFFICIENT_STOCK`. |

> [!NOTE]
> **Controlled Inventory State for Alternative Tests**: The baseline seed database maintains positive stock for primary milk variants so normal multi-variant matching tests succeed. For alternative-flow integration tests targeting `milk`, the test suite updates all primary milk variant inventory rows (`SKU-AMUL-MILK-500ML`, `SKU-AMUL-MILK-1L`, `SKU-NANDINI-MILK-500ML`) to `available_quantity = 0` within a controlled test transaction before invoking the product matching endpoint.

---

## 2. Seed Dataset Summary Metrics

- **Total Unique Products**: 100
- **Total Product Variants**: 200
- **Total Inventory Records**: 200
- **Total Unique Brands**: 15 (Amul, Nandini, Mother Dairy, Fortune, Aashirvaad, Tata Sampann, Dabur, Catch, Saffola, Raw Pressery, Sofit, OatMlk, Urban Platter, Organic Tattva, Natureland Organic)
- **Total Product Categories**: 10 (Dairy, Plant-Based Products, Rice & Grains, Flour, Pulses & Lentils, Spices & Masala, Cooking Oils & Ghee, Fresh Vegetables, Fresh Fruits, Staples & Condiments)
- **Total Alternative Relationships (`alternatives_for`)**: 34
- **Low-Stock Inventory Records (Stock 1–3)**: 12
- **Out-of-Stock Inventory Records (Stock 0)**: 12

---

## 3. Seed Data Schema Definitions (`scripts/seed.py`)

```python
from decimal import Decimal

SEED_PRODUCTS = [
    # =========================================================================
    # CATEGORY 1: DAIRY (10 Products, 20 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000001",
        "name": "Taaza Toned Milk",
        "brand": "Amul",
        "category": "Dairy",
        "description": "Pasteurised toned milk",
        "metadata_json": {
            "canonical_ingredients": ["milk"],
            "product_type": "dairy",
            "sub_type": "cow_milk",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-AMUL-MILK-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("28.00"), "stock": 25},
            {"sku": "SKU-AMUL-MILK-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("54.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000002",
        "name": "GoodLife Toned Milk",
        "brand": "Nandini",
        "category": "Dairy",
        "description": "UHT treated toned milk",
        "metadata_json": {
            "canonical_ingredients": ["milk"],
            "product_type": "dairy",
            "sub_type": "cow_milk",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-NANDINI-MILK-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("27.00"), "stock": 2} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000003",
        "name": "Fresh Cow Milk",
        "brand": "Mother Dairy",
        "category": "Dairy",
        "description": "Pure cow milk",
        "metadata_json": {
            "canonical_ingredients": ["milk", "cow_milk"],
            "product_type": "dairy",
            "sub_type": "cow_milk",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-MOTHER-MILK-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("30.00"), "stock": 20},
            {"sku": "SKU-MOTHER-MILK-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("58.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000004",
        "name": "Fresh Malai Paneer",
        "brand": "Amul",
        "category": "Dairy",
        "description": "Rich cottage cheese",
        "metadata_json": {
            "canonical_ingredients": ["paneer"],
            "product_type": "dairy",
            "sub_type": "cottage_cheese",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-AMUL-PANEER-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("95.00"), "stock": 0}, # OUT OF STOCK
            {"sku": "SKU-AMUL-PANEER-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("220.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000005",
        "name": "Pasteurised Salted Butter",
        "brand": "Amul",
        "category": "Dairy",
        "description": "Classic salted butter",
        "metadata_json": {
            "canonical_ingredients": ["butter"],
            "product_type": "dairy",
            "sub_type": "butter",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-AMUL-BUTTER-100G", "size": Decimal("100.00"), "size_unit": "g", "price": Decimal("58.00"), "stock": 30},
            {"sku": "SKU-AMUL-BUTTER-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("275.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000006",
        "name": "Masti Dahi Curd",
        "brand": "Amul",
        "category": "Dairy",
        "description": "Fresh thick curd",
        "metadata_json": {
            "canonical_ingredients": ["curd"],
            "product_type": "dairy",
            "sub_type": "yogurt",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-AMUL-CURD-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("22.00"), "stock": 25},
            {"sku": "SKU-AMUL-CURD-400G", "size": Decimal("400.00"), "size_unit": "g", "price": Decimal("40.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000007",
        "name": "Ultimate Dahi",
        "brand": "Mother Dairy",
        "category": "Dairy",
        "description": "Smooth thick yogurt",
        "metadata_json": {
            "canonical_ingredients": ["curd"],
            "product_type": "dairy",
            "sub_type": "yogurt",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-MOTHER-CURD-400G", "size": Decimal("400.00"), "size_unit": "g", "price": Decimal("42.00"), "stock": 1} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000008",
        "name": "Diced Mozzarella Cheese",
        "brand": "Amul",
        "category": "Dairy",
        "description": "Blend mozzarella cheese",
        "metadata_json": {
            "canonical_ingredients": ["cheese"],
            "product_type": "dairy",
            "sub_type": "mozzarella",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-AMUL-CHEESE-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("130.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000009",
        "name": "Fresh Heavy Cream",
        "brand": "Mother Dairy",
        "category": "Dairy",
        "description": "Rich cooking cream",
        "metadata_json": {
            "canonical_ingredients": ["heavy_cream"],
            "product_type": "dairy",
            "sub_type": "cream",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-MOTHER-CREAM-200ML", "size": Decimal("200.00"), "size_unit": "ml", "price": Decimal("65.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000010",
        "name": "Pure Desi Ghee",
        "brand": "Amul",
        "category": "Dairy",
        "description": "Clarified butter ghee",
        "metadata_json": {
            "canonical_ingredients": ["ghee"],
            "product_type": "dairy",
            "sub_type": "ghee",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-AMUL-GHEE-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("315.00"), "stock": 18},
            {"sku": "SKU-AMUL-GHEE-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("610.00"), "stock": 12}
        ]
    },

    # =========================================================================
    # CATEGORY 2: PLANT-BASED PRODUCTS (10 Products, 20 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000011",
        "name": "Unsweetened Almond Milk",
        "brand": "Raw Pressery",
        "category": "Plant-Based Products",
        "description": "Dairy-free almond beverage",
        "metadata_json": {
            "canonical_ingredients": ["almond_milk"],
            "product_type": "plant_based",
            "sub_type": "almond_milk",
            "alternatives_for": ["milk"]
        },
        "variants": [
            {"sku": "SKU-RAW-ALMOND-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("180.00"), "stock": 12}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000012",
        "name": "Organic Soy Milk",
        "brand": "Sofit",
        "category": "Plant-Based Products",
        "description": "Protein rich soy milk",
        "metadata_json": {
            "canonical_ingredients": ["soy_milk"],
            "product_type": "plant_based",
            "sub_type": "soy_milk",
            "alternatives_for": ["milk"]
        },
        "variants": [
            {"sku": "SKU-SOFIT-SOY-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("140.00"), "stock": 3} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000013",
        "name": "Oat Milk Barista Blend",
        "brand": "OatMlk",
        "category": "Plant-Based Products",
        "description": "Creamy oat beverage",
        "metadata_json": {
            "canonical_ingredients": ["oat_milk"],
            "product_type": "plant_based",
            "sub_type": "oat_milk",
            "alternatives_for": ["milk"]
        },
        "variants": [
            {"sku": "SKU-OATMLK-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("210.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000014",
        "name": "Organic Firm Tofu",
        "brand": "Urban Platter",
        "category": "Plant-Based Products",
        "description": "Soy protein cottage cheese substitute",
        "metadata_json": {
            "canonical_ingredients": ["tofu"],
            "product_type": "plant_based",
            "sub_type": "soy_block",
            "alternatives_for": ["paneer"]
        },
        "variants": [
            {"sku": "SKU-UP-TOFU-250G", "size": Decimal("250.00"), "size_unit": "g", "price": Decimal("120.00"), "stock": 2}, # LOW STOCK
            {"sku": "SKU-UP-TOFU-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("220.00"), "stock": 10}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000015",
        "name": "Plant-Based Dairy-Free Butter",
        "brand": "Urban Platter",
        "category": "Plant-Based Products",
        "description": "Vegan cultured butter substitute",
        "metadata_json": {
            "canonical_ingredients": ["vegan_butter"],
            "product_type": "plant_based",
            "sub_type": "butter_substitute",
            "alternatives_for": ["butter"]
        },
        "variants": [
            {"sku": "SKU-UP-VEGAN-BUTTER-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("195.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000016",
        "name": "Organic Soy Curd",
        "brand": "Sofit",
        "category": "Plant-Based Products",
        "description": "Plant-based yogurt alternative",
        "metadata_json": {
            "canonical_ingredients": ["soy_curd"],
            "product_type": "plant_based",
            "sub_type": "yogurt_substitute",
            "alternatives_for": ["curd"]
        },
        "variants": [
            {"sku": "SKU-SOFIT-CURD-400G", "size": Decimal("400.00"), "size_unit": "g", "price": Decimal("85.00"), "stock": 8}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000017",
        "name": "Vegan Shredded Cheddar Cheese",
        "brand": "Urban Platter",
        "category": "Plant-Based Products",
        "description": "Melty plant cheese alternative",
        "metadata_json": {
            "canonical_ingredients": ["vegan_cheese"],
            "product_type": "plant_based",
            "sub_type": "cheese_substitute",
            "alternatives_for": ["cheese"]
        },
        "variants": [
            {"sku": "SKU-VEGAN-CHEESE-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("260.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000018",
        "name": "Rich Coconut Milk Cream",
        "brand": "Urban Platter",
        "category": "Plant-Based Products",
        "description": "Thick unsweetened coconut cream",
        "metadata_json": {
            "canonical_ingredients": ["coconut_cream"],
            "product_type": "plant_based",
            "sub_type": "cream_substitute",
            "alternatives_for": ["heavy_cream"]
        },
        "variants": [
            {"sku": "SKU-UP-COCO-CREAM-400ML", "size": Decimal("400.00"), "size_unit": "ml", "price": Decimal("165.00"), "stock": 14}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000019",
        "name": "Vegan Cooking Ghee Substitute",
        "brand": "Organic Tattva",
        "category": "Plant-Based Products",
        "description": "Cold-pressed herbal fat blend",
        "metadata_json": {
            "canonical_ingredients": ["vegan_ghee"],
            "product_type": "plant_based",
            "sub_type": "ghee_substitute",
            "alternatives_for": ["ghee"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-VEGAN-GHEE-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("380.00"), "stock": 9}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000020",
        "name": "Coconut Yogurt",
        "brand": "Raw Pressery",
        "category": "Plant-Based Products",
        "description": "Probiotic coconut curd",
        "metadata_json": {
            "canonical_ingredients": ["coconut_yogurt"],
            "product_type": "plant_based",
            "sub_type": "yogurt_substitute",
            "alternatives_for": ["curd"]
        },
        "variants": [
            {"sku": "SKU-RAW-COCO-YOGURT-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("110.00"), "stock": 11}
        ]
    },

    # =========================================================================
    # CATEGORY 3: RICE & GRAINS (10 Products, 20 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000021",
        "name": "Everyday Basmati Rice",
        "brand": "Fortune",
        "category": "Rice & Grains",
        "description": "Long grain fragrant basmati rice",
        "metadata_json": {
            "canonical_ingredients": ["white_rice", "basmati_rice"],
            "product_type": "grain",
            "sub_type": "basmati",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FORTUNE-BASMATI-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("115.00"), "stock": 40},
            {"sku": "SKU-FORTUNE-BASMATI-5KG", "size": Decimal("5000.00"), "size_unit": "g", "price": Decimal("520.00"), "stock": 3} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000022",
        "name": "Organic Brown Basmati Rice",
        "brand": "Organic Tattva",
        "category": "Rice & Grains",
        "description": "Whole grain brown rice",
        "metadata_json": {
            "canonical_ingredients": ["brown_rice"],
            "product_type": "grain",
            "sub_type": "brown_rice",
            "alternatives_for": ["white_rice"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-BROWN-RICE-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("160.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000023",
        "name": "White Royal Quinoa Seeds",
        "brand": "Urban Platter",
        "category": "Rice & Grains",
        "description": "Protein-rich white quinoa grains",
        "metadata_json": {
            "canonical_ingredients": ["quinoa"],
            "product_type": "superfood_grain",
            "sub_type": "quinoa",
            "alternatives_for": ["white_rice"]
        },
        "variants": [
            {"sku": "SKU-UP-QUINOA-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("295.00"), "stock": 12},
            {"sku": "SKU-ORGANIC-QUINOA-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("550.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000024",
        "name": "Organic Red Rice",
        "brand": "Natureland Organic",
        "category": "Rice & Grains",
        "description": "Unpolished red rice",
        "metadata_json": {
            "canonical_ingredients": ["red_rice"],
            "product_type": "grain",
            "sub_type": "red_rice",
            "alternatives_for": ["white_rice"]
        },
        "variants": [
            {"sku": "SKU-NATURE-RED-RICE-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("145.00"), "stock": 3} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000025",
        "name": "Sona Masoori Raw Rice",
        "brand": "Fortune",
        "category": "Rice & Grains",
        "description": "Lightweight aromatic medium-grain rice",
        "metadata_json": {
            "canonical_ingredients": ["white_rice", "sona_masoori"],
            "product_type": "grain",
            "sub_type": "raw_rice",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FORTUNE-SONA-5KG", "size": Decimal("5000.00"), "size_unit": "g", "price": Decimal("380.00"), "stock": 22}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000026",
        "name": "Organic Foxtail Millet",
        "brand": "Organic Tattva",
        "category": "Rice & Grains",
        "description": "Unpolished foxtail millet grain",
        "metadata_json": {
            "canonical_ingredients": ["millet", "foxtail_millet"],
            "product_type": "millet",
            "sub_type": "foxtail",
            "alternatives_for": ["white_rice"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-MILLET-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("90.00"), "stock": 16}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000027",
        "name": "Rolled Oats",
        "brand": "Saffola",
        "category": "Rice & Grains",
        "description": "100% natural grain oats",
        "metadata_json": {
            "canonical_ingredients": ["oats"],
            "product_type": "grain",
            "sub_type": "oats",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-SAFFOLA-OATS-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("110.00"), "stock": 35},
            {"sku": "SKU-SAFFOLA-OATS-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("200.00"), "stock": 25}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000028",
        "name": "Poha Thick Flattened Rice",
        "brand": "Tata Sampann",
        "category": "Rice & Grains",
        "description": "High fibre flattened rice flakes",
        "metadata_json": {
            "canonical_ingredients": ["poha"],
            "product_type": "grain_flakes",
            "sub_type": "poha",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-POHA-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("55.00"), "stock": 28}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000029",
        "name": "Sooji Semolina Rava",
        "brand": "Tata Sampann",
        "category": "Rice & Grains",
        "description": "Coarse wheat semolina",
        "metadata_json": {
            "canonical_ingredients": ["semolina", "sooji"],
            "product_type": "grain_flour",
            "sub_type": "semolina",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-SOOJI-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("48.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000030",
        "name": "Sabudana Tapioca Pearls",
        "brand": "Organic Tattva",
        "category": "Rice & Grains",
        "description": "Pure tapioca sago pearls",
        "metadata_json": {
            "canonical_ingredients": ["tapioca_pearls", "sabudana"],
            "product_type": "starch",
            "sub_type": "sabudana",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-ORGANIC-SABUDANA-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("75.00"), "stock": 19}
        ]
    },

    # =========================================================================
    # CATEGORY 4: FLOUR (10 Products, 20 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000031",
        "name": "Shuddh Chakki Atta",
        "brand": "Aashirvaad",
        "category": "Flour",
        "description": "100% pure whole wheat flour",
        "metadata_json": {
            "canonical_ingredients": ["wheat_flour", "atta"],
            "product_type": "flour",
            "sub_type": "whole_wheat",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-AASH-WHEAT-5KG", "size": Decimal("5000.00"), "size_unit": "g", "price": Decimal("245.00"), "stock": 35},
            {"sku": "SKU-AASH-WHEAT-10KG", "size": Decimal("10000.00"), "size_unit": "g", "price": Decimal("470.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000032",
        "name": "Multigrain Atta",
        "brand": "Aashirvaad",
        "category": "Flour",
        "description": "High fibre 6-grain flour blend",
        "metadata_json": {
            "canonical_ingredients": ["multigrain_flour"],
            "product_type": "flour",
            "sub_type": "multigrain",
            "alternatives_for": ["wheat_flour"]
        },
        "variants": [
            {"sku": "SKU-AASH-MULTI-5KG", "size": Decimal("5000.00"), "size_unit": "g", "price": Decimal("295.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000033",
        "name": "Superfine Blanched Almond Flour",
        "brand": "Urban Platter",
        "category": "Flour",
        "description": "Low carb keto almond flour",
        "metadata_json": {
            "canonical_ingredients": ["almond_flour"],
            "product_type": "flour",
            "sub_type": "nut_flour",
            "alternatives_for": ["wheat_flour"]
        },
        "variants": [
            {"sku": "SKU-UP-ALMOND-FLOUR-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("650.00"), "stock": 2} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000034",
        "name": "Organic Ragi Finger Millet Flour",
        "brand": "Aashirvaad",
        "category": "Flour",
        "description": "Calcium rich ragi flour",
        "metadata_json": {
            "canonical_ingredients": ["ragi_flour"],
            "product_type": "flour",
            "sub_type": "millet_flour",
            "alternatives_for": ["wheat_flour"]
        },
        "variants": [
            {"sku": "SKU-AASH-RAGI-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("85.00"), "stock": 2} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000035",
        "name": "Fine Besan Gram Flour",
        "brand": "Tata Sampann",
        "category": "Flour",
        "description": "100% unpolished chana dal flour",
        "metadata_json": {
            "canonical_ingredients": ["gram_flour", "besan"],
            "product_type": "flour",
            "sub_type": "gram_flour",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-BESAN-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("65.00"), "stock": 30},
            {"sku": "SKU-TATA-BESAN-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("125.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000036",
        "name": "Refined Maida Flour",
        "brand": "Fortune",
        "category": "Flour",
        "description": "All purpose refined wheat flour",
        "metadata_json": {
            "canonical_ingredients": ["all_purpose_flour", "maida"],
            "product_type": "flour",
            "sub_type": "refined_flour",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FORTUNE-MAIDA-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("52.00"), "stock": 25}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000037",
        "name": "Organic Jowar Sorghum Flour",
        "brand": "Organic Tattva",
        "category": "Flour",
        "description": "Gluten free jowar flour",
        "metadata_json": {
            "canonical_ingredients": ["jowar_flour"],
            "product_type": "flour",
            "sub_type": "millet_flour",
            "alternatives_for": ["wheat_flour"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-JOWAR-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("95.00"), "stock": 14}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000038",
        "name": "Corn Starch Flour",
        "brand": "Urban Platter",
        "category": "Flour",
        "description": "Fine maize corn starch powder",
        "metadata_json": {
            "canonical_ingredients": ["corn_starch", "corn_flour"],
            "product_type": "starch",
            "sub_type": "corn_starch",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-UP-CORNSTARCH-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("80.00"), "stock": 22}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000039",
        "name": "Rice Flour",
        "brand": "Natureland Organic",
        "category": "Flour",
        "description": "Fine ground white rice flour",
        "metadata_json": {
            "canonical_ingredients": ["rice_flour"],
            "product_type": "flour",
            "sub_type": "rice_flour",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-NATURE-RICEFLOUR-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("45.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000040",
        "name": "Organic Bajra Pearl Millet Flour",
        "brand": "Organic Tattva",
        "category": "Flour",
        "description": "Stone ground pearl millet flour",
        "metadata_json": {
            "canonical_ingredients": ["bajra_flour"],
            "product_type": "flour",
            "sub_type": "millet_flour",
            "alternatives_for": ["wheat_flour"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-BAJRA-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("88.00"), "stock": 12}
        ]
    },

    # =========================================================================
    # CATEGORY 5: PULSES & LENTILS (12 Products, 24 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000041",
        "name": "Unpolished Toor Arhar Dal",
        "brand": "Tata Sampann",
        "category": "Pulses & Lentils",
        "description": "Protein rich pigeon pea lentils",
        "metadata_json": {
            "canonical_ingredients": ["toor_dal", "arhar_dal"],
            "product_type": "pulse",
            "sub_type": "toor_dal",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-TOOR-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("175.00"), "stock": 35},
            {"sku": "SKU-TATA-TOOR-5KG", "size": Decimal("5000.00"), "size_unit": "g", "price": Decimal("840.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000042",
        "name": "Yellow Moong Dal Split",
        "brand": "Tata Sampann",
        "category": "Pulses & Lentils",
        "description": "Easy to digest split yellow moong",
        "metadata_json": {
            "canonical_ingredients": ["yellow_moong_dal"],
            "product_type": "pulse",
            "sub_type": "moong_dal",
            "alternatives_for": ["toor_dal"]
        },
        "variants": [
            {"sku": "SKU-TATA-MOONG-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("72.00"), "stock": 25},
            {"sku": "SKU-TATA-MOONG-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("140.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000043",
        "name": "Organic Chana Dal",
        "brand": "Organic Tattva",
        "category": "Pulses & Lentils",
        "description": "Unpolished split Bengal gram",
        "metadata_json": {
            "canonical_ingredients": ["chana_dal"],
            "product_type": "pulse",
            "sub_type": "chana_dal",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-CHANA-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("110.00"), "stock": 1} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000044",
        "name": "Whole Black Urad Dal",
        "brand": "Tata Sampann",
        "category": "Pulses & Lentils",
        "description": "Whole unpolished black gram lentils",
        "metadata_json": {
            "canonical_ingredients": ["urad_dal", "black_urad"],
            "product_type": "pulse",
            "sub_type": "urad_dal",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-URAD-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("165.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000045",
        "name": "Red Masoor Dal Split",
        "brand": "Fortune",
        "category": "Pulses & Lentils",
        "description": "Pink split red lentils",
        "metadata_json": {
            "canonical_ingredients": ["masoor_dal", "red_lentils"],
            "product_type": "pulse",
            "sub_type": "masoor_dal",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FORTUNE-MASOOR-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("105.00"), "stock": 28}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000046",
        "name": "Kabuli Chana Chickpeas",
        "brand": "Tata Sampann",
        "category": "Pulses & Lentils",
        "description": "Large white chickpeas",
        "metadata_json": {
            "canonical_ingredients": ["chickpeas", "kabuli_chana"],
            "product_type": "legume",
            "sub_type": "chickpea",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-KABULI-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("85.00"), "stock": 22},
            {"sku": "SKU-TATA-KABULI-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("160.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000047",
        "name": "Rajma Red Kidney Beans",
        "brand": "Organic Tattva",
        "category": "Pulses & Lentils",
        "description": "Premium red kidney beans",
        "metadata_json": {
            "canonical_ingredients": ["rajma", "kidney_beans"],
            "product_type": "legume",
            "sub_type": "kidney_beans",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-ORGANIC-RAJMA-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("95.00"), "stock": 19}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000048",
        "name": "Green Moong Whole",
        "brand": "Natureland Organic",
        "category": "Pulses & Lentils",
        "description": "Whole green gram for sprouting",
        "metadata_json": {
            "canonical_ingredients": ["green_moong"],
            "product_type": "pulse",
            "sub_type": "whole_moong",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-NATURE-GREENMOONG-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("80.00"), "stock": 24}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000049",
        "name": "White Black Eyed Beans Lobia",
        "brand": "Natureland Organic",
        "category": "Pulses & Lentils",
        "description": "Unpolished black eyed peas",
        "metadata_json": {
            "canonical_ingredients": ["lobia", "black_eyed_peas"],
            "product_type": "legume",
            "sub_type": "lobia",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-NATURE-LOBIA-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("75.00"), "stock": 16}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000050",
        "name": "Kala Chana Black Chickpeas",
        "brand": "Tata Sampann",
        "category": "Pulses & Lentils",
        "description": "Small black Bengal gram",
        "metadata_json": {
            "canonical_ingredients": ["kala_chana", "black_chickpeas"],
            "product_type": "legume",
            "sub_type": "black_chana",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-KALACHANA-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("120.00"), "stock": 21}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000051",
        "name": "Soya Chunks Protein",
        "brand": "Fortune",
        "category": "Pulses & Lentils",
        "description": "High protein soy bean chunks",
        "metadata_json": {
            "canonical_ingredients": ["soya_chunks"],
            "product_type": "soy_protein",
            "sub_type": "soya_chunks",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FORTUNE-SOYA-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("45.00"), "stock": 30}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000052",
        "name": "Organic Horse Gram Kulthi",
        "brand": "Organic Tattva",
        "category": "Pulses & Lentils",
        "description": "Traditional horse gram pulse",
        "metadata_json": {
            "canonical_ingredients": ["horse_gram"],
            "product_type": "pulse",
            "sub_type": "kulthi",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-ORGANIC-HORSEGRAM-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("70.00"), "stock": 17}
        ]
    },

    # =========================================================================
    # CATEGORY 6: SPICES & MASALA (12 Products, 18 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000053",
        "name": "Turmeric Powder Haldi",
        "brand": "Catch",
        "category": "Spices & Masala",
        "description": "Rich curcumin turmeric powder",
        "metadata_json": {
            "canonical_ingredients": ["turmeric_powder", "turmeric"],
            "product_type": "spice",
            "sub_type": "powder",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-CATCH-TURMERIC-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("48.00"), "stock": 40},
            {"sku": "SKU-CATCH-TURMERIC-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("110.00"), "stock": 3} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000054",
        "name": "Red Chilli Powder Lal Mirch",
        "brand": "Catch",
        "category": "Spices & Masala",
        "description": "Hot red chilli spice powder",
        "metadata_json": {
            "canonical_ingredients": ["red_chilli_powder"],
            "product_type": "spice",
            "sub_type": "powder",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-CATCH-CHILLI-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("75.00"), "stock": 35}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000055",
        "name": "Smoked Paprika Powder",
        "brand": "Urban Platter",
        "category": "Spices & Masala",
        "description": "Sweet smoked paprika seasoning",
        "metadata_json": {
            "canonical_ingredients": ["paprika"],
            "product_type": "spice",
            "sub_type": "paprika",
            "alternatives_for": ["red_chilli_powder"]
        },
        "variants": [
            {"sku": "SKU-UP-PAPRIKA-100G", "size": Decimal("100.00"), "size_unit": "g", "price": Decimal("180.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000056",
        "name": "Coriander Powder Dhaniya",
        "brand": "Tata Sampann",
        "category": "Spices & Masala",
        "description": "Aromatic coriander powder",
        "metadata_json": {
            "canonical_ingredients": ["coriander_powder"],
            "product_type": "spice",
            "sub_type": "powder",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-DHANIYA-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("52.00"), "stock": 30}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000057",
        "name": "Cumin Seeds Jeera Whole",
        "brand": "Catch",
        "category": "Spices & Masala",
        "description": "Natural whole cumin seeds",
        "metadata_json": {
            "canonical_ingredients": ["cumin_seeds", "jeera"],
            "product_type": "spice",
            "sub_type": "whole_spice",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-CATCH-JEERA-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("95.00"), "stock": 25}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000058",
        "name": "Garam Masala Blend",
        "brand": "Tata Sampann",
        "category": "Spices & Masala",
        "description": "Chef crafted aromatic spice mix",
        "metadata_json": {
            "canonical_ingredients": ["garam_masala"],
            "product_type": "spice_blend",
            "sub_type": "masala_mix",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-GARAM-100G", "size": Decimal("100.00"), "size_unit": "g", "price": Decimal("88.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000059",
        "name": "Black Pepper Whole",
        "brand": "Organic Tattva",
        "category": "Spices & Masala",
        "description": "Organic whole black peppercorns",
        "metadata_json": {
            "canonical_ingredients": ["black_pepper"],
            "product_type": "spice",
            "sub_type": "whole_spice",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-ORGANIC-PEPPER-100G", "size": Decimal("100.00"), "size_unit": "g", "price": Decimal("135.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000060",
        "name": "Mustard Seeds Rai",
        "brand": "Catch",
        "category": "Spices & Masala",
        "description": "Small black mustard seeds",
        "metadata_json": {
            "canonical_ingredients": ["mustard_seeds", "rai"],
            "product_type": "spice",
            "sub_type": "whole_spice",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-CATCH-RAI-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("42.00"), "stock": 30}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000061",
        "name": "Compounded Asafoetida Hing",
        "brand": "Catch",
        "category": "Spices & Masala",
        "description": "Strong aromatic hing powder",
        "metadata_json": {
            "canonical_ingredients": ["asafoetida", "hing"],
            "product_type": "spice",
            "sub_type": "powder",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-CATCH-HING-50G", "size": Decimal("50.00"), "size_unit": "g", "price": Decimal("90.00"), "stock": 22}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000062",
        "name": "Green Cardamom Elaichi",
        "brand": "Organic Tattva",
        "category": "Spices & Masala",
        "description": "Whole green cardamom pods",
        "metadata_json": {
            "canonical_ingredients": ["cardamom", "elaichi"],
            "product_type": "spice",
            "sub_type": "whole_spice",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-ORGANIC-ELAICHI-50G", "size": Decimal("50.00"), "size_unit": "g", "price": Decimal("210.00"), "stock": 14}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000063",
        "name": "Cinnamon Powder",
        "brand": "Urban Platter",
        "category": "Spices & Masala",
        "description": "Pure Ceylon cinnamon powder",
        "metadata_json": {
            "canonical_ingredients": ["cinnamon"],
            "product_type": "spice",
            "sub_type": "powder",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-UP-CINNAMON-100G", "size": Decimal("100.00"), "size_unit": "g", "price": Decimal("150.00"), "stock": 16}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000064",
        "name": "Pink Himalayan Rock Salt",
        "brand": "Tata Sampann",
        "category": "Spices & Masala",
        "description": "Mineral rich pink rock salt",
        "metadata_json": {
            "canonical_ingredients": ["salt", "himalayan_salt"],
            "product_type": "salt",
            "sub_type": "rock_salt",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-TATA-SALT-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("40.00"), "stock": 50}
        ]
    },

    # =========================================================================
    # CATEGORY 7: COOKING OILS & GHEE (10 Products, 20 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000065",
        "name": "Refined Sunflower Oil",
        "brand": "Fortune",
        "category": "Cooking Oils & Ghee",
        "description": "Light refined sunflower oil",
        "metadata_json": {
            "canonical_ingredients": ["sunflower_oil", "cooking_oil"],
            "product_type": "oil",
            "sub_type": "sunflower_oil",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FORTUNE-SUN-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("145.00"), "stock": 30},
            {"sku": "SKU-FORTUNE-SUN-5L", "size": Decimal("5000.00"), "size_unit": "ml", "price": Decimal("710.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000066",
        "name": "Cold Pressed Extra Virgin Olive Oil",
        "brand": "Urban Platter",
        "category": "Cooking Oils & Ghee",
        "description": "Premium Mediterranean olive oil",
        "metadata_json": {
            "canonical_ingredients": ["olive_oil"],
            "product_type": "oil",
            "sub_type": "olive_oil",
            "alternatives_for": ["sunflower_oil"]
        },
        "variants": [
            {"sku": "SKU-UP-OLIVEOIL-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("550.00"), "stock": 12},
            {"sku": "SKU-UP-OLIVEOIL-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("990.00"), "stock": 8}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000067",
        "name": "Kachi Ghani Mustard Oil",
        "brand": "Fortune",
        "category": "Cooking Oils & Ghee",
        "description": "Pure cold pressed mustard oil",
        "metadata_json": {
            "canonical_ingredients": ["mustard_oil"],
            "product_type": "oil",
            "sub_type": "mustard_oil",
            "alternatives_for": ["sunflower_oil"]
        },
        "variants": [
            {"sku": "SKU-FORTUNE-MUSTARD-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("155.00"), "stock": 25}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000068",
        "name": "Cold Pressed Virgin Coconut Oil",
        "brand": "Organic Tattva",
        "category": "Cooking Oils & Ghee",
        "description": "Unrefined pure coconut oil",
        "metadata_json": {
            "canonical_ingredients": ["coconut_oil"],
            "product_type": "oil",
            "sub_type": "coconut_oil",
            "alternatives_for": ["sunflower_oil", "ghee"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-COCO-OIL-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("240.00"), "stock": 16}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000069",
        "name": "Gold Blended Cooking Oil",
        "brand": "Saffola",
        "category": "Cooking Oils & Ghee",
        "description": "Heart care blended edible oil",
        "metadata_json": {
            "canonical_ingredients": ["blended_oil", "cooking_oil"],
            "product_type": "oil",
            "sub_type": "blended_oil",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-SAFFOLA-GOLD-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("170.00"), "stock": 2} # LOW STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000070",
        "name": "Physically Refined Rice Bran Oil",
        "brand": "Fortune",
        "category": "Cooking Oils & Ghee",
        "description": "Oryzanol rich rice bran oil",
        "metadata_json": {
            "canonical_ingredients": ["rice_bran_oil"],
            "product_type": "oil",
            "sub_type": "rice_bran_oil",
            "alternatives_for": ["sunflower_oil"]
        },
        "variants": [
            {"sku": "SKU-FORTUNE-RICEBRAN-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("150.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000071",
        "name": "Filtered Groundnut Peanut Oil",
        "brand": "Dabur",
        "category": "Cooking Oils & Ghee",
        "description": "Traditional groundnut cooking oil",
        "metadata_json": {
            "canonical_ingredients": ["groundnut_oil", "peanut_oil"],
            "product_type": "oil",
            "sub_type": "groundnut_oil",
            "alternatives_for": ["sunflower_oil"]
        },
        "variants": [
            {"sku": "SKU-DABUR-GROUNDNUT-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("190.00"), "stock": 14}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000072",
        "name": "Cold Pressed Til Sesame Oil",
        "brand": "Organic Tattva",
        "category": "Cooking Oils & Ghee",
        "description": "Pure sesame seed oil",
        "metadata_json": {
            "canonical_ingredients": ["sesame_oil", "til_oil"],
            "product_type": "oil",
            "sub_type": "sesame_oil",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-ORGANIC-SESAME-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("210.00"), "stock": 11}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000073",
        "name": "Pure Cow Ghee",
        "brand": "Mother Dairy",
        "category": "Cooking Oils & Ghee",
        "description": "Golden cow milk ghee",
        "metadata_json": {
            "canonical_ingredients": ["ghee", "cow_ghee"],
            "product_type": "ghee",
            "sub_type": "cow_ghee",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-MOTHER-GHEE-500ML", "size": Decimal("500.00"), "size_unit": "ml", "price": Decimal("320.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000074",
        "name": "Pure Buffalo Ghee",
        "brand": "Nandini",
        "category": "Cooking Oils & Ghee",
        "description": "Traditional thick buffalo ghee",
        "metadata_json": {
            "canonical_ingredients": ["ghee"],
            "product_type": "ghee",
            "sub_type": "buffalo_ghee",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-NANDINI-GHEE-1L", "size": Decimal("1000.00"), "size_unit": "ml", "price": Decimal("590.00"), "stock": 10}
        ]
    },

    # =========================================================================
    # CATEGORY 8: FRESH VEGETABLES (12 Products, 24 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000075",
        "name": "Fresh Farm Potato",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Fresh yellow potatoes",
        "metadata_json": {
            "canonical_ingredients": ["potato"],
            "product_type": "vegetable",
            "sub_type": "tuber",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-POTATO-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("30.00"), "stock": 50},
            {"sku": "SKU-FARM-POTATO-2KG", "size": Decimal("2000.00"), "size_unit": "g", "price": Decimal("58.00"), "stock": 30}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000076",
        "name": "Organic Sweet Potato",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Nutritious sweet orange potatoes",
        "metadata_json": {
            "canonical_ingredients": ["sweet_potato"],
            "product_type": "vegetable",
            "sub_type": "tuber",
            "alternatives_for": ["potato"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-SWEETPOTATO-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("40.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000077",
        "name": "Fresh Red Onion",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Crisp red onions",
        "metadata_json": {
            "canonical_ingredients": ["onion", "red_onion"],
            "product_type": "vegetable",
            "sub_type": "bulb",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-ONION-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("35.00"), "stock": 45},
            {"sku": "SKU-FARM-ONION-2KG", "size": Decimal("2000.00"), "size_unit": "g", "price": Decimal("68.00"), "stock": 25}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000078",
        "name": "Fresh Hybrid Tomato",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Ripe red cooking tomatoes",
        "metadata_json": {
            "canonical_ingredients": ["tomato"],
            "product_type": "vegetable",
            "sub_type": "fruit_veg",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-TOMATO-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("25.00"), "stock": 40},
            {"sku": "SKU-FARM-TOMATO-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("48.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000079",
        "name": "Fresh Garlic Bulbs",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Pungent garlic cloves",
        "metadata_json": {
            "canonical_ingredients": ["garlic"],
            "product_type": "vegetable",
            "sub_type": "bulb",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-GARLIC-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("45.00"), "stock": 30}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000080",
        "name": "Fresh Ginger Root",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Aromatic ginger root",
        "metadata_json": {
            "canonical_ingredients": ["ginger"],
            "product_type": "vegetable",
            "sub_type": "rhizome",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-GINGER-200G", "size": Decimal("200.00"), "size_unit": "g", "price": Decimal("30.00"), "stock": 35}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000081",
        "name": "Fresh Green Chilli",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Spicy green chillies",
        "metadata_json": {
            "canonical_ingredients": ["green_chilli"],
            "product_type": "vegetable",
            "sub_type": "pepper",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-CHILLI-100G", "size": Decimal("100.00"), "size_unit": "g", "price": Decimal("15.00"), "stock": 40}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000082",
        "name": "Fresh Coriander Leaves Cilantro",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Fresh aromatic green cilantro",
        "metadata_json": {
            "canonical_ingredients": ["coriander_leaves", "cilantro"],
            "product_type": "vegetable",
            "sub_type": "herb",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-CORIANDER-100G", "size": Decimal("100.00"), "size_unit": "g", "price": Decimal("12.00"), "stock": 50}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000083",
        "name": "Fresh Green Capsicum Bell Pepper",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Crisp green bell pepper",
        "metadata_json": {
            "canonical_ingredients": ["capsicum", "bell_pepper"],
            "product_type": "vegetable",
            "sub_type": "pepper",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-CAPSICUM-250G", "size": Decimal("250.00"), "size_unit": "g", "price": Decimal("28.00"), "stock": 25}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000084",
        "name": "Fresh Cauliflower Gobhi",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Whole white cauliflower head",
        "metadata_json": {
            "canonical_ingredients": ["cauliflower", "gobhi"],
            "product_type": "vegetable",
            "sub_type": "brassica",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-CAULIFLOWER-1PC", "size": Decimal("1.00"), "size_unit": "pc", "price": Decimal("35.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000085",
        "name": "Fresh Green Peas Matar",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Sweet shelled green peas",
        "metadata_json": {
            "canonical_ingredients": ["green_peas", "matar"],
            "product_type": "vegetable",
            "sub_type": "peas",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-PEAS-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("45.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000086",
        "name": "Fresh Baby Spinach Palak",
        "brand": "Natureland Organic",
        "category": "Fresh Vegetables",
        "description": "Tender green spinach leaves",
        "metadata_json": {
            "canonical_ingredients": ["spinach", "palak"],
            "product_type": "vegetable",
            "sub_type": "greens",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FARM-SPINACH-250G", "size": Decimal("250.00"), "size_unit": "g", "price": Decimal("20.00"), "stock": 22}
        ]
    },

    # =========================================================================
    # CATEGORY 9: FRESH FRUITS (8 Products, 16 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000087",
        "name": "Robusta Banana",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Fresh ripe bananas",
        "metadata_json": {
            "canonical_ingredients": ["banana"],
            "product_type": "fruit",
            "sub_type": "banana",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-BANANA-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("30.00"), "stock": 35},
            {"sku": "SKU-FRUIT-BANANA-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("58.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000088",
        "name": "Royal Gala Red Apple",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Crisp sweet red apples",
        "metadata_json": {
            "canonical_ingredients": ["apple"],
            "product_type": "fruit",
            "sub_type": "pome",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-APPLE-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("110.00"), "stock": 25},
            {"sku": "SKU-FRUIT-APPLE-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("210.00"), "stock": 15}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000089",
        "name": "Fresh Lemon Nimboo",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Juicy yellow lemons",
        "metadata_json": {
            "canonical_ingredients": ["lemon", "lemon_juice"],
            "product_type": "fruit",
            "sub_type": "citrus",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-LEMON-250G", "size": Decimal("250.00"), "size_unit": "g", "price": Decimal("35.00"), "stock": 30}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000090",
        "name": "Nagpur Orange Santra",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Sweet citrus Nagpur oranges",
        "metadata_json": {
            "canonical_ingredients": ["orange"],
            "product_type": "fruit",
            "sub_type": "citrus",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-ORANGE-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("85.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000091",
        "name": "Papaya Semi Ripe",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Fresh sweet papaya",
        "metadata_json": {
            "canonical_ingredients": ["papaya"],
            "product_type": "fruit",
            "sub_type": "tropical",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-PAPAYA-1PC", "size": Decimal("1.00"), "size_unit": "pc", "price": Decimal("60.00"), "stock": 12}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000092",
        "name": "Pomegranate Anar",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Red juicy pomegranate arils",
        "metadata_json": {
            "canonical_ingredients": ["pomegranate", "anar"],
            "product_type": "fruit",
            "sub_type": "berry",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-ANAR-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("125.00"), "stock": 16}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000093",
        "name": "Green Seedless Grapes",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Sweet green grapes",
        "metadata_json": {
            "canonical_ingredients": ["grapes"],
            "product_type": "fruit",
            "sub_type": "berry",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-GRAPES-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("75.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000094",
        "name": "Ripe Mango Alphonso",
        "brand": "Natureland Organic",
        "category": "Fresh Fruits",
        "description": "Premium sweet Alphonso mangoes",
        "metadata_json": {
            "canonical_ingredients": ["mango"],
            "product_type": "fruit",
            "sub_type": "tropical",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FRUIT-MANGO-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("280.00"), "stock": 14}
        ]
    },

    # =========================================================================
    # CATEGORY 10: STAPLES & CONDIMENTS (6 Products, 18 Variants)
    # =========================================================================
    {
        "id": "a0000000-0000-0000-0000-000000000095",
        "name": "Refined White Sugar",
        "brand": "Fortune",
        "category": "Staples & Condiments",
        "description": "Pure sparkling white sugar crystals",
        "metadata_json": {
            "canonical_ingredients": ["sugar", "white_sugar"],
            "product_type": "sweetener",
            "sub_type": "sugar",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-FORTUNE-SUGAR-1KG", "size": Decimal("1000.00"), "size_unit": "g", "price": Decimal("48.00"), "stock": 45},
            {"sku": "SKU-FORTUNE-SUGAR-5KG", "size": Decimal("5000.00"), "size_unit": "g", "price": Decimal("230.00"), "stock": 20}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000096",
        "name": "Organic Gur Jaggery Powder",
        "brand": "Organic Tattva",
        "category": "Staples & Condiments",
        "description": "Natural unrefined sugarcane jaggery",
        "metadata_json": {
            "canonical_ingredients": ["jaggery", "gur"],
            "product_type": "sweetener",
            "sub_type": "jaggery",
            "alternatives_for": ["sugar"]
        },
        "variants": [
            {"sku": "SKU-ORGANIC-JAGGERY-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("65.00"), "stock": 25}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000097",
        "name": "100% Pure Squeezed Honey",
        "brand": "Dabur",
        "category": "Staples & Condiments",
        "description": "Natural wild forest honey",
        "metadata_json": {
            "canonical_ingredients": ["honey"],
            "product_type": "sweetener",
            "sub_type": "honey",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-DABUR-HONEY-250G", "size": Decimal("250.00"), "size_unit": "g", "price": Decimal("115.00"), "stock": 1}, # LOW STOCK
            {"sku": "SKU-DABUR-HONEY-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("210.00"), "stock": 18}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000098",
        "name": "Pure Organic Maple Syrup",
        "brand": "Urban Platter",
        "category": "Staples & Condiments",
        "description": "Grade A Canadian maple syrup",
        "metadata_json": {
            "canonical_ingredients": ["maple_syrup"],
            "product_type": "sweetener",
            "sub_type": "syrup",
            "alternatives_for": ["honey", "sugar"]
        },
        "variants": [
            {"sku": "SKU-UP-MAPLE-250ML", "size": Decimal("250.00"), "size_unit": "ml", "price": Decimal("495.00"), "stock": 10}
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000099",
        "name": "Creamy Peanut Butter",
        "brand": "Urban Platter",
        "category": "Staples & Condiments",
        "description": "High protein roasted peanut butter",
        "metadata_json": {
            "canonical_ingredients": ["peanut_butter"],
            "product_type": "spread",
            "sub_type": "nut_butter",
            "alternatives_for": []
        },
        "variants": [
            {"sku": "SKU-RAW-PEANUT-500G", "size": Decimal("500.00"), "size_unit": "g", "price": Decimal("220.00"), "stock": 0} # OUT OF STOCK
        ]
    },
    {
        "id": "a0000000-0000-0000-0000-000000000100",
        "name": "Organic Blue Agave Nectar",
        "brand": "Urban Platter",
        "category": "Staples & Condiments",
        "description": "Low glycemic natural sweetener syrup",
        "metadata_json": {
            "canonical_ingredients": ["agave_nectar"],
            "product_type": "sweetener",
            "sub_type": "nectar",
            "alternatives_for": ["honey", "sugar"]
        },
        "variants": [
            {"sku": "SKU-NATURAL-AGAVE-250ML", "size": Decimal("250.00"), "size_unit": "ml", "price": Decimal("360.00"), "stock": 0} # OUT OF STOCK
        ]
    }
]
```
