from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import ApiKey

class ApiKeyAuthentication(BaseAuthentication):
    keyword = "X-API-KEY"

    def authenticate(self, request):
        key = request.headers.get(self.keyword)
        if not key:
            return None

        try:
            apikey = ApiKey.objects.select_related("host").get(key=key, active=True)
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid API key")

        return (None, apikey)