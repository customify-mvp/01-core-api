# Arquitectura - Core API

**Versión:** 1.0  
**Última actualización:** 12 de Noviembre 2025  
**Reviewers:** Backend Team

---

## 📊 Diagrama Arquitectónico de Alto Nivel
```
┌───────────────────────────────────────────────────────────────────┐
│                          CORE API                                  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              PRESENTATION LAYER                           │   │
│  │  (FastAPI, HTTP, JSON, Middleware)                        │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  API Endpoints (REST)                              │  │   │
│  │  │  ├── POST   /auth/register                         │  │   │
│  │  │  ├── POST   /auth/login                            │  │   │
│  │  │  ├── POST   /designs                               │  │   │
│  │  │  ├── GET    /designs                               │  │   │
│  │  │  ├── GET    /designs/{id}                          │  │   │
│  │  │  ├── PUT    /designs/{id}                          │  │   │
│  │  │  ├── DELETE /designs/{id}                          │  │   │
│  │  │  └── GET    /health                                │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Pydantic Schemas (Validation)                     │  │   │
│  │  │  ├── DesignCreateRequest                           │  │   │
│  │  │  ├── DesignResponse                                │  │   │
│  │  │  ├── LoginRequest                                  │  │   │
│  │  │  └── TokenResponse                                 │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Middleware                                        │  │   │
│  │  │  ├── CORS (Cloudflare whitelist)                  │  │   │
│  │  │  ├── Auth (JWT verification)                      │  │   │
│  │  │  ├── Rate Limiting (Redis sliding window)         │  │   │
│  │  │  ├── Error Handler (standardized responses)       │  │   │
│  │  │  └── Logging (structured JSON)                    │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └────────────────────┬──────────────────────────────────────┘   │
│                       │                                           │
│  ┌────────────────────▼──────────────────────────────────────┐   │
│  │           APPLICATION LAYER                               │   │
│  │  (Use Cases - Business Logic Orchestration)               │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Use Cases                                          │ │   │
│  │  │                                                     │ │   │
│  │  │  Auth:                                             │ │   │
│  │  │  ├── RegisterUserUseCase                          │ │   │
│  │  │  │   1. Validate email unique                     │ │   │
│  │  │  │   2. Hash password                             │ │   │
│  │  │  │   3. Create user entity                        │ │   │
│  │  │  │   4. Save via repository                       │ │   │
│  │  │  │   5. Create default subscription               │ │   │
│  │  │  │                                                 │ │   │
│  │  │  ├── LoginUserUseCase                             │ │   │
│  │  │  │   1. Get user by email                         │ │   │
│  │  │  │   2. Verify password                           │ │   │
│  │  │  │   3. Generate JWT tokens                       │ │   │
│  │  │  │   4. Store session in Redis                    │ │   │
│  │  │  │                                                 │ │   │
│  │  │  Designs:                                          │ │   │
│  │  │  ├── CreateDesignUseCase                          │ │   │
│  │  │  │   1. Check user subscription active            │ │   │
│  │  │  │   2. Check quota (designs this month)          │ │   │
│  │  │  │   3. Validate design_data schema               │ │   │
│  │  │  │   4. If AI requested: call OpenAI              │ │   │
│  │  │  │   5. Create design entity                      │ │   │
│  │  │  │   6. Save via repository                       │ │   │
│  │  │  │   7. Enqueue render job (SQS)                  │ │   │
│  │  │  │                                                 │ │   │
│  │  │  ├── UpdateDesignUseCase                          │ │   │
│  │  │  ├── DeleteDesignUseCase                          │ │   │
│  │  │  └── ListDesignsUseCase                           │ │   │
│  │  │                                                     │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  DTOs (Data Transfer Objects)                       │ │   │
│  │  │  ├── UserDTO                                        │ │   │
│  │  │  ├── DesignDTO                                      │ │   │
│  │  │  └── SubscriptionDTO                                │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └────────────────────┬──────────────────────────────────────┘   │
│                       │                                           │
│  ┌────────────────────▼──────────────────────────────────────┐   │
│  │              DOMAIN LAYER (CORE)                          │   │
│  │  (Business Entities, Rules, Interfaces)                   │   │
│  │  ⚠️  NO external dependencies (pure Python)              │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Entities (Business Objects)                        │ │   │
│  │  │                                                     │ │   │
│  │  │  class User:                                       │ │   │
│  │  │      id: str                                       │ │   │
│  │  │      email: Email  # Value Object                 │ │   │
│  │  │      password_hash: str                           │ │   │
│  │  │      created_at: datetime                         │ │   │
│  │  │      subscription: Subscription                   │ │   │
│  │  │                                                     │ │   │
│  │  │      def is_active(self) -> bool:                 │ │   │
│  │  │          return self.subscription.is_active       │ │   │
│  │  │                                                     │ │   │
│  │  │  class Design:                                     │ │   │
│  │  │      id: str                                       │ │   │
│  │  │      user_id: str                                  │ │   │
│  │  │      product_type: str                             │ │   │
│  │  │      design_data: DesignData  # Value Object      │ │   │
│  │  │      status: DesignStatus  # Enum                 │ │   │
│  │  │      preview_url: Optional[str]                   │ │   │
│  │  │                                                     │ │   │
│  │  │      def validate(self) -> None:                  │ │   │
│  │  │          # Business rules validation              │ │   │
│  │  │                                                     │ │   │
│  │  │  class Subscription:                               │ │   │
│  │  │      user_id: str                                  │ │   │
│  │  │      plan: PlanType  # Enum: starter, pro, ent   │ │   │
│  │  │      status: SubscriptionStatus                   │ │   │
│  │  │      designs_this_month: int                      │ │   │
│  │  │                                                     │ │   │
│  │  │      def has_quota(self) -> bool:                 │ │   │
│  │  │          limit = self.plan.design_limit           │ │   │
│  │  │          return self.designs_this_month < limit   │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Value Objects (Immutable)                          │ │   │
│  │  │                                                     │ │   │
│  │  │  class Email:                                      │ │   │
│  │  │      value: str                                    │ │   │
│  │  │      def __init__(self, value: str):              │ │   │
│  │  │          if not self._is_valid(value):            │ │   │
│  │  │              raise ValueError("Invalid email")    │ │   │
│  │  │          self.value = value                       │ │   │
│  │  │                                                     │ │   │
│  │  │  class DesignData:                                 │ │   │
│  │  │      text: str                                     │ │   │
│  │  │      font: str                                     │ │   │
│  │  │      color: str                                    │ │   │
│  │  │      position: dict                                │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Repository Interfaces (Abstract)                   │ │   │
│  │  │                                                     │ │   │
│  │  │  class IUserRepository(ABC):                       │ │   │
│  │  │      @abstractmethod                               │ │   │
│  │  │      async def create(self, user: User) -> User    │ │   │
│  │  │                                                     │ │   │
│  │  │      @abstractmethod                               │ │   │
│  │  │      async def get_by_id(self, id: str) -> User   │ │   │
│  │  │                                                     │ │   │
│  │  │  class IDesignRepository(ABC):                     │ │   │
│  │  │      @abstractmethod                               │ │   │
│  │  │      async def create(self, design: Design)        │ │   │
│  │  │                                                     │ │   │
│  │  │      @abstractmethod                               │ │   │
│  │  │      async def get_by_user(self, user_id: str)    │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Domain Services                                    │ │   │
│  │  │  (Logic que no pertenece a una entidad)            │ │   │
│  │  │                                                     │ │   │
│  │  │  class PasswordHasher:                             │ │   │
│  │  │      def hash(self, password: str) -> str          │ │   │
│  │  │      def verify(self, plain, hashed) -> bool       │ │   │
│  │  │                                                     │ │   │
│  │  │  class QuotaChecker:                               │ │   │
│  │  │      def check(self, subscription: Subscription)   │ │   │
│  │  │                                                     │ │   │
│  │  │  class DesignValidator:                            │ │   │
│  │  │      def validate_schema(self, data: dict) -> bool│ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └────────────────────┬──────────────────────────────────────┘   │
│                       │ implements                                │
│  ┌────────────────────▼──────────────────────────────────────┐   │
│  │         INFRASTRUCTURE LAYER                              │   │
│  │  (External Systems, Frameworks, I/O)                      │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Database (PostgreSQL via SQLAlchemy)               │ │   │
│  │  │                                                     │ │   │
│  │  │  SQLAlchemy Models (ORM):                          │ │   │
│  │  │  ├── UserModel (maps to User entity)               │ │   │
│  │  │  ├── DesignModel (maps to Design entity)           │ │   │
│  │  │  └── SubscriptionModel                             │ │   │
│  │  │                                                     │ │   │
│  │  │  Repository Implementations:                       │ │   │
│  │  │  ├── UserRepositoryImpl(IUserRepository)           │ │   │
│  │  │  │   - Uses SQLAlchemy async sessions             │ │   │
│  │  │  │   - Converts Model ↔ Entity                    │ │   │
│  │  │  └── DesignRepositoryImpl(IDesignRepository)       │ │   │
│  │  │                                                     │ │   │
│  │  │  Alembic Migrations:                               │ │   │
│  │  │  └── Versioned schema changes                      │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Cache (Redis)                                      │ │   │
│  │  │  ├── RedisClient (connection pool)                 │ │   │
│  │  │  ├── Session storage (JWT blacklist)               │ │   │
│  │  │  ├── Rate limiting counters                        │ │   │
│  │  │  └── Cache layer (API responses)                   │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Storage (S3)                                       │ │   │
│  │  │  ├── S3Client (boto3 wrapper)                      │ │   │
│  │  │  ├── Upload images                                 │ │   │
│  │  │  ├── Presigned URLs                                │ │   │
│  │  │  └── Lifecycle policies                            │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Queue (SQS)                                        │ │   │
│  │  │  ├── SQSClient (boto3)                             │ │   │
│  │  │  └── Enqueue render jobs                           │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  AI Services                                        │ │   │
│  │  │  ├── OpenAIClient (design suggestions)             │ │   │
│  │  │  ├── PineconeClient (vector search)                │ │   │
│  │  │  └── Retry logic + fallbacks                       │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  External Integrations                              │ │   │
│  │  │  ├── ShopifyClient (OAuth, webhooks)               │ │   │
│  │  │  └── StripeClient (payments, subscriptions)        │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Responsabilidades por Capa

### PRESENTATION LAYER

**Responsabilidades:**
- Recibir HTTP requests
- Validar inputs (Pydantic)
- Autenticar/Autorizar (JWT middleware)
- Rate limiting (Redis)
- Llamar Use Cases
- Formatear responses
- Manejo de errores HTTP (400, 401, 403, 404, 500)

**NO debe:**
- ❌ Contener business logic
- ❌ Acceder directamente a base de datos
- ❌ Conocer detalles de infraestructura

**Ejemplo:**
```python
# app/presentation/api/v1/endpoints/designs.py

@router.post("/designs", response_model=DesignResponse)
async def create_design(
    request: DesignCreateRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateDesignUseCase = Depends(get_create_design_use_case)
):
    """
    Presentation layer SOLO:
    1. Valida request (Pydantic)
    2. Extrae user del JWT
    3. Llama use case
    4. Formatea response
    
    NO hace business logic.
    """
    try:
        design = await use_case.execute(
            user_id=current_user.id,
            product_type=request.product_type,
            design_data=request.design_data,
            use_ai=request.use_ai_suggestions
        )
        return DesignResponse.from_entity(design)
    except QuotaExceededError as e:
        raise HTTPException(status_code=402, detail=str(e))
```

### APPLICATION LAYER

**Responsabilidades:**
- Orquestar business logic (use cases)
- Coordinar entre múltiples entidades/servicios
- Implementar workflows complejos
- Transacciones (si span multiple repos)

**NO debe:**
- ❌ Conocer HTTP/REST/JSON
- ❌ Conocer SQLAlchemy/Redis directamente
- ❌ Contener lógica de validación de entidades (eso es Domain)

**Ejemplo:**
```python
# app/application/use_cases/designs/create_design.py

class CreateDesignUseCase:
    def __init__(
        self,
        design_repo: IDesignRepository,
        subscription_repo: ISubscriptionRepository,
        quota_checker: QuotaChecker,
        ai_client: OpenAIClient,
        queue_client: SQSClient
    ):
        self.design_repo = design_repo
        self.subscription_repo = subscription_repo
        self.quota_checker = quota_checker
        self.ai_client = ai_client
        self.queue_client = queue_client
    
    async def execute(
        self,
        user_id: str,
        product_type: str,
        design_data: dict,
        use_ai: bool
    ) -> Design:
        """
        Use Case orquesta el flujo:
        1. Business rules check
        2. Coordina múltiples services
        3. Persiste datos
        4. Encola jobs
        
        Pero NO conoce HTTP ni SQLAlchemy.
        """
        # 1. Check subscription
        subscription = await self.subscription_repo.get_by_user(user_id)
        if not subscription.is_active:
            raise InactiveSubscriptionError()
        
        # 2. Check quota
        if not self.quota_checker.check(subscription):
            raise QuotaExceededError(subscription.plan)
        
        # 3. AI suggestions si requested
        ai_suggestions = None
        if use_ai:
            ai_suggestions = await self.ai_client.suggest_designs(
                product_type=product_type,
                text=design_data.get('text')
            )
        
        # 4. Create entity (domain logic)
        design = Design.create(
            user_id=user_id,
            product_type=product_type,
            design_data=design_data,
            ai_suggestions=ai_suggestions
        )
        
        # 5. Persist
        design = await self.design_repo.create(design)
        
        # 6. Enqueue render job
        await self.queue_client.enqueue_render_job(design.id)
        
        # 7. Update subscription usage
        await self.subscription_repo.increment_usage(user_id)
        
        return design
```

### DOMAIN LAYER

**Responsabilidades:**
- Definir entidades (User, Design, Subscription)
- Business rules (validations, constraints)
- Value objects (Email, Money)
- Repository interfaces
- Domain services (logic que no pertenece a una entidad)

**NO debe:**
- ❌ Conocer NADA de infrastructure (SQLAlchemy, Redis, S3, HTTP)
- ❌ Tener dependencies externas (solo Python standard lib)
- ❌ Hacer I/O (no DB, no file, no network)

**Ejemplo:**
```python
# app/domain/entities/design.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class DesignStatus(Enum):
    DRAFT = "draft"
    RENDERING = "rendering"
    PUBLISHED = "published"

@dataclass
class Design:
    """
    Domain entity - Pure business logic.
    
    NO tiene dependencies externas.
    NO conoce SQLAlchemy.
    NO hace I/O.
    """
    id: str
    user_id: str
    product_type: str
    design_data: dict
    status: DesignStatus
    preview_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def create(
        cls,
        user_id: str,
        product_type: str,
        design_data: dict,
        ai_suggestions: Optional[list] = None
    ) -> 'Design':
        """Factory method con business rules."""
        # Business rule: validate product type
        allowed_types = ['t-shirt', 'mug', 'poster', 'hoodie']
        if product_type not in allowed_types:
            raise ValueError(f"Invalid product type: {product_type}")
        
        # Business rule: design_data must have required fields
        required_fields = ['text', 'font', 'color']
        if not all(field in design_data for field in required_fields):
            raise ValueError("Missing required fields in design_data")
        
        import uuid
        from datetime import datetime
        
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            product_type=product_type,
            design_data=design_data,
            status=DesignStatus.DRAFT,
            preview_url=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def validate(self) -> None:
        """Business rules validation."""
        # Rule: text length max 100 chars
        if len(self.design_data.get('text', '')) > 100:
            raise ValueError("Text too long (max 100 chars)")
        
        # Rule: color must be valid hex
        import re
        color = self.design_data.get('color', '')
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError(f"Invalid color: {color}")
    
    def mark_as_rendering(self) -> None:
        """Business logic: transition status."""
        if self.status != DesignStatus.DRAFT:
            raise ValueError("Can only render drafts")
        self.status = DesignStatus.RENDERING
    
    def mark_as_published(self, preview_url: str) -> None:
        """Business logic: publish design."""
        if self.status != DesignStatus.RENDERING:
            raise ValueError("Can only publish after rendering")
        self.status = DesignStatus.PUBLISHED
        self.preview_url = preview_url


# app/domain/repositories/design_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.design import Design

class IDesignRepository(ABC):
    """
    Repository interface defined in Domain.
    
    Infrastructure implementa esta interface.
    """
    
    @abstractmethod
    async def create(self, design: Design) -> Design:
        """Persist design, return with generated ID."""
        pass
    
    @abstractmethod
    async def get_by_id(self, design_id: str) -> Optional[Design]:
        """Get design by ID."""
        pass
    
    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Design]:
        """Get user's designs with pagination."""
        pass
    
    @abstractmethod
    async def update(self, design: Design) -> Design:
        """Update existing design."""
        pass
    
    @abstractmethod
    async def delete(self, design_id: str) -> bool:
        """Soft delete design."""
        pass
```

### INFRASTRUCTURE LAYER

**Responsabilidades:**
- Implementar repository interfaces
- Interactuar con DB (SQLAlchemy)
- Cache (Redis)
- External APIs (OpenAI, S3, Shopify, Stripe)
- Queue (SQS)
- Convertir entre Domain entities ↔ Infrastructure models

**NO debe:**
- ❌ Contener business logic

**Ejemplo:**
```python
# app/infrastructure/database/repositories/design_repo_impl.py

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.design_repository import IDesignRepository
from app.domain.entities.design import Design, DesignStatus
from app.infrastructure.database.models.design_model import DesignModel

class DesignRepositoryImpl(IDesignRepository):
    """
    Infrastructure implementation of IDesignRepository.
    
    Usa SQLAlchemy, pero Domain NO lo sabe.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, design: Design) -> Design:
        """Convert entity → model, save, convert back."""
        # Entity → Model
        model = DesignModel(
            id=design.id,
            user_id=design.user_id,
            product_type=design.product_type,
            design_data=design.design_data,  # JSONB column
            status=design.status.value,
            preview_url=design.preview_url,
            created_at=design.created_at,
            updated_at=design.updated_at,
            is_deleted=False
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        # Model → Entity
        return self._model_to_entity(model)
    
    async def get_by_id(self, design_id: str) -> Optional[Design]:
        """Get design by ID."""
        stmt = select(DesignModel).where(
            DesignModel.id == design_id,
            DesignModel.is_deleted == False
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Design]:
        """Get user's designs with pagination."""
        stmt = (
            select(DesignModel)
            .where(
                DesignModel.user_id == user_id,
                DesignModel.is_deleted == False
            )
            .order_by(DesignModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(m) for m in models]
    
    def _model_to_entity(self, model: DesignModel) -> Design:
        """Convert SQLAlchemy model to Domain entity."""
        return Design(
            id=model.id,
            user_id=model.user_id,
            product_type=model.product_type,
            design_data=model.design_data,
            status=DesignStatus(model.status),
            preview_url=model.preview_url,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
```

---

## 🔄 Data Flow Completo

### Ejemplo: User crea un design con AI suggestions
```
1. CLIENT (Dashboard React)
   │
   │ POST /api/v1/designs
   │ {
   │   "product_type": "t-shirt",
   │   "design_data": {
   │     "text": "Happy Birthday",
   │     "font": "Bebas-Bold",
   │     "color": "#FF69B4"
   │   },
   │   "use_ai_suggestions": true
   │ }
   │
   ↓ HTTP (Authorization: Bearer JWT)

2. CLOUDFLARE CDN
   │ - DDoS protection
   │ - WAF rules
   │ - SSL termination
   │
   ↓ HTTPS

3. AWS ALB
   │ - Health checks
   │ - Load balancing (round robin)
   │ - TLS re-encryption
   │
   ↓ HTTP (internal VPC)

4. PRESENTATION LAYER
   │ app/presentation/api/v1/endpoints/designs.py
   │
   │ @router.post("/designs")
   │ async def create_design(...):
   │
   ├─→ Auth Middleware
   │    ├─ Verify JWT signature
   │    ├─ Check expiry
   │    ├─ Extract user_id
   │    └─ Return current_user
   │
   ├─→ Rate Limit Middleware
   │    ├─ Redis: Check request count (IP + user)
   │    ├─ If exceeded: 429 Too Many Requests
   │    └─ Else: Increment counter
   │
   ├─→ Pydantic Validation
   │    ├─ Validate request schema
   │    ├─ Type checking
   │    └─ If invalid: 400 Bad Request
   │
   └─→ Call Use Case
        ↓

5. APPLICATION LAYER
   │ app/application/use_cases/designs/create_design.py
   │
   │ CreateDesignUseCase.execute()
   │
   ├─→ Get Subscription (via repository)
   │    └─ INFRASTRUCTURE calls PostgreSQL
   │         └─ Returns Subscription entity
   │
   ├─→ Check Subscription Active
   │    └─ if not: raise InactiveSubscriptionError
   │
   ├─→ Check Quota (via domain service)
   │    ├─ QuotaChecker.check(subscription)
   │    └─ if exceeded: raise QuotaExceededError
   │
   ├─→ Call AI Service (if requested)
   │    └─ INFRASTRUCTURE calls OpenAI API
   │         ├─ POST https://api.openai.com/v1/chat/completions
   │         ├─ Prompt: "Generate 5 t-shirt design suggestions..."
   │         ├─ Response: 5 suggestions (text, colors, layout)
   │         └─ Returns parsed suggestions
   │
   ├─→ Create Design Entity (DOMAIN)
   │    ├─ Design.create(user_id, product_type, design_data)
   │    ├─ Validates business rules
   │    │   ├─ Product type in allowed list
   │    │   ├─ Required fields present
   │    │   ├─ Text length < 100 chars
   │    │   └─ Color valid hex
   │    └─ Returns Design entity (status: DRAFT)
   │
   ├─→ Persist Design (via repository)
   │    └─ INFRASTRUCTURE
   │         ├─ Convert entity → SQLAlchemy model
   │         ├─ INSERT INTO designs (...)
   │         ├─ Commit transaction
   │         └─ Return entity with DB-generated ID
   │
   ├─→ Enqueue Render Job
   │    └─ INFRASTRUCTURE calls SQS
   │         ├─ Message: {"design_id": "abc123", "action": "render"}
   │         └─ Worker will pick up later
   │
   └─→ Increment Subscription Usage
        └─ UPDATE subscriptions SET designs_this_month = X + 1
        ↓

6. PRESENTATION LAYER (Response)
   │
   ├─→ Convert entity → DesignResponse (Pydantic)
   │    └─ Serialize to JSON
   │
   └─→ Return HTTP 201 Created
        ↓

7. CLOUDFLARE CDN
   │ - Cache response (if cacheable)
   │ - Return to client
   │
   ↓

8. CLIENT
   │ 201 Created
   │ {
   │   "id": "550e8400-e29b-41d4-a716-446655440000",
   │   "user_id": "user-123",
   │   "product_type": "t-shirt",
   │   "status": "draft",
   │   "preview_url": null,  ← rendering...
   │   "ai_suggestions": [
   │     {
   │       "text": "Happy Birthday!",
   │       "font": "Bebas-Bold",
   │       "colors": ["#FF69B4", "#FFFFFF"],
   │       "layout": "centered"
   │     },
   │     ...
   │   ],
   │   "created_at": "2025-12-08T10:30:00Z"
   │ }
   │
   └─→ Frontend updates UI
        ├─ Show design in list
        ├─ Show "Rendering..." status
        └─ Poll /designs/{id} para preview_url
```

**Latencia total:**
- Without AI: ~150ms
  - Auth middleware: 5ms (JWT verify)
  - Rate limit check: 3ms (Redis)
  - Validation: 2ms
  - DB queries: 50ms (get subscription, create design)
  - SQS enqueue: 20ms
  - Overhead: 70ms
  
- With AI: ~2.8s
  - Same as above: 150ms
  - OpenAI API call: 2.5s (GPT-4)
  - Cache (80% of time): 150ms solo

---

## 🏛️ Decisiones Arquitectónicas (ADRs)

### ADR-001: FastAPI sobre Django

**Status:** Accepted  
**Decisión:** Usar FastAPI como web framework

**Contexto:**
- Necesitamos async/await para performance con I/O
- Auto-docs (OpenAPI) esencial para frontend team
- Type safety con Pydantic v2

**Alternativas consideradas:**
- Django + DRF: Descartado por sync-only, menos performante
- Flask: Descartado por falta de async first-class, no auto-docs

**Consecuencias:**
- ✅ Performance: 3-5x mejor que Django
- ✅ Auto-docs gratis (Swagger UI)
- ✅ Type safety con Pydantic
- ❌ Ecosystem menor que Django (pero suficiente)
- ❌ No admin panel built-in (crear custom)

---

### ADR-002: Clean Architecture

**Status:** Accepted  
**Decisión:** Implementar Clean Architecture con 4 capas

**Contexto:**
- Proyecto vivirá 5+ años
- Múltiples developers trabajarán
- Necesitamos testability alta
- Queremos poder cambiar DB/frameworks sin refactor completo

**Alternativas consideradas:**
- Monolito simple (archivos planos): Descartado, no escala
- Microservicios: Overkill para MVP, added complexity

**Consecuencias:**
- ✅ Testability: Unit tests sin DB (fast)
- ✅ Maintainability: Clear separation of concerns
- ✅ Flexibility: Cambiar infrastructure fácil
- ❌ Boilerplate: Más archivos/carpetas
- ❌ Learning curve: Team debe entender capas

---

### ADR-003: Async by Default

**Status:** Accepted  
**Decisión:** Todas las operaciones I/O son async/await

**Contexto:**
- 80% de operaciones son I/O bound (DB, Redis, OpenAI, S3)
- FastAPI y SQLAlchemy 2.0 son async-first
- Concurrency requirements altos (100s requests simultáneos)

**Consecuencias:**
- ✅ Performance: 3-5x mejor throughput
- ✅ Resource efficiency: Menos workers needed
- ❌ No sync libraries (ej: `requests` → usar `httpx`)
- ❌ Debugging ligeramente más complejo

---

### ADR-004: JWT Authentication (Stateless)

**Status:** Accepted  
**Decisión:** JWT tokens stateless, refresh tokens en Redis

**Contexto:**
- Horizontal scaling: N instancias detrás ALB
- No queremos sticky sessions
- Queremos microservices-ready para futuro

**Alternativas consideradas:**
- Server-side sessions: Descartado, necesita shared state (Redis sync)
- OAuth2 third-party: Overkill para MVP

**Implementación:**
- Access token: 7 días expiry (JWT)
- Refresh token: 30 días expiry (stored in Redis)
- Logout: Blacklist token en Redis (TTL = token expiry)

**Consecuencias:**
- ✅ Scalability: Stateless, no sticky sessions
- ✅ Performance: No DB lookup cada request
- ❌ Token revocation: Solo via blacklist (Redis)
- ❌ Token size: 300-500 bytes vs 32 bytes session ID

---

### ADR-005: Repository Pattern

**Status:** Accepted  
**Decisión:** Abstraer DB access con Repository interfaces en Domain

**Contexto:**
- Clean Architecture requiere dependency inversion
- Queremos test use cases sin DB real
- Queremos flexibilidad para cambiar DB (PostgreSQL → MongoDB futuro?)

**Consecuencias:**
- ✅ Testability: Mock repositories en tests
- ✅ Flexibility: Cambiar DB implementation sin cambiar use cases
- ❌ Boilerplate: Interface + Implementation por cada entity

---

## 📈 Escalabilidad

### Horizontal Scaling

**Actual (MVP):**
```
ALB
 ├─ ECS Task 1 (0.5 vCPU, 1GB RAM)
 └─ ECS Task 2 (0.5 vCPU, 1GB RAM)
      ↓
 [PostgreSQL RDS - db.t3.micro]
 [Redis ElastiCache - cache.t3.micro]
```

**Año 1 (1K users):**
```
ALB
 ├─ ECS Task 1 (1 vCPU, 2GB RAM)
 ├─ ECS Task 2
 ├─ ECS Task 3
 └─ ECS Task 4
      ↓
 [PostgreSQL RDS - db.t3.small]
 [Redis ElastiCache - cache.t3.small with replica]
```

**Año 2 (10K users):**
```
ALB
 ├─ ECS Tasks: 10x (2 vCPU, 4GB RAM each)
      ↓
 [PostgreSQL RDS - db.t3.medium]
   ├─ Writer instance
   └─ Read replica (analytics queries)
 [Redis ElastiCache - cache.m5.large]
   ├─ Primary
   └─ Replica (Multi-AZ)
```

### Bottlenecks y Soluciones

| Bottleneck | Síntoma | Solución |
|------------|---------|----------|
| **DB Connections** | Connection pool exhausted | Increase pool size, add read replicas |
| **Redis Memory** | Cache evictions frecuentes | Scale up instance, optimize TTLs |
| **OpenAI Rate Limits** | 429 errors | Cache agresivo (80% hit rate), queue requests |
| **CPU (ECS)** | CPU >80% sustained | Auto-scale tasks horizontally |
| **DB Slow Queries** | p95 latency >500ms | Add indexes, optimize queries, add read replica |

---

## 🔒 Seguridad

### Security Layers
```
1. NETWORK (AWS VPC)
   ├─ API en private subnet (no public IP)
   ├─ Security groups (port 8000 only from ALB)
   └─ NACLs (network ACLs)

2. APPLICATION (FastAPI)
   ├─ JWT verification (every request)
   ├─ Input validation (Pydantic)
   ├─ SQL injection prevention (SQLAlchemy parameterized)
   ├─ XSS prevention (output escaping)
   ├─ Rate limiting (100 req/min per IP)
   └─ CORS (whitelisted origins)

3. DATA (PostgreSQL)
   ├─ Encryption at rest (KMS)
   ├─ Encryption in transit (TLS 1.2+)
   ├─ IAM authentication (no passwords)
   └─ Least privilege (app role can't DROP tables)

4. SECRETS (AWS Secrets Manager)
   ├─ Database passwords
   ├─ API keys (OpenAI, Stripe)
   ├─ JWT secret
   └─ Rotation: Every 90 días (automated)
```

### Threat Model

| Threat | Mitigation | Test |
|--------|------------|------|
| SQL Injection | SQLAlchemy parameterized queries | OWASP ZAP scan |
| XSS | Output escaping, CSP headers | Manual + ZAP |
| CSRF | SameSite cookies, no state-changing GETs | Unit tests |
| Auth bypass | JWT signature verify, expiry check | Unit tests |
| DDoS | Cloudflare + rate limiting + autoscaling | Load testing |
| Data leak | Authorization checks (user owns resource) | Unit tests |

---

## 📚 Referencias

- [Clean Architecture - Uncle Bob](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [SQLAlchemy 2.0 Style Guide](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

---
