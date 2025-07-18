from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from ..models import UserAPIKey


class APIKeyAuthentication(BaseAuthentication):
    keyword = "Api-Key"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        if not auth_header.startswith(self.keyword + " "):
            return None

        api_key = auth_header[len(self.keyword) + 1 :].strip()

        try:
            key_obj = UserAPIKey.objects.select_related("user").get(key=api_key)
        except UserAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")

        return (key_obj.user, None)
