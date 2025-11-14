📋 Lista Completa de Desarrollo - 01-core-api
Componente: Core API (Backend FastAPI)
Orden de implementación: Bottom-up (Database → Domain → Application → Presentation)

🎯 Resumen Ejecutivo
Total de módulos: 7 módulos principales
Total de endpoints: 45 endpoints REST
Total de use cases: 32 use cases


📦 MÓDULO 1: Authentication & Authorization

✓ UC-AUTH-01: Register User
  Input: email, password, full_name
  Output: User (sin token, debe hacer login)
  Business Rules:
  - Email único
  - Password min 8 chars, debe tener número y letra
  - Email lowercase
  - Auto-crear subscription Free

✓ UC-AUTH-02: Login User
  Input: email, password
  Output: access_token, refresh_token, user
  Business Rules:
  - Verificar password
  - Usuario debe estar activo
  - Actualizar last_login
  - Generar JWT (7 días expiry)

✓ UC-AUTH-03: Refresh Token
  Input: refresh_token
  Output: new_access_token
  Business Rules:
  - Verificar refresh_token válido
  - Usuario sigue activo
  - Generar nuevo access_token

✓ UC-AUTH-04: Logout
  Input: access_token
  Output: success
  Business Rules:
  - Blacklist token en Redis
  - TTL = tiempo restante del token

✓ UC-AUTH-05: Request Password Reset
  Input: email
  Output: success (siempre, aunque email no exista - security)
  Business Rules:
  - Generar reset token (UUID)
  - Store en Redis (TTL 1h)
  - Enviar email con link

✓ UC-AUTH-06: Reset Password
  Input: reset_token, new_password
  Output: success
  Business Rules:
  - Verificar token en Redis
  - Validar nuevo password
  - Hash y actualizar
  - Invalidar token

1.2 Endpoints API

POST   /api/v1/auth/register
  Body: {email, password, full_name}
  Response: 201 {id, email, full_name, created_at}

POST   /api/v1/auth/login
  Body: {email, password}
  Response: 200 {access_token, refresh_token, user}

POST   /api/v1/auth/refresh
  Body: {refresh_token}
  Response: 200 {access_token}

POST   /api/v1/auth/logout
  Headers: Authorization: Bearer {token}
  Response: 200 {message: "Logged out"}

POST   /api/v1/auth/password-reset/request
  Body: {email}
  Response: 200 {message: "If email exists, reset link sent"}

POST   /api/v1/auth/password-reset/confirm
  Body: {reset_token, new_password}
  Response: 200 {message: "Password updated"}

GET    /api/v1/auth/me
  Headers: Authorization: Bearer {token}
  Response: 200 {id, email, full_name, subscription, ...}


1.3 Entidades Domain

# app/domain/entities/user.py

class User:
    id: str
    email: str
    password_hash: str
    full_name: str
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    @staticmethod
    def create(email: str, password: str, full_name: str) -> User
    
    def verify_password(self, password: str) -> bool
    def update_password(self, new_password: str)
    def mark_login(self)
    
# app/domain/repositories/user_repository.py

class IUserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]
    
    @abstractmethod
    async def update(self, user: User) -> User
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool
    
    @abstractmethod
    async def exists_email(self, email: str) -> bool
```

---

## 📦 MÓDULO 2: User Management

### 2.1 Casos de Uso
```
✓ UC-USER-01: Get User Profile
  Input: user_id (from JWT)
  Output: User (con subscription info)
  Business Rules:
  - Usuario debe estar activo

✓ UC-USER-02: Update User Profile
  Input: user_id, updates (full_name, avatar_url)
  Output: User actualizado
  Business Rules:
  - No puede cambiar email (por ahora)
  - Avatar URL debe ser válida

✓ UC-USER-03: Upload Avatar
  Input: user_id, image_file
  Output: avatar_url
  Business Rules:
  - Max 5MB
  - Formatos: JPG, PNG
  - Resize a 300x300px
  - Upload a S3

✓ UC-USER-04: Delete Account (Soft Delete)
  Input: user_id, password (confirmación)
  Output: success
  Business Rules:
  - Verificar password
  - Soft delete (is_deleted = true)
  - Cancel subscription activa
  - Anonymize data (GDPR)
```

### 2.2 Endpoints API
```
GET    /api/v1/users/me
  Headers: Authorization: Bearer {token}
  Response: 200 {id, email, full_name, avatar_url, subscription, stats}

PUT    /api/v1/users/me
  Headers: Authorization: Bearer {token}
  Body: {full_name?, avatar_url?}
  Response: 200 {user updated}

POST   /api/v1/users/me/avatar
  Headers: Authorization: Bearer {token}
  Body: multipart/form-data {file}
  Response: 200 {avatar_url}

DELETE /api/v1/users/me
  Headers: Authorization: Bearer {token}
  Body: {password}
  Response: 200 {message: "Account deleted"}
```

---

## 📦 MÓDULO 3: Designs Management

### 3.1 Casos de Uso
```
✓ UC-DESIGN-01: Create Design
  Input: user_id, product_type, design_data, use_ai_suggestions
  Output: Design (status: draft)
  Business Rules:
  - Check subscription quota (designs_this_month < limit)
  - Validate design_data (text, font, color)
  - If use_ai: llamar AI service (async)
  - Create design entity
  - Persist to DB
  - Queue render job (Celery)
  - Increment subscription counter
  
✓ UC-DESIGN-02: List Designs
  Input: user_id, filters (product_type?, status?), pagination (skip, limit)
  Output: List[Design], total, has_more
  Business Rules:
  - Solo designs del user
  - Excluir is_deleted
  - Order by created_at DESC
  - Default limit: 20

✓ UC-DESIGN-03: Get Design by ID
  Input: user_id, design_id
  Output: Design
  Business Rules:
  - Verificar ownership (design.user_id == user_id)
  - Excluir is_deleted

✓ UC-DESIGN-04: Update Design
  Input: user_id, design_id, updates (design_data)
  Output: Design actualizado
  Business Rules:
  - Verificar ownership
  - Solo si status = draft o published
  - Si cambia design_data: re-queue render job
  - Status → rendering

✓ UC-DESIGN-05: Delete Design (Soft Delete)
  Input: user_id, design_id
  Output: success
  Business Rules:
  - Verificar ownership
  - Soft delete (is_deleted = true)
  - Decrement subscription counter

✓ UC-DESIGN-06: Duplicate Design
  Input: user_id, design_id
  Output: New Design (copy)
  Business Rules:
  - Check quota
  - Copy design_data
  - New ID, status = draft
  - Increment counter

✓ UC-DESIGN-07: Get Design Stats
  Input: user_id, design_id
  Output: Stats (views, conversions, revenue)
  Business Rules:
  - Solo si tiene orders asociados
  - Calcular desde orders table
```

### 3.2 Endpoints API
```
POST   /api/v1/designs
  Headers: Authorization: Bearer {token}
  Body: {product_type, design_data, use_ai_suggestions?}
  Response: 201 {design}
  
GET    /api/v1/designs
  Headers: Authorization: Bearer {token}
  Query: ?product_type=t-shirt&status=published&skip=0&limit=20
  Response: 200 {designs: [], total, skip, limit, has_more}

GET    /api/v1/designs/{design_id}
  Headers: Authorization: Bearer {token}
  Response: 200 {design}

PUT    /api/v1/designs/{design_id}
  Headers: Authorization: Bearer {token}
  Body: {design_data}
  Response: 200 {design updated}

DELETE /api/v1/designs/{design_id}
  Headers: Authorization: Bearer {token}
  Response: 200 {message: "Design deleted"}

POST   /api/v1/designs/{design_id}/duplicate
  Headers: Authorization: Bearer {token}
  Response: 201 {new_design}

GET    /api/v1/designs/{design_id}/stats
  Headers: Authorization: Bearer {token}
  Response: 200 {views, conversions, revenue}

3.3 Entidades Domain
# app/domain/entities/design.py

class Design:
    id: str
    user_id: str
    product_type: str  # t-shirt, mug, poster, hoodie, tote-bag
    design_data: dict  # {text, font, color, position, rotation, scale}
    status: DesignStatus  # draft, rendering, published, failed
    preview_url: Optional[str]
    thumbnail_url: Optional[str]
    ai_suggestions: Optional[List[dict]]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    @staticmethod
    def create(user_id, product_type, design_data) -> Design
    
    def validate(self) -> None
    def update_data(self, new_data: dict)
    def mark_rendered(self, preview_url: str)
    def mark_failed(self, error: str)

class DesignStatus(str, Enum):
    DRAFT = "draft"
    RENDERING = "rendering"
    PUBLISHED = "published"
    FAILED = "failed"


3.4 Repository Interface
# app/domain/repositories/design_repository.py

class IDesignRepository(ABC):
    @abstractmethod
    async def create(self, design: Design) -> Design
    
    @abstractmethod
    async def get_by_id(self, design_id: str) -> Optional[Design]
    
    @abstractmethod
    async def get_by_user(
        self, 
        user_id: str, 
        filters: dict,
        skip: int, 
        limit: int
    ) -> Tuple[List[Design], int]
    
    @abstractmethod
    async def update(self, design: Design) -> Design
    
    @abstractmethod
    async def delete(self, design_id: str) -> bool
    
    @abstractmethod
    async def count_by_user(self, user_id: str) -> int
```

---

## 📦 MÓDULO 4: Subscriptions Management

### 4.1 Casos de Uso
```
✓ UC-SUB-01: Get User Subscription
  Input: user_id
  Output: Subscription (con usage info)
  Business Rules:
  - Incluir usage este mes
  - Incluir límites del plan
  - Días restantes del periodo

✓ UC-SUB-02: Check Quota Available
  Input: user_id
  Output: bool (has_quota)
  Business Rules:
  - designs_this_month < designs_limit
  - Subscription activa

✓ UC-SUB-03: Increment Usage Counter
  Input: user_id
  Output: updated_subscription
  Business Rules:
  - designs_this_month += 1
  - Used by CreateDesignUseCase

✓ UC-SUB-04: Decrement Usage Counter
  Input: user_id
  Output: updated_subscription
  Business Rules:
  - designs_this_month -= 1
  - Used by DeleteDesignUseCase

✓ UC-SUB-05: Activate Subscription (from Stripe)
  Input: user_id, plan, stripe_subscription_id
  Output: Subscription activated
  Business Rules:
  - Update plan
  - status = active
  - Set period dates
  - Reset counter

✓ UC-SUB-06: Cancel Subscription
  Input: user_id
  Output: Subscription cancelled
  Business Rules:
  - status = canceled
  - Still active hasta end of period
  - Cancel en Stripe también

✓ UC-SUB-07: Reset Monthly Usage (Cron Job)
  Input: None (runs monthly)
  Output: All subscriptions reset
  Business Rules:
  - designs_this_month = 0
  - current_period_start/end updated
  - Run first day of month
```

### 4.2 Endpoints API
```
GET    /api/v1/subscriptions/me
  Headers: Authorization: Bearer {token}
  Response: 200 {
    plan, 
    status, 
    designs_this_month, 
    designs_limit,
    current_period_start,
    current_period_end,
    days_remaining
  }

GET    /api/v1/subscriptions/usage
  Headers: Authorization: Bearer {token}
  Response: 200 {
    designs_used, 
    designs_remaining, 
    percentage_used,
    quota_available: bool
  }

POST   /api/v1/subscriptions/cancel
  Headers: Authorization: Bearer {token}
  Response: 200 {message: "Subscription will cancel at period end"}

4.3 Entidades Domain
# app/domain/entities/subscription.py

class Subscription:
    id: str
    user_id: str
    plan: SubscriptionPlan  # free, starter, professional, enterprise
    status: SubscriptionStatus  # active, canceled, past_due, trialing
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    designs_this_month: int
    designs_limit: int  # Based on plan
    current_period_start: datetime
    current_period_end: datetime
    created_at: datetime
    updated_at: datetime
    
    def has_quota(self) -> bool
    def increment_usage(self)
    def decrement_usage(self)
    def reset_monthly_usage(self)
    def activate(self, plan: str, stripe_subscription_id: str)
    def cancel(self)
    def is_active(self) -> bool

class SubscriptionPlan(str, Enum):
    FREE = "free"  # 10 designs/mes
    STARTER = "starter"  # 100 designs/mes
    PROFESSIONAL = "professional"  # 500 designs/mes
    ENTERPRISE = "enterprise"  # Unlimited

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
4.4 Repository Interface

# app/domain/repositories/subscription_repository.py
class ISubscriptionRepository(ABC):
    @abstractmethod
    async def create(self, subscription: Subscription) -> Subscription
    
    @abstractmethod
    async def get_by_user(self, user_id: str) -> Optional[Subscription]
    
    @abstractmethod
    async def get_by_stripe_subscription_id(
        self, 
        stripe_subscription_id: str
    ) -> Optional[Subscription]
    
    @abstractmethod
    async def update(self, subscription: Subscription) -> Subscription
    
    @abstractmethod
    async def get_all_active(self) -> List[Subscription]
```

---

## 📦 MÓDULO 5: Orders Management

### 5.1 Casos de Uso
```
✓ UC-ORDER-01: Create Order (from Shopify webhook)
  Input: external_order_id, design_id, platform, order_data
  Output: Order (status: pending)
  Business Rules:
  - Verificar design existe
  - platform: shopify, woocommerce, manual
  - Queue PDF generation job
  - Notify merchant (email)

✓ UC-ORDER-02: List Orders
  Input: user_id, filters, pagination
  Output: List[Order], total
  Business Rules:
  - Solo orders del user
  - Order by created_at DESC

✓ UC-ORDER-03: Get Order by ID
  Input: user_id, order_id
  Output: Order
  Business Rules:
  - Verificar ownership
  - Include design info

✓ UC-ORDER-04: Update Order Status
  Input: order_id, status (processing, completed, failed)
  Output: Order updated
  Business Rules:
  - Status progression:
    pending → processing → completed
    pending → failed

✓ UC-ORDER-05: Regenerate PDF
  Input: user_id, order_id
  Output: Order (status: processing)
  Business Rules:
  - Verificar ownership
  - Queue PDF generation again
  - Status → processing
```

### 5.2 Endpoints API
```
POST   /api/v1/orders (Internal only, no public endpoint)
  Used by: Shopify webhook handler
  
GET    /api/v1/orders
  Headers: Authorization: Bearer {token}
  Query: ?status=completed&skip=0&limit=20
  Response: 200 {orders: [], total}

GET    /api/v1/orders/{order_id}
  Headers: Authorization: Bearer {token}
  Response: 200 {order with design info}

POST   /api/v1/orders/{order_id}/regenerate-pdf
  Headers: Authorization: Bearer {token}
  Response: 200 {message: "PDF generation queued"}
5.3 Entidades Domain

# app/domain/entities/order.py

class Order:
    id: str
    user_id: str
    design_id: str
    external_order_id: str  # Shopify order ID
    platform: OrderPlatform  # shopify, woocommerce, manual
    pdf_url: Optional[str]
    status: OrderStatus  # pending, processing, completed, failed
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    
    @staticmethod
    def create(
        user_id: str,
        design_id: str,
        external_order_id: str,
        platform: str
    ) -> Order
    
    def mark_processing(self)
    def mark_completed(self, pdf_url: str)
    def mark_failed(self, error: str)

class OrderPlatform(str, Enum):
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MANUAL = "manual"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
5.4 Repository Interface

# app/domain/repositories/order_repository.py

class IOrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order
    
    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]
    
    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        filters: dict,
        skip: int,
        limit: int
    ) -> Tuple[List[Order], int]
    
    @abstractmethod
    async def get_by_external_id(
        self,
        external_order_id: str,
        platform: str
    ) -> Optional[Order]
    
    @abstractmethod
    async def update(self, order: Order) -> Order
```

---

## 📦 MÓDULO 6: Analytics

### 6.1 Casos de Uso
```
✓ UC-ANALYTICS-01: Get Dashboard Summary
  Input: user_id, date_range (last_7_days, last_30_days, all_time)
  Output: Summary stats
  Business Rules:
  - Total designs created
  - Total orders
  - Total revenue (if available)
  - Conversion rate (orders / designs)

✓ UC-ANALYTICS-02: Get Designs Over Time
  Input: user_id, date_range
  Output: Time series data
  Business Rules:
  - Group by day
  - Count designs created per day

✓ UC-ANALYTICS-03: Get Popular Products
  Input: user_id
  Output: Top 5 product types
  Business Rules:
  - Count designs por product_type
  - Order by count DESC

✓ UC-ANALYTICS-04: Get Conversion Funnel
  Input: user_id
  Output: Funnel data
  Business Rules:
  - Designs created
  - Designs with orders
  - Orders completed
  - Calculate percentages
```

### 6.2 Endpoints API
```
GET    /api/v1/analytics/summary
  Headers: Authorization: Bearer {token}
  Query: ?date_range=last_30_days
  Response: 200 {
    total_designs,
    total_orders,
    total_revenue,
    conversion_rate,
    designs_this_month,
    compared_to_last_month: {change_percentage}
  }

GET    /api/v1/analytics/designs-over-time
  Headers: Authorization: Bearer {token}
  Query: ?date_range=last_30_days
  Response: 200 {
    data: [{date, count}, ...],
    trend: "up" | "down" | "stable"
  }

GET    /api/v1/analytics/popular-products
  Headers: Authorization: Bearer {token}
  Response: 200 {
    products: [
      {product_type: "t-shirt", count: 45, percentage: 60},
      ...
    ]
  }

GET    /api/v1/analytics/conversion-funnel
  Headers: Authorization: Bearer {token}
  Response: 200 {
    stages: [
      {name: "Designs Created", count: 100, percentage: 100},
      {name: "Designs with Orders", count: 30, percentage: 30},
      {name: "Orders Completed", count: 28, percentage: 28}
    ]
  }
```

---

## 📦 MÓDULO 7: AI Suggestions (Integration)

### 7.1 Casos de Uso
```
✓ UC-AI-01: Get Design Suggestions
  Input: user_id, product_type, occasion?, style?, user_text?
  Output: List[Suggestion] (5 suggestions)
  Business Rules:
  - Check cache first (Redis, key=hash(params))
  - If cache miss: call OpenAI
  - Cache result (TTL 24h)
  - Log usage (track cost)

✓ UC-AI-02: Optimize Text
  Input: user_id, text, context
  Output: optimized_text
  Business Rules:
  - Max 100 chars input
  - Return improved version
  - Cache result
```

### 7.2 Endpoints API
```
POST   /api/v1/ai/suggest-designs
  Headers: Authorization: Bearer {token}
  Body: {
    product_type: "t-shirt",
    occasion?: "birthday",
    style?: "modern",
    user_text?: "Happy Birthday"
  }
  Response: 200 {
    suggestions: [
      {
        text_content: "Happy Birthday!",
        font: "Bebas-Bold",
        colors: ["#FF69B4", "#FFFFFF"],
        layout: "centered",
        reasoning: "Bold colors work well..."
      },
      ... (5 total)
    ],
    cached: bool
  }

POST   /api/v1/ai/optimize-text
  Headers: Authorization: Bearer {token}
  Body: {text: "hppy bday", context: "birthday"}
  Response: 200 {
    original: "hppy bday",
    optimized: "Happy Birthday",
    improvements: ["Fixed spelling", "Capitalized"]
  }
```

---

## 📦 MÓDULO ADICIONAL: File Uploads

### 8.1 Casos de Uso
```
✓ UC-UPLOAD-01: Get Presigned Upload URL
  Input: user_id, filename, content_type
  Output: presigned_url, key
  Business Rules:
  - Generar unique key (UUID)
  - Presigned URL valid 15 min
  - Max file size: 5MB

✓ UC-UPLOAD-02: Confirm Upload
  Input: user_id, key
  Output: public_url (CloudFront)
  Business Rules:
  - Verificar file existe en S3
  - Return CDN URL
```

### 8.2 Endpoints API
```
POST   /api/v1/uploads/presigned-url
  Headers: Authorization: Bearer {token}
  Body: {filename: "avatar.jpg", content_type: "image/jpeg"}
  Response: 200 {
    upload_url: "https://s3.amazonaws.com/...",
    key: "uploads/users/{user_id}/...",
    expires_in: 900
  }

POST   /api/v1/uploads/complete
  Headers: Authorization: Bearer {token}
  Body: {key: "uploads/users/{user_id}/..."}
  Response: 200 {
    public_url: "https://cdn.customify.app/..."
  }
```

---

## 📋 Resumen Completo de Endpoints

### Total: 45 Endpoints

**Authentication (7):**
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- POST /api/v1/auth/password-reset/request
- POST /api/v1/auth/password-reset/confirm
- GET /api/v1/auth/me

**Users (4):**
- GET /api/v1/users/me
- PUT /api/v1/users/me
- POST /api/v1/users/me/avatar
- DELETE /api/v1/users/me

**Designs (7):**
- POST /api/v1/designs
- GET /api/v1/designs
- GET /api/v1/designs/{id}
- PUT /api/v1/designs/{id}
- DELETE /api/v1/designs/{id}
- POST /api/v1/designs/{id}/duplicate
- GET /api/v1/designs/{id}/stats

**Subscriptions (3):**
- GET /api/v1/subscriptions/me
- GET /api/v1/subscriptions/usage
- POST /api/v1/subscriptions/cancel

**Orders (4):**
- POST /api/v1/orders (internal)
- GET /api/v1/orders
- GET /api/v1/orders/{id}
- POST /api/v1/orders/{id}/regenerate-pdf

**Analytics (4):**
- GET /api/v1/analytics/summary
- GET /api/v1/analytics/designs-over-time
- GET /api/v1/analytics/popular-products
- GET /api/v1/analytics/conversion-funnel

**AI (2):**
- POST /api/v1/ai/suggest-designs
- POST /api/v1/ai/optimize-text

**Uploads (2):**
- POST /api/v1/uploads/presigned-url
- POST /api/v1/uploads/complete

**Health (1):**
- GET /health

**Shopify (3 - Módulo 3):**
- GET /api/v1/shopify/install
- GET /api/v1/shopify/callback
- POST /api/v1/shopify/webhooks/orders-create

**Stripe (2 - Módulo 3):**
- POST /api/v1/billing/checkout
- POST /api/v1/stripe/webhooks

**Docs (2 - Auto-generated):**
- GET /docs (Swagger UI)
- GET /redoc (ReDoc)

---

## 🗂️ Estructura de Archivos Completa
```
01-core-api/
├── app/
│   ├── main.py (FastAPI app)
│   ├── config.py (Settings, env vars)
│   │
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── user.py (User)
│   │   │   ├── design.py (Design)
│   │   │   ├── subscription.py (Subscription)
│   │   │   └── order.py (Order)
│   │   │
│   │   ├── repositories/
│   │   │   ├── user_repository.py (IUserRepository)
│   │   │   ├── design_repository.py (IDesignRepository)
│   │   │   ├── subscription_repository.py (ISubscriptionRepository)
│   │   │   └── order_repository.py (IOrderRepository)
│   │   │
│   │   ├── value_objects/
│   │   │   └── email.py (Email)
│   │   │
│   │   ├── exceptions/
│   │   │   ├── auth_exceptions.py
│   │   │   ├── design_exceptions.py
│   │   │   └── subscription_exceptions.py
│   │   │
│   │   └── services/
│   │       └── quota_checker.py (QuotaChecker)
│   │
│   ├── application/
│   │   └── use_cases/
│   │       ├── auth/
│   │       │   ├── register_user.py
│   │       │   ├── login_user.py
│   │       │   ├── refresh_token.py
│   │       │   ├── logout_user.py
│   │       │   ├── request_password_reset.py
│   │       │   └── reset_password.py
│   │       │
│   │       ├── users/
│   │       │   ├── get_user_profile.py
│   │       │   ├── update_user_profile.py
│   │       │   ├── upload_avatar.py
│   │       │   └── delete_account.py
│   │       │
│   │       ├── designs/
│   │       │   ├── create_design.py
│   │       │   ├── list_designs.py
│   │       │   ├── get_design.py
│   │       │   ├── update_design.py
│   │       │   ├── delete_design.py
│   │       │   ├── duplicate_design.py
│   │       │   └── get_design_stats.py
│   │       │
│   │       ├── subscriptions/
│   │       │   ├── get_subscription.py
│   │       │   ├── check_quota.py
│   │       │   ├── activate_subscription.py
│   │       │   ├── cancel_subscription.py
│   │       │   └── reset_monthly_usage.py
│   │       │
│   │       ├── orders/
│   │       │   ├── create_order.py
│   │       │   ├── list_orders.py
│   │       │   ├── get_order.py
│   │       │   └── regenerate_pdf.py
│   │       │
│   │       ├── analytics/
│   │       │   ├── get_dashboard_summary.py
│   │       │   ├── get_designs_over_time.py
│   │       │   ├── get_popular_products.py
│   │       │   └── get_conversion_funnel.py
│   │       │
│   │       └── ai/
│   │           ├── get_design_suggestions.py
│   │           └── optimize_text.py
│   │
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── session.py (async engine, session factory)
│   │   │   │
│   │   │   ├── models/
│   │   │   │   ├── user_model.py (SQLAlchemy UserModel)
│   │   │   │   ├── design_model.py
│   │   │   │   ├── subscription_model.py
│   │   │   │   └── order_model.py
│   │   │   │
│   │   │   └── repositories/
│   │   │       ├── user_repo_impl.py (IUserRepository impl)
│   │   │       ├── design_repo_impl.py
│   │   │       ├── subscription_repo_impl.py
│   │   │       └── order_repo_impl.py
│   │   │
│   │   ├── cache/
│   │   │   ├── redis_client.py (async Redis wrapper)
│   │   │   ├── cache_service.py (@cached decorator)
│   │   │   ├── rate_limiter.py (sliding window)
│   │   │   └── session_manager.py (JWT blacklist)
│   │   │
│   │   ├── storage/
│   │   │   ├── s3_client.py (async S3 wrapper)
│   │   │   └── image_optimizer.py (PIL optimization)
│   │   │
│   │   ├── ai/
│   │   │   ├── openai_client.py (GPT-4 suggestions)
│   │   │   └── pinecone_client.py (vector search)
│   │   │
│   │   ├── integrations/
│   │   │   ├── shopify/
│   │   │   │   ├── oauth.py
│   │   │   │   ├── shopify_client.py
│   │   │   │   └── webhooks.py
│   │   │   │
│   │   │   └── stripe/
│   │   │       ├── stripe_client.py
│   │   │       └── webhooks.py
│   │   │
│   │   └── email/
│   │       ├── ses_client.py (AWS SES)
│   │       └── templates/
│   │           ├── welcome_email.html
│   │           └── password_reset.html
│   │
│   ├── presentation/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py (main API router)
│   │   │       │
│   │   │       └── endpoints/
│   │   │           ├── auth.py
│   │   │           ├── users.py
│   │   │           ├── designs.py
│   │   │           ├── subscriptions.py
│   │   │           ├── orders.py
│   │   │           ├── analytics.py
│   │   │           ├── ai.py
│   │   │           ├── uploads.py
│   │   │           ├── shopify.py
│   │   │           ├── shopify_webhooks.py
│   │   │           ├── billing.py
│   │   │           └── stripe_webhooks.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth_schema.py (Pydantic schemas)
│   │   │   ├── user_schema.py
│   │   │   ├── design_schema.py
│   │   │   ├── subscription_schema.py
│   │   │   ├── order_schema.py
│   │   │   ├── analytics_schema.py
│   │   │   └── ai_schema.py
│   │   │
│   │   ├── middleware/
│   │   │   ├── error_handler.py (global error handler)
│   │   │   ├── logging_middleware.py (structured logs)
│   │   │   └── rate_limit_middleware.py
│   │   │
│   │   └── dependencies/
│   │       ├── auth.py (get_current_user)
│   │       ├── database.py (get_db_session)
│   │       └── repositories.py (DI for repositories)
│   │
│   └── shared/
│       └── utils/
│           ├── security.py (hash, JWT)
│           ├── logger.py (structured logging)
│           ├── validators.py (common validators)
│           └── metrics.py (CloudWatch metrics)
│
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_indexes.py
│   │   └── 003_add_shopify_stores.py
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_user.py
│   │   │   ├── test_design.py
│   │   │   └── test_subscription.py
│   │   │
│   │   └── application/
│   │       ├── test_register_user.py
│   │       ├── test_create_design.py
│   │       └── test_check_quota.py
│   │
│   ├── integration/
│   │   ├── database/
│   │   │   └── test_repositories.py
│   │   │
│   │   └── api/
│   │       ├── test_auth_endpoints.py
│   │       ├── test_design_endpoints.py
│   │       └── test_subscription_endpoints.py
│   │
│   └── e2e/
│       └── test_complete_flow.py
│
├── scripts/
│   ├── seed_dev_data.py
│   ├── reset_monthly_usage.py (cron job)
│   └── upload_initial_assets.py
│
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example
│
├── requirements.txt
├── requirements-dev.txt
├── .env
├── .gitignore
├── pyproject.toml
├── alembic.ini
└── README.md



📊 Métricas de Éxito
Al completar el Core API deberías tener:
yamlCódigo:
  - ~8,000 líneas Python
  - 45 endpoints REST funcionales
  - 32 use cases implementados
  - 20+ tests (>70% coverage)

Database:
  - 5 tablas principales
  - 15+ índices optimizados
  - 3+ migrations

Performance:
  - Latency p95 <500ms
  - Cache hit rate >70%
  - 0 N+1 queries