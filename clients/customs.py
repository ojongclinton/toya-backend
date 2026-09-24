import random
from .models import Clients
from rest_framework_simplejwt.tokens import RefreshToken , AccessToken , RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.timezone import now
from datetime import timedelta
from core.models import PasswordResetCode, SignupOTP

class OTP: 
    def __init__(self) : 
        pass 
    
    def generate_otp(self, user) : 
        """Generate OTP for password reset (legacy method)."""

        reset_code = str(random.randint(100000, 999999))

        PasswordResetCode.objects.update_or_create(
            user=user,
            defaults={
                "reset_code": reset_code,
                "created_at": now(), 
                "is_valided" : False
            }
        )

        print(f"Reset Code: {reset_code}")
        
        return reset_code


class SignupOTPManager:
    """Manager for signup phone verification OTPs.

    Note: For the moment this is used by both driver and clients systems for authentication.
    This is to avoid duplicate codes for similar interactions, but if the need comes up
    to have dedicated logics for driver apps, then we can create a new manager for drivers in drivers/customs
    """
    
    OTP_VALIDITY_MINUTES = 15
    MAX_ATTEMPTS = 5
    
    @staticmethod
    def generate_signup_otp(user):
        """Generate a new signup OTP for the user."""
        code = str(random.randint(100000, 999999))
        
        SignupOTP.objects.update_or_create(
            user=user,
            defaults={
                "code": code,
                "created_at": now(),
                "is_used": False,
                "attempts": 0
            }
        )
        
        print(f"Signup OTP: {code} for user {user.email}")
        return code
    
    @staticmethod
    def validate_signup_otp(user, code):
        """Validate signup OTP with TTL and attempt limits.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            otp_obj = SignupOTP.objects.get(user=user)
        except SignupOTP.DoesNotExist:
            return False, "No verification code found for this user."
        
        # Check if already used
        if otp_obj.is_used:
            return False, "This validation code has already been used."
        
        # Check attempts limit
        if otp_obj.attempts >= SignupOTPManager.MAX_ATTEMPTS:
            return False, "Too many invalid attempts. Please request a new code."
        
        # Check TTL
        if now() - otp_obj.created_at > timedelta(minutes=SignupOTPManager.OTP_VALIDITY_MINUTES):
            return False, "Code expired. Please request a new one."
        
        # Check code match
        if otp_obj.code != code:
            otp_obj.attempts += 1
            otp_obj.save()
            return False, f"Invalid code. {SignupOTPManager.MAX_ATTEMPTS - otp_obj.attempts} attempts remaining."
        
        # Success: mark as used
        otp_obj.is_used = True
        otp_obj.save()
        return True, "Code validated successfully."
    
    @staticmethod
    def cleanup_expired_otps():
        """Delete expired OTPs (optional cleanup task)."""
        expiry_time = now() - timedelta(minutes=SignupOTPManager.OTP_VALIDITY_MINUTES)
        SignupOTP.objects.filter(created_at__lt=expiry_time).delete()


class Communication : 
    def __init__(self) : 
        pass
    
    def communication_with_sms_otp(self) : 
        pass
    
    def communication_with_whatsapp_otp(self) : 
        pass
    
    def communication_with_email_otp(self) : 
        pass



class JWT : 
    def __init__(self) : 
        pass
    
    def get_tokens_for_user(Clients) : 
        refresh = RefreshToken.for_user(Clients)
        
        return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
        
    def filter_and_decode_token(auth_token): 
        
        token_prefix = 'Bearer '
        token = auth_token[len(token_prefix):] if auth_token.startswith(token_prefix) else None
        
        if token is None : 
            raise AuthenticationFailed("Token not found")       
        
        try : 
            payload = AccessToken(token).payload
            id = payload['user_id']
            user = Clients.objects.get(id = id)
            
            return token , user
        except Exception  : 
            raise AuthenticationFailed("Invalid token")
        
        
    def process_block_token(self, refresh_token):
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)

                refresh.blacklist()

                return True
            except Exception as e:
                raise AuthenticationFailed(f"Error processing refresh token: {str(e)}")

        return False
            
            
        