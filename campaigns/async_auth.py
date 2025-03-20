from rest_framework.authentication import TokenAuthentication
from asgiref.sync import sync_to_async

class AsyncTokenAuthentication(TokenAuthentication):
    async def authenticate(self, request):
        # Wrap the synchronous authentication in sync_to_async.
        return await sync_to_async(super().authenticate)(request)
