# Document 01: Project Overview & Core Principles

## 1. Product Vision
The **AI-Powered Recipe-to-Commerce System** bridges unstructured culinary content (images, photos, text recipes, web pages, and YouTube cooking videos) with a deterministic e-commerce purchasing pipeline. 

Users can submit any recipe input. The AI engine parses the recipe, extracts ingredients, and normalizes them into canonical identifiers. The system then dynamically queries the product catalog and inventory database to surface purchasable product variants across brands and sizes, allowing users to seamlessly transition from recipe discovery to cart creation and checkout.

---

## 2. Core Architectural Principle
> **"AI understands content. Backend handles deterministic business logic. PostgreSQL is the source of truth. The user makes the purchasing decision."**

```
User Input
    │
    ▼
┌──────────────────────────────────────┐
│  AI Engine (Vertex AI / LangChain)   │ ───► Extract & Normalize Unstructured Recipe
└──────────────────────────────────────┘
    │ (Canonical Ingredients)
    ▼
┌──────────────────────────────────────┐
│  Backend Logic (FastAPI + SQLModel)  │ ───► Deterministic DB Lookup (Catalog & Inventory)
└──────────────────────────────────────┘
    │ (Available Products & Variants)
    ▼
┌──────────────────────────────────────┐
│  User Decision (Frontend UI)         │ ───► Selects Brand, Variant Size, & Quantity
└──────────────────────────────────────┘
    │ (Selected SKUs)
    ▼
┌──────────────────────────────────────┐
│  Cart & Checkout Pipeline            │ ───► Fresh Stock Re-validation & Order Creation
└──────────────────────────────────────┘
```

### Strict Control Separation
1. **AI / LLM Domain**:
   - Extracting dish titles, raw ingredients, quantities, and units from unstructured media.
   - Normalizing raw ingredient strings (e.g., *"fresh farm milk"*, *"whole milk"*, *"toned milk"*) into canonical identifiers (e.g., `milk`).
   - Ranking pre-filtered in-stock alternatives **ONLY** when no matching product variants are available in inventory across all relevant brands and package sizes.
   - **Prohibition**: The LLM MUST NOT control inventory, product pricing, cart state, order creation, stock reservation, or purchasing decisions.

2. **Backend / PostgreSQL Domain**:
   - Storing canonical products, SKUs/variants, inventory counts, user carts, and confirmed orders.
   - Performing exact and dynamic catalog searches using canonical keys and metadata queries.
   - Re-validating inventory atomically during checkout.
   - Enforcing business constraints and transaction boundaries.

3. **User Domain**:
   - Reviewing low-confidence ingredient extractions.
   - Choosing specific brands, package sizes (e.g., 500ml vs 1L), and purchase quantities.
   - Adding items to the cart and initiating checkout.

---

## 3. Supported Input Types
The application handles five distinct input types through streamlined processing pipelines:

| Input Type | Ingestion Mechanism | Extraction Pipeline |
| :--- | :--- | :--- |
| **Image Upload** | Multi-part Form Data / Supabase Storage | Vision LLM (Vertex AI Multimodal) |
| **Camera Capture** | Client Camera -> File Upload -> Supabase | Identical Vision LLM pipeline as Image Upload |
| **Plain Text** | JSON String Payload | Text LLM (Vertex AI Structured Extraction) |
| **Recipe URL** | HTML Scraping via HTTP Client | HTML Text Extraction -> LLM Processing |
| **YouTube Video URL** | YouTube API / Transcript Extractor | Audio Transcript -> LLM Processing |

> [!IMPORTANT]
> **Camera & Upload Unified Pipeline**: Camera captures and uploaded files pass through the exact same backend ingestion route (`/api/v1/recipes/process-image`) and Supabase Storage pipeline. No dedicated camera backend service exists.
>
> **YouTube Input Constraint**: Video frame analysis is explicitly out of scope for MVP. Video processing relies strictly on text transcripts.

---

## 4. Key Business Rules Summary

### A. Multi-Variant Matching & Purchase Flexibility
- **Multi-Variant Matching**: If a recipe calls for `Milk - 500ml`, the backend surfaces **all available variants** of milk (e.g., Amul 500ml, Amul 1L, Nandini 500ml, Country Delight 2L). The recipe size is informational and does not restrict user selection.
- **Purchase Quantity Independence**: Users may select any quantity of a variant regardless of recipe requirements (e.g., buying 2x 1L milk for a 500ml recipe).
- **No Payment Gateway**: Checkout completes upon successful atomic inventory validation and order creation in PostgreSQL.

### B. Precision Out-of-Stock / Alternative Rule
Alternative recommendations are triggered **ONLY** when no purchasable product variant matching the canonical ingredient is available in inventory across all relevant brands and package sizes.

```
Canonical Ingredient
        ↓
Search matching product variants
        ↓
Check inventory across ALL relevant variants
        ↓
Is ANY matching variant available?
        │
     ┌──┴──┐
     │     │
    YES    NO
     │     │
     ▼     ▼
Show     Check metadata
matching     ↓
products   Compatible alternatives
              ↓
           Check inventory
              ↓
           LLM ranking
              ↓
           Show alternatives
```

> [!IMPORTANT]
> **Stock Evaluation Rule**: If even ONE matching product variant is available in inventory, DO NOT trigger the alternative flow.
> 
> **Example**:
> - **Recipe ingredient**: `Milk`
> - **Inventory State**:
>   - Amul 500ml → OUT OF STOCK
>   - Amul 1L → OUT OF STOCK
>   - Nandini 500ml → AVAILABLE
> - **Result**: Show Nandini 500ml. **DO NOT** show almond milk, soy milk, oat milk, etc.
> - Only when **ALL** relevant matching milk variants have zero available inventory should the alternative flow execute.

### C. Alternative Compatibility & LLM Responsibility
Alternative compatibility is determined strictly by product catalog metadata, not by the LLM.

```
Product Metadata
        ↓
Determine eligible alternatives
        ↓
Inventory check
        ↓
Keep only available alternatives
        ↓
LLM ranking / explanation
        ↓
Show alternatives to user
```

#### LLM Capabilities & Boundaries

**The LLM MAY**:
- Rank eligible, in-stock alternatives.
- Explain why an already-eligible alternative may be suitable for the recipe.
- Help order multiple eligible alternatives based on culinary context.

**The LLM MUST NOT**:
- Invent a new product.
- Invent an alternative relationship.
- Decide that an incompatible product is an alternative.
- Override product catalog metadata.
- Override inventory availability.
- Recommend an out-of-stock alternative.
- Directly modify catalog or inventory data.

> [!NOTE]
> **Metadata & Ranking Example**:
> - **Product Metadata**:
>   - `almond_milk`: `alternatives_for: ["milk"]`
>   - `soy_milk`: `alternatives_for: ["milk"]`
> - **Inventory**:
>   - Almond Milk → Available
>   - Soy Milk → Available
>   - Oat Milk → Unavailable
> - **Flow Result**: The LLM receives ONLY the eligible, available alternatives (`almond_milk` and `soy_milk`) and ranks them. It MUST NOT independently decide that another product (e.g. coconut water) is a valid milk alternative.

---

## 5. Non-Goals & Scope Boundaries
To maintain MVP focus and simplicity, the following features are explicitly **excluded**:
- Multi-tenancy / `tenant_id` structures.
- SQL Agents / Natural language SQL generation.
- Microservices architecture (a single modular FastAPI backend is used).
- Payment gateway integration.
- Video frame extraction or computer vision models outside Vertex AI multimodal LLMs.
- Fallback cloud storage or database providers (Supabase Storage and PostgreSQL are strict single sources).
- Automatic cart selection by AI.
