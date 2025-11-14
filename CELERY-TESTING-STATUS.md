# Celery Worker - Testing & Troubleshooting

## ✅ Tests Passed

### Test 2: Services Running ✅
```bash
docker-compose ps
```
**Result:** All services UP and HEALTHY
- customify-api: ✅ Running (port 8000)
- customify-worker: ✅ Running
- customify-flower: ✅ Running (port 5555)
- customify-postgres: ✅ Healthy
- customify-redis: ✅ Healthy

### Test 5: Worker Status Endpoint ✅
```bash
GET http://localhost:8000/api/v1/system/worker-status
```
**Result:**
```json
{
  "workers_available": true,
  "workers": {
    "celery@94464f2e0209": {
      "pid": 1,
      "uptime": 384,
      "pool": {
        "max-concurrency": 2,
        "processes": [8, 9],
        "max-tasks-per-child": 1000
      }
    }
  },
  "registered_tasks": {
    "celery@94464f2e0209": [
      "app.infrastructure.workers.celery_app.debug_task",
      "render_design_preview",
      "send_email"
    ]
  },
  "broker": "redis://redis:6379/0"
}
```

### Test 4: Flower UI ✅
```bash
GET http://localhost:5555
```
**Result:** HTTP 200 OK - Flower monitoring UI is accessible

### Health Check ✅
```bash
GET http://localhost:8000/api/v1/system/health
```
**Result:** `{"status":"ok","message":"Customify Core API is running"}`

## ⚠️ Issue: Worker Not Processing Tasks

### Symptoms
1. Worker starts successfully
2. Tasks are queued (get Task ID)
3. Worker never processes tasks (no logs, status stays "draft")
4. No "ready" message appears in worker logs

### Current Worker Logs
```
 -------------- celery@d0965fa4257f v5.3.4 (emerald-rush)
--- ***** -----
.> app:         customify_workers
.> transport:   redis://redis:6379/0
.> results:     postgresql://customify:**@postgres:5432/customify_dev
.> concurrency: 2 (prefork)
.> queues: default, high_priority

[tasks]
  . debug_task
  . render_design_preview
  . send_email
```

Worker hangs after initialization, never shows "ready" or "Connected to".

### Possible Causes

1. **Result Backend Connection Issue**
   - Worker connects to Redis (broker) OK
   - May be failing to connect to PostgreSQL result backend
   - No explicit error shown, just hangs

2. **Task Routing Mismatch**
   - Tasks may be going to wrong queue
   - Worker listening to `default` and `high_priority`
   - `render_design_preview` routed to `high_priority`
   - But task name in celery_app.py is just `"render_design_preview"`, not full path

3. **Clock Skew Warning**
   - Saw warning: "Substantial drift... Current drift is 18000 seconds (5 hours)"
   - May cause task scheduling issues

## 🔧 Troubleshooting Steps

### Step 1: Verify Redis Connection
```bash
docker-compose exec worker redis-cli -h redis ping
# Expected: PONG
```

### Step 2: Verify PostgreSQL Connection
```bash
docker-compose exec worker python -c "
from app.infrastructure.database.sync_session import sync_engine
conn = sync_engine.connect()
print('✅ PostgreSQL connection OK')
conn.close()
"
# Expected: ✅ PostgreSQL connection OK
```

### Step 3: Check Celery Inspect
```bash
docker-compose exec api python -c "
from app.infrastructure.workers.celery_app import celery_app
inspect = celery_app.control.inspect()
print('Active:', inspect.active())
print('Registered:', inspect.registered())
print('Stats:', inspect.stats())
"
```

### Step 4: Send Task Directly to Default Queue
```bash
docker-compose exec api python -c "
from app.infrastructure.workers.celery_app import celery_app
# Send to default queue explicitly
result = celery_app.send_task('app.infrastructure.workers.celery_app.debug_task', queue='default')
print('Task ID:', result.id)
"
```

### Step 5: Run Worker in Debug Mode
```bash
docker-compose stop worker

# Run with verbose logging
docker-compose run --rm worker celery -A app.infrastructure.workers.celery_app worker --loglevel=debug --concurrency=1 --pool=solo --queues=default

# In another terminal, send task:
docker-compose exec api python -c "
from app.infrastructure.workers.celery_app import debug_task
result = debug_task.delay()
print('Task sent:', result.id)
"

# Watch debug logs for task processing
```

### Step 6: Fix Clock Skew
The 5-hour drift warning suggests timezone issues. Check:
```bash
# Worker time
docker-compose exec worker date

# System time
date

# If different, sync system clock or set worker timezone:
# In docker-compose.yml:
environment:
  - TZ=America/New_York  # Or your timezone
```

### Step 7: Simplify Result Backend (Test Only)
Try using Redis for both broker AND result backend:
```python
# In celery_app.py (temporary test)
celery_app = Celery(
    "customify_workers",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),  # Use Redis instead of PostgreSQL
    include=[...]
)
```

If this works, the issue is PostgreSQL result backend configuration.

### Step 8: Check Task Name Registration
```bash
docker-compose exec worker python -c "
from app.infrastructure.workers.celery_app import celery_app
print('Registered tasks:')
for task in celery_app.tasks:
    print(' -', task)
"
```

Verify `render_design_preview` appears exactly as registered.

## 📋 Manual Test Workflow

### Full End-to-End Test (When Worker Fixed)

```powershell
# 1. Register user
$body = @{email='test@test.com'; password='Test1234!'; full_name='Test User'} | ConvertTo-Json
Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/auth/register' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing

# 2. Login and get token
$login = @{email='test@test.com'; password='Test1234!'} | ConvertTo-Json
$response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/auth/login' -Method POST -Body $login -ContentType 'application/json' -UseBasicParsing
$token = ($response.Content | ConvertFrom-Json).access_token

# 3. Create design
$headers = @{Authorization="Bearer $token"}
$design = @{
    product_type='t-shirt'
    design_data=@{
        text='Worker Test'
        font='Bebas-Bold'
        color='#FF0000'
        fontSize=24
    }
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/designs' -Method POST -Headers $headers -Body $design -ContentType 'application/json' -UseBasicParsing
$designData = $response.Content | ConvertFrom-Json
$designId = $designData.id

Write-Host "Design created: $designId"
Write-Host "Initial status: $($designData.status)"  # Should be "draft"

# 4. Wait for worker to process (2s render + processing)
Start-Sleep -Seconds 5

# 5. Check status again
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/designs/$designId" -Headers $headers -UseBasicParsing
$design = $response.Content | ConvertFrom-Json

Write-Host "Final status: $($design.status)"  # Should be "published"
Write-Host "Preview URL: $($design.preview_url)"  # Should have URL

# Expected output:
# Design created: xxx-xxx-xxx
# Initial status: draft
# Final status: published
# Preview URL: https://cdn.customify.app/designs/xxx/preview.png
```

## ✅ What's Working

1. **Infrastructure Setup**
   - ✅ Sync database session (sync_session.py)
   - ✅ Sync repository (sync_design_repo.py)
   - ✅ Celery configuration (celery_app.py)
   - ✅ Worker tasks (render_design.py, send_email.py)
   - ✅ Logging configuration (logging_config.py)
   - ✅ Health check endpoints (system.py)

2. **Docker Compose**
   - ✅ All services start successfully
   - ✅ Health checks pass
   - ✅ Flower monitoring accessible

3. **API Integration**
   - ✅ CreateDesignUseCase queues tasks correctly
   - ✅ Tasks get Task IDs
   - ✅ Worker status endpoint returns correct info

## 🚧 What Needs Fixing

1. **Worker Task Processing**
   - ⚠️ Worker hangs after startup
   - ⚠️ Tasks never execute
   - ⚠️ No error messages

**Root cause likely:** Result backend configuration or task routing issue

## 📝 Recommended Next Steps

1. Run Step 5 (debug mode worker) to see detailed logs
2. Try Step 7 (Redis result backend) to isolate issue
3. Check Step 6 (clock skew) - 5 hour difference is significant
4. Verify task names match exactly (Step 8)

## 💡 Quick Fixes to Try

### Fix 1: Use Redis Result Backend (Simplest)
```python
# app/infrastructure/workers/celery_app.py
celery_app = Celery(
    "customify_workers",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),  # Change this line
    include=[...]
)
```

Rebuild: `docker-compose up -d --build worker`

### Fix 2: Add Worker Ready Event Handler
```python
# app/infrastructure/workers/celery_app.py
from celery.signals import worker_ready

@worker_ready.connect
def on_worker_ready(**kwargs):
    print("🚀 Worker is ready to process tasks!")
```

This will confirm when worker actually starts listening.

### Fix 3: Explicit Task Registration
```python
# app/infrastructure/workers/tasks/render_design.py
# Change task name to be explicit
@celery_app.task(bind=True, name="render_design_preview", queue="high_priority")
def render_design_preview(self, design_id: str) -> dict:
    ...
```

## 📊 Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Services Running | ✅ PASS | All containers healthy |
| Worker Status API | ✅ PASS | Endpoint returns correct data |
| Health Check | ✅ PASS | API responding |
| Flower UI | ✅ PASS | Monitoring accessible |
| Task Queueing | ✅ PASS | Tasks get IDs |
| **Task Processing** | ❌ FAIL | **Worker not executing tasks** |
| Design Status Change | ❌ FAIL | Stays "draft" (depends on task processing) |

**Overall:** 5/7 tests passing. Core functionality implemented correctly, worker configuration needs debugging.
