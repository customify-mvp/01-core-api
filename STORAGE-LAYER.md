# Storage Layer Implementation

## Overview

The Storage Layer provides file storage capabilities for user-generated content (design previews, thumbnails, PDFs, avatars). It supports both **AWS S3** (production) and **Local filesystem** (development).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Domain Layer                         │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │  IStorageRepository (interface)          │           │
│  │  - upload_design_preview()               │           │
│  │  - upload_design_thumbnail()             │           │
│  │  - delete_design_assets()                │           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────┴──────────┐         ┌──────────┴─────────┐
│ Infrastructure    │         │  Infrastructure    │
│                   │         │                    │
│ StorageRepoImpl   │         │ LocalStorageRepo   │
│ (S3)              │         │ (filesystem)       │
│                   │         │                    │
│ Uses:             │         │ Uses:              │
│ └─ S3Client       │         │ └─ pathlib         │
└───────────────────┘         └────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# AWS S3 Settings
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
S3_BUCKET_NAME=customify-production
S3_PUBLIC_BUCKET=true  # false for signed URLs

# CloudFront (optional)
CLOUDFRONT_DOMAIN=d123abc.cloudfront.net

# Storage Mode
USE_LOCAL_STORAGE=true  # true for dev, false for production
```

### App Config

```python
# app/config.py

class Settings(BaseSettings):
    # AWS S3
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "customify-production"
    S3_PUBLIC_BUCKET: bool = True
    CLOUDFRONT_DOMAIN: str = ""
    
    # Storage
    USE_LOCAL_STORAGE: bool = True
    
    @property
    def s3_base_url(self) -> str:
        """Returns CloudFront or S3 direct URL."""
        if self.CLOUDFRONT_DOMAIN:
            return f"https://{self.CLOUDFRONT_DOMAIN}"
        return f"https://{self.S3_BUCKET_NAME}.s3.{self.AWS_REGION}.amazonaws.com"
```

---

## File Structure

```
app/
├── domain/
│   └── repositories/
│       └── storage_repository.py          # Interface
│
└── infrastructure/
    └── storage/
        ├── __init__.py                    # Factory (get_storage_repository)
        ├── s3_client.py                   # AWS S3 wrapper
        ├── storage_repo_impl.py           # S3 implementation
        └── local_storage.py               # Local filesystem mock
```

---

## Usage

### 1. In Celery Workers

```python
from app.infrastructure.storage import get_storage_repository
from io import BytesIO

# Get storage (auto-selects S3 or local based on config)
storage = get_storage_repository()

# Upload preview
with open('design.png', 'rb') as f:
    url = storage.upload_design_preview(design_id, f)
    print(f"Preview URL: {url}")

# Upload thumbnail
with open('thumb.png', 'rb') as f:
    url = storage.upload_design_thumbnail(design_id, f)

# Delete all assets
storage.delete_design_assets(design_id)
```

### 2. In Render Task

```python
from app.infrastructure.workers.tasks.render_design import render_design_preview

# Task flow:
# 1. Get design from DB
# 2. Mark as RENDERING
# 3. Generate image (PIL)
# 4. Upload to storage (S3 or local)
# 5. Generate thumbnail
# 6. Upload thumbnail
# 7. Mark as PUBLISHED with URLs

result = render_design_preview.delay(design_id)
```

---

## Storage Implementations

### S3 Storage (Production)

**File:** `app/infrastructure/storage/storage_repo_impl.py`

- Uploads to S3 bucket
- Uses CloudFront if configured
- Public URLs: `https://bucket.s3.region.amazonaws.com/designs/xxx/preview.png`
- CloudFront URLs: `https://d123.cloudfront.net/designs/xxx/preview.png`

**Paths:**
- Preview: `designs/{design_id}/preview.png`
- Thumbnail: `designs/{design_id}/thumbnail.png`

**Metadata:**
- `design_id`: Design UUID
- `type`: "preview" or "thumbnail"

### Local Storage (Development)

**File:** `app/infrastructure/storage/local_storage.py`

- Saves to `./storage/designs/{design_id}/` directory
- Returns mock URLs: `http://localhost:8000/static/designs/{design_id}/preview.png`
- Useful for local development without AWS credentials

**Directory Structure:**
```
storage/
└── designs/
    └── {design_id}/
        ├── preview.png
        └── thumbnail.png
```

---

## S3 Client

### Methods

#### `upload_file(file_data, key, content_type, metadata)`
```python
url = s3_client.upload_file(
    file_data=open('image.png', 'rb'),
    key='designs/123/preview.png',
    content_type='image/png',
    metadata={'design_id': '123', 'type': 'preview'}
)
```

#### `delete_file(key)`
```python
success = s3_client.delete_file('designs/123/preview.png')
```

#### `file_exists(key)`
```python
if s3_client.file_exists('designs/123/preview.png'):
    print('File exists!')
```

#### `get_signed_url(key, expiration)`
```python
# For private buckets (S3_PUBLIC_BUCKET=false)
url = s3_client.get_signed_url('designs/123/preview.png', expiration=3600)
```

---

## Image Rendering

### Render Flow (PIL)

```python
# 1. Create image (600x600)
image = Image.new('RGB', (600, 600), color='#FF0000')

# 2. Add text
draw = ImageDraw.Draw(image)
font = ImageFont.truetype('/path/to/font.ttf', 48)
draw.text((x, y), 'Custom Text', fill='#FFFFFF', font=font)

# 3. Save to buffer
buffer = BytesIO()
image.save(buffer, format='PNG')

# 4. Upload to storage
buffer.seek(0)
url = storage.upload_design_preview(design_id, buffer)
```

### Thumbnail Generation

```python
# Resize to 200x200 (maintains aspect ratio)
image.thumbnail((200, 200), Image.Resampling.LANCZOS)

# Save to buffer
thumbnail_buffer = BytesIO()
image.save(thumbnail_buffer, format='PNG')

# Upload
url = storage.upload_design_thumbnail(design_id, thumbnail_buffer)
```

---

## AWS Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://customify-production --region us-east-1
```

### 2. Configure Bucket Policy (Public)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::customify-production/*"
    }
  ]
}
```

### 3. Enable CORS

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]
```

### 4. Create IAM User

Permissions needed:
- `s3:PutObject`
- `s3:GetObject`
- `s3:DeleteObject`
- `s3:ListBucket`

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
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::customify-production"
    }
  ]
}
```

### 5. CloudFront (Optional)

Benefits:
- Global CDN (faster delivery)
- HTTPS by default
- Cache control
- Custom domain support

Setup:
1. Create CloudFront distribution
2. Origin: S3 bucket
3. Get distribution domain (e.g., `d123abc.cloudfront.net`)
4. Set `CLOUDFRONT_DOMAIN` in `.env`

---

## Testing

### Test Local Storage

```bash
# 1. Set USE_LOCAL_STORAGE=true in .env

# 2. Create design via API
curl -X POST http://localhost:8000/api/v1/designs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_type": "t-shirt",
    "design_data": {
      "text": "Test Design",
      "font": "Bebas-Bold",
      "color": "#FF0000"
    }
  }'

# 3. Wait for worker (2-3 seconds)

# 4. Check files exist
ls ./storage/designs/{design_id}/
# Should see: preview.png, thumbnail.png

# 5. View image
open ./storage/designs/{design_id}/preview.png
```

### Test S3 Storage

```bash
# 1. Set AWS credentials in .env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=customify-dev
USE_LOCAL_STORAGE=false

# 2. Rebuild worker
docker-compose up -d --build worker

# 3. Create design
# Same as above

# 4. Verify S3 upload
aws s3 ls s3://customify-dev/designs/

# 5. Get design
curl http://localhost:8000/api/v1/designs/{id} \
  -H "Authorization: Bearer $TOKEN"

# Check preview_url and thumbnail_url
# Should be: https://customify-dev.s3.us-east-1.amazonaws.com/designs/xxx/preview.png
```

### Test Direct S3 Upload

```python
from app.infrastructure.storage.s3_client import s3_client
from io import BytesIO

# Create test data
data = BytesIO(b"test image data")

# Upload
url = s3_client.upload_file(data, "test/upload.png")
print(f"Uploaded: {url}")

# Verify exists
exists = s3_client.file_exists("test/upload.png")
print(f"Exists: {exists}")

# Delete
deleted = s3_client.delete_file("test/upload.png")
print(f"Deleted: {deleted}")
```

---

## Error Handling

### S3 Errors

```python
try:
    url = storage.upload_design_preview(design_id, image_data)
except Exception as e:
    logger.error(f"Upload failed: {e}")
    # Mark design as failed
    design.mark_failed(str(e))
```

Common errors:
- `NoCredentialsError`: AWS credentials not configured
- `ClientError (403)`: Insufficient permissions
- `ClientError (404)`: Bucket not found
- `ClientError (NoSuchKey)`: File not found

### Retry Logic

Celery automatically retries on failure:

```python
@celery_app.task(bind=True, max_retries=3)
def render_design_preview(self, design_id: str):
    try:
        # Upload to S3
        storage.upload_design_preview(design_id, image_data)
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

---

## Performance

### Upload Times (Approximate)

| File Size | Local | S3 (us-east-1) | S3 + CloudFront |
|-----------|-------|----------------|-----------------|
| 100 KB    | <1ms  | 100-200ms      | 50-100ms        |
| 500 KB    | 1ms   | 300-500ms      | 150-300ms       |
| 2 MB      | 5ms   | 1-2s           | 500ms-1s        |

### Optimization Tips

1. **Use CloudFront**: Reduces latency by 50-70%
2. **Compress Images**: Use PNG compression level 6-9
3. **Parallel Uploads**: Upload preview + thumbnail concurrently
4. **Thumbnail First**: Generate thumbnail before full preview

---

## Monitoring

### CloudWatch Metrics (S3)

- `NumberOfObjects`: Total files in bucket
- `BucketSizeBytes`: Total storage used
- `AllRequests`: Total API calls
- `4xxErrors`, `5xxErrors`: Error rates

### Logging

```python
# All operations are logged
logger.info(f"Uploaded preview: {url}")
logger.error(f"Upload failed: {error}")
```

Check worker logs:
```bash
docker-compose logs worker | grep "Uploaded"
docker-compose logs worker | grep "ERROR"
```

---

## Cleanup

### Delete Old Designs

```python
from app.infrastructure.storage import get_storage_repository

storage = get_storage_repository()

# Delete all assets for a design
storage.delete_design_assets(design_id)
```

### Bulk Cleanup Script

```python
# scripts/cleanup_storage.py
import boto3
from datetime import datetime, timedelta

s3 = boto3.client('s3')
bucket = 'customify-production'

# Delete files older than 90 days
cutoff = datetime.now() - timedelta(days=90)

response = s3.list_objects_v2(Bucket=bucket, Prefix='designs/')
for obj in response.get('Contents', []):
    if obj['LastModified'] < cutoff:
        s3.delete_object(Bucket=bucket, Key=obj['Key'])
        print(f"Deleted: {obj['Key']}")
```

---

## Security

### S3 Bucket Security

1. **Private by default**: Set `S3_PUBLIC_BUCKET=false`
2. **Use signed URLs**: `s3_client.get_signed_url(key, expiration=3600)`
3. **Bucket encryption**: Enable AES-256 encryption
4. **Access logging**: Enable S3 access logs
5. **Versioning**: Enable versioning for recovery

### IAM Best Practices

- Use least privilege permissions
- Rotate access keys regularly
- Use IAM roles for EC2/ECS (avoid hardcoded keys)
- Enable MFA for console access

---

## Future Enhancements

1. **Image Optimization**: WebP format, compression
2. **Multiple Sizes**: Generate multiple thumbnail sizes
3. **CDN Purge**: CloudFront cache invalidation
4. **Progress Tracking**: Upload progress for large files
5. **Virus Scanning**: ClamAV integration
6. **Watermarking**: Add watermarks to previews
7. **PDF Generation**: Generate print-ready PDFs
8. **Batch Processing**: Upload multiple designs concurrently

---

## Troubleshooting

### Issue: "NoCredentialsError"

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution:**
```bash
# Set credentials in .env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Restart worker
docker-compose restart worker
```

### Issue: "Access Denied"

```
ClientError: An error occurred (AccessDenied) when calling the PutObject operation
```

**Solution:** Check IAM permissions include `s3:PutObject`

### Issue: Local storage not working

```
FileNotFoundError: [Errno 2] No such file or directory: './storage/designs/xxx/preview.png'
```

**Solution:**
```bash
# Create storage directory
mkdir -p ./storage/designs

# Check permissions
chmod -R 755 ./storage
```

---

## Summary

✅ **Implemented:**
- S3Client wrapper (upload, delete, signed URLs)
- Storage repository interface (domain layer)
- S3 implementation (production)
- Local storage implementation (development)
- Factory pattern (auto-select based on config)
- Image rendering (PIL/Pillow)
- Thumbnail generation
- Error handling and retry logic

✅ **Tested:**
- Local storage mode
- S3 upload/delete
- Thumbnail generation
- URL generation (S3 + CloudFront)

✅ **Ready for:**
- Local development (USE_LOCAL_STORAGE=true)
- Production deployment (USE_LOCAL_STORAGE=false + AWS credentials)
