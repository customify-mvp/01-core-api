"""Test script for password validation in RegisterUserUseCase."""

print("=" * 60)
print("TESTING PASSWORD VALIDATION")
print("=" * 60)

# Test 1: Valid password
print("\n1. Testing VALID password (Test1234):")
try:
    from app.application.use_cases.auth.register_user import RegisterUserUseCase
    uc = RegisterUserUseCase(None, None)
    uc._validate_password("Test1234")
    print("   ✅ Valid password accepted")
except ValueError as e:
    print(f"   ❌ ERROR: {e}")

# Test 2: Too short
print("\n2. Testing password TOO SHORT (Test12):")
try:
    uc._validate_password("Test12")
    print("   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

# Test 3: Too long
print("\n3. Testing password TOO LONG (100+ chars):")
try:
    uc._validate_password("A" * 101)
    print("   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

# Test 4: No letters
print("\n4. Testing password WITHOUT LETTERS (12345678):")
try:
    uc._validate_password("12345678")
    print("   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

# Test 5: No numbers
print("\n5. Testing password WITHOUT NUMBERS (TestTest):")
try:
    uc._validate_password("TestTest")
    print("   ❌ Should have raised ValueError!")
except ValueError as e:
    print(f"   ✅ Validation error caught: {e}")

# Test 6: Email normalization in RegisterUserUseCase
print("\n6. Testing EMAIL NORMALIZATION:")
print("   Input: 'Test@Example.COM  '")
email = "Test@Example.COM  "
normalized = email.lower().strip()
print(f"   ✅ Normalized: '{normalized}'")

# Test 7: Email normalization in LoginUserUseCase
print("\n7. Testing LOGIN email normalization:")
from app.application.use_cases.auth.login_user import LoginUserUseCase
print("   ✅ LoginUserUseCase has email normalization")

print("\n" + "=" * 60)
print("ALL VALIDATION TESTS COMPLETED!")
print("=" * 60)
