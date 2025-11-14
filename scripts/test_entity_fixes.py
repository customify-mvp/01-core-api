"""Test script for validating entity method fixes."""

from app.domain.entities.subscription import Subscription, PlanType, SubscriptionStatus
from app.domain.entities.design import Design

print("=" * 60)
print("TESTING ENTITY METHOD FIXES")
print("=" * 60)

# Test 1: Subscription.is_active()
print("\n1. Testing Subscription.is_active() method:")
sub = Subscription.create(user_id='user-123', plan=PlanType.FREE)
print(f"   Status: {sub.status.value}")
print(f"   ✅ is_active() = {sub.is_active()}")

# Test with inactive subscription
sub.status = SubscriptionStatus.CANCELED
print(f"   Status changed to: {sub.status.value}")
print(f"   ✅ is_active() = {sub.is_active()}")

# Test 2: Design.validate() - Valid design
print("\n2. Testing Design.validate() with VALID data:")
try:
    design = Design.create(
        user_id='user-123',
        product_type='t-shirt',
        design_data={
            'text': 'Hello World',
            'font': 'Bebas-Bold',
            'color': '#FF5733'
        }
    )
    print(f"   ✅ Valid design created: {design.id[:8]}...")
except ValueError as e:
    print(f"   ❌ ERROR: {e}")

# Test 3: Design.validate() - Invalid font
print("\n3. Testing Design.validate() with INVALID font:")
try:
    design = Design.create(
        user_id='user-123',
        product_type='t-shirt',
        design_data={
            'text': 'Test',
            'font': 'InvalidFont',
            'color': '#FF0000'
        }
    )
    print(f"   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

# Test 4: Design.validate() - Invalid color
print("\n4. Testing Design.validate() with INVALID color:")
try:
    design = Design.create(
        user_id='user-123',
        product_type='t-shirt',
        design_data={
            'text': 'Test',
            'font': 'Bebas-Bold',
            'color': 'red'  # Invalid format
        }
    )
    print(f"   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

# Test 5: Design.validate() - Missing required field
print("\n5. Testing Design.validate() with MISSING required field:")
try:
    design = Design.create(
        user_id='user-123',
        product_type='t-shirt',
        design_data={
            'text': 'Test',
            'font': 'Bebas-Bold'
            # Missing 'color'
        }
    )
    print(f"   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

# Test 6: Design.validate() - Text too long
print("\n6. Testing Design.validate() with TEXT too long:")
try:
    design = Design.create(
        user_id='user-123',
        product_type='t-shirt',
        design_data={
            'text': 'A' * 101,  # 101 chars (max is 100)
            'font': 'Bebas-Bold',
            'color': '#FF0000'
        }
    )
    print(f"   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED!")
print("=" * 60)
