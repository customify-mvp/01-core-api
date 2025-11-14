# Customify Core API - Deployment Guide

Complete guide for deploying Customify Core API to production environments.

---

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [AWS Infrastructure](#aws-infrastructure)
- [Docker Deployment](#docker-deployment)
- [AWS ECS Deployment](#aws-ecs-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring Setup](#monitoring-setup)
- [Security Hardening](#security-hardening)
- [Backup & Recovery](#backup--recovery)
- [Scaling Guidelines](#scaling-guidelines)
- [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

### Code Readiness

- [ ] All tests passing (`pytest --cov=app`)
- [ ] Coverage >70%
- [ ] No security vulnerabilities (`safety check`)
- [ ] Code reviewed and approved
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `app/__init__.py`
- [ ] Git tag created (`vX.Y.Z`)

### Infrastructure

- [ ] Production database created (RDS)
- [ ] Redis cluster created (ElastiCache)
- [ ] S3 bucket created and configured
- [ ] CloudFront distribution created (optional)
- [ ] IAM roles and policies created
- [ ] VPC and security groups configured
- [ ] SSL certificate obtained (ACM)

### Secrets

- [ ] JWT secret key generated (secure random)
- [ ] Database credentials stored in Secrets Manager
- [ ] AWS access keys created (IAM user for app)
- [ ] Stripe keys obtained (if using payments)
- [ ] Encryption key generated (Fernet)

### Monitoring

- [ ] Sentry project created
- [ ] CloudWatch alarms configured
- [ ] PagerDuty/Opsgenie integration
- [ ] Log aggregation setup (CloudWatch Logs)

---

## Environment Setup

### Production Environment Variables

Create `.env.production`:
```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database (from AWS RDS)
DATABASE_URL=postgresql+asyncpg://customify:SECURE_PASSWORD@prod-db.us-east-1.rds.amazonaws.com:5432/customify_prod

# Redis (from ElastiCache)
REDIS_URL=redis://prod-redis.cache.amazonaws.com:6379/0

# JWT (MUST be secure random 32+ chars)
JWT_SECRET_KEY=GENERATE_WITH_openssl_rand_base64_32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=customify-production
CLOUDFRONT_DOMAIN=d123456789abcde.cloudfront.net

# Storage
USE_LOCAL_STORAGE=false

# Encryption
ENCRYPTION_KEY=GENERATE_WITH_python_fernet_generate_key

# CORS (production domains)
CORS_ORIGINS=https://app.customify.com,https://www.customify.com

# Sentry (error tracking)
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0

# Stripe (payments)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Shopify
SHOPIFY_API_KEY=...
SHOPIFY_API_SECRET=...
```

### Generate Secure Secrets
```bash
# JWT Secret (32+ chars)
openssl rand -base64 32

# Encryption Key (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Database Password
openssl rand -base64 24
```

---

## Database Setup

### 1. Create RDS Instance

**AWS Console:**
1. Navigate to RDS → Create database
2. Choose PostgreSQL 15.x
3. Template: Production
4. DB instance class: db.t3.medium (start small, scale up)
5. Storage: 100 GB GP3, autoscaling enabled
6. Multi-AZ deployment: Yes
7. VPC: Use production VPC
8. Security group: Allow port 5432 from app security group only
9. Database name: `customify_prod`
10. Automated backups: 7 days retention

**AWS CLI:**
```bash
aws rds create-db-instance \
    --db-instance-identifier customify-prod-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 15.3 \
    --master-username customify \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 100 \
    --storage-type gp3 \
    --storage-encrypted \
    --multi-az \
    --db-name customify_prod \
    --backup-retention-period 7 \
    --vpc-security-group-ids sg-12345678 \
    --db-subnet-group-name customify-prod-subnet-group \
    --tags Key=Environment,Value=production Key=Application,Value=customify
```

### 2. Configure Database
```bash
# Connect to database
psql postgresql://customify:PASSWORD@prod-db.us-east-1.rds.amazonaws.com:5432/customify_prod

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create read-only user (for analytics)
CREATE USER customify_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE customify_prod TO customify_readonly;
GRANT USAGE ON SCHEMA public TO customify_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO customify_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO customify_readonly;
```

### 3. Run Migrations
```bash
# Set production DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://customify:PASSWORD@prod-db.us-east-1.rds.amazonaws.com:5432/customify_prod"

# Run migrations
alembic upgrade head

# Verify tables
psql $DATABASE_URL -c "\dt"
```

---

## AWS Infrastructure

### 1. S3 Bucket
```bash
# Create bucket
aws s3 mb s3://customify-production --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket customify-production \
    --versioning-configuration Status=Enabled

# Configure lifecycle (delete old thumbnails after 90 days)
aws s3api put-bucket-lifecycle-configuration \
    --bucket customify-production \
    --lifecycle-configuration file://s3-lifecycle.json

# Block public access (use signed URLs instead)
aws s3api put-public-access-block \
    --bucket customify-production \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

**s3-lifecycle.json:**
```json
{
  "Rules": [
    {
      "Id": "DeleteOldThumbnails",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "designs/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "INTELLIGENT_TIERING"
        }
      ],
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 30
      }
    }
  ]
}
```

### 2. CloudFront CDN (Optional but Recommended)
```bash
# Create distribution
aws cloudfront create-distribution \
    --origin-domain-name customify-production.s3.amazonaws.com \
    --default-root-object index.html \
    --comment "Customify Production CDN"
```

**CloudFront configuration:**
- Origin: S3 bucket
- Viewer Protocol Policy: Redirect HTTP to HTTPS
- Allowed HTTP Methods: GET, HEAD, OPTIONS
- Cached Methods: GET, HEAD, OPTIONS
- TTL: Min 0, Default 86400 (1 day), Max 31536000 (1 year)
- Compress Objects: Yes
- Price Class: Use All Edge Locations

### 3. ElastiCache Redis
```bash
# Create Redis cluster
aws elasticache create-replication-group \
    --replication-group-id customify-prod-redis \
    --replication-group-description "Customify production Redis" \
    --engine redis \
    --engine-version 7.0 \
    --cache-node-type cache.t3.micro \
    --num-cache-clusters 2 \
    --automatic-failover-enabled \
    --multi-az-enabled \
    --cache-subnet-group-name customify-prod-subnet-group \
    --security-group-ids sg-redis-12345
```

### 4. IAM Roles

**ECS Task Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Attach policies:**
- `AmazonECSTaskExecutionRolePolicy` (AWS managed)
- Custom policy for Secrets Manager, CloudWatch Logs

**ECS Task Role (for app container):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::customify-production/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:customify/*"
    }
  ]
}
```

---

## Docker Deployment

### 1. Create Production Dockerfile

**Dockerfile.prod:**
```dockerfile
# Build stage
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

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd -m -u 1000 customify && \
    chown -R customify:customify /app

USER customify

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
```

### 2. Build and Push to ECR
```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name customify-api --region us-east-1

# Build image
docker build -t customify-api:latest -f Dockerfile.prod .

# Tag for ECR
docker tag customify-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest
docker tag customify-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/customify-api:v1.0.0

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/customify-api:v1.0.0
```

---

## AWS ECS Deployment

### 1. Create Task Definition

**ecs-task-definition.json:**
```json
{
  "family": "customify-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/customify-task-role",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest",
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
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:customify/database-url"
        },
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:customify/jwt-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/customify-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    },
    {
      "name": "worker",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest",
      "essential": false,
      "command": [
        "celery",
        "-A",
        "app.infrastructure.workers.celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=4"
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:customify/database-url"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:customify/redis-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/customify-worker",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "worker"
        }
      }
    }
  ]
}
```

### 2. Register Task Definition
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

### 3. Create ECS Service
```bash
aws ecs create-service \
    --cluster customify-prod \
    --service-name customify-api-service \
    --task-definition customify-api:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-api-12345],assignPublicIp=DISABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/customify-api/abcd1234,containerName=api,containerPort=8000" \
    --health-check-grace-period-seconds 60 \
    --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
    --enable-execute-command
```

### 4. Setup Application Load Balancer
```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name customify-prod-alb \
    --subnets subnet-12345 subnet-67890 \
    --security-groups sg-alb-12345 \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4

# Create target group
aws elbv2 create-target-group \
    --name customify-api-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-12345 \
    --target-type ip \
    --health-check-enabled \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 10 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3

# Create HTTPS listener (requires SSL certificate)
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/... \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...

# Redirect HTTP to HTTPS
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}"
```

---

## Kubernetes Deployment

### 1. Create Deployment YAML

**k8s/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customify-api
  namespace: customify-prod
  labels:
    app: customify-api
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: customify-api
  template:
    metadata:
      labels:
        app: customify-api
        version: v1.0.0
    spec:
      containers:
      - name: api
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/customify-api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: customify-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: customify-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: customify-secrets
              key: jwt-secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: customify-api-service
  namespace: customify-prod
spec:
  type: LoadBalancer
  selector:
    app: customify-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: customify-api-hpa
  namespace: customify-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: customify-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace customify-prod

# Create secrets
kubectl create secret generic customify-secrets \
    --from-literal=database-url="$DATABASE_URL" \
    --from-literal=redis-url="$REDIS_URL" \
    --from-literal=jwt-secret-key="$JWT_SECRET_KEY" \
    -n customify-prod

# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -n customify-prod
kubectl get svc -n customify-prod

# View logs
kubectl logs -f deployment/customify-api -n customify-prod
```

---

## Monitoring Setup

### 1. CloudWatch Alarms
```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name customify-api-high-cpu \
    --alarm-description "Alert when API CPU > 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:customify-alerts

# High error rate
aws cloudwatch put-metric-alarm \
    --alarm-name customify-api-high-errors \
    --alarm-description "Alert when 5xx errors > 10/min" \
    --metric-name 5XXError \
    --namespace AWS/ApplicationELB \
    --statistic Sum \
    --period 60 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:customify-alerts
```

### 2. Sentry Integration

**In application:**
```python
# app/main.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=f"customify-api@{settings.VERSION}",
        traces_sample_rate=0.1,  # 10% of transactions
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
    )
```

### 3. Custom Metrics (Prometheus)

Already implemented in application. Scrape endpoint:
```
GET /metrics
```

---

## Security Hardening

### 1. Network Security

**VPC Setup:**
- Public subnets: ALB only
- Private subnets: ECS tasks, RDS, ElastiCache
- No public IPs on app containers
- NAT Gateway for outbound internet

**Security Groups:**
```bash
# ALB security group (allow 80, 443 from internet)
aws ec2 create-security-group \
    --group-name customify-alb-sg \
    --description "ALB security group" \
    --vpc-id vpc-12345

aws ec2 authorize-security-group-ingress \
    --group-id sg-alb-12345 \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-alb-12345 \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# API security group (allow 8000 from ALB only)
aws ec2 create-security-group \
    --group-name customify-api-sg \
    --description "API security group" \
    --vpc-id vpc-12345

aws ec2 authorize-security-group-ingress \
    --group-id sg-api-12345 \
    --protocol tcp \
    --port 8000 \
    --source-group sg-alb-12345

# Database security group (allow 5432 from API only)
aws ec2 authorize-security-group-ingress \
    --group-id sg-db-12345 \
    --protocol tcp \
    --port 5432 \
    --source-group sg-api-12345
```

### 2. IAM Least Privilege

- Use separate IAM roles for each service
- Never use root credentials
- Rotate access keys every 90 days
- Enable MFA for all human users

### 3. Secrets Management

**Store in AWS Secrets Manager:**
```bash
# Create secret
aws secretsmanager create-secret \
    --name customify/database-url \
    --secret-string "$DATABASE_URL" \
    --description "Production database URL"

# Rotate secret (manually)
aws secretsmanager update-secret \
    --secret-id customify/database-url \
    --secret-string "$NEW_DATABASE_URL"

# Automatic rotation (configure in console)
```

### 4. Enable WAF
```bash
# Create Web ACL
aws wafv2 create-web-acl \
    --name customify-waf \
    --scope REGIONAL \
    --default-action Allow={} \
    --rules file://waf-rules.json \
    --region us-east-1

# Associate with ALB
aws wafv2 associate-web-acl \
    --web-acl-arn arn:aws:wafv2:us-east-1:123456789012:regional/webacl/customify-waf/... \
    --resource-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/customify-prod-alb/...
```

---

## Backup & Recovery

### 1. Database Backups

**Automated (RDS):**
- Automatic daily snapshots (7 day retention)
- Transaction logs backed up every 5 minutes
- Point-in-time recovery available

**Manual Snapshot:**
```bash
aws rds create-db-snapshot \
    --db-instance-identifier customify-prod-db \
    --db-snapshot-identifier customify-prod-manual-$(date +%Y%m%d)
```

**Restore from Snapshot:**
```bash
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier customify-prod-db-restored \
    --db-snapshot-identifier customify-prod-manual-20240115
```

### 2. S3 Backups

**Enable versioning** (already done in setup)

**Cross-region replication:**
```bash
aws s3api put-bucket-replication \
    --bucket customify-production \
    --replication-configuration file://replication-config.json
```

### 3. Disaster Recovery Plan

**RTO (Recovery Time Objective):** 1 hour  
**RPO (Recovery Point Objective):** 5 minutes

**Steps:**
1. Spin up new RDS instance from latest snapshot
2. Update DNS to point to backup region
3. Deploy application to backup region
4. Verify all services operational
5. Monitor for 24 hours

---

## Scaling Guidelines

### Horizontal Scaling (ECS)

**Auto-scaling policy:**
```bash
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/customify-prod/customify-api-service \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 10

aws application-autoscaling put-scaling-policy \
    --policy-name customify-api-cpu-scaling \
    --service-namespace ecs \
    --resource-id service/customify-prod/customify-api-service \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

**scaling-policy.json:**
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleOutCooldown": 60,
  "ScaleInCooldown": 300
}
```

### Vertical Scaling

**Increase CPU/Memory:**

1. Update task definition with new values
2. Register new version
3. Update service with new task definition
4. ECS performs rolling update

### Database Scaling

**Read replicas:**
```bash
aws rds create-db-instance-read-replica \
    --db-instance-identifier customify-prod-db-replica-1 \
    --source-db-instance-identifier customify-prod-db \
    --db-instance-class db.t3.medium
```

**Vertical scaling (change instance class):**
```bash
aws rds modify-db-instance \
    --db-instance-identifier customify-prod-db \
    --db-instance-class db.m5.large \
    --apply-immediately
```

---

## Rollback Procedures

### ECS Rollback
```bash
# List task definitions
aws ecs list-task-definitions --family-prefix customify-api

# Rollback to previous version
aws ecs update-service \
    --cluster customify-prod \
    --service customify-api-service \
    --task-definition customify-api:PREVIOUS_VERSION \
    --force-new-deployment
```

### Database Rollback
```bash
# List recent migrations
alembic history

# Downgrade to specific version
alembic downgrade <revision>

# Or downgrade one version
alembic downgrade -1
```

### Full Rollback Procedure

1. **Stop deployments**
2. **Rollback application** (ECS task definition)
3. **Rollback database** (if schema changed)
4. **Clear caches** (Redis FLUSHALL)
5. **Monitor errors** (Sentry, CloudWatch)
6. **Verify functionality**
7. **Communicate to team**

---

## Post-Deployment Verification
```bash
# 1. Health check
curl https://api.customify.com/health

# 2. Register new user
curl -X POST https://api.customify.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!","full_name":"Test"}'

# 3. Login
curl -X POST https://api.customify.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!"}'

# 4. Create design (test background worker)
curl -X POST https://api.customify.com/api/v1/designs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_type":"t-shirt","design_data":{"text":"Test","font":"Bebas-Bold","color":"#FF0000"}}'

# 5. Check CloudWatch logs
aws logs tail /ecs/customify-api --follow

# 6. Check metrics
open https://console.aws.amazon.com/cloudwatch/
```

---

## Support

- **Deployment Issues:** devops@customify.app
- **Runbook:** https://docs.customify.app/runbook
- **On-Call:** https://pagerduty.com/customify
```

---

## 📦 Resumen de Archivos Generados

Todos los archivos están listos para ser agregados al repositorio:
```
01-core-api/
├── README.md                    ✅ (ya existe, actualizado)
├── CONTRIBUTING.md              ✅ (nuevo)
├── CHANGELOG.md                 ✅ (nuevo)
├── API_REFERENCE.md             ✅ (nuevo)
└── DEPLOYMENT_GUIDE.md          ✅ (nuevo)