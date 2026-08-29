# Document 13: Testing Strategy & E2E Validation

## 1. Test Suite Framework & Organization
The testing suite is built on **`pytest`** and **`pytest-asyncio`** targeting an isolated PostgreSQL test database (`postgresql+asyncpg://.../recipe_commerce_test`).

> [!IMPORTANT]
> **PostgreSQL Test Database Mandate**: SQLite as a test database substitute is strictly prohibited. Tests MUST execute against PostgreSQL to validate JSONB GIN index behavior, row-level locking (`SELECT ... FOR UPDATE`), and exact transaction semantics.

### Directory Layout

```
tests/
├── unit/
│   ├── test_normalization.py       # Canonical string normalization & snake_case rules
│   ├── test_pricing_math.py        # Decimal currency precision & line item calculations
│   └── test_inventory_logic.py     # Quantity validation & inventory deduction logic
│
├── integration/
│   ├── test_auth_api.py            # Signup, login, 1-hr JWT validation, 401 error cases
│   ├── test_recipe_api.py          # Recipe ingestion endpoints & Supabase mock validation
│   ├── test_product_matching_api.py# Deterministic product matching & multi-variant surfacing
│   ├── test_cart_api.py            # Active cart auto-creation, item additions, SKU uniqueness
│   ├── test_checkout_order_api.py  # Atomic checkout, row locking, price snapshots
│   └── test_seed_integrity.py      # Validation of 100-product canonical seed catalog
│
├── ai/
│   ├── test_structured_output.py   # Pydantic schema validation for ExtractedRecipe
│   ├── test_confidence_eval.py     # Confidence thresholding (0.70) & confirmation flags
│   └── test_alternative_ranking.py # Candidate pre-filtering & LLM alternative ranking
│
└── e2e/
    └── test_end_to_end_scenarios.py# 9 mandatory end-to-end integration workflows
```

---

## 2. Seed Data Integrity Testing Specification (`tests/integration/test_seed_integrity.py`)

The 100-product canonical dataset defined in [`docs/12-seed-data.md`](file:///Users/shubham/Desktop/clock_it%20_backend/docs/12-seed-data.md) serves as the authoritative catalog fixture for all integration and E2E tests.

`test_seed_integrity.py` validates the baseline database state upon migration and seeding:

1. **Exact Entity Counts**:
   - `Product` count == `100`
   - `ProductVariant` count == `200`
   - `Inventory` count == `200` (1:1 mapping with `ProductVariant`)
   - Unique `brand` count == `15`
   - Unique `category` count == `10`
   - Products with `metadata_json->'alternatives_for'` mappings == `34`
   - Low-stock inventory records (`1 <= available_quantity <= 3`) == `12`
   - Out-of-stock inventory records (`available_quantity == 0`) == `12`

2. **Relational Integrity & Schema Validation**:
   - Every `ProductVariant` links to a valid `Product.id` foreign key.
   - Every `ProductVariant` has exactly one corresponding `Inventory.variant_id` record.
   - Every `sku` in `product_variants` is globally unique.
   - Every variant `price` and `size` field is `Decimal`-compatible (`NUMERIC(10, 2)`).

3. **Mandatory Fixture Verification**:
   - **Primary Milk**: `SKU-AMUL-MILK-500ML`, `SKU-AMUL-MILK-1L`, `SKU-NANDINI-MILK-500ML`, `SKU-MOTHER-MILK-500ML`, `SKU-MOTHER-MILK-1L`.
   - **Milk Alternatives**: Raw Pressery Almond Milk (`SKU-RAW-ALMOND-1L`), Sofit Soy Milk (`SKU-SOFIT-SOY-1L`), OatMlk Oat Milk (`SKU-OATMLK-1L`).
   - **Out-of-Stock Paneer**: Amul Paneer (`SKU-AMUL-PANEER-200G`, `SKU-AMUL-PANEER-500G`) both have `available_quantity == 0`.
   - **Paneer Alternatives**: Urban Platter Tofu (`SKU-UP-TOFU-250G`, `SKU-UP-TOFU-500G`) both have `alternatives_for: ["paneer"]`.

---

## 3. Unit Testing Strategy

### A. Normalization Tests (`test_normalization.py`)
- Verifies raw string extractions convert to exact lowercase `snake_case` canonical keys:
  - `"atta"`, `"wheat flour"`, `"whole wheat flour"` ──► `"wheat_flour"`
  - `"fresh farm milk"`, `"toned milk"`, `"cow milk"` ──► `"milk"`
  - `"cottage cheese"`, `"fresh paneer"` ──► `"paneer"`
- Verifies functional distinctions are preserved (`"almond_milk"` vs `"cow_milk"`).

### B. Pricing Math Tests (`test_pricing_math.py`)
- **Decimal Standard**: All assertions use `decimal.Decimal` objects exclusively. Floating-point comparisons are strictly forbidden.
- Verifies `unit_price * quantity = line_subtotal` (e.g. `Decimal("54.00") * 3 = Decimal("162.00")`).
- Verifies `sum(line_subtotals) = total_amount`.

### C. Inventory & Quantity Validation Tests (`test_inventory_logic.py`)
- Verifies `quantity <= 0` raises HTTP 400 validation error.
- Verifies `quantity > 0` passes schema validation.
- Verifies inventory stock checks for sufficient, low, zero, and out-of-stock scenarios.

---

## 4. Integration Testing Strategy

### A. Authentication API Tests (`test_auth_api.py`)
Validates the complete 10-step authentication contract:
1. Register user via `POST /api/v1/auth/signup` (201 Created).
2. Login user via `POST /api/v1/auth/login` (200 OK, returns 1-hour JWT).
3. Access protected route with `Authorization: Bearer <token>` (200 OK).
4. Missing Authorization header (401 Unauthorized).
5. Invalid JWT signature (401 Unauthorized).
6. Expired JWT token (> 3600 seconds) (401 Unauthorized).
7. Malformed UUID in `sub` claim (e.g., `"not-a-uuid"`) (401 Unauthorized).
8. Missing `sub` claim in token payload (401 Unauthorized).
9. Inactive user (`is_active = False`) (401 Unauthorized).
10. Validates token claims contain `sub`, `iat`, `exp` with algorithm `HS256`.

### B. Strict Resource Ownership Isolation Tests
Verifies that User A attempting to access User B's resources (`recipes`, `recipe_ingredients`, `carts`, `cart_items`, `orders`, `order_items`) receives **`HTTP 404 Not Found`** with `detail: "Resource not found"`, hiding resource existence and preventing ID enumeration.

### C. Supabase Storage Service Tests (`test_recipe_api.py`)
- Mocks Supabase Storage SDK client in integration tests.
- Validates MIME type allowlist (`image/jpeg`, `image/png`, `image/webp`).
- Verifies invalid MIME types, empty payloads, or payloads > 10MB (`10,485,760` bytes) return `HTTP 400 Bad Request`.
- Verifies generated object path format: `users/{user_id}/recipes/{recipe_id}.{extension}`.
- Verifies Supabase upload failure returns `HTTP 502 Bad Gateway` (`STORAGE_UPLOAD_FAILED`).
- Confirms zero local filesystem (`/tmp`), AWS S3, GCP GCS, or CDN fallbacks exist.

### D. Deterministic Product Matching Tests (`test_product_matching_api.py`)
- Validates that searching for `canonical_name: "milk"` surfaces all 5 available in-stock variants across all 3 brands (Amul 500ml/1L, Nandini 500ml, Mother Dairy 500ml/1L).
- Verifies multi-brand and multi-size variants are returned without artificial brand capping.

---

## 5. AI Engine & Workflow Testing Strategy (`tests/ai/`)

- **Structured Output Parsing (`test_structured_output.py`)**: Tests Pydantic model validation (`ExtractedRecipe`, `RankedAlternativeResponse`).
- **Confidence Threshold Evaluation (`test_confidence_eval.py`)**: Tests threshold `0.70`. Extractions with `confidence >= 0.70` set `requires_confirmation = False`; extractions with `confidence < 0.70` set `requires_confirmation = True`.
- **Alternative Candidate Ranking (`test_alternative_ranking.py`)**: Mocks Vertex AI responses to verify LLM alternative ranking logic receives pre-filtered in-stock candidates (`available_quantity > 0`) matching `metadata_json->'alternatives_for'`.

---

## 6. End-to-End Test Scenarios (Mandatory Validation Matrix)

### Scenario 1: Image Recipe Pipeline to Confirmed Order
1. Upload recipe image to `POST /api/v1/recipes/process-image`.
2. Fetch matching product variants via `POST /api/v1/recipes/{id}/products`.
3. Add selected variant SKU to active cart via `POST /api/v1/cart/items`.
4. Execute checkout via `POST /api/v1/orders`.
5. Verify order status is `confirmed`, subtotal math matches `Decimal`, stock is deducted, and `OrderItem` historical snapshots are immutable.

### Scenario 2: Camera Photo Ingestion Pipeline
- Upload camera snapshot binary payload to `POST /api/v1/recipes/process-image`.
- Verify camera capture uses the exact same storage and AI parsing pipeline as standard file upload.

### Scenario 3: Plain Text Recipe Parsing
- Post payload `{"title": "Pancakes", "text": "1 cup milk, 2 eggs, 1 cup flour"}` to `POST /api/v1/recipes/process-text`.
- Verify structured ingredient extraction (`milk`, `egg`, `wheat_flour`).

### Scenario 4: Recipe Webpage URL Scraping
- Post URL payload to `POST /api/v1/recipes/process-url`.
- Verify `webpage_fetcher.py` strips HTML tags and passes clean body text to LLM parser.

### Scenario 5: YouTube Video Transcript Processing
- Post YouTube URL payload to `POST /api/v1/recipes/process-video`.
- Verify `youtube_transcript.py` extracts audio transcript text and parses recipe ingredients.

### Scenario 6: Out-of-Stock Primary Fallback to Alternatives
- Execute within an isolated test transaction (`session.begin_nested()` SAVEPOINT): update primary milk variants (`SKU-AMUL-MILK-500ML`, `SKU-AMUL-MILK-1L`, `SKU-NANDINI-MILK-500ML`, `SKU-MOTHER-MILK-500ML`, `SKU-MOTHER-MILK-1L`) to `available_quantity = 0`.
- Request product matches for `canonical_name: "milk"`.
- Verify out-of-stock gatekeeper triggers alternative flow, pre-filters in-stock metadata candidates (`Almond Milk`, `Soy Milk`), filters out out-of-stock candidates (`Oat Milk`), invokes LLM ranking, and returns ranked alternatives with 1-sentence rationales.
- Rollback transaction cleanly after test, leaving baseline seed catalog intact.

### Scenario 7: Package Size Freedom (500ml Recipe -> 1L Purchase)
- Recipe ingredient requires `500ml milk`. User selects `1L` variant (`SKU-AMUL-MILK-1L`).
- Verify cart accepts `1L` variant without enforcing `recipe_size == product_variant_size`.

### Scenario 8: Multiple Purchase Quantity & Decimal Totals
- User selects variant `SKU-AMUL-MILK-1L` (`price = Decimal("54.00")`) with `quantity = 3`.
- Verify `line_total = Decimal("162.00")` and order grand total reflects exact 3x unit price.

### Scenario 9: Inventory Race Condition & Concurrency Hardening
- Cart contains SKU with `quantity = 5` when `available_quantity = 5`.
- Concurrent transaction reduces stock to `2` prior to checkout execution.
- User posts `POST /api/v1/orders`.
- Verify backend returns `HTTP 409 Conflict` with `INSUFFICIENT_STOCK` payload.
- **Transaction Atomicity Verification**: Verify row locks (`SELECT ... FOR UPDATE`) on `Cart`, `CartItem`, and `Inventory` prevent overselling, roll back transaction cleanly, leave zero orphan order items, and preserve inventory.

---

## 7. Database Transaction & Isolation Strategy

1. **Atomic Checkout Transaction Boundary**:
   Checkout executes the following operations inside a **single PostgreSQL transaction**:
   ```sql
   BEGIN TRANSACTION;
   SELECT * FROM carts WHERE user_id = $1 AND status = 'active' FOR UPDATE;
   SELECT * FROM cart_items WHERE cart_id = $cart_id FOR UPDATE;
   SELECT * FROM inventory WHERE variant_id = $variant_id FOR UPDATE;
   -- Validate Stock & Read Authoritative Decimal Prices
   -- Deduct Inventory
   -- Insert Order & OrderItem Snapshots
   -- Update Cart Status = 'converted'
   COMMIT TRANSACTION;
   ```
   If stock validation fails, the entire transaction issues a `ROLLBACK`, guaranteeing zero partial state corruption.

2. **Test State Isolation**:
   Every integration test runs inside a nested transaction (`SAVEPOINT`). Changes made during tests (e.g. stock deduction or setting primary milk stock to 0) are rolled back automatically upon test completion, keeping the canonical 100-product seed database pristine and reproducible across test runs.
