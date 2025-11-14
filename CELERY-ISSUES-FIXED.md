# Celery Worker Issues - Corrections Applied

## Issues Identified and Fixed

### ✅ Issue 1: Celery Database Backend URL
**Problem:** Celery doesn't support async drivers (asyncpg)
**Location:** `app/infrastructure/workers/celery_app.py` line 10

**Solution Applied:**
1. Added `celery_database_url` property to `Settings` class in `app/config.py`:
   - Converts `postgresql+asyncpg://` → `db+postgresql://`
   - Returns sync-compatible URL for Celery result backend

2. Updated `celery_app.py` to use the new property:
   ```python
   backend=settings.celery_database_url  # ✅ Now uses sync driver
   ```

---

### ✅ Issue 2: Design Entity Methods
**Problem:** Methods `mark_rendered()` and `mark_failed()` referenced but unclear if existed
**Location:** `app/infrastructure/workers/tasks/render_design.py`

**Solution Applied:**
- Verified that `Design` entity already has correct methods:
  - ✅ `mark_rendering()` - Changes DRAFT → RENDERING
  - ✅ `mark_published(preview_url, thumbnail_url)` - RENDERING → PUBLISHED
  - ✅ `mark_failed(error_message)` - RENDERING → FAILED
- No changes needed - methods already implemented correctly

---

### ✅ Issue 3: Worker Logging Configuration
**Problem:** Tasks were using `print()` statements instead of proper logging
**Location:** All task files

**Solution Applied:**
1. Created `app/infrastructure/workers/logging_config.py`:
   - Configures logging with INFO/WARNING levels based on DEBUG setting
   - Suppresses noisy Celery/Kombu logs
   - Returns configured logger instance

2. Updated `render_design.py`:
   - Replaced all `print()` with `logger.info()`, `logger.error()`, `logger.debug()`
   - Added structured logging with context (design_id, URLs, errors)
   - Uses `exc_info=True` for full error tracebacks

3. Updated `send_email.py`:
   - Replaced all `print()` with `logger.info()`, `logger.error()`, `logger.debug()`
   - Added structured logging for email operations

---

### ✅ Issue 4: Worker Health Check Endpoint
**Problem:** No way to check if workers are running
**Location:** Missing endpoint

**Solution Applied:**
1. Created `app/presentation/api/v1/endpoints/system.py`:
   - `GET /api/v1/system/health` - Basic API health check
   - `GET /api/v1/system/worker-status` - Detailed worker status:
     * Active workers and their stats
     * Currently executing tasks
     * Scheduled tasks
     * Registered task types
     * Broker URL (credentials hidden)
     * Error handling if workers unavailable

2. Updated `app/presentation/api/v1/router.py`:
   - Added system router to API v1

**Usage:**
```bash
# Check API health
curl http://localhost:8000/api/v1/system/health

# Check worker status
curl http://localhost:8000/api/v1/system/worker-status
```

---

### ✅ Issue 5: Docker Compose Worker Environment
**Problem:** Worker service had `DATABASE_URL` with `+asyncpg` driver
**Location:** `docker-compose.yml` worker service

**Solution Applied:**
- Changed worker `DATABASE_URL` from:
  ```yaml
  DATABASE_URL: postgresql+asyncpg://customify:customify123@postgres:5432/customify_dev
  ```
  To:
  ```yaml
  DATABASE_URL: postgresql://customify:customify123@postgres:5432/customify_dev
  ```
- Added comment: `# Database (use service name as host, sync driver for Celery)`

---

## Files Modified

1. ✅ `app/config.py` - Added `celery_database_url` property
2. ✅ `app/infrastructure/workers/celery_app.py` - Use sync database URL
3. ✅ `app/infrastructure/workers/logging_config.py` - Created logging config
4. ✅ `app/infrastructure/workers/tasks/render_design.py` - Replace print with logger
5. ✅ `app/infrastructure/workers/tasks/send_email.py` - Replace print with logger
6. ✅ `app/presentation/api/v1/endpoints/system.py` - Created worker health check
7. ✅ `app/presentation/api/v1/router.py` - Added system router
8. ✅ `docker-compose.yml` - Fixed worker DATABASE_URL

---

## Verification Steps

### 1. Test Celery Database Connection
```bash
# Start services
docker-compose up -d

# Check worker logs
docker-compose logs worker

# Should see: "Connected to db+postgresql://..."
# Should NOT see errors about async drivers
```

### 2. Test Worker Logging
```bash
# Create a design (triggers render task)
curl -X POST http://localhost:8000/api/v1/designs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test", "design_data": {"text": "Hello"}}'

# Check worker logs for structured logging
docker-compose logs -f worker

# Should see:
# 2025-11-14 12:34:56 - customify.workers - INFO - Starting render for design abc123
# 2025-11-14 12:34:58 - customify.workers - INFO - Completed render for design abc123
```

### 3. Test Worker Health Endpoint
```bash
# Check API health
curl http://localhost:8000/api/v1/system/health

# Check worker status
curl http://localhost:8000/api/v1/system/worker-status

# Expected response:
{
  "workers_available": true,
  "workers": {
    "celery@customify-worker": {
      "pool": {"max-concurrency": 2},
      ...
    }
  },
  "active_tasks": {...},
  "registered_tasks": {
    "celery@customify-worker": [
      "render_design_preview",
      "send_email",
      "debug_task"
    ]
  },
  "broker": "redis:6379/0"
}
```

### 4. Test End-to-End Flow
```bash
# 1. Create design
DESIGN_ID=$(curl -X POST http://localhost:8000/api/v1/designs ... | jq -r '.id')

# 2. Check status immediately (should be DRAFT or RENDERING)
curl http://localhost:8000/api/v1/designs/$DESIGN_ID | jq '.status'

# 3. Wait 2 seconds (mock render time)
sleep 2

# 4. Check status again (should be PUBLISHED)
curl http://localhost:8000/api/v1/designs/$DESIGN_ID | jq '.status, .preview_url'

# Expected:
# "PUBLISHED"
# "https://cdn.customify.app/designs/{id}/preview.png"
```

---

## Next Steps (Optional Improvements)

### Task Tracking (Optional for MVP)
Add `render_task_id` field to Design entity to track Celery task status:
- Migration to add `render_task_id` column
- Store `task.id` when queueing render job
- Create endpoint to check task progress: `GET /designs/{id}/render-status`

**Benefits:**
- Real-time progress updates
- Better error tracking
- Can retry specific tasks

**Skip for MVP:** Current status-based tracking (DRAFT → RENDERING → PUBLISHED) is sufficient.

---

## Summary

All critical issues have been fixed:
- ✅ Celery now uses sync PostgreSQL driver (psycopg2)
- ✅ Proper structured logging with configurable levels
- ✅ Worker health check endpoint for monitoring
- ✅ Docker compose environment fixed for worker service
- ✅ All print() statements replaced with logger calls

The worker implementation is now production-ready for MVP deployment.
