# Customify - Plantillas de Desarrollo con IA

**Versión:** 1.0.0  
**Última actualización:** Noviembre 2025  
**Propósito:** Guías completas para desarrollo asistido por IA (Claude, Copilot, Cursor)

---

## 🎯 Objetivo de estas Plantillas

Estas plantillas sirven como:

1. **Memoria técnica persistente** para agentes IA (especialmente GitHub Copilot que tiene memoria corta)
2. **Base de conocimiento** para Claude Projects, Cursor AI
3. **Trazabilidad diaria** de avances y pendientes
4. **Documentación viva** que evoluciona con el proyecto
5. **Onboarding rápido** para nuevos developers

---

## 🏗️ Arquitectura Customify - Vista General
```
┌────────────────────────────────────────────────────────────────┐
│                    CLIENTE FINAL                                │
│           (Comprador en tienda Shopify)                         │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ↓
┌────────────────────────────────────────────────────────────────┐
│              06-WIDGET-EMBEBIBLE (React)                        │
│   Editor de diseños + Preview + AI Suggestions                 │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ↓
┌────────────────────────────────────────────────────────────────┐
│           CLOUDFLARE CDN + WAF + DDoS Protection                │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ↓
┌────────────────────────────────────────────────────────────────┐
│                  AWS ALB (Load Balancer)                        │
└────────┬──────────────┴────────────────────┬───────────────────┘
         │                                    │
         ↓                                    ↓
┌─────────────────────┐            ┌─────────────────────────────┐
│  01-CORE-API        │            │ 07-DASHBOARD-MERCHANT       │
│  (FastAPI)          │            │ (React SPA)                 │
│  - Auth             │            │ - Gestión designs           │
│  - Designs CRUD     │            │ - Analytics                 │
│  - Subscriptions    │            │ - Settings                  │
└──────────┬──────────┘            └─────────────────────────────┘
           │
           ├─────────────────┬─────────────────┬─────────────────┐
           │                 │                 │                 │
           ↓                 ↓                 ↓                 ↓
    ┌──────────┐      ┌──────────┐    ┌──────────┐     ┌──────────┐
    │02-AI     │      │03-INTEG  │    │04-WORKERS│     │05-RENDER │
    │SERVICES  │      │LAYER     │    │(Celery)  │     │ENGINE    │
    │          │      │          │    │          │     │          │
    │-OpenAI   │      │-Shopify  │    │-Render   │     │-Canvas   │
    │-Pinecone │      │-Stripe   │    │-PDF Gen  │     │-PIL      │
    │-RAG      │      │-WooComm  │    │-Email    │     │-Fonts    │
    └──────────┘      └──────────┘    └──────────┘     └──────────┘
           │                 │                 │                 │
           └─────────────────┴─────────────────┴─────────────────┘
                                      │
                   ┌──────────────────┼──────────────────┐
                   │                  │                  │
                   ↓                  ↓                  ↓
            ┌──────────┐       ┌──────────┐      ┌──────────┐
            │08-DATABASE│       │09-CACHE  │      │10-STORAGE│
            │          │       │          │      │          │
            │PostgreSQL│       │Redis     │      │S3        │
            │RDS       │       │Sessions  │      │Images    │
            │          │       │RateLimit │      │PDFs      │
            └──────────┘       └──────────┘      └──────────┘
                                      │
                                      ↓
                              ┌──────────────┐
                              │11-OBSERV     │
                              │              │
                              │-Sentry       │
                              │-CloudWatch   │
                              │-Mixpanel     │
                              └──────────────┘
```

---

## 📚 Componentes del Sistema

| # | Componente | Tecnología Principal | Propósito | Semanas Plan |
|---|------------|---------------------|-----------|--------------|
| **01** | Core API | FastAPI (Python 3.12) | Backend principal, Auth, CRUD | 1-2 |
| **02** | AI Services | OpenAI + Pinecone + LangChain | Suggestions, RAG, optimización | 3 |
| **03** | Integration Layer | Python + REST APIs | Shopify, Stripe, WooCommerce | 6-7 |
| **04** | Background Workers | Celery + SQS | Procesar jobs async (render, PDF) | 4 |
| **05** | Render Engine | Python + PIL/Canvas | Generar imágenes preview | 5 |
| **06** | Widget Embebible | React + TypeScript | Editor cliente final (embed) | 4-6 |
| **07** | Dashboard Merchant | React + TypeScript | Panel admin merchants | 8 |
| **08** | Database | PostgreSQL + Alembic | Persistencia datos | 1 |
| **09** | Cache Layer | Redis + ElastiCache | Cache, sessions, rate limiting | 1 |
| **10** | Storage | S3 + CloudFront | Archivos estáticos (imgs, PDFs) | 2 |
| **11** | Observability | Sentry + CloudWatch + Mixpanel | Logs, errors, analytics | 9-12 |

---

## 🎯 Orden de Desarrollo Sugerido

### Fase 1: Backend Foundation (Semanas 1-3)
```
1. 08-database        (Semana 1) ← Primero: Schema + migrations
2. 09-cache-layer     (Semana 1) ← Setup Redis
3. 01-core-api        (Semanas 1-2) ← Auth + CRUD designs
4. 02-ai-services     (Semana 3) ← OpenAI integration
```

### Fase 2: Frontend & Workers (Semanas 4-6)
```
5. 04-background-workers (Semana 4) ← Celery + SQS
6. 05-render-engine      (Semana 5) ← Image generation
7. 06-widget-embebible   (Semanas 4-6) ← React editor
8. 10-storage            (Semana 5) ← S3 uploads
```

### Fase 3: Integrations & Dashboard (Semanas 6-8)
```
9. 03-integration-layer  (Semanas 6-7) ← Shopify, Stripe
10. 07-dashboard-merchant (Semana 8) ← Admin panel
```

### Fase 4: Polish & Launch (Semanas 9-12)
```
11. 11-observability (Semanas 9-12) ← Monitoring, testing
    + Bug fixes, optimization, launch
```

---

## 🤖 Cómo Usar estas Plantillas con Agentes IA

### Para Claude Projects (Memoria larga)

1. **Al iniciar componente nuevo:**
```
   Abre Claude Projects
   Agrega archivos del componente:
   - README.md
   - ARQUITECTURA.md
   - TECNOLOGIAS.md
   - PROMPTS_IA.md
   
   Prompt inicial:
   "He agregado la documentación completa del componente [nombre].
    Léela y confírmame que entiendes:
    1. El propósito del componente
    2. Las tecnologías a usar
    3. La arquitectura
    4. Las restricciones importantes"
```

2. **Durante desarrollo:**
```
   Actualiza DAILY-LOG.md al final del día
   Mañana: Claude lee tu log de ayer
   
   Prompt:
   "Lee mi DAILY-LOG.md de ayer. Continúa desde donde quedé.
    Pending items: [lista del log]"
```

### Para GitHub Copilot (Memoria corta)

1. **Siempre mantén abiertos estos archivos:**
   - `TECNOLOGIAS.md` ← Copilot lee esto para contexto
   - `DESARROLLO.md` ← Convenciones de código
   - Archivo actual que estás editando

2. **Usa comentarios con contexto:**
```python
   # TECNOLOGÍA: FastAPI + SQLAlchemy async + Pydantic v2
   # ARQUITECTURA: Clean Architecture - Use Case pattern
   # RESTRICCIÓN: Siempre async/await, nunca sync I/O
   
   async def create_design(user_id: str, data: dict) -> Design:
       # Copilot: Implementa CreateDesignUseCase siguiendo Clean Architecture
       # 1. Validar user tiene subscription activa
       # 2. Check quota designs_this_month < plan_limit
       # 3. Create Design entity
       # 4. Save via repository
       # 5. Enqueue render job (SQS)
```

3. **Naming conventions específicas en TECNOLOGIAS.md:**
   - Copilot autocomplete será consistente

### Para Cursor AI (Inteligencia mejorada)

1. **Configurar `.cursorrules` (archivo en raíz):**
```
   Ver archivo PROMPTS_IA.md de cada componente
   Tiene sección específica para Cursor
```

2. **Comandos Cursor útiles:**
```
   Cmd+K: "Implementa [feature] siguiendo ARQUITECTURA.md"
   Cmd+L: Chat con contexto de múltiples archivos
```

---

## 🎨 Convenciones Globales del Proyecto

### Naming Conventions

**Python (Backend):**
```python
# Archivos: snake_case
user_repository.py
create_design_use_case.py

# Clases: PascalCase
class CreateDesignUseCase
class DesignRepository

# Funciones/métodos: snake_case
async def create_design()
async def get_user_by_id()

# Constantes: UPPER_SNAKE_CASE
MAX_DESIGNS_PER_MONTH = 100
DEFAULT_PLAN = "starter"

# Variables: snake_case
user_id = "123"
design_data = {...}
```

**TypeScript (Frontend):**
```typescript
// Archivos: kebab-case
design-editor.tsx
ai-suggestions.tsx

// Componentes: PascalCase
export function DesignEditor() {}
export function AISuggestions() {}

// Funciones: camelCase
function createDesign() {}
function getUserProfile() {}

// Constantes: UPPER_SNAKE_CASE
const MAX_FILE_SIZE = 10_000_000

// Variables: camelCase
const userId = "123"
const designData = {...}

// Interfaces/Types: PascalCase
interface Design {}
type DesignData = {}
```

### Git Workflow

**Branches:**
```
main              ← Production (protected)
staging           ← Staging environment
develop           ← Development base

feature/[nombre]  ← Nuevas features
fix/[nombre]      ← Bug fixes
hotfix/[nombre]   ← Urgent production fixes
```

**Commits:** Conventional Commits
```
feat: Add AI suggestions endpoint
fix: Resolve race condition in cache
docs: Update TECNOLOGIAS.md for component X
refactor: Extract validation logic to domain service
test: Add unit tests for CreateDesignUseCase
chore: Update dependencies
```

---

## 📊 Trazabilidad Diaria - Sistema

Cada componente tiene un archivo `DAILY-LOG.md` para tracking diario.

**Al final del día (5 min):**
1. Abre `DAILY-LOG.md` de tu componente actual
2. Agrega entrada con fecha
3. Lista qué completaste, qué falta, bloqueadores

**Al iniciar día siguiente:**
1. Lee tu entrada de ayer
2. Prompt a tu IA:
```
   "Lee mi DAILY-LOG.md. Continúa desde donde quedé ayer.
    Pending tasks: [lista]"
```

Ver `DAILY-PROGRESS-TEMPLATE.md` para formato exacto.

---

## 🎯 Próximo Paso

**Si es tu primera vez:**

1. Lee este archivo completo (00-OVERVIEW.md) ✅
2. Lee DAILY-PROGRESS-TEMPLATE.md
3. Identifica qué componente empezarás (probablemente 08-database o 01-core-api)
4. Abre la carpeta de ese componente
5. Lee en orden: README.md → ARQUITECTURA.md → TECNOLOGIAS.md → DESARROLLO.md
6. Configura tu agente IA favorito con PROMPTS_IA.md
7. Empieza a codear 🚀

**Si ya estás desarrollando:**

1. Abre tu DAILY-LOG.md de ayer
2. Resume a tu agente IA dónde quedaste
3. Continúa con tus pending items
4. Al final del día: Actualiza DAILY-LOG.md

---

## 🔗 Links Rápidos a Componentes

- [01-core-api/](./01-core-api/) - FastAPI Backend
- [02-ai-services/](./02-ai-services/) - OpenAI & Pinecone
- [03-integration-layer/](./03-integration-layer/) - Shopify & Stripe
- [04-background-workers/](./04-background-workers/) - Celery Workers
- [05-render-engine/](./05-render-engine/) - Image Rendering
- [06-widget-embebible/](./06-widget-embebible/) - React Widget
- [07-dashboard-merchant/](./07-dashboard-merchant/) - React Dashboard
- [08-database/](./08-database/) - PostgreSQL
- [09-cache-layer/](./09-cache-layer/) - Redis
- [10-storage/](./10-storage/) - S3
- [11-observability/](./11-observability/) - Monitoring

---

**¡Bienvenido a Customify! Construyamos algo increíble.** 🎨🤖