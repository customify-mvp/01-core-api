# ============================================================
# Celery Worker Quick Start Guide
# ============================================================

## Overview

This project uses Celery for background task processing with:
- **Redis** as message broker (development)
- **PostgreSQL** as result backend
- **2 Queues**: `high_priority` (renders), `default` (emails)

## Tasks

1. **render_design_preview** (Queue: `high_priority`)
   - Renders design previews asynchronously (2-10s)
   - Updates design status: DRAFT → RENDERING → PUBLISHED
   - Rate limit: 10/minute

2. **send_email** (Queue: `default`)
   - Sends emails (currently mock implementation)
   - Rate limit: 50/minute

## Running Workers

### Using Docker Compose (Recommended)

```bash
# Start all services (API, Worker, Redis, PostgreSQL)
docker-compose up -d

# View worker logs
docker-compose logs -f worker

# View Flower monitoring UI
open http://localhost:5555

# Stop services
docker-compose down
```

### Local Development

**Linux/macOS:**
```bash
chmod +x scripts/start_worker.sh
./scripts/start_worker.sh
```

**Windows:**
```bash
scripts\start_worker.bat
```

**Manual (any OS):**
```bash
# Activate virtual environment first
celery -A app.infrastructure.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=high_priority,default
```

## Monitoring

### Flower Web UI
- URL: http://localhost:5555
- View tasks, workers, queues, task history
- Real-time monitoring

### Celery CLI
```bash
# Inspect active tasks
celery -A app.infrastructure.workers.celery_app inspect active

# Inspect scheduled tasks
celery -A app.infrastructure.workers.celery_app inspect scheduled

# Check worker stats
celery -A app.infrastructure.workers.celery_app inspect stats

# Ping workers
celery -A app.infrastructure.workers.celery_app inspect ping
```

## Testing

### Test Connectivity
```python
from app.infrastructure.workers.celery_app import debug_task

# Queue test task
result = debug_task.delay()
print(result.get(timeout=10))
```

### Test Render Task
```python
from app.infrastructure.workers.tasks.render_design import render_design_preview

# Queue render task
result = render_design_preview.delay("design-uuid-here")
print(result.get(timeout=30))  # Wait max 30s
```

### Test via API
```bash
# Create design (automatically queues render task)
curl -X POST http://localhost:8000/api/v1/designs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "workspace_id": "workspace-uuid",
    "name": "Test Design",
    "template_id": "template-uuid",
    "design_data": {}
  }'

# Check design status (should be RENDERING → PUBLISHED)
curl http://localhost:8000/api/v1/designs/{design_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### Environment Variables
```bash
# Required
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Optional
CELERY_BROKER_URL=redis://localhost:6379/0  # Defaults to REDIS_URL
CELERY_RESULT_BACKEND=db+postgresql://...    # Defaults to DATABASE_URL
```

### Worker Settings (celery_app.py)
```python
worker_prefetch_multiplier=1  # Take 1 task at a time
worker_max_tasks_per_child=1000  # Restart after 1000 tasks
task_time_limit=300  # Hard limit: 5 minutes
task_soft_time_limit=240  # Soft limit: 4 minutes
```

### Retry Strategy
```python
max_retries=3  # Retry up to 3 times
retry_backoff=True  # Exponential backoff
backoff_max=600  # Max 10 minutes between retries
retry_jitter=True  # Add randomness to prevent thundering herd
```

## Troubleshooting

### Worker won't start
```bash
# Check Redis
redis-cli -u redis://localhost:6379/0 ping

# Check PostgreSQL
psql -h localhost -U customify -d customify_dev -c '\q'

# Verify Python dependencies
pip list | grep celery
```

### Tasks stuck in "PENDING"
- Worker not running → Start worker
- Wrong queue → Check task route configuration
- Redis connection issue → Verify REDIS_URL

### Tasks fail immediately
- Check worker logs: `docker-compose logs -f worker`
- Check database connection
- Verify task imports in `celery_app.py`

### High memory usage
- Restart worker (max_tasks_per_child=1000)
- Reduce concurrency
- Check for memory leaks in task code

## Production Deployment

### Switch to AWS SQS (Production Broker)
```python
# celery_app.py
broker_url = "sqs://" if settings.ENVIRONMENT == "production" else str(settings.REDIS_URL)
```

### Environment Variables
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/xxx/customify-tasks
```

### Scaling
```bash
# Horizontal scaling (multiple workers)
docker-compose up -d --scale worker=4

# Vertical scaling (more concurrency per worker)
celery ... worker --concurrency=4
```

## Next Steps

1. ✅ Workers configured and running
2. 🔄 Implement actual rendering logic (PIL/Pillow)
3. 🔄 Implement AWS SES email sending
4. 🔄 Add webhook processing task
5. 🔄 Implement PDF generation task
6. 🔄 Switch to SQS broker for production
7. 🔄 Add monitoring alerts (Sentry, CloudWatch)

## Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Redis Documentation](https://redis.io/docs/)
- [AWS SQS with Celery](https://docs.celeryproject.org/en/stable/getting-started/brokers/sqs.html)
