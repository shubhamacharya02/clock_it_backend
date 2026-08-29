# Document 14: Error Handling & System Exception Matrix

## 1. Standardized Error Response Format
All application API errors follow a strict, uniform JSON payload contract across all endpoints:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of the error.",
    "details": [
      {
        "field": "variant_id",
        "value": "SKU-AMUL-MILK-1L",
        "issue": "Requested quantity (5) exceeds available inventory (2)."
      }
    ]
  }
}
```

> [!IMPORTANT]
> **Details Array Contract**: The `details` field MUST always be present as a JSON array (`list`). If no specific field-level details exist, `details` MUST be returned as an empty array (`[]`).

---

## 2. Comprehensive System Error Mapping Matrix

| Domain | Edge Case Scenario | Status Code | Internal Error Code | Handling & Transaction Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | Missing `Authorization: Bearer` header | `401 Unauthorized` | `UNAUTHORIZED` | Reject request before router execution. |
| **Authentication** | Invalid JWT signature or corrupted token | `401 Unauthorized` | `INVALID_TOKEN` | Reject request; prompt user to re-authenticate. |
| **Authentication** | Expired JWT access token (> 3600s / 1 hr) | `401 Unauthorized` | `EXPIRED_TOKEN` | Reject request; access token lifetime is strictly 1 hour. |
| **Authentication** | Malformed or non-UUID string in `sub` claim | `401 Unauthorized` | `INVALID_TOKEN_SUB` | Validate `sub` format before DB query; reject invalid UUID. |
| **Authentication** | Inactive (`is_active=False`) or missing user | `401 Unauthorized` | `USER_INACTIVE` | Reject request; return 401. |
| **Resource Isolation**| Accessing another user's resource | `404 Not Found` | `RESOURCE_NOT_FOUND` | User-owned resources (`recipes`, `carts`, `orders`) return 404 to hide resource existence. |
| **Media Ingestion** | File MIME type not in allowlist | `400 Bad Request` | `INVALID_FILE_TYPE` | Reject before storage upload. Allowed: `image/jpeg`, `image/png`, `image/webp`. |
| **Media Ingestion** | Payload size exceeds 10MB limit | `400 Bad Request` | `FILE_TOO_LARGE` | Enforce bounded stream reading; reject if > 10,485,760 bytes. |
| **Media Ingestion** | Empty or unreadable image payload | `400 Bad Request` | `INVALID_IMAGE_PAYLOAD` | Reject before Vertex AI processing. |
| **Supabase Storage**| Storage API timeout or upload failure | `502 Bad Gateway` | `STORAGE_UPLOAD_FAILED` | Return 502 error; write no DB record. No local disk or S3/GCS fallback. |
| **Web Ingestion** | Target URL unreachable or returns error | `422 Unprocessable` | `URL_FETCH_FAILED` | Return 422 indicating webpage scraping failure. |
| **YouTube Ingestion**| Video transcript unavailable | `400 Bad Request` | `TRANSCRIPT_UNAVAILABLE` | Return 400 indicating no audio transcript found. |
| **AI Engine** | Vertex AI API downtime, timeout, or quota | `502 Bad Gateway` | `LLM_SERVICE_UNAVAILABLE` | Return 502 with retry suggestion. No silent AI provider substitution. |
| **AI Engine** | LLM output fails Pydantic schema | `502 Bad Gateway` | `LLM_STRUCTURE_ERROR` | Log raw response for debugging; return 502. |
| **AI Engine** | Ingredient confidence score < 0.70 | `200 OK` | N/A | **Expected Business State**: Return payload with `requires_confirmation: true`. |
| **Product Match** | Zero primary in-stock & zero alternatives | `200 OK` | N/A | **Expected Business State**: Return item with `status: "OUT_OF_STOCK_NO_ALTERNATIVES"`. |
| **Catalog** | Nonexistent variant ID requested | `404 Not Found` | `VARIANT_NOT_FOUND` | Public catalog item query for missing SKU returns 404. |
| **Cart** | Adding inactive variant SKU to cart | `400 Bad Request` | `VARIANT_INACTIVE` | Prevent cart item insertion. |
| **Cart** | Cart item quantity <= 0 | `400 Bad Request` | `INVALID_QUANTITY` | Quantity must be integer >= 1. |
| **Checkout** | Attempting checkout on empty cart | `400 Bad Request` | `EMPTY_CART` | Reject checkout immediately before locking inventory. |
| **Checkout** | Stock insufficient during checkout | `409 Conflict` | `INSUFFICIENT_STOCK` | Abort checkout transaction via `ROLLBACK`; return available stock details. |
| **Database** | Lock timeout, deadlock, DB failure | `500 Internal Error`| `DATABASE_TRANSACTION_ERROR`| Rollback PostgreSQL transaction cleanly; hide raw SQL details from client. |

---

## 3. Information Disclosure & Security Rules
To prevent information leakage and system fingerprinting:
1. **No Stack Trace Exposure**: Production API responses MUST NEVER include Python tracebacks, exception class names, or internal file paths.
2. **No Secret Leakage**: Database credentials, Supabase API keys, JWT secret keys, and GCP service account keys MUST NEVER be exposed in error responses.
3. **No Internal SQL Exposure**: Database errors MUST NOT leak raw PostgreSQL error messages, table structures, column names, or failing SQL queries to the client.
4. **Server-Side Logging**: Full tracebacks and diagnostic information MUST be logged server-side via structured logging for debugging.

---

## 4. Global Exception Handler Implementation Specification

```python
# app/main.py (Global Exception Handlers)
from typing import List, Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: List[Dict[str, Any]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []

# 1. Custom Application Exception Handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

# 2. FastAPI Request Validation Error Handler (Normalizes Pydantic Errors)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_details = []
    for err in exc.errors():
        field_path = " -> ".join([str(loc) for loc in err.get("loc", [])])
        formatted_details.append({
            "field": field_path,
            "issue": err.get("msg", "Invalid field value")
        })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload validation failed.",
                "details": formatted_details
            }
        }
    )

# 3. Global Unhandled Internal Exception Handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log raw exception server-side here
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": []
            }
        }
    )
```
