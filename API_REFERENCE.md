# Customify Core API - Complete API Reference

**Version:** 1.0.0  
**Base URL:** `https://api.customify.app`  
**Development:** `http://localhost:8000`

---

## Table of Contents

- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Endpoints](#endpoints)
  - [Health](#health)
  - [Authentication](#authentication-endpoints)
  - [Users](#users)
  - [Designs](#designs)
  - [Subscriptions](#subscriptions)
  - [System](#system)

---

## Authentication

### JWT Bearer Token

All authenticated endpoints require a JWT token in the `Authorization` header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Obtaining a Token

1. **Register** a new user (`POST /api/v1/auth/register`)
2. **Login** with credentials (`POST /api/v1/auth/login`)
3. Use the returned `access_token` in subsequent requests

### Token Properties

- **Expiration:** 7 days (10,080 minutes)
- **Algorithm:** HS256
- **Claims:** `sub` (user_id), `exp` (expiration), `iat` (issued at)

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Request accepted (processing async) |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate email) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Common Error Examples

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

**409 Conflict:**
```json
{
  "detail": "Email user@example.com already registered"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Rate Limiting

**Current Limits:**
- **Authenticated users:** 100 requests per minute per user
- **Unauthenticated:** 20 requests per minute per IP

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673780400
```

**Exceeded Response:**
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Rate limit exceeded. Max 100 requests per 60s"
}
```

---

## Pagination

### Query Parameters

- `skip` (integer, default: 0): Number of records to skip
- `limit` (integer, default: 20, max: 100): Number of records to return

### Response Format
```json
{
  "designs": [...],
  "total": 42,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

### Example Request
```http
GET /api/v1/designs?skip=20&limit=20
```

---

## Endpoints

---

### Health

#### GET /health

**Description:** Health check endpoint for monitoring.

**Authentication:** None

**Response:** 200 OK
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  },
  "workers": 2
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### Authentication Endpoints

#### POST /api/v1/auth/register

**Description:** Register a new user account.

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Validation Rules:**
- `email`: Valid email format
- `password`: 8-100 characters, must contain letter and number
- `full_name`: 1-255 characters

**Response:** 201 Created
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": null,
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:00:00Z",
  "last_login": null
}
```

**Errors:**
- `409`: Email already registered
- `422`: Validation error

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe"
  }'
```

---

#### POST /api/v1/auth/login

**Description:** Login with credentials and receive JWT token.

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "avatar_url": null,
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-15T10:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

**Errors:**
- `401`: Invalid credentials
- `403`: User account inactive

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

**Save Token:**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePassword123!"}' \
  | jq -r '.access_token')
```

---

#### GET /api/v1/auth/me

**Description:** Get current authenticated user profile.

**Authentication:** Required

**Response:** 200 OK
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": null,
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:00:00Z",
  "last_login": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `401`: Invalid or expired token
- `403`: User account inactive

**Example:**
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### Designs

#### POST /api/v1/designs

**Description:** Create a new design. Design rendering happens asynchronously.

**Authentication:** Required

**Request Body:**
```json
{
  "product_type": "t-shirt",
  "design_data": {
    "text": "Hello World",
    "font": "Bebas-Bold",
    "color": "#FF0000"
  },
  "use_ai_suggestions": false
}
```

**Product Types:**
- `t-shirt`
- `mug`
- `poster`
- `hoodie`
- `tote-bag`

**Available Fonts:**
- `Bebas-Bold`
- `Montserrat-Regular`
- `Montserrat-Bold`
- `Pacifico-Regular`
- `Roboto-Regular`

**Color Format:** Hex color code (`#RRGGBB`)

**Response:** 201 Created
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_type": "t-shirt",
  "design_data": {
    "text": "Hello World",
    "font": "Bebas-Bold",
    "color": "#FF0000"
  },
  "status": "draft",
  "preview_url": null,
  "thumbnail_url": null,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Status Flow:**
1. `draft` - Initial state after creation
2. `rendering` - Background worker processing
3. `published` - Rendering complete, preview available
4. `failed` - Rendering failed

**Errors:**
- `400`: Invalid design data
- `402`: Quota exceeded (free plan limit reached)
- `422`: Validation error

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/designs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_type": "t-shirt",
    "design_data": {
      "text": "Hello World",
      "font": "Bebas-Bold",
      "color": "#FF0000"
    }
  }'
```

---

#### GET /api/v1/designs

**Description:** List all designs for authenticated user with pagination.

**Authentication:** Required

**Query Parameters:**
- `skip` (integer, default: 0): Offset
- `limit` (integer, default: 20, max: 100): Page size

**Response:** 200 OK
```json
{
  "designs": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "product_type": "t-shirt",
      "design_data": {
        "text": "Hello World",
        "font": "Bebas-Bold",
        "color": "#FF0000"
      },
      "status": "published",
      "preview_url": "https://cdn.customify.app/designs/123.../preview.png",
      "thumbnail_url": "https://cdn.customify.app/designs/123.../thumbnail.png",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:30Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20,
  "has_more": false
}
```

**Example:**
```bash
# First page
curl http://localhost:8000/api/v1/designs \
  -H "Authorization: Bearer $TOKEN"

# Second page
curl "http://localhost:8000/api/v1/designs?skip=20&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

---

#### GET /api/v1/designs/{design_id}

**Description:** Get a specific design by ID.

**Authentication:** Required

**Path Parameters:**
- `design_id` (string, UUID): Design ID

**Response:** 200 OK
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_type": "t-shirt",
  "design_data": {
    "text": "Hello World",
    "font": "Bebas-Bold",
    "color": "#FF0000"
  },
  "status": "published",
  "preview_url": "https://cdn.customify.app/designs/123.../preview.png",
  "thumbnail_url": "https://cdn.customify.app/designs/123.../thumbnail.png",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:30Z"
}
```

**Errors:**
- `404`: Design not found
- `403`: Design doesn't belong to user

**Example:**
```bash
curl http://localhost:8000/api/v1/designs/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer $TOKEN"
```

---

### Subscriptions

**Note:** Subscription endpoints are planned for future releases.

---

### System

#### GET /api/v1/system/worker-status

**Description:** Check Celery worker status (admin only).

**Authentication:** Required

**Response:** 200 OK
```json
{
  "workers": {
    "worker@hostname": {
      "total": {
        "tasks.completed": 42,
        "tasks.failed": 1
      }
    }
  },
  "active_tasks": {
    "worker@hostname": []
  },
  "registered_tasks": [
    "render_design_preview",
    "send_email",
    "debug_task"
  ],
  "broker": "redis://localhost:6379/0"
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/system/worker-status \
  -H "Authorization: Bearer $TOKEN"
```

---

## Webhooks

**Coming Soon:**
- Shopify order webhook
- WooCommerce order webhook
- Stripe payment webhook

---

## SDK Examples

### Python
```python
import httpx

BASE_URL = "http://localhost:8000"

# Register
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }
    )
    user = response.json()

    # Login
    response = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    )
    token = response.json()["access_token"]

    # Create design
    response = await client.post(
        f"{BASE_URL}/api/v1/designs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_type": "t-shirt",
            "design_data": {
                "text": "Hello World",
                "font": "Bebas-Bold",
                "color": "#FF0000"
            }
        }
    )
    design = response.json()
    print(f"Design created: {design['id']}")
```

### JavaScript
```javascript
const BASE_URL = 'http://localhost:8000';

// Register
const registerResponse = await fetch(`${BASE_URL}/api/v1/auth/register`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!',
    full_name: 'John Doe'
  })
});
const user = await registerResponse.json();

// Login
const loginResponse = await fetch(`${BASE_URL}/api/v1/auth/login`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!'
  })
});
const {access_token} = await loginResponse.json();

// Create design
const designResponse = await fetch(`${BASE_URL}/api/v1/designs`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    product_type: 't-shirt',
    design_data: {
      text: 'Hello World',
      font: 'Bebas-Bold',
      color: '#FF0000'
    }
  })
});
const design = await designResponse.json();
console.log('Design created:', design.id);
```

---

## Postman Collection

Import this collection to Postman:

[Download Postman Collection](https://api.customify.app/postman-collection.json)

---

## Support

- **API Status:** https://status.customify.app
- **Documentation:** https://docs.customify.app
- **Support:** support@customify.app