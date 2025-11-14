# Deployment Guide - Core API

**Propósito:** Docker, CI/CD, y deployment a AWS ECS

---

## 🐳 Docker

### Dockerfile (Multi-Stage, Optimizado)
```dockerfile
# deployment/Dockerfile

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Development)
```yaml
# docker-compose.yml

version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: deployment/Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/customify
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=true
    volumes:
      - ./app:/app/app  # Hot reload
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: customify
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Build & Run
```bash
# Development (hot reload)
docker-compose up -d

# Production build
docker build -t customify-api:latest -f deployment/Dockerfile .

# Run production
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e REDIS_URL="redis://..." \
  customify-api:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag customify-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest
```

---

## 🚀 CI/CD (GitHub Actions)

### Workflow: Test & Lint
```yaml
# .github/workflows/ci.yml

name: CI

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: customify_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Lint (ruff)
        run: ruff check .
      
      - name: Format check (black)
        run: black --check .
      
      - name: Type check (mypy)
        run: mypy app
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/customify_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test-secret-key-min-32-characters-long
        run: |
          pytest -v --cov=app --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### Workflow: Deploy to ECS
```yaml
# .github/workflows/cd.yml

name: CD

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: customify-api
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f deployment/Dockerfile .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Deploy to ECS
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: customify-api
          IMAGE_TAG: ${{ github.sha }}
        run: |
          # Update task definition with new image
          aws ecs update-service \
            --cluster customify-cluster \
            --service customify-api-service \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster customify-cluster \
            --services customify-api-service
```

---

## ☁️ AWS ECS Deployment

### Task Definition (JSON)
```json
{
  "family": "customify-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/customify-api-task-role",
  "containerDefinitions": [
    {
      "name": "customify-api",
      "image": "ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "AWS_REGION", "value": "us-east-1"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:customify/database-url"
        },
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:customify/jwt-secret"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:customify/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/customify-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Service Definition
```json
{
  "serviceName": "customify-api-service",
  "taskDefinition": "customify-api:1",
  "desiredCount": 2,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": [
        "subnet-private-1a",
        "subnet-private-1b"
      ],
      "securityGroups": ["sg-api"],
      "assignPublicIp": "DISABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:...",
      "containerName": "customify-api",
      "containerPort": 8000
    }
  ],
  "healthCheckGracePeriodSeconds": 60,
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 100
  }
}
```

---

## 🔐 Secrets Management

### AWS Secrets Manager
```bash
# Create secret
aws secretsmanager create-secret \
  --name customify/database-url \
  --secret-string "postgresql+asyncpg://user:pass@rds-endpoint:5432/customify"

# Rotate secret (every 90 days)
aws secretsmanager rotate-secret \
  --secret-id customify/database-url \
  --rotation-lambda-arn arn:aws:lambda:...
```

### Environment Variables
```bash
# Production (.env nunca commitear)
ENVIRONMENT=production
DEBUG=false

# Database (from Secrets Manager)
DATABASE_URL=<from-secrets-manager>

# Redis
REDIS_URL=redis://customify-redis.cache.amazonaws.com:6379/0

# JWT
JWT_SECRET_KEY=<from-secrets-manager>

# AWS
AWS_REGION=us-east-1
S3_BUCKET_NAME=customify-production

# OpenAI
OPENAI_API_KEY=<from-secrets-manager>

# Stripe
STRIPE_SECRET_KEY=<from-secrets-manager>
```

---

## 📊 Monitoring Post-Deploy

### Health Checks
```bash
# ALB health check
curl https://api.customify.app/health

# Deep health check (DB + Redis)
curl https://api.customify.app/health/deep

# CloudWatch logs
aws logs tail /ecs/customify-api --follow
```

### Metrics to Watch (First 24h)
```
✅ ALB Target Health: 100% healthy
✅ Response Time p95: <500ms
✅ Error Rate 5xx: <1%
✅ CPU Usage: <70%
✅ Memory Usage: <80%
✅ Request Count: Esperado según traffic
```

### Rollback Plan
```bash
# If issues detected:

# 1. Check logs
aws logs tail /ecs/customify-api --since 10m

# 2. Rollback to previous task definition
aws ecs update-service \
  --cluster customify-cluster \
  --service customify-api-service \
  --task-definition customify-api:PREVIOUS_VERSION

# 3. Monitor rollback
aws ecs wait services-stable \
  --cluster customify-cluster \
  --services customify-api-service

# 4. Verify health
curl https://api.customify.app/health
```

---

## 🚨 Troubleshooting Deploy Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| ECS tasks failing immediately | Check logs | Fix application error, check env vars |
| Health checks failing | Test `/health` manually | Fix health endpoint, adjust grace period |
| Can't connect to DB | Security group | Allow ECS SG → RDS SG on port 5432 |
| Secrets not loading | IAM permissions | Add `secretsmanager:GetSecretValue` to task role |
| Out of memory | Container crashing | Increase memory in task definition |
| Slow deployment | Rolling update | Use Blue/Green deployment for zero-downtime |

---

## 🎯 Deployment Checklist

Pre-deploy:
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Migrations ready (if schema changes)
- [ ] Secrets updated in AWS Secrets Manager
- [ ] Monitoring dashboard ready

Deploy:
- [ ] Merge to main
- [ ] CI/CD pipeline triggered
- [ ] Docker image built and pushed to ECR
- [ ] ECS service updated
- [ ] Wait for services-stable

Post-deploy (monitor 24h):
- [ ] Health checks passing
- [ ] Logs clean (no errors)
- [ ] Latency within targets
- [ ] Error rate <1%
- [ ] Database connections healthy

---
