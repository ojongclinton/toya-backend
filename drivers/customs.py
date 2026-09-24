import random
from .models import Drivers
from rest_framework_simplejwt.tokens import RefreshToken , AccessToken , RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed





class JWT : 
    def __init__(self) : 
        pass
    
    def get_tokens_for_user(Drivers) : 
        refresh = RefreshToken.for_user(Drivers)
        
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
            user = Drivers.objects.get(id = id)
            
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
            
            
        