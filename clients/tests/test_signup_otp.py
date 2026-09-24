"""
Tests for OTP signup verification flow for Clients.

Run with verbose output:
    pytest clients/tests/test_signup_otp.py -v -s
"""
import pytest
import logging
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework import status
from django.utils.timezone import now
from datetime import timedelta
from unittest.mock import patch, MagicMock

from clients.models import Clients
from core.models import SignupOTP
from clients.customs import SignupOTPManager

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def api_client():
    """Fixture for DRF API client."""
    return APIClient()


@pytest.fixture
def test_client_data():
    """Fixture for test client registration data."""
    return {
        'username': 'testclient',
        'email': 'testclient@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'Client',
        'phone_number': '+237697200001',
        'adresse': 'Test Address'
    }


@pytest.fixture
def create_unverified_client(db):
    """Fixture to create an unverified client."""
    client = Clients.objects.create(
        username='unverified',
        email='unverified@example.com',
        first_name='Unverified',
        last_name='User',
        phone_number='+237697200002',
        is_phone_verified=False
    )
    client.set_password('testpass123')
    client.save()
    return client


@pytest.fixture
def create_verified_client(db):
    """Fixture to create a verified client."""
    client = Clients.objects.create(
        username='verified',
        email='verified@example.com',
        first_name='Verified',
        last_name='User',
        phone_number='+237697200003',
        is_phone_verified=True
    )
    client.set_password('testpass123')
    client.save()
    return client


@pytest.mark.django_db
class TestSignupOTPManager:
    """Unit tests for SignupOTPManager."""
    
    def test_generate_signup_otp(self, create_unverified_client):
        """Test OTP generation creates a 6-digit code."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Generate Signup OTP")
        logger.info("="*80)
        
        user = create_unverified_client
        logger.info(f"📱 User created: {user.phone_number} (verified={user.is_phone_verified})")
        
        code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"🔐 OTP generated: {code}")
        
        assert len(code) == 6
        assert code.isdigit()
        logger.info("✅ OTP is 6-digit numeric code")
        
        # Verify OTP is stored in database
        otp_obj = SignupOTP.objects.get(user=user)
        assert otp_obj.code == code
        assert otp_obj.is_used is False
        assert otp_obj.attempts == 0
        logger.info(f"✅ OTP stored in DB: code={otp_obj.code}, is_used={otp_obj.is_used}, attempts={otp_obj.attempts}")
        logger.info("="*80 + "\n")
    
    def test_generate_otp_rotation(self, create_unverified_client):
        """Test that generating a new OTP rotates the old one."""
        logger.info("\n" + "="*80)
        logger.info("TEST: OTP Rotation (Old OTP Invalidated)")
        logger.info("="*80)
        
        user = create_unverified_client
        logger.info(f"📱 User: {user.phone_number}")
        
        code1 = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"🔐 First OTP generated: {code1}")
        
        code2 = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"🔐 Second OTP generated: {code2}")
        
        assert code1 != code2
        logger.info("✅ OTPs are different (rotation working)")
        
        assert SignupOTP.objects.filter(user=user).count() == 1
        logger.info("✅ Only 1 OTP record exists (old one replaced)")
        
        otp_obj = SignupOTP.objects.get(user=user)
        assert otp_obj.code == code2
        logger.info(f"✅ Active OTP is the new one: {code2}")
        logger.info("="*80 + "\n")
    
    def test_validate_otp_success(self, create_unverified_client):
        """Test successful OTP validation."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Validate OTP - Success Case")
        logger.info("="*80)
        
        user = create_unverified_client
        code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"📱 User: {user.phone_number}")
        logger.info(f"🔐 OTP generated: {code}")
        
        success, message = SignupOTPManager.validate_signup_otp(user, code)
        logger.info(f"🔍 Validation attempt with correct code: {code}")
        logger.info(f"📝 Result: success={success}, message='{message}'")
        
        assert success is True
        assert "successfully" in message.lower()
        logger.info("✅ Validation successful")
        
        otp_obj = SignupOTP.objects.get(user=user)
        assert otp_obj.is_used is True
        logger.info(f"✅ OTP marked as used: is_used={otp_obj.is_used}")
        logger.info("="*80 + "\n")
    
    def test_validate_otp_wrong_code(self, create_unverified_client):
        """Test validation with wrong code increments attempts."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Validate OTP - Wrong Code (Attempt Counter)")
        logger.info("="*80)
        
        user = create_unverified_client
        correct_code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"📱 User: {user.phone_number}")
        logger.info(f"🔐 Correct OTP: {correct_code}")
        
        wrong_code = "000000"
        success, message = SignupOTPManager.validate_signup_otp(user, wrong_code)
        logger.info(f"🔍 Validation attempt with WRONG code: {wrong_code}")
        logger.info(f"📝 Result: success={success}, message='{message}'")
        
        assert success is False
        assert "invalid" in message.lower()
        logger.info("✅ Validation failed as expected")
        
        otp_obj = SignupOTP.objects.get(user=user)
        assert otp_obj.attempts == 1
        assert otp_obj.is_used is False
        logger.info(f"✅ Attempt counter incremented: attempts={otp_obj.attempts}, is_used={otp_obj.is_used}")
        logger.info("="*80 + "\n")
    
    def test_validate_otp_expired(self, create_unverified_client):
        """Test validation fails for expired OTP."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Validate OTP - Expired (TTL Check)")
        logger.info("="*80)
        
        user = create_unverified_client
        code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"📱 User: {user.phone_number}")
        logger.info(f"🔐 OTP generated: {code}")
        
        # Manually set created_at to 20 minutes ago (past TTL)
        otp_obj = SignupOTP.objects.get(user=user)
        old_time = now() - timedelta(minutes=20)
        otp_obj.created_at = old_time
        otp_obj.save()
        logger.info(f"⏰ OTP timestamp manually set to 20 minutes ago (TTL is 15 min)")
        logger.info(f"   Created at: {old_time}")
        
        success, message = SignupOTPManager.validate_signup_otp(user, code)
        logger.info(f"🔍 Validation attempt with expired OTP: {code}")
        logger.info(f"📝 Result: success={success}, message='{message}'")
        
        assert success is False
        assert "expired" in message.lower()
        logger.info("✅ Validation failed due to expiration (TTL enforced)")
        logger.info("="*80 + "\n")
    
    def test_validate_otp_already_used(self, create_unverified_client):
        """Test validation fails if OTP already used."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Validate OTP - Already Used (One-Time Use)")
        logger.info("="*80)
        
        user = create_unverified_client
        code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"📱 User: {user.phone_number}")
        logger.info(f"🔐 OTP generated: {code}")
        
        # Use the OTP once
        success1, message1 = SignupOTPManager.validate_signup_otp(user, code)
        logger.info(f"🔍 First validation attempt: success={success1}")
        logger.info(f"   Message: '{message1}'")
        
        # Try to use again
        success, message = SignupOTPManager.validate_signup_otp(user, code)
        logger.info(f"🔍 Second validation attempt (reuse): success={success}")
        logger.info(f"   Message: '{message}'")
        
        assert success is False
        assert "already been used" in message.lower()
        logger.info("✅ Reuse prevented (one-time use enforced)")
        logger.info("="*80 + "\n")
    
    def test_validate_otp_max_attempts(self, create_unverified_client):
        """Test validation fails after max attempts."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Validate OTP - Max Attempts Limit")
        logger.info("="*80)
        
        user = create_unverified_client
        correct_code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"📱 User: {user.phone_number}")
        logger.info(f"🔐 Correct OTP: {correct_code}")
        logger.info(f"🚫 Attempting with wrong code 5 times (max limit)...")
        
        # Exhaust attempts
        for i in range(1, 6):
            success, msg = SignupOTPManager.validate_signup_otp(user, "000000")
            logger.info(f"   Attempt {i}/5: success={success}")
        
        otp_obj = SignupOTP.objects.get(user=user)
        logger.info(f"✅ After 5 failed attempts: attempts={otp_obj.attempts}")
        
        # Next attempt should fail with too many attempts
        success, message = SignupOTPManager.validate_signup_otp(user, "000000")
        logger.info(f"🔍 Attempt 6 (over limit): success={success}")
        logger.info(f"📝 Message: '{message}'")
        
        assert success is False
        assert "too many" in message.lower()
        logger.info("✅ Max attempts limit enforced (5 attempts)")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestRegisterWithOTPFeatureFlag:
    """Test registration flow with ENFORCE_PHONE_VERIFICATION flag."""
    
    @patch('clients.tasks.notifiy_new_user_with_sms_tasks.delay')
    @override_settings(ENFORCE_PHONE_VERIFICATION=True)
    def test_register_with_verification_enabled(self, mock_sms, api_client, test_client_data):
        """Test registration with phone verification enabled."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Register with ENFORCE_PHONE_VERIFICATION=True")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True")
        logger.info(f"📱 Registering user: {test_client_data['phone_number']}")
        
        response = api_client.post('/api/clients/auth/register/', test_client_data, format='json')
        logger.info(f"📡 POST /api/clients/auth/register/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response data: {response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['verification_required'] is True
        assert 'Tokens' not in response.data
        assert 'Id' in response.data
        logger.info("✅ No tokens issued (verification required)")
        
        # Verify user created but not verified
        user = Clients.objects.get(phone_number=test_client_data['phone_number'])
        assert user.is_phone_verified is False
        logger.info(f"✅ User created: is_phone_verified={user.is_phone_verified}")
        
        # Verify OTP was generated
        assert SignupOTP.objects.filter(user=user).exists()
        otp_obj = SignupOTP.objects.get(user=user)
        logger.info(f"✅ OTP generated and stored: {otp_obj.code}")
        
        # Verify SMS was sent
        assert mock_sms.called
        logger.info(f"✅ SMS task called: {mock_sms.call_count} time(s)")
        logger.info("="*80 + "\n")
    
    @patch('clients.tasks.notifiy_new_user_with_sms_tasks.delay')
    @override_settings(ENFORCE_PHONE_VERIFICATION=False)
    def test_register_with_verification_disabled(self, mock_sms, api_client, test_client_data):
        """Test legacy registration flow (backward compatible)."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Register with ENFORCE_PHONE_VERIFICATION=False (Legacy)")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=False")
        logger.info(f"📱 Registering user: {test_client_data['phone_number']}")
        
        response = api_client.post('/api/clients/auth/register/', test_client_data, format='json')
        logger.info(f"📡 POST /api/clients/auth/register/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response has Tokens: {'Tokens' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        assert 'access' in response.data['Tokens']
        assert 'refresh' in response.data['Tokens']
        logger.info("✅ Tokens issued immediately (backward compatible)")
        
        # Verify welcome SMS was sent (not OTP)
        assert mock_sms.called
        logger.info(f"✅ Welcome SMS sent (not OTP)")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestRequestSignupOTP:
    """Test request-signup-otp endpoint."""
    
    @patch('clients.tasks.notifiy_new_user_with_sms_tasks.delay')
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_request_otp_success(self, mock_sms, api_client, create_unverified_client):
        """Test successful OTP request."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Request Signup OTP - Success")
        logger.info("="*80)
        
        user = create_unverified_client
        logger.info(f"📱 User: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/clients/auth/request-signup-otp/',
            {'phone_number': user.phone_number},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/request-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_200_OK
        assert "sent successfully" in response.data['Message']
        logger.info("✅ OTP request successful")
        
        # Verify OTP was generated
        assert SignupOTP.objects.filter(user=user).exists()
        otp_obj = SignupOTP.objects.get(user=user)
        logger.info(f"✅ OTP generated: {otp_obj.code}")
        
        assert mock_sms.called
        logger.info(f"✅ SMS sent via Celery task")
        logger.info("="*80 + "\n")
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_request_otp_user_not_found(self, api_client):
        """Test OTP request for non-existent user."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Request OTP - User Not Found")
        logger.info("="*80)
        
        fake_phone = '+237697999999'
        logger.info(f"📱 Requesting OTP for non-existent user: {fake_phone}")
        
        response = api_client.post(
            '/api/clients/auth/request-signup-otp/',
            {'phone_number': fake_phone},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/request-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data['Message'].lower()
        logger.info("✅ 404 returned for non-existent user")
        logger.info("="*80 + "\n")
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_request_otp_already_verified(self, api_client, create_verified_client):
        """Test OTP request for already verified user."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Request OTP - Already Verified User")
        logger.info("="*80)
        
        user = create_verified_client
        logger.info(f"📱 User: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/clients/auth/request-signup-otp/',
            {'phone_number': user.phone_number},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/request-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already verified" in response.data['Message'].lower()
        logger.info("✅ Request rejected (user already verified)")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestVerifySignupOTP:
    """Test verify-signup-otp endpoint."""
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_verify_otp_success(self, api_client, create_unverified_client):
        """Test successful OTP verification."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Verify Signup OTP - Success (Full Flow)")
        logger.info("="*80)
        
        user = create_unverified_client
        code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"📱 User: {user.phone_number} (verified={user.is_phone_verified})")
        logger.info(f"🔐 OTP generated: {code}")
        
        response = api_client.post(
            '/api/clients/auth/verify-signup-otp/',
            {'phone_number': user.phone_number, 'otp_code': code},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/verify-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response has Tokens: {'Tokens' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        assert 'access' in response.data['Tokens']
        logger.info("✅ Verification successful, tokens issued")
        
        # Verify user is now verified
        user.refresh_from_db()
        assert user.is_phone_verified is True
        logger.info(f"✅ User now verified: is_phone_verified={user.is_phone_verified}")
        logger.info("="*80 + "\n")
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_verify_otp_wrong_code(self, api_client, create_unverified_client):
        """Test verification with wrong code."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Verify OTP - Wrong Code via API")
        logger.info("="*80)
        
        user = create_unverified_client
        correct_code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"📱 User: {user.phone_number}")
        logger.info(f"🔐 Correct OTP: {correct_code}")
        
        wrong_code = '000000'
        response = api_client.post(
            '/api/clients/auth/verify-signup-otp/',
            {'phone_number': user.phone_number, 'otp_code': wrong_code},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/verify-signup-otp/ with WRONG code: {wrong_code}")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.data['Message'].lower()
        logger.info("✅ Verification rejected (invalid code)")
        logger.info("="*80 + "\n")
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_verify_otp_already_verified(self, api_client, create_verified_client):
        """Test verification for already verified user returns tokens."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Verify OTP - Already Verified User (Graceful)")
        logger.info("="*80)
        
        user = create_verified_client
        logger.info(f"📱 User: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/clients/auth/verify-signup-otp/',
            {'phone_number': user.phone_number, 'otp_code': '123456'},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/verify-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        assert "already verified" in response.data['Message'].lower()
        logger.info("✅ Graceful handling: tokens issued for already verified user")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestLoginWithVerificationGate:
    """Test login gating based on phone verification."""
    
    @override_settings(ENFORCE_PHONE_VERIFICATION=True)
    def test_login_unverified_user_blocked(self, api_client, create_unverified_client):
        """Test login blocked for unverified user when flag is enabled."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Login Gate - Unverified User Blocked")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True")
        
        user = create_unverified_client
        logger.info(f"📱 User: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/clients/auth/login/',
            {'phone_number': user.phone_number, 'password': 'testpass123'},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/login/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not verified" in response.data['Message'].lower()
        assert response.data['verification_required'] is True
        logger.info("✅ Login blocked (phone not verified)")
        logger.info("="*80 + "\n")
    
    @override_settings(ENFORCE_PHONE_VERIFICATION=True)
    def test_login_verified_user_allowed(self, api_client, create_verified_client):
        """Test login allowed for verified user."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Login Gate - Verified User Allowed")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True")
        
        user = create_verified_client
        logger.info(f"📱 User: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/clients/auth/login/',
            {'phone_number': user.phone_number, 'password': 'testpass123'},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/login/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response has Tokens: {'Tokens' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        logger.info("✅ Login allowed (phone verified)")
        logger.info("="*80 + "\n")
    
    @override_settings(ENFORCE_PHONE_VERIFICATION=False)
    def test_login_unverified_user_allowed_when_disabled(self, api_client, create_unverified_client):
        """Test login allowed for unverified user when flag is disabled (backward compatible)."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Login Gate - Backward Compatible (Flag OFF)")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=False")
        
        user = create_unverified_client
        logger.info(f"📱 User: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/clients/auth/login/',
            {'phone_number': user.phone_number, 'password': 'testpass123'},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/login/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response has Tokens: {'Tokens' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        logger.info("✅ Login allowed even without verification (backward compatible)")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestForgotPasswordSecurity:
    """Test that forgot_password no longer returns OTP in response."""
    
    @patch('clients.tasks.notifiy_new_user_with_sms_tasks.delay')
    def test_forgot_password_no_otp_in_response(self, mock_sms, api_client, create_verified_client):
        """Test forgot_password does not return OTP value."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Security - Forgot Password (No OTP in Response)")
        logger.info("="*80)
        
        user = create_verified_client
        logger.info(f"📱 User: {user.phone_number}")
        
        response = api_client.post(
            '/api/clients/auth/forgot_password/',
            {'phone_number': user.phone_number},
            format='json'
        )
        logger.info(f"📡 POST /api/clients/auth/forgot_password/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response data: {response.data}")
        logger.info(f"🔒 'OTP' key in response: {'OTP' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'OTP' not in response.data
        assert "sent successfully" in response.data['Message']
        assert mock_sms.called
        logger.info("✅ Security: OTP NOT exposed in API response")
        logger.info("✅ OTP sent via SMS only")
        logger.info("="*80 + "\n")
