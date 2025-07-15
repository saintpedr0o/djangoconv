from django.urls import path
from .views import AsyncConvertView, ResultsConvertView


app_name = "converter_api"

urlpatterns = [
    path("convert/", AsyncConvertView.as_view(), name="convert"),
    path("result/<str:token>/", ResultsConvertView.as_view(), name="result"),
]
