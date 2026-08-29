# Document 03: Complete System & Data Flows

## 1. Recipe Processing Ingestion Flows

### A. Image & Camera Upload Flow
Camera capture and normal image upload use the **exact same backend image processing pipeline**. Public image URLs are NOT required by the architecture; storage path or supported image reference mechanisms are passed to the AI pipeline.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI (/recipes/process-image)
    participant Storage as Supabase Storage
    participant Graph as Recipe LangGraph
    participant LLM as Vertex AI Vision
    participant DB as PostgreSQL

    Client->>API: POST /recipes/process-image (File Payload)
    API->>API: Validate MIME Type & File Size (<= 10MB)
    API->>Storage: Upload Image to bucket 'recipe-media'
    Storage-->>API: Return storage_path / Image Reference
    API->>Graph: Invoke Recipe Graph (storage_path / Image Reference)
    Graph->>LLM: Send Multimodal Prompt + Image Reference
    LLM-->>Graph: Return Extracted JSON (Dish, Ingredients, Quantities, Confidence)
    Graph->>Graph: Perform Semantic Ingredient Normalization & Check Confidence Threshold (0.70)
    Graph-->>API: Structured Recipe Object
    API->>DB: Persist Recipe & RecipeIngredients (status='completed')
    API-->>Client: 201 Created (Recipe JSON + Ingredients)
```

---

### B. Plain Text Recipe Flow
```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI (/recipes/process-text)
    participant Graph as Recipe LangGraph
    participant LLM as Vertex AI Text
    participant DB as PostgreSQL

    Client->>API: POST /recipes/process-text (Text JSON)
    API->>Graph: Invoke Recipe Graph (Raw Text)
    Graph->>LLM: Send Text Extraction Prompt
    LLM-->>Graph: Return Extracted JSON
    Graph->>Graph: Perform Semantic Ingredient Normalization & Evaluate Confidence
    Graph-->>API: Structured Recipe Object
    API->>DB: Persist Recipe & RecipeIngredients
    API-->>Client: 201 Created (Recipe JSON)
```

---

### C. Recipe Webpage URL Flow
```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI (/recipes/process-url)
    participant Fetcher as Webpage Fetcher Integration
    participant Graph as Recipe LangGraph
    participant LLM as Vertex AI Text
    participant DB as PostgreSQL

    Client->>API: POST /recipes/process-url (url)
    API->>Fetcher: Fetch Webpage Content (httpx)
    Fetcher->>Fetcher: Strip Script/Style HTML tags & Extract Main Body Text
    Fetcher-->>API: Clean HTML Text Content
    API->>Graph: Invoke Recipe Graph (Clean Text)
    Graph->>LLM: Parse Recipe from Text
    LLM-->>Graph: Return Structured JSON
    Graph-->>API: Structured Recipe Object
    API->>DB: Persist Recipe & RecipeIngredients
    API-->>Client: 201 Created (Recipe JSON)
```

---

### D. YouTube Video URL Flow
```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI (/recipes/process-video)
    participant Scraper as YouTube Transcript Integration
    participant Graph as Recipe LangGraph
    participant LLM as Vertex AI Text
    participant DB as PostgreSQL

    Client->>API: POST /recipes/process-video (video_url)
    API->>Scraper: Extract Video ID & Fetch Transcript
    Scraper-->>API: Concatenated Transcript Text
    API->>Graph: Invoke Recipe Graph (Transcript Text)
    Graph->>LLM: Parse Recipe from Video Transcript
    LLM-->>Graph: Return Structured JSON
    Graph-->>API: Structured Recipe Object
    API->>DB: Persist Recipe & RecipeIngredients
    API-->>Client: 201 Created (Recipe JSON)
```

---

### E. Semantic Ingredient Normalization Principle
The AI engine is responsible strictly for **semantic ingredient normalization**:

```
"fresh whole milk" ──┐
"toned milk" ───────┼───► LLM ───► canonical_name: "milk"
"cow milk" ─────────┘
```

The LLM produces the standardized canonical identifier string (e.g. `milk`). After normalization:
- Backend services use the canonical identifier to query PostgreSQL for actual products and product variants.
- The LLM **MUST NOT**: query the database directly, select an actual SKU, control inventory, or invent catalog products.

---

## 2. Product Discovery & Matching Flow

### Recipe Quantity vs. Purchase Quantity Rule
Recipe ingredient quantity (e.g., `Milk = 500ml`) is informational and does **NOT** constrain the user's purchase selection.
- **Example**: A user may select `Milk 1L × 1`, `Milk 1L × 2`, or `Milk 2L × 1` for a `500ml` recipe requirement.
- **Inventory Constraint**: The system strictly enforces `requested_purchase_quantity <= available_inventory_quantity`. It does **NOT** enforce `purchase_quantity == recipe_quantity`.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI (/recipes/{id}/products)
    participant ProductSvc as Product Service
    participant DB as PostgreSQL

    Client->>API: POST /recipes/{recipe_id}/products
    API->>ProductSvc: Match Products for Recipe Canonical Ingredients
    
    loop For Each Recipe Ingredient
        ProductSvc->>DB: Query products JOIN variants JOIN inventory WHERE canonical_name = X AND available_quantity > 0
        
        alt Available Matching Primary Variants Exist (Across any brand/size)
            DB-->>ProductSvc: Return Matching Variants (All Brands, Sizes, Stock)
            ProductSvc->>ProductSvc: Mark Status = "MATCH_FOUND"
        else Zero Matching Variants in Stock
            ProductSvc->>ProductSvc: Trigger Alternative Discovery Flow (See Section 3)
        end
    end

    ProductSvc-->>API: Mapped Ingredients to Available Products/Alternatives
    API-->>Client: 200 OK (Product Options Array grouped by Ingredient)
```

---

## 3. Alternative Compatibility & Recommendation Flow

Alternative recommendations are triggered **ONLY** when no purchasable product variant matching the canonical ingredient is available in inventory across all relevant brands and package sizes.

```
Primary Ingredient
        ↓
Check ALL matching product variants
        ↓
Any primary variant available?
        │
    ┌───┴────┐
    │        │
   YES       NO
    │        │
    ▼        ▼
Show       Product Metadata
Primary        ↓
Products   Eligible Alternatives
               ↓
           Inventory Filter
               ↓
           Available Alternatives
               ↓
           LLM Ranking
               ↓
           Show Alternatives
```

> [!IMPORTANT]
> **LLM Input Boundaries**: The LLM receives **ONLY** alternatives that:
> 1. Are already declared compatible by product catalog metadata (`metadata_json->'alternatives_for'`).
> 2. Exist in the catalog.
> 3. Have available inventory (`available_quantity > 0`).
>
> The LLM may rank or explain eligible alternatives. The LLM **must NOT** determine alternative compatibility itself or recommend out-of-stock items.

```mermaid
sequenceDiagram
    autonumber
    participant ProductSvc as Product Service
    participant DB as PostgreSQL
    participant Graph as Alternative LangGraph
    participant LLM as Vertex AI

    Note over ProductSvc: Triggered ONLY when primary ingredient has ZERO in-stock variants across ALL brands & sizes

    ProductSvc->>DB: Query products WHERE metadata_json->'alternatives_for' CONTAINS canonical_name
    DB-->>ProductSvc: Candidate Alternative Products (From Metadata)
    ProductSvc->>DB: Filter Candidates: JOIN variants JOIN inventory WHERE available_quantity > 0
    DB-->>ProductSvc: Available Compatible Variants

    alt Compatible Available Variants Found
        ProductSvc->>Graph: Invoke Alternative Graph (Ingredient Context + Available Candidates)
        Graph->>LLM: Rank candidates by culinary suitability & generate concise rationale
        LLM-->>Graph: Ranked Alternatives with Reasons
        Graph-->>ProductSvc: Final Ranked Alternatives List
    else No Compatible Variants Available
        ProductSvc->>ProductSvc: Set Status = "OUT_OF_STOCK_NO_ALTERNATIVES"
    end
```

---

## 4. Cart & Checkout Pipeline Flow

### Authoritative Pricing & Order Snapshot Rule
During checkout, the Order Service reads the **authoritative current product variant price** from PostgreSQL when calculating the order total and writes an immutable snapshot into `order_items`.

- **Example**:
  - `ProductVariant`: Current price = ₹120
  - `OrderItem Snapshot`: `unit_price_snapshot = ₹120`, `quantity = 2`, `line_total = ₹240`
- Preserves financial audit trails even if product prices change in the future.

### Atomic Checkout Transaction Flow
```
BEGIN TRANSACTION
        ↓
Lock relevant inventory rows (SELECT ... FOR UPDATE)
        ↓
Validate requested quantities (available_quantity >= requested_quantity)
        ↓
Read authoritative current prices
        ↓
Calculate subtotal / taxes / total
        ↓
Deduct inventory
        ↓
Create order
        ↓
Create order item snapshots
        ↓
Convert cart
        ↓
COMMIT
```

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI (/orders)
    participant OrderSvc as Order Service
    participant DB as PostgreSQL

    Client->>API: POST /api/v1/orders (Checkout Active Cart)
    API->>OrderSvc: Process Checkout for Current User
    OrderSvc->>DB: BEGIN TRANSACTION
    OrderSvc->>DB: Lock Cart & Fetch Items: SELECT * FROM cart_items WHERE cart_id = X FOR UPDATE
    
    loop For Each Cart Item
        OrderSvc->>DB: SELECT * FROM inventory WHERE variant_id = SKU FOR UPDATE
        
        alt Available Quantity < Requested Quantity
            DB-->>OrderSvc: Insufficient Inventory
            OrderSvc->>DB: ROLLBACK TRANSACTION
            OrderSvc-->>API: Raise HTTP 409 Conflict (Item Out of Stock)
            API-->>Client: 409 Conflict Error Payload
        end
    end

    Note over OrderSvc,DB: All items have sufficient stock
    
    loop For Each Cart Item
        OrderSvc->>DB: Read Authoritative Variant Price & UPDATE inventory (available_quantity = available_quantity - qty)
    end

    OrderSvc->>OrderSvc: Calculate Final Price Subtotal, Taxes, & Total Amount
    OrderSvc->>DB: INSERT INTO orders (user_id, order_number, total_amount, status='confirmed')
    OrderSvc->>DB: INSERT INTO order_items (snapshot: brand, SKU, size, unit_price_snapshot, qty, line_total)
    OrderSvc->>DB: UPDATE carts SET status = 'converted' WHERE id = X
    OrderSvc->>DB: COMMIT TRANSACTION
    
    OrderSvc-->>API: Order Object with Order Items
    API-->>Client: 201 Created (Order Confirmation Details)
```
