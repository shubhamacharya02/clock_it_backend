# Document 05: API Specification & REST Contracts

## 1. Authentication Endpoints

### `POST /api/v1/auth/signup`
- **Description**: Registers a new user.
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe"
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "created_at": "2026-08-30T00:00:00Z"
    }
    ```
  - `400 Bad Request`: Email already exists.

---

### `POST /api/v1/auth/login`
- **Description**: Authenticates user credentials and returns a JWT access token valid for 1 hour.
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 3600
    }
    ```
  - `401 Unauthorized`: Invalid email or password.
- **Token Specifications**:
  - JWT access token lifetime = 1 hour (3600 seconds).
  - All protected endpoints require a valid Bearer JWT passed via `Authorization: Bearer <token>`.
  - Expired or invalid tokens return `401 Unauthorized`.

---

### `GET /api/v1/auth/me`
- **Description**: Fetches current authenticated user profile.
- **Authentication**: Bearer Token required.
- **Responses**:
  - `200 OK`: User profile object.
  - `401 Unauthorized`: Invalid or expired JWT token.

---

## 2. Recipe Ingestion Endpoints

> [!IMPORTANT]
> **Unified Image Endpoint**: `POST /api/v1/recipes/process-image` handles both uploaded recipe images and client camera captures via the exact same backend ingestion, Supabase Storage, and Vertex AI Vision pipeline. No separate camera endpoint exists.

### `POST /api/v1/recipes/process-image`
- **Description**: Processes an uploaded recipe image or camera snapshot via Vertex AI Vision.
- **Authentication**: Bearer Token required.
- **Content-Type**: `multipart/form-data`
- **Form Parameters**:
  - `file`: Binary file (image/jpeg, image/png, image/webp; max 10MB)
- **Responses**:
  - `201 Created`:
    ```json
    {
      "recipe_id": "8f3b2e1a-4c9d-4e5f-b6a7-8c9d0e1f2a3b",
      "title": "Paneer Butter Masala",
      "source_type": "image",
      "storage_path": "users/123/recipes/photo_001.jpg",
      "status": "completed",
      "ingredients": [
        {
          "id": "11111111-2222-3333-4444-555555555555",
          "raw_name": "Fresh Paneer Cubes",
          "canonical_name": "paneer",
          "quantity": 250.0,
          "unit": "g",
          "confidence": 0.95,
          "requires_confirmation": false
        },
        {
          "id": "22222222-3333-4444-5555-666666666666",
          "raw_name": "Whole Milk",
          "canonical_name": "milk",
          "quantity": 500.0,
          "unit": "ml",
          "confidence": 0.98,
          "requires_confirmation": false
        }
      ]
    }
    ```
  - `400 Bad Request`: Invalid MIME type or payload exceeding 10MB.
  - `401 Unauthorized`: Invalid or expired JWT.
  - `502 Bad Gateway`: Supabase Storage upload or Vertex AI failure.

---

### `POST /api/v1/recipes/process-text`
- **Description**: Processes a raw text recipe.
- **Authentication**: Bearer Token required.
- **Request Body**:
  ```json
  {
    "title": "Quick Butter Chicken",
    "text": "Ingredients: 500g chicken, 200ml butter cream, 2 tsp garam masala..."
  }
  ```
- **Responses**:
  - `201 Created`: Structured Recipe object.
  - `401 Unauthorized`: Invalid or expired JWT.

---

### `POST /api/v1/recipes/process-url`
- **Description**: Fetches recipe webpage HTML via `Webpage Fetcher Integration`, strips script/style tags, extracts body text, and parses ingredients via LLM.
- **Authentication**: Bearer Token required.
- **Request Body**:
  ```json
  {
    "url": "https://example.com/recipes/paneer-tikka"
  }
  ```
- **Responses**:
  - `201 Created`: Structured Recipe object.
  - `401 Unauthorized`: Invalid or expired JWT.
  - `422 Unprocessable Entity`: Unable to scrape content or URL unreachable.

---

### `POST /api/v1/recipes/process-video`
- **Description**: Fetches audio transcript for YouTube video via `YouTube Transcript Integration` and extracts ingredients via LLM. Video frame analysis is explicitly out of scope.
- **Authentication**: Bearer Token required.
- **Request Body**:
  ```json
  {
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }
  ```
- **Responses**:
  - `201 Created`: Structured Recipe object.
  - `400 Bad Request`: Transcript missing or disabled for the video.
  - `401 Unauthorized`: Invalid or expired JWT.

---

### `GET /api/v1/recipes/{recipe_id}`
- **Description**: Retrieves a processed recipe by ID.
- **Authentication**: Bearer Token required.
- **Responses**:
  - `200 OK`: Full Recipe entity with ingredients.
  - `401 Unauthorized`: Invalid or expired JWT.
  - `404 Not Found`: Recipe does not exist or does not belong to the authenticated user.

---

### `PATCH /api/v1/recipes/{recipe_id}/ingredients`
- **Description**: Allows user to confirm or edit low-confidence ingredient details.
- **Authentication**: Bearer Token required.
- **Request Body**:
  ```json
  {
    "updates": [
      {
        "ingredient_id": "11111111-2222-3333-4444-555555555555",
        "canonical_name": "paneer",
        "quantity": 300.0,
        "unit": "g"
      }
    ]
  }
  ```
- **Responses**:
  - `200 OK`: Updated Recipe entity.
  - `401 Unauthorized`: Invalid or expired JWT.
  - `404 Not Found`: Recipe does not exist or does not belong to the authenticated user.

---

## 3. Product Discovery Endpoints

### `POST /api/v1/recipes/{recipe_id}/products`
- **Description**: Matches recipe ingredients to available product SKUs in PostgreSQL.
- **Authentication**: Bearer Token required.
- **Product Discovery Rules**:
  - **Size Freedom**: Recipe quantity and unit (`500ml milk`) DO NOT constrain purchasable package sizes. All active in-stock variants (`500ml`, `1L`, `2L`, `5L`) across all brands are returned. The system does NOT enforce `recipe_size == product_variant_size` or auto-select sizes.
  - **Purchase Quantity Independence**: Users select any purchase quantity. The backend validates inventory against the user's requested purchase quantity, NOT recipe quantity.
  - **Strict Out-of-Stock Alternative Gate**: Alternative discovery executes **ONLY IF** ZERO active + in-stock primary product variants exist across ALL relevant brands and package sizes. (e.g., If `Nandini 500ml Milk` has stock 10, show Nandini Milk; DO NOT return Almond/Soy milk as alternatives and DO NOT invoke alternative LLM).
- **Responses**:
  - `200 OK` (Primary Product Match):
    ```json
    {
      "recipe_id": "8f3b2e1a-4c9d-4e5f-b6a7-8c9d0e1f2a3b",
      "matches": [
        {
          "ingredient_id": "22222222-3333-4444-5555-666666666666",
          "canonical_name": "milk",
          "recipe_quantity": 500.0,
          "recipe_unit": "ml",
          "status": "MATCH_FOUND",
          "products": [
            {
              "variant_id": "sku_101",
              "product_name": "Taaza Toned Milk",
              "brand": "Amul",
              "size": 500.0,
              "size_unit": "ml",
              "price": 28.0,
              "available_quantity": 15,
              "is_alternative": false,
              "alternative_reason": null
            },
            {
              "variant_id": "sku_102",
              "product_name": "Taaza Toned Milk",
              "brand": "Amul",
              "size": 1000.0,
              "size_unit": "ml",
              "price": 54.0,
              "available_quantity": 8,
              "is_alternative": false,
              "alternative_reason": null
            }
          ]
        }
      ]
    }
    ```
  - `200 OK` (Alternative Recommendation when ALL Primary SKUs Out of Stock):
    ```json
    {
      "recipe_id": "8f3b2e1a-4c9d-4e5f-b6a7-8c9d0e1f2a3b",
      "matches": [
        {
          "ingredient_id": "22222222-3333-4444-5555-666666666666",
          "canonical_name": "milk",
          "recipe_quantity": 500.0,
          "recipe_unit": "ml",
          "status": "ALTERNATIVE_RECOMMENDED",
          "products": [
            {
              "variant_id": "sku_almond_101",
              "product_name": "Unsweetened Almond Milk",
              "brand": "Raw Pressery",
              "size": 1000.0,
              "size_unit": "ml",
              "price": 180.0,
              "available_quantity": 12,
              "is_alternative": true,
              "alternative_reason": "Primary milk products are currently out of stock."
            }
          ]
        }
      ]
    }
    ```
  - `401 Unauthorized`: Invalid or expired JWT.
  - `404 Not Found`: Recipe does not exist or does not belong to user.

---

### `GET /api/v1/products/{variant_id}`
- **Description**: Retrieves single product variant SKU details.
- **Authentication**: Bearer Token required.
- **Responses**:
  - `200 OK`: Product Variant object.
  - `404 Not Found`: Variant SKU not found.

---

## 4. Cart Management Endpoints

> [!IMPORTANT]
> **Cart Inventory Rule**: Cart operations (`POST /cart/items`, `PATCH /cart/items/{id}`) validate that requested quantity does not exceed current stock, but **DO NOT** deduct or reserve inventory. The MVP database contains no `reserved_quantity` column. Inventory is deducted strictly during successful checkout.

### `GET /api/v1/cart`
- **Description**: Fetches user's active cart. If the user has an active cart, returns it. If the user does NOT have an active cart, automatically initializes a new empty active cart and returns it.
- **Authentication**: Bearer Token required.
- **Responses**:
  - `200 OK`: Active Cart object containing items, unit prices, subtotal, and totals.

---

### `POST /api/v1/cart/items`
- **Description**: Adds a product variant SKU to cart. If the SKU is already present in the active cart, updates the `quantity` on the existing `CartItem` row (enforcing `UNIQUE(cart_id, variant_id)`).
- **Authentication**: Bearer Token required.
- **Request Body**:
  ```json
  {
    "variant_id": "sku_101",
    "quantity": 2
  }
  ```
- **Responses**:
  - `200 OK`: Updated Cart object.
  - `400 Bad Request`: Variant inactive or invalid quantity (`quantity <= 0`).
  - `404 Not Found`: Variant SKU does not exist.
  - `409 Conflict`: Requested quantity exceeds currently available inventory.

---

### `PATCH /api/v1/cart/items/{item_id}`
- **Description**: Updates item quantity in cart.
- **Authentication**: Bearer Token required.
- **Request Body**: `{"quantity": 3}`
- **Responses**:
  - `200 OK`: Updated Cart object.
  - `404 Not Found`: Cart item does not exist or does not belong to user's active cart.
  - `409 Conflict`: Requested quantity exceeds available inventory.

---

### `DELETE /api/v1/cart/items/{item_id}`
- **Description**: Removes an item from cart.
- **Authentication**: Bearer Token required.
- **Responses**:
  - `200 OK`: Updated Cart object.
  - `404 Not Found`: Cart item does not exist or does not belong to user's active cart.

---

## 5. Checkout & Order Endpoints

### `POST /api/v1/orders`
- **Description**: Executes checkout on user's active cart with atomic stock validation and row locking (`SELECT ... FOR UPDATE`).
- **Authentication**: Bearer Token required.
- **Validation Rules**:
  - **Empty Cart Check**: If the user's active cart contains zero items, returns `400 Bad Request` (`EMPTY_CART`). No order or transaction is created.
  - **Stock Re-validation**: Re-reads stock with row locks. If any item stock is insufficient, rolls back transaction and returns `409 Conflict`.
  - **Authoritative Price Reading**: Reads current product variant prices from PostgreSQL, computes grand total, deducts stock, creates order and immutable snapshots (`unit_price_snapshot`, `line_total`), and marks cart as `converted`.
- **Responses**:
  - `201 Created`:
    ```json
    {
      "order_id": "99999999-8888-7777-6666-555555555555",
      "order_number": "ORD-20260830-10492",
      "total_amount": 110.0,
      "status": "confirmed",
      "items": [
        {
          "variant_id": "sku_101",
          "product_name_snapshot": "Taaza Toned Milk",
          "brand_snapshot": "Amul",
          "size_snapshot": 500.0,
          "unit_snapshot": "ml",
          "unit_price_snapshot": 28.0,
          "quantity": 2,
          "line_total": 56.0
        }
      ],
      "created_at": "2026-08-30T01:00:00Z"
    }
    ```
  - `400 Bad Request`: Cart is empty (`EMPTY_CART`) or cart is inactive.
  - `401 Unauthorized`: Invalid or expired JWT.
  - `409 Conflict`: Insufficient inventory at moment of checkout (`INSUFFICIENT_STOCK`).

---

### `GET /api/v1/orders/{order_id}`
- **Description**: Retrieves order details by order ID.
- **Authentication**: Bearer Token required.
- **Responses**:
  - `200 OK`: Full Order object with historical snapshot items.
  - `404 Not Found`: Order does not exist or does not belong to the authenticated user.

---

### `GET /api/v1/orders`
- **Description**: Lists all historical orders for the authenticated user.
- **Authentication**: Bearer Token required.
- **Responses**:
  - `200 OK`: List of Order objects.

---

## 6. Global Business & Security Rules

1. Every protected endpoint requires a valid Bearer JWT passed via the `Authorization: Bearer <token>` header.
2. Users can access only their own recipes, recipe ingredients, carts, cart items, orders, and order items. Attempts to access another user's resources return `404 Not Found` (to hide resource existence).
3. The AI engine must never directly query or mutate PostgreSQL.
4. Standard product discovery is deterministic SQL/database logic.
5. Alternatives are triggered ONLY when ALL primary variants are out of stock across all brands and package sizes.
6. Alternative compatibility comes strictly from product metadata (`metadata_json->'alternatives_for'`).
7. The LLM only ranks/explains backend-approved alternative candidates that exist in the catalog and have available inventory.
8. The LLM cannot invent products or compatibility relationships.
9. Recipe quantity does not constrain purchasable package size.
10. User purchase quantity is independent from recipe required quantity.
11. Cart operations do not reserve or deduct inventory.
12. Checkout performs fresh, authoritative inventory validation.
13. Checkout reads authoritative current product prices from PostgreSQL.
14. Checkout is atomic and uses database inventory row locking (`SELECT ... FOR UPDATE`).
15. Failed inventory validation during checkout returns `409 Conflict`.
16. Empty-cart checkout returns `400 Bad Request` (`EMPTY_CART`).
17. Successful order creation returns `201 Created`.
18. No payment gateway exists in the MVP version.
19. Camera captures and uploaded images use the exact same image processing endpoint (`POST /recipes/process-image`).
20. YouTube processing uses audio transcripts only; video-frame analysis is out of scope.
21. Supabase Storage is the single configured storage provider.
22. PostgreSQL is the single source of truth for catalog, inventory, carts, and orders.
