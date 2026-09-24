"""
Tests for OTP signup verification flow for Drivers.

Run with verbose output:
    pytest drivers/tests/test_signup_otp.py -v -s
"""
import pytest
import logging
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework import status
from django.utils.timezone import now
from datetime import timedelta
from unittest.mock import patch, MagicMock

from drivers.models import Drivers
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
def test_driver_data():
    """Fixture for test driver registration data."""
    return {
        'username': 'testdriver',
        'email': 'testdriver@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'Driver',
        'phone_number': '+237697300001',
        'adresse': 'Test Address'
    }


@pytest.fixture
def create_unverified_driver(db):
    """Fixture to create an unverified driver."""
    driver = Drivers.objects.create(
        username='unverified_driver',
        email='unverified_driver@example.com',
        first_name='Unverified',
        last_name='Driver',
        phone_number='+237697300002',
        is_phone_verified=False
    )
    driver.set_password('testpass123')
    driver.save()
    return driver


@pytest.fixture
def create_verified_driver(db):
    """Fixture to create a verified driver."""
    driver = Drivers.objects.create(
        username='verified_driver',
        email='verified_driver@example.com',
        first_name='Verified',
        last_name='Driver',
        phone_number='+237697300003',
        is_phone_verified=True
    )
    driver.set_password('testpass123')
    driver.save()
    return driver


@pytest.mark.django_db
class TestSignupOTPManagerDrivers:
    """Unit tests for SignupOTPManager with Drivers."""
    
    def test_generate_signup_otp(self, create_unverified_driver):
        """Test OTP generation creates a 6-digit code for drivers."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Generate Signup OTP (Drivers)")
        logger.info("="*80)
        
        user = create_unverified_driver
        logger.info(f"🚗 Driver created: {user.phone_number} (verified={user.is_phone_verified})")
        
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
    
    def test_generate_otp_rotation(self, create_unverified_driver):
        """Test that generating a new OTP rotates the old one."""
        logger.info("\n" + "="*80)
        logger.info("TEST: OTP Rotation (Drivers)")
        logger.info("="*80)
        
        user = create_unverified_driver
        logger.info(f"🚗 Driver: {user.phone_number}")
        
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
    
    def test_validate_otp_success(self, create_unverified_driver):
        """Test successful OTP validation for drivers."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Validate OTP - Success (Drivers)")
        logger.info("="*80)
        
        user = create_unverified_driver
        code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"🚗 Driver: {user.phone_number}")
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


@pytest.mark.django_db
class TestRegisterDriversWithOTPFeatureFlag:
    """Test driver registration flow with ENFORCE_PHONE_VERIFICATION flag."""
    
    @patch('drivers.tasks.notifiy_new_user_with_sms_tasks.delay')
    @override_settings(ENFORCE_PHONE_VERIFICATION=True)
    def test_register_with_verification_enabled(self, mock_sms, api_client, test_driver_data):
        """Test driver registration with phone verification enabled."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Driver Register with ENFORCE_PHONE_VERIFICATION=True")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True")
        logger.info(f"🚗 Registering driver: {test_driver_data['phone_number']}")
        
        response = api_client.post('/api/drivers/auth/register/', test_driver_data, format='json')
        logger.info(f"📡 POST /api/drivers/auth/register/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response data: {response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['verification_required'] is True
        assert 'Tokens' not in response.data
        assert 'Id' in response.data
        logger.info("✅ No tokens issued (verification required)")
        
        # Verify driver created but not verified
        user = Drivers.objects.get(phone_number=test_driver_data['phone_number'])
        assert user.is_phone_verified is False
        logger.info(f"✅ Driver created: is_phone_verified={user.is_phone_verified}")
        
        # Verify OTP was generated
        assert SignupOTP.objects.filter(user=user).exists()
        otp_obj = SignupOTP.objects.get(user=user)
        logger.info(f"✅ OTP generated and stored: {otp_obj.code}")
        
        # Verify SMS was sent
        assert mock_sms.called
        logger.info(f"✅ SMS task called: {mock_sms.call_count} time(s)")
        logger.info("="*80 + "\n")
    
    @patch('drivers.tasks.notifiy_new_user_with_sms_tasks.delay')
    @override_settings(ENFORCE_PHONE_VERIFICATION=False)
    def test_register_with_verification_disabled(self, mock_sms, api_client, test_driver_data):
        """Test legacy driver registration flow (backward compatible)."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Driver Register with ENFORCE_PHONE_VERIFICATION=False (Legacy)")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=False")
        logger.info(f"🚗 Registering driver: {test_driver_data['phone_number']}")
        
        response = api_client.post('/api/drivers/auth/register/', test_driver_data, format='json')
        logger.info(f"📡 POST /api/drivers/auth/register/")
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
class TestRequestSignupOTPDrivers:
    """Test request-signup-otp endpoint for drivers."""
    
    @patch('drivers.tasks.notifiy_new_user_with_sms_tasks.delay')
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_request_otp_success(self, mock_sms, api_client, create_unverified_driver):
        """Test successful OTP request for drivers."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Request Signup OTP - Success (Drivers)")
        logger.info("="*80)
        
        user = create_unverified_driver
        logger.info(f"🚗 Driver: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/drivers/auth/request-signup-otp/',
            {'phone_number': user.phone_number},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/request-signup-otp/")
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
        """Test OTP request for non-existent driver."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Request OTP - Driver Not Found")
        logger.info("="*80)
        
        fake_phone = '+237697399999'
        logger.info(f"🚗 Requesting OTP for non-existent driver: {fake_phone}")
        
        response = api_client.post(
            '/api/drivers/auth/request-signup-otp/',
            {'phone_number': fake_phone},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/request-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data['Message'].lower()
        logger.info("✅ 404 returned for non-existent driver")
        logger.info("="*80 + "\n")
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_request_otp_already_verified(self, api_client, create_verified_driver):
        """Test OTP request for already verified driver."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Request OTP - Already Verified Driver")
        logger.info("="*80)
        
        user = create_verified_driver
        logger.info(f"🚗 Driver: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/drivers/auth/request-signup-otp/',
            {'phone_number': user.phone_number},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/request-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already verified" in response.data['Message'].lower()
        logger.info("✅ Request rejected (driver already verified)")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestVerifySignupOTPDrivers:
    """Test verify-signup-otp endpoint for drivers."""
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_verify_otp_success(self, api_client, create_unverified_driver):
        """Test successful OTP verification for drivers."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Verify Signup OTP - Success (Drivers Full Flow)")
        logger.info("="*80)
        
        user = create_unverified_driver
        code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"🚗 Driver: {user.phone_number} (verified={user.is_phone_verified})")
        logger.info(f"🔐 OTP generated: {code}")
        
        response = api_client.post(
            '/api/drivers/auth/verify-signup-otp/',
            {'phone_number': user.phone_number, 'otp_code': code},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/verify-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response has Tokens: {'Tokens' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        assert 'access' in response.data['Tokens']
        logger.info("✅ Verification successful, tokens issued")
        
        # Verify driver is now verified
        user.refresh_from_db()
        assert user.is_phone_verified is True
        logger.info(f"✅ Driver now verified: is_phone_verified={user.is_phone_verified}")
        logger.info("="*80 + "\n")
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_verify_otp_wrong_code(self, api_client, create_unverified_driver):
        """Test verification with wrong code for drivers."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Verify OTP - Wrong Code via API (Drivers)")
        logger.info("="*80)
        
        user = create_unverified_driver
        correct_code = SignupOTPManager.generate_signup_otp(user)
        logger.info(f"🚗 Driver: {user.phone_number}")
        logger.info(f"🔐 Correct OTP: {correct_code}")
        
        wrong_code = '000000'
        response = api_client.post(
            '/api/drivers/auth/verify-signup-otp/',
            {'phone_number': user.phone_number, 'otp_code': wrong_code},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/verify-signup-otp/ with WRONG code: {wrong_code}")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.data['Message'].lower()
        logger.info("✅ Verification rejected (invalid code)")
        logger.info("="*80 + "\n")
    
    @override_settings(ENABLE_OTP_THROTTLING=False)
    def test_verify_otp_already_verified(self, api_client, create_verified_driver):
        """Test verification for already verified driver returns tokens."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Verify OTP - Already Verified Driver (Graceful)")
        logger.info("="*80)
        
        user = create_verified_driver
        logger.info(f"🚗 Driver: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/drivers/auth/verify-signup-otp/',
            {'phone_number': user.phone_number, 'otp_code': '123456'},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/verify-signup-otp/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        assert "already verified" in response.data['Message'].lower()
        logger.info("✅ Graceful handling: tokens issued for already verified driver")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestLoginDriversWithVerificationGate:
    """Test driver login gating based on phone verification."""
    
    @override_settings(ENFORCE_PHONE_VERIFICATION=True)
    def test_login_unverified_driver_blocked(self, api_client, create_unverified_driver):
        """Test login blocked for unverified driver when flag is enabled."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Driver Login Gate - Unverified Driver Blocked")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True")
        
        user = create_unverified_driver
        logger.info(f"🚗 Driver: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/drivers/auth/login/',
            {'phone_number': user.phone_number, 'password': 'testpass123'},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/login/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response message: {response.data.get('Message')}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not verified" in response.data['Message'].lower()
        assert response.data['verification_required'] is True
        logger.info("✅ Login blocked (phone not verified)")
        logger.info("="*80 + "\n")
    
    @override_settings(ENFORCE_PHONE_VERIFICATION=True)
    def test_login_verified_driver_allowed(self, api_client, create_verified_driver):
        """Test login allowed for verified driver."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Driver Login Gate - Verified Driver Allowed")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=True")
        
        user = create_verified_driver
        logger.info(f"🚗 Driver: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/drivers/auth/login/',
            {'phone_number': user.phone_number, 'password': 'testpass123'},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/login/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response has Tokens: {'Tokens' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        logger.info("✅ Login allowed (phone verified)")
        logger.info("="*80 + "\n")
    
    @override_settings(ENFORCE_PHONE_VERIFICATION=False)
    def test_login_unverified_driver_allowed_when_disabled(self, api_client, create_unverified_driver):
        """Test login allowed for unverified driver when flag is disabled (backward compatible)."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Driver Login Gate - Backward Compatible (Flag OFF)")
        logger.info("="*80)
        logger.info(f"🔧 Feature flag: ENFORCE_PHONE_VERIFICATION=False")
        
        user = create_unverified_driver
        logger.info(f"🚗 Driver: {user.phone_number} (verified={user.is_phone_verified})")
        
        response = api_client.post(
            '/api/drivers/auth/login/',
            {'phone_number': user.phone_number, 'password': 'testpass123'},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/login/")
        logger.info(f"📝 Response status: {response.status_code}")
        logger.info(f"📝 Response has Tokens: {'Tokens' in response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tokens' in response.data
        logger.info("✅ Login allowed even without verification (backward compatible)")
        logger.info("="*80 + "\n")


@pytest.mark.django_db
class TestForgotPasswordSecurityDrivers:
    """Test that forgot_password no longer returns OTP in response for drivers."""
    
    @patch('drivers.tasks.notifiy_new_user_with_sms_tasks.delay')
    def test_forgot_password_no_otp_in_response(self, mock_sms, api_client, create_verified_driver):
        """Test forgot_password does not return OTP value for drivers."""
        logger.info("\n" + "="*80)
        logger.info("TEST: Security - Driver Forgot Password (No OTP in Response)")
        logger.info("="*80)
        
        user = create_verified_driver
        logger.info(f"🚗 Driver: {user.phone_number}")
        
        response = api_client.post(
            '/api/drivers/auth/forgot_password/',
            {'phone_number': user.phone_number},
            format='json'
        )
        logger.info(f"📡 POST /api/drivers/auth/forgot_password/")
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
