# Document 15: Specification Validation Report

## 1. Documents Reviewed
The following 16 canonical architecture, specification, and planning documents were reviewed as a single unified system contract:

1. [`docs/01-project-overview.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/01-project-overview.md) — Product Vision, Core Principles, Ingestion Inputs, Scope Boundaries.
2. [`docs/02-architecture.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/02-architecture.md) — Modular Monolith Layout, Layer Boundaries, Directory Tree.
3. [`docs/03-system-flow.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/03-system-flow.md) — Sequence Diagrams for Ingestion (Image, Camera, Text, URL, Video), Product Matching, Alternatives, and Checkout.
4. [`docs/04-database-schema.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/04-database-schema.md) — ERD, Metadata JSONB Contract, SQLModel Models (`Decimal` Currency), Constraints, Indexes.
5. [`docs/05-api-specification.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/05-api-specification.md) — REST Endpoint Contracts, 1-Hour JWT Expiry, Success/Error Status Codes, Global Security & Business Rules.
6. [`docs/06-ai-architecture.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/06-ai-architecture.md) — Configurable GCP Vertex AI Integration, Structured Pydantic Output, LangGraph Workflows (`recipe_graph`, `alternative_graph`).
7. [`docs/07-prompt-architecture.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/07-prompt-architecture.md) — External Prompt Storage Design, System/Human Prompts, Variable Injections, Loading Utilities.
8. [`docs/08-product-matching.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/08-product-matching.md) — Deterministic Product Catalog Matching Engine & Metadata Queries.
9. [`docs/09-inventory-cart-order.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/09-inventory-cart-order.md) — Cart Lifecycle, Transaction Safety, Row Locking (`FOR UPDATE`), Snapshot Integrity.
10. [`docs/10-authentication-security.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/10-authentication-security.md) — JWT Authentication (1-Hour Expiration), Passlib Password Hashing, 404 Resource Isolation.
11. [`docs/11-storage.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/11-storage.md) — Supabase Storage Private Access Architecture, Safe Object Paths (`users/{user_id}/recipes/{recipe_id}.{ext}`), 10MB Bounded Upload Limit.
12. [`docs/12-seed-data.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/12-seed-data.md) — 100-Product Deterministic Seed Catalog, 200 Variants, 200 Inventory Records, 34 Alternatives, `Decimal` Values.
13. [`docs/13-testing-strategy.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/13-testing-strategy.md) — Seed Integrity Testing, Unit, Integration, AI, and 9 Mandatory E2E Scenarios (Including Concurrency Race Condition Testing).
14. [`docs/14-error-handling.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/14-error-handling.md) — Standardized JSON Error Payload Contract (`{"error": {"code": "...", "message": "...", "details": [...]}}`) & System Exception Matrix.
15. [`docs/15-specification-validation.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/15-specification-validation.md) — Complete Specification Validation Report.
16. [`docs/16-master-implementation-plan.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/16-master-implementation-plan.md) — Master Implementation Plan & 11 Milestones.

---

## 2. Overall Result

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│                     STATUS: READY FOR IMPLEMENTATION                      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

The architecture defined across Documents 01 through 16 describes **one single, internally consistent, production-ready specification**. All business rules, technical boundaries, database constraints, API contracts, security models, testing strategies, error formats, and AI responsibilities align without conflict.

---

## 3. Cross-Document Consistency Matrix

| Architectural Dimension | Document Alignment Across Docs 01–16 | Status |
| :--- | :--- | :--- |
| **API ↔ Service Boundary** | Endpoints in Doc 05 delegate to services in Doc 02 (`AuthService`, `RecipeService`, `ProductService`, `CartService`, `OrderService`, `StorageService`). Routers contain zero SQL or LLM calls. | **Consistent** |
| **Service ↔ Database Boundary** | Services execute async PostgreSQL queries via `AsyncSession` (`SQLModel` / `asyncpg`). Transactions use explicit boundaries (`session.begin()`). | **Consistent** |
| **AI ↔ Database Isolation** | AI extracts recipe data and normalizes `canonical_name` strings. AI **never** queries PostgreSQL, selects SKUs, checks stock, modifies inventory, or calculates prices. Product matching is 100% deterministic backend SQL. | **Consistent** |
| **Matching ↔ Metadata Contract** | `recipe_ingredients.canonical_name` matches `metadata_json->'canonical_ingredients'` in PostgreSQL. Alternative relationships are defined strictly by `metadata_json->'alternatives_for'`. | **Consistent** |
| **Out-of-Stock Alternative Gate** | Alternative flow triggers ONLY when primary matching SKUs have 0 in-stock variants across ALL relevant brands/sizes. DB pre-filters available stock before LLM ranking. | **Consistent** |
| **Size & Quantity Independence** | Recipe quantity (e.g. 500ml) is informational. All in-stock package sizes (500ml, 1L, 2L) are surfaced. User chooses package size and purchase unit count. | **Consistent** |
| **Cart ↔ Inventory Behavior** | Cart operations check current stock availability but DO NOT deduct or reserve stock. `reserved_quantity` column is excluded from the inventory table. `cart_items` enforces `UNIQUE(cart_id, variant_id)`. | **Consistent** |
| **Checkout ↔ Price & Snapshot** | Checkout executes row locks (`SELECT ... FOR UPDATE`) on `Cart`, `CartItem`, and `Inventory` rows within a single PostgreSQL transaction, reads authoritative current prices, deducts stock, and writes immutable `OrderItem` snapshots. | **Consistent** |
| **Monetary & Size Precision** | All currency fields (`price`, `total_amount`, `unit_price_snapshot`, `line_total`) and variant sizes (`size`) use `decimal.Decimal` in Python / SQLModel and `NUMERIC(10, 2)` in PostgreSQL. | **Consistent** |
| **Authentication & Security** | JWT lifetime is strictly 1 hour (3600 seconds), algorithm `HS256`, claims `sub`, `iat`, `exp`. Bearer authorization required. `sub` validated as `uuid.UUID`. User-owned resource isolation returns `404 Not Found`. | **Consistent** |
| **Storage Architecture** | Supabase Storage is the sole object store (private access bucket `recipe-media`). Server-generated paths (`users/{user_id}/recipes/{recipe_id}.{ext}`). 10MB payload limit, MIME allowlist (`jpeg`, `png`, `webp`). Storage failure = 502. | **Consistent** |
| **100-Product Catalog Seed** | Seed contains 100 products, 200 variants, 200 inventory records, 15 brands, 10 categories, 34 alternatives, 12 low-stock, 12 out-of-stock records. Seed integrity validated in `test_seed_integrity.py`. | **Consistent** |
| **Standard Error Payload** | All error responses strictly adhere to `{"error": {"code": "...", "message": "...", "details": [...]}}`. Information disclosure rules prevent stack trace and secret leakage. | **Consistent** |
| **Testing Strategy** | Suite covers unit, integration, AI, and 9 mandatory E2E scenarios including checkout race condition testing using isolated PostgreSQL transactions (`SAVEPOINT`). | **Consistent** |

---

## 4. Architecture Layer Validation

1. **Modular Monolith**: Clean layer separation (API Router ──► Service Layer ──► AI Engine / Data Access Layer). Eliminates microservices operational complexity and distributed transaction sagas.
2. **FastAPI Engine**: Dependency injection (`Depends(get_current_user)`, `Depends(get_db)`), Pydantic input/output validation, async routing.
3. **Data Access Stack**: `FastAPI` ──► `Async SQLAlchemy Session` ──► `SQLModel` ──► `asyncpg` ──► `PostgreSQL`. SQLModel is the sole ORM layer.
4. **Storage Layer**: Supabase Storage is the single configured object store for recipe media (`recipe-media`). Uploads pass through `StorageService`; no local disk `/tmp`, S3, GCS, or CDN fallbacks are configured.
5. **AI Engine Stack**: Configurable GCP Vertex AI (`VERTEX_MODEL_NAME` default `"gemini-1.5-flash"`, `VERTEX_VISION_MODEL_NAME` default `"gemini-1.5-pro"`) via `langchain-google-vertexai`. LangChain enforcing structured Pydantic output. LangGraph orchestrating multi-step AI tasks.

---

## 5. Data Flow Validation

- **Unified Image & Camera Flow**: `POST /recipes/process-image` ingests both file uploads and camera snapshots. Files are uploaded to Supabase Storage; storage paths (`recipes.storage_path`) are passed to Vertex AI Vision. Public URLs are not required.
- **Plain Text Flow**: Ingests JSON text payload directly into `recipe_graph` for extraction and normalization.
- **Web URL Flow**: Scrapes HTML via `Webpage Fetcher Integration`, strips script/style tags, and passes clean body text to LLM parser.
- **YouTube Video Flow**: Extracts transcript via `YouTube Transcript Integration` and parses text transcript via LLM. Video frame analysis is explicitly out of scope.
- **Product Matching Flow**: Deterministic SQL query matching `canonical_name` against `metadata_json->'canonical_ingredients'`. Surfaces all in-stock variants across brands and sizes.
- **Alternative Flow**: Executes ONLY when primary in-stock count is zero across all brands/sizes. Queries `metadata_json->'alternatives_for'`, filters in-stock variants, passes candidates to LLM for ranking and 1-sentence rationale generation.
- **Cart & Checkout Flow**: Cart operations update `cart_items` (updating quantity for duplicate SKUs via `UNIQUE(cart_id, variant_id)` constraint). Checkout locks `Cart`, `CartItem`, and `Inventory` rows (`SELECT FOR UPDATE`), validates stock, reads current prices, deducts stock, writes `Order` and `OrderItem` snapshots, converts cart, and commits transaction. Returns HTTP `201 Created`.

---

## 6. Database Entity & Index Validation

### Entity Relationship Structure
- `User` `(1:N)` ──► `Recipe` `(1:N)` ──► `RecipeIngredient`
- `User` `(1:N)` ──► `Cart` `(1:N)` ──► `CartItem` `(N:1)` ──► `ProductVariant`
- `User` `(1:N)` ──► `Order` `(1:N)` ──► `OrderItem` `(N:1)` ──► `ProductVariant`
- `Product` `(1:N)` ──► `ProductVariant` `(1:1)` ──► `Inventory`

### Key Field Specifications & Constraints
- `recipe_ingredients`: `confidence` between `0.0` and `1.0` (`ge=0.0, le=1.0`).
- `product_variants`: `size` stored as `Decimal` / `NUMERIC(10, 2)`, `price` stored as `Decimal` / `NUMERIC(10, 2)`.
- `inventory`: `available_quantity >= 0`. `reserved_quantity` column excluded. 1:1 mapping with `ProductVariant`.
- `cart_items`: `quantity > 0`, `UniqueConstraint("cart_id", "variant_id")`.
- `orders`: `total_amount` stored as `Decimal` / `NUMERIC(10, 2)`.
- `order_items`: `quantity > 0`, `unit_price_snapshot` and `line_total` stored as `Decimal` / `NUMERIC(10, 2)`.

### Index Strategy Verification
- `CREATE INDEX idx_products_metadata_json_gin ON products USING gin (metadata_json);` (Supports GIN JSONB queries for `canonical_ingredients` and `alternatives_for`).
- `CREATE INDEX idx_recipe_ingredients_canonical ON recipe_ingredients (canonical_name);`
- `CREATE INDEX idx_products_brand ON products (brand);`
- `CREATE INDEX idx_products_category ON products (category);`
- `CREATE INDEX idx_product_variants_product_id ON product_variants (product_id);`
- `CREATE UNIQUE INDEX idx_product_variants_sku ON product_variants (sku);`
- `CREATE UNIQUE INDEX idx_inventory_variant_id ON inventory (variant_id);`
- `CREATE INDEX idx_cart_items_cart_id ON cart_items (cart_id);`
- `CREATE INDEX idx_cart_items_variant_id ON cart_items (variant_id);`
- `CREATE UNIQUE INDEX idx_cart_items_cart_variant ON cart_items (cart_id, variant_id);`

---

## 7. API Endpoint Matrix

| Endpoint | Method | Auth | Request Body / Form | Service Dependency | DB / AI Dependencies | Success Status | Error Statuses | Ownership Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/signup` | POST | None | JSON: email, password, full_name | `AuthService` | PostgreSQL (`users`) | `201 Created` | 400 | N/A |
| `/api/v1/auth/login` | POST | None | JSON: email, password | `AuthService` | PostgreSQL (`users`) | `200 OK` | 401 | N/A |
| `/api/v1/auth/me` | GET | Bearer | None | `AuthService` | PostgreSQL (`users`) | `200 OK` | 401 | `current_user.id` |
| `/api/v1/recipes/process-image` | POST | Bearer | Multipart: file (image/camera) | `RecipeService` | Supabase Storage, Vertex AI, DB | `201 Created` | 400, 401, 502 | `current_user.id` |
| `/api/v1/recipes/process-text` | POST | Bearer | JSON: title, text | `RecipeService` | Vertex AI, DB | `201 Created` | 401 | `current_user.id` |
| `/api/v1/recipes/process-url` | POST | Bearer | JSON: url | `RecipeService` | Webpage Fetcher, Vertex AI, DB | `201 Created` | 401, 422 | `current_user.id` |
| `/api/v1/recipes/process-video` | POST | Bearer | JSON: video_url | `RecipeService` | YouTube Transcript, Vertex AI, DB | `201 Created` | 400, 401 | `current_user.id` |
| `/api/v1/recipes/{recipe_id}` | GET | Bearer | None | `RecipeService` | PostgreSQL (`recipes`) | `200 OK` | 401, 404 | `recipe.user_id == current_user.id` (404 if mismatch) |
| `/api/v1/recipes/{recipe_id}/ingredients` | PATCH | Bearer | JSON: updates array | `RecipeService` | PostgreSQL (`recipe_ingredients`) | `200 OK` | 401, 404 | `recipe.user_id == current_user.id` (404 if mismatch) |
| `/api/v1/recipes/{recipe_id}/products` | POST | Bearer | None | `ProductService` | PostgreSQL (`products`, `variants`, `inventory`), Alternative Graph | `200 OK` | 401, 404 | `recipe.user_id == current_user.id` (404 if mismatch) |
| `/api/v1/products/{variant_id}` | GET | Bearer | None | `ProductService` | PostgreSQL (`product_variants`) | `200 OK` | 401, 404 | Public Catalog Item |
| `/api/v1/cart` | GET | Bearer | None | `CartService` | PostgreSQL (`carts`, `cart_items`) | `200 OK` | 401 | `cart.user_id == current_user.id` (Auto-creates if empty) |
| `/api/v1/cart/items` | POST | Bearer | JSON: variant_id, quantity | `CartService` | PostgreSQL (`cart_items`, `inventory`) | `200 OK` | 400, 401, 404, 409 | `cart.user_id == current_user.id` |
| `/api/v1/cart/items/{item_id}` | PATCH | Bearer | JSON: quantity | `CartService` | PostgreSQL (`cart_items`, `inventory`) | `200 OK` | 401, 404, 409 | `cart.user_id == current_user.id` |
| `/api/v1/cart/items/{item_id}` | DELETE | Bearer | None | `CartService` | PostgreSQL (`cart_items`) | `200 OK` | 401, 404 | `cart.user_id == current_user.id` |
| `/api/v1/orders` | POST | Bearer | None | `OrderService` | PostgreSQL (`inventory` FOR UPDATE, `orders`, `order_items`, `carts`) | `201 Created` | 400, 401, 409 | `cart.user_id == current_user.id` |
| `/api/v1/orders/{order_id}` | GET | Bearer | None | `OrderService` | PostgreSQL (`orders`, `order_items`) | `200 OK` | 401, 404 | `order.user_id == current_user.id` (404 if mismatch) |
| `/api/v1/orders` | GET | Bearer | None | `OrderService` | PostgreSQL (`orders`) | `200 OK` | 401 | `order.user_id == current_user.id` |

---

## 8. AI Boundary Validation Matrix

| Operation | AI Allowed? | Deterministic Backend Only? | Architectural Rationale |
| :--- | :---: | :---: | :--- |
| **Recipe Text / Image Parsing** | **YES** | No | AI parses unstructured media into structured ingredient JSON. |
| **Ingredient Normalization** | **YES** | No | AI normalizes raw text ("toned milk") into canonical keys (`milk`). |
| **Confidence Scoring** | **YES** | No | AI assigns float score (0.0–1.0) indicating extraction certainty. |
| **Alternative Ranking** | **YES** | No | AI ranks pre-filtered in-stock candidates and generates 1-sentence rationale. |
| **Database Queries (SQL)** | **NO** | **YES** | AI must never execute raw SQL or query PostgreSQL directly. |
| **Product / SKU Selection** | **NO** | **YES** | Backend `ProductService` queries catalog based on canonical keys. |
| **Alternative Candidate Lookup**| **NO** | **YES** | `metadata_json->'alternatives_for'` defines compatible alternatives. |
| **Stock Availability Checks** | **NO** | **YES** | Backend filters `inventory.available_quantity > 0` deterministically. |
| **Cart & Pricing Logic** | **NO** | **YES** | Backend calculates subtotals and checks stock constraints. |
| **Checkout & Order Creation** | **NO** | **YES** | Backend executes atomic PostgreSQL transaction with row locks. |

---

## 9. Security & Resource Authorization Validation

- **JWT Specifications**: Lifetime set strictly to 3600 seconds (1 hour). Algorithm set to `HS256`. Claims: `sub`, `iat`, `exp`. `sub` claim parsed and validated as a valid `uuid.UUID`.
- **Password Hashing**: Salted hashing via `passlib` with `bcrypt`.
- **Bearer Authentication**: Required on all protected endpoints via `Authorization: Bearer <token>`.
- **Resource Ownership**: Users can access ONLY their own recipes, carts, cart items, and orders (`user_id == current_user.id`). Attempting to access another user's resource returns `404 Not Found` to prevent resource existence enumeration.

---

## 10. Business Rule Validation Checklist

- [x] **Canonical Ingredient Matching**: Primary key `recipe_ingredients.canonical_name` maps to `metadata_json->'canonical_ingredients'`.
- [x] **Package Size Freedom**: `recipe_size == product_variant_size` is NOT enforced. All active in-stock package sizes (`500ml`, `1L`, `2L`) are surfaced across all brands.
- [x] **Purchase Quantity Independence**: User selects any purchase quantity (`1 × 500ml`, `2 × 1L`). Backend validates against `available_quantity`.
- [x] **Out-of-Stock Alternative Gate**: Alternative flow triggers ONLY when primary matching in-stock variant count is ZERO across all brands and sizes.
- [x] **Cart Non-Reservation**: Cart operations check stock but do NOT deduct or reserve stock. `reserved_quantity` column is excluded from database.
- [x] **Atomic Checkout**: Uses `SELECT ... FOR UPDATE` row locks on Cart, CartItem, and Inventory, reads authoritative current variant prices, deducts stock, writes `Order` and `OrderItem` snapshots, converts cart, and commits. Returns `201 Created`.
- [x] **Empty Cart Validation**: Checkout on an empty cart returns `400 Bad Request` (`EMPTY_CART`).
- [x] **Historical Order Snapshots**: `OrderItem` stores immutable product name, brand, size, unit price snapshot, and line total using `Decimal`.

---

## 11. Contradictions / Gaps Log

The comprehensive verification audit across Documents 01 through 16 identified **zero architectural contradictions**.

- **CRITICAL Issues**: `0`
- **HIGH Issues**: `0`
- **MEDIUM Issues**: `0`
- **LOW Issues**: `0`

---

## 12. Implementation Readiness Declaration

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│   CONCLUSION: THE SPECIFICATION IS COMPLETE, CONSISTENT, AND READY FOR   │
│   PHASE 1 IMPLEMENTATION UPON EXPLICIT HUMAN APPROVAL.                    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```
