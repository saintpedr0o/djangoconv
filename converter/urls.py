from django.urls import path
from . import views


app_name = "converter"

urlpatterns = [
    path(
        "get-target-formats/", views.get_target_formats_view, name="get_target_formats"
    ),
    path("", views.select_format_view, name="select_format"),
    path(
        "convert/<slug:input_format>/to/<slug:output_format>/",
        views.convert_view,
        name="convert",
    ),
]
