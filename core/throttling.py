"""
Throttling classes for OTP endpoints to prevent abuse.

CONFIGURATION:
--------------
To change throttling rates, update the 'rate' attribute in each class below.
Format: '<number>/<period>' where period can be: second, minute, hour, day
Examples:
  - '5/hour'    = 5 requests per hour
  - '10/minute' = 10 requests per minute
  - '100/day'   = 100 requests per day
  - '3/second'  = 3 requests per second

To enable/disable throttling globally, set ENABLE_OTP_THROTTLING in settings.
When disabled, these throttle classes will allow all requests through.
"""
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings


class OTPRequestThrottle(AnonRateThrottle):
    """
    Throttle for OTP request endpoints (signup, password reset).
    
    Current limit: 5 requests per hour per phone number/IP.
    
    To change the rate, update the 'rate' attribute below.
    Examples: '3/hour', '10/minute', '50/day'
    """
    scope = 'otp_request'
    rate = '5/hour'  # Change this value to adjust throttling rate
    
    def allow_request(self, request, view):
        """Check if throttling is enabled before applying rate limit."""
        # Feature flag: disable throttling if ENABLE_OTP_THROTTLING is False
        if not getattr(settings, 'ENABLE_OTP_THROTTLING', True):
            return True
        return super().allow_request(request, view)
    
    def get_cache_key(self, request, view):
        """Use phone_number from request data as throttle key if available."""
        phone_number = request.data.get('phone_number')
        if phone_number:
            return f'throttle_otp_request_{phone_number}'
        # Fallback to IP-based throttling
        return super().get_cache_key(request, view)


class OTPVerifyThrottle(AnonRateThrottle):
    """
    Throttle for OTP verification endpoints.
    
    Current limit: 10 requests per hour per phone number/IP.
    
    To change the rate, update the 'rate' attribute below.
    Examples: '5/hour', '20/minute', '100/day'
    """
    scope = 'otp_verify'
    rate = '10/hour'  # Change this value to adjust throttling rate
    
    def allow_request(self, request, view):
        """Check if throttling is enabled before applying rate limit."""
        # Feature flag: disable throttling if ENABLE_OTP_THROTTLING is False
        if not getattr(settings, 'ENABLE_OTP_THROTTLING', True):
            return True
        return super().allow_request(request, view)
    
    def get_cache_key(self, request, view):
        """Use phone_number from request data as throttle key if available."""
        phone_number = request.data.get('phone_number')
        if phone_number:
            return f'throttle_otp_verify_{phone_number}'
        # Fallback to IP-based throttling
        return super().get_cache_key(request, view)
