"""
Integration test for Repository Pattern.

Tests repository implementations with actual database operations.
Run with: docker-compose exec api python scripts/test_repositories.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.domain.entities.user import User
from app.domain.entities.subscription import Subscription, PlanType, SubscriptionStatus
from app.domain.entities.design import Design, DesignStatus
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories import (
    UserRepositoryImpl,
    SubscriptionRepositoryImpl,
    DesignRepositoryImpl
)


async def test_user_repository():
    """Test UserRepositoryImpl CRUD operations."""
    print("\n" + "="*60)
    print("TEST: UserRepositoryImpl")
    print("="*60)
    
    async with AsyncSessionLocal() as session:
        repo = UserRepositoryImpl(session)
        
        # 1. Test: Create user
        print("\n1️⃣  Testing CREATE...")
        user = User.create(
            email=f"test_{datetime.now().timestamp()}@example.com",
            password_hash="hashed_password_123",
            full_name="Test User"
        )
        created_user = await repo.create(user)
        print(f"✅ Created user: {created_user.email} (ID: {created_user.id})")
        
        # 2. Test: Get by ID
        print("\n2️⃣  Testing GET BY ID...")
        found_user = await repo.get_by_id(created_user.id)
        assert found_user is not None
        assert found_user.email == created_user.email
        print(f"✅ Found user by ID: {found_user.email}")
        
        # 3. Test: Get by email
        print("\n3️⃣  Testing GET BY EMAIL...")
        found_user = await repo.get_by_email(created_user.email)
        assert found_user is not None
        assert found_user.id == created_user.id
        print(f"✅ Found user by email: {found_user.email}")
        
        # 4. Test: Check email exists
        print("\n4️⃣  Testing EXISTS EMAIL...")
        exists = await repo.exists_email(created_user.email)
        assert exists is True
        print(f"✅ Email exists check: {exists}")
        
        # 5. Test: Update user
        print("\n5️⃣  Testing UPDATE...")
        found_user.full_name = "Updated Name"
        found_user.updated_at = datetime.now(timezone.utc)
        updated_user = await repo.update(found_user)
        assert updated_user.full_name == "Updated Name"
        print(f"✅ Updated user name: {updated_user.full_name}")
        
        # 6. Test: Soft delete user
        print("\n6️⃣  Testing DELETE (soft)...")
        deleted = await repo.delete(created_user.id)
        assert deleted is True
        print(f"✅ Soft deleted user")
        
        # 7. Verify user is deleted
        found_user = await repo.get_by_id(created_user.id)
        assert found_user is None
        print(f"✅ Verified user is deleted (returns None)")
        
        await session.commit()
        print("\n" + "="*60)
        print("✅ ALL USER REPOSITORY TESTS PASSED")
        print("="*60)


async def test_subscription_repository():
    """Test SubscriptionRepositoryImpl CRUD operations."""
    print("\n" + "="*60)
    print("TEST: SubscriptionRepositoryImpl")
    print("="*60)
    
    async with AsyncSessionLocal() as session:
        # Create a test user first
        user_repo = UserRepositoryImpl(session)
        user = User.create(
            email=f"sub_test_{datetime.now().timestamp()}@example.com",
            password_hash="hash",
            full_name="Sub Test User"
        )
        user = await user_repo.create(user)
        
        repo = SubscriptionRepositoryImpl(session)
        
        # 1. Test: Create subscription
        print("\n1️⃣  Testing CREATE...")
        subscription = Subscription.create(
            user_id=user.id,
            plan=PlanType.FREE
        )
        created_sub = await repo.create(subscription)
        print(f"✅ Created subscription: {created_sub.plan.value} (ID: {created_sub.id})")
        
        # 2. Test: Get by ID
        print("\n2️⃣  Testing GET BY ID...")
        found_sub = await repo.get_by_id(created_sub.id)
        assert found_sub is not None
        assert found_sub.plan == PlanType.FREE
        print(f"✅ Found subscription by ID: {found_sub.plan.value}")
        
        # 3. Test: Get by user
        print("\n3️⃣  Testing GET BY USER...")
        found_sub = await repo.get_by_user(user.id)
        assert found_sub is not None
        assert found_sub.id == created_sub.id
        print(f"✅ Found subscription by user_id")
        
        # 4. Test: Update subscription
        print("\n4️⃣  Testing UPDATE...")
        found_sub.plan = PlanType.STARTER
        found_sub.updated_at = datetime.now(timezone.utc)
        updated_sub = await repo.update(found_sub)
        assert updated_sub.plan == PlanType.STARTER
        print(f"✅ Updated subscription plan: {updated_sub.plan.value}")
        
        await session.commit()
        print("\n" + "="*60)
        print("✅ ALL SUBSCRIPTION REPOSITORY TESTS PASSED")
        print("="*60)


async def test_design_repository():
    """Test DesignRepositoryImpl CRUD operations."""
    print("\n" + "="*60)
    print("TEST: DesignRepositoryImpl")
    print("="*60)
    
    async with AsyncSessionLocal() as session:
        # Create a test user first
        user_repo = UserRepositoryImpl(session)
        user = User.create(
            email=f"design_test_{datetime.now().timestamp()}@example.com",
            password_hash="hash",
            full_name="Design Test User"
        )
        user = await user_repo.create(user)
        
        repo = DesignRepositoryImpl(session)
        
        # 1. Test: Create design
        print("\n1️⃣  Testing CREATE...")
        design = Design.create(
            user_id=user.id,
            product_type="t-shirt",
            design_data={
                "text": "Test Design",
                "font": "Arial",
                "color": "#000000"
            }
        )
        created_design = await repo.create(design)
        print(f"✅ Created design: {created_design.product_type} (ID: {created_design.id})")
        
        # 2. Test: Get by ID
        print("\n2️⃣  Testing GET BY ID...")
        found_design = await repo.get_by_id(created_design.id)
        assert found_design is not None
        assert found_design.design_data["text"] == "Test Design"
        print(f"✅ Found design by ID: {found_design.design_data['text']}")
        
        # 3. Test: Get by user
        print("\n3️⃣  Testing GET BY USER...")
        designs = await repo.get_by_user(user.id)
        assert len(designs) == 1
        assert designs[0].id == created_design.id
        print(f"✅ Found {len(designs)} design(s) for user")
        
        # 4. Test: Count by user
        print("\n4️⃣  Testing COUNT BY USER...")
        count = await repo.count_by_user(user.id)
        assert count == 1
        print(f"✅ Counted {count} design(s)")
        
        # 5. Test: Update design
        print("\n5️⃣  Testing UPDATE...")
        found_design.status = DesignStatus.PUBLISHED
        found_design.updated_at = datetime.now(timezone.utc)
        updated_design = await repo.update(found_design)
        assert updated_design.status == DesignStatus.PUBLISHED
        print(f"✅ Updated design status: {updated_design.status.value}")
        
        # 6. Test: Soft delete
        print("\n6️⃣  Testing DELETE (soft)...")
        deleted = await repo.delete(created_design.id)
        assert deleted is True
        print(f"✅ Soft deleted design")
        
        # 7. Verify deleted
        found_design = await repo.get_by_id(created_design.id)
        assert found_design is None
        print(f"✅ Verified design is deleted (returns None)")
        
        await session.commit()
        print("\n" + "="*60)
        print("✅ ALL DESIGN REPOSITORY TESTS PASSED")
        print("="*60)


async def main():
    """Run all repository tests."""
    print("\n" + "🚀 STARTING REPOSITORY INTEGRATION TESTS" + "\n")
    
    try:
        await test_user_repository()
        await test_subscription_repository()
        await test_design_repository()
        
        print("\n" + "="*60)
        print("🎉 ALL REPOSITORY TESTS PASSED! 🎉")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
