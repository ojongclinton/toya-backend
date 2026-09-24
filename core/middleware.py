"""
JWT Authentication Middleware for Django Channels WebSocket
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs
import jwt
from django.conf import settings


@database_sync_to_async
def get_user_from_token(token):
    """Decode JWT token and get user."""
    from django.contrib.auth.models import AnonymousUser
    from core.models import BaseUser
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=['HS256']
        )
        
        user_id = payload.get('user_id')
        if not user_id:
            return AnonymousUser()
        
        # Get user from database
        user = BaseUser.objects.get(id=user_id)
        return user
        
    except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError):
        return AnonymousUser()
    except BaseUser.DoesNotExist:
        return AnonymousUser()
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Token can be passed in:
    1. Query string: ?token=<jwt_token>
    2. Headers: Authorization: Bearer <jwt_token>
    """
    
    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser
        
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        # If not in query string, try headers
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Convenience function to wrap URLRouter with JWT authentication.
    Usage: JWTAuthMiddlewareStack(URLRouter(...))
    """
    return JWTAuthMiddleware(inner)
