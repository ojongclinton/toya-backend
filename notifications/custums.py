import random
from drivers.models import Drivers
from clients.models import Clients
from rest_framework_simplejwt.tokens import RefreshToken , AccessToken , RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from backoffice.models import BackofficeAdmin
from core.models import BaseUser


class JWT : 
    def __init__(self) : 
        pass
        
    def filter_and_decode_token(auth_token): 
        
        token_prefix = 'Bearer '
        token = auth_token[len(token_prefix):] if auth_token.startswith(token_prefix) else None
        
        if token is None : 
            raise AuthenticationFailed("Token not found")       
        
        try : 
            try : 
                payload = AccessToken(token).payload
                id = payload['user_id']
                user = Drivers.objects.get(id = id)
                
                return token , user
            except  :
                try : 
                    payload = AccessToken(token).payload
                    id = payload['user_id']
                    user = Clients.objects.get(id = id)
                    
                    return token , user
                except Exception : 
                    raise AuthenticationFailed("Users (Driver or Client Does not Exist)")
                
        
        except Exception  : 
            raise AuthenticationFailed("Invalid token")
    
    


class RetrieveBackofficeUser: 
    def __init__(self) -> None:
        pass
    
    
    def retrieve_backoffice_user(self, sender_or_reciepient_id) : 
        
        backoffice = BackofficeAdmin.objects.all().first()
        
        if backoffice : 
            sender = BaseUser.objects.get(id=backoffice.id)

            return sender
        sender_or_reciepient =  BaseUser.objects.get(id=sender_or_reciepient_id)
        return sender_or_reciepient
        