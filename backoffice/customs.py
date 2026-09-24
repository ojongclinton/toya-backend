import random
from .models import BackofficeAdmin
from rest_framework_simplejwt.tokens import RefreshToken , AccessToken , RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils import timezone
from datetime import timedelta, date


class OTP: 
    def __init__(self) : 
        pass 
    
    def generate_otp( length=6) : 
        
        otp = random.randint(100000,999999)
        
        return str(otp)
    
    
    
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
            user = BackofficeAdmin.objects.get(id = id)
            
            return token , user
        except Exception  : 
            raise AuthenticationFailed("Invalid token")
        
        
    def process_block_token(refresh_token) : 
        
        if refresh_token : 
            refresh = RefreshToken(refresh_token)
            refresh.blacklist() 
            
        return True
            
                    
        
class Utils: 
    
    def __init__(self) -> None:
        pass
    
    def generate_dates_for_month(self, year, month):
        """
        Generate a list of all dates in a given month.
        """
        first_day = date(year, month, 1)
        next_month = first_day.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        return [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
