from channels.auth import AuthMiddlewareStack
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async


class TokenAuthMiddleware:
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        query_string = scope['query_string']
        print("HEADERS", query_string)
        if b'auth' in query_string:
            try:
                token_name, token_key = query_string.decode().split('=')
                print("TOKENNNNNNN ", token_name, token_key)
                if token_name == 'auth':
                    scope['user'] = self.get_user(self, token_key)
            except Exception as e:
                scope['user'] = AnonymousUser()
                print(e)

        return self.inner(scope)

    
    @database_sync_to_async  
    def get_user(self, key):
        token = Token.objects.get(key=key)
        user = token.user
        return user

TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))