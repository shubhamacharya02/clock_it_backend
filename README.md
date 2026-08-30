<div align="center">

# ✨ ClockIt AI Backend ✨
### *Recipe-to-Commerce Intelligence Platform*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-AsyncPG-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash/Pro-8E44AD?style=for-the-badge&logo=googlegemini&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![LangChain](https://img.shields.io/badge/LangGraph-LangChain-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<br />

### 🛠️ Core Technology Stack

[![My Skills](https://skillicons.dev/icons?i=py,fastapi,postgres,docker,gcp,git,vscode,github,postman)](https://skillicons.dev)

</div>

---

## 📖 Table of Contents
- [🌟 Overview](#-overview)
- [💻 Tech Stack & Architecture](#-tech-stack--architecture)
- [🏗️ System Architecture & Data Flow](#️-system-architecture--data-flow)
- [🔄 Detailed User Flow](#-detailed-user-flow)
- [📊 Database Schema & Data Models](#-database-schema--data-models)
- [🔌 API Specification Directory](#-api-specification-directory)
- [⚙️ Environment Configuration](#️-environment-configuration)
- [🚀 Quick Start & Installation](#-quick-start--installation)
- [🧪 Testing & Verification](#-testing--verification)
- [🛡️ Security & Authentication](#️-security--authentication)

---

## 🌟 Overview

**ClockIt AI Backend** is an enterprise-grade, asynchronous Python platform that seamlessly bridges culinary content (recipes from images, videos, web links, or raw text) directly with e-commerce fulfillment. 

By leveraging **Google Gemini 1.5 Flash/Pro**, **LangChain**, and **LangGraph**, the backend automatically ingests multi-modal recipe inputs, parses ingredients into structured schemas, matches ingredients to store inventory with confidence scoring, and orchestrates an atomic cart-to-checkout workflow.

### Key Capabilities
- 📸 **Multi-Modal Ingestion**: Extract recipes from food photos/images, web article URLs, YouTube video transcripts, or unformatted text.
- 🧠 **LangGraph Orchestration**: State-driven LLM graph pipelines for extraction, unit standardization, ingredient normalization, and data validation.
- 🎯 **Smart Product Matcher**: Algorithmic e-commerce mapping connecting extracted ingredients to available product variants based on semantic similarity and inventory bounds.
- 🛒 **Real-Time Cart & Inventory**: Dynamic availability verification, quantity management, and transactional order settlement.
- ⚡ **High Performance Async Core**: Built on FastAPI, SQLModel, SQLAlchemy 2.0 (AsyncIO), and `asyncpg` for maximum throughput.

---

## 💻 Tech Stack & Architecture

| Layer | Component | Technologies |
| :--- | :--- | :--- |
| **API Layer** | Web Framework | **FastAPI**, Uvicorn (ASGI), Pydantic v2 |
| **AI Orchestration** | LLM Engine & Agents | **LangGraph**, **LangChain**, **Google Gemini 1.5 Flash/Pro** (via Vertex AI / Google GenAI SDK) |
| **Database Layer** | Async ORM & Storage | **PostgreSQL**, **SQLModel**, **SQLAlchemy 2.0 (AsyncIO)**, **asyncpg**, **Alembic** (Migrations) |
| **External Integration**| Scrapers & Storage | **BeautifulSoup4**, **youtube-transcript-api**, **httpx**, **Supabase Storage** |
| **Authentication** | Security | **PyJWT** (Bearer JWT), **Passlib** (Bcrypt hashing) |
| **DevOps & Container** | Deployment | **Docker**, **Docker Compose**, **GCP Cloud Run** |
| **Testing** | Quality Assurance | **Pytest**, **Pytest-AsyncIO** |

---

## 🏗️ System Architecture & Data Flow

### High-Level System Architecture

```mermaid
graph TD
    subgraph Client Layer
        A[Mobile / Web Client]
    end

    subgraph API Gateway & Core API
        B[FastAPI Application]
        C[CORS & Exception Handlers]
        D[JWT Security & Auth Middleware]
    end

    subgraph Business Logic Services
        E[Recipe Service]
        F[Product Service Engine]
        G[Cart Service]
        H[Order Service]
    end

    subgraph AI Pipeline - LangGraph
        I[Ingestion Router]
        J[Web / YouTube Extractor]
        K[Gemini Vision / Text LLM Node]
        L[Ingredient Structurer & Normalizer]
    end

    subgraph Persistence & External
        M[(PostgreSQL DB)]
        N[Supabase Storage]
        O[Google Gemini API]
    end

    A -->|HTTP / REST| B
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    D --> H

    E --> I
    I -->|Image| K
    I -->|URL / Video| J
    J --> K
    K <-->|LangChain| O
    K --> L
    L --> M

    E <--> N
    F <--> M
    G <--> M
    H <--> M
```

---

### AI Extraction Workflow (LangGraph Engine)

```mermaid
flowchart LR
    A([Input Payload]) --> B{Source Type?}
    
    B -->|Image File| C[Supabase Upload & Gemini Vision Pro]
    B -->|Web URL| D[BS4 Scraper & Text Parser]
    B -->|YouTube Link| E[Youtube Transcript API]
    B -->|Raw Text| F[Direct Text Formatter]

    C --> G[LangGraph Processing Node]
    D --> G
    E --> G
    F --> G

    G --> H[Gemini 1.5 Flash Structured Prompt]
    H --> I{Valid JSON Output?}
    I -->|No| J[Retry / Normalization Fallback]
    J --> H
    I -->|Yes| K[Persist Recipe & RecipeIngredients]
    K --> L([Return Recipe Response])
```

---

## 🔄 Detailed User Flow

The complete lifecycle from user onboarding to automated cart checkout:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as FastAPI Backend
    participant AI as LangGraph / Gemini Engine
    participant DB as PostgreSQL Database
    participant Cart as Cart & Inventory Engine

    User->>API: 1. Signup / Login (/api/v1/auth/login)
    API-->>User: Return JWT Bearer Token

    User->>API: 2. Submit Recipe URL/Image (/api/v1/recipes/process-url)
    API->>AI: Trigger Extraction Workflow
    AI->>AI: Fetch Content, Extract Text & Query Gemini
    AI->>DB: Save Recipe & Extracted Ingredients
    API-->>User: Return Structured Recipe Response

    User->>API: 3. Discover Matched Products (/api/v1/recipes/{id}/products)
    API->>DB: Query Catalog & Match Ingredients (Confidence Threshold > 0.70)
    API-->>User: Return Matched E-Commerce Variants

    User->>API: 4. Add Selected Items to Cart (/api/v1/cart/items)
    API->>Cart: Verify Stock & Update Active Cart
    Cart->>DB: Persist CartItems
    API-->>User: Return Updated Cart State

    User->>API: 5. Checkout Order (/api/v1/orders)
    API->>Cart: Validate Available Inventory
    Cart->>DB: Create Order, Snapshot Items & Deduct Stock
    API-->>User: Return Order Confirmation & Summary
```

### User Journey Matrix

| Step | Action | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **1. Authentication** | Authenticate User | `POST /api/v1/auth/login` | Obtains a Bearer token for accessing protected routes. |
| **2. Ingestion** | Submit Content | `POST /api/v1/recipes/process-*` | Ingests recipe from image, URL, video, or text. |
| **3. Structuring** | AI Parsing | *Internal LangGraph Engine* | Extracts ingredients, quantities, units, and preparation steps. |
| **4. Discovery** | Product Matching | `POST /api/v1/recipes/{id}/products` | Finds retail product variants matching recipe ingredients. |
| **5. Selection** | Cart Management | `POST /api/v1/cart/items` | Adds chosen product variants with requested quantities to user's active cart. |
| **6. Fulfillment**| Atomic Checkout | `POST /api/v1/orders` | Converts active cart to confirmed order and deducts physical inventory. |

---

## 📊 Database Schema & Data Models

```mermaid
erDiagram
    USERS ||--o{ RECIPES : creates
    USERS ||--o{ CARTS : owns
    USERS ||--o{ ORDERS : places
    RECIPES ||--|{ RECIPE_INGREDIENTS : contains
    PRODUCTS ||--|{ PRODUCT_VARIANTS : offers
    PRODUCT_VARIANTS ||--|| INVENTORY : tracks
    CARTS ||--o{ CART_ITEMS : holds
    PRODUCT_VARIANTS ||--o{ CART_ITEMS : mapped_to
    ORDERS ||--|{ ORDER_ITEMS : includes
    PRODUCT_VARIANTS ||--o{ ORDER_ITEMS : snapshotted_in

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
    }

    RECIPES {
        uuid id PK
        uuid user_id FK
        string title
        string source_type
        string source_url
        string storage_path
        string status
    }

    RECIPE_INGREDIENTS {
        uuid id PK
        uuid recipe_id FK
        string name
        string original_text
        decimal quantity
        string unit
        string preparation
    }

    PRODUCTS {
        uuid id PK
        string name
        string brand
        string category
        jsonb metadata_json
    }

    PRODUCT_VARIANTS {
        uuid id PK
        uuid product_id FK
        string sku UK
        decimal size
        string size_unit
        decimal price
    }

    INVENTORY {
        uuid id PK
        uuid variant_id FK
        int available_quantity
        int reserved_quantity
    }

    CARTS {
        uuid id PK
        uuid user_id FK
        string status
    }

    CART_ITEMS {
        uuid id PK
        uuid cart_id FK
        uuid variant_id FK
        int quantity
    }

    ORDERS {
        uuid id PK
        uuid user_id FK
        string order_number UK
        decimal total_amount
        string status
    }

    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid variant_id FK
        string product_name_snapshot
        decimal unit_price_snapshot
        int quantity
        decimal line_total
    }
```

---

## 🔌 API Specification Directory

### 🔑 Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/signup` | Register a new user account | ❌ |
| `POST` | `/api/v1/auth/login` | Authenticate user and issue JWT access token | ❌ |
| `GET` | `/api/v1/auth/me` | Retrieve profile information for authenticated user | 🔐 |

### 🥗 Recipes (`/api/v1/recipes`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/recipes/process-image` | Upload image file to parse recipe with Gemini Vision | 🔐 |
| `POST` | `/api/v1/recipes/process-text` | Ingest raw recipe text content | 🔐 |
| `POST` | `/api/v1/recipes/process-url` | Scrape web page URL and extract structured recipe | 🔐 |
| `POST` | `/api/v1/recipes/process-video` | Extract YouTube video transcript and convert to recipe | 🔐 |
| `GET` | `/api/v1/recipes/{recipe_id}` | Fetch detailed recipe by ID with extracted ingredients | 🔐 |
| `PATCH`| `/api/v1/recipes/{recipe_id}/ingredients` | Batch update recipe ingredient details | 🔐 |

### 🛍️ Products & Matching (`/api/v1/products`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/recipes/{recipe_id}/products` | Perform AI ingredient-to-product variant matching | 🔐 |
| `GET` | `/api/v1/products/{variant_id}` | Get product variant details & current stock levels | 🔐 |

### 🛒 Cart (`/api/v1/cart`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/cart` | Retrieve user's current active cart and items | 🔐 |
| `POST` | `/api/v1/cart/items` | Add product variant to active cart | 🔐 |
| `PATCH`| `/api/v1/cart/items/{item_id}` | Update quantity of item in active cart | 🔐 |
| `DELETE`| `/api/v1/cart/items/{item_id}` | Remove item from active cart | 🔐 |

### 📦 Orders (`/api/v1/orders`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/orders` | Checkout active cart, deduct inventory & create order | 🔐 |
| `GET` | `/api/v1/orders` | List user order history | 🔐 |
| `GET` | `/api/v1/orders/{order_id}` | Retrieve specific order details by ID | 🔐 |

### 🏥 System Health (`/health`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Application health status and environment check | ❌ |

---

## ⚙️ Environment Configuration

Create a `.env` file in the root directory following `.env.example`:

```env
# Application Settings
APP_NAME="AI Recipe-to-Commerce Backend"
ENVIRONMENT="development"
DEBUG=True
PORT=8000
CONFIDENCE_THRESHOLD=0.70

# Database Connection
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/recipe_commerce"

# JWT Authentication
JWT_SECRET="your-super-secret-jwt-key"
JWT_ALGORITHM="HS256"
JWT_EXPIRATION_SECONDS=3600

# Supabase Storage Integration
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your-supabase-service-role-key"

# AI Models (Google Gemini / Vertex AI)
GEMINI_API_KEY="your-gemini-api-key"
GOOGLE_API_KEY="your-google-api-key"
VERTEX_PROJECT_ID="your-gcp-project-id"
VERTEX_LOCATION="us-central1"
VERTEX_MODEL_NAME="gemini-1.5-flash"
VERTEX_VISION_MODEL_NAME="gemini-1.5-pro"

# CORS Configuration
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Python**: 3.11+
- **PostgreSQL**: 14+
- **Docker & Docker Compose** (Optional for containerized run)

### Local Setup (Virtual Environment)

1. **Clone Repository & Navigate**
   ```bash
   git clone https://github.com/shubhamacharya02/clock_it_backend.git
   cd clock_it_backend
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set Up Database & Run Migrations**
   ```bash
   # Run Alembic migrations
   alembic upgrade head

   # Seed catalog database with sample products and inventory
   python -m scripts.seed_database
   ```

5. **Start Uvicorn Development Server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access Interactive API Docs**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Docker Setup

Run the entire backend stack effortlessly using Docker Compose:

```bash
# Build and launch application container
docker-compose up --build -d

# View container logs
docker-compose logs -f app
```

---

## 🧪 Testing & Verification

The repository contains an automated test suite using `pytest` and `pytest-asyncio`.

```bash
# Execute full test suite
pytest -v

# Run with output logging
pytest -v -s
```

---

## 🛡️ Security & Authentication

- **JWT Tokens**: Signed with `HS256` HMAC algorithms and configured expiration.
- **Password Hashing**: Salted and hashed using `Passlib` and `Bcrypt`.
- **CORS Protection**: Dynamic whitelist regex supporting trusted frontend origins (`localhost`, `127.0.0.1`, Vercel deployments).
- **Atomic Database Operations**: Prevents race conditions during inventory deductions and order creation.

---

<div align="center">
  <sub>Built with ❤️ by the ClockIt AI Engineering Team</sub>
</div>
