"""
Seed development data into the database.

Creates:
- 1 test user (test@customify.app)
- 1 subscription (free plan)
- 3 example designs

Run with: python scripts/seed_dev_data.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import AsyncSessionLocal, engine
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.subscription_model import SubscriptionModel
from app.infrastructure.database.models.design_model import DesignModel

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_data():
    """Seed development data."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if user already exists
            stmt = select(UserModel).where(UserModel.email == "test@customify.app")
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("⚠️  Test user already exists. Skipping seed.")
                return
            
            print("🌱 Seeding development data...")
            
            # ============================================================
            # 1. Create test user
            # ============================================================
            user_id = str(uuid.uuid4())
            user = UserModel(
                id=user_id,
                email="test@customify.app",
                password_hash=pwd_context.hash("Test1234"),
                full_name="Test User",
                avatar_url=None,
                is_active=True,
                is_verified=True,
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_login=None
            )
            session.add(user)
            await session.flush()  # Get user.id before creating related records
            
            print(f"✅ Created user: {user.email} (ID: {user.id})")
            
            # ============================================================
            # 2. Create subscription (free plan)
            # ============================================================
            subscription_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            subscription = SubscriptionModel(
                id=subscription_id,
                user_id=user.id,
                plan="free",
                status="active",
                stripe_customer_id=None,
                stripe_subscription_id=None,
                designs_this_month=0,
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                created_at=now,
                updated_at=now
            )
            session.add(subscription)
            await session.flush()
            
            print(f"✅ Created subscription: {subscription.plan} plan (ID: {subscription.id})")
            
            # ============================================================
            # 3. Create 3 example designs
            # ============================================================
            designs = [
                {
                    "id": str(uuid.uuid4()),
                    "product_type": "t-shirt",
                    "design_data": {
                        "text": "Hello World",
                        "font": "Arial",
                        "color": "#000000",
                        "fontSize": 48,
                        "position": {"x": 150, "y": 200}
                    },
                    "status": "published",
                    "preview_url": "https://via.placeholder.com/600x600/000000/FFFFFF?text=Hello+World",
                    "thumbnail_url": "https://via.placeholder.com/150x150/000000/FFFFFF?text=Hello+World"
                },
                {
                    "id": str(uuid.uuid4()),
                    "product_type": "mug",
                    "design_data": {
                        "text": "Coffee Lover",
                        "font": "Georgia",
                        "color": "#8B4513",
                        "fontSize": 36,
                        "position": {"x": 100, "y": 150}
                    },
                    "status": "draft",
                    "preview_url": None,
                    "thumbnail_url": None
                },
                {
                    "id": str(uuid.uuid4()),
                    "product_type": "poster",
                    "design_data": {
                        "text": "Dream Big, Work Hard",
                        "font": "Helvetica",
                        "color": "#1E90FF",
                        "fontSize": 72,
                        "position": {"x": 200, "y": 300}
                    },
                    "status": "published",
                    "preview_url": "https://via.placeholder.com/600x800/1E90FF/FFFFFF?text=Dream+Big",
                    "thumbnail_url": "https://via.placeholder.com/150x200/1E90FF/FFFFFF?text=Dream+Big"
                }
            ]
            
            for design_data in designs:
                design = DesignModel(
                    id=design_data["id"],
                    user_id=user.id,
                    product_type=design_data["product_type"],
                    design_data=design_data["design_data"],
                    status=design_data["status"],
                    preview_url=design_data["preview_url"],
                    thumbnail_url=design_data["thumbnail_url"],
                    is_deleted=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(design)
                print(f"✅ Created design: {design.product_type} - '{design.design_data['text']}' ({design.status})")
            
            # Commit all changes
            await session.commit()
            
            print("\n🎉 Seed completed successfully!")
            print(f"\n📊 Summary:")
            print(f"   Users: 1")
            print(f"   Subscriptions: 1")
            print(f"   Designs: 3")
            print(f"\n🔑 Test credentials:")
            print(f"   Email: test@customify.app")
            print(f"   Password: Test1234")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error seeding data: {e}")
            raise
        finally:
            await session.close()


async def main():
    """Main entry point."""
    print("=" * 60)
    print("CUSTOMIFY - Seed Development Data")
    print("=" * 60)
    
    # Wait for database to be ready
    print("\n⏳ Connecting to database...")
    
    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        print("✅ Database connection established")
        
        # Run seed
        await seed_data()
        
    except Exception as e:
        print(f"\n❌ Failed to connect to database: {e}")
        print("\n💡 Make sure:")
        print("   1. Docker containers are running: docker-compose up -d")
        print("   2. Migrations are applied: alembic upgrade head")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
