# Document 16: Master Implementation Plan

> [!WARNING]
> **THIS IS A PLANNING DOCUMENT ONLY. DO NOT EXECUTE PRODUCTION CODE OR GENERATE BACKEND FILES UNTIL THIS IMPLEMENTATION PLAN IS EXPLICITLY APPROVED.**

---

## 1. Specification & Contract Reference
This master implementation plan translates the approved system contract defined in Canonical Documents 01 through 15 into a concrete, dependency-aware execution blueprint:

- [`docs/01-project-overview.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/01-project-overview.md) — Product Vision, Core Principles, Ingestion Inputs, Scope Boundaries.
- [`docs/02-architecture.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/02-architecture.md) — Modular Monolith Layout, Layer Boundaries, Directory Tree.
- [`docs/03-system-flow.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/03-system-flow.md) — Sequence Diagrams for Recipe Ingestion, Product Discovery, Alternatives, and Checkout.
- [`docs/04-database-schema.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/04-database-schema.md) — ERD, Metadata JSONB Contract, SQLModel Models (`Decimal` Currency), Constraints, Indexes.
- [`docs/05-api-specification.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/05-api-specification.md) — REST Endpoint Contracts, 1-Hour JWT Expiry, Success/Error Status Codes, Global Rules.
- [`docs/06-ai-architecture.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/06-ai-architecture.md) — Configurable GCP Vertex AI Integration, Structured Pydantic Output, LangGraph Workflows (`recipe_graph`, `alternative_graph`).
- [`docs/07-prompt-architecture.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/07-prompt-architecture.md) — Externalized Prompt Templates, Variable Injection Contracts, Prompt Loader.
- [`docs/08-product-matching.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/08-product-matching.md) — Deterministic Product Catalog Matching Engine & Metadata Queries.
- [`docs/09-inventory-cart-order.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/09-inventory-cart-order.md) — Cart Lifecycle, Transaction Safety, Row Locking (`FOR UPDATE`), Snapshot Integrity.
- [`docs/10-authentication-security.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/10-authentication-security.md) — JWT Authentication (1-Hour Expiration), Passlib Password Hashing, Resource Isolation.
- [`docs/11-storage.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/11-storage.md) — Supabase Storage Architecture, Object Paths, Upload Policies.
- [`docs/12-seed-data.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/12-seed-data.md) — 100-Product Deterministic Seed Dataset Specification (`Decimal` Prices) & Metadata Examples.
- [`docs/13-testing-strategy.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/13-testing-strategy.md) — Testing Suite Plan (Unit, Integration, AI, Concurrency).
- [`docs/14-error-handling.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/14-error-handling.md) — Standardized JSON Error Response Payload & System Exception Matrix.
- [`docs/15-specification-validation.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/15-specification-validation.md) — Approved Specification Validation Report (`READY FOR IMPLEMENTATION`).

---

## 2. Architectural Principles & Technical Constraints

1. **Modular Monolith**: Single FastAPI Python application (`backend/app/`). No microservices, sagas, or distributed event buses.
2. **Deterministic Catalog Logic**: `ProductService` queries PostgreSQL directly via SQLModel. The LLM **never** queries PostgreSQL, selects SKUs, inspects inventory, or modifies catalog data.
3. **AI Layer Isolation & Configurable Models**: Vertex AI (`VERTEX_MODEL_NAME` default `"gemini-1.5-flash"`, `VERTEX_VISION_MODEL_NAME` default `"gemini-1.5-pro"`) and LangChain are used strictly for parsing unstructured recipe inputs, normalizing canonical ingredient strings, and ranking pre-filtered metadata-compatible alternatives. Model identifiers are fully configurable via settings and compatible with `langchain-google-vertexai` SDK.
4. **Data Access Stack**: `FastAPI` ──► `Async SQLAlchemy Session` ──► `SQLModel` ──► `asyncpg` ──► `PostgreSQL`. SQLModel is the sole ORM layer.
5. **Monetary Precision Standard**: All currency fields (`price`, `total_amount`, `unit_price_snapshot`, `line_total`) MUST be initialized and calculated using `decimal.Decimal` in Python and mapped to `NUMERIC(10, 2)` in PostgreSQL. Floating-point arithmetic (`float`) for currency is strictly prohibited.
6. **Storage Specification**: Supabase Storage is the single configured object store for recipe media. Uploads pass through `StorageService`; no fallback storage is configured.
7. **Single Source of Truth**: PostgreSQL is the authoritative source for products, variants, inventory counts, carts, and confirmed orders.

---

## 3. Dependency-Aware Implementation Sequence

```mermaid
graph TD
    M1[Milestone 1: Skeleton & Configuration] --> M2[Milestone 2: SQLModel Entities & Migrations]
    M2 --> M3[Milestone 3: Authentication & Security Engine]
    M2 --> M4[Milestone 4: Supabase Storage Service]
    
    M3 & M4 --> M5[Milestone 5: AI Engine, Prompts & Recipe Pipeline]
    M2 --> M6[Milestone 6: Deterministic Product Matching Engine]
    
    M5 & M6 --> M7[Milestone 7: Metadata Alternative Recommendation Engine]
    M2 & M3 --> M8[Milestone 8: Active Cart Management Engine]
    
    M6 & M8 --> M9[Milestone 9: Atomic Checkout & Order Snapshot Engine]
    M5 & M7 & M9 --> M10[Milestone 10: Master API Routing & Error Handlers]
    M10 --> M11[Milestone 11: End-to-End Test Suite & Concurrency Hardening]
```

---

## 4. Complete Project Structure & File Mapping

Every planned backend file is mapped below to its specification source:

| File Path | Primary Responsibility | Key Dependencies | Source Specification | MVP? |
| :--- | :--- | :--- | :--- | :---: |
| `app/__init__.py` | Package initialization | None | Doc 02 | **YES** |
| `app/main.py` | FastAPI instantiation & global error handlers | FastAPI, Routers | Doc 02, Doc 05 | **YES** |
| `app/core/config.py` | Environment variable validation (`Settings`) | `pydantic-settings` | Doc 02, Doc 10 | **YES** |
| `app/core/database.py` | Async SQLAlchemy engine & session maker | `SQLModel`, `asyncpg` | Doc 02, Doc 04 | **YES** |
| `app/core/security.py` | JWT issuance/verification & bcrypt hashing | `PyJWT`, `passlib` | Doc 02, Doc 10 | **YES** |
| `app/core/dependencies.py` | FastAPI `get_current_user` & `get_db` | `FastAPI`, `security.py` | Doc 05, Doc 10 | **YES** |
| `app/models/user.py` | `User` SQLModel entity | `SQLModel` | Doc 04 | **YES** |
| `app/models/recipe.py` | `Recipe` SQLModel entity & enums | `SQLModel` | Doc 04 | **YES** |
| `app/models/recipe_ingredient.py` | `RecipeIngredient` SQLModel entity | `SQLModel` | Doc 04 | **YES** |
| `app/models/product.py` | `Product` SQLModel entity with JSONB metadata | `SQLModel`, `JSONB` | Doc 04 | **YES** |
| `app/models/product_variant.py` | `ProductVariant` SQLModel entity (SKU, `Decimal`) | `SQLModel`, `NUMERIC` | Doc 04 | **YES** |
| `app/models/inventory.py` | `Inventory` SQLModel entity (`available_quantity`) | `SQLModel` | Doc 04 | **YES** |
| `app/models/cart.py` | `Cart` & `CartItem` SQLModel entities | `SQLModel` | Doc 04 | **YES** |
| `app/models/order.py` | `Order` & `OrderItem` SQLModel entities (Snapshots, `Decimal`) | `SQLModel`, `NUMERIC` | Doc 04 | **YES** |
| `app/schemas/auth.py` | Auth DTOs (Signup, Login, Token) | `Pydantic` | Doc 05 | **YES** |
| `app/schemas/recipe.py` | Recipe Request/Response DTOs | `Pydantic` | Doc 05 | **YES** |
| `app/schemas/product.py` | Product Matching Response DTOs | `Pydantic` | Doc 05 | **YES** |
| `app/schemas/cart.py` | Cart Request/Response DTOs | `Pydantic` | Doc 05 | **YES** |
| `app/schemas/order.py` | Order Request/Response DTOs | `Pydantic` | Doc 05 | **YES** |
| `app/services/storage_service.py` | Supabase Storage SDK client wrapper | `supabase-py` | Doc 02, Doc 11 | **YES** |
| `app/services/recipe_service.py` | Recipe ingestion orchestration & persistence | `RecipeGraph`, Storage | Doc 03, Doc 06 | **YES** |
| `app/services/product_service.py` | Deterministic catalog matching & alternative gate | `SQLModel`, DB | Doc 03, Doc 08 | **YES** |
| `app/services/cart_service.py` | Active cart management & SKU item validation | `SQLModel`, DB | Doc 05, Doc 09 | **YES** |
| `app/services/order_service.py` | Atomic checkout, cart/inventory row locking & Decimal price snapshots | `SQLModel`, DB | Doc 03, Doc 09 | **YES** |
| `app/ai/llm.py` | Configurable Vertex AI `ChatVertexAI` instantiation | `langchain-google-vertexai` | Doc 06 | **YES** |
| `app/ai/schemas/recipe_output.py` | LLM ExtractedRecipe Pydantic models | `Pydantic` | Doc 06 | **YES** |
| `app/ai/schemas/alternative_output.py` | LLM RankedAlternativeResponse Pydantic models | `Pydantic` | Doc 06 | **YES** |
| `app/ai/chains/recipe_extraction.py` | LangChain extraction chain | `LangChain` | Doc 06, Doc 07 | **YES** |
| `app/ai/chains/alternative_ranking.py` | LangChain alternative ranking chain | `LangChain` | Doc 06, Doc 07 | **YES** |
| `app/ai/workflows/recipe_graph.py` | LangGraph `recipe_graph` workflow | `LangGraph` | Doc 03, Doc 06 | **YES** |
| `app/ai/workflows/alternative_graph.py` | LangGraph `alternative_graph` workflow | `LangGraph` | Doc 03, Doc 06 | **YES** |
| `app/prompts/recipe_extraction/system.txt` | Externalized extraction system prompt | Text | Doc 07 | **YES** |
| `app/prompts/recipe_extraction/human.txt` | Externalized extraction human prompt template | Text | Doc 07 | **YES** |
| `app/prompts/alternative_ranking/system.txt` | Externalized alternative ranking system prompt | Text | Doc 07 | **YES** |
| `app/prompts/alternative_ranking/human.txt` | Externalized alternative ranking human prompt | Text | Doc 07 | **YES** |
| `app/integrations/webpage_fetcher.py` | Webpage HTML fetcher & body text extractor | `httpx`, `BeautifulSoup` | Doc 02, Doc 03 | **YES** |
| `app/integrations/youtube_transcript.py` | YouTube transcript API integration | `youtube-transcript-api` | Doc 02, Doc 03 | **YES** |
| `app/api/v1/router.py` | Master v1 API Router aggregator | `FastAPI` | Doc 02, Doc 05 | **YES** |
| `app/api/v1/auth.py` | Auth router (`/signup`, `/login`, `/me`) | `FastAPI`, `AuthService` | Doc 05 | **YES** |
| `app/api/v1/recipes.py` | Recipe router (`/process-*`, `/{id}`) | `FastAPI`, `RecipeService` | Doc 05 | **YES** |
| `app/api/v1/products.py` | Product matching router (`/{id}/products`) | `FastAPI`, `ProductService` | Doc 05 | **YES** |
| `app/api/v1/cart.py` | Cart router (`/cart`, `/cart/items`) | `FastAPI`, `CartService` | Doc 05 | **YES** |
| `app/api/v1/orders.py` | Checkout router (`/orders`) | `FastAPI`, `OrderService` | Doc 05 | **YES** |

---

## 5. Database Implementation Plan

### Schema Entities & Keys
1. **`users`**: PK `id` (UUID), `email` (VARCHAR, Unique, Indexed), `hashed_password`, `full_name`, `is_active`, `created_at`, `updated_at`.
2. **`recipes`**: PK `id` (UUID), FK `user_id` (`users.id`), `title`, `source_type` (Enum), `source_url`, `storage_path`, `raw_content`, `status` (Enum), `created_at`, `updated_at`. Cascade delete on `recipe_ingredients`.
3. **`recipe_ingredients`**: PK `id` (UUID), FK `recipe_id` (`recipes.id`), `raw_name`, `canonical_name` (Indexed), `quantity`, `unit`, `confidence` (`ge=0.0, le=1.0`), `requires_confirmation`, `is_user_modified`.
4. **`products`**: PK `id` (UUID), `name`, `brand` (Indexed), `category` (Indexed), `description`, `metadata_json` (JSONB, GIN Indexed), `is_active`.
5. **`product_variants`**: PK `id` (UUID), FK `product_id` (`products.id`), `sku` (VARCHAR, Unique, Indexed), `size` (`gt=0.0`), `size_unit`, `price` (`Decimal` / `NUMERIC(10,2)`), `is_active`.
6. **`inventory`**: PK `id` (UUID), FK `variant_id` (`product_variants.id`, Unique, Indexed), `available_quantity` (`ge=0`), `updated_at`. (`reserved_quantity` column excluded).
7. **`carts`**: PK `id` (UUID), FK `user_id` (`users.id`, Indexed), `status` (Enum: active, converted, abandoned).
8. **`cart_items`**: PK `id` (UUID), FK `cart_id` (`carts.id`), FK `variant_id` (`product_variants.id`), `quantity` (`gt=0`), `UniqueConstraint("cart_id", "variant_id")`.
9. **`orders`**: PK `id` (UUID), FK `user_id` (`users.id`, Indexed), `order_number` (Unique, Indexed), `total_amount` (`Decimal` / `NUMERIC(10,2)`), `status` (Enum: confirmed, cancelled).
10. **`order_items`**: PK `id` (UUID), FK `order_id` (`orders.id`), FK `variant_id` (`product_variants.id`), `product_name_snapshot`, `brand_snapshot`, `size_snapshot`, `unit_snapshot`, `unit_price_snapshot` (`Decimal`), `quantity` (`gt=0`), `line_total` (`Decimal`).

### Migration Dependency Sequence (Alembic)
`Migration 001_initial_schema.py`:
1. Create `users` table.
2. Create `recipes` & `recipe_ingredients` tables.
3. Create `products`, `product_variants`, & `inventory` tables.
4. Create `carts` & `cart_items` tables with `uq_cart_items_cart_variant` unique constraint.
5. Create `orders` & `order_items` tables.
6. Create `idx_products_metadata_json_gin` GIN index on `products(metadata_json)`.

---

## 6. Authentication Implementation Plan

- **Endpoints**: `POST /api/v1/auth/signup`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- **Password Hashing**: `passlib.context.CryptContext(schemes=["bcrypt"])`.
- **JWT Generation**: `PyJWT.encode()`, algorithm `HS256`, expiration set strictly to 3600 seconds (1 hour). Payload: `{"sub": str(user_id), "exp": expire_timestamp}`.
- **Security Dependency (`get_current_user`)**: Extracts Bearer token from `Authorization` header, decodes JWT signature, fetches active user from DB. Raises `401 Unauthorized` if expired or invalid.
- **Resource Ownership Authorization**:
  ```python
  if resource.user_id != current_user.id:
      raise HTTPException(status_code=404, detail="Resource not found")
  ```

---

## 7. Recipe Ingestion Pipeline Plan

All 4 ingestion sources converge cleanly into `RecipeGraph` for parsing and persistence:

```
[1. Upload / Camera File] ──► Supabase Storage ──► Storage Path ──┐
[2. Raw Recipe Text] ──────────────────────────────────────────────┼──► Recipe LangGraph ──► Vertex AI ──► PostgreSQL
[3. Recipe URL] ──────────► Webpage Integration (Clean Text) ─────┤
[4. YouTube Video URL] ───► Transcript Integration (Text) ────────┘
```

- **Unified Image & Camera Pipeline**: `POST /recipes/process-image` handles both file uploads and camera snapshots. Files are saved to Supabase Storage; storage paths / references are passed to Vertex AI Vision. Public URLs are not required.
- **Webpage Ingestion**: `httpx` fetches HTML, strips `<script>`/`<style>` tags, and passes clean body text to LLM.
- **YouTube Ingestion**: `youtube-transcript-api` extracts audio transcript text and passes text to LLM. Video frame analysis is explicitly out of scope.

---

## 8. AI Engine & Prompt Implementation Plan

- **Configurable Vertex AI Client (`app/ai/llm.py`)**: `ChatVertexAI(model_name=settings.VERTEX_MODEL_NAME, temperature=0.0)` for sub-second structured extraction and `ChatVertexAI(model_name=settings.VERTEX_VISION_MODEL_NAME, temperature=0.0)` for multimodal queries.
- **Prompt Storage (`app/prompts/`)**:
  - `recipe_extraction/system.txt` & `human.txt`: Takes `{input_type}` and `{raw_content}`.
  - `alternative_ranking/system.txt` & `human.txt`: Takes `{canonical_name}` and `{candidates_json}`.
- **Prompt Loader**: Cached file loader (`load_prompt(category, filename)`).
- **LangChain Chains**: Uses `.with_structured_output(ExtractedRecipe)` and `.with_structured_output(RankedAlternativeResponse)`.
- **LangGraph Workflows**:
  - `recipe_graph`: Nodes: `prepare_input` ──► `extract_recipe` ──► `normalize_ingredients` ──► `evaluate_confidence`.
  - `alternative_graph`: Nodes: `receive_prefiltered_candidates` ──► `rank_alternatives_llm` ──► `format_alternative_output`.

---

## 9. Ingredient Normalization & Confidence Plan

- **Normalization Rules**: Convert raw strings (e.g. *"fresh farm milk"*, *"toned milk"*, *"cow milk"*) to lowercase `snake_case` canonical keys (e.g. `milk`). Strip brand names and decorative descriptors ("organic", "fresh", "farm-picked"). Preserve functional distinctions (`almond_milk` vs `cow_milk`).
- **Isolation**: Normalization is executed purely by the AI engine. No PostgreSQL queries are executed during normalization.
- **Confidence Evaluation Threshold (`0.70`)**:
  - `confidence >= 0.70`: Auto-confirmed (`requires_confirmation = False`).
  - `confidence < 0.70`: Flagged for confirmation (`requires_confirmation = True`).

---

## 10. Product Matching Plan

`ProductService` executes deterministic SQL queries against PostgreSQL:

```sql
SELECT p, pv, i 
FROM products p
JOIN product_variants pv ON p.id = pv.product_id
JOIN inventory i ON pv.id = i.variant_id
WHERE p.is_active = TRUE 
  AND pv.is_active = TRUE 
  AND i.available_quantity > 0
  AND p.metadata_json->'canonical_ingredients' @> '["milk"]';
```

- **No LLM Involvement**: Primary product matching is 100% deterministic SQL.
- **Multi-Variant Surfacing**: Returns all available SKUs across all brands (Amul, Nandini) and package sizes (500ml, 1L, 2L).
- **Size Freedom & Quantity Independence**: `recipe_size == product_variant_size` is NOT enforced. `purchase_quantity == recipe_quantity` is NOT enforced. User selects size and quantity; backend validates `requested_quantity <= available_quantity`.

---

## 11. Alternative Discovery Plan

- **Strict Gatekeeper**: Alternative discovery executes **ONLY IF** zero primary matching variants are in stock across all brands and sizes (`available_quantity > 0`).
- **Metadata Discovery Query**:
  ```sql
  SELECT p, pv, i 
  FROM products p
  JOIN product_variants pv ON p.id = pv.product_id
  JOIN inventory i ON pv.id = i.variant_id
  WHERE p.is_active = TRUE 
    AND pv.is_active = TRUE 
    AND i.available_quantity > 0
    AND p.metadata_json->'alternatives_for' @> '["milk"]';
  ```
- **Database Stock Filtering**: In-stock candidates are filtered by SQL **BEFORE** passing candidate payloads to `alternative_graph`.
- **LLM Boundaries**: LLM receives pre-filtered candidates, ranks culinary suitability, and generates a 1-sentence rationale (`"is_alternative": true`, `"alternative_reason": "..."`). LLM cannot invent products, invent compatibility, or override metadata.

---

## 12. Cart Management Plan

- **Endpoints**: `GET /api/v1/cart`, `POST /api/v1/cart/items`, `PATCH /api/v1/cart/items/{item_id}`, `DELETE /api/v1/cart/items/{item_id}`.
- **Active Cart Auto-Initialization**: `GET /cart` fetches active cart; if absent, initializes a new empty active cart and returns it.
- **No Stock Deduction / Reservation**: Cart additions validate stock availability (`requested_qty <= available_qty`) but **DO NOT** deduct or reserve inventory.
- **SKU Uniqueness**: `POST /cart/items` checks `UNIQUE(cart_id, variant_id)`. If SKU already exists in cart, updates `quantity` on existing row.

---

## 13. Checkout & Order Processing Plan

- **Endpoint**: `POST /api/v1/orders`.
- **Atomic Checkout Sequence**:
  ```sql
  BEGIN TRANSACTION;
  -- 1. Fetch & lock active cart and cart items within single transaction
  SELECT * FROM carts WHERE user_id = $user_id AND status = 'active' FOR UPDATE;
  SELECT * FROM cart_items WHERE cart_id = $cart_id FOR UPDATE;

  -- 2. Reject if cart is empty
  -- IF cart_items IS EMPTY -> ROLLBACK & RETURN 400 Bad Request (EMPTY_CART)

  -- 3. Lock corresponding inventory rows for each cart item
  SELECT * FROM inventory WHERE variant_id = $variant_id FOR UPDATE;

  -- 4. Validate available stock against requested quantity
  -- IF available_quantity < requested_quantity -> ROLLBACK & RETURN 409 Conflict (INSUFFICIENT_STOCK)

  -- 5. Lock variant and product rows for authoritative Decimal price & snapshot details
  SELECT * FROM product_variants WHERE id = $variant_id FOR UPDATE;

  -- 6. Deduct inventory: available_quantity = available_quantity - item.quantity
  -- 7. Calculate Decimal line totals & order grand total (Decimal("0.00"))
  -- 8. Create Order & OrderItem historical snapshots (unit_price_snapshot, line_total Decimal)
  -- 9. Mark cart status = 'converted'
  COMMIT TRANSACTION;
  ```
- **Transaction Locking Rationale**: Executing row locks (`FOR UPDATE`) on the active cart, cart items, and inventory within a single PostgreSQL transaction guarantees atomic evaluation, preventing race conditions and inventory overselling when parallel checkouts execute concurrently.

---

## 14. API Implementation Matrix

| Endpoint | Router File | Schema File | Service File | DB / AI Dependencies | Success Status | Error Statuses | Ownership Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST /auth/signup` | `api/v1/auth.py` | `schemas/auth.py` | `security.py` | DB (`users`) | `201 Created` | 400 | N/A |
| `POST /auth/login` | `api/v1/auth.py` | `schemas/auth.py` | `security.py` | DB (`users`) | `200 OK` | 401 | N/A |
| `GET /auth/me` | `api/v1/auth.py` | `schemas/auth.py` | `security.py` | DB (`users`) | `200 OK` | 401 | `current_user.id` |
| `POST /recipes/process-image` | `api/v1/recipes.py` | `schemas/recipe.py` | `recipe_service.py` | Supabase Storage, Vertex AI, DB | `201 Created` | 400, 401, 502 | `current_user.id` |
| `POST /recipes/process-text` | `api/v1/recipes.py` | `schemas/recipe.py` | `recipe_service.py` | Vertex AI, DB | `201 Created` | 401 | `current_user.id` |
| `POST /recipes/process-url` | `api/v1/recipes.py` | `schemas/recipe.py` | `recipe_service.py` | `webpage_fetcher.py`, Vertex AI, DB | `201 Created` | 401, 422 | `current_user.id` |
| `POST /recipes/process-video` | `api/v1/recipes.py` | `schemas/recipe.py` | `recipe_service.py` | `youtube_transcript.py`, Vertex AI, DB | `201 Created` | 400, 401 | `current_user.id` |
| `GET /recipes/{recipe_id}` | `api/v1/recipes.py` | `schemas/recipe.py` | `recipe_service.py` | DB (`recipes`) | `200 OK` | 401, 404 | `recipe.user_id == current_user.id` |
| `PATCH /recipes/{recipe_id}/ingredients` | `api/v1/recipes.py` | `schemas/recipe.py` | `recipe_service.py` | DB (`recipe_ingredients`) | `200 OK` | 401, 404 | `recipe.user_id == current_user.id` |
| `POST /recipes/{recipe_id}/products` | `api/v1/products.py` | `schemas/product.py` | `product_service.py` | DB (`products`, `variants`, `inventory`), Alternative Graph | `200 OK` | 401, 404 | `recipe.user_id == current_user.id` |
| `GET /products/{variant_id}` | `api/v1/products.py` | `schemas/product.py` | `product_service.py` | DB (`product_variants`) | `200 OK` | 401, 404 | Public Catalog Item |
| `GET /cart` | `api/v1/cart.py` | `schemas/cart.py` | `cart_service.py` | DB (`carts`, `cart_items`) | `200 OK` | 401 | `cart.user_id == current_user.id` |
| `POST /cart/items` | `api/v1/cart.py` | `schemas/cart.py` | `cart_service.py` | DB (`cart_items`, `inventory`) | `200 OK` | 400, 401, 404, 409 | `cart.user_id == current_user.id` |
| `PATCH /cart/items/{item_id}` | `api/v1/cart.py` | `schemas/cart.py` | `cart_service.py` | DB (`cart_items`, `inventory`) | `200 OK` | 401, 404, 409 | `cart.user_id == current_user.id` |
| `DELETE /cart/items/{item_id}` | `api/v1/cart.py` | `schemas/cart.py` | `cart_service.py` | DB (`cart_items`) | `200 OK` | 401, 404 | `cart.user_id == current_user.id` |
| `POST /orders` | `api/v1/orders.py` | `schemas/order.py` | `order_service.py` | DB (`inventory` FOR UPDATE, `orders`, `order_items`, `carts`) | `201 Created` | 400, 401, 409 | `cart.user_id == current_user.id` |
| `GET /orders/{order_id}` | `api/v1/orders.py` | `schemas/order.py` | `order_service.py` | DB (`orders`, `order_items`) | `200 OK` | 401, 404 | `order.user_id == current_user.id` |
| `GET /orders` | `api/v1/orders.py` | `schemas/order.py` | `order_service.py` | DB (`orders`) | `200 OK` | 401 | `order.user_id == current_user.id` |

---

## 15. Global Error Handling Plan

Custom exception handler (`AppException`) registered in `main.py`:

- **400 Bad Request**: Invalid payload, MIME type mismatch, file > 10MB, or empty cart checkout (`EMPTY_CART`).
- **401 Unauthorized**: Invalid credentials, missing Bearer token, or expired JWT.
- **404 Not Found**: Resource does not exist OR resource belongs to another user (resource isolation).
- **409 Conflict**: Insufficient inventory during cart addition or checkout stock re-validation (`INSUFFICIENT_STOCK`).
- **422 Unprocessable Entity**: Webpage HTML scraping failure or unparseable input.
- **502 Bad Gateway**: Supabase Storage API error or Vertex AI service failure.

---

## 16. Test Suite Strategy & Plan

```
tests/
├── unit/
│   ├── test_security.py            # JWT issuance, 1-hr expiration, & bcrypt password hashing
│   ├── test_normalization.py       # Canonical string normalization & snake_case rules
│   └── test_pricing_math.py        # Decimal currency precision, line totals, grand totals
├── integration/
│   ├── test_auth_api.py            # Signup, login, bearer token validation, 401 errors
│   ├── test_recipe_ingestion_api.py# Process image, camera, text, URL, video APIs
│   ├── test_product_matching_api.py# Deterministic product matching, multi-variant surfacing
│   ├── test_alternative_flow_api.py# Out-of-stock gatekeeper & metadata alternative ranking
│   ├── test_cart_api.py            # Active cart auto-creation, item additions, SKU uniqueness
│   ├── test_checkout_api.py        # Atomic checkout, empty cart validation, price snapshots
│   └── test_concurrency.py         # Concurrent checkout row locking (SELECT FOR UPDATE) oversell test
└── ai/
    └── test_structured_output.py   # Pydantic schema validation & confidence evaluation threshold
```

### Critical Concurrency Test Specification
`tests/integration/test_concurrency.py`: Simulates two parallel checkout HTTP requests (`asyncio.gather`) targeting the last remaining SKU unit (`available_quantity = 1`). Verifies that exactly one checkout receives `201 Created` while the concurrent request receives `409 Conflict` (`INSUFFICIENT_STOCK`), proving zero overselling occurs.

---

## 17. Environment Configuration Plan (`.env.example`)

```env
# Application Settings
APP_NAME="AI Recipe-to-Commerce Backend"
ENVIRONMENT="development"
DEBUG=True
PORT=8000
CONFIDENCE_THRESHOLD=0.70

# Database Configuration
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/recipe_commerce"

# JWT Security Configuration
JWT_SECRET="replace_with_a_secure_random_secret_key_in_production"
JWT_ALGORITHM="HS256"
JWT_EXPIRATION_SECONDS=3600

# Supabase Storage Configuration
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your-supabase-service-role-or-anon-key"

# GCP Vertex AI Configuration (Configurable Models)
VERTEX_PROJECT_ID="your-gcp-project-id"
VERTEX_LOCATION="us-central1"
VERTEX_MODEL_NAME="gemini-1.5-flash"
VERTEX_VISION_MODEL_NAME="gemini-1.5-pro"
```

---

## 18. MVP Scope Boundary

### IN SCOPE
- Unified image & camera recipe parsing via Supabase Storage and Vertex AI Vision.
- Text recipe, URL webpage HTML, and YouTube transcript text recipe parsing.
- AI ingredient extraction, `snake_case` canonical normalization, confidence evaluation.
- Multi-brand, multi-size deterministic SQL product catalog matching.
- Strict out-of-stock gatekeeper and metadata-driven (`alternatives_for`) LLM alternative ranking.
- Active cart management with `UNIQUE(cart_id, variant_id)` SKU updates.
- Atomic checkout transaction with row locking (`SELECT FOR UPDATE`) on cart, cart items, and inventory rows, authoritative Decimal price calculation, and immutable `OrderItem` snapshots.
- JWT authentication with 1-hour expiry and resource ownership authorization.

### OUT OF SCOPE
- Payment gateway integration or payment tables.
- Inventory reservation systems or `reserved_quantity` columns.
- Redis, Celery, or background task brokers.
- Vector databases, Graph databases, or SQL Agents.
- Separate microservices, recommendation services, or category tables.
- Video frame extraction (YouTube processing uses transcripts only).
- Multi-tenancy or enterprise SSO.

---

## 19. Implementation Milestones

### Milestone 1 — Project Skeleton & Configuration
- **Objective**: Setup repository structure, `.env.example`, Pydantic settings, and async SQLAlchemy database engine.
- **Files**: `app/__init__.py`, `app/main.py`, `app/core/config.py`, `app/core/database.py`, `requirements.txt`.
- **Dependencies**: `pydantic-settings`, `sqlmodel`, `asyncpg`.
- **Tests**: `tests/unit/test_security.py` (configuration loading).
- **Acceptance Criteria**: FastAPI application initializes cleanly; async database connection pool connects.

### Milestone 2 — SQLModel Entities & Alembic Migrations
- **Objective**: Define all 10 SQLModel entities with `Decimal` monetary fields, constraints, and indexes; generate baseline migration.
- **Files**: `app/models/user.py`, `recipe.py`, `recipe_ingredient.py`, `product.py`, `product_variant.py`, `inventory.py`, `cart.py`, `order.py`, `alembic/`.
- **Dependencies**: Milestone 1, `alembic`.
- **Tests**: Entity instantiation tests & migration verification.
- **Acceptance Criteria**: Alembic baseline migration runs cleanly; GIN index on `products(metadata_json)` and unique constraints created.

### Milestone 3 — Authentication & Security Engine
- **Objective**: Implement bcrypt password hashing, 1-hour JWT token generation, `get_current_user` dependency, and auth API endpoints.
- **Files**: `app/core/security.py`, `app/core/dependencies.py`, `app/schemas/auth.py`, `app/api/v1/auth.py`.
- **Dependencies**: Milestone 2, `PyJWT`, `passlib`.
- **Tests**: `tests/unit/test_security.py`, `tests/integration/test_auth_api.py`.
- **Acceptance Criteria**: Signup, login, and `/me` routes functional; expired/invalid tokens return 401.

### Milestone 4 — Supabase Storage Service
- **Objective**: Implement `StorageService` for uploading recipe media with MIME type checking and 10MB size validation.
- **Files**: `app/services/storage_service.py`.
- **Dependencies**: Milestone 1, `supabase-py`.
- **Tests**: Storage client upload unit tests with mocks.
- **Acceptance Criteria**: Uploads generate user-isolated storage paths (`users/{user_id}/recipes/{id}_{file}`).

### Milestone 5 — AI Engine, Prompts & Recipe Processing Pipelines
- **Objective**: Implement external prompt loader, configurable Vertex AI client, Pydantic structured output schemas, LangGraph `recipe_graph`, and recipe ingestion APIs.
- **Files**: `app/ai/llm.py`, `schemas/recipe_output.py`, `chains/recipe_extraction.py`, `workflows/recipe_graph.py`, `prompts/recipe_extraction/*`, `integrations/webpage_fetcher.py`, `youtube_transcript.py`, `services/recipe_service.py`, `api/v1/recipes.py`.
- **Dependencies**: Milestone 3, Milestone 4, `langchain-google-vertexai`, `langgraph`.
- **Tests**: `tests/integration/test_recipe_ingestion_api.py`, `tests/ai/test_structured_output.py`.
- **Acceptance Criteria**: All 4 recipe ingestion sources parse structured ingredients; confidence thresholding flags low-confidence items.

### Milestone 6 — Deterministic Product Matching Engine
- **Objective**: Implement `ProductService` for deterministic SQL catalog matching across brands and package sizes.
- **Files**: `app/schemas/product.py`, `app/services/product_service.py`, `app/api/v1/products.py`.
- **Dependencies**: Milestone 2, Milestone 5.
- **Tests**: `tests/integration/test_product_matching_api.py`.
- **Acceptance Criteria**: Canonical ingredient lookup returns all available in-stock SKUs; recipe size/quantity restrictions are not enforced.

### Milestone 7 — Metadata Alternative Recommendation Engine
- **Objective**: Implement out-of-stock gatekeeper, metadata `alternatives_for` query, stock filtering, and LangGraph `alternative_graph` LLM ranking.
- **Files**: `app/ai/schemas/alternative_output.py`, `chains/alternative_ranking.py`, `workflows/alternative_graph.py`, `prompts/alternative_ranking/*`, `services/product_service.py`.
- **Dependencies**: Milestone 6.
- **Tests**: `tests/integration/test_alternative_flow_api.py`.
- **Acceptance Criteria**: Alternatives trigger ONLY when primary in-stock count is 0; LLM receives pre-filtered in-stock candidates and outputs ranked items with rationales.

### Milestone 8 — Active Cart Management Engine
- **Objective**: Implement active cart auto-initialization, SKU item addition, quantity updates, and deletion.
- **Files**: `app/schemas/cart.py`, `app/services/cart_service.py`, `app/api/v1/cart.py`.
- **Dependencies**: Milestone 3, Milestone 6.
- **Tests**: `tests/integration/test_cart_api.py`.
- **Acceptance Criteria**: Active cart auto-created on `GET /cart`; duplicate SKUs update existing `CartItem.quantity`; stock checked without reservation.

### Milestone 9 — Atomic Checkout & Order Snapshot Engine
- **Objective**: Implement atomic checkout transaction using row locking (`SELECT FOR UPDATE`) on cart, cart items, and inventory rows, authoritative Decimal price calculation, stock deduction, and immutable `OrderItem` snapshots.
- **Files**: `app/schemas/order.py`, `app/services/order_service.py`, `app/api/v1/orders.py`.
- **Dependencies**: Milestone 8.
- **Tests**: `tests/integration/test_checkout_api.py`, `tests/integration/test_concurrency.py`.
- **Acceptance Criteria**: Empty cart returns 400 `EMPTY_CART`; stock deduction is atomic; parallel checkouts cannot oversell inventory.

### Milestone 10 — Master API Routing & Global Error Handling
- **Objective**: Register master API router (`/api/v1`) and global `AppException` error handlers in `main.py`.
- **Files**: `app/api/v1/router.py`, `app/main.py`.
- **Dependencies**: Milestones 3 through 9.
- **Tests**: API error handling integration tests across status codes (400, 401, 404, 409, 422, 502).
- **Acceptance Criteria**: All REST endpoints exposed under `/api/v1`; error payloads follow standardized format.

### Milestone 11 — End-to-End Testing Suite & Concurrency Hardening
- **Objective**: Execute full test suite covering all 9 mandatory E2E scenarios and concurrency validation.
- **Files**: `tests/e2e/test_end_to_end_scenarios.py`, `tests/integration/test_concurrency.py`.
- **Dependencies**: Milestone 10.
- **Tests**: Complete `pytest` suite execution.
- **Acceptance Criteria**: 100% test pass rate across unit, integration, AI, E2E, and concurrency tests.

---

## 20. Definition of Done Checklist

- [ ] FastAPI application starts cleanly on configured port.
- [ ] Alembic baseline database migrations apply without errors.
- [ ] User signup, login (1-hour JWT), and `/me` endpoints function as specified.
- [ ] Recipe ingestion handles image uploads, camera snapshots, plain text, web URLs, and YouTube transcripts.
- [ ] Vertex AI and LangChain generate valid structured Pydantic recipe outputs.
- [ ] Ingredient normalization produces lowercase `snake_case` canonical keys without DB queries.
- [ ] Low-confidence extractions (`confidence < 0.70`) set `requires_confirmation: true`.
- [ ] Product discovery deterministically surfaces all matching in-stock SKUs across brands and sizes.
- [ ] Alternative flow executes ONLY when all primary variants are out of stock.
- [ ] Alternative candidates are pre-filtered by DB metadata and stock before LLM ranking.
- [ ] Active cart auto-initializes and updates quantity for duplicate SKUs.
- [ ] Cart operations check stock but do NOT reserve or deduct inventory.
- [ ] Checkout is atomic, uses row locking (`SELECT FOR UPDATE`) on cart, cart items, and inventory rows, and rejects empty carts (`EMPTY_CART`).
- [ ] Order items preserve immutable catalog snapshots (`unit_price_snapshot`, `line_total`).
- [ ] Currency fields use `Decimal` / `NUMERIC(10, 2)` throughout.
- [ ] Ownership authorization returns `404 Not Found` for resources belonging to another user.
- [ ] Configurable Vertex AI model identifiers load from environment settings (`VERTEX_MODEL_NAME`, `VERTEX_VISION_MODEL_NAME`).
- [ ] All APIs strictly adhere to OpenAPI contracts in Document 05.
- [ ] Concurrency test proves zero overselling occurs under parallel checkouts.
- [ ] Zero prohibited architecture (microservices, vector DBs, SQL agents, payment gateways) introduced.
