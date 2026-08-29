import asyncio
import uuid
from decimal import Decimal
from typing import List, Dict, Any
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory

# Seed catalog constants
BRANDS = [
    "Amul", "Nandini", "Mother Dairy", "Nestle", "Milky Mist",
    "Raw Pressery", "Sofit", "OatMlk", "Urban Platter", "Aashirvaad",
    "Fortune", "Tata Simply Better", "Pillsbury", "Sunfeast", "Organic Tattva"
]

CATEGORIES = [
    "Dairy", "Alternative Dairy", "Atta & Flours", "Rice & Grains",
    "Pulses & Dals", "Cooking Oils", "Spices & Masalas", "Snacks & Biscuits",
    "Beverages", "Baking & Desserts"
]

def generate_100_products() -> List[Dict[str, Any]]:
    """Generates deterministic 100-product, 200-variant catalog matching Document 12."""
    products_data = []

    # --- 1. Dairy Products (10 Products, 20 Variants) ---
    # P1: Amul Taaza Milk
    products_data.append({
        "name": "Taaza Toned Milk", "brand": "Amul", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["milk"], "product_type": "dairy", "sub_type": "cow_milk", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-AMUL-MILK-500ML", "size": Decimal("500.00"), "unit": "ml", "price": Decimal("27.00"), "stock": 25},
            {"sku": "SKU-AMUL-MILK-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("54.00"), "stock": 15}
        ]
    })
    # P2: Nandini Toned Milk
    products_data.append({
        "name": "Nandini Toned Milk", "brand": "Nandini", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["milk"], "product_type": "dairy", "sub_type": "cow_milk", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-NANDINI-MILK-500ML", "size": Decimal("500.00"), "unit": "ml", "price": Decimal("24.00"), "stock": 30},
            {"sku": "SKU-NANDINI-MILK-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("48.00"), "stock": 20}
        ]
    })
    # P3: Mother Dairy Toned Milk
    products_data.append({
        "name": "Mother Dairy Toned Milk", "brand": "Mother Dairy", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["milk"], "product_type": "dairy", "sub_type": "cow_milk", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-MD-MILK-500ML", "size": Decimal("500.00"), "unit": "ml", "price": Decimal("26.00"), "stock": 18},
            {"sku": "SKU-MD-MILK-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("52.00"), "stock": 12}
        ]
    })
    # P4: Amul Malai Paneer (OUT OF STOCK EDGE CASE FIXTURE)
    products_data.append({
        "name": "Malai Paneer", "brand": "Amul", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["paneer"], "product_type": "dairy", "sub_type": "paneer", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-AMUL-PANEER-200G", "size": Decimal("200.00"), "unit": "g", "price": Decimal("90.00"), "stock": 0},
            {"sku": "SKU-AMUL-PANEER-500G", "size": Decimal("500.00"), "unit": "g", "price": Decimal("210.00"), "stock": 0}
        ]
    })
    # P5: Milky Mist Paneer (OUT OF STOCK EDGE CASE FIXTURE)
    products_data.append({
        "name": "Fresh Paneer", "brand": "Milky Mist", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["paneer"], "product_type": "dairy", "sub_type": "paneer", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-MILKYMIST-PANEER-200G", "size": Decimal("200.00"), "unit": "g", "price": Decimal("95.00"), "stock": 0},
            {"sku": "SKU-MILKYMIST-PANEER-500G", "size": Decimal("500.00"), "unit": "g", "price": Decimal("220.00"), "stock": 0}
        ]
    })
    # P6-P10: Curd, Butter, Cheese, Ghee, Cream
    products_data.append({
        "name": "Masti Dahi Curd", "brand": "Amul", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["curd", "dahi"], "product_type": "dairy", "sub_type": "curd", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-AMUL-CURD-400G", "size": Decimal("400.00"), "unit": "g", "price": Decimal("35.00"), "stock": 25},
            {"sku": "SKU-AMUL-CURD-1KG", "size": Decimal("1000.00"), "unit": "g", "price": Decimal("75.00"), "stock": 10}
        ]
    })
    products_data.append({
        "name": "Salted Butter", "brand": "Amul", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["butter"], "product_type": "dairy", "sub_type": "butter", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-AMUL-BUTTER-100G", "size": Decimal("100.00"), "unit": "g", "price": Decimal("56.00"), "stock": 40},
            {"sku": "SKU-AMUL-BUTTER-500G", "size": Decimal("500.00"), "unit": "g", "price": Decimal("275.00"), "stock": 15}
        ]
    })
    products_data.append({
        "name": "Processed Cheese Slices", "brand": "Amul", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["cheese"], "product_type": "dairy", "sub_type": "cheese", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-AMUL-CHEESE-200G", "size": Decimal("200.00"), "unit": "g", "price": Decimal("140.00"), "stock": 20},
            {"sku": "SKU-AMUL-CHEESE-400G", "size": Decimal("400.00"), "unit": "g", "price": Decimal("270.00"), "stock": 8}
        ]
    })
    products_data.append({
        "name": "Pure Cow Ghee", "brand": "Mother Dairy", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["ghee"], "product_type": "dairy", "sub_type": "ghee", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-MD-GHEE-500ML", "size": Decimal("500.00"), "unit": "ml", "price": Decimal("325.00"), "stock": 12},
            {"sku": "SKU-MD-GHEE-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("630.00"), "stock": 6}
        ]
    })
    products_data.append({
        "name": "Fresh Cream", "brand": "Nestle", "category": "Dairy",
        "metadata": {"canonical_ingredients": ["cream", "fresh_cream"], "product_type": "dairy", "sub_type": "cream", "alternatives_for": []},
        "variants": [
            {"sku": "SKU-NESTLE-CREAM-250ML", "size": Decimal("250.00"), "unit": "ml", "price": Decimal("75.00"), "stock": 14},
            {"sku": "SKU-NESTLE-CREAM-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("260.00"), "stock": 5}
        ]
    })

    # --- 2. Alternative Dairy Products (10 Products, 20 Variants - Alternative Relationships) ---
    # P11: Raw Pressery Almond Milk (Alternative for milk)
    products_data.append({
        "name": "Almond Milk Unsweetened", "brand": "Raw Pressery", "category": "Alternative Dairy",
        "metadata": {"canonical_ingredients": ["almond_milk"], "product_type": "plant_based", "sub_type": "almond_milk", "alternatives_for": ["milk"]},
        "variants": [
            {"sku": "SKU-RAW-ALMOND-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("180.00"), "stock": 15},
            {"sku": "SKU-RAW-ALMOND-250ML", "size": Decimal("250.00"), "unit": "ml", "price": Decimal("60.00"), "stock": 25}
        ]
    })
    # P12: Sofit Soy Milk (Alternative for milk)
    products_data.append({
        "name": "Soy Milk Natural", "brand": "Sofit", "category": "Alternative Dairy",
        "metadata": {"canonical_ingredients": ["soy_milk"], "product_type": "plant_based", "sub_type": "soy_milk", "alternatives_for": ["milk"]},
        "variants": [
            {"sku": "SKU-SOFIT-SOY-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("135.00"), "stock": 20},
            {"sku": "SKU-SOFIT-SOY-200ML", "size": Decimal("200.00"), "unit": "ml", "price": Decimal("35.00"), "stock": 30}
        ]
    })
    # P13: OatMlk Oat Milk (Alternative for milk)
    products_data.append({
        "name": "Oat Milk Barista Edition", "brand": "OatMlk", "category": "Alternative Dairy",
        "metadata": {"canonical_ingredients": ["oat_milk"], "product_type": "plant_based", "sub_type": "oat_milk", "alternatives_for": ["milk"]},
        "variants": [
            {"sku": "SKU-OATMLK-OAT-1L", "size": Decimal("1000.00"), "unit": "ml", "price": Decimal("210.00"), "stock": 18},
            {"sku": "SKU-OATMLK-OAT-500ML", "size": Decimal("500.00"), "unit": "ml", "price": Decimal("115.00"), "stock": 22}
        ]
    })
    # P14: Urban Platter Tofu (Alternative for paneer)
    products_data.append({
        "name": "Firm Organic Tofu", "brand": "Urban Platter", "category": "Alternative Dairy",
        "metadata": {"canonical_ingredients": ["tofu"], "product_type": "plant_based", "sub_type": "tofu", "alternatives_for": ["paneer"]},
        "variants": [
            {"sku": "SKU-UP-TOFU-250G", "size": Decimal("250.00"), "unit": "g", "price": Decimal("85.00"), "stock": 15},
            {"sku": "SKU-UP-TOFU-500G", "size": Decimal("500.00"), "unit": "g", "price": Decimal("160.00"), "stock": 10}
        ]
    })
    # P15-P20: Coconut Milk, Cashew Milk, Peanut Butter, Coconut Cream, Vegan Cheese, Rice Milk
    for i in range(15, 21):
        names = ["Coconut Milk", "Cashew Milk", "Peanut Butter", "Coconut Cream", "Vegan Cheese", "Rice Milk"]
        can_keys = ["coconut_milk", "cashew_milk", "peanut_butter", "coconut_cream", "vegan_cheese", "rice_milk"]
        alt_for = ["cream"] if i == 18 else (["milk"] if i in [15, 16, 20] else [])
        idx = i - 15
        products_data.append({
            "name": names[idx], "brand": "Urban Platter", "category": "Alternative Dairy",
            "metadata": {"canonical_ingredients": [can_keys[idx]], "product_type": "plant_based", "sub_type": can_keys[idx], "alternatives_for": alt_for},
            "variants": [
                {"sku": f"SKU-UP-ALT-{i}-A", "size": Decimal("250.00"), "unit": "g", "price": Decimal("120.00"), "stock": 12},
                {"sku": f"SKU-UP-ALT-{i}-B", "size": Decimal("500.00"), "unit": "g", "price": Decimal("220.00"), "stock": 8}
            ]
        })

    # --- 3. Atta & Flours (10 Products, 20 Variants) ---
    flour_brands = ["Aashirvaad", "Pillsbury", "Tata Simply Better", "Organic Tattva", "Fortune"]
    flour_names = ["Whole Wheat Atta", "Multigrain Atta", "Select Sharbati Atta", "Besan Gram Flour", "Maida Refined Wheat Flour", "Rava Sooji", "Rice Flour", "Ragi Flour", "Jowar Flour", "Bajra Flour"]
    flour_keys = ["wheat_flour", "multigrain_flour", "sharbati_flour", "besan", "maida", "sooji", "rice_flour", "ragi_flour", "jowar_flour", "bajra_flour"]
    for i in range(21, 31):
        idx = i - 21
        brand = flour_brands[idx % len(flour_brands)]
        products_data.append({
            "name": flour_names[idx], "brand": brand, "category": "Atta & Flours",
            "metadata": {"canonical_ingredients": [flour_keys[idx]], "product_type": "staples", "sub_type": "flour", "alternatives_for": []},
            "variants": [
                {"sku": f"SKU-FLOUR-{i}-1KG", "size": Decimal("1000.00"), "unit": "g", "price": Decimal("65.00"), "stock": 35},
                {"sku": f"SKU-FLOUR-{i}-5KG", "size": Decimal("5000.00"), "unit": "g", "price": Decimal("310.00"), "stock": 15}
            ]
        })

    # --- 4-10. Remaining Categories (70 Products, 140 Variants) ---
    # Fills out remaining 70 products cleanly across Categories 4-10
    cat_specs = [
        ("Rice & Grains", ["Basmati Rice", "Sona Masoori Rice", "Brown Rice", "Poha", "Quinoa", "Oats", "Dalia", "Jasmine Rice", "Idli Rice", "Red Rice"], ["basmati_rice", "sona_masoori", "brown_rice", "poha", "quinoa", "oats", "dalia", "jasmine_rice", "idli_rice", "red_rice"]),
        ("Pulses & Dals", ["Toor Dal", "Moong Dal", "Chana Dal", "Urad Dal", "Rajma Red", "Kabuli Chana", "Black Masoor", "Green Moong", "Lobiya", "Kala Chana"], ["toor_dal", "moong_dal", "chana_dal", "urad_dal", "rajma", "kabuli_chana", "black_masoor", "green_moong", "lobiya", "kala_chana"]),
        ("Cooking Oils", ["Sunflower Oil", "Mustard Oil", "Groundnut Oil", "Rice Bran Oil", "Extra Virgin Olive Oil", "Sesame Oil", "Coconut Oil", "Canola Oil", "Blended Oil", "Soya Oil"], ["sunflower_oil", "mustard_oil", "groundnut_oil", "rice_bran_oil", "olive_oil", "sesame_oil", "coconut_oil", "canola_oil", "blended_oil", "soya_oil"]),
        ("Spices & Masalas", ["Turmeric Powder", "Red Chilli Powder", "Coriander Powder", "Garam Masala", "Cumin Seeds", "Mustard Seeds", "Black Pepper", "Cardamom", "Cinnamon", "Cloves"], ["turmeric", "red_chilli", "coriander_powder", "garam_masala", "cumin", "mustard_seeds", "black_pepper", "cardamom", "cinnamon", "cloves"]),
        ("Snacks & Biscuits", ["Marie Gold Biscuits", "Good Day Cookies", "Bourbon Biscuits", "Classic Salted Chips", "Alooj Bhujia", "Roasted Almonds", "Salted Cashews", "Raisins", "Dark Chocolate", "Digestive Biscuits"], ["marie_biscuits", "cookies", "bourbon", "potato_chips", "bhujia", "almonds", "cashews", "raisins", "chocolate", "digestive_biscuits"]),
        ("Beverages", ["Green Tea", "Masala Chai Tea", "Instant Coffee", "Filter Coffee", "Orange Juice", "Apple Juice", "Lemonade", "Sparkling Water", "Coconut Water", "Energy Drink"], ["green_tea", "tea", "instant_coffee", "filter_coffee", "orange_juice", "apple_juice", "lemonade", "sparkling_water", "coconut_water", "energy_drink"]),
        ("Baking & Desserts", ["Baking Powder", "Baking Soda", "Vanilla Extract", "Cocoa Powder", "Icing Sugar", "Dark Compound", "Cake Mix", "Yeast", "Condensed Milk", "Custard Powder"], ["baking_powder", "baking_soda", "vanilla_extract", "cocoa_powder", "icing_sugar", "dark_compound", "cake_mix", "yeast", "condensed_milk", "custard_powder"])
    ]

    prod_counter = 31
    for category_name, item_names, item_keys in cat_specs:
        for idx in range(10):
            brand = BRANDS[prod_counter % len(BRANDS)]
            stock1 = 2 if prod_counter % 8 == 0 else (0 if prod_counter % 9 == 0 else 20)
            stock2 = 3 if prod_counter % 8 == 0 else (0 if prod_counter % 9 == 0 else 15)

            products_data.append({
                "name": item_names[idx], "brand": brand, "category": category_name,
                "metadata": {"canonical_ingredients": [item_keys[idx]], "product_type": category_name.lower().replace(" ", "_"), "sub_type": item_keys[idx], "alternatives_for": []},
                "variants": [
                    {"sku": f"SKU-PROD-{prod_counter}-V1", "size": Decimal("250.00"), "unit": "g", "price": Decimal("85.00"), "stock": stock1},
                    {"sku": f"SKU-PROD-{prod_counter}-V2", "size": Decimal("500.00"), "unit": "g", "price": Decimal("165.00"), "stock": stock2}
                ]
            })
            prod_counter += 1

    return products_data

async def seed_database():
    """Seeds Supabase PostgreSQL database with deterministic 100-product catalog."""
    print("🌱 Starting database seeding process...")

    async with async_session_maker() as session:
        catalog = generate_100_products()
        inserted_products = 0
        inserted_variants = 0

        for p_data in catalog:
            # Idempotent SKU check
            first_sku = p_data["variants"][0]["sku"]
            stmt = select(ProductVariant).where(ProductVariant.sku == first_sku)
            res = await session.execute(stmt)
            if res.scalar_one_or_none():
                continue

            product = Product(
                name=p_data["name"],
                brand=p_data["brand"],
                category=p_data["category"],
                description=f"Fresh quality {p_data['name']} by {p_data['brand']}.",
                metadata_json=p_data["metadata"],
                is_active=True
            )
            session.add(product)
            await session.flush()
            inserted_products += 1

            for v_data in p_data["variants"]:
                variant = ProductVariant(
                    product_id=product.id,
                    sku=v_data["sku"],
                    size=v_data["size"],
                    size_unit=v_data["unit"],
                    price=v_data["price"],
                    is_active=True
                )
                session.add(variant)
                await session.flush()

                inventory = Inventory(
                    variant_id=variant.id,
                    available_quantity=v_data["stock"]
                )
                session.add(inventory)
                inserted_variants += 1

        await session.commit()
        print(f"✅ Seeding finished! Inserted {inserted_products} new products and {inserted_variants} variants/inventory records.")

if __name__ == "__main__":
    asyncio.run(seed_database())
