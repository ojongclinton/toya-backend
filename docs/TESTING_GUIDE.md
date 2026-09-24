# OTP Signup Verification - Testing Guide

## Running Tests with Verbose Output

### Run All Tests with Detailed Logs

**Clients:**
```bash
pytest clients/tests/test_signup_otp.py -v -s
```

**Drivers:**
```bash
pytest drivers/tests/test_signup_otp.py -v -s
```

**Both:**
```bash
pytest clients/tests/test_signup_otp.py drivers/tests/test_signup_otp.py -v -s
```

**Flags:**
- `-v` = Verbose mode (shows test names)
- `-s` = Show print/log output (displays our custom logging)

### Run Specific Test Class

**Clients:**
```bash
# Test OTP Manager only
pytest clients/tests/test_signup_otp.py::TestSignupOTPManager -v -s

# Test Registration flow
pytest clients/tests/test_signup_otp.py::TestRegisterWithOTPFeatureFlag -v -s

# Test OTP endpoints
pytest clients/tests/test_signup_otp.py::TestRequestSignupOTP -v -s
pytest clients/tests/test_signup_otp.py::TestVerifySignupOTP -v -s

# Test login gating
pytest clients/tests/test_signup_otp.py::TestLoginWithVerificationGate -v -s

# Test security
pytest clients/tests/test_signup_otp.py::TestForgotPasswordSecurity -v -s
```

**Drivers:**
```bash
# Test OTP Manager for drivers
pytest drivers/tests/test_signup_otp.py::TestSignupOTPManagerDrivers -v -s

# Test Driver Registration flow
pytest drivers/tests/test_signup_otp.py::TestRegisterDriversWithOTPFeatureFlag -v -s

# Test Driver OTP endpoints
pytest drivers/tests/test_signup_otp.py::TestRequestSignupOTPDrivers -v -s
pytest drivers/tests/test_signup_otp.py::TestVerifySignupOTPDrivers -v -s

# Test Driver login gating
pytest drivers/tests/test_signup_otp.py::TestLoginDriversWithVerificationGate -v -s

# Test Driver security
pytest drivers/tests/test_signup_otp.py::TestForgotPasswordSecurityDrivers -v -s
```

### Run Single Test
```bash
pytest clients/tests/test_signup_otp.py::TestSignupOTPManager::test_generate_signup_otp -v -s
```

### Run Tests with Coverage
```bash
pytest clients/tests/test_signup_otp.py --cov=clients --cov=core --cov-report=html -v -s
```

---

## Understanding Test Output

### Log Format
Each test outputs structured logs with emojis for easy scanning:

```
================================================================================
TEST: Generate Signup OTP
================================================================================
📱 User created: +237697200002 (verified=False)
🔐 OTP generated: 123456
✅ OTP is 6-digit numeric code
✅ OTP stored in DB: code=123456, is_used=False, attempts=0
================================================================================
```

### Emoji Legend
- 📱 **Phone/User info** - User details and phone numbers
- 🔐 **OTP codes** - Generated OTP values
- 🔧 **Configuration** - Feature flag settings
- 📡 **API calls** - HTTP requests being made
- 📝 **Responses** - API response data
- 🔍 **Validation** - Validation attempts
- ⏰ **Timestamps** - Time-related operations
- 🚫 **Failures** - Expected failure scenarios
- ✅ **Success** - Assertions passed
- 🔒 **Security** - Security-related checks

---

## Test Coverage

### Unit Tests (TestSignupOTPManager)
- ✅ OTP generation (6-digit code)
- ✅ OTP rotation (old code invalidated)
- ✅ Successful validation
- ✅ Wrong code (attempt counter)
- ✅ Expired OTP (TTL check)
- ✅ Already used OTP (one-time use)
- ✅ Max attempts limit (5 attempts)

### Registration Tests (TestRegisterWithOTPFeatureFlag)
- ✅ Registration with ENFORCE_PHONE_VERIFICATION=True
- ✅ Registration with ENFORCE_PHONE_VERIFICATION=False (legacy)

### OTP Request Tests (TestRequestSignupOTP)
- ✅ Successful OTP request
- ✅ User not found (404)
- ✅ Already verified user (400)

### OTP Verification Tests (TestVerifySignupOTP)
- ✅ Successful verification (full flow)
- ✅ Wrong code rejection
- ✅ Already verified user (graceful handling)

### Login Gating Tests (TestLoginWithVerificationGate)
- ✅ Unverified user blocked (flag ON)
- ✅ Verified user allowed (flag ON)
- ✅ Backward compatibility (flag OFF)

### Security Tests (TestForgotPasswordSecurity)
- ✅ OTP not exposed in API responses

---

## Sample Test Output

```bash
$ pytest clients/tests/test_signup_otp.py::TestSignupOTPManager::test_validate_otp_success -v -s

================================================================================
TEST: Validate OTP - Success Case
================================================================================
📱 User: +237697200002
🔐 OTP generated: 456789
🔍 Validation attempt with correct code: 456789
📝 Result: success=True, message='OTP validated successfully'
✅ Validation successful
✅ OTP marked as used: is_used=True
================================================================================

PASSED
```

---

## Debugging Failed Tests

### Check OTP Values
All OTP codes are logged in the test output. Compare:
- Generated OTP (🔐 OTP generated: ...)
- Validation attempt (🔍 Validation attempt with ...)

### Check Feature Flags
Look for configuration lines:
- 🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True/False
- 🔧 Feature flag: ENABLE_OTP_THROTTLING=True/False

### Check API Responses
Full response data is logged:
- 📝 Response status: 200
- 📝 Response data: {...}
- 📝 Response message: "..."

### Check Database State
User and OTP states are logged:
- 📱 User: ... (verified=True/False)
- ✅ OTP stored in DB: code=..., is_used=..., attempts=...

---

## Common Issues

### Issue: Tests fail with "User not found"
**Solution**: Check that fixtures are creating users correctly. Look for:
```
📱 User created: +237697200002 (verified=False)
```

### Issue: OTP validation fails
**Solution**: Check the logs for:
- Generated OTP vs attempted OTP
- TTL expiration (⏰ timestamp logs)
- Attempt counter (attempts=...)

### Issue: Feature flag not working
**Solution**: Verify the `@override_settings` decorator is present and check logs for:
```
🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True
```

---

## CI/CD Integration

### GitHub Actions / GitLab CI
```yaml
- name: Run OTP Tests
  run: |
    pytest clients/tests/test_signup_otp.py -v --tb=short
```

### Pre-commit Hook
```bash
#!/bin/bash
pytest clients/tests/test_signup_otp.py -v --tb=short || exit 1
```

---

## Next Steps

1. **Run migrations** before testing:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Run all tests**:
   ```bash
   pytest clients/tests/test_signup_otp.py -v -s
   ```

3. **Check coverage**:
   ```bash
   pytest clients/tests/test_signup_otp.py --cov=clients.customs --cov=core.throttling --cov-report=term-missing
   ```

4. **Create similar tests for drivers**:
   - Copy `test_signup_otp.py` to `drivers/tests/`
   - Update imports and model references
   - Run with same verbose flags

---

## Performance Notes

- All tests use mocked SMS tasks (no actual SMS sent)
- Database is reset between tests (pytest-django)
- Throttling disabled in tests via `@override_settings(ENABLE_OTP_THROTTLING=False)`
- Average test execution: ~0.1s per test
- Full suite: ~2-3 seconds

---

## Support

For issues or questions:
1. Check the verbose test output first
2. Review `docs/OTP_SIGNUP_IMPLEMENTATION_SUMMARY.md`
3. Check `docs/otp_signup_verification_plan.md`
