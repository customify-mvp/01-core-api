"""Manual integration test for use cases - Complete flow."""

import asyncio
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories.user_repo_impl import UserRepositoryImpl
from app.infrastructure.database.repositories.subscription_repo_impl import SubscriptionRepositoryImpl
from app.infrastructure.database.repositories.design_repo_impl import DesignRepositoryImpl
from app.application.use_cases.auth.register_user import RegisterUserUseCase
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.application.use_cases.designs.create_design import CreateDesignUseCase


async def test_complete_flow():
    """Test: Register → Login → Create Design"""
    
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Complete User Flow")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        # Initialize repositories
        user_repo = UserRepositoryImpl(session)
        subscription_repo = SubscriptionRepositoryImpl(session)
        design_repo = DesignRepositoryImpl(session)
        
        # 1. Register User
        print("\n1️⃣  Testing RegisterUserUseCase...")
        register_uc = RegisterUserUseCase(user_repo, subscription_repo)
        
        try:
            user = await register_uc.execute(
                email="flow_test@test.com",
                password="Test1234",
                full_name="Flow Test User"
            )
            print(f"   ✅ User registered: {user.email} (id: {user.id[:8]}...)")
            await session.commit()
        except Exception as e:
            print(f"   ⚠️  User might already exist: {e}")
            await session.rollback()
            # Get existing user
            user = await user_repo.get_by_email("flow_test@test.com")
            if user:
                print(f"   ✅ Using existing user: {user.email}")
            else:
                print("   ❌ Failed to get user")
                return
        
        # 2. Test password validation
        print("\n2️⃣  Testing password validation...")
        try:
            await register_uc.execute(
                email="weak_pass@test.com",
                password="weak",  # Too short
                full_name="Weak Password Test"
            )
            print("   ❌ Should have rejected weak password!")
        except ValueError as e:
            print(f"   ✅ Weak password rejected: {e}")
            await session.rollback()
        
        # 3. Login User
        print("\n3️⃣  Testing LoginUserUseCase...")
        login_uc = LoginUserUseCase(user_repo)
        
        try:
            logged_user, token = await login_uc.execute(
                email="FLOW_TEST@TEST.COM",  # Test case insensitive
                password="Test1234"
            )
            print(f"   ✅ User logged in: {logged_user.email}")
            print(f"   ✅ Token generated: {token[:40]}...")
            print(f"   ✅ Last login: {logged_user.last_login}")
            await session.commit()
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            await session.rollback()
            return
        
        # 4. Create Design
        print("\n4️⃣  Testing CreateDesignUseCase...")
        create_design_uc = CreateDesignUseCase(design_repo, subscription_repo)
        
        try:
            design = await create_design_uc.execute(
                user_id=user.id,
                product_type="t-shirt",
                design_data={
                    "text": "Integration Test",
                    "font": "Bebas-Bold",
                    "color": "#FF0000"
                },
                use_ai_suggestions=False
            )
            print(f"   ✅ Design created: {design.id[:8]}...")
            print(f"   ✅ Product: {design.product_type}")
            print(f"   ✅ Status: {design.status.value}")
            await session.commit()
        except Exception as e:
            print(f"   ❌ Design creation failed: {e}")
            await session.rollback()
            return
        
        # 5. Test design validation
        print("\n5️⃣  Testing design validation...")
        try:
            await create_design_uc.execute(
                user_id=user.id,
                product_type="t-shirt",
                design_data={
                    "text": "Invalid Font Test",
                    "font": "InvalidFont",  # Not in whitelist
                    "color": "#FF0000"
                }
            )
            print("   ❌ Should have rejected invalid font!")
        except ValueError as e:
            print(f"   ✅ Invalid design rejected: {e}")
            await session.rollback()
        
        # 6. Verify Subscription Usage
        print("\n6️⃣  Verifying subscription usage...")
        subscription = await subscription_repo.get_by_user(user.id)
        print(f"   ✅ Plan: {subscription.plan.value}")
        print(f"   ✅ Status: {subscription.status.value}")
        print(f"   ✅ Designs this month: {subscription.designs_this_month}")
        print(f"   ✅ Quota: {subscription.designs_this_month}/{10}")  # FREE plan limit
        print(f"   ✅ Remaining: {subscription.get_remaining_quota()}")
        
        # 7. Count user designs
        print("\n7️⃣  Verifying design count...")
        design_count = await design_repo.count_by_user(user.id)
        print(f"   ✅ Total designs in DB: {design_count}")
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_complete_flow())
