from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import UserAPIKey
from rest_framework import status


class APIKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        api_key_obj, created = UserAPIKey.objects.get_or_create(user=request.user)

        if created or not api_key_obj.key:
            api_key_obj.regenerate_key()

        return Response({"api_key": api_key_obj.key}, status=status.HTTP_200_OK)


class APIKeyRefreshView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            api_key_obj = request.user.api_key
        except UserAPIKey.DoesNotExist:
            return Response(
                {"result": "API-key not found"}, status=status.HTTP_404_NOT_FOUND
            )

        api_key_obj.regenerate_key()
        return Response({"api_key": api_key_obj.key}, status=status.HTTP_200_OK)
