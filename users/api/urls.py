from django.urls import path
from .views import APIKeyView, APIKeyRefreshView


app_name = "api_key"

urlpatterns = [
    path("get-api-key/", APIKeyView.as_view(), name="get_or_create_api_key"),
    path("refresh-api-key/", APIKeyRefreshView.as_view(), name="refresh_api_key"),
]
